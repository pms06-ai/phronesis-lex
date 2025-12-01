"""
Prompt Templates for Phronesis LEX

Optimized prompts for UK Family Court document analysis.
Each template is designed for copy-paste into AI subscription platforms.
"""

from typing import Dict, Optional
from enum import Enum


class PromptType(str, Enum):
    CLAIM_EXTRACTION = "claim_extraction"
    DOCUMENT_SUMMARY = "document_summary"
    CLAIM_ANALYSIS = "claim_analysis"
    CREDIBILITY_ASSESSMENT = "credibility_assessment"
    CONTRADICTION_ANALYSIS = "contradiction_analysis"
    TIMELINE_EXTRACTION = "timeline_extraction"
    EVIDENCE_EVALUATION = "evidence_evaluation"
    LEGAL_FRAMEWORK = "legal_framework"


class PromptTemplates:
    """
    Template library for generating AI prompts.

    Each template includes:
    - System context for the AI
    - Task-specific instructions
    - Output format specification (JSON for parsing)
    - UK Family Court legal framework context
    """

    SYSTEM_CONTEXT = """You are a legal document analyst specializing in UK Family Court proceedings.
You have expertise in:
- Children Act 1989 and welfare checklist (s.1(3))
- Re B [2013] UKSC 33 (balance of probabilities)
- Lucas Direction (lies don't necessarily indicate guilt)
- Re H-C [2016] EWCA Civ 136 (proper evidential approach)

Your analysis must be:
- Objective and evidence-based
- Free from speculation
- Grounded in legal principles
- Formatted for systematic review"""

    CLAIM_EXTRACTION = """## Task: Extract Claims from Document

Analyze the following document and extract all factual claims made.

### Document Text:
```
{document_text}
```

### Instructions:
1. Identify each distinct factual claim (not opinions or arguments)
2. Note who made each claim and when
3. Categorize by type (event, character, capability, outcome, process)
4. Rate evidence strength (direct/circumstantial/hearsay/assertion)
5. Flag claims requiring corroboration

### Required Output Format (JSON):
```json
{{
  "claims": [
    {{
      "id": "CLM001",
      "text": "The exact claim text",
      "claimant": "Who made this claim",
      "document_reference": "Document name/paragraph",
      "claim_type": "event|character|capability|outcome|process",
      "evidence_type": "direct|circumstantial|hearsay|assertion",
      "date_mentioned": "YYYY-MM-DD or null",
      "subjects": ["Person or entity the claim is about"],
      "requires_corroboration": true,
      "legal_relevance": "Why this matters for the proceedings"
    }}
  ],
  "summary": {{
    "total_claims": 0,
    "by_type": {{}},
    "by_evidence_strength": {{}},
    "key_themes": []
  }}
}}
```

Provide ONLY the JSON output, no additional commentary."""

    DOCUMENT_SUMMARY = """## Task: Summarize Legal Document

Create a structured summary of this UK Family Court document.

### Document Text:
```
{document_text}
```

### Instructions:
1. Identify document type and purpose
2. Extract key parties mentioned
3. Summarize main allegations/claims
4. Note any orders, directions, or recommendations
5. Identify dates and timeline elements
6. Flag urgency indicators

### Required Output Format (JSON):
```json
{{
  "document_type": "statement|report|order|application|response|expert_report",
  "author": "Document author",
  "date": "YYYY-MM-DD",
  "parties": [
    {{
      "name": "Party name",
      "role": "mother|father|child|social_worker|guardian|expert|other",
      "relationship": "Description"
    }}
  ],
  "executive_summary": "2-3 sentence overview",
  "key_points": [
    {{
      "point": "Description",
      "category": "allegation|fact|recommendation|order|concern",
      "importance": "high|medium|low"
    }}
  ],
  "timeline_elements": [
    {{
      "date": "YYYY-MM-DD",
      "event": "Description"
    }}
  ],
  "children_welfare": {{
    "concerns_raised": [],
    "positive_factors": [],
    "welfare_checklist_items": []
  }},
  "next_steps": [],
  "flags": {{
    "urgent": false,
    "safeguarding": false,
    "disclosure_required": false
  }}
}}
```

Provide ONLY the JSON output, no additional commentary."""

    CLAIM_ANALYSIS = """## Task: Analyze Claim for Legal Proceedings

Analyze this specific claim in the context of UK Family Court proceedings.

### Claim:
```
{claim_text}
```

### Source Document: {document_name}
### Claimant: {claimant}
### Context: {context}

### Instructions:
1. Assess claim specificity and verifiability
2. Identify what evidence would support or refute this
3. Apply Re B standard (balance of probabilities)
4. Consider Lucas Direction if claim involves dishonesty
5. Note potential biases or self-interest
6. Identify corroborating or contradicting evidence needed

### Required Output Format (JSON):
```json
{{
  "claim_assessment": {{
    "specificity": "high|medium|low",
    "verifiable": true,
    "verification_method": "How this could be verified",
    "time_bound": true,
    "date_specificity": "exact|approximate|vague"
  }},
  "evidence_analysis": {{
    "evidence_type": "direct|circumstantial|hearsay|opinion",
    "weight": "strong|moderate|weak",
    "limitations": [],
    "corroboration_needed": []
  }},
  "legal_framework": {{
    "relevant_principles": [],
    "re_b_application": "How Re B applies",
    "lucas_direction_relevant": false,
    "welfare_checklist_items": []
  }},
  "bias_indicators": {{
    "self_interest_score": 0.0,
    "emotional_language": false,
    "speculation_present": false,
    "flags": []
  }},
  "recommended_actions": [],
  "questions_to_explore": []
}}
```

Provide ONLY the JSON output, no additional commentary."""

    CREDIBILITY_ASSESSMENT = """## Task: Credibility Assessment

Assess the credibility indicators in this witness statement/document.

### Document Text:
```
{document_text}
```

### Author/Witness: {author}
### Document Type: {document_type}

### Instructions:
Apply forensic document analysis principles:
1. Internal consistency (does the account contradict itself?)
2. External consistency (does it align with known facts?)
3. Specificity of detail (vague vs. specific claims)
4. Emotional content analysis (appropriate vs. performative)
5. Self-serving content ratio
6. Acknowledgment of uncertainty or opposing views
7. Timeline coherence

Remember: Apply Lucas Direction - inconsistencies don't automatically indicate untruthfulness.

### Required Output Format (JSON):
```json
{{
  "credibility_indicators": {{
    "internal_consistency": {{
      "score": 0.0,
      "inconsistencies": [],
      "notes": ""
    }},
    "specificity": {{
      "score": 0.0,
      "vague_claims": [],
      "detailed_claims": []
    }},
    "emotional_analysis": {{
      "appropriate": true,
      "performative_elements": [],
      "notes": ""
    }},
    "self_interest": {{
      "ratio": 0.0,
      "self_serving_claims": [],
      "balanced_acknowledgments": []
    }},
    "uncertainty_acknowledgment": {{
      "present": true,
      "examples": []
    }}
  }},
  "timeline_analysis": {{
    "coherent": true,
    "gaps": [],
    "contradictions": []
  }},
  "lucas_direction_notes": "",
  "overall_assessment": {{
    "credibility_score": 0.0,
    "confidence": "high|medium|low",
    "key_strengths": [],
    "key_concerns": [],
    "areas_requiring_clarification": []
  }}
}}
```

Provide ONLY the JSON output, no additional commentary."""

    CONTRADICTION_ANALYSIS = """## Task: Contradiction Analysis

Analyze these two claims for potential contradictions.

### Claim A:
```
{claim_a_text}
```
- Source: {claim_a_source}
- Author: {claim_a_author}
- Date: {claim_a_date}

### Claim B:
```
{claim_b_text}
```
- Source: {claim_b_source}
- Author: {claim_b_author}
- Date: {claim_b_date}

### Instructions:
1. Determine if claims are truly contradictory or merely different perspectives
2. Assess severity of contradiction if present
3. Consider possible explanations (memory, perception, time passage)
4. Apply Lucas Direction principles
5. Identify what evidence could resolve the contradiction

### Required Output Format (JSON):
```json
{{
  "contradiction_assessment": {{
    "is_contradiction": true,
    "contradiction_type": "direct|temporal|contextual|perspective|none",
    "severity": "critical|significant|minor|apparent_only",
    "confidence": 0.0
  }},
  "analysis": {{
    "specific_conflict": "What exactly conflicts",
    "possible_explanations": [],
    "cannot_both_be_true": true,
    "time_factor": "Could time explain the difference?",
    "perception_factor": "Could different perceptions explain this?"
  }},
  "lucas_direction": {{
    "applies": false,
    "notes": ""
  }},
  "resolution": {{
    "evidence_needed": [],
    "questions_to_ask": [],
    "verification_steps": []
  }},
  "legal_significance": {{
    "impacts_welfare": false,
    "impacts_credibility": true,
    "relevant_to": []
  }}
}}
```

Provide ONLY the JSON output, no additional commentary."""

    TIMELINE_EXTRACTION = """## Task: Extract Timeline from Documents

Create a chronological timeline from these documents.

### Documents:
{documents}

### Instructions:
1. Extract all dated events
2. Identify approximate dates where exact dates unknown
3. Note source document for each event
4. Flag conflicting dates between sources
5. Identify gaps in the timeline
6. Note events with welfare significance

### Required Output Format (JSON):
```json
{{
  "timeline": [
    {{
      "date": "YYYY-MM-DD",
      "date_precision": "exact|month|year|approximate",
      "event": "Description",
      "source_document": "Document reference",
      "source_author": "Who reported this",
      "event_type": "incident|assessment|court|service|milestone|other",
      "welfare_relevant": true,
      "verification_status": "verified|claimed|disputed",
      "notes": ""
    }}
  ],
  "conflicts": [
    {{
      "event": "Description",
      "date_claim_1": {{"date": "", "source": ""}},
      "date_claim_2": {{"date": "", "source": ""}},
      "resolution_needed": true
    }}
  ],
  "gaps": [
    {{
      "period": "Description of gap",
      "significance": "Why this matters"
    }}
  ],
  "summary": {{
    "date_range": {{"start": "", "end": ""}},
    "total_events": 0,
    "key_periods": []
  }}
}}
```

Provide ONLY the JSON output, no additional commentary."""

    EVIDENCE_EVALUATION = """## Task: Evidence Evaluation

Evaluate the evidence presented for this claim in UK Family Court context.

### Claim:
```
{claim_text}
```

### Supporting Evidence Presented:
{evidence_list}

### Instructions:
Apply Re B [2013] UKSC 33 principles:
1. Assess each piece of evidence on its own merits
2. Consider cumulative effect of evidence
3. Apply balance of probabilities standard
4. Distinguish between direct and circumstantial evidence
5. Assess hearsay reliability
6. Consider what evidence is missing

### Required Output Format (JSON):
```json
{{
  "claim_summary": "",
  "evidence_items": [
    {{
      "description": "",
      "type": "direct|circumstantial|hearsay|documentary|expert",
      "source": "",
      "weight": "strong|moderate|weak",
      "reliability_factors": [],
      "limitations": []
    }}
  ],
  "cumulative_assessment": {{
    "overall_strength": "strong|moderate|weak|insufficient",
    "balance_of_probabilities": {{
      "met": true,
      "confidence": 0.0,
      "reasoning": ""
    }},
    "key_supporting_factors": [],
    "key_weaknesses": []
  }},
  "missing_evidence": [
    {{
      "description": "",
      "would_strengthen_or_weaken": "strengthen|weaken",
      "obtainable": true
    }}
  ],
  "re_b_application": "",
  "recommendation": ""
}}
```

Provide ONLY the JSON output, no additional commentary."""

    LEGAL_FRAMEWORK = """## Task: Legal Framework Analysis

Analyze how UK Family Court legal principles apply to this situation.

### Situation:
```
{situation}
```

### Key Claims/Issues:
{claims}

### Instructions:
Apply relevant legal framework:
1. Children Act 1989 welfare checklist (s.1(3))
2. Welfare paramount principle (s.1(1))
3. No order principle (s.1(5))
4. Re B burden of proof
5. Any other relevant case law

### Required Output Format (JSON):
```json
{{
  "welfare_checklist_s1_3": {{
    "a_wishes_feelings": {{
      "applicable": true,
      "analysis": "",
      "evidence": []
    }},
    "b_physical_emotional_educational": {{
      "applicable": true,
      "analysis": "",
      "evidence": []
    }},
    "c_effect_of_change": {{
      "applicable": true,
      "analysis": "",
      "evidence": []
    }},
    "d_age_sex_background": {{
      "applicable": true,
      "analysis": "",
      "evidence": []
    }},
    "e_harm_suffered_or_risk": {{
      "applicable": true,
      "analysis": "",
      "evidence": []
    }},
    "f_parents_capability": {{
      "applicable": true,
      "analysis": "",
      "evidence": []
    }},
    "g_court_powers": {{
      "applicable": true,
      "analysis": "",
      "evidence": []
    }}
  }},
  "case_law_application": [
    {{
      "case": "",
      "principle": "",
      "application": ""
    }}
  ],
  "burden_of_proof": {{
    "who_bears": "",
    "standard": "balance of probabilities",
    "analysis": ""
  }},
  "no_order_principle": {{
    "consideration": "",
    "intervention_justified": true,
    "reasoning": ""
  }},
  "recommendations": []
}}
```

Provide ONLY the JSON output, no additional commentary."""

    @classmethod
    def get_template(cls, prompt_type: PromptType) -> str:
        """Get template by type."""
        templates = {
            PromptType.CLAIM_EXTRACTION: cls.CLAIM_EXTRACTION,
            PromptType.DOCUMENT_SUMMARY: cls.DOCUMENT_SUMMARY,
            PromptType.CLAIM_ANALYSIS: cls.CLAIM_ANALYSIS,
            PromptType.CREDIBILITY_ASSESSMENT: cls.CREDIBILITY_ASSESSMENT,
            PromptType.CONTRADICTION_ANALYSIS: cls.CONTRADICTION_ANALYSIS,
            PromptType.TIMELINE_EXTRACTION: cls.TIMELINE_EXTRACTION,
            PromptType.EVIDENCE_EVALUATION: cls.EVIDENCE_EVALUATION,
            PromptType.LEGAL_FRAMEWORK: cls.LEGAL_FRAMEWORK,
        }
        return templates.get(prompt_type, "")

    @classmethod
    def list_templates(cls) -> Dict[str, str]:
        """List all available templates with descriptions."""
        return {
            PromptType.CLAIM_EXTRACTION: "Extract factual claims from documents",
            PromptType.DOCUMENT_SUMMARY: "Create structured document summaries",
            PromptType.CLAIM_ANALYSIS: "Deep analysis of individual claims",
            PromptType.CREDIBILITY_ASSESSMENT: "Assess witness/document credibility",
            PromptType.CONTRADICTION_ANALYSIS: "Analyze contradictions between claims",
            PromptType.TIMELINE_EXTRACTION: "Build chronological timeline",
            PromptType.EVIDENCE_EVALUATION: "Evaluate evidence for claims",
            PromptType.LEGAL_FRAMEWORK: "Apply UK Family Court legal principles",
        }
