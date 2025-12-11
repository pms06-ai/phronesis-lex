# Detection Algorithms - Code Reference for FastAPI Adaptation

This document provides the extracted core algorithms from the FCIP v5.0 detection engines, formatted for easy reference during FastAPI implementation.

---

## CONTRADICTION DETECTION - Core Algorithms

### 1. Semantic Similarity Calculation

**Purpose:** Determine if two claims are about the same subject (0.0 to 1.0 score)

**Source:** `contradiction.py` lines 373-398

```python
def _calculate_semantic_similarity(self, text_a: str, text_b: str) -> float:
    """
    Three-tier approach with graceful fallback
    """
    if not text_a or not text_b:
        return 0.0

    # Tier 1: SentenceTransformer (best, requires model)
    if self.enable_semantic and self._model:
        try:
            embeddings = self._model.encode([text_a, text_b], convert_to_tensor=True)
            similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
            return max(0.0, min(1.0, similarity))
        except Exception:
            pass

    # Tier 2: RapidFuzz token sort ratio (good, lightweight)
    if RAPIDFUZZ_AVAILABLE:
        return fuzz.token_sort_ratio(text_a.lower(), text_b.lower()) / 100.0

    # Tier 3: Basic word overlap (Jaccard similarity)
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)
```

**FastAPI Adaptation Notes:**
- Cache sentence transformer model as singleton
- Consider async model inference for large batches
- Store embeddings in Redis for repeat comparisons
- Default threshold: 0.6

---

### 2. Polarity Opposition Detection

**Purpose:** Detect if two claims assert opposite things

**Source:** `contradiction.py` lines 399-433

```python
def _check_polarity_opposition(self, text_a: str, text_b: str) -> Tuple[bool, float]:
    """
    Returns (is_opposite, confidence)
    """
    text_a_lower = text_a.lower()
    text_b_lower = text_b.lower()

    # Method 1: Explicit negation patterns (confidence: 0.9)
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

    # Method 2: Polarity opposite dictionary (confidence: 0.85)
    for word, opposites in self._polarity_index.items():
        if word in text_a_lower:
            for opp in opposites:
                if opp in text_b_lower:
                    return True, 0.85

    return False, 0.0
```

**Polarity Index Construction:**

```python
# From lines 141-157
POLARITY_OPPOSITES = {
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

def _build_polarity_index(self) -> Dict[str, Set[str]]:
    """Build bidirectional index for O(1) lookup"""
    index = {}
    for positive, negatives in POLARITY_OPPOSITES.items():
        index[positive] = set(negatives)
        for neg in negatives:
            if neg not in index:
                index[neg] = set()
            index[neg].add(positive)
    return index
```

**FastAPI Adaptation Notes:**
- Load polarity dictionary from config/database
- Allow custom domain-specific opposites
- Compile regex patterns at startup
- Consider expanding dictionary based on case law terms

---

### 3. Self-Contradiction Detection (Most Critical)

**Purpose:** Find when same author contradicts themselves

**Source:** `contradiction.py` lines 502-571

```python
def _detect_self_contradictions(self, claims: List[dict], case_id: str) -> List[Contradiction]:
    """
    Self-contradiction is CRITICAL severity - most legally significant
    Lower threshold (0.7) because same-author conflicts are devastating
    """
    contradictions = []

    # Step 1: Group by author
    author_groups: Dict[str, List[dict]] = {}
    for claim in claims:
        author = claim.get("asserted_by")
        if author:
            key = author.lower().strip()
            if key not in author_groups:
                author_groups[key] = []
            author_groups[key].append(claim)

    # Step 2: Compare all pairs from same author
    for author, group in author_groups.items():
        if len(group) < 2:
            continue

        for i, claim_a in enumerate(group):
            for claim_b in group[i+1:]:
                # Check semantic similarity
                similarity = self._calculate_semantic_similarity(
                    claim_a.get("text", ""),
                    claim_b.get("text", "")
                )

                # Lower threshold for self-contradiction (0.6 vs 0.7 general)
                if similarity < self.semantic_threshold:
                    continue

                # Check for contradiction
                is_opposite, conf = self._check_polarity_opposition(
                    claim_a.get("text", ""),
                    claim_b.get("text", "")
                )

                # Lower confidence threshold (0.7 vs 0.8 general)
                if is_opposite and conf >= 0.7:
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
                        same_author=True,  # KEY FLAG
                        claim_a_date=claim_a.get("time_start"),
                        claim_b_date=claim_b.get("time_start"),
                        contradiction_type=ContradictionType.SELF_CONTRADICTION,
                        severity=Severity.CRITICAL,  # Always CRITICAL
                        semantic_similarity=similarity,
                        polarity_opposite=True,
                        confidence=conf + 0.1,  # Boost confidence for self-contradiction
                        detection_method="self_contradiction",
                        explanation=f"Self-contradiction by '{author}': "
                                   f"the same person made contradictory statements."
                    )
                    contradictions.append(contradiction)

    return contradictions
```

**Legal Significance (lines 66-73):**

```python
LEGAL_SIGNIFICANCE[ContradictionType.SELF_CONTRADICTION] = {
    "severity": Severity.CRITICAL,
    "case_law": "Re H-C [2016] EWCA Civ 136 (Lucas direction)",
    "explanation": "A witness contradicting their own prior statement raises "
                  "serious credibility issues. Per Lucas, lies must be evaluated "
                  "but may be told for reasons other than guilt.",
    "recommended_action": "Cross-examine on the inconsistency; consider whether "
                         "the contradiction goes to the heart of the witness's account."
}
```

**FastAPI Adaptation Notes:**
- Create dedicated endpoint: `POST /api/v1/contradiction/self-contradictions`
- Index claims by author in database for fast lookup
- Send real-time alerts for CRITICAL self-contradictions
- Track temporal gap between contradictory statements

---

### 4. Modality Shift Detection

**Purpose:** Detect allegations treated as proven facts (Re B violation)

**Source:** `contradiction.py` lines 573-635

```python
def _detect_modality_shifts(self, claims: List[dict], case_id: str) -> List[Contradiction]:
    """
    Detects when allegations are treated as established facts without proof.
    Violates Re B [2008] UKHL 35 - facts must be proved on balance of probabilities.
    """
    contradictions = []

    # Step 1: Separate by modality
    alleged_claims = [c for c in claims if c.get("modality") == "alleged"]
    asserted_claims = [c for c in claims if c.get("modality") == "asserted"]

    # Step 2: Find where allegations become assertions
    for alleged in alleged_claims:
        for asserted in asserted_claims:
            # High threshold - must be clearly same topic
            similarity = self._calculate_semantic_similarity(
                alleged.get("text", ""),
                asserted.get("text", "")
            )

            if similarity >= 0.7:  # Note: Higher than general threshold
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
```

**Fact Indicators to Expand:**

```python
# Additional indicators to consider
FACT_ASSERTION_INDICATORS = [
    # Definitive language
    "established", "confirmed", "demonstrated", "proved", "shown",
    # Truth claims
    "clear that", "evident that", "obvious that", "the fact that",
    # Conclusive language
    "determined", "found that", "concluded that",
    # Certainty markers
    "undoubtedly", "certainly", "definitely", "without doubt"
]

# Provisional language (absence suggests modality shift)
PROVISIONAL_LANGUAGE = [
    "alleged", "claimed", "reportedly", "supposedly",
    "if proved", "if established", "subject to proof"
]
```

**FastAPI Adaptation Notes:**
- Critical for family court cases
- Track proof evidence between allegation and assertion
- Allow manual marking of "proved allegations"
- Generate Re B compliance report

---

### 5. Temporal Contradiction Detection

**Purpose:** Detect timeline impossibilities

**Source:** `contradiction.py` lines 637-688

```python
def _detect_temporal_contradictions(self, claims: List[dict], case_id: str) -> List[Contradiction]:
    """
    Detects when same/similar events have different dates.
    Timeline analysis is often decisive in legal cases.
    """
    contradictions = []

    # Get claims with temporal information
    temporal_claims = [c for c in claims if c.get("time_start") or c.get("time_expression")]

    # Compare pairs
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
```

**Enhanced Temporal Logic:**

```python
def calculate_temporal_gap(date_a: str, date_b: str) -> Optional[int]:
    """Calculate days between two dates"""
    try:
        from datetime import datetime
        d_a = datetime.fromisoformat(date_a.replace('Z', '+00:00'))
        d_b = datetime.fromisoformat(date_b.replace('Z', '+00:00'))
        return abs((d_a - d_b).days)
    except:
        return None

def is_temporal_impossible(event_a: dict, event_b: dict) -> bool:
    """
    Check if two events can't both be true given timeline.
    E.g., "Father visited on 2020-01-15" vs "Father was in hospital 2020-01-14 to 2020-01-20"
    """
    # Requires temporal reasoning engine
    # See temporal.py in engines
    pass
```

**FastAPI Adaptation Notes:**
- Integrate with temporal reasoning engine
- Visualize timeline with conflicting events
- Calculate confidence based on date precision
- Flag impossible sequences (e.g., effect before cause)

---

### 6. Value Contradiction Detection

**Purpose:** Detect different numbers for same attribute

**Source:** `contradiction.py` lines 690-750

```python
def _detect_value_contradictions(self, claims: List[dict], case_id: str) -> List[Contradiction]:
    """
    Detects inconsistent values (dates, amounts, frequencies).
    May indicate estimation, error, or exaggeration.
    """
    contradictions = []

    # Pattern to extract numbers with units
    number_pattern = re.compile(
        r'\b(\d+(?:\.\d+)?)\s*(times?|occasions?|days?|weeks?|months?|years?|hours?)?\b',
        re.IGNORECASE
    )

    # Extract numbers from all claims
    value_claims = []
    for claim in claims:
        text = claim.get("text", "")
        matches = number_pattern.findall(text)
        if matches:
            claim["_numbers"] = [
                (float(m[0]), m[1].lower() if m[1] else "")
                for m in matches
            ]
            value_claims.append(claim)

    # Compare pairs
    for i, claim_a in enumerate(value_claims):
        for claim_b in value_claims[i+1:]:
            # Check semantic similarity (lower threshold for value comparisons)
            similarity = self._calculate_semantic_similarity(
                claim_a.get("text", ""),
                claim_b.get("text", "")
            )

            if similarity < 0.5:  # Lower than general threshold
                continue

            # Compare numbers with same units
            for num_a, unit_a in claim_a.get("_numbers", []):
                for num_b, unit_b in claim_b.get("_numbers", []):
                    # Must have same unit
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
                            break  # One contradiction per pair is enough

    return contradictions
```

**Enhanced Value Patterns:**

```python
# More sophisticated number extraction
VALUE_PATTERNS = {
    'currency': r'[£$€]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
    'percentage': r'(\d+(?:\.\d+)?)\s*%',
    'frequency': r'(\d+)\s*(times?|occasions?|instances?)',
    'duration': r'(\d+)\s*(days?|weeks?|months?|years?|hours?|minutes?)',
    'age': r'(\d+)\s*years?\s*old',
    'count': r'(\d+)\s*(children|visits|meetings|sessions)',
}

def normalize_value(value: float, unit: str) -> Tuple[float, str]:
    """
    Normalize to base units for comparison
    E.g., "2 weeks" -> (14, "days")
    """
    conversions = {
        'weeks': ('days', 7),
        'months': ('days', 30),
        'years': ('days', 365),
    }
    if unit in conversions:
        base_unit, multiplier = conversions[unit]
        return value * multiplier, base_unit
    return value, unit
```

**FastAPI Adaptation Notes:**
- Normalize values before comparison
- Allow tolerance ranges (configurable per metric)
- Track source of each value (contemporaneous vs recollection)
- Flag rounding vs significant discrepancies

---

## BIAS DETECTION - Core Algorithms

### 1. Z-Score Calculation

**Purpose:** Determine statistical significance of bias signal

**Source:** `bias.py` lines 268-293

```python
def _calculate_z_score(self, observed: float, baseline: BiasBaseline) -> Tuple[float, float]:
    """
    Z-score: measures how many standard deviations observed is from baseline mean

    Returns: (z_score, p_value)
    """
    if baseline.std_dev <= 0:
        return 0.0, 1.0

    # Standard z-score formula
    z = (observed - baseline.mean) / baseline.std_dev

    # Calculate two-tailed p-value
    if SCIPY_AVAILABLE:
        # Precise calculation using cumulative distribution function
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    else:
        # Approximation for common significance levels
        if abs(z) >= 2.576:
            p_value = 0.01    # 99% confidence
        elif abs(z) >= 1.96:
            p_value = 0.05    # 95% confidence
        elif abs(z) >= 1.645:
            p_value = 0.10    # 90% confidence
        else:
            p_value = 0.5     # Not significant

    return z, p_value
```

**Severity Mapping:**

```python
def _get_severity(self, z_score: float) -> Severity:
    """Map z-score to severity level"""
    abs_z = abs(z_score)
    if abs_z >= self.z_critical:      # Default: 2.0
        return Severity.HIGH
    elif abs_z >= self.z_warning:     # Default: 1.5
        return Severity.MEDIUM
    else:
        return Severity.LOW
```

**FastAPI Adaptation Notes:**
- Make thresholds configurable per deployment
- Log z-score distribution for baseline calibration
- Add confidence intervals
- Support one-tailed tests for directional hypotheses

---

### 2. Certainty Language Analysis

**Purpose:** Detect over-confident or under-confident language

**Source:** `bias.py` lines 305-352

```python
def _analyse_certainty(self, doc_id: str, doc_type: str, text: str, case_id: str) -> Optional[BiasSignal]:
    """
    Analyzes ratio of high certainty to total certainty markers.
    Professional reports should show appropriate hedging.
    """
    # Count markers
    high_count = count_pattern_matches(text, CERTAINTY_HIGH_PATTERNS)
    low_count = count_pattern_matches(text, CERTAINTY_LOW_PATTERNS)
    total = high_count + low_count

    # Require minimum sample size
    if total < self.min_sample_size:  # Default: 10
        return None

    # Calculate ratio
    ratio = high_count / total

    # Get baseline for this document type
    baseline = self.baselines.get(doc_type, "certainty_ratio")

    if not baseline:
        # Use default if no specific baseline
        baseline = BiasBaseline(
            "default_certainty", "default", "certainty_ratio",
            100, 0.40, 0.15, "default"
        )

    # Calculate statistical significance
    z_score, p_value = self._calculate_z_score(ratio, baseline)

    # Flag if exceeds warning threshold
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
```

**Certainty Patterns:**

```python
# High certainty markers (lines 39-50)
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

# Low certainty markers (lines 52-63)
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
```

**Interpretation:**
- **High z-score (> 1.5):** Over-confident language, lack of appropriate hedging
- **Low z-score (< -1.5):** Excessive hedging, may indicate lack of confidence in findings
- **Expected baseline:** 0.40 (40% high certainty, 60% low certainty)

**FastAPI Adaptation Notes:**
- Expand pattern lists with domain-specific terms
- Track patterns per author to detect individual bias
- Correlate with claim certainty scores
- Generate suggestions for hedging language

---

### 3. Negative Attribution Analysis

**Purpose:** Detect disproportionate negativity in language

**Source:** `bias.py` lines 354-400

```python
def _analyse_negativity(self, doc_id: str, doc_type: str, text: str, case_id: str) -> Optional[BiasSignal]:
    """
    Analyzes ratio of negative to total evaluative language.
    Some negativity expected in concerning cases, but should be proportionate.
    """
    # Count patterns
    neg_count = count_pattern_matches(text, NEGATIVE_PATTERNS)
    pos_count = count_pattern_matches(text, POSITIVE_PATTERNS)
    total = neg_count + pos_count

    if total < self.min_sample_size:
        return None

    # Calculate ratio
    ratio = neg_count / total

    # Get baseline
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
```

**Sentiment Patterns:**

```python
# Negative patterns (lines 65-78)
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

# Positive patterns (lines 80-91)
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
```

**Interpretation:**
- **High z-score:** Disproportionately negative framing, potential confirmation bias
- **Low z-score:** May be minimizing legitimate concerns
- **Expected baseline:** 0.45 (55% positive, 45% negative)

**FastAPI Adaptation Notes:**
- Track negativity per entity mentioned
- Correlate with case outcomes
- Generate balance reports
- Flag sudden shifts in tone between documents

---

### 4. Quantifier Extremity Analysis

**Purpose:** Detect black-and-white thinking vs nuanced language

**Source:** `bias.py` lines 402-448

```python
def _analyse_extremity(self, doc_id: str, doc_type: str, text: str, case_id: str) -> Optional[BiasSignal]:
    """
    Analyzes use of extreme vs moderate quantifiers.
    Extreme quantifiers (always, never) indicate potential overgeneralization.
    """
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
```

**Quantifier Patterns:**

```python
# Extreme quantifiers (lines 93-102)
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

# Moderate quantifiers (lines 104-113)
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
```

**Interpretation:**
- **High z-score:** Overgeneralization, black-and-white thinking
- **Low z-score:** May indicate appropriate nuance
- **Expected baseline:** 0.25 (25% extreme, 75% moderate)

**FastAPI Adaptation Notes:**
- Flag extreme quantifiers for review
- Suggest moderate alternatives
- Track per author/document type
- Correlate with reliability ratings

---

### 5. Entity Attribution Asymmetry (Chi-Square Test)

**Purpose:** Detect if specific entity has disproportionate negative attribution

**Source:** `bias.py` lines 450-524

```python
def analyse_entity_attribution(self, claims: List[dict], entity_id: str, case_id: str) -> Optional[BiasSignal]:
    """
    Chi-square test for independence.
    Tests if entity has disproportionate negative claims vs case average.
    """
    # Count claims about this entity
    entity_claims = [c for c in claims if entity_id in str(c.get("about_entity_ids", []))]
    if len(entity_claims) < self.min_sample_size:
        return None

    # Count negative vs positive for entity
    negative = sum(1 for c in entity_claims if c.get("sentiment") == "negative")
    positive = sum(1 for c in entity_claims if c.get("sentiment") == "positive")
    total = negative + positive

    if total < self.min_sample_size:
        return None

    entity_negative_ratio = negative / total

    # Count overall case negative vs positive
    all_negative = sum(1 for c in claims if c.get("sentiment") == "negative")
    all_positive = sum(1 for c in claims if c.get("sentiment") == "positive")
    all_total = all_negative + all_positive

    if all_total < self.min_sample_size:
        return None

    overall_ratio = all_negative / all_total

    # Chi-square test for independence
    if SCIPY_AVAILABLE and NUMPY_AVAILABLE:
        # Construct contingency table
        observed = np.array([
            [negative, positive],  # Entity
            [all_negative - negative, all_positive - positive]  # Others
        ])

        # Chi-square validity check (all cells >= 5)
        if observed.min() >= 5:
            chi2, p_value, dof, expected = stats.chi2_contingency(observed)

            # Effect size (Cramér's V)
            n = observed.sum()
            effect_size = (chi2 / n) ** 0.5

            # Flag if significant and meaningful effect
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
```

**Chi-Square Test Details:**

```
Null Hypothesis: Entity's negative/positive ratio is same as case average
Alternative: Entity has different ratio (two-tailed)

Contingency Table:
                Negative    Positive
Entity          a           b
Others          c           d

Chi-square = Σ((Observed - Expected)² / Expected)

Effect Size (Cramér's V) = √(χ² / n)
  - 0.1: Small effect
  - 0.3: Medium effect
  - 0.5: Large effect

Significance: p < 0.05 AND V > 0.1
```

**FastAPI Adaptation Notes:**
- Require sentiment classification on claims
- Run for all entities, flag outliers
- Visualize as entity bias network
- Track across document timeline

---

### 6. Pattern Counting Utility

**Purpose:** Core utility for counting regex pattern matches

**Source:** `bias.py` lines 116-121

```python
def count_pattern_matches(text: str, patterns: List[str]) -> int:
    """
    Count total matches across all patterns in list.
    Case-insensitive matching.
    """
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text, re.IGNORECASE))
    return count
```

**Optimization for FastAPI:**

```python
# Compile patterns once at module/class init
class BiasPatterns:
    def __init__(self):
        self.certainty_high = [re.compile(p, re.IGNORECASE) for p in CERTAINTY_HIGH_PATTERNS]
        self.certainty_low = [re.compile(p, re.IGNORECASE) for p in CERTAINTY_LOW_PATTERNS]
        self.negative = [re.compile(p, re.IGNORECASE) for p in NEGATIVE_PATTERNS]
        self.positive = [re.compile(p, re.IGNORECASE) for p in POSITIVE_PATTERNS]
        self.extreme_quant = [re.compile(p, re.IGNORECASE) for p in EXTREME_QUANTIFIER_PATTERNS]
        self.moderate_quant = [re.compile(p, re.IGNORECASE) for p in MODERATE_QUANTIFIER_PATTERNS]

    def count_matches(self, text: str, pattern_list: List[re.Pattern]) -> int:
        """Count matches using pre-compiled patterns"""
        count = 0
        for pattern in pattern_list:
            count += len(pattern.findall(text))
        return count

# Singleton instance
_bias_patterns = BiasPatterns()
```

---

## CONFIGURATION VALUES

### From config.py (lines 1-45)

```python
class FCIPConfig(BaseSettings):
    """Configuration with defaults"""

    # Bias Detection
    bias_z_warning: float = 1.5      # Trigger MEDIUM severity
    bias_z_critical: float = 2.0      # Trigger HIGH severity
    bias_min_sample_size: int = 10    # Minimum markers required

    # Entity Resolution (for contradiction detection)
    entity_fuzzy_threshold: int = 88

    # LLM Settings
    llm_temperature: float = 0.1
    llm_max_tokens: int = 8192

    # Confidence Calibration
    certainty_high_threshold: float = 0.85
    certainty_medium_threshold: float = 0.50
    certainty_low_threshold: float = 0.25
```

---

## SUMMARY OF KEY ADAPTATIONS FOR FASTAPI

1. **Make all detection methods async** - Use `async def` for I/O operations
2. **Cache compiled patterns** - Compile regex at startup, not per-request
3. **Cache semantic embeddings** - Use Redis for embedding cache with TTL
4. **Pydantic models everywhere** - Replace dataclasses with BaseModel
5. **Database-backed results** - Persist all contradictions and bias signals
6. **Batch processing API** - Support analyzing multiple documents/claims at once
7. **Real-time streaming** - WebSocket endpoint for live contradiction detection
8. **Configurable thresholds** - All thresholds in database/config, not hardcoded
9. **Graceful degradation** - Fallback methods when ML libraries unavailable
10. **Comprehensive logging** - Log all detection events for analysis

These algorithms are production-ready and can be directly adapted to FastAPI with minimal changes to core logic.
