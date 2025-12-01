"""API views for cases app."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count

from .models import Case
from .serializers import CaseSerializer


class CaseViewSet(viewsets.ModelViewSet):
    """CRUD API for cases."""
    
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for a case."""
        case = self.get_object()
        
        stats = {
            'documents': case.documents.count() if hasattr(case, 'documents') else 0,
            'claims': case.claims.count() if hasattr(case, 'claims') else 0,
            'timeline_events': case.timeline_events.count() if hasattr(case, 'timeline_events') else 0,
            'bias_indicators': case.bias_signals.count() if hasattr(case, 'bias_signals') else 0,
            'contradictions': case.contradictions.count() if hasattr(case, 'contradictions') else 0,
            'entities': case.entities.count() if hasattr(case, 'entities') else 0,
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Run full analysis on a case."""
        case = self.get_object()
        
        # TODO: Integrate with FCIP analysis service
        # For now, return a placeholder
        return Response({
            'status': 'pending',
            'message': 'Full case analysis queued',
            'case_id': str(case.id)
        })
