from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
import uuid

from documents.models import Document
from .models import Claim, TimelineEvent, BiasIndicator, CompetingClaim, AnalysisRun
from .serializers import (
    ClaimSerializer,
    TimelineEventSerializer,
    BiasIndicatorSerializer,
    CompetingClaimSerializer,
    AnalysisRunSerializer,
)
from .tasks import start_analysis_task

# Try imports to check availability
try:
    from services.ai.claude_service import get_claude_service
    from services.ai.gemini_service import get_gemini_service
    AI_AVAILABLE = True
except ImportError:
    try:
        from services.ai.claude_service import get_claude_service
        from services.ai.gemini_service import get_gemini_service
        AI_AVAILABLE = True
    except ImportError:
        AI_AVAILABLE = False


class ClaimViewSet(ReadOnlyModelViewSet):
    """List and retrieve claims for a case."""
    serializer_class = ClaimSerializer
    
    def get_queryset(self):
        case_id = self.request.query_params.get('case_id')
        qs = Claim.objects.select_related('document').all()
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs


class TimelineEventViewSet(ReadOnlyModelViewSet):
    """List and retrieve timeline events for a case."""
    serializer_class = TimelineEventSerializer
    
    def get_queryset(self):
        case_id = self.request.query_params.get('case_id')
        qs = TimelineEvent.objects.select_related('source_document').all()
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs


class BiasIndicatorViewSet(ReadOnlyModelViewSet):
    """List and retrieve bias indicators for a case."""
    serializer_class = BiasIndicatorSerializer
    
    def get_queryset(self):
        case_id = self.request.query_params.get('case_id')
        qs = BiasIndicator.objects.select_related('document').all()
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs


class CompetingClaimViewSet(ReadOnlyModelViewSet):
    """List contradictions between claims."""
    serializer_class = CompetingClaimSerializer
    
    def get_queryset(self):
        case_id = self.request.query_params.get('case_id')
        qs = CompetingClaim.objects.select_related('claim_a', 'claim_b').all()
        if case_id:
            qs = qs.filter(claim_a__case_id=case_id)
        return qs


class AnalysisRunViewSet(ReadOnlyModelViewSet):
    """List analysis runs with optional case filtering."""
    serializer_class = AnalysisRunSerializer

    def get_queryset(self):
        qs = AnalysisRun.objects.select_related('case').all()
        case_id = self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs.order_by('-created_at')


class DocumentAnalysisView(APIView):
    """POST /api/documents/<uuid:doc_id>/analyze - Run AI analysis on document."""

    def post(self, request, doc_id):
        if not AI_AVAILABLE:
            return Response(
                {"detail": "AI services not available (check requirements)"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        doc = get_object_or_404(Document, pk=doc_id)
        if not doc.full_text:
            return Response(
                {"detail": "Document has no extracted text"}, 
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        try:
            # Sync for single doc analysis for now
            import asyncio
            gemini = get_gemini_service()
            analysis = asyncio.run(gemini.analyze_document(doc.full_text, doc_type=doc.doc_type))
            return Response({"analysis": analysis, "document_id": str(doc_id)})
        except Exception as e:
            return Response(
                {"detail": f"Analysis failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CaseAnalysisView(APIView):
    """POST /api/cases/<uuid:case_id>/analyze - Trigger full case analysis."""

    def post(self, request, case_id):
        if not AI_AVAILABLE:
            return Response(
                {"detail": "AI services not available"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        docs = Document.objects.filter(case_id=case_id, full_text__isnull=False)
        if not docs.exists():
            return Response(
                {"detail": "No documents with text found for this case"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Create AnalysisRun
        run = AnalysisRun.objects.create(
            id=uuid.uuid4(),
            case_id=case_id,
            run_type='full_analysis',
            status='pending',
            model_used='gemini-pro', # default
            total_tokens=0
        )
        
        # Start background task
        start_analysis_task(run.id)
        
        return Response({
            "analysis_run_id": str(run.id),
            "status": "pending",
            "message": "Analysis started in background"
        }, status=status.HTTP_202_ACCEPTED)


class CaseStatsView(APIView):
    """GET /api/cases/<uuid:case_id>/stats - Get case statistics."""

    def get(self, request, case_id):
        claims_count = Claim.objects.filter(case_id=case_id).count()
        events_count = TimelineEvent.objects.filter(case_id=case_id).count()
        biases_count = BiasIndicator.objects.filter(case_id=case_id).count()
        docs_count = Document.objects.filter(case_id=case_id).count()
        contradictions_count = CompetingClaim.objects.filter(claim_a__case_id=case_id).count()
        
        return Response({
            "case_id": str(case_id),
            "documents": docs_count,
            "claims": claims_count,
            "timeline_events": events_count,
            "bias_indicators": biases_count,
            "contradictions": contradictions_count,
        })
