"""
Claude AI Service
Integration with Anthropic Claude API for document analysis
"""
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import anthropic

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS, CHUNK_SIZE, OVERLAP_SIZE


class ClaudeService:
    """Service for interacting with Claude API for legal document analysis"""

    def __init__(self, api_key: str = ANTHROPIC_API_KEY):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = CLAUDE_MODEL
        self.max_tokens = CLAUDE_MAX_TOKENS
        self.total_tokens_used = 0

    async def analyze_document(self,
                               document_text: str,
                               case_context: Optional[str] = None,
                               doc_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive document analysis extracting claims, entities, and issues.
        Returns structured JSON with all extracted information.
        """
        prompt = self._build_document_analysis_prompt(document_text, case_context, doc_type)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        self.total_tokens_used += response.usage.input_tokens + response.usage.output_tokens

        return self._parse_json_response(response.content[0].text)

    async def extract_claims(self,
                            document_text: str,
                            professional_context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract all claims, assertions, and allegations from document text."""
        prompt = self._build_claims_extraction_prompt(document_text, professional_context)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        self.total_tokens_used += response.usage.input_tokens + response.usage.output_tokens

        result = self._parse_json_response(response.content[0].text)
        return result.get("claims", [])

    async def detect_biases(self,
                           text: str,
                           professional: Optional[str] = None,
                           capacity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Detect cognitive biases and rhetorical manipulation in text."""
        prompt = self._build_bias_detection_prompt(text, professional, capacity)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        self.total_tokens_used += response.usage.input_tokens + response.usage.output_tokens

        result = self._parse_json_response(response.content[0].text)
        return result.get("biases", [])

    async def analyze_competing_claims(self,
                                       claim_a: Dict[str, Any],
                                       claim_b: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the logical relationship between two competing claims."""
        prompt = self._build_competing_claims_prompt(claim_a, claim_b)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        self.total_tokens_used += response.usage.input_tokens + response.usage.output_tokens

        return self._parse_json_response(response.content[0].text)

    async def extract_timeline_events(self,
                                      document_text: str,
                                      existing_events: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
        """Extract chronological events from document text."""
        prompt = self._build_timeline_extraction_prompt(document_text, existing_events)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        self.total_tokens_used += response.usage.input_tokens + response.usage.output_tokens

        result = self._parse_json_response(response.content[0].text)
        return result.get("events", [])

    async def generate_executive_summary(self,
                                         case_data: Dict[str, Any]) -> str:
        """Generate an executive summary of case analysis."""
        prompt = self._build_summary_prompt(case_data)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        self.total_tokens_used += response.usage.input_tokens + response.usage.output_tokens

        return response.content[0].text

    def chunk_text(self, text: str) -> List[str]:
        """Split large text into chunks for processing."""
        if len(text) <= CHUNK_SIZE:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            if end < len(text):
                # Find a good break point (paragraph or sentence)
                break_point = text.rfind('\n\n', start, end)
                if break_point == -1:
                    break_point = text.rfind('. ', start, end)
                if break_point > start:
                    end = break_point + 1

            chunks.append(text[start:end])
            start = end - OVERLAP_SIZE if end < len(text) else end

        return chunks

    def _build_document_analysis_prompt(self,
                                        text: str,
                                        context: Optional[str],
                                        doc_type: Optional[str]) -> str:
        """Build comprehensive document analysis prompt."""
        return f"""Analyze this legal document comprehensively. Extract all information in structured JSON format.

DOCUMENT TYPE: {doc_type or 'Unknown'}

CASE CONTEXT:
{context or 'No additional context provided'}

DOCUMENT TEXT:
{text}

Extract and return as JSON with these sections:

{{
  "document_metadata": {{
    "apparent_author": "string or null",
    "apparent_date": "YYYY-MM-DD or null",
    "document_type": "string",
    "parties_mentioned": ["list of party names"]
  }},

  "claims": [
    {{
      "claim_type": "assertion|allegation|finding|conclusion|recommendation|opinion",
      "claim_text": "exact quote of the claim",
      "claimant": "who made this claim",
      "target": "who/what the claim is about",
      "evidence_cited": ["list of evidence referenced"],
      "page_paragraph": "approximate location",
      "confidence": 0.0-1.0
    }}
  ],

  "entities": [
    {{
      "name": "entity name",
      "type": "person|organization|court|case_reference|date|location",
      "role": "their role in the case if apparent",
      "mentions": number of times mentioned
    }}
  ],

  "timeline_events": [
    {{
      "date": "YYYY-MM-DD or approximate",
      "event_type": "incident|hearing|report|decision|filing",
      "description": "what happened",
      "participants": ["who was involved"],
      "significance": "critical|important|routine"
    }}
  ],

  "procedural_elements": [
    {{
      "procedure": "name of procedure/requirement",
      "status": "followed|violated|unclear",
      "evidence": "what shows compliance or violation"
    }}
  ],

  "potential_issues": [
    {{
      "issue_type": "unsupported_assertion|circular_reasoning|missing_evidence|contradiction|bias_indicator",
      "description": "description of the issue",
      "quote": "relevant text",
      "severity": "high|medium|low"
    }}
  ]
}}

Be thorough and extract EVERY claim, entity, and event. Include exact quotes where possible."""

    def _build_claims_extraction_prompt(self,
                                        text: str,
                                        professional_context: Optional[str]) -> str:
        """Build prompt for focused claims extraction."""
        return f"""Extract ALL claims, assertions, allegations, findings, and conclusions from this legal text.

PROFESSIONAL CONTEXT: {professional_context or 'Unknown author/capacity'}

TEXT:
{text}

Return JSON with this structure:
{{
  "claims": [
    {{
      "claim_type": "assertion|allegation|finding|conclusion|recommendation|observation|submission",
      "claim_text": "EXACT quote of the claim - include full sentence",
      "context": "surrounding text for context (1-2 sentences before/after)",
      "claimant": "who made this claim (if identifiable)",
      "claimant_capacity": "their professional capacity",
      "target_entity": "who/what the claim is about",
      "date_mentioned": "any date associated with the claim",
      "evidence_cited": ["specific evidence referenced to support this claim"],
      "evidence_strength": "strong|moderate|weak|absent",
      "logical_issues": ["any logical problems: circular reasoning, unsupported, etc."],
      "confidence": 0.0-1.0
    }}
  ],
  "statistics": {{
    "total_claims": number,
    "by_type": {{"assertion": n, "allegation": n, ...}},
    "supported_claims": number,
    "unsupported_claims": number
  }}
}}

IMPORTANT:
- Extract EVERY factual claim, not just major ones
- Include claims about what someone said, did, or believed
- Include professional opinions and recommendations
- Flag any claims that appear unsupported or contradictory"""

    def _build_bias_detection_prompt(self,
                                     text: str,
                                     professional: Optional[str],
                                     capacity: Optional[str]) -> str:
        """Build prompt for cognitive bias detection."""
        return f"""Analyze this text for cognitive biases and rhetorical manipulation.

AUTHOR: {professional or 'Unknown'}
CAPACITY: {capacity or 'Unknown'}

TEXT:
{text}

Detect and return as JSON:
{{
  "biases": [
    {{
      "bias_type": "confirmation|outcome|anchoring|availability|hindsight|attribution|groupthink|authority|narrative|selective_attention",
      "evidence_text": "EXACT quote showing the bias",
      "context": "surrounding context",
      "explanation": "why this indicates the bias",
      "severity": "high|medium|low",
      "confidence": 0.0-1.0
    }}
  ],

  "rhetorical_manipulation": [
    {{
      "technique": "emotional_appeal|appeal_to_authority|straw_man|ad_hominem|false_dichotomy|loaded_language|omission",
      "evidence_text": "exact quote",
      "explanation": "how this manipulates",
      "impact": "high|medium|low"
    }}
  ],

  "institutional_narrative_indicators": [
    {{
      "indicator": "coordinated_language|selective_quotation|evidence_omission|predetermined_conclusion",
      "evidence_text": "quote",
      "explanation": "why this suggests institutional narrative"
    }}
  ],

  "overall_assessment": {{
    "objectivity_score": 0.0-1.0,
    "primary_concerns": ["list main bias/manipulation concerns"],
    "summary": "brief overall assessment"
  }}
}}

Be rigorous but fair - only flag clear instances with specific evidence."""

    def _build_competing_claims_prompt(self,
                                       claim_a: Dict[str, Any],
                                       claim_b: Dict[str, Any]) -> str:
        """Build prompt for analyzing competing claims."""
        return f"""Evaluate the logical relationship between these competing claims:

CLAIM A:
Text: {claim_a.get('claim_text')}
Made by: {claim_a.get('claimant', 'Unknown')} as {claim_a.get('claimant_capacity', 'Unknown')}
Date: {claim_a.get('date_made', 'Unknown')}
Evidence cited: {claim_a.get('evidence_cited', 'None specified')}

CLAIM B:
Text: {claim_b.get('claim_text')}
Made by: {claim_b.get('claimant', 'Unknown')} as {claim_b.get('claimant_capacity', 'Unknown')}
Date: {claim_b.get('date_made', 'Unknown')}
Evidence cited: {claim_b.get('evidence_cited', 'None specified')}

Analyze and return as JSON:
{{
  "relationship": "contradicts|supports|qualifies|supersedes|partially_contradicts|contextualizes",

  "logical_analysis": {{
    "claim_a_validity": {{
      "premises_stated": ["list premises"],
      "conclusion_follows": true/false,
      "logical_gaps": ["any gaps in reasoning"]
    }},
    "claim_b_validity": {{
      "premises_stated": ["list premises"],
      "conclusion_follows": true/false,
      "logical_gaps": ["any gaps in reasoning"]
    }}
  }},

  "evidential_analysis": {{
    "claim_a_evidence_strength": "strong|moderate|weak|absent",
    "claim_b_evidence_strength": "strong|moderate|weak|absent",
    "evidence_comparison": "which claim has better evidential support and why"
  }},

  "credibility_factors": {{
    "claim_a": ["factors affecting credibility"],
    "claim_b": ["factors affecting credibility"]
  }},

  "resolution_recommendation": {{
    "favored_claim": "a|b|neither|both_partially_valid",
    "confidence": 0.0-1.0,
    "reasoning": "detailed explanation"
  }}
}}"""

    def _build_timeline_extraction_prompt(self,
                                          text: str,
                                          existing_events: Optional[List[Dict]]) -> str:
        """Build prompt for timeline event extraction."""
        existing_str = ""
        if existing_events:
            existing_str = f"\nEXISTING TIMELINE EVENTS (avoid duplicates):\n{json.dumps(existing_events[:10], indent=2)}\n"

        return f"""Extract all chronological events from this legal document.
{existing_str}
DOCUMENT TEXT:
{text}

Return JSON:
{{
  "events": [
    {{
      "date": "YYYY-MM-DD (use best estimate if approximate)",
      "date_precision": "exact|month|year|approximate",
      "time": "HH:MM or null",
      "event_type": "incident|allegation|report|assessment|hearing|decision|order|filing|disclosure|meeting|contact",
      "description": "clear description of what happened",
      "participants": ["list of people involved"],
      "location": "where it happened if mentioned",
      "source_quote": "exact text this is based on",
      "significance": "critical|important|routine|minor",
      "verified": false
    }}
  ],
  "date_references": [
    {{
      "original_text": "how the date was written",
      "interpreted_as": "YYYY-MM-DD",
      "confidence": 0.0-1.0
    }}
  ]
}}

IMPORTANT:
- Extract ALL date-referenced events, even minor ones
- Include relative dates ("two weeks later", "the following month")
- Flag any timeline inconsistencies you notice"""

    def _build_summary_prompt(self, case_data: Dict[str, Any]) -> str:
        """Build prompt for executive summary generation."""
        return f"""Generate an executive summary for this legal case analysis.

CASE DATA:
{json.dumps(case_data, indent=2, default=str)}

Write a professional forensic analysis summary following this structure:

# Executive Synthesis
[2-3 paragraph overview of key findings, major issues identified, and overall assessment]

## Key Parties and Their Positions
[Brief summary of each party's position and the strength of their case]

## Critical Timeline Points
[Most significant events in chronological order with implications]

## Evidence Assessment
[Summary of evidence quality, gaps, and contradictions]

## Bias and Procedural Concerns
[Any detected biases or procedural violations with severity]

## Recommendations
[Strategic recommendations based on the analysis]

Write in a formal, objective tone suitable for legal proceedings. Be specific with references to evidence."""

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from Claude's response, handling markdown code blocks."""
        text = response_text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # Return error structure
            return {
                "error": f"Failed to parse JSON response: {str(e)}",
                "raw_response": response_text[:500]
            }

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics."""
        return {
            "total_tokens": self.total_tokens_used,
            "estimated_cost": self.total_tokens_used * 0.00001  # Rough estimate
        }


# Singleton instance
_claude_service: Optional[ClaudeService] = None


def get_claude_service() -> ClaudeService:
    """Get or create Claude service instance."""
    global _claude_service
    if _claude_service is None:
        _claude_service = ClaudeService()
    return _claude_service
