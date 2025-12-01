"""
Serializers for Analysis API
Comprehensive serialization with validation for all analysis models.
"""
from rest_framework import serializers
from .models import (
    Claim, Contradiction, BiasSignal, TimelineEvent,
    ToulminArgument, Entity, LegalRule, AnalysisRun, BiasBaseline
)


class ClaimSerializer(serializers.ModelSerializer):
    """Serializer for Claim model with related document info."""
    source_document = serializers.CharField(source='document.filename', read_only=True)
    document_type = serializers.CharField(source='document.doc_type', read_only=True)
    
    class Meta:
        model = Claim
        fields = [
            'id', 'case', 'document', 'source_document', 'document_type',
            'claim_type', 'claim_text', 'source_quote',
            'subject', 'predicate', 'object_value',
            'modality', 'polarity', 'certainty', 'certainty_markers',
            'asserted_by', 'time_expression', 'time_start', 'time_end',
            'page_number', 'paragraph_number',
            'confidence', 'extractor_model',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_certainty(self, value):
        if value < 0 or value > 1:
            raise serializers.ValidationError("Certainty must be between 0 and 1")
        return value


class ClaimCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating claims (typically from AI extraction)."""
    
    class Meta:
        model = Claim
        fields = [
            'case', 'document',
            'claim_type', 'claim_text', 'source_quote',
            'subject', 'predicate', 'object_value',
            'modality', 'polarity', 'certainty', 'certainty_markers',
            'asserted_by', 'time_expression',
            'page_number', 'paragraph_number',
            'confidence', 'extractor_model', 'extraction_prompt_hash'
        ]


class ContradictionSerializer(serializers.ModelSerializer):
    """Serializer for Contradiction model with full claim details."""
    # Claim A details
    claim_a_text = serializers.CharField(source='claim_a.claim_text', read_only=True)
    claim_a_document_id = serializers.UUIDField(source='claim_a.document.id', read_only=True)
    claim_a_document_name = serializers.CharField(source='claim_a.document.filename', read_only=True)
    claim_a_page = serializers.IntegerField(source='claim_a.page_number', read_only=True, allow_null=True)
    claim_a_author = serializers.CharField(source='claim_a.asserted_by', read_only=True, allow_null=True)
    
    # Claim B details
    claim_b_text = serializers.CharField(source='claim_b.claim_text', read_only=True)
    claim_b_document_id = serializers.UUIDField(source='claim_b.document.id', read_only=True)
    claim_b_document_name = serializers.CharField(source='claim_b.document.filename', read_only=True)
    claim_b_page = serializers.IntegerField(source='claim_b.page_number', read_only=True, allow_null=True)
    claim_b_author = serializers.CharField(source='claim_b.asserted_by', read_only=True, allow_null=True)
    
    class Meta:
        model = Contradiction
        fields = [
            'id', 'case', 'contradiction_type', 'severity',
            'claim_a', 'claim_a_text', 'claim_a_document_id', 'claim_a_document_name',
            'claim_a_page', 'claim_a_author',
            'claim_b', 'claim_b_text', 'claim_b_document_id', 'claim_b_document_name',
            'claim_b_page', 'claim_b_author',
            'description', 'legal_significance', 'recommended_action',
            'confidence', 'semantic_similarity',
            'temporal_conflict', 'same_author',
            'resolved', 'resolution_note', 'resolved_at', 'resolved_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContradictionResolveSerializer(serializers.Serializer):
    """Serializer for resolving contradictions."""
    note = serializers.CharField(required=True, min_length=10)
    
    def validate_note(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Resolution note must be at least 10 characters")
        return value.strip()


class BiasSignalSerializer(serializers.ModelSerializer):
    """Serializer for BiasSignal model."""
    document_name = serializers.CharField(source='document.filename', read_only=True)
    document_type = serializers.CharField(source='document.doc_type', read_only=True)
    
    class Meta:
        model = BiasSignal
        fields = [
            'id', 'case', 'document', 'document_name', 'document_type',
            'signal_type', 'severity',
            'metric_value', 'baseline_mean', 'baseline_std',
            'z_score', 'p_value', 'direction',
            'description', 'baseline_id', 'baseline_source',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TimelineEventSerializer(serializers.ModelSerializer):
    """Serializer for TimelineEvent model."""
    source_document_id = serializers.UUIDField(source='document.id', read_only=True)
    source_document_name = serializers.CharField(source='document.filename', read_only=True)
    
    class Meta:
        model = TimelineEvent
        fields = [
            'id', 'case', 'document', 'source_document_id', 'source_document_name',
            'event_date', 'event_type', 'description', 'significance',
            'verified', 'conflicting_events',
            'participants', 'location',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ToulminArgumentSerializer(serializers.ModelSerializer):
    """Serializer for ToulminArgument model."""
    warrant_rule_id = serializers.CharField(source='warrant_rule.rule_id', read_only=True, allow_null=True)
    warrant_rule_name = serializers.CharField(source='warrant_rule.short_name', read_only=True, allow_null=True)
    supporting_claim_ids = serializers.PrimaryKeyRelatedField(
        source='supporting_claims',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = ToulminArgument
        fields = [
            'id', 'case',
            'claim_text', 'grounds', 'warrant',
            'warrant_rule_id', 'warrant_rule_name',
            'backing', 'qualifier', 'rebuttal',
            'falsifiability_conditions', 'missing_evidence', 'alternative_explanations',
            'confidence_lower', 'confidence_upper', 'confidence_mean',
            'supporting_claim_ids',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class EntitySerializer(serializers.ModelSerializer):
    """Serializer for Entity model."""
    
    class Meta:
        model = Entity
        fields = [
            'id', 'case', 'canonical_name', 'entity_type',
            'aliases', 'roles', 'organisation',
            'claim_count', 'sentiment_score',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class LegalRuleSerializer(serializers.ModelSerializer):
    """Serializer for LegalRule model."""
    
    class Meta:
        model = LegalRule
        fields = ['rule_id', 'short_name', 'full_citation', 'text', 'category', 'keywords']


class BiasBaselineSerializer(serializers.ModelSerializer):
    """Serializer for BiasBaseline model."""
    
    class Meta:
        model = BiasBaseline
        fields = ['baseline_id', 'doc_type', 'metric', 'corpus_size', 'mean', 'std_dev', 'source', 'last_calibrated']


class AnalysisRunSerializer(serializers.ModelSerializer):
    """Serializer for AnalysisRun model."""
    duration_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = AnalysisRun
        fields = [
            'id', 'case', 'run_type', 'status',
            'started_at', 'completed_at', 'duration_seconds',
            'documents_analyzed', 'claims_extracted',
            'contradictions_found', 'biases_detected',
            'error_message',
            'model_used', 'total_tokens', 'estimated_cost',
            'progress_percent', 'progress_message'
        ]
        read_only_fields = ['id', 'started_at', 'duration_seconds']
    
    def get_duration_seconds(self, obj):
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None


# Summary serializers for aggregated views

class ContradictionSummarySerializer(serializers.Serializer):
    """Serializer for contradiction summary statistics."""
    total = serializers.IntegerField()
    by_type = serializers.DictField(child=serializers.IntegerField())
    by_severity = serializers.DictField(child=serializers.IntegerField())
    unresolved = serializers.IntegerField()
    self_contradictions = serializers.IntegerField()
    most_severe = ContradictionSerializer(many=True, read_only=True)


class BiasReportSerializer(serializers.Serializer):
    """Serializer for comprehensive bias report."""
    total_signals = serializers.IntegerField()
    by_severity = serializers.DictField(child=serializers.IntegerField())
    by_type = serializers.DictField(child=serializers.IntegerField())
    by_document = serializers.DictField(child=serializers.IntegerField())
    statistical_summary = serializers.DictField()
    signals = BiasSignalSerializer(many=True)


class CaseStatsSerializer(serializers.Serializer):
    """Serializer for case statistics."""
    documents = serializers.IntegerField()
    claims = serializers.IntegerField()
    timeline_events = serializers.IntegerField()
    bias_indicators = serializers.IntegerField()
    contradictions = serializers.IntegerField()
    entities = serializers.IntegerField()
    arguments = serializers.IntegerField()
    
    # Breakdown stats
    claims_by_type = serializers.DictField(child=serializers.IntegerField(), required=False)
    claims_by_modality = serializers.DictField(child=serializers.IntegerField(), required=False)
    contradictions_by_type = serializers.DictField(child=serializers.IntegerField(), required=False)


class GenerateArgumentRequestSerializer(serializers.Serializer):
    """Serializer for argument generation request."""
    finding_type = serializers.ChoiceField(
        choices=[
            ('welfare', 'Welfare Assessment'),
            ('threshold', 'Threshold Criteria'),
            ('credibility', 'Credibility Finding'),
            ('expert', 'Expert Opinion'),
            ('bias', 'Bias Finding'),
        ],
        default='welfare'
    )
    claim_text = serializers.CharField(required=False, allow_blank=True)

