"""
Serializers for Documents API
"""
from rest_framework import serializers
from .models import Document, Professional, ProfessionalCapacity, DocumentType


class DocumentSerializer(serializers.ModelSerializer):
    """Full document serializer with analysis stats."""
    doc_type_display = serializers.CharField(source='get_doc_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'case', 'filename', 'original_filename',
            'file_path', 'file_size', 'mime_type',
            'doc_type', 'doc_type_display', 'title',
            'date_filed', 'author', 'author_role', 'organisation',
            'status', 'status_display', 'processing_error', 'processed_at',
            'page_count', 'word_count',
            'claim_count', 'bias_signal_count',
            'created_at', 'updated_at',
            'metadata'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'processed_at',
            'claim_count', 'bias_signal_count', 'word_count'
        ]


class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for document lists."""
    doc_type_display = serializers.CharField(source='get_doc_type_display', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'filename', 'doc_type', 'doc_type_display',
            'date_filed', 'author', 'status',
            'claim_count', 'bias_signal_count',
            'created_at'
        ]


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload."""
    file = serializers.FileField()
    doc_type = serializers.ChoiceField(
        choices=DocumentType.choices,
        default=DocumentType.OTHER
    )
    title = serializers.CharField(max_length=500, required=False, allow_blank=True)
    date_filed = serializers.DateField(required=False, allow_null=True)
    author = serializers.CharField(max_length=255, required=False, allow_blank=True)
    author_role = serializers.CharField(max_length=100, required=False, allow_blank=True)
    organisation = serializers.CharField(max_length=255, required=False, allow_blank=True)


class DocumentContentSerializer(serializers.ModelSerializer):
    """Serializer for document with full text content."""
    
    class Meta:
        model = Document
        fields = [
            'id', 'filename', 'doc_type', 'content',
            'page_count', 'word_count'
        ]


class ProfessionalSerializer(serializers.ModelSerializer):
    """Serializer for Professional model."""
    
    class Meta:
        model = Professional
        fields = [
            'id', 'case', 'name', 'title', 'qualifications',
            'role', 'organisation', 'email', 'phone',
            'document_count', 'claim_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'document_count', 'claim_count']


class ProfessionalCapacitySerializer(serializers.ModelSerializer):
    """Serializer for ProfessionalCapacity model."""
    professional_name = serializers.CharField(source='professional.name', read_only=True)
    document_filename = serializers.CharField(source='document.filename', read_only=True)
    
    class Meta:
        model = ProfessionalCapacity
        fields = [
            'id', 'professional', 'professional_name',
            'document', 'document_filename',
            'capacity', 'is_author', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

