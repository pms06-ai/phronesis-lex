"""
Analysis Models for Phronesis LEX - FCIP v5.0

Comprehensive domain models for forensic case intelligence platform.
Follows UK Family Court proceedings terminology and legal standards.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


# =============================================================================
# ENUM CHOICES
# =============================================================================

class ClaimType(models.TextChoices):
    """Types of claims extracted from legal documents."""
    ASSERTION = 'assertion', 'Assertion'
    ALLEGATION = 'allegation', 'Allegation'
    FINDING = 'finding', 'Finding'
    CONCLUSION = 'conclusion', 'Conclusion'
    RECOMMENDATION = 'recommendation', 'Recommendation'
    OPINION = 'opinion', 'Opinion'
    OBSERVATION = 'observation', 'Observation'
    CONCERN = 'concern', 'Concern'
    SUBMISSION = 'submission', 'Submission'


class Modality(models.TextChoices):
    """Epistemic modality - how a claim is presented."""
    ASSERTED = 'asserted', 'Asserted (direct statement)'
    REPORTED = 'reported', 'Reported (attributed to someone)'
    ALLEGED = 'alleged', 'Alleged (contested/unproven)'
    DENIED = 'denied', 'Denied (negation)'
    HYPOTHETICAL = 'hypothetical', 'Hypothetical (conditional)'


class Polarity(models.TextChoices):
    """Polarity of a claim - affirmative or negative."""
    AFFIRM = 'affirm', 'Affirm'
    NEGATE = 'negate', 'Negate'


class Severity(models.TextChoices):
    """Severity levels for issues and signals."""
    CRITICAL = 'critical', 'Critical'
    HIGH = 'high', 'High'
    MEDIUM = 'medium', 'Medium'
    LOW = 'low', 'Low'
    INFO = 'info', 'Info'


class ContradictionType(models.TextChoices):
    """Types of contradictions between claims."""
    DIRECT = 'direct', 'Direct Contradiction'
    TEMPORAL = 'temporal', 'Temporal Impossibility'
    SELF = 'self', 'Self-Contradiction'
    MODALITY = 'modality', 'Modality Confusion'
    VALUE = 'value', 'Value Mismatch'
    ATTRIBUTION = 'attribution', 'Attribution Conflict'
    QUOTATION = 'quotation', 'Quotation Mismatch'
    OMISSION = 'omission', 'Material Omission'


class BiasType(models.TextChoices):
    """Types of statistical bias signals."""
    CERTAINTY_LANGUAGE = 'certainty_language', 'Certainty Language'
    NEGATIVE_ATTRIBUTION = 'negative_attribution', 'Negative Attribution'
    QUANTIFIER_EXTREMITY = 'quantifier_extremity', 'Quantifier Extremity'
    ATTRIBUTION_ASYMMETRY = 'attribution_asymmetry', 'Attribution Asymmetry'


class EntityType(models.TextChoices):
    """Types of entities in legal proceedings."""
    PERSON = 'person', 'Person'
    ORGANIZATION = 'organization', 'Organization'
    CHILD = 'child', 'Child'
    PARENT = 'parent', 'Parent'
    SOCIAL_WORKER = 'social_worker', 'Social Worker'
    GUARDIAN = 'guardian', 'Guardian'
    JUDGE = 'judge', 'Judge'
    PSYCHOLOGIST = 'psychologist', 'Psychologist'
    BARRISTER = 'barrister', 'Barrister'
    SOLICITOR = 'solicitor', 'Solicitor'
    EXPERT = 'expert', 'Expert'
    LOCAL_AUTHORITY = 'local_authority', 'Local Authority'
    CAFCASS = 'cafcass', 'CAFCASS'
    OTHER = 'other', 'Other'


class Significance(models.TextChoices):
    """Significance level for timeline events."""
    CRITICAL = 'critical', 'Critical'
    MAJOR = 'major', 'Major'
    ROUTINE = 'routine', 'Routine'
    MINOR = 'minor', 'Minor'


class RunStatus(models.TextChoices):
    """Status of analysis runs."""
    PENDING = 'pending', 'Pending'
    RUNNING = 'running', 'Running'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class RunType(models.TextChoices):
    """Types of analysis runs."""
    DOCUMENT = 'document', 'Document Analysis'
    CASE = 'case', 'Full Case Analysis'
    CONTRADICTION = 'contradiction', 'Contradiction Detection'
    BIAS = 'bias', 'Bias Detection'
    CLAIM_EXTRACTION = 'claim_extraction', 'Claim Extraction'


class RuleCategory(models.TextChoices):
    """Categories of legal rules."""
    WELFARE = 'welfare', 'Welfare'
    THRESHOLD = 'threshold', 'Threshold'
    EVIDENCE = 'evidence', 'Evidence'
    PROFESSIONAL = 'professional', 'Professional'
    PROCEDURAL = 'procedural', 'Procedural'


# =============================================================================
# BASE MODEL
# =============================================================================

class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields."""
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# =============================================================================
# CLAIMS
# =============================================================================

class Claim(TimeStampedModel):
    """
    An extracted claim from a document with epistemic annotation.
    
    Claims capture assertions, allegations, findings, etc. from legal documents
    with full metadata about modality (how it's stated), certainty, and attribution.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='claims'
    )
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='claims'
    )
    
    # Core content
    claim_type = models.CharField(
        max_length=30,
        choices=ClaimType.choices,
        default=ClaimType.ASSERTION,
        db_index=True
    )
    claim_text = models.TextField(help_text="The text of the claim")
    source_quote = models.TextField(
        blank=True,
        null=True,
        help_text="Exact quote from document"
    )
    
    # Subject-Predicate-Object structure
    subject = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text="Who/what the claim is about"
    )
    subject_entity = models.ForeignKey(
        'Entity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='claims_as_subject'
    )
    predicate = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The action or state being claimed"
    )
    predicate_category = models.CharField(max_length=100, blank=True, null=True)
    object_value = models.TextField(blank=True, null=True)
    
    # Epistemic stance
    modality = models.CharField(
        max_length=20,
        choices=Modality.choices,
        default=Modality.ASSERTED,
        db_index=True,
        help_text="How the claim is presented (asserted, alleged, etc.)"
    )
    polarity = models.CharField(
        max_length=10,
        choices=Polarity.choices,
        default=Polarity.AFFIRM
    )
    certainty = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Certainty score 0.0-1.0"
    )
    certainty_markers = models.JSONField(
        default=list,
        blank=True,
        help_text="Words indicating certainty level"
    )
    
    # Attribution
    asserted_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text="Who made this claim"
    )
    asserted_by_entity = models.ForeignKey(
        'Entity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='claims_asserted'
    )
    
    # Temporal context
    time_expression = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Time reference in the claim"
    )
    time_start = models.DateField(blank=True, null=True)
    time_end = models.DateField(blank=True, null=True)
    
    # Document location
    page_number = models.IntegerField(blank=True, null=True)
    paragraph_number = models.IntegerField(blank=True, null=True)
    
    # Extraction metadata
    confidence = models.FloatField(
        default=0.8,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Extraction confidence"
    )
    extractor_model = models.CharField(max_length=100, default='fcip_v5')
    extraction_prompt_hash = models.CharField(max_length=64, blank=True, null=True)
    
    class Meta:
        db_table = 'claims'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', 'claim_type']),
            models.Index(fields=['case', 'modality']),
            models.Index(fields=['document', 'page_number']),
            models.Index(fields=['asserted_by']),
        ]
    
    def __str__(self):
        return f"[{self.modality}] {self.claim_text[:60]}..."
    
    def clean(self):
        if self.certainty < 0 or self.certainty > 1:
            raise ValidationError({'certainty': 'Must be between 0 and 1'})


# =============================================================================
# CONTRADICTIONS
# =============================================================================

class Contradiction(TimeStampedModel):
    """
    A detected contradiction between two claims.
    
    Contradictions are identified through semantic analysis, temporal logic,
    and modality comparison. Self-contradictions are particularly significant
    under the Lucas direction.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='contradictions'
    )
    
    # Type and severity
    contradiction_type = models.CharField(
        max_length=30,
        choices=ContradictionType.choices,
        db_index=True
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM,
        db_index=True
    )
    
    # The two claims in conflict
    claim_a = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
        related_name='contradictions_as_a'
    )
    claim_b = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
        related_name='contradictions_as_b'
    )
    
    # Analysis
    description = models.TextField(
        help_text="Human-readable description of the contradiction"
    )
    legal_significance = models.TextField(
        blank=True,
        null=True,
        help_text="Legal implications and relevant case law"
    )
    recommended_action = models.TextField(
        blank=True,
        null=True,
        help_text="Suggested response or cross-examination approach"
    )
    
    # Metrics
    confidence = models.FloatField(
        default=0.8,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    semantic_similarity = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="How semantically similar the claims are"
    )
    
    # Flags
    temporal_conflict = models.BooleanField(
        default=False,
        help_text="Whether the contradiction involves timeline issues"
    )
    same_author = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Self-contradiction by same author"
    )
    
    # Resolution
    resolved = models.BooleanField(default=False, db_index=True)
    resolution_note = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'contradictions'
        ordering = [
            models.Case(
                models.When(severity='critical', then=0),
                models.When(severity='high', then=1),
                models.When(severity='medium', then=2),
                models.When(severity='low', then=3),
                default=4,
            ),
            '-created_at'
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['claim_a', 'claim_b'],
                name='unique_contradiction_pair'
            ),
            models.CheckConstraint(
                check=~models.Q(claim_a=models.F('claim_b')),
                name='claims_must_differ'
            )
        ]
    
    def __str__(self):
        return f"[{self.contradiction_type}] {self.severity}: {self.description[:50]}..."
    
    def save(self, *args, **kwargs):
        # Auto-detect self-contradiction
        if self.claim_a.asserted_by and self.claim_b.asserted_by:
            self.same_author = (
                self.claim_a.asserted_by.lower().strip() == 
                self.claim_b.asserted_by.lower().strip()
            )
            if self.same_author and self.contradiction_type != ContradictionType.SELF:
                self.contradiction_type = ContradictionType.SELF
        super().save(*args, **kwargs)


# =============================================================================
# BIAS SIGNALS
# =============================================================================

class BiasSignal(TimeStampedModel):
    """
    A statistical bias signal detected in document analysis.
    
    Uses z-score analysis comparing document language against corpus baselines
    for certainty language, negativity, and extreme quantifiers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='bias_signals'
    )
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='bias_signals'
    )
    
    # Signal type
    signal_type = models.CharField(
        max_length=50,
        choices=BiasType.choices,
        db_index=True
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM
    )
    
    # Statistical measures
    metric_value = models.FloatField(help_text="Observed metric value")
    baseline_mean = models.FloatField(help_text="Expected baseline mean")
    baseline_std = models.FloatField(help_text="Baseline standard deviation")
    z_score = models.FloatField(db_index=True, help_text="Z-score from baseline")
    p_value = models.FloatField(blank=True, null=True)
    direction = models.CharField(
        max_length=10,
        help_text="'higher' or 'lower' than expected"
    )
    
    # Human-readable
    description = models.TextField()
    
    # Baseline reference
    baseline_id = models.CharField(max_length=100, blank=True, null=True)
    baseline_source = models.CharField(
        max_length=50,
        default='estimated',
        help_text="'empirical', 'estimated', or 'calibrated'"
    )
    
    class Meta:
        db_table = 'bias_signals'
        ordering = ['-z_score']
        indexes = [
            models.Index(fields=['case', 'signal_type']),
            models.Index(fields=['document', 'signal_type']),
        ]
    
    def __str__(self):
        return f"[{self.signal_type}] z={self.z_score:.2f} ({self.severity})"


# =============================================================================
# TIMELINE EVENTS
# =============================================================================

class TimelineEvent(TimeStampedModel):
    """A temporal event extracted from case documents."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='timeline_events'
    )
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='timeline_events'
    )
    
    event_date = models.DateField(db_index=True)
    event_type = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    significance = models.CharField(
        max_length=20,
        choices=Significance.choices,
        default=Significance.ROUTINE
    )
    
    # Verification
    verified = models.BooleanField(default=False)
    conflicting_events = models.JSONField(
        default=list,
        blank=True,
        help_text="IDs of events that conflict with this one"
    )
    
    # Participants
    participants = models.JSONField(default=list, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'timeline_events'
        ordering = ['event_date']
        indexes = [
            models.Index(fields=['case', 'event_date']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.event_date}: {self.description[:50]}..."


# =============================================================================
# TOULMIN ARGUMENTS
# =============================================================================

class ToulminArgument(TimeStampedModel):
    """
    A Toulmin-structured legal argument.
    
    Follows Stephen Toulmin's argumentation model:
    Claim → Grounds → Warrant → Backing → Qualifier → Rebuttal
    
    Extended with falsifiability conditions for forensic analysis.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='arguments'
    )
    
    # Toulmin components
    claim_text = models.TextField(help_text="The assertion being made")
    grounds = models.JSONField(
        default=list,
        help_text="Evidence supporting the claim"
    )
    warrant = models.TextField(
        help_text="Legal rule connecting grounds to claim"
    )
    warrant_rule = models.ForeignKey(
        'LegalRule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='arguments'
    )
    backing = models.JSONField(
        default=list,
        help_text="Authority supporting the warrant (case law)"
    )
    qualifier = models.CharField(
        max_length=100,
        default='probably',
        help_text="Strength qualifier (probably, certainly, etc.)"
    )
    rebuttal = models.JSONField(
        default=list,
        help_text="Conditions that would invalidate the claim"
    )
    
    # Falsifiability (v5 enhancement)
    falsifiability_conditions = models.JSONField(
        default=list,
        help_text="Tests that would disprove the argument"
    )
    missing_evidence = models.JSONField(
        default=list,
        help_text="Evidence that should exist but wasn't found"
    )
    alternative_explanations = models.JSONField(
        default=list,
        help_text="Other ways to interpret the evidence"
    )
    
    # Confidence bounds
    confidence_lower = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    confidence_upper = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    confidence_mean = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Supporting claims
    supporting_claims = models.ManyToManyField(
        Claim,
        related_name='arguments',
        blank=True
    )
    
    class Meta:
        db_table = 'arguments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"[{self.qualifier}] {self.claim_text[:50]}..."


# =============================================================================
# ENTITIES
# =============================================================================

class Entity(TimeStampedModel):
    """A resolved entity (person/organization) in a case."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='entities'
    )
    
    canonical_name = models.CharField(max_length=255, db_index=True)
    entity_type = models.CharField(
        max_length=30,
        choices=EntityType.choices,
        default=EntityType.PERSON,
        db_index=True
    )
    aliases = models.JSONField(
        default=list,
        help_text="Alternative names/references"
    )
    roles = models.JSONField(
        default=list,
        help_text="Roles in the case"
    )
    organisation = models.CharField(max_length=255, blank=True, null=True)
    
    # Analysis metrics
    claim_count = models.IntegerField(default=0)
    sentiment_score = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)],
        help_text="Average sentiment in claims about this entity"
    )
    
    class Meta:
        db_table = 'entities'
        ordering = ['canonical_name']
        verbose_name_plural = 'entities'
        constraints = [
            models.UniqueConstraint(
                fields=['case', 'canonical_name'],
                name='unique_entity_per_case'
            )
        ]
    
    def __str__(self):
        return f"{self.canonical_name} ({self.entity_type})"


# =============================================================================
# LEGAL RULES
# =============================================================================

class LegalRule(models.Model):
    """
    A substantive legal rule for argument warrants.
    
    Contains UK Family Law rules including:
    - Children Act 1989 (CA1989)
    - Family Procedure Rules 2010 (FPR)
    - Practice Directions (PD12J, etc.)
    - Key case law (Re B, Lucas direction, etc.)
    """
    rule_id = models.CharField(max_length=50, primary_key=True)
    short_name = models.CharField(max_length=100, db_index=True)
    full_citation = models.CharField(max_length=255)
    text = models.TextField()
    category = models.CharField(
        max_length=30,
        choices=RuleCategory.choices,
        db_index=True
    )
    
    # Additional metadata
    keywords = models.JSONField(default=list, blank=True)
    related_rules = models.ManyToManyField(
        'self',
        symmetrical=True,
        blank=True
    )
    
    class Meta:
        db_table = 'legal_rules'
        ordering = ['category', 'short_name']
    
    def __str__(self):
        return f"{self.short_name} ({self.full_citation})"


# =============================================================================
# ANALYSIS RUNS
# =============================================================================

class AnalysisRun(TimeStampedModel):
    """Record of an analysis run for audit and tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='analysis_runs'
    )
    
    run_type = models.CharField(max_length=30, choices=RunType.choices)
    status = models.CharField(
        max_length=20,
        choices=RunStatus.choices,
        default=RunStatus.PENDING,
        db_index=True
    )
    
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Results summary
    documents_analyzed = models.IntegerField(default=0)
    claims_extracted = models.IntegerField(default=0)
    contradictions_found = models.IntegerField(default=0)
    biases_detected = models.IntegerField(default=0)
    
    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    error_traceback = models.TextField(blank=True, null=True)
    
    # AI model info
    model_used = models.CharField(max_length=100, blank=True, null=True)
    total_tokens = models.IntegerField(default=0)
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0
    )
    
    # Progress tracking
    progress_percent = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    progress_message = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'analysis_runs'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.run_type} - {self.status} ({self.started_at})"
    
    def mark_completed(self):
        """Mark the run as completed."""
        self.status = RunStatus.COMPLETED
        self.completed_at = timezone.now()
        self.progress_percent = 100
        self.save()
    
    def mark_failed(self, error_message: str, traceback: str = None):
        """Mark the run as failed."""
        self.status = RunStatus.FAILED
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.error_traceback = traceback
        self.save()


# =============================================================================
# BIAS BASELINES
# =============================================================================

class BiasBaseline(models.Model):
    """Calibrated baselines for bias detection."""
    baseline_id = models.CharField(max_length=100, primary_key=True)
    doc_type = models.CharField(max_length=50, db_index=True)
    metric = models.CharField(max_length=50)
    
    # Statistics
    corpus_size = models.IntegerField(default=100)
    mean = models.FloatField()
    std_dev = models.FloatField()
    
    # Source and validation
    source = models.CharField(
        max_length=50,
        default='estimated',
        help_text="'empirical', 'estimated', or 'calibrated'"
    )
    last_calibrated = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'bias_baselines'
        unique_together = ['doc_type', 'metric']
    
    def __str__(self):
        return f"{self.doc_type}/{self.metric}: μ={self.mean:.3f}, σ={self.std_dev:.3f}"

