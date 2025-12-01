"""
API Views for Cases
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone

from .models import Case, CaseNote
from .serializers import (
    CaseSerializer, CaseListSerializer, CaseCreateSerializer,
    CaseNoteSerializer
)

logger = logging.getLogger(__name__)


class CaseViewSet(viewsets.ModelViewSet):
    """CRUD API for cases with analysis actions."""
    queryset = Case.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CaseListSerializer
        if self.action == 'create':
            return CaseCreateSerializer
        return CaseSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filters
        case_status = self.request.query_params.get('status')
        if case_status:
            qs = qs.filter(status=case_status)
        
        case_type = self.request.query_params.get('case_type')
        if case_type:
            qs = qs.filter(case_type=case_type)
        
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(reference__icontains=search) |
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        return qs
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get comprehensive case statistics."""
        case = self.get_object()
        
        # Refresh counts
        case.update_counts()
        
        # Get detailed stats from related models
        from django_backend.analysis.models import Claim, Contradiction, BiasSignal, TimelineEvent
        
        claims = Claim.objects.filter(case=case)
        contradictions = Contradiction.objects.filter(case=case)
        biases = BiasSignal.objects.filter(case=case)
        
        # Claims breakdown
        claims_by_type = dict(claims.values('claim_type').annotate(
            count=Count('id')
        ).values_list('claim_type', 'count'))
        
        claims_by_modality = dict(claims.values('modality').annotate(
            count=Count('id')
        ).values_list('modality', 'count'))
        
        # Contradictions breakdown
        contradictions_by_type = dict(contradictions.values('contradiction_type').annotate(
            count=Count('id')
        ).values_list('contradiction_type', 'count'))
        
        contradictions_by_severity = dict(contradictions.values('severity').annotate(
            count=Count('id')
        ).values_list('severity', 'count'))
        
        # Bias breakdown
        biases_by_type = dict(biases.values('signal_type').annotate(
            count=Count('id')
        ).values_list('signal_type', 'count'))
        
        avg_certainty = claims.aggregate(avg=Avg('certainty'))['avg']
        
        stats = {
            'documents': case.document_count,
            'claims': case.claim_count,
            'timeline_events': TimelineEvent.objects.filter(case=case).count(),
            'bias_indicators': case.bias_signal_count,
            'contradictions': case.contradiction_count,
            'entities': case.entities.count() if hasattr(case, 'entities') else 0,
            'arguments': case.arguments.count() if hasattr(case, 'arguments') else 0,
            
            # Breakdown stats
            'claims_by_type': claims_by_type,
            'claims_by_modality': claims_by_modality,
            'contradictions_by_type': contradictions_by_type,
            'contradictions_by_severity': contradictions_by_severity,
            'biases_by_type': biases_by_type,
            
            # Summary metrics
            'average_claim_certainty': round(avg_certainty, 3) if avg_certainty else None,
            'self_contradictions': contradictions.filter(same_author=True).count(),
            'unresolved_contradictions': contradictions.filter(resolved=False).count(),
            'high_severity_biases': biases.filter(severity__in=['high', 'critical']).count(),
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Trigger full case analysis pipeline."""
        case = self.get_object()
        
        from django_backend.analysis.models import AnalysisRun
        
        # Check for running analysis
        running = AnalysisRun.objects.filter(
            case=case,
            status__in=['pending', 'running']
        ).exists()
        
        if running:
            return Response({
                'error': 'Analysis already in progress for this case'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create analysis run
        run = AnalysisRun.objects.create(
            case=case,
            run_type='case',
            status='pending',
            progress_message='Analysis queued...'
        )
        
        # TODO: Queue analysis task
        # For now, return the run ID
        
        return Response({
            'message': 'Case analysis queued',
            'run_id': str(run.id),
            'case_id': str(case.id)
        })
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get AI-generated case summary."""
        case = self.get_object()
        
        # TODO: Generate summary using Claude
        # For now, return basic info
        
        from django_backend.analysis.models import Contradiction
        
        critical_contradictions = Contradiction.objects.filter(
            case=case,
            severity__in=['critical', 'high'],
            resolved=False
        ).count()
        
        summary = {
            'case_id': str(case.id),
            'reference': case.reference,
            'title': case.title,
            'status': case.status,
            'key_issues': case.key_issues,
            'analysis_summary': {
                'documents_analyzed': case.document_count,
                'claims_extracted': case.claim_count,
                'critical_contradictions': critical_contradictions,
                'bias_signals': case.bias_signal_count,
            },
            'recommendations': [
                "Review high-severity contradictions",
                "Cross-examine on self-contradictions",
                "Challenge biased language patterns"
            ] if critical_contradictions > 0 else [
                "Case documentation appears consistent"
            ]
        }
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard statistics across all cases."""
        cases = Case.objects.all()
        
        total_cases = cases.count()
        active_cases = cases.filter(status='active').count()
        
        from django_backend.documents.models import Document
        from django_backend.analysis.models import Claim, Contradiction
        
        total_documents = Document.objects.count()
        total_claims = Claim.objects.count()
        total_contradictions = Contradiction.objects.count()
        unresolved_contradictions = Contradiction.objects.filter(resolved=False).count()
        
        # Recent cases
        recent_cases = cases.order_by('-created_at')[:5]
        
        # Cases by type
        cases_by_type = dict(cases.values('case_type').annotate(
            count=Count('id')
        ).values_list('case_type', 'count'))
        
        # Upcoming hearings
        upcoming = cases.filter(
            next_hearing_date__gte=timezone.now().date()
        ).order_by('next_hearing_date')[:5]
        
        return Response({
            'total_cases': total_cases,
            'active_cases': active_cases,
            'total_documents': total_documents,
            'total_claims': total_claims,
            'total_contradictions': total_contradictions,
            'unresolved_contradictions': unresolved_contradictions,
            'cases_by_type': cases_by_type,
            'recent_cases': CaseListSerializer(recent_cases, many=True).data,
            'upcoming_hearings': CaseListSerializer(upcoming, many=True).data,
        })


class CaseNoteViewSet(viewsets.ModelViewSet):
    """CRUD API for case notes."""
    queryset = CaseNote.objects.select_related('case')
    serializer_class = CaseNoteSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        case_id = self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)
        
        note_type = self.request.query_params.get('note_type')
        if note_type:
            qs = qs.filter(note_type=note_type)
        
        priority = self.request.query_params.get('priority')
        if priority:
            qs = qs.filter(priority=priority)
        
        return qs
