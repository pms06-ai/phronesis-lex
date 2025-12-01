"""
Case Models for Phronesis LEX
"""
import uuid
from django.db import models
from django.utils import timezone


class CaseType(models.TextChoices):
    """Types of UK Family Court cases."""
    PRIVATE_LAW = 'private_law', 'Private Law (Child Arrangements)'
    PUBLIC_LAW = 'public_law', 'Public Law (Care Proceedings)'
    ADOPTION = 'adoption', 'Adoption'
    FINANCIAL = 'financial', 'Financial Remedies'
    DOMESTIC_ABUSE = 'domestic_abuse', 'Domestic Abuse'
    SPECIAL_GUARDIANSHIP = 'special_guardianship', 'Special Guardianship'
    OTHER = 'other', 'Other'


class CaseStatus(models.TextChoices):
    """Case lifecycle status."""
    ACTIVE = 'active', 'Active'
    PENDING = 'pending', 'Pending'
    CLOSED = 'closed', 'Closed'
    ARCHIVED = 'archived', 'Archived'


class CourtLevel(models.TextChoices):
    """UK Court hierarchy."""
    FAMILY_COURT = 'family_court', 'Family Court'
    HIGH_COURT = 'high_court', 'High Court (Family Division)'
    COURT_OF_APPEAL = 'court_of_appeal', 'Court of Appeal'
    SUPREME_COURT = 'supreme_court', 'Supreme Court'


class Case(models.Model):
    """
    A family law case being analyzed.
    
    The central entity around which all documents, claims,
    and analysis are organized.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Case identification
    reference = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Court case reference number"
    )
    title = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Case title (e.g., 'Re A (Children)')"
    )
    
    # Classification
    case_type = models.CharField(
        max_length=30,
        choices=CaseType.choices,
        default=CaseType.PRIVATE_LAW,
        db_index=True
    )
    court = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Specific court name"
    )
    court_level = models.CharField(
        max_length=30,
        choices=CourtLevel.choices,
        default=CourtLevel.FAMILY_COURT
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Court region/circuit"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=CaseStatus.choices,
        default=CaseStatus.ACTIVE,
        db_index=True
    )
    
    # Key dates
    filing_date = models.DateField(blank=True, null=True)
    next_hearing_date = models.DateField(blank=True, null=True)
    final_hearing_date = models.DateField(blank=True, null=True)
    
    # Parties (stored as JSON for flexibility)
    applicants = models.JSONField(
        default=list,
        blank=True,
        help_text="List of applicant details"
    )
    respondents = models.JSONField(
        default=list,
        blank=True,
        help_text="List of respondent details"
    )
    children = models.JSONField(
        default=list,
        blank=True,
        help_text="List of children (anonymized)"
    )
    
    # Case summary
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Brief case description"
    )
    key_issues = models.JSONField(
        default=list,
        blank=True,
        help_text="List of key issues in dispute"
    )
    
    # Analysis state (cached counts for performance)
    document_count = models.IntegerField(default=0)
    claim_count = models.IntegerField(default=0)
    contradiction_count = models.IntegerField(default=0)
    bias_signal_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'cases'
        ordering = ['-created_at']
        verbose_name_plural = 'cases'
        indexes = [
            models.Index(fields=['status', 'case_type']),
            models.Index(fields=['reference']),
        ]
    
    def __str__(self):
        return f"{self.reference} - {self.title or 'Untitled'}"
    
    def update_counts(self):
        """Update cached analysis counts."""
        self.document_count = self.documents.count()
        self.claim_count = self.claims.count()
        self.contradiction_count = self.contradictions.count()
        self.bias_signal_count = self.bias_signals.count()
        self.save(update_fields=[
            'document_count', 'claim_count',
            'contradiction_count', 'bias_signal_count'
        ])


class CaseNote(models.Model):
    """Notes and annotations on a case."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    note_type = models.CharField(
        max_length=50,
        default='general',
        choices=[
            ('general', 'General'),
            ('analysis', 'Analysis'),
            ('strategy', 'Strategy'),
            ('question', 'Question'),
            ('action', 'Action Required'),
        ]
    )
    priority = models.CharField(
        max_length=20,
        default='normal',
        choices=[
            ('low', 'Low'),
            ('normal', 'Normal'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ]
    )
    
    is_pinned = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'case_notes'
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.case.reference})"
