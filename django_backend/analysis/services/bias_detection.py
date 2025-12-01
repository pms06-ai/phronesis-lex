"""
Bias Detection Service
Statistical analysis of linguistic patterns against corpus baselines.
"""
import re
import logging
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

from django.db import transaction

logger = logging.getLogger(__name__)

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


# Linguistic patterns for UK legal documents
CERTAINTY_HIGH_PATTERNS = [
    r"\bclearly\b", r"\bobviously\b", r"\bcertainly\b", r"\bdefinitely\b",
    r"\bundoubtedly\b", r"\bwithout doubt\b", r"\bplainly\b",
    r"\bevident(ly)?\b", r"\bestablished\b", r"\bconfirmed\b",
    r"\bmanifest(ly)?\b", r"\bunquestionabl[ye]\b",
]

CERTAINTY_LOW_PATTERNS = [
    r"\bperhaps\b", r"\bpossibly\b", r"\bmay\b", r"\bmight\b",
    r"\bappears?\b", r"\bseems?\b", r"\bsuggests?\b", r"\bindicates?\b",
    r"\bcould\b", r"\bunclear\b", r"\buncertain\b", r"\bpotentially\b",
]

NEGATIVE_PATTERNS = [
    r"\bfailed\b", r"\brefused\b", r"\bunable\b", r"\binadequate\b",
    r"\bpoor\b", r"\bconcern(s|ed|ing)?\b", r"\bdefici(ent|ency)\b",
    r"\black(s|ed|ing)?\b", r"\bnegative\b", r"\bunacceptable\b",
    r"\bworrying\b", r"\balarming\b", r"\bunsatisfactory\b",
    r"\buncooperative\b", r"\bdifficult\b", r"\bhostile\b",
]

POSITIVE_PATTERNS = [
    r"\bachieved\b", r"\bexcellent\b", r"\bstrong\b", r"\bpositive\b",
    r"\bappropriate\b", r"\bgood\b", r"\bimproved\b", r"\bprogress\b",
    r"\bsuccessful\b", r"\beffective\b", r"\bcooperative\b",
    r"\bsupportive\b", r"\bwarm\b", r"\battentive\b",
]

EXTREME_QUANTIFIER_PATTERNS = [
    r"\balways\b", r"\bnever\b", r"\bevery\b", r"\bnone\b",
    r"\bcompletely\b", r"\btotally\b", r"\babsolutely\b", r"\ball\b",
    r"\bentirely\b", r"\bwholly\b",
]

MODERATE_QUANTIFIER_PATTERNS = [
    r"\bsometimes\b", r"\boften\b", r"\busually\b", r"\bgenerally\b",
    r"\bsomewhat\b", r"\bpartially\b", r"\bmostly\b", r"\bsome\b",
    r"\bfrequently\b", r"\boccasionally\b",
]


def count_pattern_matches(text: str, patterns: List[str]) -> int:
    """Count matches for regex patterns."""
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text, re.IGNORECASE))
    return count


@dataclass
class BiasSignalResult:
    """Result of bias detection analysis."""
    signal_type: str
    metric_value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    p_value: Optional[float]
    direction: str
    severity: str
    description: str
    baseline_id: str
    baseline_source: str


class BiasDetectionService:
    """
    Service for detecting statistical bias in documents.
    
    Compares document linguistic patterns against corpus baselines
    using z-score analysis.
    """
    
    Z_WARNING = 1.5
    Z_CRITICAL = 2.0
    MIN_SAMPLE_SIZE = 5
    
    def __init__(self):
        self.baselines = {}
        self._load_baselines()
    
    def _load_baselines(self):
        """Load baselines from database."""
        from django_backend.analysis.models import BiasBaseline
        
        try:
            for baseline in BiasBaseline.objects.all():
                key = (baseline.doc_type, baseline.metric)
                self.baselines[key] = {
                    'mean': baseline.mean,
                    'std_dev': baseline.std_dev,
                    'baseline_id': baseline.baseline_id,
                    'source': baseline.source,
                }
        except Exception as e:
            logger.warning(f"Could not load baselines: {e}")
            self._use_default_baselines()
    
    def _use_default_baselines(self):
        """Use default estimated baselines."""
        doc_types = [
            'section_7_report', 'section_37_report', 'psychological_report',
            'social_work_report', 'cafcass_analysis', 'witness_statement',
            'expert_report', 'other'
        ]
        
        for doc_type in doc_types:
            self.baselines[(doc_type, 'certainty_ratio')] = {
                'mean': 0.40, 'std_dev': 0.15,
                'baseline_id': f'{doc_type}_certainty', 'source': 'estimated'
            }
            self.baselines[(doc_type, 'negative_ratio')] = {
                'mean': 0.45, 'std_dev': 0.12,
                'baseline_id': f'{doc_type}_negative', 'source': 'estimated'
            }
            self.baselines[(doc_type, 'extreme_ratio')] = {
                'mean': 0.25, 'std_dev': 0.10,
                'baseline_id': f'{doc_type}_extreme', 'source': 'estimated'
            }
    
    def analyze(
        self,
        text: str,
        doc_type: str
    ) -> List[BiasSignalResult]:
        """
        Analyze document for bias signals.
        
        Args:
            text: Document text
            doc_type: Type of document
            
        Returns:
            List of BiasSignalResult objects
        """
        signals = []
        doc_type_normalized = doc_type.lower().replace(" ", "_").replace("-", "_")
        
        # Certainty analysis
        certainty = self._analyze_certainty(text, doc_type_normalized)
        if certainty:
            signals.append(certainty)
        
        # Negativity analysis
        negativity = self._analyze_negativity(text, doc_type_normalized)
        if negativity:
            signals.append(negativity)
        
        # Extremity analysis
        extremity = self._analyze_extremity(text, doc_type_normalized)
        if extremity:
            signals.append(extremity)
        
        return signals
    
    def _get_baseline(self, doc_type: str, metric: str) -> Dict:
        """Get baseline for document type and metric."""
        baseline = self.baselines.get((doc_type, metric))
        if not baseline:
            baseline = self.baselines.get(('other', metric))
        if not baseline:
            # Default fallback
            defaults = {
                'certainty_ratio': {'mean': 0.40, 'std_dev': 0.15},
                'negative_ratio': {'mean': 0.45, 'std_dev': 0.12},
                'extreme_ratio': {'mean': 0.25, 'std_dev': 0.10},
            }
            return {
                **defaults.get(metric, {'mean': 0.5, 'std_dev': 0.2}),
                'baseline_id': f'default_{metric}',
                'source': 'default'
            }
        return baseline
    
    def _calculate_z_score(
        self,
        observed: float,
        mean: float,
        std_dev: float
    ) -> Tuple[float, Optional[float]]:
        """Calculate z-score and p-value."""
        if std_dev <= 0:
            return 0.0, None
        
        z = (observed - mean) / std_dev
        
        if SCIPY_AVAILABLE:
            p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        else:
            # Approximate p-value
            if abs(z) >= 2.576:
                p_value = 0.01
            elif abs(z) >= 1.96:
                p_value = 0.05
            elif abs(z) >= 1.645:
                p_value = 0.10
            else:
                p_value = 0.5
        
        return z, p_value
    
    def _get_severity(self, z_score: float) -> str:
        """Map z-score to severity."""
        abs_z = abs(z_score)
        if abs_z >= self.Z_CRITICAL:
            return 'high'
        elif abs_z >= self.Z_WARNING:
            return 'medium'
        return 'low'
    
    def _analyze_certainty(self, text: str, doc_type: str) -> Optional[BiasSignalResult]:
        """Analyze certainty language ratio."""
        high_count = count_pattern_matches(text, CERTAINTY_HIGH_PATTERNS)
        low_count = count_pattern_matches(text, CERTAINTY_LOW_PATTERNS)
        total = high_count + low_count
        
        if total < self.MIN_SAMPLE_SIZE:
            return None
        
        ratio = high_count / total
        baseline = self._get_baseline(doc_type, 'certainty_ratio')
        z_score, p_value = self._calculate_z_score(ratio, baseline['mean'], baseline['std_dev'])
        
        if abs(z_score) >= self.Z_WARNING:
            direction = "higher" if z_score > 0 else "lower"
            return BiasSignalResult(
                signal_type='certainty_language',
                metric_value=ratio,
                baseline_mean=baseline['mean'],
                baseline_std=baseline['std_dev'],
                z_score=z_score,
                p_value=p_value,
                direction=direction,
                severity=self._get_severity(z_score),
                description=(
                    f"Certainty language is {direction} than typical for this document type "
                    f"(ratio: {ratio:.2f}, expected: {baseline['mean']:.2f}, z={z_score:.2f}). "
                    f"{'Over-confident language may indicate bias.' if direction == 'higher' else 'Appropriate hedging detected.'}"
                ),
                baseline_id=baseline['baseline_id'],
                baseline_source=baseline['source'],
            )
        
        return None
    
    def _analyze_negativity(self, text: str, doc_type: str) -> Optional[BiasSignalResult]:
        """Analyze negative attribution ratio."""
        neg_count = count_pattern_matches(text, NEGATIVE_PATTERNS)
        pos_count = count_pattern_matches(text, POSITIVE_PATTERNS)
        total = neg_count + pos_count
        
        if total < self.MIN_SAMPLE_SIZE:
            return None
        
        ratio = neg_count / total
        baseline = self._get_baseline(doc_type, 'negative_ratio')
        z_score, p_value = self._calculate_z_score(ratio, baseline['mean'], baseline['std_dev'])
        
        if abs(z_score) >= self.Z_WARNING:
            direction = "higher" if z_score > 0 else "lower"
            return BiasSignalResult(
                signal_type='negative_attribution',
                metric_value=ratio,
                baseline_mean=baseline['mean'],
                baseline_std=baseline['std_dev'],
                z_score=z_score,
                p_value=p_value,
                direction=direction,
                severity=self._get_severity(z_score),
                description=(
                    f"Negative language is {direction} than typical "
                    f"(ratio: {ratio:.2f}, expected: {baseline['mean']:.2f}, z={z_score:.2f}). "
                    f"{'Disproportionately negative language may indicate confirmation bias.' if direction == 'higher' else 'Document appears balanced.'}"
                ),
                baseline_id=baseline['baseline_id'],
                baseline_source=baseline['source'],
            )
        
        return None
    
    def _analyze_extremity(self, text: str, doc_type: str) -> Optional[BiasSignalResult]:
        """Analyze extreme quantifier usage."""
        extreme_count = count_pattern_matches(text, EXTREME_QUANTIFIER_PATTERNS)
        moderate_count = count_pattern_matches(text, MODERATE_QUANTIFIER_PATTERNS)
        total = extreme_count + moderate_count
        
        if total < self.MIN_SAMPLE_SIZE:
            return None
        
        ratio = extreme_count / total
        baseline = self._get_baseline(doc_type, 'extreme_ratio')
        z_score, p_value = self._calculate_z_score(ratio, baseline['mean'], baseline['std_dev'])
        
        if abs(z_score) >= self.Z_WARNING:
            direction = "higher" if z_score > 0 else "lower"
            return BiasSignalResult(
                signal_type='quantifier_extremity',
                metric_value=ratio,
                baseline_mean=baseline['mean'],
                baseline_std=baseline['std_dev'],
                z_score=z_score,
                p_value=p_value,
                direction=direction,
                severity=self._get_severity(z_score),
                description=(
                    f"Use of extreme quantifiers (always/never/all/none) is {direction} than typical "
                    f"(ratio: {ratio:.2f}, expected: {baseline['mean']:.2f}, z={z_score:.2f}). "
                    f"{'Extreme language lacks nuance expected in professional reports.' if direction == 'higher' else 'Appropriate nuanced language detected.'}"
                ),
                baseline_id=baseline['baseline_id'],
                baseline_source=baseline['source'],
            )
        
        return None
    
    def save_signals(
        self,
        signals: List[BiasSignalResult],
        case,
        document
    ) -> int:
        """Save bias signals to database."""
        from django_backend.analysis.models import BiasSignal
        
        created_count = 0
        
        with transaction.atomic():
            for signal in signals:
                BiasSignal.objects.create(
                    case=case,
                    document=document,
                    signal_type=signal.signal_type,
                    severity=signal.severity,
                    metric_value=signal.metric_value,
                    baseline_mean=signal.baseline_mean,
                    baseline_std=signal.baseline_std,
                    z_score=signal.z_score,
                    p_value=signal.p_value,
                    direction=signal.direction,
                    description=signal.description,
                    baseline_id=signal.baseline_id,
                    baseline_source=signal.baseline_source,
                )
                created_count += 1
        
        return created_count

