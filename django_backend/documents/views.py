"""
API Views for Documents
"""
import os
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import Document, Professional, ProfessionalCapacity
from .serializers import (
    DocumentSerializer, DocumentListSerializer,
    DocumentUploadSerializer, DocumentContentSerializer,
    ProfessionalSerializer, ProfessionalCapacitySerializer
)
from django_backend.cases.models import Case

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    """CRUD API for documents."""
    queryset = Document.objects.select_related('case')
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentListSerializer
        if self.action == 'upload':
            return DocumentUploadSerializer
        if self.action == 'content':
            return DocumentContentSerializer
        return DocumentSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        case_id = self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)
        
        doc_type = self.request.query_params.get('doc_type')
        if doc_type:
            qs = qs.filter(doc_type=doc_type)
        
        doc_status = self.request.query_params.get('status')
        if doc_status:
            qs = qs.filter(status=doc_status)
        
        author = self.request.query_params.get('author')
        if author:
            qs = qs.filter(author__icontains=author)
        
        return qs
    
    @action(detail=True, methods=['get'])
    def content(self, request, pk=None):
        """Get document with full text content."""
        document = self.get_object()
        serializer = DocumentContentSerializer(document)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload a new document."""
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        case_id = request.data.get('case_id')
        if not case_id:
            return Response(
                {'error': 'case_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        case = get_object_or_404(Case, pk=case_id)
        uploaded_file = serializer.validated_data['file']
        
        # Create upload directory
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'documents', str(case_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, uploaded_file.name)
        with open(file_path, 'wb+') as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)
        
        # Create document record
        document = Document.objects.create(
            case=case,
            filename=uploaded_file.name,
            original_filename=uploaded_file.name,
            file_path=file_path,
            file_size=uploaded_file.size,
            mime_type=uploaded_file.content_type,
            doc_type=serializer.validated_data.get('doc_type', 'other'),
            title=serializer.validated_data.get('title'),
            date_filed=serializer.validated_data.get('date_filed'),
            author=serializer.validated_data.get('author'),
            author_role=serializer.validated_data.get('author_role'),
            organisation=serializer.validated_data.get('organisation'),
            status='pending'
        )
        
        return Response(
            DocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Trigger analysis for a document."""
        document = self.get_object()
        
        if document.status == 'processing':
            return Response(
                {'error': 'Document is already being processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Queue document for analysis
        # For now, just update status
        document.status = 'processing'
        document.save()
        
        return Response({
            'message': 'Document queued for analysis',
            'document_id': str(document.id)
        })


class CaseDocumentViewSet(viewsets.ModelViewSet):
    """Documents nested under cases."""
    queryset = Document.objects.select_related('case')
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentListSerializer
        return DocumentSerializer
    
    def get_queryset(self):
        case_pk = self.kwargs.get('case_pk')
        return super().get_queryset().filter(case_id=case_pk)
    
    def perform_create(self, serializer):
        case_pk = self.kwargs.get('case_pk')
        case = get_object_or_404(Case, pk=case_pk)
        serializer.save(case=case)
    
    @action(detail=False, methods=['get'])
    def stats(self, request, case_pk=None):
        """Get document statistics for a case."""
        documents = Document.objects.filter(case_id=case_pk)
        
        stats = {
            'total': documents.count(),
            'by_type': {},
            'by_status': {},
            'total_claims': 0,
            'total_pages': 0,
            'total_words': 0,
        }
        
        for doc in documents:
            stats['by_type'][doc.doc_type] = stats['by_type'].get(doc.doc_type, 0) + 1
            stats['by_status'][doc.status] = stats['by_status'].get(doc.status, 0) + 1
            stats['total_claims'] += doc.claim_count
            stats['total_pages'] += doc.page_count
            stats['total_words'] += doc.word_count
        
        return Response(stats)


class ProfessionalViewSet(viewsets.ModelViewSet):
    """CRUD API for professionals."""
    queryset = Professional.objects.select_related('case')
    serializer_class = ProfessionalSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        case_id = self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)
        
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role__icontains=role)
        
        return qs


class ProfessionalCapacityViewSet(viewsets.ModelViewSet):
    """CRUD API for professional capacities."""
    queryset = ProfessionalCapacity.objects.select_related('professional', 'document')
    serializer_class = ProfessionalCapacitySerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        professional_id = self.request.query_params.get('professional_id')
        if professional_id:
            qs = qs.filter(professional_id=professional_id)
        
        document_id = self.request.query_params.get('document_id')
        if document_id:
            qs = qs.filter(document_id=document_id)
        
        return qs

