"""
Claim Extraction Service
Uses Claude AI to extract epistemic claims from legal documents.
"""
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic package not installed. AI extraction unavailable.")


# Prompt for FCIP claim extraction
CLAIM_EXTRACTION_PROMPT = '''You are an expert legal analyst specializing in UK Family Court proceedings.
Extract ALL claims from this document with precise epistemic annotation.

For each claim, identify:
1. **claim_type**: assertion, allegation, finding, conclusion, recommendation, opinion, observation, concern, submission
2. **claim_text**: The exact text of the claim
3. **source_quote**: Full sentence containing the claim
4. **modality**: How the claim is presented:
   - asserted: Direct statement ("The father attended")
   - reported: Attributed to someone ("The mother stated...")
   - alleged: Contested/unproven ("It is alleged...")
   - denied: Negation ("The father denies...")
   - hypothetical: Conditional ("If the father had...")
5. **polarity**: affirm or negate
6. **certainty**: 0.0-1.0 based on hedging language
7. **certainty_markers**: Words indicating certainty ("clearly", "perhaps", "may")
8. **subject**: Who/what the claim is about
9. **predicate**: The action or state
10. **object_value**: What is being claimed
11. **asserted_by**: Who made this claim
12. **time_expression**: Any temporal reference

DOCUMENT TYPE: {doc_type}
DOCUMENT TEXT:
{text}

Return JSON array of claims:
```json
[
  {{
    "claim_type": "string",
    "claim_text": "string",
    "source_quote": "string",
    "modality": "asserted|reported|alleged|denied|hypothetical",
    "polarity": "affirm|negate",
    "certainty": 0.0-1.0,
    "certainty_markers": ["list"],
    "subject": "string or null",
    "predicate": "string or null",
    "object_value": "string or null",
    "asserted_by": "string or null",
    "time_expression": "string or null",
    "page_paragraph": "string or null"
  }}
]
```

Extract EVERY factual claim, allegation, finding, and professional opinion.
Be thorough - include minor claims and observations.
'''


class ClaimExtractionService:
    """Service for extracting claims from documents using Claude AI."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'ANTHROPIC_API_KEY', None)
        self.client = None
        self.model = getattr(settings, 'CLAUDE_MODEL', 'claude-sonnet-4-20250514')
        self.max_tokens = 8192
        
        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
    
    @property
    def is_available(self) -> bool:
        """Check if the service is available."""
        return self.client is not None
    
    def extract_claims(
        self,
        text: str,
        doc_type: str = 'other',
        case_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract claims from document text.
        
        Args:
            text: Document text to analyze
            doc_type: Type of document
            case_context: Optional case context
            
        Returns:
            Dict with 'claims' list, 'tokens_used', 'prompt_hash'
        """
        if not self.is_available:
            return {
                'claims': [],
                'error': 'AI service not configured',
                'tokens_used': 0,
                'prompt_hash': None
            }
        
        prompt = CLAIM_EXTRACTION_PROMPT.format(
            doc_type=doc_type,
            text=text[:50000]  # Limit text size
        )
        
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            response_text = response.content[0].text
            
            claims = self._parse_claims_response(response_text)
            
            return {
                'claims': claims,
                'tokens_used': tokens_used,
                'prompt_hash': prompt_hash,
                'model': self.model
            }
            
        except Exception as e:
            logger.error(f"Claim extraction failed: {e}")
            return {
                'claims': [],
                'error': str(e),
                'tokens_used': 0,
                'prompt_hash': prompt_hash
            }
    
    def _parse_claims_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse Claude's response to extract claims."""
        text = response_text.strip()
        
        # Remove markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'claims' in data:
                return data['claims']
            return []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse claims JSON: {e}")
            # Try to extract JSON array from response
            import re
            match = re.search(r'\[[\s\S]*\]', text)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return []
    
    def chunk_text(self, text: str, chunk_size: int = 30000, overlap: int = 1000) -> List[str]:
        """Split large text into overlapping chunks for processing."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                # Find a good break point
                break_point = text.rfind('\n\n', start + chunk_size // 2, end)
                if break_point == -1:
                    break_point = text.rfind('. ', start + chunk_size // 2, end)
                if break_point > start:
                    end = break_point + 1
            
            chunks.append(text[start:end])
            start = end - overlap if end < len(text) else end
        
        return chunks

