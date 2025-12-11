# Detection Engines - Quick Reference Card

Fast lookup for key algorithms, thresholds, and patterns during FastAPI implementation.

---

## CONTRADICTION DETECTION

### Default Thresholds

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `semantic_threshold` | 0.6 | Min similarity to compare claims |
| `polarity_threshold` | 0.8 | Min confidence for opposition (general) |
| `polarity_threshold` (self) | 0.7 | Lower threshold for self-contradictions |
| `semantic_threshold` (modality) | 0.7 | Higher threshold for modality shifts |
| `semantic_threshold` (value) | 0.5 | Lower threshold for value comparisons |
| `value_diff_threshold` | 0.2 | 20% difference triggers flag |

### Severity Mapping

```
SELF_CONTRADICTION → CRITICAL (always)
MODALITY_SHIFT     → HIGH
DIRECT             → HIGH
TEMPORAL           → HIGH
QUOTATION          → HIGH
ATTRIBUTION        → MEDIUM
VALUE              → MEDIUM
OMISSION           → MEDIUM
```

### Confidence Boosters

```python
self_contradiction:  confidence + 0.1
temporal:            similarity * 0.85
modality_shift:      similarity * 0.9
value:               min(0.9, similarity + diff_ratio * 0.5)
```

### Quick Polarity Check

```python
# Returns True if texts assert opposites
explicit_negations = [
    ("did", "did not"),
    ("was", "was not"),
    ("has", "has not"),
    ("attended", "did not attend"),
    ("cooperated", "failed to cooperate"),
    ("engaged", "failed to engage"),
    ("truthful", "lied"),
]
```

---

## BIAS DETECTION

### Default Baselines

| Metric | Mean | Std Dev | Interpretation |
|--------|------|---------|----------------|
| `certainty_ratio` | 0.40 | 0.15 | 40% high certainty expected |
| `negative_ratio` | 0.45 | 0.12 | 45% negative expected |
| `extreme_ratio` | 0.25 | 0.10 | 25% extreme quantifiers |

### Z-Score Thresholds

```
z >= 2.0  → HIGH severity    (p ≤ 0.05)
z >= 1.5  → MEDIUM severity  (p ≤ 0.13)
z < 1.5   → LOW severity
```

### Minimum Sample Sizes

```
Default:                   10 markers
Entity attribution:        10 claims about entity
Chi-square validity:       All cells >= 5
```

### Chi-Square Significance

```
Statistical: p < 0.05
Practical:   Cramér's V > 0.1
Both required to flag
```

---

## LINGUISTIC PATTERNS

### Certainty Language

#### High Certainty (avoid excess)
```regex
clearly|obviously|certainly|definitely|undoubtedly
without doubt|plainly|evident|established|confirmed
```

#### Low Certainty (appropriate hedging)
```regex
perhaps|possibly|may|might|appears|seems
suggests|indicates|could|unclear
```

### Sentiment Language

#### Negative Patterns
```regex
failed|refused|unable|inadequate|poor
concern|deficient|lack|negative|unacceptable
worrying|alarming
```

#### Positive Patterns
```regex
achieved|excellent|strong|positive|appropriate
good|improved|progress|successful|effective
```

### Quantifiers

#### Extreme (overgeneralization risk)
```regex
always|never|every|none|completely
totally|absolutely|all
```

#### Moderate (appropriate nuance)
```regex
sometimes|often|usually|generally|somewhat
partially|mostly|some
```

---

## VALUE EXTRACTION

### Number Patterns

```python
# Basic number with unit
r'\b(\d+(?:\.\d+)?)\s*(times?|occasions?|days?|weeks?|months?|years?|hours?)?\b'

# Currency
r'[£$€]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'

# Percentage
r'(\d+(?:\.\d+)?)\s*%'

# Age
r'(\d+)\s*years?\s*old'
```

### Unit Normalization

```python
weeks  → days (× 7)
months → days (× 30)
years  → days (× 365)
```

---

## TEMPORAL PATTERNS

### Expressions to Extract

```python
# Absolute dates
r'\d{1,2}/\d{1,2}/\d{4}'
r'\d{4}-\d{2}-\d{2}'
r'\d{1,2}\s+(?:January|February|...)\s+\d{4}'

# Relative dates
r'(\d+)\s+(days?|weeks?|months?)\s+(?:ago|later|before|after)'

# Ranges
r'from\s+(.+?)\s+to\s+(.+)'
r'between\s+(.+?)\s+and\s+(.+)'
```

---

## ATTRIBUTION PATTERNS

### Reported Speech

```python
r'(?:(\w+(?:\s+\w+)?)\s+(?:stated|said|reported|claimed|alleged|asserted|denied))'
```

Captures speaker name before speech verb.

---

## FACT ASSERTION INDICATORS

### Modality Shift Detection

```python
# Treating allegations as facts (red flags)
established|confirmed|demonstrated|proved|shown
clear that|evident that|obvious that|the fact that
determined|found that|concluded that
undoubtedly|certainly|definitely|without doubt

# Appropriate provisional language
alleged|claimed|reportedly|supposedly
if proved|if established|subject to proof
```

---

## LEGAL CASE LAW REFERENCES

### Quick Lookup

```
SELF_CONTRADICTION → Re H-C [2016] EWCA Civ 136 (Lucas direction)
MODALITY_SHIFT     → Re B [2008] UKHL 35
DIRECT             → Re A (A Child) [2015] EWFC 11
OMISSION           → Duty of full and frank disclosure
```

---

## ALGORITHM COMPLEXITY

### Time Complexity

```
Contradiction Detection:
- Per contradiction type: O(n²) where n = claims
- Optimized by grouping: O(k * m²) where k = groups, m = avg group size
- Self-contradiction: O(a * c²) where a = authors, c = claims per author

Bias Detection:
- Pattern matching: O(n) where n = document length
- Entity attribution: O(e * c) where e = entities, c = claims

Database Queries:
- Claims by author: O(1) with index
- Claims by subject: O(1) with index
- Claims by entity: O(1) with index
```

### Optimization Targets

```
Large case (>1000 claims):
- Use batch processing
- Cache semantic embeddings
- Parallel processing per contradiction type
- Sample if >5000 claims

Real-time detection:
- Process incrementally as claims added
- Store embeddings in Redis (TTL: 24h)
- Use compiled regex patterns
- Async all I/O operations
```

---

## FASTAPI ENDPOINT STRUCTURE

### Contradiction Endpoints

```
POST   /api/v1/contradiction/detect
       { case_id, claims[] } → ContradictionReport

POST   /api/v1/contradiction/compare
       { case_id, claim_a, claim_b } → Contradiction?

GET    /api/v1/contradiction/report/{case_id}
       → ContradictionReport

GET    /api/v1/contradiction/self/{case_id}
       → List[Contradiction] (CRITICAL only)

WS     /api/v1/contradiction/stream/{case_id}
       → Real-time contradiction detection
```

### Bias Endpoints

```
POST   /api/v1/bias/analyze-document
       { doc_id, doc_type, text, case_id } → List[BiasSignal]

POST   /api/v1/bias/analyze-entity
       { claims[], entity_id, case_id } → BiasSignal?

GET    /api/v1/bias/report/{case_id}
       → BiasReport

GET    /api/v1/bias/baselines/{doc_type}
       → List[BiasBaseline]

PUT    /api/v1/bias/baselines/{doc_type}/{metric}
       { mean, std_dev, corpus_size } → BiasBaseline
```

---

## DATABASE INDEXES

### Required for Performance

```sql
-- Contradictions
CREATE INDEX idx_contradictions_case ON contradictions(case_id);
CREATE INDEX idx_contradictions_severity ON contradictions(severity);
CREATE INDEX idx_contradictions_type ON contradictions(contradiction_type);
CREATE INDEX idx_contradictions_claims ON contradictions(claim_a_id, claim_b_id);

-- Claims (for detection)
CREATE INDEX idx_claims_case ON claims(case_id);
CREATE INDEX idx_claims_author ON claims(asserted_by);
CREATE INDEX idx_claims_subject ON claims(subject);
CREATE INDEX idx_claims_modality ON claims(modality);
CREATE INDEX idx_claims_document ON claims(document_id);

-- Bias Signals
CREATE INDEX idx_bias_case ON bias_signals(case_id);
CREATE INDEX idx_bias_doc ON bias_signals(document_id);
CREATE INDEX idx_bias_severity ON bias_signals(severity);
CREATE INDEX idx_bias_type ON bias_signals(signal_type);
```

---

## CACHING STRATEGY

### Redis Keys

```
# Semantic embeddings
embedding:{claim_id} → vector (TTL: 24h)

# Document analysis
bias:{doc_id}:{metric} → BiasSignal (TTL: 1h)

# Baseline corpus
baseline:{doc_type}:{metric} → BiasBaseline (TTL: 7d)

# Compiled patterns (persistent)
patterns:bias:certainty_high → List[str]
patterns:bias:negative → List[str]
patterns:polarity_opposites → Dict[str, List[str]]
```

---

## ERROR HANDLING

### Graceful Degradation

```python
# Semantic similarity
try:
    SentenceTransformer → use
except:
    try:
        RapidFuzz → use
    except:
        Jaccard similarity → use

# Z-score p-value
try:
    scipy.stats.norm.cdf → use
except:
    Lookup table approximation → use

# Chi-square test
try:
    scipy.stats.chi2_contingency → use
except:
    Skip entity attribution analysis
```

### Minimum Requirements

```python
# Works without any ML dependencies:
✓ Polarity opposition (regex)
✓ Value contradictions (regex + math)
✓ Basic semantic similarity (Jaccard)
✓ Bias pattern matching (regex)
✓ Z-score calculation (pure math)

# Requires scipy/numpy:
✗ Chi-square entity attribution
✗ Precise p-values

# Requires sentence-transformers:
✗ High-quality semantic similarity
```

---

## VALIDATION RULES

### Request Validation

```python
# Contradiction detection
min_claims: 2
max_claims_per_batch: 1000

# Bias analysis
min_text_length: 100 chars
max_text_length: 1MB

# Entity attribution
min_entity_claims: 10
min_case_claims: 20
```

### Response Validation

```python
# All scores 0.0-1.0
0 <= semantic_similarity <= 1
0 <= confidence <= 1
0 <= polarity_confidence <= 1

# Z-scores typically -5 to +5
-10 <= z_score <= 10

# P-values 0-1
0 <= p_value <= 1
```

---

## TESTING CHECKLIST

### Unit Tests

```
✓ Semantic similarity with known pairs
✓ Polarity opposition detection
✓ Z-score calculation accuracy
✓ Pattern matching counts
✓ Value extraction and normalization
✓ Baseline management
✓ Severity determination
```

### Integration Tests

```
✓ Full contradiction pipeline
✓ Full bias pipeline
✓ Database persistence
✓ Cache hit/miss scenarios
✓ Graceful degradation paths
✓ Error handling
```

### Performance Tests

```
✓ 100 claims in <1s
✓ 1000 claims in <10s
✓ 10000 claims with sampling
✓ Concurrent requests (10 users)
✓ Cache effectiveness (>80% hit rate)
```

---

## MONITORING METRICS

### Key Metrics to Track

```
# Detection rates
contradictions_detected_total{type, severity}
bias_signals_detected_total{type, severity}

# Performance
detection_duration_seconds{engine}
semantic_similarity_duration_ms
pattern_matching_duration_ms

# Cache
cache_hit_rate{key_type}
cache_size_bytes

# Quality
false_positive_rate (from user feedback)
precision_at_k (top k contradictions are valid)
```

---

## QUICK DECISION TREE

### When to flag a contradiction?

```
Is semantic_similarity >= threshold?
  NO → Skip
  YES ↓

Are claims from same document?
  YES → Skip (internal consistency)
  NO ↓

Is polarity opposite?
  NO → Skip
  YES ↓

Is confidence >= threshold?
  NO → Skip
  YES ↓

Are authors same?
  YES → CRITICAL self-contradiction
  NO ↓

Is modality shift (alleged→asserted)?
  YES → HIGH modality shift
  NO ↓

Is temporal conflict?
  YES → HIGH temporal
  NO ↓

Is value conflict?
  YES → MEDIUM value
  NO → HIGH direct
```

### When to flag a bias signal?

```
Count pattern matches
  < min_sample_size → Skip
  >= min_sample_size ↓

Calculate ratio
  ratio = matching / total ↓

Get baseline for doc_type
  Not found? Use default ↓

Calculate z-score
  |z| < z_warning (1.5) → Skip
  |z| >= z_warning ↓

Determine severity
  |z| >= z_critical (2.0) → HIGH
  |z| >= z_warning (1.5) → MEDIUM
  |z| < z_warning → LOW ↓

Create BiasSignal
```

---

## COMMON PITFALLS

### Avoid These Mistakes

```
❌ Comparing claims from same document for direct contradictions
✓ Skip same-document pairs (internal consistency different)

❌ Using generic threshold for all contradiction types
✓ Adjust thresholds per type (self: 0.7, modality: 0.7, general: 0.8)

❌ Flagging every z-score deviation
✓ Require minimum sample size AND threshold

❌ Treating all contradictions equally
✓ Prioritize: CRITICAL > HIGH > MEDIUM

❌ Running O(n²) on all claims
✓ Group by subject/author first

❌ Ignoring temporal information
✓ Track dates, calculate gaps

❌ Hardcoding baselines
✓ Store in database, allow calibration

❌ Regex patterns with word boundaries on multiword phrases
✓ Use \b only around complete word patterns
```

---

## PRODUCTION DEPLOYMENT

### Environment Variables

```bash
# Bias Detection
FCIP_BIAS_Z_WARNING=1.5
FCIP_BIAS_Z_CRITICAL=2.0
FCIP_BIAS_MIN_SAMPLE_SIZE=10

# Performance
FCIP_MAX_CLAIMS_PER_BATCH=1000
FCIP_ENABLE_CACHING=true
FCIP_CACHE_TTL_HOURS=24

# Dependencies
FCIP_ENABLE_SENTENCE_TRANSFORMERS=true
FCIP_SENTENCE_MODEL=all-MiniLM-L6-v2
```

### Health Check Endpoints

```
GET /health/detection-engines
{
  "status": "healthy",
  "dependencies": {
    "sentence_transformers": true,
    "rapidfuzz": true,
    "scipy": true,
    "numpy": true
  },
  "performance": {
    "avg_detection_ms": 245,
    "cache_hit_rate": 0.87
  }
}
```

---

## VERSION COMPATIBILITY

### Current Implementation

```
Python: 3.10+
Pydantic: 2.0+
FastAPI: 0.100+

Optional:
- sentence-transformers: 2.2+
- rapidfuzz: 3.0+
- scipy: 1.10+
- numpy: 1.24+
```

---

This quick reference covers the essential information needed during FastAPI implementation. Refer to the full analysis documents for detailed explanations and legal context.
