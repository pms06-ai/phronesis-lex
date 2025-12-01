"""
FCIP v5.0 Core Models - Domain models for forensic case intelligence.

Features:
- Epistemic claim structure (modality, certainty, attribution)
- Provenance tracking with chain of custody
- Confidence with methodology attribution
- Toulmin argumentation with falsifiability
"""

from datetime import datetime, date
from enum import Enum
from typing import Literal, Optional, List, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# ENUMS
# =============================================================================

class EntityType(str, Enum):
    """Types of entities in legal proceedings."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    CHILD = "child"
    PARENT = "parent"
    SOCIAL_WORKER = "social_worker"
    GUARDIAN = "guardian"
    JUDGE = "judge"
    PSYCHOLOGIST = "psychologist"
    BARRISTER = "barrister"
    SOLICITOR = "solicitor"
    EXPERT = "expert"
    OTHER = "other"


class DocumentType(str, Enum):
    """Types of legal documents."""
    COURT_ORDER = "court_order"
    WITNESS_STATEMENT = "witness_statement"
    SOCIAL_WORK_REPORT = "social_work_report"
    PSYCHOLOGICAL_REPORT = "psychological_report"
    SECTION_7_REPORT = "section_7_report"
    SECTION_37_REPORT = "section_37_report"
    CAFCASS_ANALYSIS = "cafcass_analysis"
    MEDICAL_RECORD = "medical_record"
    POLICE_REPORT = "police_report"
    LEGAL_SUBMISSION = "legal_submission"
    EXPERT_REPORT = "expert_report"
    CORRESPONDENCE = "correspondence"
    MEETING_MINUTES = "meeting_minutes"
    SAR_RESPONSE = "sar_response"
    OTHER = "other"


class ClaimType(str, Enum):
    """Types of claims extracted from documents."""
    ASSERTION = "assertion"
    ALLEGATION = "allegation"
    FINDING = "finding"
    CONCLUSION = "conclusion"
    RECOMMENDATION = "recommendation"
    OPINION = "opinion"
    OBSERVATION = "observation"
    CONCERN = "concern"
    SUBMISSION = "submission"


class Modality(str, Enum):
    """Epistemic modality of a claim."""
    ASSERTED = "asserted"      # Direct assertion: "The father attended"
    REPORTED = "reported"      # Attribution: "The mother stated..."
    ALLEGED = "alleged"        # Contested: "It is alleged..."
    DENIED = "denied"          # Negation: "The father denies..."
    HYPOTHETICAL = "hypothetical"  # Conditional: "If the father had..."


class Polarity(str, Enum):
    """Polarity of a claim."""
    AFFIRM = "affirm"
    NEGATE = "negate"


class Severity(str, Enum):
    """Severity levels for signals."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# =============================================================================
# CORE MODELS
# =============================================================================

class Confidence(BaseModel):
    """Confidence score with methodology attribution."""
    model_config = ConfigDict(frozen=True)

    score: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    methodology: str = Field(description="How confidence was determined")
    factors: List[str] = Field(default_factory=list, description="Contributing factors")

    @classmethod
    def llm_extracted(cls, score: float, model: str) -> "Confidence":
        """Create confidence from LLM extraction."""
        return cls(score=score, methodology="llm_extraction", factors=[f"model:{model}"])

    @classmethod
    def rule_based(cls, score: float, rules: List[str]) -> "Confidence":
        """Create confidence from rule-based extraction."""
        return cls(score=score, methodology="rule_based", factors=rules)

    @classmethod
    def statistical(cls, score: float, test: str, p_value: float) -> "Confidence":
        """Create confidence from statistical test."""
        return cls(score=score, methodology="statistical", factors=[f"test:{test}", f"p:{p_value:.4f}"])


class Provenance(BaseModel):
    """Chain of custody for documents and evidence."""
    model_config = ConfigDict(frozen=True)

    source: str = Field(description="Original source of document")
    acquisition_date: date = Field(description="When document was acquired")
    disclosure_reference: Optional[str] = Field(default=None, description="Disclosure bundle reference")
    chain: List[str] = Field(default_factory=list, description="Chain of custody events")
    integrity_hash: Optional[str] = Field(default=None, description="SHA3-256 hash")
    gaps: List[str] = Field(default_factory=list, description="Identified gaps in chain")


class Entity(BaseModel):
    """An actor or entity in the case."""
    model_config = ConfigDict(frozen=True)

    entity_id: UUID = Field(default_factory=uuid4)
    canonical_name: str = Field(description="Primary name")
    entity_type: EntityType = Field(description="Type of entity")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    roles: List[str] = Field(default_factory=list, description="Roles in case")
    organisation: Optional[str] = Field(default=None, description="Associated organization")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class Claim(BaseModel):
    """An assertion extracted from a document with epistemic annotation."""
    model_config = ConfigDict(frozen=True)

    claim_id: UUID = Field(default_factory=uuid4)
    document_id: UUID = Field(description="Source document")
    case_id: str = Field(description="Parent case")

    # Content
    text: str = Field(description="The claim text")
    claim_type: ClaimType = Field(description="Type of claim")
    source_quote: Optional[str] = Field(default=None, description="Exact supporting quote")

    # Subject-Predicate-Object
    subject: Optional[str] = Field(default=None, description="Subject entity")
    subject_entity_id: Optional[UUID] = Field(default=None)
    predicate: Optional[str] = Field(default=None, description="Action or state")
    predicate_category: Optional[str] = Field(default=None)
    object_value: Optional[str] = Field(default=None, description="What is asserted")

    # Epistemic stance
    modality: Modality = Field(default=Modality.ASSERTED)
    polarity: Polarity = Field(default=Polarity.AFFIRM)
    certainty: float = Field(default=0.5, ge=0.0, le=1.0)
    certainty_calibrated: Optional[float] = Field(default=None)
    certainty_markers: List[str] = Field(default_factory=list)

    # Attribution
    asserted_by: Optional[str] = Field(default=None, description="Who made this claim")
    asserted_by_entity_id: Optional[UUID] = Field(default=None)

    # Temporal
    time_expression: Optional[str] = Field(default=None)
    time_start: Optional[str] = Field(default=None)
    time_end: Optional[str] = Field(default=None)
    time_precision: str = Field(default="unknown")

    # Extraction metadata
    extractor: str = Field(default="fcip_v5")
    extractor_model: Optional[str] = Field(default=None)
    extraction_prompt_hash: Optional[str] = Field(default=None)
    confidence: Confidence = Field(default_factory=lambda: Confidence(score=0.8, methodology="default"))

    # Flags
    is_requirement: bool = Field(default=False)
    deadline_expression: Optional[str] = Field(default=None)


class ToulminArgument(BaseModel):
    """Toulmin argumentation structure with falsifiability."""
    model_config = ConfigDict(frozen=True)

    argument_id: UUID = Field(default_factory=uuid4)
    case_id: str = Field(description="Parent case")

    # Toulmin components
    claim_text: str = Field(description="The assertion being made")
    grounds: List[str] = Field(description="Evidence supporting the claim")
    warrant: str = Field(description="Reasoning connecting grounds to claim")
    warrant_rule_id: Optional[str] = Field(default=None, description="Legal rule reference")
    backing: List[str] = Field(default_factory=list, description="Support for warrant")
    qualifier: str = Field(default="probably", description="Strength qualifier")
    rebuttal: List[str] = Field(default_factory=list, description="Conditions invalidating claim")

    # v5 Enhancements
    falsifiability_conditions: List[dict] = Field(
        default_factory=list,
        description="Tests that would disprove the argument"
    )
    missing_evidence: List[str] = Field(default_factory=list)
    alternative_explanations: List[str] = Field(default_factory=list)

    # Confidence bounds
    confidence_lower: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_upper: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence_mean: float = Field(default=0.5, ge=0.0, le=1.0)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BiasSignal(BaseModel):
    """Statistical bias signal detected in document analysis."""
    model_config = ConfigDict(frozen=True)

    signal_id: UUID = Field(default_factory=uuid4)
    document_id: str = Field(description="Source document")
    case_id: str = Field(description="Parent case")

    # Signal details
    signal_type: str = Field(description="Type of bias detected")
    metric_value: float = Field(description="Observed metric value")
    baseline_mean: float = Field(description="Expected baseline mean")
    baseline_std: float = Field(description="Baseline standard deviation")
    z_score: float = Field(description="Z-score from baseline")
    p_value: Optional[float] = Field(default=None)

    # Interpretation
    description: str = Field(description="Human-readable description")
    severity: Severity = Field(description="Severity level")
    direction: str = Field(description="higher or lower than expected")

    # Reference
    baseline_id: str = Field(description="Reference baseline used")
    baseline_source: str = Field(default="estimated")


class ParsedTemporal(BaseModel):
    """Parsed temporal expression."""
    model_config = ConfigDict(frozen=True)

    raw_text: str = Field(description="Original text")
    expression_type: str = Field(description="absolute, relative, immediate, range")
    base_date: Optional[date] = Field(default=None)
    anchor_event: Optional[str] = Field(default=None)
    offset_value: Optional[int] = Field(default=None)
    offset_unit: Optional[str] = Field(default=None)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    is_deadline: bool = Field(default=False)
    working_days: bool = Field(default=False)
