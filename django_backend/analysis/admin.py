"""
Admin configuration for Analysis app.
"""
from django.contrib import admin
from .models import (
    Claim, Contradiction, BiasSignal, TimelineEvent,
    ToulminArgument, Entity, LegalRule, AnalysisRun, BiasBaseline
)


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = [
        'claim_text_short', 'case', 'claim_type', 'modality',
        'certainty', 'asserted_by', 'created_at'
    ]
    list_filter = ['claim_type', 'modality', 'polarity']
    search_fields = ['claim_text', 'asserted_by', 'subject', 'case__reference']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    raw_id_fields = ['case', 'document', 'subject_entity', 'asserted_by_entity']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def claim_text_short(self, obj):
        return obj.claim_text[:80] + '...' if len(obj.claim_text) > 80 else obj.claim_text
    claim_text_short.short_description = 'Claim'


@admin.register(Contradiction)
class ContradictionAdmin(admin.ModelAdmin):
    list_display = [
        'description_short', 'case', 'contradiction_type', 'severity',
        'same_author', 'resolved', 'created_at'
    ]
    list_filter = ['contradiction_type', 'severity', 'resolved', 'same_author']
    search_fields = ['description', 'case__reference']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    raw_id_fields = ['case', 'claim_a', 'claim_b']
    readonly_fields = ['id', 'created_at', 'updated_at', 'resolved_at']
    
    def description_short(self, obj):
        return obj.description[:60] + '...' if len(obj.description) > 60 else obj.description
    description_short.short_description = 'Description'
    
    fieldsets = [
        ('Identification', {
            'fields': ['id', 'case']
        }),
        ('Classification', {
            'fields': ['contradiction_type', 'severity']
        }),
        ('Claims', {
            'fields': ['claim_a', 'claim_b']
        }),
        ('Analysis', {
            'fields': [
                'description', 'legal_significance', 'recommended_action',
                'confidence', 'semantic_similarity',
                'temporal_conflict', 'same_author'
            ]
        }),
        ('Resolution', {
            'fields': ['resolved', 'resolution_note', 'resolved_at', 'resolved_by']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(BiasSignal)
class BiasSignalAdmin(admin.ModelAdmin):
    list_display = [
        'signal_type', 'case', 'document', 'severity',
        'z_score', 'direction', 'created_at'
    ]
    list_filter = ['signal_type', 'severity', 'direction']
    search_fields = ['description', 'case__reference', 'document__filename']
    ordering = ['-z_score']
    
    raw_id_fields = ['case', 'document']
    readonly_fields = ['id', 'created_at']


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = [
        'event_date', 'event_type', 'description_short',
        'case', 'significance', 'verified'
    ]
    list_filter = ['event_type', 'significance', 'verified']
    search_fields = ['description', 'case__reference']
    date_hierarchy = 'event_date'
    ordering = ['event_date']
    
    raw_id_fields = ['case', 'document']
    readonly_fields = ['id', 'created_at']
    
    def description_short(self, obj):
        return obj.description[:60] + '...' if len(obj.description) > 60 else obj.description
    description_short.short_description = 'Description'


@admin.register(ToulminArgument)
class ToulminArgumentAdmin(admin.ModelAdmin):
    list_display = [
        'claim_text_short', 'case', 'qualifier',
        'confidence_mean', 'created_at'
    ]
    search_fields = ['claim_text', 'warrant', 'case__reference']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    raw_id_fields = ['case', 'warrant_rule']
    readonly_fields = ['id', 'created_at']
    filter_horizontal = ['supporting_claims']
    
    def claim_text_short(self, obj):
        return obj.claim_text[:60] + '...' if len(obj.claim_text) > 60 else obj.claim_text
    claim_text_short.short_description = 'Claim'


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = [
        'canonical_name', 'case', 'entity_type',
        'organisation', 'claim_count'
    ]
    list_filter = ['entity_type']
    search_fields = ['canonical_name', 'case__reference', 'organisation']
    ordering = ['canonical_name']
    
    raw_id_fields = ['case']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(LegalRule)
class LegalRuleAdmin(admin.ModelAdmin):
    list_display = ['rule_id', 'short_name', 'full_citation', 'category']
    list_filter = ['category']
    search_fields = ['rule_id', 'short_name', 'text', 'full_citation']
    ordering = ['category', 'short_name']
    
    filter_horizontal = ['related_rules']


@admin.register(AnalysisRun)
class AnalysisRunAdmin(admin.ModelAdmin):
    list_display = [
        'run_type', 'case', 'status',
        'claims_extracted', 'contradictions_found',
        'started_at', 'completed_at'
    ]
    list_filter = ['status', 'run_type']
    search_fields = ['case__reference']
    date_hierarchy = 'started_at'
    ordering = ['-started_at']
    
    raw_id_fields = ['case']
    readonly_fields = [
        'id', 'started_at', 'completed_at',
        'documents_analyzed', 'claims_extracted',
        'contradictions_found', 'biases_detected'
    ]


@admin.register(BiasBaseline)
class BiasBaselineAdmin(admin.ModelAdmin):
    list_display = ['baseline_id', 'doc_type', 'metric', 'mean', 'std_dev', 'corpus_size', 'source']
    list_filter = ['doc_type', 'metric', 'source']
    search_fields = ['baseline_id', 'doc_type']
    ordering = ['doc_type', 'metric']

