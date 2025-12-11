# PHRONESIS: IMPLEMENTATION PROMPT FOR CLAUDE CODE
## Technical Specification for Terminal Agent

**Project:** Forensic Documentary Analysis System
**Client:** Paul Stephen
**Architect:** Claude (Chat Interface)
**Implementer:** Claude Code (Terminal Agent)

---

## EXECUTIVE SUMMARY FOR CLAUDE CODE

You are building **PHRONESIS** - a violation-centered evidence analysis system for a broadcasting complaint case. The system analyzes documentary content, cross-references with known facts, and generates legally-usable evidence packages.

**Core Philosophy:** Start with alleged violations → Request only evidence needed to prove each → Assess strength honestly.

**Your Mission:** Build the processing pipeline that takes raw inputs (transcripts, documents, correspondence) and outputs structured violation reports with evidence linkage.

---

## PART 1: PROJECT CONTEXT

### The Case
- Paul and Samantha Stephen were arrested for conspiracy to murder but never charged (NFA - No Further Action)
- Channel 4 broadcast documentary showing their arrest/custody footage despite 12+ consent refusals
- Documentary portrayed them as suspects for 45+ minutes before any exculpatory content
- Client is pursuing Ofcom complaint, ICO complaint, and potential litigation

### What We Already Have
```
/mnt/project/
├── Documentary transcripts (Part 1: JSON, Part 2: DOCX)
├── Channel 4 correspondence (emails, meeting transcripts, letters)
├── Existing analysis documents (cross-reference frameworks, timestamp reports)
└── Various PDFs (correspondence, Simon Ford materials)
```

### What We're Building
A modular analysis system that:
1. Processes documentary transcripts to extract references, framing, and timing
2. Processes evidence documents to extract facts and quotes
3. Cross-references to identify suppressions and violations
4. Generates structured reports for legal/regulatory use
5. Honestly assesses evidence gaps

---

## PART 2: SYSTEM ARCHITECTURE

```
┌──────────────────────────────────────────────────────────────────┐
│                        PHRONESIS SYSTEM                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  INPUT LAYER                                                      │
│  ━━━━━━━━━━━                                                      │
│  • Documentary transcripts (JSON/DOCX)                           │
│  • Correspondence (PDFs, DOCX)                                   │
│  • Evidence documents (user-uploaded on demand)                  │
│                                                                   │
│  ↓                                                                │
│                                                                   │
│  PROCESSING LAYER                                                 │
│  ━━━━━━━━━━━━━━━━━                                                │
│  Module 1: Transcript Analyzer                                    │
│    - Extract references (Paul, Samantha, conspiracy, suspects)   │
│    - Classify segments (accusatory, suspect-framing, exculpatory)│
│    - Calculate timing metrics                                     │
│                                                                   │
│  Module 2: Evidence Extractor                                     │
│    - Parse documents for key quotes                              │
│    - Extract dates, speakers, context                            │
│    - Tag evidence by type (exculpatory, admission, etc.)         │
│                                                                   │
│  Module 3: Violation Analyzer                                     │
│    - Match documentary content to evidence                        │
│    - Identify suppressions (available but not included)          │
│    - Calculate strength scores                                    │
│                                                                   │
│  ↓                                                                │
│                                                                   │
│  OUTPUT LAYER                                                     │
│  ━━━━━━━━━━━━                                                     │
│  • Structured violation reports (JSON)                           │
│  • Evidence linkage matrices                                      │
│  • Markdown reports (human-readable)                             │
│  • Request logs (what evidence is still needed)                  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## PART 3: IMPLEMENTATION PHASES

### PHASE 1: Foundation (Priority: CRITICAL)
**Goal:** Core data structures and basic processing

**Tasks:**
1. Create project directory structure
2. Implement transcript parser for JSON/DOCX formats
3. Build reference detection system (regex patterns)
4. Create violation template structure
5. Implement basic output generator (Markdown)

**Expected Duration:** 2-3 hours
**Deliverable:** Working transcript analysis with reference counts

---

### PHASE 2: Violation Engine (Priority: HIGH)
**Goal:** Systematic violation assessment with evidence linkage

**Tasks:**
1. Implement 12 violation templates (from specification)
2. Build evidence matching logic
3. Create strength scoring system (STRONG/MODERATE/WEAK/UNSUBSTANTIATED)
4. Implement evidence gap detection
5. Generate violation reports with evidence citations

**Expected Duration:** 3-4 hours
**Deliverable:** Complete violation analysis report with honest assessments

---

### PHASE 3: Cross-Reference System (Priority: HIGH)
**Goal:** Link documentary claims to known facts

**Tasks:**
1. Build claim extraction from documentary
2. Implement fact extraction from evidence documents
3. Create suppression detection algorithm
4. Generate cross-reference matrix
5. Calculate suppression metrics

**Expected Duration:** 2-3 hours
**Deliverable:** Suppression analysis with quantified gaps

---

### PHASE 4: Report Generation (Priority: MEDIUM)
**Goal:** Professional output formatting

**Tasks:**
1. Create Ofcom-style complaint format
2. Generate evidence bundle structure
3. Implement timeline visualization
4. Create summary dashboards
5. Export to PDF/DOCX

**Expected Duration:** 2-3 hours
**Deliverable:** Print-ready complaint packages

---

## PART 4: TECHNICAL SPECIFICATIONS

### 4.1 Directory Structure

```
phronesis/
├── README.md
├── requirements.txt
├── config.yaml
│
├── src/
│   ├── __init__.py
│   ├── main.py                      # Entry point
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                # Configuration management
│   │   └── logger.py                # Logging setup
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── transcript_parser.py     # Parse JSON/DOCX transcripts
│   │   ├── document_parser.py       # Parse evidence documents
│   │   └── correspondence_parser.py # Parse emails/letters
│   │
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── reference_analyzer.py    # Detect name/concept references
│   │   ├── segment_classifier.py    # Classify transcript segments
│   │   ├── timing_analyzer.py       # Calculate timing metrics
│   │   └── suppression_detector.py  # Identify omissions
│   │
│   ├── violations/
│   │   ├── __init__.py
│   │   ├── violation_base.py        # Base violation class
│   │   ├── ofcom_violations.py      # Ofcom Code violations
│   │   ├── gdpr_violations.py       # UK GDPR violations
│   │   └── defamation_violations.py # Defamation claims
│   │
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── markdown_generator.py    # Generate markdown reports
│   │   ├── json_generator.py        # Generate structured data
│   │   └── pdf_generator.py         # Generate PDF outputs
│   │
│   └── utils/
│       ├── __init__.py
│       ├── text_utils.py            # Text processing utilities
│       ├── date_utils.py            # Date handling
│       └── file_utils.py            # File operations
│
├── data/
│   ├── input/
│   │   ├── transcripts/
│   │   ├── correspondence/
│   │   └── evidence/
│   │
│   ├── processed/
│   │   └── [intermediate data files]
│   │
│   └── output/
│       ├── reports/
│       ├── evidence_bundles/
│       └── visualizations/
│
├── templates/
│   ├── violation_templates.yaml     # Violation definitions
│   ├── patterns.yaml                # Regex patterns for detection
│   └── report_templates/
│       ├── ofcom_complaint.md
│       ├── ico_complaint.md
│       └── evidence_summary.md
│
├── tests/
│   ├── test_parsers.py
│   ├── test_analyzers.py
│   └── test_generators.py
│
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md
    └── USAGE.md
```

---

### 4.2 Core Data Structures

#### TranscriptSegment
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TranscriptSegment:
    """Represents a segment of documentary transcript."""
    id: int
    start_time: float              # Seconds from start
    end_time: float
    text: str
    speaker: Optional[str] = None
    
    # Analysis fields
    classification: Optional[str] = None  # ACCUSATORY, SUSPECT_FRAMING, etc.
    references: List[str] = None          # ["paul", "samantha", "conspiracy"]
    weight: float = 0.0                   # Impact score
    
    def timestamp(self) -> str:
        """Return HH:MM:SS format timestamp."""
        hours = int(self.start_time // 3600)
        minutes = int((self.start_time % 3600) // 60)
        seconds = int(self.start_time % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
```

#### EvidenceFact
```python
@dataclass
class EvidenceFact:
    """Represents a fact extracted from evidence documents."""
    fact_id: str
    source_document: str
    page_reference: str
    
    fact_text: str
    speaker: Optional[str] = None
    date: Optional[str] = None
    context: str = ""
    
    fact_type: str = ""  # EXCULPATORY, ADMISSION, JUDICIAL, etc.
    relevance: List[str] = None  # Which violations this relates to
    
    verified: bool = False
```

#### Violation
```python
@dataclass
class Violation:
    """Represents an alleged violation with evidence assessment."""
    violation_id: str
    category: str                  # OFCOM, GDPR, DEFAMATION
    code_section: str              # e.g., "7.1", "Article 6"
    
    claim: str                     # What we allege
    evidence_required: List[str]   # What we need to prove it
    evidence_have: List[str]       # What we actually have
    evidence_gaps: List[str]       # What's missing
    
    strength: str                  # STRONG, MODERATE, WEAK, UNSUBSTANTIATED
    strength_score: float          # 0.0-1.0
    
    supporting_facts: List[EvidenceFact] = None
    documentary_evidence: List[TranscriptSegment] = None
```

---

### 4.3 Key Algorithms

#### Reference Detection
```python
import re
from typing import Dict, List

class ReferenceAnalyzer:
    """Detect references to Paul, Samantha, and key concepts."""
    
    PATTERNS = {
        'paul_direct': [
            r'\bPaul\b',
            r'\bPaul\s+Stevens?\b',
            r'\bMr\.?\s*Stevens?\b',
        ],
        'samantha_direct': [
            r'\bSamantha\b',
            r'\bSam\b',
            r'\bSamantha\s+Stevens?\b',
        ],
        'suspect_framing': [
            r'\bsuspect\b',
            r'\bsuspects\b',
            r'\barrested\b',
            r'\bconspiracy\b',
            r'\bdetained\b',
        ],
        'exculpatory': [
            r'\bno\s+further\s+action\b',
            r'\bNFA\b',
            r'\bno\s+charges?\b',
            r'\breleased\b',
            r'\bcleared\b',
            r'\bmoving\s+away\s+from\b',
        ]
    }
    
    def analyze_segment(self, text: str) -> Dict[str, List[str]]:
        """Return all detected references in text."""
        results = {}
        
        for category, patterns in self.PATTERNS.items():
            matches = []
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches.append(pattern)
            if matches:
                results[category] = matches
                
        return results
    
    def count_references(self, segments: List[TranscriptSegment]) -> Dict[str, int]:
        """Count total references across all segments."""
        counts = {category: 0 for category in self.PATTERNS.keys()}
        
        for segment in segments:
            refs = self.analyze_segment(segment.text)
            for category, matches in refs.items():
                counts[category] += len(matches)
                
        return counts
```

#### Segment Classification
```python
class SegmentClassifier:
    """Classify transcript segments by their nature."""
    
    CLASSIFICATIONS = {
        'ACCUSATORY': {
            'patterns': [r'doing\s+these\s+murders', r'committed', r'responsible'],
            'weight': 0.15
        },
        'SUSPECT_FRAMING': {
            'patterns': [r'suspect', r'arrested', r'conspiracy'],
            'weight': 0.10
        },
        'IMPLICIT_GUILT': {
            'patterns': [r'involved', r'in\s+conjunction', r'together'],
            'weight': 0.05
        },
        'NEUTRAL': {
            'patterns': [],  # Default
            'weight': 0.0
        },
        'EXCULPATORY_CONDITIONAL': {
            'patterns': [r'if.*innocent', r'if.*nothing\s+to\s+do'],
            'weight': -0.05
        },
        'EXCULPATORY_DIRECT': {
            'patterns': [r'no\s+further\s+action', r'moving\s+away', r'not\s+charged'],
            'weight': -0.20
        }
    }
    
    def classify(self, segment: TranscriptSegment) -> str:
        """Determine segment classification."""
        text = segment.text.lower()
        
        # Check each classification in order of severity
        for classification, config in self.CLASSIFICATIONS.items():
            if classification == 'NEUTRAL':
                continue
            for pattern in config['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    segment.classification = classification
                    segment.weight = config['weight']
                    return classification
        
        # Default to NEUTRAL
        segment.classification = 'NEUTRAL'
        segment.weight = 0.0
        return 'NEUTRAL'
```

#### Timing Analyzer
```python
class TimingAnalyzer:
    """Calculate timing metrics for fairness analysis."""
    
    def calculate_exculpatory_delay(
        self, 
        segments: List[TranscriptSegment]
    ) -> Dict[str, float]:
        """
        For each suspect-framing segment, calculate time until
        first exculpatory content.
        """
        results = {}
        
        # Find all suspect-framing segments
        suspect_segments = [
            s for s in segments 
            if s.classification in ['ACCUSATORY', 'SUSPECT_FRAMING']
        ]
        
        # Find all exculpatory segments
        exculpatory_segments = [
            s for s in segments
            if 'EXCULPATORY' in s.classification
        ]
        
        if not exculpatory_segments:
            # No exculpatory content at all
            return {
                'total_suspect_framing': len(suspect_segments),
                'total_exculpatory': 0,
                'ratio': f"{len(suspect_segments)}:0",
                'first_exculpatory_timestamp': None,
                'delay_from_start': None
            }
        
        first_exculpatory = min(exculpatory_segments, key=lambda s: s.start_time)
        
        return {
            'total_suspect_framing': len(suspect_segments),
            'total_exculpatory': len(exculpatory_segments),
            'ratio': f"{len(suspect_segments)}:{len(exculpatory_segments)}",
            'first_exculpatory_timestamp': first_exculpatory.timestamp(),
            'delay_from_start': first_exculpatory.start_time
        }
```

#### Suppression Detector
```python
class SuppressionDetector:
    """Identify evidence that was available but not included."""
    
    def detect_suppressions(
        self,
        documentary_segments: List[TranscriptSegment],
        evidence_facts: List[EvidenceFact]
    ) -> List[Dict]:
        """
        Compare what was broadcast vs what was available.
        """
        suppressions = []
        
        for fact in evidence_facts:
            if fact.fact_type != 'EXCULPATORY':
                continue
                
            # Check if this fact appears anywhere in documentary
            fact_included = self._fact_in_documentary(fact, documentary_segments)
            
            if not fact_included:
                suppressions.append({
                    'fact_id': fact.fact_id,
                    'fact_text': fact.fact_text,
                    'source': fact.source_document,
                    'suppression_type': 'COMPLETE_OMISSION',
                    'impact': 'High - viewer unaware of exculpatory evidence'
                })
        
        return suppressions
    
    def _fact_in_documentary(
        self, 
        fact: EvidenceFact, 
        segments: List[TranscriptSegment]
    ) -> bool:
        """Check if fact's content appears in documentary."""
        # Simple keyword matching - can be made more sophisticated
        keywords = self._extract_keywords(fact.fact_text)
        
        for segment in segments:
            segment_text = segment.text.lower()
            matches = sum(1 for kw in keywords if kw in segment_text)
            
            # If 70%+ keywords match, consider it included
            if matches / len(keywords) >= 0.7:
                return True
        
        return False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract significant keywords from text."""
        # Remove common words, extract meaningful terms
        stop_words = {'the', 'a', 'an', 'is', 'was', 'are', 'were', 'of', 'to'}
        words = re.findall(r'\w+', text.lower())
        return [w for w in words if w not in stop_words and len(w) > 3]
```

---

### 4.4 Violation Assessment Logic

```python
class ViolationAssessor:
    """Assess strength of each alleged violation."""
    
    def assess_violation(self, violation: Violation) -> Violation:
        """Calculate strength score and classification."""
        
        # Count what we have vs what we need
        have_count = len([e for e in violation.evidence_have if e])
        need_count = len(violation.evidence_required)
        gap_count = len(violation.evidence_gaps)
        
        if need_count == 0:
            violation.strength = "UNASSESSABLE"
            violation.strength_score = 0.0
            return violation
        
        # Calculate base score
        have_ratio = have_count / need_count
        
        # Adjust for critical gaps
        critical_gap_penalty = gap_count * 0.15
        
        final_score = max(0.0, have_ratio - critical_gap_penalty)
        violation.strength_score = final_score
        
        # Classify
        if final_score >= 0.8:
            violation.strength = "STRONG"
        elif final_score >= 0.5:
            violation.strength = "MODERATE"
        elif final_score >= 0.2:
            violation.strength = "WEAK"
        else:
            violation.strength = "UNSUBSTANTIATED"
        
        return violation
```

---

### 4.5 Configuration File (config.yaml)

```yaml
project:
  name: "Phronesis - Documentary Analysis System"
  version: "1.0.0"
  case_name: "Stephen v Channel Four Television Corporation"

paths:
  input:
    transcripts: "data/input/transcripts/"
    correspondence: "data/input/correspondence/"
    evidence: "data/input/evidence/"
  
  output:
    reports: "data/output/reports/"
    evidence_bundles: "data/output/evidence_bundles/"
    visualizations: "data/output/visualizations/"
  
  templates: "templates/"

analysis:
  # Timing thresholds
  exculpatory_delay_threshold: 600  # 10 minutes in seconds
  
  # Ratio thresholds
  imbalance_threshold: 5.0  # 5:1 suspect:exculpatory is concerning
  
  # Classification weights
  weights:
    accusatory: 0.15
    suspect_framing: 0.10
    implicit_guilt: 0.05
    neutral: 0.0
    exculpatory_conditional: -0.05
    exculpatory_direct: -0.20

violations:
  # Which violations to assess
  ofcom:
    - "7.1"  # Fairness
    - "7.2"  # Accuracy
    - "7.4"  # Opportunity to respond
    - "8.1"  # Privacy
    - "8.3"  # Consent
    - "8.4"  # Custody footage
  
  gdpr:
    - "Article 6"   # Lawful basis
    - "Article 7"   # Consent
    - "Article 21"  # Right to object
  
  defamation:
    - "innuendo"

output:
  formats:
    - "markdown"
    - "json"
    - "pdf"  # Optional, requires additional setup
  
  include_timestamps: true
  include_evidence_citations: true
  include_gap_analysis: true
```

---

## PART 5: PRIORITY IMPLEMENTATION ORDER

### Week 1: MVP (Minimum Viable Product)

**Day 1-2: Foundation**
```bash
# Tasks:
1. Set up project structure
2. Implement transcript parser (JSON format from Part 1)
3. Build reference analyzer with regex patterns
4. Create basic output (Markdown report with reference counts)

# Success Criteria:
- Parse Part 1 transcript
- Count references to Paul, Samantha, suspects, conspiracy
- Generate simple Markdown report showing counts
```

**Day 3-4: Classification & Timing**
```bash
# Tasks:
1. Implement segment classifier
2. Build timing analyzer
3. Calculate 27:1 ratio and 45:43 delay
4. Generate timing analysis report

# Success Criteria:
- Each segment classified correctly
- Timing metrics calculated accurately
- Report shows: ratio, delay, timeline
```

**Day 5-7: Violation Engine**
```bash
# Tasks:
1. Implement violation templates
2. Build evidence matching
3. Create gap detection
4. Generate violation reports

# Success Criteria:
- All 12 violations assessed
- Evidence matched to requirements
- Gaps clearly identified
- Honest strength scoring
```

### Week 2: Enhancement

**Day 8-10: Cross-Reference System**
```bash
# Tasks:
1. Parse correspondence documents
2. Extract C4 admissions
3. Build cross-reference matrix
4. Generate suppression analysis

# Success Criteria:
- All consent refusals extracted
- Admissions linked to violations
- Suppression findings documented
```

**Day 11-14: Polish & Output**
```bash
# Tasks:
1. Improve report formatting
2. Add visualizations (timeline charts)
3. Generate Ofcom-ready package
4. Create user guide

# Success Criteria:
- Professional report formatting
- Easy-to-read outputs
- Complete evidence packages
```

---

## PART 6: TESTING CRITERIA

### Unit Tests
```python
# test_reference_analyzer.py
def test_paul_detection():
    analyzer = ReferenceAnalyzer()
    text = "The possible suspect which is our Paul Stevens"
    refs = analyzer.analyze_segment(text)
    assert 'paul_direct' in refs
    assert 'suspect_framing' in refs

# test_segment_classifier.py
def test_accusatory_classification():
    classifier = SegmentClassifier()
    segment = TranscriptSegment(
        id=1,
        start_time=0.0,
        end_time=5.0,
        text="Paul out doing these murders"
    )
    classification = classifier.classify(segment)
    assert classification == 'ACCUSATORY'
    assert segment.weight == 0.15

# test_timing_analyzer.py
def test_exculpatory_delay():
    analyzer = TimingAnalyzer()
    segments = [
        TranscriptSegment(1, 600.0, 605.0, "suspect", classification='SUSPECT_FRAMING'),
        TranscriptSegment(2, 2743.0, 2748.0, "moving away from conspiracy", classification='EXCULPATORY_DIRECT')
    ]
    result = analyzer.calculate_exculpatory_delay(segments)
    assert result['first_exculpatory_timestamp'] == "00:45:43"
```

### Integration Tests
```python
# test_full_pipeline.py
def test_part1_analysis():
    """Test complete analysis of Part 1 transcript."""
    # Load Part 1 transcript
    transcript = load_transcript("data/input/transcripts/part1.json")
    
    # Run full analysis
    analyzer = DocumentaryAnalyzer()
    results = analyzer.analyze(transcript)
    
    # Verify key metrics
    assert results['reference_counts']['suspect_framing'] >= 27
    assert results['reference_counts']['exculpatory'] <= 1
    assert results['timing']['ratio'] == "27:1" or results['timing']['ratio'] == "27:0"
    assert results['timing']['first_exculpatory_timestamp'] in ["00:45:43", None]
```

---

## PART 7: EXPECTED OUTPUTS

### 7.1 Violation Analysis Report (Markdown)

```markdown
# PHRONESIS VIOLATION ANALYSIS
## Case: Stephen v Channel Four Television Corporation
## Date: [Generated Date]

---

## EXECUTIVE SUMMARY

**Violations Assessed:** 12
**STRONG Evidence:** 5
**MODERATE Evidence:** 4
**WEAK Evidence:** 2
**UNSUBSTANTIATED:** 1

---

## VIOLATION 1: UNFAIR TREATMENT (Ofcom Code 7.1)

**Status:** ✅ STRONG (Score: 0.85)

**The Claim:**
Channel 4 treated Paul and Samantha unjustly by portraying them as murder suspects despite knowing they were cleared.

**Evidence Required:**
- [✓] Documentary shows suspect-framing language
- [✓] Quantified imbalance (suspect vs exculpatory)
- [⚠] C4 knew NFA status before broadcast
- [✓] Exculpatory evidence existed but excluded

**Evidence We Have:**
1. **Documentary suspect-framing**
   - Source: Part 1 transcript, segment 432
   - Quote: "With all three suspects detained..."
   - Timestamp: 00:26:47
   
2. **Quantified imbalance**
   - 27 suspect-framing statements
   - 1 exculpatory statement (trailer only)
   - Ratio: 27:1
   
3. **Evidence existed**
   - Source: Meeting transcript, 19 November 2025
   - Quote: Simon Ford references police "moving away from conspiracy"
   - Indicates C4 aware of investigative conclusions

**Evidence Gaps:**
- ❓ CPS NFA decision letter (date confirmation)
- ❓ Stephen Alderton court statement (specific exculpatory content)

**Assessment:**
Strong case based on documentary content and quantifiable imbalance. Upgrades to DEFINITIVE with CPS letter confirming dates.

---

[... continues for all 12 violations ...]
```

### 7.2 Cross-Reference Matrix (JSON)

```json
{
  "cross_references": [
    {
      "documentary_segment": {
        "timestamp": "00:10:14",
        "text": "The possible suspect which is our Paul Stevens",
        "classification": "SUSPECT_FRAMING",
        "viewer_understanding": "Paul is a murder suspect"
      },
      "factual_reality": {
        "truth": "Paul was questioned but never charged; received NFA December 2024",
        "evidence_source": "CPS NFA Letter [REQUESTED]",
        "available_to_c4": true
      },
      "suppression_analysis": {
        "fact_known": true,
        "fact_included": false,
        "suppression_type": "COMPLETE_OMISSION",
        "impact": "Viewer believes Paul is suspect; unaware he was cleared"
      },
      "legal_relevance": {
        "ofcom_breach": ["7.1", "7.2"],
        "defamation": true,
        "gdpr": ["Article 5"]
      }
    }
  ]
}
```

### 7.3 Evidence Request Log

```markdown
# EVIDENCE REQUEST LOG
## What We Need & Why

---

### TIER 1 - CRITICAL

#### CPS NFA Decision Letter
**Status:** ❌ NOT YET PROVIDED
**Why Critical:** Confirms official clearance date; proves C4 knew status before broadcast
**Unlocks:** Violations 1, 2, 4, 10
**Request to Client:** "Do you have the CPS letter confirming NFA decision for Paul and Samantha?"

#### Stephen Alderton's Court Statement  
**Status:** ❌ NOT YET PROVIDED
**Why Critical:** If contains "excellent stepfather" quote, proves deliberate suppression
**Unlocks:** Violation 11
**Request to Client:** "Do you have Alderton's written statement to the court?"

---

### TIER 2 - IMPORTANT

#### Judge's Sentencing Remarks
**Status:** ❌ NOT YET PROVIDED
**Why Important:** Judicial finding on whether Alderton acted alone
**Unlocks:** Violation 12, strengthens Violation 2
**Request to Client:** "Do you have the judge's sentencing transcript?"

---

[... continues for all requested evidence ...]
```

---

## PART 8: IMPLEMENTATION PROMPT FOR CLAUDE CODE

**COPY THIS SECTION TO CLAUDE CODE:**

```
PROJECT: Phronesis - Documentary Analysis System
ROLE: Implementation Engineer
CONTEXT: Building forensic analysis tool for broadcasting complaint

YOUR MISSION:
Build a Python-based analysis system that processes documentary transcripts and evidence documents to generate legally-usable violation reports with honest evidence gap assessments.

PRIORITY 1 - MVP (Build This First):
1. Parse transcript JSON file from /mnt/project/12-08_Vendetta_Part_One__Cambridgeshire_Double_Murder_Investigation.json
2. Implement reference detection (count mentions of Paul, Samantha, "suspect", "conspiracy", etc.)
3. Classify each segment (ACCUSATORY, SUSPECT_FRAMING, EXCULPATORY, etc.)
4. Calculate timing metrics (27:1 ratio, 45:43 delay to first exculpatory)
5. Generate Markdown report with findings

DIRECTORY STRUCTURE:
phronesis/
├── src/
│   ├── parsers/transcript_parser.py
│   ├── analyzers/reference_analyzer.py
│   ├── analyzers/segment_classifier.py
│   ├── analyzers/timing_analyzer.py
│   └── generators/markdown_generator.py
├── data/
│   └── output/reports/
└── config.yaml

KEY ALGORITHMS:
- Reference detection: Use regex patterns (provided in spec)
- Segment classification: Pattern matching with weights (provided)
- Timing analysis: Calculate delays between suspect-framing and exculpatory
- Gap detection: Flag when evidence is referenced but not provided

SUCCESS CRITERIA:
✓ Parse Part 1 JSON transcript successfully
✓ Count 27+ suspect-framing references
✓ Count 0-1 exculpatory references in main content
✓ Calculate 45:43 timestamp for first exculpatory
✓ Generate professional Markdown report

TECHNICAL CONSTRAINTS:
- Python 3.8+
- Use dataclasses for structures
- Config-driven (YAML)
- Modular design (easy to extend)
- Well-documented code

IMPORTANT PHILOSOPHY:
- Start with violations, request evidence on-demand
- Honestly assess strength (STRONG/MODERATE/WEAK/UNSUBSTANTIATED)
- Flag gaps explicitly - don't hide missing evidence
- Generate legally-usable outputs

FULL SPECIFICATION:
See attached PHRONESIS_VIOLATIONS_ANALYSIS.md and this technical spec.

START WITH:
1. Create project structure
2. Implement transcript_parser.py for JSON format
3. Build reference_analyzer.py with regex patterns
4. Test on Part 1 transcript
5. Generate initial report

QUESTIONS? ASK FOR:
- Clarification on any specification details
- Additional test cases
- Output format preferences
```

---

## PART 9: HANDOFF CHECKLIST

**Before giving this to Claude Code, ensure:**

- [ ] Transcript files are accessible at /mnt/project/
- [ ] Output directory exists or will be created
- [ ] Any specific format preferences are noted
- [ ] Priority order is clear (MVP first)

**After Claude Code completes Phase 1, validate:**

- [ ] Reference counts match expected values (~27:1 ratio)
- [ ] Timestamp calculations are accurate
- [ ] Output is professionally formatted
- [ ] Code is modular and extensible

**Then proceed to Phase 2 (Violation Engine)**

---

*Phronesis Implementation Specification v1.0*
*Prepared by: Claude (Chat) for Claude Code (Terminal)*
*Date: 10 December 2025*
