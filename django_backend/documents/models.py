"""
Document Models for Phronesis LEX
Handles document storage, metadata, and processing state.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator


class DocumentType(models.TextChoices):
    """Types of legal documents in UK Family Court proceedings."""
    SECTION_7_REPORT = 'section_7_report', 'Section 7 Report (Welfare)'
    SECTION_37_REPORT = 'section_37_report', 'Section 37 Report'
    PSYCHOLOGICAL_REPORT = 'psychological_report', 'Psychological Assessment'
    SOCIAL_WORK_REPORT = 'social_work_report', 'Social Work Assessment'
    CAFCASS_ANALYSIS = 'cafcass_analysis', 'CAFCASS Analysis'
    WITNESS_STATEMENT = 'witness_statement', 'Witness Statement'
    EXPERT_REPORT = 'expert_report', 'Expert Report'
    POSITION_STATEMENT = 'position_statement', 'Position Statement'
    SKELETON_ARGUMENT = 'skeleton_argument', 'Skeleton Argument'
    COURT_ORDER = 'court_order', 'Court Order'
    JUDGMENT = 'judgment', 'Judgment'
    APPLICATION = 'application', 'Application'
    POLICE_DISCLOSURE = 'police_disclosure', 'Police Disclosure'
    MEDICAL_RECORDS = 'medical_records', 'Medical Records'
    SCHOOL_RECORDS = 'school_records', 'School Records'
    CORRESPONDENCE = 'correspondence', 'Correspondence'
    OTHER = 'other', 'Other'


class ProcessingStatus(models.TextChoices):
    """Document processing pipeline status."""
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    NEEDS_REVIEW = 'needs_review', 'Needs Review'


class Document(models.Model):
    """
    A legal document in a case.
    
    Documents go through a processing pipeline:
    1. Upload → 2. Text Extraction → 3. Claim Extraction → 4. Analysis
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    
    # File metadata
    filename = models.CharField(max_length=255, db_index=True)
    original_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    file_size = models.BigIntegerField(default=0, help_text="Size in bytes")
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    
    # Document metadata
    doc_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
        db_index=True
    )
    title = models.CharField(max_length=500, blank=True, null=True)
    date_filed = models.DateField(blank=True, null=True, db_index=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    author_role = models.CharField(max_length=100, blank=True, null=True)
    organisation = models.CharField(max_length=255, blank=True, null=True)
    
    # Processing state
    status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        db_index=True
    )
    processing_error = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    # Content
    content = models.TextField(blank=True, null=True, help_text="Extracted text content")
    page_count = models.IntegerField(default=0)
    word_count = models.IntegerField(default=0)
    
    # Analysis summary (cached for performance)
    claim_count = models.IntegerField(default=0)
    bias_signal_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional metadata as JSON
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-date_filed', '-created_at']
        indexes = [
            models.Index(fields=['case', 'doc_type']),
            models.Index(fields=['case', 'status']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"{self.filename} ({self.doc_type})"
    
    def mark_completed(self):
        """Mark document processing as complete."""
        self.status = ProcessingStatus.COMPLETED
        self.processed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error: str):
        """Mark document processing as failed."""
        self.status = ProcessingStatus.FAILED
        self.processing_error = error
        self.save()


class Professional(models.Model):
    """
    A professional involved in a case (social worker, guardian, expert, etc.)
    Used for entity resolution and attribution tracking.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='professionals'
    )
    
    # Identity
    name = models.CharField(max_length=255, db_index=True)
    title = models.CharField(max_length=100, blank=True, null=True)  # Mr, Ms, Dr, etc.
    qualifications = models.CharField(max_length=500, blank=True, null=True)
    
    # Role
    role = models.CharField(max_length=100, db_index=True)
    organisation = models.CharField(max_length=255, blank=True, null=True)
    
    # Contact (optional)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    
    # Analysis metadata
    document_count = models.IntegerField(default=0)
    claim_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'professionals'
        ordering = ['name']
        unique_together = ['case', 'name', 'role']
    
    def __str__(self):
        return f"{self.name} ({self.role})"


class ProfessionalCapacity(models.Model):
    """
    A professional's capacity/role in a specific document.
    Tracks who said what in which document with what authority.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name='capacities'
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='professional_capacities'
    )
    
    capacity = models.CharField(max_length=100, help_text="Role in this document")
    is_author = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'professional_capacities'
        unique_together = ['professional', 'document', 'capacity']
    
    def __str__(self):
        return f"{self.professional.name} as {self.capacity} in {self.document.filename}"

