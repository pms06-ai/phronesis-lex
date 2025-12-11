# Detection Engines Analysis - FastAPI Migration Guide

**Source Location:** `c:\Users\pstep\phronesis-lex-1\backend\fcip\engines\`

This document analyzes the contradiction detection and bias detection engines from the FCIP v5.0 system for adaptation to FastAPI backend.

---

## 1. CONTRADICTION DETECTION ENGINE

**File:** `c:\Users\pstep\phronesis-lex-1\backend\fcip\engines\contradiction.py`

### Overview
Systematic detection of contradictions across legal documents. Identifies 8 types of contradictions with legal significance tied to UK case law.

### Contradiction Types Detected

| Type | Severity | Description | Case Law |
|------|----------|-------------|----------|
| **SELF_CONTRADICTION** | CRITICAL | Same author contradicts themselves | Re H-C [2016] EWCA Civ 136 (Lucas direction) |
| **MODALITY_SHIFT** | HIGH | Allegations treated as established facts | Re B [2008] UKHL 35 |
| **DIRECT** | HIGH | Opposite assertions about same subject | Re A (A Child) [2015] EWFC 11 |
| **TEMPORAL** | HIGH | Timeline impossibilities | General evidential principles |
| **QUOTATION** | HIGH | Misrepresented quotes | Professional conduct obligations |
| **ATTRIBUTION** | MEDIUM | Disputes about who said/did what | General evidential principles |
| **VALUE** | MEDIUM | Different numbers for same attribute | General evidential principles |
| **OMISSION** | MEDIUM | Material context omitted | Duty of full and frank disclosure |

### Core Algorithm Components

#### 1. Semantic Similarity Calculation
```python
# Uses three fallback levels:
# - Primary: SentenceTransformer ('all-MiniLM-L6-v2')
# - Secondary: RapidFuzz token_sort_ratio
# - Tertiary: Basic word overlap (Jaccard similarity)

def _calculate_semantic_similarity(text_a: str, text_b: str) -> float:
    # Returns 0.0 to 1.0
    # Threshold: 0.6 for most comparisons
```

**Key Parameters:**
- `semantic_threshold`: 0.6 (default) - Minimum similarity to compare claims
- `polarity_threshold`: 0.8 (default) - Minimum confidence for opposition

#### 2. Polarity Opposition Detection
```python
def _check_polarity_opposition(text_a: str, text_b: str) -> Tuple[bool, float]:
    # Returns (is_opposite, confidence)
```

**Detection Methods:**
- **Explicit negation patterns:** Regular expressions for "did/did not", "was/was not", etc.
- **Polarity opposite words:** Dictionary lookup (e.g., "attended" vs "did not attend")
- **Confidence scoring:** 0.9 for explicit negations, 0.85 for word opposites

**Polarity Dictionary (Sample):**
```python
POLARITY_OPPOSITES = {
    "attended": ["did not attend", "failed to attend", "was absent"],
    "cooperated": ["refused to cooperate", "did not cooperate"],
    "engaged": ["did not engage", "refused to engage"],
    "truthful": ["lied", "untruthful", "dishonest", "fabricated"],
    # ... 15+ predefined pairs
}
```

#### 3. Self-Contradiction Detection
**Most Legally Significant**

```python
def _detect_self_contradictions(claims: List[dict], case_id: str) -> List[Contradiction]:
    # Groups claims by author
    # Compares all pairs from same author
    # Lower threshold (0.7) vs direct contradictions
    # Automatically elevates severity to CRITICAL
```

**Logic:**
1. Group all claims by `asserted_by` field
2. For each author with 2+ claims:
   - Compare all pairs (n^2 complexity)
   - Check semantic similarity >= 0.6
   - Check polarity opposition >= 0.7
   - Flag as CRITICAL severity

#### 4. Modality Shift Detection
**Violations of Re B Standard**

```python
def _detect_modality_shifts(claims: List[dict], case_id: str) -> List[Contradiction]:
    # Finds allegations treated as proven facts
```

**Logic:**
1. Separate claims into `modality == "alleged"` and `modality == "asserted"`
2. For each alleged + asserted pair:
   - Check semantic similarity >= 0.7 (higher threshold)
   - Look for fact indicators: "established", "confirmed", "clear that", "the fact that"
   - Flag if asserted claim treats allegation as proven without evidence

**Legal Significance:** Violates Re B [2008] requirement that facts must be proved on balance of probabilities.

#### 5. Temporal Contradiction Detection

```python
def _detect_temporal_contradictions(claims: List[dict], case_id: str) -> List[Contradiction]:
    # Detects timeline impossibilities
```

**Logic:**
1. Filter claims with `time_start` or `time_expression`
2. For each pair:
   - Check semantic similarity >= 0.6 (about same event)
   - Compare dates: if different dates for similar events, flag
3. Calculate `temporal_gap_days` if dates parseable

#### 6. Value Contradiction Detection

```python
def _detect_value_contradictions(claims: List[dict], case_id: str) -> List[Contradiction]:
    # Detects different numbers for same attribute
```

**Logic:**
1. Extract numbers using regex: `\b(\d+(?:\.\d+)?)\s*(times?|occasions?|days?|weeks?|months?|years?|hours?)\b`
2. For each pair with numbers:
   - Check semantic similarity >= 0.5 (lower threshold)
   - Compare numbers with same units
   - Flag if difference > 20% of larger value

#### 7. Attribution Contradiction Detection

```python
def _detect_attribution_contradictions(claims: List[dict], case_id: str) -> List[Contradiction]:
    # Detects conflicting attribution of statements
```

**Logic:**
1. Extract reported speech with regex: `(\w+(?:\s+\w+)?)\s+(?:stated|said|reported|claimed|alleged|asserted|denied)`
2. For each pair of reported speech:
   - Check semantic similarity >= 0.6
   - If similarity > 0.8 but different speakers, flag
   - Indicates misattribution or confusion

### Data Structures

#### Contradiction Model
```python
@dataclass
class Contradiction:
    contradiction_id: UUID
    case_id: str

    # The conflicting claims
    claim_a_id: UUID
    claim_b_id: UUID
    claim_a_text: str
    claim_b_text: str
    claim_a_source: str  # Document ID
    claim_b_source: str

    # Classification
    contradiction_type: ContradictionType
    severity: Severity

    # Semantic analysis
    semantic_similarity: float
    polarity_opposite: bool

    # Attribution
    claim_a_author: Optional[str]
    claim_b_author: Optional[str]
    same_author: bool  # Critical flag

    # Temporal
    claim_a_date: Optional[str]
    claim_b_date: Optional[str]
    temporal_gap_days: Optional[int]

    # Legal
    explanation: str
    legal_significance: str
    recommended_action: str
    case_law_reference: str

    # Confidence
    confidence: float
    detection_method: str
```

#### ContradictionReport Model
```python
@dataclass
class ContradictionReport:
    case_id: str
    total_contradictions: int
    by_type: Dict[ContradictionType, int]
    by_severity: Dict[Severity, int]
    self_contradictions: List[Contradiction]
    modality_shifts: List[Contradiction]
    critical_findings: List[Contradiction]
    contradictions: List[Contradiction]  # Sorted by severity
    authors_with_self_contradictions: List[str]
    documents_with_most_contradictions: List[Tuple[str, int]]
```

### Key Methods for FastAPI Adaptation

#### Main Entry Point
```python
def detect_contradictions(claims: List[Claim], case_id: str) -> ContradictionReport:
    # Orchestrates all detection types
    # Returns comprehensive report
```

#### Targeted Comparison
```python
def compare_claims(claim_a: Claim, claim_b: Claim, case_id: str) -> Optional[Contradiction]:
    # Compare two specific claims
    # Useful for UI interactions
```

### Dependencies
- **sentence-transformers:** For semantic similarity (optional, has fallbacks)
- **rapidfuzz:** For fuzzy string matching (optional, has fallbacks)
- **Graceful degradation:** Works without ML dependencies using basic word overlap

---

## 2. BIAS DETECTION ENGINE

**File:** `c:\Users\pstep\phronesis-lex-1\backend\fcip\engines\bias.py`

### Overview
Statistical detection of linguistic bias by comparing documents against corpus baselines using z-score analysis.

### Bias Dimensions Analyzed

| Dimension | Metric | Baseline Mean | Std Dev | Description |
|-----------|--------|---------------|---------|-------------|
| **Certainty Language** | certainty_ratio | 0.40 | 0.15 | Ratio of high certainty markers to total |
| **Negative Attribution** | negative_ratio | 0.45 | 0.12 | Ratio of negative to total sentiment words |
| **Quantifier Extremity** | extreme_ratio | 0.25 | 0.10 | Ratio of extreme to total quantifiers |
| **Attribution Asymmetry** | negative_ratio (per entity) | Case average | 0.10 | Entity-specific negative claim ratio |

### Core Algorithm Components

#### 1. Pattern Matching for Linguistic Features

**High Certainty Patterns:**
```python
CERTAINTY_HIGH_PATTERNS = [
    r"\bclearly\b", r"\bobviously\b", r"\bcertainly\b",
    r"\bdefinitely\b", r"\bundoubtedly\b", r"\bwithout doubt\b",
    r"\bplainly\b", r"\bevident(ly)?\b", r"\bestablished\b", r"\bconfirmed\b"
]
```

**Low Certainty Patterns:**
```python
CERTAINTY_LOW_PATTERNS = [
    r"\bperhaps\b", r"\bpossibly\b", r"\bmay\b", r"\bmight\b",
    r"\bappears?\b", r"\bseems?\b", r"\bsuggests?\b", r"\bindicates?\b",
    r"\bcould\b", r"\bunclear\b"
]
```

**Negative Patterns:**
```python
NEGATIVE_PATTERNS = [
    r"\bfailed\b", r"\brefused\b", r"\bunable\b", r"\binadequate\b",
    r"\bpoor\b", r"\bconcern(s|ed|ing)?\b", r"\bdefici(ent|ency)\b",
    r"\black(s|ed|ing)?\b", r"\bnegative\b", r"\bunacceptable\b"
]
```

**Positive Patterns:**
```python
POSITIVE_PATTERNS = [
    r"\bachieved\b", r"\bexcellent\b", r"\bstrong\b", r"\bpositive\b",
    r"\bappropriate\b", r"\bgood\b", r"\bimproved\b", r"\bprogress\b"
]
```

**Extreme Quantifiers:**
```python
EXTREME_QUANTIFIER_PATTERNS = [
    r"\balways\b", r"\bnever\b", r"\bevery\b", r"\bnone\b",
    r"\bcompletely\b", r"\btotally\b", r"\babsolutely\b", r"\ball\b"
]
```

**Moderate Quantifiers:**
```python
MODERATE_QUANTIFIER_PATTERNS = [
    r"\bsometimes\b", r"\boften\b", r"\busually\b", r"\bgenerally\b",
    r"\bsomewhat\b", r"\bpartially\b", r"\bmostly\b", r"\bsome\b"
]
```

#### 2. Z-Score Calculation

```python
def _calculate_z_score(observed: float, baseline: BiasBaseline) -> Tuple[float, float]:
    """
    Z-score formula: z = (observed - mean) / std_dev

    Returns: (z_score, p_value)
    """
    z = (observed - baseline.mean) / baseline.std_dev

    # Two-tailed p-value
    if SCIPY_AVAILABLE:
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    else:
        # Approximation:
        # |z| >= 2.576 → p ≤ 0.01
        # |z| >= 1.96  → p ≤ 0.05
        # |z| >= 1.645 → p ≤ 0.10
```

**Configuration from config.py:**
- `bias_z_warning`: 1.5 (triggers MEDIUM severity)
- `bias_z_critical`: 2.0 (triggers HIGH severity)
- `bias_min_sample_size`: 10 (minimum markers required)

#### 3. Certainty Language Analysis

```python
def _analyse_certainty(doc_id: str, doc_type: str, text: str, case_id: str) -> Optional[BiasSignal]:
    """
    1. Count high certainty markers
    2. Count low certainty markers
    3. Calculate ratio: high / (high + low)
    4. Compare to baseline for doc_type
    5. Calculate z-score
    6. Flag if |z| >= z_warning
    """
```

**Expected Baseline:**
- Professional reports should be moderately hedged
- Mean: 0.40 (40% high certainty)
- Std Dev: 0.15

**Interpretation:**
- **High z-score:** Over-confident language, lack of appropriate hedging
- **Low z-score:** Excessive hedging, uncertainty

#### 4. Negative Attribution Analysis

```python
def _analyse_negativity(doc_id: str, doc_type: str, text: str, case_id: str) -> Optional[BiasSignal]:
    """
    1. Count negative patterns
    2. Count positive patterns
    3. Calculate ratio: negative / (negative + positive)
    4. Compare to baseline
    5. Calculate z-score
    6. Flag if |z| >= z_warning
    """
```

**Expected Baseline:**
- Slightly more negative expected in concerning cases
- Mean: 0.45 (45% negative)
- Std Dev: 0.12

**Interpretation:**
- **High z-score:** Disproportionately negative framing
- **Low z-score:** Potentially minimizing concerns

#### 5. Quantifier Extremity Analysis

```python
def _analyse_extremity(doc_id: str, doc_type: str, text: str, case_id: str) -> Optional[BiasSignal]:
    """
    1. Count extreme quantifiers (always, never, all, none)
    2. Count moderate quantifiers (sometimes, often, usually)
    3. Calculate ratio: extreme / (extreme + moderate)
    4. Compare to baseline
    5. Calculate z-score
    6. Flag if |z| >= z_warning
    """
```

**Expected Baseline:**
- Most language should be moderate
- Mean: 0.25 (25% extreme)
- Std Dev: 0.10

**Interpretation:**
- **High z-score:** Black-and-white thinking, overgeneralization
- **Low z-score:** May indicate appropriate nuance

#### 6. Entity Attribution Asymmetry Analysis

```python
def analyse_entity_attribution(claims: List[dict], entity_id: str, case_id: str) -> Optional[BiasSignal]:
    """
    Chi-square test for independence

    1. Count negative vs positive claims about specific entity
    2. Calculate entity_negative_ratio
    3. Compare to overall case negative_ratio
    4. Perform chi-square test
    5. Calculate effect size (Cramér's V)
    6. Flag if p < 0.05 and effect_size > 0.1
    """
```

**Statistical Test:**
```python
# Contingency table:
#                   Negative   Positive
# About Entity      neg_count  pos_count
# About Others      other_neg  other_pos

chi2, p_value, dof, expected = stats.chi2_contingency(observed)
effect_size = sqrt(chi2 / n)  # Cramér's V

# Significance: p < 0.05 AND effect_size > 0.1
```

**Interpretation:**
- Tests if entity has disproportionate negative attribution
- Controls for overall case negativity
- Effect size ensures practical significance

### Data Structures

#### BiasBaseline Model
```python
@dataclass
class BiasBaseline:
    baseline_id: str
    doc_type: str  # "section_7_report", "psychological_report", etc.
    metric: str    # "certainty_ratio", "negative_ratio", "extreme_ratio"
    corpus_size: int
    mean: float
    std_dev: float
    source: str  # "empirical", "estimated", "calibrated"
```

#### BaselineCorpus Model
```python
@dataclass
class BaselineCorpus:
    baselines: Dict[Tuple[str, str], BiasBaseline]

    def get(doc_type: str, metric: str) -> Optional[BiasBaseline]
    def add(baseline: BiasBaseline) -> None
    def get_all_for_doc_type(doc_type: str) -> List[BiasBaseline]
```

#### BiasSignal Model (from core.py)
```python
class BiasSignal(BaseModel):
    signal_id: UUID
    document_id: str
    case_id: str

    # Signal details
    signal_type: str  # "certainty_language", "negative_attribution", etc.
    metric_value: float  # Observed ratio
    baseline_mean: float
    baseline_std: float
    z_score: float
    p_value: Optional[float]

    # Interpretation
    description: str
    severity: Severity  # Based on z-score thresholds
    direction: str  # "higher" or "lower"

    # Reference
    baseline_id: str
    baseline_source: str
```

### Key Methods for FastAPI Adaptation

#### Main Entry Point
```python
def analyse(doc_id: str, doc_type: str, text: str, case_id: str) -> List[BiasSignal]:
    """
    Analyzes document for all bias dimensions
    Returns list of signals (only those exceeding thresholds)
    """
```

#### Entity-Level Analysis
```python
def analyse_entity_attribution(claims: List[dict], entity_id: str, case_id: str) -> Optional[BiasSignal]:
    """
    Chi-square test for entity attribution bias
    Requires minimum sample size
    """
```

#### Report Generation
```python
def generate_bias_report(signals: List[BiasSignal], case_id: str) -> dict:
    """
    Aggregates signals into summary report
    Groups by severity and type
    Sorts by z-score magnitude
    """
```

### Baseline Management

**Default Baselines Created:**
- section_7_report
- section_37_report
- psychological_report
- social_work_report
- cafcass_analysis
- witness_statement
- court_order
- expert_report

**Baselines are:**
- Currently estimated (source="estimated")
- Should be calibrated with empirical data over time
- Can be customized per jurisdiction/court

### Dependencies
- **scipy:** For z-score p-value calculation (optional, has approximation fallback)
- **numpy:** For chi-square test (optional, required for entity attribution analysis)
- **Graceful degradation:** Core bias detection works without scipy

---

## 3. INTEGRATION REQUIREMENTS FOR FASTAPI

### Shared Dependencies (from core.py)
```python
from ..models.core import (
    Claim, Modality, Polarity, Severity, ClaimType,
    BiasSignal, Entity, Confidence
)
```

### Configuration Requirements
```python
# From config.py
class FCIPConfig:
    # Bias Detection
    bias_z_warning: float = 1.5
    bias_z_critical: float = 2.0
    bias_min_sample_size: int = 10
```

### API Endpoint Recommendations

#### Contradiction Detection Endpoints
```
POST /api/v1/contradiction/detect
  Request: { case_id: str, claims: List[Claim] }
  Response: ContradictionReport

POST /api/v1/contradiction/compare
  Request: { case_id: str, claim_a: Claim, claim_b: Claim }
  Response: Contradiction | null

GET /api/v1/contradiction/report/{case_id}
  Response: ContradictionReport
```

#### Bias Detection Endpoints
```
POST /api/v1/bias/analyze-document
  Request: { doc_id: str, doc_type: str, text: str, case_id: str }
  Response: List[BiasSignal]

POST /api/v1/bias/analyze-entity
  Request: { claims: List[dict], entity_id: str, case_id: str }
  Response: BiasSignal | null

GET /api/v1/bias/report/{case_id}
  Response: { total_signals, by_severity, by_type, signals }

GET /api/v1/bias/baselines/{doc_type}
  Response: List[BiasBaseline]
```

### Database Schema Recommendations

#### Contradictions Table
```sql
CREATE TABLE contradictions (
    contradiction_id UUID PRIMARY KEY,
    case_id VARCHAR NOT NULL,
    claim_a_id UUID NOT NULL REFERENCES claims(claim_id),
    claim_b_id UUID NOT NULL REFERENCES claims(claim_id),
    contradiction_type VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    semantic_similarity FLOAT,
    polarity_opposite BOOLEAN,
    same_author BOOLEAN,
    temporal_gap_days INTEGER,
    confidence FLOAT,
    detection_method VARCHAR,
    explanation TEXT,
    legal_significance TEXT,
    recommended_action TEXT,
    case_law_reference VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_contradictions_case ON contradictions(case_id);
CREATE INDEX idx_contradictions_severity ON contradictions(severity);
CREATE INDEX idx_contradictions_type ON contradictions(contradiction_type);
```

#### Bias Signals Table
```sql
CREATE TABLE bias_signals (
    signal_id UUID PRIMARY KEY,
    document_id VARCHAR NOT NULL,
    case_id VARCHAR NOT NULL,
    signal_type VARCHAR NOT NULL,
    metric_value FLOAT NOT NULL,
    baseline_mean FLOAT NOT NULL,
    baseline_std FLOAT NOT NULL,
    z_score FLOAT NOT NULL,
    p_value FLOAT,
    description TEXT,
    severity VARCHAR NOT NULL,
    direction VARCHAR NOT NULL,
    baseline_id VARCHAR,
    baseline_source VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bias_signals_case ON bias_signals(case_id);
CREATE INDEX idx_bias_signals_doc ON bias_signals(document_id);
CREATE INDEX idx_bias_signals_severity ON bias_signals(severity);
```

#### Bias Baselines Table
```sql
CREATE TABLE bias_baselines (
    baseline_id VARCHAR PRIMARY KEY,
    doc_type VARCHAR NOT NULL,
    metric VARCHAR NOT NULL,
    corpus_size INTEGER NOT NULL,
    mean FLOAT NOT NULL,
    std_dev FLOAT NOT NULL,
    source VARCHAR NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(doc_type, metric)
);
```

---

## 4. PERFORMANCE OPTIMIZATION STRATEGIES

### Contradiction Detection

**Current Complexity:**
- Direct contradictions: O(n^2) per subject group
- Self-contradictions: O(n^2) per author
- Other types: O(n^2) worst case

**Optimization Strategies:**
1. **Batch processing:** Process claims in batches
2. **Caching:** Cache semantic embeddings for reuse
3. **Parallel processing:** Use asyncio for independent comparisons
4. **Indexing:** Pre-group claims by subject/author
5. **Early termination:** Skip low-confidence pairs early

**Recommended Thresholds for Large Cases:**
- Max claims per comparison: 1000
- Use sampling for cases > 5000 claims
- Cache embeddings in Redis for 24 hours

### Bias Detection

**Current Complexity:**
- Pattern matching: O(n) where n = document length
- Entity attribution: O(m * c) where m = entities, c = claims

**Optimization Strategies:**
1. **Compiled regex:** Compile patterns once at startup
2. **Concurrent analysis:** Run all bias dimensions in parallel
3. **Lazy baseline loading:** Load baselines on-demand
4. **Result caching:** Cache document-level bias scores

---

## 5. TESTING REQUIREMENTS

### Unit Tests Needed

#### Contradiction Detection
```python
test_semantic_similarity_calculation()
test_polarity_opposition_detection()
test_self_contradiction_detection()
test_modality_shift_detection()
test_temporal_contradiction_detection()
test_value_contradiction_detection()
test_attribution_contradiction_detection()
test_deduplication()
test_legal_significance_assignment()
test_report_generation()
```

#### Bias Detection
```python
test_pattern_matching()
test_z_score_calculation()
test_certainty_analysis()
test_negativity_analysis()
test_extremity_analysis()
test_entity_attribution_chi_square()
test_baseline_management()
test_severity_determination()
test_report_generation()
```

### Integration Tests Needed
```python
test_full_contradiction_pipeline()
test_full_bias_pipeline()
test_concurrent_processing()
test_database_persistence()
test_api_endpoints()
test_error_handling()
test_missing_dependencies_fallback()
```

---

## 6. MIGRATION CHECKLIST

### Phase 1: Core Algorithm Migration
- [ ] Port contradiction detection logic to FastAPI service
- [ ] Port bias detection logic to FastAPI service
- [ ] Implement Pydantic models for all data structures
- [ ] Add graceful dependency handling (sentence-transformers, scipy)
- [ ] Write comprehensive unit tests

### Phase 2: Database Integration
- [ ] Create database schemas
- [ ] Implement SQLAlchemy models
- [ ] Add CRUD operations for contradictions
- [ ] Add CRUD operations for bias signals
- [ ] Add baseline management system

### Phase 3: API Development
- [ ] Create FastAPI endpoints for contradiction detection
- [ ] Create FastAPI endpoints for bias analysis
- [ ] Add request/response validation
- [ ] Implement error handling
- [ ] Add API documentation (OpenAPI)

### Phase 4: Optimization
- [ ] Implement caching strategy (Redis)
- [ ] Add batch processing support
- [ ] Enable async processing
- [ ] Add rate limiting
- [ ] Performance testing with large datasets

### Phase 5: Frontend Integration
- [ ] Design UI components for contradiction display
- [ ] Design UI components for bias signal display
- [ ] Create interactive comparison tools
- [ ] Add visualization for contradiction networks
- [ ] Add visualization for bias metrics

---

## 7. KEY INSIGHTS FOR ADAPTATION

### Strengths of Current Implementation
1. **Comprehensive detection:** 8 contradiction types with legal grounding
2. **Statistical rigor:** Z-score analysis with p-values for bias
3. **Graceful degradation:** Works without heavy ML dependencies
4. **Legal significance:** Tied to UK case law and recommended actions
5. **Modular design:** Each detection type is independent

### Areas for Enhancement
1. **Scalability:** Current O(n^2) algorithms need optimization for large cases
2. **Real-time updates:** Design for incremental processing as claims added
3. **Machine learning:** Could add ML-based contradiction detection
4. **Baseline calibration:** Need system for updating baselines with real data
5. **Multi-language:** Currently English-only regex patterns

### Critical Algorithms to Preserve
1. **Polarity opposition detection:** Core logic is solid
2. **Modality shift detection:** Legally sophisticated
3. **Z-score bias analysis:** Statistically sound
4. **Self-contradiction prioritization:** Critical for legal cases
5. **Chi-square entity attribution:** Proper statistical test

### Recommended Simplifications for FastAPI
1. **Remove dataclasses:** Use Pydantic BaseModel throughout
2. **Async-first design:** Make all detection methods async
3. **Database-backed:** Store all results, not just in-memory
4. **API-driven:** Expose all detection methods as endpoints
5. **Event-driven:** Emit events for detected contradictions/bias

---

## SUMMARY

Both engines are production-ready with sophisticated algorithms grounded in legal principles (contradiction) and statistical analysis (bias). The key to successful FastAPI migration is:

1. **Preserve core algorithms** - They're legally and statistically sound
2. **Modernize data layer** - Use Pydantic, SQLAlchemy, async/await
3. **Optimize for scale** - Add caching, batching, parallel processing
4. **Maintain graceful degradation** - Keep fallbacks for optional dependencies
5. **Enhance observability** - Add logging, metrics, tracing for production

The engines are ready to be adapted with minimal changes to core logic.
