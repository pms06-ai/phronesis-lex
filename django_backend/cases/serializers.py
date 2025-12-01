"""
Serializers for Cases API
"""
from rest_framework import serializers
from .models import Case, CaseNote


class CaseSerializer(serializers.ModelSerializer):
    """Full case serializer with analysis stats."""
    case_type_display = serializers.CharField(source='get_case_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    court_level_display = serializers.CharField(source='get_court_level_display', read_only=True)
    
    class Meta:
        model = Case
        fields = [
            'id', 'reference', 'title',
            'case_type', 'case_type_display',
            'court', 'court_level', 'court_level_display', 'region',
            'status', 'status_display',
            'filing_date', 'next_hearing_date', 'final_hearing_date',
            'applicants', 'respondents', 'children',
            'description', 'key_issues',
            'document_count', 'claim_count',
            'contradiction_count', 'bias_signal_count',
            'created_at', 'updated_at',
            'metadata'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'document_count', 'claim_count',
            'contradiction_count', 'bias_signal_count'
        ]


class CaseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for case lists."""
    case_type_display = serializers.CharField(source='get_case_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Case
        fields = [
            'id', 'reference', 'title',
            'case_type', 'case_type_display',
            'status', 'status_display',
            'document_count', 'claim_count',
            'contradiction_count', 'next_hearing_date',
            'created_at'
        ]


class CaseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new case."""
    
    class Meta:
        model = Case
        fields = [
            'reference', 'title', 'case_type',
            'court', 'court_level', 'region',
            'filing_date', 'next_hearing_date',
            'applicants', 'respondents', 'children',
            'description', 'key_issues'
        ]
    
    def validate_reference(self, value):
        if Case.objects.filter(reference=value).exists():
            raise serializers.ValidationError("A case with this reference already exists")
        return value


class CaseNoteSerializer(serializers.ModelSerializer):
    """Serializer for case notes."""
    
    class Meta:
        model = CaseNote
        fields = [
            'id', 'case', 'title', 'content',
            'note_type', 'priority',
            'is_pinned', 'is_resolved',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
