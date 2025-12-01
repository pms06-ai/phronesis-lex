"""
FCIP v5.0 Contradiction Detection Engine

The revolutionary core: systematic detection of contradictions across legal documents.

Contradiction Types:
1. DIRECT - Opposite assertions about the same subject
2. TEMPORAL - Events that can't both be true given timeline
3. SELF_CONTRADICTION - Same author contradicting themselves (most legally significant)
4. MODALITY_SHIFT - Allegations treated as established facts
5. VALUE - Different numbers/values for same attribute
6. ATTRIBUTION - Disputes about who said/did what
7. QUOTATION - Misrepresented quotes across documents
8. OMISSION - Material context omitted (detected via asymmetric reporting)

Legal Significance:
- Self-contradictions are devastating for credibility (Lucas direction applies)
- Modality shifts indicate potential confirmation bias
- Attribution conflicts reveal partisan framing
- Temporal impossibilities suggest fabrication or confusion
"""

import re
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set
from uuid import UUID, uuid4

try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

from ..models.core import Claim, Modality, Polarity, Severity, ClaimType


# =============================================================================
# CONTRADICTION TYPES
# =============================================================================

class ContradictionType(str, Enum):
    """Types of contradictions detected."""
    DIRECT = "direct"                    # A says X, B says not-X
    TEMPORAL = "temporal"                # Events can't both be true given time
    SELF_CONTRADICTION = "self_contradiction"  # Same author contradicts self
    MODALITY_SHIFT = "modality_shift"    # Allegation → assertion without proof
    VALUE = "value"                      # Different numbers for same thing
    ATTRIBUTION = "attribution"          # Dispute about who said/did what
    QUOTATION = "quotation"              # Quote misrepresented
    OMISSION = "omission"                # Material context missing


# =============================================================================
# LEGAL SIGNIFICANCE
# =============================================================================

LEGAL_SIGNIFICANCE = {
    ContradictionType.SELF_CONTRADICTION: {
        "severity": Severity.CRITICAL,
        "case_law": "Re H-C [2016] EWCA Civ 136 (Lucas direction)",
        "explanation": "A witness contradicting their own prior statement raises "
                      "serious credibility issues. Per Lucas, lies must be evaluated "
                      "but may be told for reasons other than guilt.",
        "recommended_action": "Cross-examine on the inconsistency; consider whether "
                             "the contradiction goes to the heart of the witness's account."
    },
    ContradictionType.MODALITY_SHIFT: {
        "severity": Severity.HIGH,
        "case_law": "Re B [2008] UKHL 35",
        "explanation": "Treating an allegation as an established fact without proof "
                      "violates the Re B standard. Facts must be proved on the "
                      "balance of probabilities - 'real possibility' is not enough.",
        "recommended_action": "Challenge the finding; request the court identify the "
                             "evidential basis for treating allegation as proved fact."
    },
    ContradictionType.DIRECT: {
        "severity": Severity.HIGH,
        "case_law": "Re A (A Child) [2015] EWFC 11",
        "explanation": "Direct contradiction between accounts. Per Re A, evidence "
                      "cannot be evaluated in compartments - the court must consider "
                      "all evidence together.",
        "recommended_action": "Present both versions side-by-side; identify which "
                             "has independent corroboration."
    },
    ContradictionType.TEMPORAL: {
        "severity": Severity.HIGH,
        "case_law": "General evidential principles",
        "explanation": "Temporal impossibility undermines the reliability of one "
                      "or both accounts. Timeline analysis is often decisive.",
        "recommended_action": "Create detailed timeline; obtain documentary evidence "
                             "of dates (records, correspondence, GPS, etc.)."
    },
    ContradictionType.ATTRIBUTION: {
        "severity": Severity.MEDIUM,
        "case_law": "General evidential principles",
        "explanation": "Dispute about who said or did something. Attribution errors "
                      "may indicate bias, confusion, or deliberate misrepresentation.",
        "recommended_action": "Cross-reference original source documents; identify "
                             "the chain of attribution."
    },
    ContradictionType.VALUE: {
        "severity": Severity.MEDIUM,
        "case_law": "General evidential principles",
        "explanation": "Different values reported for the same attribute "
                      "(dates, amounts, frequencies). May indicate estimation, "
                      "error, or exaggeration.",
        "recommended_action": "Identify source of each figure; determine which "
                             "is supported by contemporaneous documentation."
    },
    ContradictionType.QUOTATION: {
        "severity": Severity.HIGH,
        "case_law": "Professional conduct obligations",
        "explanation": "Quotes taken out of context or materially altered. "
                      "Professionals have duty not to mislead the court.",
        "recommended_action": "Present full quote in context; if professional "
                             "misquotation is deliberate, consider complaint."
    },
    ContradictionType.OMISSION: {
        "severity": Severity.MEDIUM,
        "case_law": "Duty of full and frank disclosure",
        "explanation": "Material context omitted that changes meaning. May indicate "
                      "selective presentation of evidence.",
        "recommended_action": "Supply the missing context; identify pattern of "
                             "selective presentation if systematic."
    },
}


# =============================================================================
# POLARITY OPPOSITES
# =============================================================================

POLARITY_OPPOSITES = {
    # Positive -> Negative mappings
    "attended": ["did not attend", "failed to attend", "was absent"],
    "cooperated": ["refused to cooperate", "did not cooperate", "was uncooperative"],
    "engaged": ["did not engage", "refused to engage", "was disengaged"],
    "present": ["absent", "not present", "was not there"],
    "agreed": ["disagreed", "refused", "declined"],
    "supported": ["opposed", "did not support", "undermined"],
    "improved": ["deteriorated", "worsened", "declined"],
    "stable": ["unstable", "volatile", "erratic"],
    "appropriate": ["inappropriate", "unsuitable", "inadequate"],
    "positive": ["negative", "harmful", "detrimental"],
    "consistent": ["inconsistent", "contradictory", "unreliable"],
    "protective": ["failed to protect", "unprotective", "neglectful"],
    "truthful": ["lied", "untruthful", "dishonest", "fabricated"],
    "occurred": ["did not occur", "never happened", "fabricated"],
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Contradiction:
    """A detected contradiction between claims."""
    contradiction_id: UUID = field(default_factory=uuid4)
    case_id: str = ""
    
    # The conflicting claims
    claim_a_id: UUID = field(default_factory=uuid4)
    claim_b_id: UUID = field(default_factory=uuid4)
    claim_a_text: str = ""
    claim_b_text: str = ""
    claim_a_source: str = ""  # Document filename or author
    claim_b_source: str = ""
    
    # Classification
    contradiction_type: ContradictionType = ContradictionType.DIRECT
    severity: Severity = Severity.MEDIUM
    
    # Semantic analysis
    semantic_similarity: float = 0.0  # How similar the claims are in topic
    polarity_opposite: bool = False   # Whether they assert opposite things
    
    # Attribution
    claim_a_author: Optional[str] = None
    claim_b_author: Optional[str] = None
    same_author: bool = False  # Critical for self-contradiction
    
    # Temporal
    claim_a_date: Optional[str] = None
    claim_b_date: Optional[str] = None
    temporal_gap_days: Optional[int] = None
    
    # Shared subject
    shared_subject: Optional[str] = None
    shared_predicate: Optional[str] = None
    
    # Quotes (for quotation contradictions)
    original_quote: Optional[str] = None
    altered_quote: Optional[str] = None
    
    # Explanation
    explanation: str = ""
    legal_significance: str = ""
    recommended_action: str = ""
    case_law_reference: str = ""
    
    # Confidence
    confidence: float = 0.0
    detection_method: str = ""


@dataclass
class ContradictionReport:
    """Summary report of all contradictions in a case."""
    case_id: str
    total_contradictions: int
    by_type: Dict[ContradictionType, int]
    by_severity: Dict[Severity, int]
    self_contradictions: List[Contradiction]  # Most legally significant
    modality_shifts: List[Contradiction]       # Allegations treated as facts
    critical_findings: List[Contradiction]     # Severity = CRITICAL
    contradictions: List[Contradiction]        # All contradictions
    
    # Summary stats
    authors_with_self_contradictions: List[str]
    documents_with_most_contradictions: List[Tuple[str, int]]


# =============================================================================
# CONTRADICTION DETECTION ENGINE
# =============================================================================

class ContradictionDetectionEngine:
    """
    Engine for detecting contradictions across claims in legal documents.
    
    This is the core revolutionary capability - systematically finding
    inconsistencies that would take humans hours to identify manually.
    """
    
    def __init__(
        self,
        semantic_threshold: float = 0.6,
        polarity_threshold: float = 0.8,
        enable_semantic: bool = True
    ):
        """
        Initialize the contradiction detection engine.
        
        Args:
            semantic_threshold: Minimum similarity for claims to be compared
            polarity_threshold: Minimum confidence for polarity opposition
            enable_semantic: Whether to use semantic similarity (requires sentence-transformers)
        """
        self.semantic_threshold = semantic_threshold
        self.polarity_threshold = polarity_threshold
        self.enable_semantic = enable_semantic and SENTENCE_TRANSFORMERS_AVAILABLE
        
        # Initialize semantic model if available
        self._model = None
        if self.enable_semantic:
            try:
                self._model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception:
                self.enable_semantic = False
        
        # Build polarity opposite index
        self._polarity_index = self._build_polarity_index()
    
    def _build_polarity_index(self) -> Dict[str, Set[str]]:
        """Build reverse index for polarity opposites."""
        index = {}
        for positive, negatives in POLARITY_OPPOSITES.items():
            index[positive] = set(negatives)
            for neg in negatives:
                if neg not in index:
                    index[neg] = set()
                index[neg].add(positive)
        return index
    
    def detect_contradictions(
        self,
        claims: List[Claim],
        case_id: str = ""
    ) -> ContradictionReport:
        """
        Detect all contradictions in a list of claims.
        
        Args:
            claims: List of Claim objects to analyze
            case_id: The case identifier
            
        Returns:
            ContradictionReport with all detected contradictions
        """
        contradictions: List[Contradiction] = []
        
        # Convert claims to dicts for easier handling
        claim_dicts = [self._claim_to_dict(c) for c in claims]
        
        # Group claims by subject for efficient comparison
        subject_groups = self._group_by_subject(claim_dicts)
        
        # 1. Detect direct contradictions (same subject, opposite polarity)
        direct = self._detect_direct_contradictions(claim_dicts, subject_groups, case_id)
        contradictions.extend(direct)
        
        # 2. Detect self-contradictions (same author)
        self_contradictions = self._detect_self_contradictions(claim_dicts, case_id)
        contradictions.extend(self_contradictions)
        
        # 3. Detect modality shifts (allegation → assertion)
        modality_shifts = self._detect_modality_shifts(claim_dicts, case_id)
        contradictions.extend(modality_shifts)
        
        # 4. Detect temporal contradictions
        temporal = self._detect_temporal_contradictions(claim_dicts, case_id)
        contradictions.extend(temporal)
        
        # 5. Detect value contradictions
        value_contradictions = self._detect_value_contradictions(claim_dicts, case_id)
        contradictions.extend(value_contradictions)
        
        # 6. Detect attribution contradictions
        attribution = self._detect_attribution_contradictions(claim_dicts, case_id)
        contradictions.extend(attribution)
        
        # Deduplicate (same pair might be detected by multiple methods)
        contradictions = self._deduplicate(contradictions)
        
        # Add legal significance to all contradictions
        for c in contradictions:
            self._add_legal_significance(c)
        
        # Build report
        return self._build_report(contradictions, case_id)
    
    def _claim_to_dict(self, claim: Claim) -> dict:
        """Convert Claim to dict for easier processing."""
        return {
            "claim_id": str(claim.claim_id),
            "document_id": str(claim.document_id),
            "case_id": claim.case_id,
            "text": claim.text,
            "claim_type": claim.claim_type.value if claim.claim_type else None,
            "source_quote": claim.source_quote,
            "subject": claim.subject,
            "predicate": claim.predicate,
            "object_value": claim.object_value,
            "modality": claim.modality.value if claim.modality else None,
            "polarity": claim.polarity.value if claim.polarity else None,
            "certainty": claim.certainty,
            "asserted_by": claim.asserted_by,
            "time_expression": claim.time_expression,
            "time_start": claim.time_start,
        }
    
    def _group_by_subject(self, claims: List[dict]) -> Dict[str, List[dict]]:
        """Group claims by normalized subject."""
        groups: Dict[str, List[dict]] = {}
        for claim in claims:
            subject = claim.get("subject")
            if subject:
                key = subject.lower().strip()
                if key not in groups:
                    groups[key] = []
                groups[key].append(claim)
        return groups
    
    def _calculate_semantic_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate semantic similarity between two texts."""
        if not text_a or not text_b:
            return 0.0
        
        if self.enable_semantic and self._model:
            try:
                embeddings = self._model.encode([text_a, text_b], convert_to_tensor=True)
                similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
                return max(0.0, min(1.0, similarity))
            except Exception:
                pass
        
        # Fallback to fuzzy string matching
        if RAPIDFUZZ_AVAILABLE:
            return fuzz.token_sort_ratio(text_a.lower(), text_b.lower()) / 100.0
        
        # Ultra-basic fallback: word overlap
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)
    
    def _check_polarity_opposition(self, text_a: str, text_b: str) -> Tuple[bool, float]:
        """Check if two texts assert opposite things."""
        text_a_lower = text_a.lower()
        text_b_lower = text_b.lower()
        
        # Check for explicit negation patterns
        negation_pairs = [
            (r"\bdid\b", r"\bdid not\b"),
            (r"\bwas\b", r"\bwas not\b"),
            (r"\bhas\b", r"\bhas not\b"),
            (r"\bwere\b", r"\bwere not\b"),
            (r"\bhad\b", r"\bhad not\b"),
            (r"\bnever\b", r"\balways\b"),
            (r"\bdenied\b", r"\bconfirmed\b"),
            (r"\brefused\b", r"\bagreed\b"),
            (r"\battended\b", r"\bdid not attend\b"),
            (r"\bcooperated\b", r"\bfailed to cooperate\b"),
            (r"\bengaged\b", r"\bfailed to engage\b"),
            (r"\bpresent\b", r"\babsent\b"),
        ]
        
        for pos, neg in negation_pairs:
            if re.search(pos, text_a_lower) and re.search(neg, text_b_lower):
                return True, 0.9
            if re.search(neg, text_a_lower) and re.search(pos, text_b_lower):
                return True, 0.9
        
        # Check polarity opposite words
        for word, opposites in self._polarity_index.items():
            if word in text_a_lower:
                for opp in opposites:
                    if opp in text_b_lower:
                        return True, 0.85
        
        return False, 0.0
    
    def _detect_direct_contradictions(
        self,
        claims: List[dict],
        subject_groups: Dict[str, List[dict]],
        case_id: str
    ) -> List[Contradiction]:
        """Detect direct contradictions where same subject has opposite assertions."""
        contradictions = []
        
        for subject, group in subject_groups.items():
            if len(group) < 2:
                continue
            
            # Compare all pairs within this subject group
            for i, claim_a in enumerate(group):
                for claim_b in group[i+1:]:
                    # Skip if same document (internal consistency is different)
                    if claim_a.get("document_id") == claim_b.get("document_id"):
                        continue
                    
                    # Check semantic similarity (are they about the same thing?)
                    similarity = self._calculate_semantic_similarity(
                        claim_a.get("text", ""),
                        claim_b.get("text", "")
                    )
                    
                    if similarity < self.semantic_threshold:
                        continue
                    
                    # Check for polarity opposition
                    is_opposite, conf = self._check_polarity_opposition(
                        claim_a.get("text", ""),
                        claim_b.get("text", "")
                    )
                    
                    # Also check explicit polarity field
                    if claim_a.get("polarity") and claim_b.get("polarity"):
                        if claim_a["polarity"] != claim_b["polarity"]:
                            is_opposite = True
                            conf = max(conf, 0.8)
                    
                    if is_opposite and conf >= self.polarity_threshold:
                        contradiction = Contradiction(
                            case_id=case_id,
                            claim_a_id=UUID(claim_a["claim_id"]),
                            claim_b_id=UUID(claim_b["claim_id"]),
                            claim_a_text=claim_a.get("text", ""),
                            claim_b_text=claim_b.get("text", ""),
                            claim_a_source=claim_a.get("document_id", ""),
                            claim_b_source=claim_b.get("document_id", ""),
                            claim_a_author=claim_a.get("asserted_by"),
                            claim_b_author=claim_b.get("asserted_by"),
                            same_author=claim_a.get("asserted_by") == claim_b.get("asserted_by") if claim_a.get("asserted_by") else False,
                            contradiction_type=ContradictionType.DIRECT,
                            severity=Severity.HIGH,
                            semantic_similarity=similarity,
                            polarity_opposite=True,
                            shared_subject=subject,
                            confidence=conf,
                            detection_method="polarity_opposition",
                            explanation=f"Contradictory claims about '{subject}': "
                                       f"one asserts a positive, the other a negative."
                        )
                        contradictions.append(contradiction)
        
        return contradictions
    
    def _detect_self_contradictions(
        self,
        claims: List[dict],
        case_id: str
    ) -> List[Contradiction]:
        """
        Detect self-contradictions where same author says contradictory things.
        
        This is the most legally devastating type of contradiction.
        """
        contradictions = []
        
        # Group by author
        author_groups: Dict[str, List[dict]] = {}
        for claim in claims:
            author = claim.get("asserted_by")
            if author:
                key = author.lower().strip()
                if key not in author_groups:
                    author_groups[key] = []
                author_groups[key].append(claim)
        
        for author, group in author_groups.items():
            if len(group) < 2:
                continue
            
            # Compare all pairs from same author
            for i, claim_a in enumerate(group):
                for claim_b in group[i+1:]:
                    # Check semantic similarity
                    similarity = self._calculate_semantic_similarity(
                        claim_a.get("text", ""),
                        claim_b.get("text", "")
                    )
                    
                    if similarity < self.semantic_threshold:
                        continue
                    
                    # Check for contradiction
                    is_opposite, conf = self._check_polarity_opposition(
                        claim_a.get("text", ""),
                        claim_b.get("text", "")
                    )
                    
                    if is_opposite and conf >= 0.7:  # Lower threshold for self-contradiction
                        contradiction = Contradiction(
                            case_id=case_id,
                            claim_a_id=UUID(claim_a["claim_id"]),
                            claim_b_id=UUID(claim_b["claim_id"]),
                            claim_a_text=claim_a.get("text", ""),
                            claim_b_text=claim_b.get("text", ""),
                            claim_a_source=claim_a.get("document_id", ""),
                            claim_b_source=claim_b.get("document_id", ""),
                            claim_a_author=author,
                            claim_b_author=author,
                            same_author=True,
                            claim_a_date=claim_a.get("time_start"),
                            claim_b_date=claim_b.get("time_start"),
                            contradiction_type=ContradictionType.SELF_CONTRADICTION,
                            severity=Severity.CRITICAL,
                            semantic_similarity=similarity,
                            polarity_opposite=True,
                            confidence=conf + 0.1,  # Boost for self-contradiction
                            detection_method="self_contradiction",
                            explanation=f"Self-contradiction by '{author}': "
                                       f"the same person made contradictory statements."
                        )
                        contradictions.append(contradiction)
        
        return contradictions
    
    def _detect_modality_shifts(
        self,
        claims: List[dict],
        case_id: str
    ) -> List[Contradiction]:
        """
        Detect modality shifts where allegations are treated as facts.
        
        This violates Re B [2008] - facts must be proved, not assumed.
        """
        contradictions = []
        
        # Find alleged claims
        alleged_claims = [c for c in claims if c.get("modality") == "alleged"]
        
        # Find asserted claims
        asserted_claims = [c for c in claims if c.get("modality") == "asserted"]
        
        for alleged in alleged_claims:
            for asserted in asserted_claims:
                # Check if they're about the same thing
                similarity = self._calculate_semantic_similarity(
                    alleged.get("text", ""),
                    asserted.get("text", "")
                )
                
                if similarity >= 0.7:  # High threshold - must be clearly same topic
                    # Check if the asserted claim treats the allegation as fact
                    # without indicating it was proved
                    alleged_text = alleged.get("text", "").lower()
                    asserted_text = asserted.get("text", "").lower()
                    
                    # Look for language indicating unproved treatment as fact
                    fact_indicators = [
                        "established", "confirmed", "demonstrated",
                        "clear that", "evident that", "the fact that"
                    ]
                    
                    has_fact_language = any(ind in asserted_text for ind in fact_indicators)
                    
                    if has_fact_language:
                        contradiction = Contradiction(
                            case_id=case_id,
                            claim_a_id=UUID(alleged["claim_id"]),
                            claim_b_id=UUID(asserted["claim_id"]),
                            claim_a_text=alleged.get("text", ""),
                            claim_b_text=asserted.get("text", ""),
                            claim_a_source=alleged.get("document_id", ""),
                            claim_b_source=asserted.get("document_id", ""),
                            claim_a_author=alleged.get("asserted_by"),
                            claim_b_author=asserted.get("asserted_by"),
                            contradiction_type=ContradictionType.MODALITY_SHIFT,
                            severity=Severity.HIGH,
                            semantic_similarity=similarity,
                            confidence=similarity * 0.9,
                            detection_method="modality_analysis",
                            explanation=f"An allegation is being treated as established fact "
                                       f"without indication that it was proved on the balance "
                                       f"of probabilities. This potentially violates Re B."
                        )
                        contradictions.append(contradiction)
        
        return contradictions
    
    def _detect_temporal_contradictions(
        self,
        claims: List[dict],
        case_id: str
    ) -> List[Contradiction]:
        """Detect temporal impossibilities where events can't both be true."""
        contradictions = []
        
        # Get claims with temporal information
        temporal_claims = [c for c in claims if c.get("time_start") or c.get("time_expression")]
        
        # For each pair, check for temporal conflicts
        for i, claim_a in enumerate(temporal_claims):
            for claim_b in temporal_claims[i+1:]:
                # Check semantic similarity
                similarity = self._calculate_semantic_similarity(
                    claim_a.get("text", ""),
                    claim_b.get("text", "")
                )
                
                if similarity < self.semantic_threshold:
                    continue
                
                # Check for same event, different dates
                time_a = claim_a.get("time_start") or claim_a.get("time_expression", "")
                time_b = claim_b.get("time_start") or claim_b.get("time_expression", "")
                
                if time_a and time_b and time_a != time_b:
                    # Different times claimed for similar events
                    contradiction = Contradiction(
                        case_id=case_id,
                        claim_a_id=UUID(claim_a["claim_id"]),
                        claim_b_id=UUID(claim_b["claim_id"]),
                        claim_a_text=claim_a.get("text", ""),
                        claim_b_text=claim_b.get("text", ""),
                        claim_a_source=claim_a.get("document_id", ""),
                        claim_b_source=claim_b.get("document_id", ""),
                        claim_a_author=claim_a.get("asserted_by"),
                        claim_b_author=claim_b.get("asserted_by"),
                        claim_a_date=str(time_a),
                        claim_b_date=str(time_b),
                        contradiction_type=ContradictionType.TEMPORAL,
                        severity=Severity.HIGH,
                        semantic_similarity=similarity,
                        confidence=similarity * 0.85,
                        detection_method="temporal_analysis",
                        explanation=f"Same or similar event reported with different dates: "
                                   f"'{time_a}' vs '{time_b}'"
                    )
                    contradictions.append(contradiction)
        
        return contradictions
    
    def _detect_value_contradictions(
        self,
        claims: List[dict],
        case_id: str
    ) -> List[Contradiction]:
        """Detect contradictions in reported values (numbers, frequencies, amounts)."""
        contradictions = []
        
        # Pattern to extract numbers
        number_pattern = re.compile(r'\b(\d+(?:\.\d+)?)\s*(times?|occasions?|days?|weeks?|months?|years?|hours?)?\b', re.IGNORECASE)
        
        # Claims with numbers
        value_claims = []
        for claim in claims:
            text = claim.get("text", "")
            matches = number_pattern.findall(text)
            if matches:
                claim["_numbers"] = [(float(m[0]), m[1].lower() if m[1] else "") for m in matches]
                value_claims.append(claim)
        
        # Compare pairs
        for i, claim_a in enumerate(value_claims):
            for claim_b in value_claims[i+1:]:
                # Check semantic similarity
                similarity = self._calculate_semantic_similarity(
                    claim_a.get("text", ""),
                    claim_b.get("text", "")
                )
                
                if similarity < 0.5:  # Lower threshold for value comparisons
                    continue
                
                # Compare numbers with same units
                for num_a, unit_a in claim_a.get("_numbers", []):
                    for num_b, unit_b in claim_b.get("_numbers", []):
                        if unit_a == unit_b and num_a != num_b:
                            # Significant difference?
                            diff_ratio = abs(num_a - num_b) / max(num_a, num_b, 1)
                            if diff_ratio > 0.2:  # More than 20% difference
                                contradiction = Contradiction(
                                    case_id=case_id,
                                    claim_a_id=UUID(claim_a["claim_id"]),
                                    claim_b_id=UUID(claim_b["claim_id"]),
                                    claim_a_text=claim_a.get("text", ""),
                                    claim_b_text=claim_b.get("text", ""),
                                    claim_a_source=claim_a.get("document_id", ""),
                                    claim_b_source=claim_b.get("document_id", ""),
                                    claim_a_author=claim_a.get("asserted_by"),
                                    claim_b_author=claim_b.get("asserted_by"),
                                    contradiction_type=ContradictionType.VALUE,
                                    severity=Severity.MEDIUM,
                                    semantic_similarity=similarity,
                                    confidence=min(0.9, similarity + diff_ratio * 0.5),
                                    detection_method="value_comparison",
                                    explanation=f"Different values reported: {num_a} {unit_a} "
                                               f"vs {num_b} {unit_b}"
                                )
                                contradictions.append(contradiction)
                                break
        
        return contradictions
    
    def _detect_attribution_contradictions(
        self,
        claims: List[dict],
        case_id: str
    ) -> List[Contradiction]:
        """Detect contradictions about who said or did what."""
        contradictions = []
        
        # Look for reported speech patterns
        reported_pattern = re.compile(
            r'(?:(\w+(?:\s+\w+)?)\s+(?:stated|said|reported|claimed|alleged|asserted|denied))',
            re.IGNORECASE
        )
        
        for i, claim_a in enumerate(claims):
            text_a = claim_a.get("text", "")
            match_a = reported_pattern.search(text_a)
            if not match_a:
                continue
            
            speaker_a = match_a.group(1)
            
            for claim_b in claims[i+1:]:
                text_b = claim_b.get("text", "")
                
                # Check if about same topic
                similarity = self._calculate_semantic_similarity(text_a, text_b)
                if similarity < 0.6:
                    continue
                
                match_b = reported_pattern.search(text_b)
                if match_b:
                    speaker_b = match_b.group(1)
                    
                    # Different speakers attributed for similar content
                    if speaker_a.lower() != speaker_b.lower():
                        if similarity > 0.8:  # Very similar content, different attribution
                            contradiction = Contradiction(
                                case_id=case_id,
                                claim_a_id=UUID(claim_a["claim_id"]),
                                claim_b_id=UUID(claim_b["claim_id"]),
                                claim_a_text=text_a,
                                claim_b_text=text_b,
                                claim_a_source=claim_a.get("document_id", ""),
                                claim_b_source=claim_b.get("document_id", ""),
                                claim_a_author=speaker_a,
                                claim_b_author=speaker_b,
                                contradiction_type=ContradictionType.ATTRIBUTION,
                                severity=Severity.MEDIUM,
                                semantic_similarity=similarity,
                                confidence=similarity * 0.8,
                                detection_method="attribution_analysis",
                                explanation=f"Same or similar statement attributed to "
                                           f"different sources: '{speaker_a}' vs '{speaker_b}'"
                            )
                            contradictions.append(contradiction)
        
        return contradictions
    
    def _deduplicate(self, contradictions: List[Contradiction]) -> List[Contradiction]:
        """Remove duplicate contradictions (same pair detected multiple ways)."""
        seen = set()
        unique = []
        
        for c in contradictions:
            # Create canonical key (sorted pair)
            key = tuple(sorted([str(c.claim_a_id), str(c.claim_b_id)]))
            
            if key not in seen:
                seen.add(key)
                unique.append(c)
            else:
                # Keep the one with higher confidence
                for i, existing in enumerate(unique):
                    existing_key = tuple(sorted([str(existing.claim_a_id), str(existing.claim_b_id)]))
                    if existing_key == key and c.confidence > existing.confidence:
                        unique[i] = c
                        break
        
        return unique
    
    def _add_legal_significance(self, contradiction: Contradiction) -> None:
        """Add legal significance information to a contradiction."""
        sig = LEGAL_SIGNIFICANCE.get(contradiction.contradiction_type, {})
        
        if sig:
            contradiction.legal_significance = sig.get("explanation", "")
            contradiction.recommended_action = sig.get("recommended_action", "")
            contradiction.case_law_reference = sig.get("case_law", "")
            
            # Override severity if specified
            if "severity" in sig:
                contradiction.severity = sig["severity"]
    
    def _build_report(
        self,
        contradictions: List[Contradiction],
        case_id: str
    ) -> ContradictionReport:
        """Build a summary report from detected contradictions."""
        
        # Count by type
        by_type: Dict[ContradictionType, int] = {}
        for c in contradictions:
            by_type[c.contradiction_type] = by_type.get(c.contradiction_type, 0) + 1
        
        # Count by severity
        by_severity: Dict[Severity, int] = {}
        for c in contradictions:
            by_severity[c.severity] = by_severity.get(c.severity, 0) + 1
        
        # Self-contradictions
        self_contradictions = [
            c for c in contradictions 
            if c.contradiction_type == ContradictionType.SELF_CONTRADICTION
        ]
        
        # Modality shifts
        modality_shifts = [
            c for c in contradictions
            if c.contradiction_type == ContradictionType.MODALITY_SHIFT
        ]
        
        # Critical findings
        critical = [
            c for c in contradictions
            if c.severity == Severity.CRITICAL
        ]
        
        # Authors with self-contradictions
        authors_with_self = list(set(
            c.claim_a_author for c in self_contradictions 
            if c.claim_a_author
        ))
        
        # Documents with most contradictions
        doc_counts: Dict[str, int] = {}
        for c in contradictions:
            doc_counts[c.claim_a_source] = doc_counts.get(c.claim_a_source, 0) + 1
            doc_counts[c.claim_b_source] = doc_counts.get(c.claim_b_source, 0) + 1
        
        docs_ranked = sorted(doc_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return ContradictionReport(
            case_id=case_id,
            total_contradictions=len(contradictions),
            by_type=by_type,
            by_severity=by_severity,
            self_contradictions=self_contradictions,
            modality_shifts=modality_shifts,
            critical_findings=critical,
            contradictions=sorted(contradictions, key=lambda c: (
                0 if c.severity == Severity.CRITICAL else
                1 if c.severity == Severity.HIGH else
                2 if c.severity == Severity.MEDIUM else 3,
                -c.confidence
            )),
            authors_with_self_contradictions=authors_with_self,
            documents_with_most_contradictions=docs_ranked
        )
    
    def compare_claims(
        self,
        claim_a: Claim,
        claim_b: Claim,
        case_id: str = ""
    ) -> Optional[Contradiction]:
        """
        Compare two specific claims for contradiction.
        
        Useful for targeted analysis or UI interactions.
        """
        dict_a = self._claim_to_dict(claim_a)
        dict_b = self._claim_to_dict(claim_b)
        
        similarity = self._calculate_semantic_similarity(
            dict_a.get("text", ""),
            dict_b.get("text", "")
        )
        
        if similarity < self.semantic_threshold:
            return None
        
        is_opposite, conf = self._check_polarity_opposition(
            dict_a.get("text", ""),
            dict_b.get("text", "")
        )
        
        if not is_opposite:
            return None
        
        same_author = (
            dict_a.get("asserted_by") and 
            dict_a.get("asserted_by") == dict_b.get("asserted_by")
        )
        
        contradiction = Contradiction(
            case_id=case_id,
            claim_a_id=claim_a.claim_id,
            claim_b_id=claim_b.claim_id,
            claim_a_text=dict_a.get("text", ""),
            claim_b_text=dict_b.get("text", ""),
            claim_a_source=str(dict_a.get("document_id", "")),
            claim_b_source=str(dict_b.get("document_id", "")),
            claim_a_author=dict_a.get("asserted_by"),
            claim_b_author=dict_b.get("asserted_by"),
            same_author=same_author,
            contradiction_type=(
                ContradictionType.SELF_CONTRADICTION if same_author 
                else ContradictionType.DIRECT
            ),
            severity=Severity.CRITICAL if same_author else Severity.HIGH,
            semantic_similarity=similarity,
            polarity_opposite=True,
            confidence=conf,
            detection_method="direct_comparison"
        )
        
        self._add_legal_significance(contradiction)
        
        return contradiction

