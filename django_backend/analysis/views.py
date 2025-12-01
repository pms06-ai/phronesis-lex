"""
API Views for Analysis - Phronesis LEX
Complete REST API for forensic legal analysis.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Avg, Q

from .models import (
    Claim, Contradiction, BiasSignal, TimelineEvent,
    ToulminArgument, Entity, LegalRule, AnalysisRun, BiasBaseline
)
from .serializers import (
    ClaimSerializer, ClaimCreateSerializer,
    ContradictionSerializer, ContradictionResolveSerializer,
    BiasSignalSerializer, TimelineEventSerializer,
    ToulminArgumentSerializer, EntitySerializer,
    LegalRuleSerializer, BiasBaselineSerializer, AnalysisRunSerializer,
    ContradictionSummarySerializer, BiasReportSerializer,
    CaseStatsSerializer, GenerateArgumentRequestSerializer
)
from .services import (
    ContradictionDetectionService,
    BiasDetectionService,
    ArgumentGenerationService,
    ClaimExtractionService
)
from django_backend.cases.models import Case
from django_backend.core.models import AuditLog
from django_backend.core.validators import safe_float, safe_bool

logger = logging.getLogger(__name__)


class ClaimViewSet(viewsets.ModelViewSet):
    """CRUD API for claims with filtering."""
    queryset = Claim.objects.select_related('document', 'case')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ClaimCreateSerializer
        return ClaimSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # Case filter from URL or query param
        case_pk = self.kwargs.get('case_pk')
        if case_pk:
            qs = qs.filter(case_id=case_pk)

        case_id = self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)

        # Additional filters
        claim_type = self.request.query_params.get('claim_type')
        if claim_type:
            qs = qs.filter(claim_type=claim_type)

        modality = self.request.query_params.get('modality')
        if modality:
            qs = qs.filter(modality=modality)

        asserted_by = self.request.query_params.get('asserted_by')
        if asserted_by:
            qs = qs.filter(asserted_by__icontains=asserted_by)

        # Safe float conversion for min_certainty
        min_certainty = safe_float(self.request.query_params.get('min_certainty'))
        if min_certainty is not None:
            qs = qs.filter(certainty__gte=min_certainty)

        return qs.order_by('-created_at')


class ContradictionViewSet(viewsets.ModelViewSet):
    """CRUD API for contradictions."""
    queryset = Contradiction.objects.select_related(
        'claim_a', 'claim_b',
        'claim_a__document', 'claim_b__document',
        'case'
    )
    serializer_class = ContradictionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        case_pk = self.kwargs.get('case_pk')
        if case_pk:
            qs = qs.filter(case_id=case_pk)

        case_id = self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)

        # Filters
        ctype = self.request.query_params.get('type')
        if ctype:
            qs = qs.filter(contradiction_type=ctype)

        severity = self.request.query_params.get('severity')
        if severity:
            qs = qs.filter(severity=severity)

        resolved = self.request.query_params.get('resolved')
        if resolved is not None:
            qs = qs.filter(resolved=safe_bool(resolved))

        same_author = self.request.query_params.get('same_author')
        if same_author is not None:
            qs = qs.filter(same_author=safe_bool(same_author))

        return qs

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark a contradiction as resolved."""
        contradiction = self.get_object()
        serializer = ContradictionResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contradiction.resolved = True
        contradiction.resolution_note = serializer.validated_data['note']
        contradiction.resolved_at = timezone.now()
        contradiction.resolved_by = request.user.username
        contradiction.save()

        # Audit log
        AuditLog.log(
            request=request,
            action=AuditLog.Action.UPDATE,
            resource_type='contradiction',
            resource_id=str(contradiction.id),
            description=f'Resolved contradiction: {contradiction.description[:50]}...'
        )

        return Response(ContradictionSerializer(contradiction).data)


class CaseContradictionViewSet(viewsets.ViewSet):
    """Contradiction detection and summary for cases."""
    permission_classes = [IsAuthenticated]

    def list(self, request, case_pk=None):
        """List contradictions for a case."""
        qs = Contradiction.objects.filter(case_id=case_pk).select_related(
            'claim_a', 'claim_b', 'claim_a__document', 'claim_b__document'
        )

        # Filters
        ctype = request.query_params.get('type')
        if ctype:
            qs = qs.filter(contradiction_type=ctype)

        severity = request.query_params.get('severity')
        if severity:
            qs = qs.filter(severity=severity)

        resolved = request.query_params.get('resolved')
        if resolved is not None:
            qs = qs.filter(resolved=safe_bool(resolved))

        serializer = ContradictionSerializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'next': None,
            'previous': None,
            'results': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request, case_pk=None):
        """Get contradiction summary statistics."""
        contradictions = Contradiction.objects.filter(case_id=case_pk)

        by_type = dict(contradictions.values('contradiction_type').annotate(
            count=Count('id')
        ).values_list('contradiction_type', 'count'))

        by_severity = dict(contradictions.values('severity').annotate(
            count=Count('id')
        ).values_list('severity', 'count'))

        most_severe = contradictions.filter(
            severity__in=['critical', 'high']
        ).order_by('-confidence')[:5]

        summary = {
            'total': contradictions.count(),
            'by_type': by_type,
            'by_severity': by_severity,
            'unresolved': contradictions.filter(resolved=False).count(),
            'self_contradictions': contradictions.filter(same_author=True).count(),
            'most_severe': ContradictionSerializer(most_severe, many=True).data
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
            status='pending',
            progress_message='Queued for processing...'
        )

        # Audit log
        AuditLog.log(
            request=request,
            action=AuditLog.Action.ANALYZE,
            resource_type='case',
            resource_id=str(case.id),
            resource_name=case.reference,
            description='Started contradiction detection'
        )

        # Check if we should use background tasks
        from django.conf import settings
        use_async = not getattr(settings, 'DEBUG', False)

        if use_async:
            # Queue as background task
            try:
                from django_backend.core.tasks import run_contradiction_detection
                run_contradiction_detection(str(case_pk), str(run.id))
                return Response({
                    'run_id': str(run.id),
                    'status': 'queued',
                    'message': 'Contradiction detection queued for processing'
                }, status=status.HTTP_202_ACCEPTED)
            except Exception as e:
                logger.warning(f"Failed to queue task, running synchronously: {e}")

        # Run synchronously (development mode or fallback)
        run.status = 'running'
        run.progress_message = 'Starting contradiction detection...'
        run.save()

        try:
            # Get claims
            claims = Claim.objects.filter(case=case).select_related('document')
            claims_count = claims.count()

            if claims_count < 2:
                run.mark_completed()
                run.progress_message = 'Not enough claims to analyze'
                run.save()
                return Response({
                    'run_id': str(run.id),
                    'status': 'completed',
                    'contradictions_found': 0,
                    'message': 'Not enough claims to analyze (minimum 2 required)'
                })

            run.progress_message = f'Analyzing {claims_count} claims...'
            run.progress_percent = 10
            run.save()

            # Run detection
            service = ContradictionDetectionService()
            candidates = service.detect_contradictions(claims, str(case_pk))

            run.progress_message = f'Found {len(candidates)} potential contradictions, saving...'
            run.progress_percent = 80
            run.save()

            # Save to database
            claims_by_id = {str(c.id): c for c in claims}
            created_count = service.save_contradictions(candidates, case, claims_by_id)

            run.status = 'completed'
            run.completed_at = timezone.now()
            run.contradictions_found = created_count
            run.progress_percent = 100
            run.progress_message = f'Detection complete: {created_count} contradictions found'
            run.save()

            return Response({
                'run_id': str(run.id),
                'status': 'completed',
                'contradictions_found': created_count,
                'claims_analyzed': claims_count,
                'candidates_evaluated': len(candidates)
            })

        except Exception as e:
            logger.exception("Contradiction detection failed")
            run.mark_failed(str(e))
            return Response({
                'run_id': str(run.id),
                'status': 'failed',
                'error': 'Analysis failed. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BiasSignalViewSet(viewsets.ModelViewSet):
    """CRUD API for bias signals."""
    queryset = BiasSignal.objects.select_related('document', 'case')
    serializer_class = BiasSignalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        case_pk = self.kwargs.get('case_pk')
        if case_pk:
            qs = qs.filter(case_id=case_pk)

        case_id = self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)

        signal_type = self.request.query_params.get('signal_type')
        if signal_type:
            qs = qs.filter(signal_type=signal_type)

        return qs.order_by('-z_score')


class CaseBiasViewSet(viewsets.ViewSet):
    """Bias analysis for cases."""
    permission_classes = [IsAuthenticated]

    def list(self, request, case_pk=None):
        """List bias signals for a case."""
        qs = BiasSignal.objects.filter(case_id=case_pk).select_related('document')
        serializer = BiasSignalSerializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'next': None,
            'previous': None,
            'results': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='report')
    def report(self, request, case_pk=None):
        """Get comprehensive bias report."""
        signals = BiasSignal.objects.filter(case_id=case_pk).select_related('document')

        by_severity = dict(signals.values('severity').annotate(
            count=Count('id')
        ).values_list('severity', 'count'))

        by_type = dict(signals.values('signal_type').annotate(
            count=Count('id')
        ).values_list('signal_type', 'count'))

        by_document = dict(signals.values('document__filename').annotate(
            count=Count('id')
        ).values_list('document__filename', 'count'))

        z_scores = list(signals.values_list('z_score', flat=True))

        report = {
            'total_signals': signals.count(),
            'by_severity': by_severity,
            'by_type': by_type,
            'by_document': by_document,
            'statistical_summary': {
                'mean_z_score': sum(z_scores) / len(z_scores) if z_scores else None,
                'max_z_score': max(z_scores) if z_scores else None,
                'min_z_score': min(z_scores) if z_scores else None,
                'signals_above_critical': len([z for z in z_scores if abs(z) >= 2.0]),
                'signals_above_warning': len([z for z in z_scores if abs(z) >= 1.5]),
            },
            'signals': BiasSignalSerializer(signals.order_by('-z_score'), many=True).data
        }

        return Response(report)


class TimelineEventViewSet(viewsets.ModelViewSet):
    """CRUD API for timeline events."""
    queryset = TimelineEvent.objects.select_related('document', 'case')
    serializer_class = TimelineEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        case_pk = self.kwargs.get('case_pk')
        if case_pk:
            qs = qs.filter(case_id=case_pk)

        case_id = self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)

        return qs.order_by('event_date')

    @action(detail=False, methods=['get'])
    def conflicts(self, request, case_pk=None):
        """Get timeline conflicts."""
        events = TimelineEvent.objects.filter(case_id=case_pk)
        conflicts = []

        for event in events.exclude(conflicting_events=[]):
            for conflict_id in event.conflicting_events:
                try:
                    other = events.get(id=conflict_id)
                    conflicts.append({
                        'event1': TimelineEventSerializer(event).data,
                        'event2': TimelineEventSerializer(other).data,
                        'reason': 'Conflicting accounts'
                    })
                except TimelineEvent.DoesNotExist:
                    pass

        return Response({'conflicts': conflicts})


class ToulminArgumentViewSet(viewsets.ModelViewSet):
    """CRUD API for Toulmin arguments."""
    queryset = ToulminArgument.objects.select_related('warrant_rule', 'case')
    serializer_class = ToulminArgumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        case_pk = self.kwargs.get('case_pk')
        if case_pk:
            qs = qs.filter(case_id=case_pk)

        return qs.order_by('-created_at')

    @action(detail=False, methods=['post'])
    def generate(self, request, case_pk=None):
        """Generate a Toulmin argument from case claims."""
        case = get_object_or_404(Case, pk=case_pk)

        serializer = GenerateArgumentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        finding_type = serializer.validated_data['finding_type']
        custom_claim = serializer.validated_data.get('claim_text', '')

        # Get high-confidence claims
        claims = Claim.objects.filter(
            case=case
        ).filter(
            Q(certainty__gte=0.6) | Q(confidence__gte=0.7)
        ).order_by('-certainty')[:20]

        if not claims.exists():
            return Response({
                'error': 'No suitable claims found for argument generation',
                'code': 'no_claims',
                'hint': 'Run document analysis first to extract claims'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Map finding type to pattern
        from .services.argument_generation import ArgumentPattern
        pattern_map = {
            'welfare': ArgumentPattern.WELFARE_ASSESSMENT,
            'threshold': ArgumentPattern.THRESHOLD_SATISFIED,
            'credibility': ArgumentPattern.CREDIBILITY_FINDING,
            'expert': ArgumentPattern.EXPERT_OPINION,
            'bias': ArgumentPattern.BIAS_FINDING,
        }
        pattern = pattern_map.get(finding_type, ArgumentPattern.WELFARE_ASSESSMENT)

        # Generate claim text if not provided
        if not custom_claim:
            custom_claim = f"Based on analysis of {claims.count()} claims regarding {finding_type}"

        # Generate argument
        service = ArgumentGenerationService()
        argument_data = service.generate_argument(
            claim_text=custom_claim,
            supporting_claims=list(claims[:5]),
            pattern=pattern,
            case=case
        )

        # Save argument
        argument = service.save_argument(argument_data, case, list(claims[:5]))

        # Audit log
        AuditLog.log(
            request=request,
            action=AuditLog.Action.CREATE,
            resource_type='argument',
            resource_id=str(argument.id),
            description=f'Generated Toulmin argument for {finding_type}'
        )

        return Response({
            'argument_id': str(argument.id),
            'argument': ToulminArgumentSerializer(argument).data
        }, status=status.HTTP_201_CREATED)


class EntityViewSet(viewsets.ModelViewSet):
    """CRUD API for entities."""
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        case_pk = self.kwargs.get('case_pk')
        if case_pk:
            qs = qs.filter(case_id=case_pk)

        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        return qs.order_by('canonical_name')

    @action(detail=False, methods=['get'])
    def graph(self, request, case_pk=None):
        """Get entity graph for visualization."""
        entities = Entity.objects.filter(case_id=case_pk)

        return Response({
            'case_id': case_pk,
            'nodes': EntitySerializer(entities, many=True).data,
            'total_entities': entities.count(),
            'by_type': dict(entities.values('entity_type').annotate(
                count=Count('id')
            ).values_list('entity_type', 'count'))
        })


class LegalRuleViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only API for legal rules."""
    queryset = LegalRule.objects.all()
    serializer_class = LegalRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(short_name__icontains=search) |
                Q(text__icontains=search) |
                Q(full_citation__icontains=search)
            )

        return qs


class BiasBaselineViewSet(viewsets.ModelViewSet):
    """API for bias baselines."""
    queryset = BiasBaseline.objects.all()
    serializer_class = BiasBaselineSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        doc_type = self.request.query_params.get('doc_type')
        if doc_type:
            qs = qs.filter(doc_type=doc_type)

        return qs


class AnalysisRunViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only API for analysis runs."""
    queryset = AnalysisRun.objects.all()
    serializer_class = AnalysisRunSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        case_pk = self.kwargs.get('case_pk')
        if case_pk:
            qs = qs.filter(case_id=case_pk)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        run_type = self.request.query_params.get('run_type')
        if run_type:
            qs = qs.filter(run_type=run_type)

        return qs.order_by('-started_at')
