"""
Response Parser for Phronesis LEX

Parses AI responses (JSON) back into structured data for the system.
Handles various response formats and error recovery.
"""

import json
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class ParseError(Exception):
    """Error during response parsing."""
    pass


class ParsedClaim(BaseModel):
    """A parsed claim from AI response."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    claimant: Optional[str] = None
    document_reference: Optional[str] = None
    claim_type: Optional[str] = None
    evidence_type: Optional[str] = None
    date_mentioned: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)
    requires_corroboration: bool = True
    legal_relevance: Optional[str] = None
    confidence: float = 1.0


class ParsedSummary(BaseModel):
    """A parsed document summary from AI response."""
    document_type: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    parties: List[Dict[str, str]] = Field(default_factory=list)
    executive_summary: str = ""
    key_points: List[Dict[str, Any]] = Field(default_factory=list)
    timeline_elements: List[Dict[str, str]] = Field(default_factory=list)
    children_welfare: Dict[str, List[str]] = Field(default_factory=dict)
    next_steps: List[str] = Field(default_factory=list)
    flags: Dict[str, bool] = Field(default_factory=dict)


class ParsedContradiction(BaseModel):
    """A parsed contradiction analysis from AI response."""
    is_contradiction: bool
    contradiction_type: Optional[str] = None
    severity: Optional[str] = None
    confidence: float = 0.0
    specific_conflict: Optional[str] = None
    possible_explanations: List[str] = Field(default_factory=list)
    evidence_needed: List[str] = Field(default_factory=list)
    legal_significance: Dict[str, Any] = Field(default_factory=dict)


class ParsedCredibility(BaseModel):
    """A parsed credibility assessment from AI response."""
    internal_consistency_score: float = 0.0
    specificity_score: float = 0.0
    self_interest_ratio: float = 0.0
    overall_credibility_score: float = 0.0
    key_strengths: List[str] = Field(default_factory=list)
    key_concerns: List[str] = Field(default_factory=list)
    areas_requiring_clarification: List[str] = Field(default_factory=list)
    lucas_direction_notes: Optional[str] = None


class ParsedTimeline(BaseModel):
    """A parsed timeline from AI response."""
    events: List[Dict[str, Any]] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    gaps: List[Dict[str, str]] = Field(default_factory=list)
    date_range: Dict[str, str] = Field(default_factory=dict)


class ParseResult(BaseModel):
    """Result of parsing an AI response."""
    success: bool
    prompt_type: str
    parsed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    data: Optional[Dict[str, Any]] = None
    claims: Optional[List[ParsedClaim]] = None
    summary: Optional[ParsedSummary] = None
    contradiction: Optional[ParsedContradiction] = None
    credibility: Optional[ParsedCredibility] = None
    timeline: Optional[ParsedTimeline] = None
    raw_response: str = ""
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ResponseParser:
    """
    Parse AI responses back into structured data.

    Handles:
    - Clean JSON responses
    - JSON wrapped in markdown code blocks
    - JSON with extra text before/after
    - Partial JSON (attempts recovery)
    """

    def parse(
        self,
        response: str,
        prompt_type: str,
        strict: bool = False
    ) -> ParseResult:
        """
        Parse an AI response based on the prompt type.

        Args:
            response: The raw AI response text
            prompt_type: Type of prompt that generated this response
            strict: If True, fail on any parsing issues; if False, attempt recovery

        Returns:
            ParseResult with parsed data and any errors/warnings
        """
        errors = []
        warnings = []

        # Extract JSON from response
        json_data, extraction_warnings = self._extract_json(response)
        warnings.extend(extraction_warnings)

        if json_data is None:
            return ParseResult(
                success=False,
                prompt_type=prompt_type,
                raw_response=response,
                errors=["Could not extract valid JSON from response"],
                warnings=warnings
            )

        # Parse based on prompt type
        try:
            result = self._parse_by_type(prompt_type, json_data, strict)
            result.raw_response = response
            result.warnings = warnings
            return result
        except Exception as e:
            return ParseResult(
                success=False,
                prompt_type=prompt_type,
                raw_response=response,
                data=json_data,  # Include raw JSON even if type parsing fails
                errors=[f"Error parsing {prompt_type}: {str(e)}"],
                warnings=warnings
            )

    def _extract_json(self, text: str) -> Tuple[Optional[Dict], List[str]]:
        """
        Extract JSON from text, handling various formats.

        Returns:
            Tuple of (parsed JSON dict or None, list of warnings)
        """
        warnings = []
        text = text.strip()

        # Try direct JSON parse first
        try:
            return json.loads(text), []
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        code_block_patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'`([\s\S]*?)`'
        ]

        for pattern in code_block_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    data = json.loads(match.strip())
                    warnings.append("JSON extracted from code block")
                    return data, warnings
                except json.JSONDecodeError:
                    continue

        # Try to find JSON object in text (starts with { ends with })
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                warnings.append("JSON extracted from surrounding text")
                return data, warnings
            except json.JSONDecodeError:
                pass

        # Try to find JSON array in text
        array_match = re.search(r'\[[\s\S]*\]', text)
        if array_match:
            try:
                data = json.loads(array_match.group())
                warnings.append("JSON array extracted from text")
                return {"items": data}, warnings
            except json.JSONDecodeError:
                pass

        # Attempt to fix common JSON issues
        fixed_text = self._attempt_json_fix(text)
        if fixed_text:
            try:
                data = json.loads(fixed_text)
                warnings.append("JSON repaired before parsing")
                return data, warnings
            except json.JSONDecodeError:
                pass

        return None, ["Could not find valid JSON in response"]

    def _attempt_json_fix(self, text: str) -> Optional[str]:
        """Attempt to fix common JSON formatting issues."""
        # Remove potential BOM or invisible characters
        text = text.encode('utf-8', 'ignore').decode('utf-8')

        # Try to find JSON-like content
        match = re.search(r'\{[\s\S]*\}', text)
        if not match:
            return None

        json_text = match.group()

        # Fix common issues
        # 1. Trailing commas before closing braces/brackets
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)

        # 2. Single quotes to double quotes (simple cases)
        # Only if no double quotes present in values
        if '"' not in json_text and "'" in json_text:
            json_text = json_text.replace("'", '"')

        # 3. Missing quotes around keys
        json_text = re.sub(r'(\{|,)\s*(\w+)\s*:', r'\1"\2":', json_text)

        return json_text

    def _parse_by_type(
        self,
        prompt_type: str,
        data: Dict[str, Any],
        strict: bool
    ) -> ParseResult:
        """Parse JSON data based on prompt type."""

        if prompt_type == "claim_extraction":
            return self._parse_claims(data, strict)
        elif prompt_type == "document_summary":
            return self._parse_summary(data, strict)
        elif prompt_type == "contradiction_analysis":
            return self._parse_contradiction(data, strict)
        elif prompt_type == "credibility_assessment":
            return self._parse_credibility(data, strict)
        elif prompt_type == "timeline_extraction":
            return self._parse_timeline(data, strict)
        else:
            # Generic parsing - just return the data
            return ParseResult(
                success=True,
                prompt_type=prompt_type,
                data=data
            )

    def _parse_claims(self, data: Dict, strict: bool) -> ParseResult:
        """Parse claim extraction response."""
        claims = []
        errors = []

        raw_claims = data.get("claims", [])
        if not raw_claims and "items" in data:
            raw_claims = data["items"]

        for i, claim_data in enumerate(raw_claims):
            try:
                if isinstance(claim_data, str):
                    # Simple string claim
                    claims.append(ParsedClaim(text=claim_data))
                else:
                    claims.append(ParsedClaim(
                        id=claim_data.get("id", str(uuid.uuid4())),
                        text=claim_data.get("text", ""),
                        claimant=claim_data.get("claimant"),
                        document_reference=claim_data.get("document_reference"),
                        claim_type=claim_data.get("claim_type"),
                        evidence_type=claim_data.get("evidence_type"),
                        date_mentioned=claim_data.get("date_mentioned"),
                        subjects=claim_data.get("subjects", []),
                        requires_corroboration=claim_data.get("requires_corroboration", True),
                        legal_relevance=claim_data.get("legal_relevance")
                    ))
            except Exception as e:
                if strict:
                    raise
                errors.append(f"Error parsing claim {i}: {str(e)}")

        return ParseResult(
            success=len(claims) > 0 or len(errors) == 0,
            prompt_type="claim_extraction",
            data=data,
            claims=claims,
            errors=errors
        )

    def _parse_summary(self, data: Dict, strict: bool) -> ParseResult:
        """Parse document summary response."""
        try:
            summary = ParsedSummary(
                document_type=data.get("document_type"),
                author=data.get("author"),
                date=data.get("date"),
                parties=data.get("parties", []),
                executive_summary=data.get("executive_summary", ""),
                key_points=data.get("key_points", []),
                timeline_elements=data.get("timeline_elements", []),
                children_welfare=data.get("children_welfare", {}),
                next_steps=data.get("next_steps", []),
                flags=data.get("flags", {})
            )

            return ParseResult(
                success=True,
                prompt_type="document_summary",
                data=data,
                summary=summary
            )
        except Exception as e:
            if strict:
                raise
            return ParseResult(
                success=False,
                prompt_type="document_summary",
                data=data,
                errors=[f"Error parsing summary: {str(e)}"]
            )

    def _parse_contradiction(self, data: Dict, strict: bool) -> ParseResult:
        """Parse contradiction analysis response."""
        try:
            assessment = data.get("contradiction_assessment", {})
            analysis = data.get("analysis", {})
            resolution = data.get("resolution", {})

            contradiction = ParsedContradiction(
                is_contradiction=assessment.get("is_contradiction", False),
                contradiction_type=assessment.get("contradiction_type"),
                severity=assessment.get("severity"),
                confidence=assessment.get("confidence", 0.0),
                specific_conflict=analysis.get("specific_conflict"),
                possible_explanations=analysis.get("possible_explanations", []),
                evidence_needed=resolution.get("evidence_needed", []),
                legal_significance=data.get("legal_significance", {})
            )

            return ParseResult(
                success=True,
                prompt_type="contradiction_analysis",
                data=data,
                contradiction=contradiction
            )
        except Exception as e:
            if strict:
                raise
            return ParseResult(
                success=False,
                prompt_type="contradiction_analysis",
                data=data,
                errors=[f"Error parsing contradiction: {str(e)}"]
            )

    def _parse_credibility(self, data: Dict, strict: bool) -> ParseResult:
        """Parse credibility assessment response."""
        try:
            indicators = data.get("credibility_indicators", {})
            overall = data.get("overall_assessment", {})

            credibility = ParsedCredibility(
                internal_consistency_score=indicators.get("internal_consistency", {}).get("score", 0.0),
                specificity_score=indicators.get("specificity", {}).get("score", 0.0),
                self_interest_ratio=indicators.get("self_interest", {}).get("ratio", 0.0),
                overall_credibility_score=overall.get("credibility_score", 0.0),
                key_strengths=overall.get("key_strengths", []),
                key_concerns=overall.get("key_concerns", []),
                areas_requiring_clarification=overall.get("areas_requiring_clarification", []),
                lucas_direction_notes=data.get("lucas_direction_notes")
            )

            return ParseResult(
                success=True,
                prompt_type="credibility_assessment",
                data=data,
                credibility=credibility
            )
        except Exception as e:
            if strict:
                raise
            return ParseResult(
                success=False,
                prompt_type="credibility_assessment",
                data=data,
                errors=[f"Error parsing credibility: {str(e)}"]
            )

    def _parse_timeline(self, data: Dict, strict: bool) -> ParseResult:
        """Parse timeline extraction response."""
        try:
            timeline = ParsedTimeline(
                events=data.get("timeline", []),
                conflicts=data.get("conflicts", []),
                gaps=data.get("gaps", []),
                date_range=data.get("summary", {}).get("date_range", {})
            )

            return ParseResult(
                success=True,
                prompt_type="timeline_extraction",
                data=data,
                timeline=timeline
            )
        except Exception as e:
            if strict:
                raise
            return ParseResult(
                success=False,
                prompt_type="timeline_extraction",
                data=data,
                errors=[f"Error parsing timeline: {str(e)}"]
            )

    # ==================== Batch Processing ====================

    def parse_multiple(
        self,
        responses: List[Tuple[str, str]],  # [(response, prompt_type), ...]
        strict: bool = False
    ) -> List[ParseResult]:
        """Parse multiple responses."""
        return [
            self.parse(response, prompt_type, strict)
            for response, prompt_type in responses
        ]

    def merge_claim_results(self, results: List[ParseResult]) -> List[ParsedClaim]:
        """Merge claims from multiple parse results, deduplicating."""
        all_claims = []
        seen_texts = set()

        for result in results:
            if result.claims:
                for claim in result.claims:
                    # Simple deduplication by text
                    normalized = claim.text.lower().strip()
                    if normalized not in seen_texts:
                        seen_texts.add(normalized)
                        all_claims.append(claim)

        return all_claims

    def merge_timeline_results(self, results: List[ParseResult]) -> ParsedTimeline:
        """Merge timeline events from multiple parse results."""
        all_events = []
        all_conflicts = []
        all_gaps = []

        for result in results:
            if result.timeline:
                all_events.extend(result.timeline.events)
                all_conflicts.extend(result.timeline.conflicts)
                all_gaps.extend(result.timeline.gaps)

        # Sort events by date
        all_events.sort(key=lambda e: e.get("date", "9999-99-99"))

        # Detect new conflicts from merged data
        # (Events with same date but different descriptions from different sources)
        date_events: Dict[str, List[Dict]] = {}
        for event in all_events:
            date = event.get("date")
            if date:
                if date not in date_events:
                    date_events[date] = []
                date_events[date].append(event)

        for date, events in date_events.items():
            if len(events) > 1:
                sources = set(e.get("source_document", "unknown") for e in events)
                if len(sources) > 1:
                    all_conflicts.append({
                        "date": date,
                        "events": events,
                        "note": "Multiple events on same date from different sources"
                    })

        return ParsedTimeline(
            events=all_events,
            conflicts=all_conflicts,
            gaps=all_gaps
        )
