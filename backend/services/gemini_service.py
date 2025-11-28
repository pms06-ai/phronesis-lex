"""
Gemini AI Service for Phronesis LEX
Document analysis using Google's Gemini Pro with massive context window.

Role: Strictly document analysis tasks
- Entity extraction
- Claims extraction  
- Timeline extraction
- Bias detection in text

Does NOT handle: Synthesis, contradiction analysis, evidence chains (those go to Claude)
"""
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import GOOGLE_API_KEY, GEMINI_MODEL, GEMINI_MAX_TOKENS

# Google AI import
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class GeminiService:
    """
    Gemini Pro service for document analysis.
    Leverages massive context window (1M+ tokens) for full-document processing.
    """

    def __init__(self, api_key: str = GOOGLE_API_KEY):
        self.api_key = api_key
        self.max_tokens = GEMINI_MAX_TOKENS
        self.total_tokens_used = 0
        self.model = None
        
        # Only initialize if API is available and configured
        if HAS_GEMINI and api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    def _ensure_model(self):
        """Ensure API model is available before making calls."""
        if not HAS_GEMINI:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        if not self.model:
            raise ValueError("GOOGLE_API_KEY not configured")

    async def analyze_document(
        self,
        document_text: str,
        case_context: Optional[str] = None,
        doc_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive document analysis - extracts all structured information.
        Uses Gemini's large context to process entire documents at once.
        """
        self._ensure_model()
        prompt = self._build_document_analysis_prompt(document_text, case_context, doc_type)
        
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=0.1  # Low temperature for factual extraction
            )
        )
        
        return self._parse_json_response(response.text)

    async def extract_entities(
        self,
        document_text: str,
        doc_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract named entities from document text."""
        self._ensure_model()
        prompt = self._build_entity_extraction_prompt(document_text, doc_type)
        
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=0.1
            )
        )
        
        result = self._parse_json_response(response.text)
        return result.get("entities", [])

    async def extract_claims(
        self,
        document_text: str,
        professional_context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract all claims, assertions, and allegations from document."""
        self._ensure_model()
        prompt = self._build_claims_extraction_prompt(document_text, professional_context)
        
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=0.1
            )
        )
        
        result = self._parse_json_response(response.text)
        return result.get("claims", [])

    async def extract_timeline(
        self,
        document_text: str,
        existing_events: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """Extract chronological events from document."""
        self._ensure_model()
        prompt = self._build_timeline_extraction_prompt(document_text, existing_events)
        
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=0.1
            )
        )
        
        result = self._parse_json_response(response.text)
        return result.get("events", [])

    async def detect_biases(
        self,
        text: str,
        professional: Optional[str] = None,
        capacity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Detect cognitive biases and rhetorical manipulation in text."""
        self._ensure_model()
        prompt = self._build_bias_detection_prompt(text, professional, capacity)
        
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=0.2  # Slightly higher for nuanced detection
            )
        )
        
        result = self._parse_json_response(response.text)
        return result.get("biases", [])

    async def analyze_documents_batch(
        self,
        documents: List[Dict[str, str]],
        case_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze multiple documents in a single call.
        Gemini's 1M+ context allows processing many documents together.
        
        Args:
            documents: List of {"id": str, "text": str, "doc_type": str}
            case_context: Overall case context
        """
        self._ensure_model()
        prompt = self._build_batch_analysis_prompt(documents, case_context)
        
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=0.1
            )
        )
        
        return self._parse_json_response(response.text)

    # =========================================================================
    # Prompt Builders
    # =========================================================================

    def _build_document_analysis_prompt(
        self,
        text: str,
        context: Optional[str],
        doc_type: Optional[str]
    ) -> str:
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
      "mentions": "number of times mentioned"
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

Be thorough and extract EVERY claim, entity, and event. Include exact quotes where possible.
Return ONLY valid JSON, no additional text."""

    def _build_entity_extraction_prompt(
        self,
        text: str,
        doc_type: Optional[str]
    ) -> str:
        """Build entity extraction prompt."""
        return f"""Extract all named entities from this {doc_type or 'legal'} document.

DOCUMENT TEXT:
{text}

Return JSON:
{{
  "entities": [
    {{
      "text": "exact text as it appears",
      "type": "PERSON|ORGANIZATION|COURT|CASE_NUMBER|DATE|LOCATION|LEGAL_REFERENCE|JUDGE|SOLICITOR|SOCIAL_WORKER",
      "normalized": "standardized form of the entity",
      "role": "their role if apparent (judge, applicant, respondent, etc.)",
      "confidence": 0.0-1.0
    }}
  ]
}}

Extract ALL entities including:
- Judges (format: HHJ Name, DJ Name, etc.)
- Courts (Family Court, High Court, etc.)
- Case numbers (e.g., PE23C50095)
- Local authorities
- Police forces
- Solicitor firms
- Social workers
- All dates mentioned
- Locations

Return ONLY valid JSON."""

    def _build_claims_extraction_prompt(
        self,
        text: str,
        professional_context: Optional[str]
    ) -> str:
        """Build claims extraction prompt."""
        return f"""Extract ALL claims, assertions, allegations, findings, and conclusions from this legal text.

PROFESSIONAL CONTEXT: {professional_context or 'Unknown author/capacity'}

TEXT:
{text}

Return JSON:
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
    "total_claims": 0,
    "by_type": {{}},
    "supported_claims": 0,
    "unsupported_claims": 0
  }}
}}

IMPORTANT:
- Extract EVERY factual claim, not just major ones
- Include claims about what someone said, did, or believed
- Include professional opinions and recommendations
- Flag any claims that appear unsupported or contradictory

Return ONLY valid JSON."""

    def _build_timeline_extraction_prompt(
        self,
        text: str,
        existing_events: Optional[List[Dict]]
    ) -> str:
        """Build timeline extraction prompt."""
        existing_str = ""
        if existing_events:
            existing_str = f"\nEXISTING EVENTS (avoid duplicates):\n{json.dumps(existing_events[:10], indent=2)}\n"

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
      "significance": "critical|important|routine|minor"
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
- Flag any timeline inconsistencies

Return ONLY valid JSON."""

    def _build_bias_detection_prompt(
        self,
        text: str,
        professional: Optional[str],
        capacity: Optional[str]
    ) -> str:
        """Build bias detection prompt."""
        return f"""Analyze this text for cognitive biases and rhetorical manipulation.

AUTHOR: {professional or 'Unknown'}
CAPACITY: {capacity or 'Unknown'}

TEXT:
{text}

Return JSON:
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
  "overall_assessment": {{
    "objectivity_score": 0.0-1.0,
    "primary_concerns": ["list main concerns"],
    "summary": "brief overall assessment"
  }}
}}

Be rigorous but fair - only flag clear instances with specific evidence.
Return ONLY valid JSON."""

    def _build_batch_analysis_prompt(
        self,
        documents: List[Dict[str, str]],
        case_context: Optional[str]
    ) -> str:
        """Build prompt for batch document analysis."""
        docs_text = ""
        for i, doc in enumerate(documents):
            docs_text += f"""
=== DOCUMENT {i+1} (ID: {doc.get('id', 'unknown')}, Type: {doc.get('doc_type', 'unknown')}) ===
{doc.get('text', '')}

"""
        
        return f"""Analyze these {len(documents)} legal documents comprehensively.

CASE CONTEXT:
{case_context or 'No additional context provided'}

{docs_text}

For each document, extract and return as JSON:

{{
  "documents": [
    {{
      "document_id": "the ID provided",
      "claims": [...],
      "entities": [...],
      "timeline_events": [...],
      "potential_issues": [...]
    }}
  ],
  "cross_document_observations": {{
    "recurring_entities": ["entities appearing in multiple documents"],
    "timeline_consistency": "assessment of date consistency across docs",
    "narrative_patterns": ["patterns in how events are described"]
  }}
}}

Be thorough. Return ONLY valid JSON."""

    # =========================================================================
    # Response Parsing
    # =========================================================================

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from Gemini's response, handling markdown code blocks."""
        import re
        
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
        """Get usage statistics."""
        return {
            "total_tokens": self.total_tokens_used,
            "model": GEMINI_MODEL
        }


# Singleton instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create Gemini service instance."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service

