"""
Admin configuration for Cases app.
"""
from django.contrib import admin
from .models import Case, CaseNote


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'title', 'case_type', 'status',
        'document_count', 'claim_count', 'contradiction_count',
        'next_hearing_date', 'created_at'
    ]
    list_filter = ['status', 'case_type', 'court_level']
    search_fields = ['reference', 'title', 'description']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    readonly_fields = [
        'id', 'created_at', 'updated_at',
        'document_count', 'claim_count',
        'contradiction_count', 'bias_signal_count'
    ]
    
    fieldsets = [
        ('Identification', {
            'fields': ['id', 'reference', 'title']
        }),
        ('Classification', {
            'fields': ['case_type', 'court', 'court_level', 'region', 'status']
        }),
        ('Key Dates', {
            'fields': ['filing_date', 'next_hearing_date', 'final_hearing_date']
        }),
        ('Parties', {
            'fields': ['applicants', 'respondents', 'children'],
            'classes': ['collapse']
        }),
        ('Details', {
            'fields': ['description', 'key_issues'],
            'classes': ['collapse']
        }),
        ('Analysis Statistics', {
            'fields': [
                'document_count', 'claim_count',
                'contradiction_count', 'bias_signal_count'
            ]
        }),
        ('Metadata', {
            'fields': ['metadata', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(CaseNote)
class CaseNoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'case', 'note_type', 'priority', 'is_pinned', 'is_resolved', 'created_at']
    list_filter = ['note_type', 'priority', 'is_pinned', 'is_resolved']
    search_fields = ['title', 'content', 'case__reference']
    date_hierarchy = 'created_at'
    
    raw_id_fields = ['case']
