"""API views for analysis app."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count

from .models import (
    Claim, Contradiction, BiasSignal, TimelineEvent,
    ToulminArgument, Entity, LegalRule, AnalysisRun,
    ContradictionType, Severity
)
from .serializers import (
    ClaimSerializer, ContradictionSerializer, BiasSignalSerializer,
    TimelineEventSerializer, ToulminArgumentSerializer, EntitySerializer,
    LegalRuleSerializer, AnalysisRunSerializer,
    ContradictionSummarySerializer, BiasReportSerializer
)
from .engines.contradiction import ContradictionDetectionEngine
from .engines.bias import BiasDetectionEngine
from django_backend.cases.models import Case


class ClaimViewSet(viewsets.ModelViewSet):
    """CRUD API for claims."""
    queryset = Claim.objects.select_related('document')
    serializer_class = ClaimSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        case_id = self.kwargs.get('case_pk') or self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)
        
        # Optional filters
        claim_type = self.request.query_params.get('claim_type')
        modality = self.request.query_params.get('modality')
        if claim_type:
            qs = qs.filter(claim_type=claim_type)
        if modality:
            qs = qs.filter(modality=modality)
        
        return qs


class ContradictionViewSet(viewsets.ModelViewSet):
    """CRUD API for contradictions."""
    queryset = Contradiction.objects.select_related('claim_a', 'claim_b', 'claim_a__document', 'claim_b__document')
    serializer_class = ContradictionSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        case_id = self.kwargs.get('case_pk') or self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)
        
        # Optional filters
        ctype = self.request.query_params.get('type')
        severity = self.request.query_params.get('severity')
        resolved = self.request.query_params.get('resolved')
        
        if ctype:
            qs = qs.filter(contradiction_type=ctype)
        if severity:
            qs = qs.filter(severity=severity)
        if resolved is not None:
            qs = qs.filter(resolved=resolved.lower() == 'true')
        
        return qs
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark a contradiction as resolved."""
        contradiction = self.get_object()
        note = request.data.get('note', '')
        
        contradiction.resolved = True
        contradiction.resolution_note = note
        contradiction.resolved_at = timezone.now()
        contradiction.save()
        
        return Response(ContradictionSerializer(contradiction).data)


class CaseContradictionViewSet(viewsets.ViewSet):
    """Contradiction detection and summary for a case."""
    
    def list(self, request, case_pk=None):
        """List contradictions for a case."""
        qs = Contradiction.objects.filter(case_id=case_pk).select_related(
            'claim_a', 'claim_b', 'claim_a__document', 'claim_b__document'
        )
        
        # Optional filters
        ctype = request.query_params.get('type')
        severity = request.query_params.get('severity')
        resolved = request.query_params.get('resolved')
        
        if ctype:
            qs = qs.filter(contradiction_type=ctype)
        if severity:
            qs = qs.filter(severity=severity)
        if resolved is not None:
            qs = qs.filter(resolved=resolved.lower() == 'true')
        
        serializer = ContradictionSerializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request, case_pk=None):
        """Get contradiction summary for a case."""
        contradictions = Contradiction.objects.filter(case_id=case_pk)
        
        by_type = dict(contradictions.values('contradiction_type').annotate(
            count=Count('id')
        ).values_list('contradiction_type', 'count'))
        
        by_severity = dict(contradictions.values('severity').annotate(
            count=Count('id')
        ).values_list('severity', 'count'))
        
        summary = {
            'total': contradictions.count(),
            'by_type': by_type,
            'by_severity': by_severity,
            'unresolved': contradictions.filter(resolved=False).count(),
            'self_contradictions': contradictions.filter(same_author=True).count(),
        }
        
        return Response(summary)
    
    @action(detail=False, methods=['post'], url_path='detect')
    def detect(self, request, case_pk=None):
        """Run contradiction detection for a case."""
        case = get_object_or_404(Case, pk=case_pk)
        
        # Create analysis run
        run = AnalysisRun.objects.create(
            case=case,
            run_type='contradiction',
            status='running'
        )
        
        try:
            # Get all claims for the case
            claims = Claim.objects.filter(case=case).select_related('document')
            
            if claims.count() < 2:
                run.status = 'completed'
                run.completed_at = timezone.now()
                run.save()
                return Response({
                    'run_id': str(run.id),
                    'status': 'completed',
                    'contradictions_found': 0,
                    'message': 'Not enough claims to analyze'
                })
            
            # Run detection
            engine = ContradictionDetectionEngine()
            candidates = engine.detect_contradictions(claims, str(case_pk))
            
            # Store contradictions
            created_count = 0
            for candidate in candidates:
                claim_a = claims.get(id=candidate.claim_a_id)
                claim_b = claims.get(id=candidate.claim_b_id)
                
                # Avoid duplicates
                exists = Contradiction.objects.filter(
                    case=case,
                    claim_a=claim_a,
                    claim_b=claim_b
                ).exists() or Contradiction.objects.filter(
                    case=case,
                    claim_a=claim_b,
                    claim_b=claim_a
                ).exists()
                
                if not exists:
                    Contradiction.objects.create(
                        case=case,
                        contradiction_type=candidate.contradiction_type,
                        severity=self._map_confidence_to_severity(candidate.confidence),
                        claim_a=claim_a,
                        claim_b=claim_b,
                        description=candidate.description,
                        legal_significance=candidate.legal_significance,
                        recommended_action=candidate.recommended_action,
                        confidence=candidate.confidence,
                        semantic_similarity=candidate.semantic_similarity,
                        temporal_conflict=candidate.temporal_conflict,
                        same_author=candidate.same_author,
                    )
                    created_count += 1
            
            run.status = 'completed'
            run.completed_at = timezone.now()
            run.contradictions_found = created_count
            run.save()
            
            return Response({
                'run_id': str(run.id),
                'status': 'completed',
                'contradictions_found': created_count,
                'claims_analyzed': claims.count()
            })
            
        except Exception as e:
            run.status = 'failed'
            run.error_message = str(e)
            run.completed_at = timezone.now()
            run.save()
            
            return Response({
                'run_id': str(run.id),
                'status': 'failed',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _map_confidence_to_severity(self, confidence: float) -> str:
        """Map confidence score to severity level."""
        if confidence >= 0.9:
            return 'critical'
        elif confidence >= 0.8:
            return 'high'
        elif confidence >= 0.6:
            return 'medium'
        else:
            return 'low'


class BiasSignalViewSet(viewsets.ModelViewSet):
    """CRUD API for bias signals."""
    queryset = BiasSignal.objects.select_related('document')
    serializer_class = BiasSignalSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        case_id = self.kwargs.get('case_pk') or self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs


class CaseBiasViewSet(viewsets.ViewSet):
    """Bias analysis for a case."""
    
    def list(self, request, case_pk=None):
        """List bias signals for a case."""
        qs = BiasSignal.objects.filter(case_id=case_pk).select_related('document')
        serializer = BiasSignalSerializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='report')
    def report(self, request, case_pk=None):
        """Get comprehensive bias report for a case."""
        signals = BiasSignal.objects.filter(case_id=case_pk).order_by('-z_score')
        
        by_severity = dict(signals.values('severity').annotate(
            count=Count('id')
        ).values_list('severity', 'count'))
        
        by_type = dict(signals.values('signal_type').annotate(
            count=Count('id')
        ).values_list('signal_type', 'count'))
        
        z_scores = list(signals.values_list('z_score', flat=True))
        
        report = {
            'total_signals': signals.count(),
            'by_severity': by_severity,
            'by_type': by_type,
            'statistical_summary': {
                'mean_z_score': sum(z_scores) / len(z_scores) if z_scores else None,
                'max_z_score': max(z_scores) if z_scores else None,
                'signals_above_critical': len([z for z in z_scores if abs(z) >= 2.0]),
            },
            'signals': BiasSignalSerializer(signals, many=True).data
        }
        
        return Response(report)


class TimelineEventViewSet(viewsets.ModelViewSet):
    """CRUD API for timeline events."""
    queryset = TimelineEvent.objects.select_related('document').order_by('event_date')
    serializer_class = TimelineEventSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        case_id = self.kwargs.get('case_pk') or self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs
    
    @action(detail=False, methods=['get'])
    def conflicts(self, request, case_pk=None):
        """Get timeline conflicts for a case."""
        events = TimelineEvent.objects.filter(case_id=case_pk)
        conflicts = []
        
        # Find events with conflicting_events populated
        for event in events.exclude(conflicting_events=[]):
            for conflict_id in event.conflicting_events:
                try:
                    other = events.get(id=conflict_id)
                    conflicts.append({
                        'event1': TimelineEventSerializer(event).data,
                        'event2': TimelineEventSerializer(other).data,
                        'reason': 'Conflicting accounts of the same event'
                    })
                except TimelineEvent.DoesNotExist:
                    pass
        
        return Response({'conflicts': conflicts})


class ToulminArgumentViewSet(viewsets.ModelViewSet):
    """CRUD API for Toulmin arguments."""
    queryset = ToulminArgument.objects.all()
    serializer_class = ToulminArgumentSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        case_id = self.kwargs.get('case_pk') or self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs


class EntityViewSet(viewsets.ModelViewSet):
    """CRUD API for entities."""
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        case_id = self.kwargs.get('case_pk') or self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs


class LegalRuleViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only API for legal rules."""
    queryset = LegalRule.objects.all()
    serializer_class = LegalRuleSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs


class AnalysisRunViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only API for analysis runs."""
    queryset = AnalysisRun.objects.all()
    serializer_class = AnalysisRunSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        case_id = self.kwargs.get('case_pk') or self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs
