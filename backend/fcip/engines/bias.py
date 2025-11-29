"""
FCIP v5.0 Bias Detection Engine

Statistical detection of linguistic bias by comparing against external corpus baselines.

Dimensions:
- Certainty language (over/under-confidence)
- Negative attribution (disproportionate negativity)
- Hedging frequency
- Quantifier extremity (always/never vs sometimes)
- Attribution asymmetry per entity
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from ..config import config
from ..models.core import BiasSignal, Severity


# =============================================================================
# LINGUISTIC PATTERNS
# =============================================================================

CERTAINTY_HIGH_PATTERNS = [
    r"\bclearly\b",
    r"\bobviously\b",
    r"\bcertainly\b",
    r"\bdefinitely\b",
    r"\bundoubtedly\b",
    r"\bwithout doubt\b",
    r"\bplainly\b",
    r"\bevident(ly)?\b",
    r"\bestablished\b",
    r"\bconfirmed\b",
]

CERTAINTY_LOW_PATTERNS = [
    r"\bperhaps\b",
    r"\bpossibly\b",
    r"\bmay\b",
    r"\bmight\b",
    r"\bappears?\b",
    r"\bseems?\b",
    r"\bsuggests?\b",
    r"\bindicates?\b",
    r"\bcould\b",
    r"\bunclear\b",
]

NEGATIVE_PATTERNS = [
    r"\bfailed\b",
    r"\brefused\b",
    r"\bunable\b",
    r"\binadequate\b",
    r"\bpoor\b",
    r"\bconcern(s|ed|ing)?\b",
    r"\bdefici(ent|ency)\b",
    r"\black(s|ed|ing)?\b",
    r"\bnegative\b",
    r"\bunacceptable\b",
    r"\bworrying\b",
    r"\balarming\b",
]

POSITIVE_PATTERNS = [
    r"\bachieved\b",
    r"\bexcellent\b",
    r"\bstrong\b",
    r"\bpositive\b",
    r"\bappropriate\b",
    r"\bgood\b",
    r"\bimproved\b",
    r"\bprogress\b",
    r"\bsuccessful\b",
    r"\beffective\b",
]

EXTREME_QUANTIFIER_PATTERNS = [
    r"\balways\b",
    r"\bnever\b",
    r"\bevery\b",
    r"\bnone\b",
    r"\bcompletely\b",
    r"\btotally\b",
    r"\babsolutely\b",
    r"\ball\b",
]

MODERATE_QUANTIFIER_PATTERNS = [
    r"\bsometimes\b",
    r"\boften\b",
    r"\busually\b",
    r"\bgenerally\b",
    r"\bsomewhat\b",
    r"\bpartially\b",
    r"\bmostly\b",
    r"\bsome\b",
]


def count_pattern_matches(text: str, patterns: List[str]) -> int:
    """Count matches for a list of regex patterns."""
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text, re.IGNORECASE))
    return count


# =============================================================================
# BASELINES
# =============================================================================

@dataclass
class BiasBaseline:
    """Baseline statistics for a document type and metric."""
    baseline_id: str
    doc_type: str
    metric: str
    corpus_size: int
    mean: float
    std_dev: float
    source: str  # "empirical", "estimated", "calibrated"


@dataclass
class BaselineCorpus:
    """Collection of baselines for bias detection."""
    baselines: Dict[Tuple[str, str], BiasBaseline] = field(default_factory=dict)

    def add(self, baseline: BiasBaseline) -> None:
        """Add a baseline to the corpus."""
        key = (baseline.doc_type, baseline.metric)
        self.baselines[key] = baseline

    def get(self, doc_type: str, metric: str) -> Optional[BiasBaseline]:
        """Get a baseline by document type and metric."""
        return self.baselines.get((doc_type, metric))

    def get_all_for_doc_type(self, doc_type: str) -> List[BiasBaseline]:
        """Get all baselines for a document type."""
        return [b for (dt, _), b in self.baselines.items() if dt == doc_type]


def create_default_baselines() -> BaselineCorpus:
    """Create default baseline corpus with estimated values."""
    corpus = BaselineCorpus()

    # Document types commonly analyzed
    doc_types = [
        "section_7_report",
        "section_37_report",
        "psychological_report",
        "social_work_report",
        "cafcass_analysis",
        "witness_statement",
        "court_order",
        "expert_report",
    ]

    for doc_type in doc_types:
        # Certainty ratio baseline (high certainty / total certainty markers)
        # Most professional reports should be moderately hedged
        corpus.add(BiasBaseline(
            baseline_id=f"{doc_type}_certainty",
            doc_type=doc_type,
            metric="certainty_ratio",
            corpus_size=100,
            mean=0.40,  # Expect 40% high certainty markers
            std_dev=0.15,
            source="estimated"
        ))

        # Negative attribution ratio (negative / (negative + positive))
        # Expect some negativity but should be balanced
        corpus.add(BiasBaseline(
            baseline_id=f"{doc_type}_negative",
            doc_type=doc_type,
            metric="negative_ratio",
            corpus_size=100,
            mean=0.45,  # Slightly more negative is expected in concerning cases
            std_dev=0.12,
            source="estimated"
        ))

        # Extreme quantifier ratio
        corpus.add(BiasBaseline(
            baseline_id=f"{doc_type}_extreme",
            doc_type=doc_type,
            metric="extreme_ratio",
            corpus_size=100,
            mean=0.25,  # Most language should be moderate
            std_dev=0.10,
            source="estimated"
        ))

    return corpus


# =============================================================================
# BIAS DETECTION ENGINE
# =============================================================================

class BiasDetectionEngine:
    """Engine for detecting statistical bias in document analysis."""

    def __init__(self, baselines: Optional[BaselineCorpus] = None):
        self.baselines = baselines or create_default_baselines()
        self.z_warning = config.bias_z_warning
        self.z_critical = config.bias_z_critical
        self.min_sample_size = config.bias_min_sample_size

    def analyse(
        self,
        doc_id: str,
        doc_type: str,
        text: str,
        case_id: str = ""
    ) -> List[BiasSignal]:
        """
        Analyse a document for bias signals.

        Args:
            doc_id: Document identifier
            doc_type: Type of document
            text: Document text
            case_id: Case identifier

        Returns:
            List of detected bias signals
        """
        signals = []

        # Normalize document type
        doc_type_normalized = doc_type.lower().replace(" ", "_")

        # 1. Certainty ratio analysis
        certainty_signal = self._analyse_certainty(doc_id, doc_type_normalized, text, case_id)
        if certainty_signal:
            signals.append(certainty_signal)

        # 2. Negative attribution analysis
        negative_signal = self._analyse_negativity(doc_id, doc_type_normalized, text, case_id)
        if negative_signal:
            signals.append(negative_signal)

        # 3. Extreme quantifier analysis
        extreme_signal = self._analyse_extremity(doc_id, doc_type_normalized, text, case_id)
        if extreme_signal:
            signals.append(extreme_signal)

        return signals

    def _calculate_z_score(
        self,
        observed: float,
        baseline: BiasBaseline
    ) -> Tuple[float, float]:
        """Calculate z-score and p-value."""
        if baseline.std_dev <= 0:
            return 0.0, 1.0

        z = (observed - baseline.mean) / baseline.std_dev

        # Calculate p-value if scipy available
        if SCIPY_AVAILABLE:
            p_value = 2 * (1 - stats.norm.cdf(abs(z)))  # Two-tailed
        else:
            # Approximate p-value for common z-scores
            if abs(z) >= 2.576:
                p_value = 0.01
            elif abs(z) >= 1.96:
                p_value = 0.05
            elif abs(z) >= 1.645:
                p_value = 0.10
            else:
                p_value = 0.5

        return z, p_value

    def _get_severity(self, z_score: float) -> Severity:
        """Determine severity based on z-score."""
        abs_z = abs(z_score)
        if abs_z >= self.z_critical:
            return Severity.HIGH
        elif abs_z >= self.z_warning:
            return Severity.MEDIUM
        else:
            return Severity.LOW

    def _analyse_certainty(
        self,
        doc_id: str,
        doc_type: str,
        text: str,
        case_id: str
    ) -> Optional[BiasSignal]:
        """Analyse certainty language ratio."""
        high_count = count_pattern_matches(text, CERTAINTY_HIGH_PATTERNS)
        low_count = count_pattern_matches(text, CERTAINTY_LOW_PATTERNS)
        total = high_count + low_count

        if total < self.min_sample_size:
            return None

        ratio = high_count / total
        baseline = self.baselines.get(doc_type, "certainty_ratio")

        if not baseline:
            # Use default if no specific baseline
            baseline = BiasBaseline(
                "default_certainty", "default", "certainty_ratio",
                100, 0.40, 0.15, "default"
            )

        z_score, p_value = self._calculate_z_score(ratio, baseline)

        if abs(z_score) >= self.z_warning:
            direction = "higher" if z_score > 0 else "lower"
            return BiasSignal(
                signal_id=uuid4(),
                document_id=doc_id,
                case_id=case_id,
                signal_type="certainty_language",
                metric_value=ratio,
                baseline_mean=baseline.mean,
                baseline_std=baseline.std_dev,
                z_score=z_score,
                p_value=p_value,
                description=f"Certainty language is {direction} than typical for {doc_type} "
                           f"(ratio: {ratio:.2f}, expected: {baseline.mean:.2f}, z={z_score:.2f})",
                severity=self._get_severity(z_score),
                direction=direction,
                baseline_id=baseline.baseline_id,
                baseline_source=baseline.source
            )

        return None

    def _analyse_negativity(
        self,
        doc_id: str,
        doc_type: str,
        text: str,
        case_id: str
    ) -> Optional[BiasSignal]:
        """Analyse negative attribution ratio."""
        neg_count = count_pattern_matches(text, NEGATIVE_PATTERNS)
        pos_count = count_pattern_matches(text, POSITIVE_PATTERNS)
        total = neg_count + pos_count

        if total < self.min_sample_size:
            return None

        ratio = neg_count / total
        baseline = self.baselines.get(doc_type, "negative_ratio")

        if not baseline:
            baseline = BiasBaseline(
                "default_negative", "default", "negative_ratio",
                100, 0.45, 0.12, "default"
            )

        z_score, p_value = self._calculate_z_score(ratio, baseline)

        if abs(z_score) >= self.z_warning:
            direction = "higher" if z_score > 0 else "lower"
            return BiasSignal(
                signal_id=uuid4(),
                document_id=doc_id,
                case_id=case_id,
                signal_type="negative_attribution",
                metric_value=ratio,
                baseline_mean=baseline.mean,
                baseline_std=baseline.std_dev,
                z_score=z_score,
                p_value=p_value,
                description=f"Negative language is {direction} than typical for {doc_type} "
                           f"(ratio: {ratio:.2f}, expected: {baseline.mean:.2f}, z={z_score:.2f})",
                severity=self._get_severity(z_score),
                direction=direction,
                baseline_id=baseline.baseline_id,
                baseline_source=baseline.source
            )

        return None

    def _analyse_extremity(
        self,
        doc_id: str,
        doc_type: str,
        text: str,
        case_id: str
    ) -> Optional[BiasSignal]:
        """Analyse extreme quantifier usage."""
        extreme_count = count_pattern_matches(text, EXTREME_QUANTIFIER_PATTERNS)
        moderate_count = count_pattern_matches(text, MODERATE_QUANTIFIER_PATTERNS)
        total = extreme_count + moderate_count

        if total < self.min_sample_size:
            return None

        ratio = extreme_count / total
        baseline = self.baselines.get(doc_type, "extreme_ratio")

        if not baseline:
            baseline = BiasBaseline(
                "default_extreme", "default", "extreme_ratio",
                100, 0.25, 0.10, "default"
            )

        z_score, p_value = self._calculate_z_score(ratio, baseline)

        if abs(z_score) >= self.z_warning:
            direction = "higher" if z_score > 0 else "lower"
            return BiasSignal(
                signal_id=uuid4(),
                document_id=doc_id,
                case_id=case_id,
                signal_type="quantifier_extremity",
                metric_value=ratio,
                baseline_mean=baseline.mean,
                baseline_std=baseline.std_dev,
                z_score=z_score,
                p_value=p_value,
                description=f"Use of extreme quantifiers is {direction} than typical "
                           f"(ratio: {ratio:.2f}, expected: {baseline.mean:.2f}, z={z_score:.2f})",
                severity=self._get_severity(z_score),
                direction=direction,
                baseline_id=baseline.baseline_id,
                baseline_source=baseline.source
            )

        return None

    def analyse_entity_attribution(
        self,
        claims: List[dict],
        entity_id: str,
        case_id: str
    ) -> Optional[BiasSignal]:
        """
        Analyse if an entity is disproportionately associated with negative claims.

        Args:
            claims: List of claim dicts with entity associations
            entity_id: The entity to analyse
            case_id: Case identifier

        Returns:
            BiasSignal if attribution asymmetry detected
        """
        # Count claims about this entity
        entity_claims = [c for c in claims if entity_id in str(c.get("about_entity_ids", []))]
        if len(entity_claims) < self.min_sample_size:
            return None

        # Count negative vs positive claims
        negative = sum(1 for c in entity_claims if c.get("sentiment") == "negative")
        positive = sum(1 for c in entity_claims if c.get("sentiment") == "positive")
        total = negative + positive

        if total < self.min_sample_size:
            return None

        entity_negative_ratio = negative / total

        # Compare to overall case negative ratio
        all_negative = sum(1 for c in claims if c.get("sentiment") == "negative")
        all_positive = sum(1 for c in claims if c.get("sentiment") == "positive")
        all_total = all_negative + all_positive

        if all_total < self.min_sample_size:
            return None

        overall_ratio = all_negative / all_total

        # Chi-square test for independence
        if SCIPY_AVAILABLE and NUMPY_AVAILABLE:
            observed = np.array([[negative, positive],
                                [all_negative - negative, all_positive - positive]])
            if observed.min() >= 5:  # Chi-square validity check
                chi2, p_value, dof, expected = stats.chi2_contingency(observed)

                # Effect size (Cramér's V)
                n = observed.sum()
                effect_size = (chi2 / n) ** 0.5

                if p_value < 0.05 and effect_size > 0.1:
                    direction = "higher" if entity_negative_ratio > overall_ratio else "lower"
                    return BiasSignal(
                        signal_id=uuid4(),
                        document_id="case_level",
                        case_id=case_id,
                        signal_type="attribution_asymmetry",
                        metric_value=entity_negative_ratio,
                        baseline_mean=overall_ratio,
                        baseline_std=0.1,  # Placeholder
                        z_score=chi2 ** 0.5 * (1 if direction == "higher" else -1),
                        p_value=p_value,
                        description=f"Entity has {direction} negative attribution than average "
                                   f"(entity: {entity_negative_ratio:.2f}, overall: {overall_ratio:.2f}, "
                                   f"χ²={chi2:.2f}, p={p_value:.4f})",
                        severity=Severity.HIGH if p_value < 0.01 else Severity.MEDIUM,
                        direction=direction,
                        baseline_id="entity_attribution",
                        baseline_source="chi_square"
                    )

        return None

    def generate_bias_report(
        self,
        signals: List[BiasSignal],
        case_id: str
    ) -> dict:
        """
        Generate a comprehensive bias report.

        Args:
            signals: List of detected bias signals
            case_id: Case identifier

        Returns:
            Report dictionary
        """
        return {
            "case_id": case_id,
            "total_signals": len(signals),
            "by_severity": {
                "critical": len([s for s in signals if s.severity == Severity.CRITICAL]),
                "high": len([s for s in signals if s.severity == Severity.HIGH]),
                "medium": len([s for s in signals if s.severity == Severity.MEDIUM]),
                "low": len([s for s in signals if s.severity == Severity.LOW]),
            },
            "by_type": {
                "certainty": len([s for s in signals if s.signal_type == "certainty_language"]),
                "negativity": len([s for s in signals if s.signal_type == "negative_attribution"]),
                "extremity": len([s for s in signals if s.signal_type == "quantifier_extremity"]),
                "attribution": len([s for s in signals if s.signal_type == "attribution_asymmetry"]),
            },
            "signals": [
                {
                    "id": str(s.signal_id),
                    "type": s.signal_type,
                    "severity": s.severity.value,
                    "z_score": s.z_score,
                    "p_value": s.p_value,
                    "description": s.description,
                }
                for s in sorted(signals, key=lambda x: abs(x.z_score), reverse=True)
            ]
        }
