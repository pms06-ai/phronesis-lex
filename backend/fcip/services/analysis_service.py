"""
FCIP Analysis Service - Replacement for Claude Service

This service integrates all FCIP engines to provide comprehensive
forensic document analysis with epistemic claim extraction.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from anthropic import Anthropic

from ..config import config
from ..models.core import (
    Claim, ClaimType, Modality, Polarity, Confidence,
    Entity, EntityType, ToulminArgument, BiasSignal, ParsedTemporal
)
from ..engines.entity_resolution import EntityResolutionEngine, EntityRoster
from ..engines.temporal import TemporalParser, CourtCalendar
from ..engines.argumentation import ArgumentationEngine, ArgumentPattern
from ..engines.bias import BiasDetectionEngine
from ..prompts.extraction import (
    FORENSIC_ANALYST_SYSTEM,
    CLAIM_EXTRACTION_PROMPT,
    DOCUMENT_CLASSIFICATION_PROMPT,
    get_prompt_hash,
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Complete analysis result from FCIP."""
    document_id: str
    case_id: str

    # Classification
    doc_type: str = "unknown"
    doc_type_confidence: float = 0.0
    doc_date: Optional[str] = None
    author: Optional[str] = None

    # Extracted data
    claims: List[Claim] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    timeline_events: List[dict] = field(default_factory=list)

    # Analysis results
    bias_signals: List[BiasSignal] = field(default_factory=list)
    arguments: List[ToulminArgument] = field(default_factory=list)
    contradictions: List[dict] = field(default_factory=list)

    # Metadata
    extraction_prompt_hash: Optional[str] = None
    tokens_used: int = 0
    success: bool = True
    error: Optional[str] = None


class FCIPAnalysisService:
    """
    Main analysis service integrating all FCIP engines.

    Replaces the original claude_service.py with enhanced
    epistemic extraction and statistical analysis.
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize the analysis service."""
        self.client = None
        if anthropic_api_key:
            self.client = Anthropic(api_key=anthropic_api_key)

        # Initialize engines
        self.entity_engine = EntityResolutionEngine()
        self.temporal_engine = TemporalParser()
        self.argument_engine = ArgumentationEngine()
        self.bias_engine = BiasDetectionEngine()

        # Model configuration
        self.model = "claude-sonnet-4-20250514"
        self.temperature = config.llm_temperature
        self.max_tokens = config.llm_max_tokens

    def set_api_key(self, api_key: str) -> None:
        """Set or update the Anthropic API key."""
        self.client = Anthropic(api_key=api_key)

    async def analyze_document(
        self,
        document_id: str,
        text: str,
        case_id: str,
        doc_type: Optional[str] = None,
        doc_date: Optional[str] = None,
        author: Optional[str] = None,
        professionals: Optional[List[dict]] = None
    ) -> AnalysisResult:
        """
        Perform comprehensive document analysis.

        Args:
            document_id: Unique document identifier
            text: Document text content
            case_id: Parent case identifier
            doc_type: Document type (if known)
            doc_date: Document date (if known)
            author: Document author (if known)
            professionals: List of known professionals to seed entity roster

        Returns:
            AnalysisResult with all extracted data
        """
        result = AnalysisResult(document_id=document_id, case_id=case_id)

        try:
            # 1. Seed entity roster from professionals
            if professionals:
                self.entity_engine.seed_from_professionals(professionals)

            # 2. Classify document if type unknown
            if not doc_type:
                classification = await self._classify_document(text)
                doc_type = classification.get("doc_type", "unknown")
                result.doc_type = doc_type
                result.doc_type_confidence = classification.get("confidence", 0.0)
                result.doc_date = classification.get("doc_date")
                result.author = classification.get("author")
            else:
                result.doc_type = doc_type
                result.doc_date = doc_date
                result.author = author

            # 3. Extract claims with epistemic annotation
            extraction = await self._extract_claims(
                text=text,
                doc_type=result.doc_type,
                doc_date=result.doc_date or "",
                author=result.author or "",
                case_id=case_id
            )

            # 4. Process extracted claims
            raw_claims = extraction.get("claims", [])
            raw_entities = extraction.get("entities", [])

            result.claims = self._process_claims(raw_claims, document_id, case_id)
            result.entities = self._process_entities(raw_entities)

            # 5. Resolve entities
            for claim in result.claims:
                if claim.subject:
                    resolution = self.entity_engine.resolve(claim.subject)
                    # Could update claim with resolved entity ID here

            # 6. Extract timeline events
            claim_dicts = [{"claim_id": str(c.claim_id), "time_expression": c.time_expression}
                         for c in result.claims if c.time_expression]
            result.timeline_events = self.temporal_engine.extract_timeline(claim_dicts)

            # 7. Detect bias signals
            result.bias_signals = self.bias_engine.analyse(
                doc_id=document_id,
                doc_type=result.doc_type,
                text=text,
                case_id=case_id
            )

            # 8. Store prompt hash for reproducibility
            result.extraction_prompt_hash = get_prompt_hash(
                CLAIM_EXTRACTION_PROMPT,
                text=text[:1000],
                doc_type=result.doc_type,
                doc_date=result.doc_date or "",
                author=result.author or "",
                case_id=case_id
            )

            result.success = True

        except Exception as e:
            logger.error(f"Analysis failed for document {document_id}: {e}")
            result.success = False
            result.error = str(e)

        return result

    async def _classify_document(self, text: str) -> dict:
        """Classify document type using LLM."""
        if not self.client:
            return {"doc_type": "unknown", "confidence": 0.0}

        prompt = DOCUMENT_CLASSIFICATION_PROMPT.format(text=text[:3000])

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=self.temperature,
                system=FORENSIC_ANALYST_SYSTEM,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            return json.loads(content)

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return {"doc_type": "unknown", "confidence": 0.0}

    async def _extract_claims(
        self,
        text: str,
        doc_type: str,
        doc_date: str,
        author: str,
        case_id: str
    ) -> dict:
        """Extract claims using FCIP prompts."""
        if not self.client:
            return {"claims": [], "entities": []}

        prompt = CLAIM_EXTRACTION_PROMPT.format(
            text=text,
            doc_type=doc_type,
            doc_date=doc_date,
            author=author,
            case_id=case_id
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=FORENSIC_ANALYST_SYSTEM,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Clean potential markdown formatting
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {"claims": [], "entities": []}
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {"claims": [], "entities": []}

    def _process_claims(
        self,
        raw_claims: List[dict],
        document_id: str,
        case_id: str
    ) -> List[Claim]:
        """Process raw claim dicts into Claim models."""
        claims = []

        for raw in raw_claims:
            try:
                # Map claim type
                claim_type_str = raw.get("claim_type", "assertion").lower()
                claim_type = ClaimType.ASSERTION
                for ct in ClaimType:
                    if ct.value == claim_type_str:
                        claim_type = ct
                        break

                # Map modality
                modality_str = raw.get("modality", "asserted").lower()
                modality = Modality.ASSERTED
                for m in Modality:
                    if m.value == modality_str:
                        modality = m
                        break

                # Map polarity
                polarity_str = raw.get("polarity", "affirm").lower()
                polarity = Polarity.AFFIRM if polarity_str == "affirm" else Polarity.NEGATE

                claim = Claim(
                    document_id=UUID(document_id) if isinstance(document_id, str) else document_id,
                    case_id=case_id,
                    text=raw.get("object_value", raw.get("text", "")),
                    claim_type=claim_type,
                    source_quote=raw.get("source_quote"),
                    subject=raw.get("subject"),
                    predicate=raw.get("predicate"),
                    predicate_category=raw.get("predicate_category"),
                    object_value=raw.get("object_value"),
                    modality=modality,
                    polarity=polarity,
                    certainty=float(raw.get("certainty", 0.5)),
                    certainty_markers=raw.get("certainty_markers", []),
                    asserted_by=raw.get("asserted_by"),
                    time_expression=raw.get("time_expression"),
                    time_start=raw.get("time_start"),
                    time_end=raw.get("time_end"),
                    is_requirement=raw.get("is_requirement", False),
                    deadline_expression=raw.get("deadline_expression"),
                    confidence=Confidence.llm_extracted(
                        score=float(raw.get("certainty", 0.5)),
                        model=self.model
                    )
                )
                claims.append(claim)

            except Exception as e:
                logger.warning(f"Failed to process claim: {e}")
                continue

        return claims

    def _process_entities(self, raw_entities: List[dict]) -> List[Entity]:
        """Process raw entity dicts into Entity models."""
        entities = []

        for raw in raw_entities:
            try:
                # Map entity type
                entity_type_str = raw.get("entity_type", "person").lower()
                entity_type = EntityType.PERSON
                for et in EntityType:
                    if et.value == entity_type_str:
                        entity_type = et
                        break

                entity = Entity(
                    canonical_name=raw.get("text", raw.get("canonical_name", "Unknown")),
                    entity_type=entity_type,
                    roles=[raw.get("role", "unknown")],
                    confidence=float(raw.get("confidence", 0.8))
                )
                entities.append(entity)

                # Also add to resolution engine
                self.entity_engine.add_entity(entity)

            except Exception as e:
                logger.warning(f"Failed to process entity: {e}")
                continue

        return entities

    async def generate_arguments(
        self,
        claims: List[Claim],
        case_id: str,
        finding_type: str = "welfare"
    ) -> List[ToulminArgument]:
        """
        Generate Toulmin arguments from claims.

        Args:
            claims: List of claims to build arguments from
            case_id: Case identifier
            finding_type: Type of finding (welfare, threshold, credibility, etc.)

        Returns:
            List of ToulminArguments
        """
        # Group claims by high certainty
        high_certainty = [c for c in claims if c.certainty >= 0.7]

        if not high_certainty:
            return []

        # Map finding type to argument pattern
        pattern_map = {
            "welfare": ArgumentPattern.WELFARE_ASSESSMENT,
            "threshold": ArgumentPattern.THRESHOLD_SATISFIED,
            "credibility": ArgumentPattern.CREDIBILITY_FINDING,
            "expert": ArgumentPattern.EXPERT_OPINION,
            "bias": ArgumentPattern.BIAS_FINDING,
        }
        pattern = pattern_map.get(finding_type, ArgumentPattern.WELFARE_ASSESSMENT)

        # Build argument from top claims
        claim_text = f"Based on {len(high_certainty)} high-certainty claims, findings suggest {finding_type} concerns"

        argument = self.argument_engine.build_argument(
            claim_text=claim_text,
            supporting_claims=high_certainty[:5],
            pattern=pattern,
            case_id=case_id
        )

        return [argument]

    def get_bias_report(self, case_id: str, signals: List[BiasSignal]) -> dict:
        """Generate a bias report for a case."""
        return self.bias_engine.generate_bias_report(signals, case_id)

    def detect_temporal_conflicts(self, events: List[dict]) -> List[dict]:
        """Detect temporal conflicts in timeline events."""
        return self.temporal_engine.find_temporal_conflicts(events)
