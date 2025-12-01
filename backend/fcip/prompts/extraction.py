"""
FCIP v5.0 Extraction Prompts - Optimized for epistemic precision.

These prompts are designed to extract forensically-relevant information
with full epistemic annotation (modality, certainty, attribution).
"""

import hashlib
from typing import Any, Dict

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

FORENSIC_ANALYST_SYSTEM = """You are a senior forensic document analyst specializing in UK legal proceedings (family law, civil litigation, criminal cases). Your role is to extract structured information with maximum precision and completeness.

CORE PRINCIPLES:
1. **Epistemic Precision**: Capture EXACT certainty levels and attribution chains
2. **Temporal Accuracy**: Note only explicitly stated dates/times - NEVER infer unstated dates
3. **Entity Consistency**: Use full names/titles exactly as they appear
4. **Claim Atomicity**: One assertion per claim - break compound statements
5. **Source Fidelity**: Quote verbatim supporting text

CRITICAL DISTINCTIONS:
You must distinguish between these modalities:
- **Asserted**: Direct statement of fact: "The father attended the meeting"
- **Reported**: Attributed to another: "The mother stated the father attended"
- **Alleged**: Contested/unproven: "It is alleged the father attended"
- **Denied**: Explicit denial: "The father denies attending"
- **Hypothetical**: Conditional: "If the father had attended..."

CERTAINTY CALIBRATION:
- 0.9-1.0: "certainly", "confirmed", "established fact", "undoubtedly"
- 0.7-0.9: "clearly", "evidently", stated without hedging
- 0.5-0.7: Standard assertion, neutral tone
- 0.3-0.5: "appears", "seems", "suggests", "indicates"
- 0.1-0.3: "possibly", "may", "might", "could", "perhaps"

OUTPUT: Return ONLY valid JSON with no markdown formatting or code blocks."""


# =============================================================================
# CLAIM EXTRACTION PROMPT
# =============================================================================

CLAIM_EXTRACTION_PROMPT = """Extract all factual claims from this document text with forensic precision.

DOCUMENT METADATA:
- Type: {doc_type}
- Date: {doc_date}
- Author: {author}
- Case ID: {case_id}

TEXT TO ANALYZE:
\"\"\"
{text}
\"\"\"

EXTRACTION REQUIREMENTS:

1. **Claims**: Extract EVERY assertion, finding, opinion, or statement
   - Subject: Entity making or about whom claim is made
   - Subject type: person | organization | location
   - Predicate: Action, state, assessment, decision, or communication
   - Predicate category: action | state | decision | communication | requirement | assessment
   - Object value: What is being asserted (max 500 chars)

   EPISTEMIC ANNOTATION:
   - Modality: asserted | reported | alleged | denied | hypothetical
   - Polarity: affirm | negate
   - Certainty: 0.0-1.0 (calibrated per guide above)
   - Certainty markers: List hedging/boosting words found

   ATTRIBUTION:
   - Asserted by: WHO is making this claim (if attributed)
   - If the document author is asserting directly, leave null

   TEMPORAL:
   - Time expression: Verbatim temporal phrase or null
   - Time start: YYYY-MM-DD if determinable, else null
   - Time end: YYYY-MM-DD if determinable, else null

   EVIDENCE:
   - Source quote: Exact text supporting this claim

2. **Entities**: Extract all people, organizations, locations mentioned
   - Full name as appears in text
   - Type: person | organization | location
   - Role: applicant | respondent | witness | professional | child | judge | other
   - Confidence: How certain this is a distinct entity (0-1)

3. **Requirements**: Flag any obligations or mandates
   - is_requirement: true for claims containing must/shall/required/ordered
   - deadline_expression: Verbatim deadline text if present

Return JSON matching this schema:
{{
  "claims": [
    {{
      "subject": "entity name",
      "subject_type": "person|organization|location",
      "predicate": "verb or state",
      "predicate_category": "action|state|decision|communication|requirement|assessment",
      "object_value": "what is asserted",

      "modality": "asserted|reported|alleged|denied|hypothetical",
      "polarity": "affirm|negate",
      "certainty": 0.75,
      "certainty_markers": ["clearly", "stated"],

      "asserted_by": "who makes this claim or null",
      "time_expression": "verbatim phrase or null",
      "time_start": "YYYY-MM-DD or null",
      "time_end": "YYYY-MM-DD or null",

      "source_quote": "exact supporting text",
      "is_requirement": false,
      "deadline_expression": null
    }}
  ],
  "entities": [
    {{
      "text": "Full Name as appears",
      "entity_type": "person|organization|location",
      "role": "applicant|respondent|witness|professional|child|judge|other",
      "confidence": 0.95
    }}
  ],
  "document_insights": {{
    "primary_focus": "brief summary of document purpose",
    "key_dates": ["date1", "date2"],
    "critical_claims_indices": [0, 3, 7]
  }}
}}

CRITICAL: Extract ALL claims, even minor ones. Over-extract rather than miss evidence. Do not summarize - extract each distinct assertion separately."""


# =============================================================================
# DOCUMENT CLASSIFICATION PROMPT
# =============================================================================

DOCUMENT_CLASSIFICATION_PROMPT = """Classify this legal document into the most appropriate type.

DOCUMENT TYPES:
- **court_order**: Official court orders, judgments, directions, case management orders
- **witness_statement**: Formal witness statements, affidavits, sworn testimony
- **social_work_report**: Social worker assessments, case notes, safeguarding reports, Section 7/37 reports
- **psychological_report**: Psychological assessments, psychiatric reports
- **cafcass_analysis**: CAFCASS officer reports, guardian analyses
- **medical_record**: Medical reports, health visitor notes, GP records
- **police_report**: Police reports, disclosure documents
- **legal_submission**: Position statements, skeleton arguments, legal briefs
- **expert_report**: Expert witness reports (non-psychological)
- **correspondence**: Letters, emails between parties/professionals
- **meeting_minutes**: Case conference minutes, LAC reviews, strategy meetings
- **sar_response**: Subject Access Request responses
- **other**: None of the above categories

DOCUMENT TEXT (first 3000 characters):
\"\"\"
{text}
\"\"\"

Analyze the document and return JSON:
{{
  "doc_type": "court_order",
  "confidence": 0.95,
  "doc_date": "YYYY-MM-DD or null",
  "author": "author name or role",
  "author_role": "judge|social_worker|guardian|solicitor|barrister|expert|party|other",
  "jurisdiction": "England and Wales|Scotland|Northern Ireland|null",
  "case_stage": "pre-proceedings|interim|final|appeal|null",
  "key_indicators": ["phrase that indicated type", "another indicator"],
  "reasoning": "Brief explanation of classification"
}}"""


# =============================================================================
# ENTITY RESOLUTION PROMPT
# =============================================================================

ENTITY_RESOLUTION_PROMPT = """Determine if these entity mentions refer to the same person/organization.

ENTITY 1: "{entity_1}"
Context 1: {context_1}

ENTITY 2: "{entity_2}"
Context 2: {context_2}

CASE CONTEXT:
- Case Type: {case_type}
- Known Entities: {known_entities}

Consider carefully:
- Name variations (nicknames, formal vs informal, maiden names)
- Titles and professional designations (Dr, Judge, Ms)
- Role references ("the social worker", "the mother")
- Contextual clues (organization, location, relationship)
- Potential for false positives (common names in different roles)

Return JSON:
{{
  "is_same_entity": true,
  "confidence": 0.85,
  "reasoning": "Both refer to the Local Authority social worker assigned to this case",
  "canonical_name": "Sarah Johnson",
  "entity_type": "person",
  "role": "social_worker",
  "match_factors": ["same role", "same organization", "consistent context"]
}}"""


# =============================================================================
# CONTRADICTION ANALYSIS PROMPT
# =============================================================================

CONTRADICTION_ANALYSIS_PROMPT = """Analyze if these two claims contradict each other.

CLAIM A:
{claim_a_json}

CLAIM B:
{claim_b_json}

ANALYSIS REQUIREMENTS:
1. Do they assert opposite polarities about the same subject/object?
2. Are they about the same or overlapping time periods?
3. Could both be true in different contexts or at different times?
4. Is one a report of the other (not a true contradiction)?
5. Consider modality: an allegation vs a finding are not necessarily contradictory

CONTRADICTION TYPES:
- direct_negation: One explicitly negates the other
- temporal_conflict: Same assertion with incompatible timeframes
- value_conflict: Different values for the same attribute
- none: No contradiction found

Return JSON:
{{
  "is_contradiction": true,
  "confidence": 0.80,
  "contradiction_type": "direct_negation|temporal_conflict|value_conflict|none",
  "reasoning": "Detailed explanation of analysis",
  "resolution_possibilities": [
    "Claims may refer to different time periods",
    "One may be reporting what was alleged, not asserting truth",
    "Entity disambiguation may be needed"
  ],
  "severity": "high|medium|low"
}}"""


# =============================================================================
# ARGUMENT GENERATION PROMPT
# =============================================================================

ARGUMENT_GENERATION_PROMPT = """Generate a Toulmin argument structure for this finding.

FINDING:
Type: {finding_type}
Summary: {finding_summary}
Severity: {severity}

SUPPORTING CLAIMS:
{claims_json}

LEGAL CONTEXT:
Case Type: {case_type}
Relevant Rules: {relevant_rules}

Generate a structured legal argument following Toulmin model:

1. **Claim**: The core assertion (clear, specific, testable)
2. **Grounds**: Evidence from the supporting claims (with document citations)
3. **Warrant**: The reasoning rule connecting grounds to claim
4. **Backing**: Why the warrant is valid (legal authority, precedent)
5. **Qualifier**: Strength of conclusion (certainly | probably | possibly | tentatively)
6. **Rebuttal**: Specific conditions that would invalidate the claim

7. **Falsifiability Conditions**: Generate 3-5 specific tests:
   - What evidence would disprove this argument?
   - What alternative documents should be checked?
   - What timeline conflicts would undermine it?
   - What entity disambiguation is needed?

8. **Missing Evidence**: What would strengthen or weaken this argument?

9. **Alternative Explanations**: List plausible alternative interpretations

Return JSON:
{{
  "claim_text": "The conclusion being drawn",
  "grounds": ["Evidence point 1 with citation", "Evidence point 2"],
  "warrant": "The legal/logical rule connecting evidence to conclusion",
  "warrant_rule_id": "CA1989.s1.3 or null",
  "backing": ["Legal authority 1", "Precedent 2"],
  "qualifier": "probably",
  "rebuttal": ["Condition that would invalidate 1", "Condition 2"],
  "falsifiability_conditions": [
    {{
      "type": "missing_evidence",
      "description": "What to look for",
      "test_query": "Search query or check",
      "impact": "Effect if found",
      "priority": 1
    }}
  ],
  "missing_evidence": ["Evidence that would strengthen/weaken"],
  "alternative_explanations": ["Alternative interpretation 1", "Alternative 2"],
  "confidence_lower": 0.6,
  "confidence_upper": 0.85,
  "confidence_mean": 0.72
}}"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_prompt_hash(prompt_template: str, **kwargs: Any) -> str:
    """
    Generate a hash of the filled prompt for reproducibility tracking.

    Args:
        prompt_template: The prompt template string
        **kwargs: Variables to fill into the template

    Returns:
        First 16 characters of SHA-256 hash
    """
    try:
        filled = prompt_template.format(**kwargs)
    except KeyError:
        filled = prompt_template

    return hashlib.sha256(filled.encode()).hexdigest()[:16]


def format_claims_for_prompt(claims: list) -> str:
    """Format a list of claims for inclusion in prompts."""
    formatted = []
    for i, claim in enumerate(claims[:10]):  # Limit to 10 claims
        text = claim.get("text", claim.get("object_value", ""))[:200]
        certainty = claim.get("certainty", 0.5)
        modality = claim.get("modality", "asserted")
        formatted.append(
            f"[{i+1}] ({modality}, certainty: {certainty:.2f}) {text}"
        )
    return "\n".join(formatted)


def format_entities_for_prompt(entities: list) -> str:
    """Format a list of entities for context."""
    return ", ".join([
        f"{e.get('canonical_name', e.get('text', 'Unknown'))} ({e.get('role', 'unknown')})"
        for e in entities[:20]
    ])
