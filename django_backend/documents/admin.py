"""
Admin configuration for Documents app.
"""
from django.contrib import admin
from .models import Document, Professional, ProfessionalCapacity


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'filename', 'case', 'doc_type', 'author',
        'status', 'date_filed', 'claim_count', 'created_at'
    ]
    list_filter = ['status', 'doc_type']
    search_fields = ['filename', 'title', 'author', 'case__reference']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    raw_id_fields = ['case']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'processed_at',
        'claim_count', 'bias_signal_count', 'word_count'
    ]
    
    fieldsets = [
        ('File Information', {
            'fields': [
                'id', 'case', 'filename', 'original_filename',
                'file_path', 'file_size', 'mime_type'
            ]
        }),
        ('Document Metadata', {
            'fields': [
                'doc_type', 'title', 'date_filed',
                'author', 'author_role', 'organisation'
            ]
        }),
        ('Processing Status', {
            'fields': ['status', 'processing_error', 'processed_at']
        }),
        ('Content & Analysis', {
            'fields': [
                'page_count', 'word_count',
                'claim_count', 'bias_signal_count'
            ]
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'organisation', 'case', 'document_count', 'claim_count']
    list_filter = ['role']
    search_fields = ['name', 'organisation', 'case__reference']
    
    raw_id_fields = ['case']


@admin.register(ProfessionalCapacity)
class ProfessionalCapacityAdmin(admin.ModelAdmin):
    list_display = ['professional', 'document', 'capacity', 'is_author']
    list_filter = ['is_author', 'capacity']
    search_fields = ['professional__name', 'document__filename']
    
    raw_id_fields = ['professional', 'document']

