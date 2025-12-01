"""
Prompt Generator for Phronesis LEX

Generates ready-to-use prompts for AI subscription platforms.
Optimized for copy-paste workflow with Claude, ChatGPT, Grok, Perplexity, etc.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import uuid
import json

from .templates import PromptTemplates, PromptType


class GeneratedPrompt(BaseModel):
    """A generated prompt ready for copy-paste."""
    id: str
    prompt_type: str
    created_at: str
    case_id: Optional[str] = None

    # The actual prompt content
    system_context: str
    prompt_content: str
    full_prompt: str  # Combined for easy copy-paste

    # Metadata for tracking
    input_summary: Dict[str, Any]
    expected_output_format: str
    estimated_tokens: int

    # Platform recommendations
    recommended_platforms: List[str]
    notes: str


class PromptGenerator:
    """
    Generate optimized prompts for AI subscription platforms.

    Usage:
        generator = PromptGenerator()
        prompt = generator.generate_claim_extraction(document_text, case_id)
        # Copy prompt.full_prompt to your AI platform
        # Paste AI response into ResponseParser
    """

    # Estimated tokens per character (rough approximation)
    TOKENS_PER_CHAR = 0.25

    # Platform recommendations based on task type
    PLATFORM_RECOMMENDATIONS = {
        PromptType.CLAIM_EXTRACTION: ["Claude", "ChatGPT", "Grok"],
        PromptType.DOCUMENT_SUMMARY: ["Claude", "ChatGPT", "Perplexity"],
        PromptType.CLAIM_ANALYSIS: ["Claude", "ChatGPT"],
        PromptType.CREDIBILITY_ASSESSMENT: ["Claude", "ChatGPT"],
        PromptType.CONTRADICTION_ANALYSIS: ["Claude", "ChatGPT"],
        PromptType.TIMELINE_EXTRACTION: ["Claude", "ChatGPT", "Grok"],
        PromptType.EVIDENCE_EVALUATION: ["Claude", "ChatGPT"],
        PromptType.LEGAL_FRAMEWORK: ["Claude", "ChatGPT", "Perplexity"],
    }

    def _create_prompt(
        self,
        prompt_type: PromptType,
        template_vars: Dict[str, Any],
        case_id: Optional[str] = None,
        include_system_context: bool = True
    ) -> GeneratedPrompt:
        """Create a GeneratedPrompt from template and variables."""

        template = PromptTemplates.get_template(prompt_type)
        prompt_content = template.format(**template_vars)

        # Combine system context and prompt
        if include_system_context:
            full_prompt = f"{PromptTemplates.SYSTEM_CONTEXT}\n\n{prompt_content}"
        else:
            full_prompt = prompt_content

        # Estimate tokens
        estimated_tokens = int(len(full_prompt) * self.TOKENS_PER_CHAR)

        return GeneratedPrompt(
            id=str(uuid.uuid4()),
            prompt_type=prompt_type.value,
            created_at=datetime.utcnow().isoformat(),
            case_id=case_id,
            system_context=PromptTemplates.SYSTEM_CONTEXT if include_system_context else "",
            prompt_content=prompt_content,
            full_prompt=full_prompt,
            input_summary=self._summarize_inputs(template_vars),
            expected_output_format="JSON",
            estimated_tokens=estimated_tokens,
            recommended_platforms=self.PLATFORM_RECOMMENDATIONS.get(prompt_type, ["Claude", "ChatGPT"]),
            notes=self._get_notes(prompt_type, estimated_tokens)
        )

    def _summarize_inputs(self, template_vars: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of inputs for tracking."""
        summary = {}
        for key, value in template_vars.items():
            if isinstance(value, str):
                summary[key] = f"{len(value)} characters"
            elif isinstance(value, list):
                summary[key] = f"{len(value)} items"
            else:
                summary[key] = str(type(value).__name__)
        return summary

    def _get_notes(self, prompt_type: PromptType, estimated_tokens: int) -> str:
        """Generate helpful notes for the user."""
        notes = []

        # Token warnings
        if estimated_tokens > 100000:
            notes.append("⚠️ Very large prompt - consider splitting document into sections")
        elif estimated_tokens > 50000:
            notes.append("📝 Large prompt - ensure your AI platform supports this context length")

        # Task-specific notes
        task_notes = {
            PromptType.CLAIM_EXTRACTION: "Review extracted claims for accuracy before importing",
            PromptType.CREDIBILITY_ASSESSMENT: "Remember: This is analytical support, not a definitive judgment",
            PromptType.CONTRADICTION_ANALYSIS: "Consider applying Lucas Direction to apparent contradictions",
            PromptType.LEGAL_FRAMEWORK: "Verify case citations independently",
        }

        if prompt_type in task_notes:
            notes.append(task_notes[prompt_type])

        return " | ".join(notes) if notes else "Ready for processing"

    # ==================== Specific Prompt Generators ====================

    def generate_claim_extraction(
        self,
        document_text: str,
        case_id: Optional[str] = None
    ) -> GeneratedPrompt:
        """
        Generate prompt to extract claims from a document.

        Args:
            document_text: The full text of the document
            case_id: Optional case reference

        Returns:
            GeneratedPrompt ready for copy-paste
        """
        return self._create_prompt(
            PromptType.CLAIM_EXTRACTION,
            {"document_text": document_text},
            case_id
        )

    def generate_document_summary(
        self,
        document_text: str,
        case_id: Optional[str] = None
    ) -> GeneratedPrompt:
        """Generate prompt to summarize a document."""
        return self._create_prompt(
            PromptType.DOCUMENT_SUMMARY,
            {"document_text": document_text},
            case_id
        )

    def generate_claim_analysis(
        self,
        claim_text: str,
        document_name: str,
        claimant: str,
        context: str = "",
        case_id: Optional[str] = None
    ) -> GeneratedPrompt:
        """Generate prompt to analyze a specific claim."""
        return self._create_prompt(
            PromptType.CLAIM_ANALYSIS,
            {
                "claim_text": claim_text,
                "document_name": document_name,
                "claimant": claimant,
                "context": context or "No additional context provided"
            },
            case_id
        )

    def generate_credibility_assessment(
        self,
        document_text: str,
        author: str,
        document_type: str,
        case_id: Optional[str] = None
    ) -> GeneratedPrompt:
        """Generate prompt for credibility assessment."""
        return self._create_prompt(
            PromptType.CREDIBILITY_ASSESSMENT,
            {
                "document_text": document_text,
                "author": author,
                "document_type": document_type
            },
            case_id
        )

    def generate_contradiction_analysis(
        self,
        claim_a: Dict[str, str],
        claim_b: Dict[str, str],
        case_id: Optional[str] = None
    ) -> GeneratedPrompt:
        """
        Generate prompt to analyze contradiction between two claims.

        Args:
            claim_a: Dict with keys: text, source, author, date
            claim_b: Dict with keys: text, source, author, date
        """
        return self._create_prompt(
            PromptType.CONTRADICTION_ANALYSIS,
            {
                "claim_a_text": claim_a.get("text", ""),
                "claim_a_source": claim_a.get("source", "Unknown"),
                "claim_a_author": claim_a.get("author", "Unknown"),
                "claim_a_date": claim_a.get("date", "Unknown"),
                "claim_b_text": claim_b.get("text", ""),
                "claim_b_source": claim_b.get("source", "Unknown"),
                "claim_b_author": claim_b.get("author", "Unknown"),
                "claim_b_date": claim_b.get("date", "Unknown"),
            },
            case_id
        )

    def generate_timeline_extraction(
        self,
        documents: List[Dict[str, str]],
        case_id: Optional[str] = None
    ) -> GeneratedPrompt:
        """
        Generate prompt to extract timeline from multiple documents.

        Args:
            documents: List of dicts with keys: name, text
        """
        # Format documents for the prompt
        formatted_docs = []
        for i, doc in enumerate(documents, 1):
            formatted_docs.append(f"### Document {i}: {doc.get('name', 'Unnamed')}\n```\n{doc.get('text', '')}\n```")

        return self._create_prompt(
            PromptType.TIMELINE_EXTRACTION,
            {"documents": "\n\n".join(formatted_docs)},
            case_id
        )

    def generate_evidence_evaluation(
        self,
        claim_text: str,
        evidence_list: List[Dict[str, str]],
        case_id: Optional[str] = None
    ) -> GeneratedPrompt:
        """
        Generate prompt to evaluate evidence for a claim.

        Args:
            claim_text: The claim being evaluated
            evidence_list: List of dicts with keys: description, source, type
        """
        # Format evidence list
        formatted_evidence = []
        for i, ev in enumerate(evidence_list, 1):
            formatted_evidence.append(
                f"{i}. **{ev.get('type', 'Evidence')}** from {ev.get('source', 'Unknown')}:\n"
                f"   {ev.get('description', '')}"
            )

        return self._create_prompt(
            PromptType.EVIDENCE_EVALUATION,
            {
                "claim_text": claim_text,
                "evidence_list": "\n".join(formatted_evidence)
            },
            case_id
        )

    def generate_legal_framework(
        self,
        situation: str,
        claims: List[str],
        case_id: Optional[str] = None
    ) -> GeneratedPrompt:
        """Generate prompt for legal framework analysis."""
        formatted_claims = "\n".join([f"- {claim}" for claim in claims])

        return self._create_prompt(
            PromptType.LEGAL_FRAMEWORK,
            {
                "situation": situation,
                "claims": formatted_claims
            },
            case_id
        )

    # ==================== Batch Processing ====================

    def generate_batch_claim_extraction(
        self,
        documents: List[Dict[str, str]],
        case_id: Optional[str] = None,
        max_chars_per_prompt: int = 50000
    ) -> List[GeneratedPrompt]:
        """
        Generate multiple prompts for batch document processing.

        If documents are too large, they'll be split across multiple prompts.

        Args:
            documents: List of dicts with keys: name, text
            case_id: Optional case reference
            max_chars_per_prompt: Maximum characters per prompt

        Returns:
            List of GeneratedPrompts
        """
        prompts = []

        for doc in documents:
            text = doc.get("text", "")
            name = doc.get("name", "Unnamed Document")

            if len(text) <= max_chars_per_prompt:
                # Document fits in one prompt
                prompt = self.generate_claim_extraction(text, case_id)
                prompt.notes = f"Document: {name} | {prompt.notes}"
                prompts.append(prompt)
            else:
                # Split document into chunks
                chunks = self._split_text(text, max_chars_per_prompt)
                for i, chunk in enumerate(chunks, 1):
                    prompt = self.generate_claim_extraction(chunk, case_id)
                    prompt.notes = f"Document: {name} (Part {i}/{len(chunks)}) | {prompt.notes}"
                    prompts.append(prompt)

        return prompts

    def _split_text(self, text: str, max_chars: int) -> List[str]:
        """Split text into chunks, trying to break at paragraph boundaries."""
        if len(text) <= max_chars:
            return [text]

        chunks = []
        current_chunk = ""

        # Split by paragraphs first
        paragraphs = text.split("\n\n")

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # If single paragraph is too long, split by sentences
                if len(para) > max_chars:
                    sentences = para.replace(". ", ".|").split("|")
                    current_chunk = ""
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) <= max_chars:
                            current_chunk += sentence
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sentence
                else:
                    current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    # ==================== Utilities ====================

    def list_prompt_types(self) -> Dict[str, str]:
        """List all available prompt types with descriptions."""
        return PromptTemplates.list_templates()

    def estimate_processing_time(self, prompts: List[GeneratedPrompt]) -> Dict[str, Any]:
        """
        Estimate time needed to process prompts manually.

        Assumes ~2 minutes per prompt for copy-paste workflow.
        """
        total_prompts = len(prompts)
        total_tokens = sum(p.estimated_tokens for p in prompts)

        return {
            "total_prompts": total_prompts,
            "total_estimated_tokens": total_tokens,
            "estimated_minutes": total_prompts * 2,  # ~2 min per prompt
            "recommendation": self._get_batch_recommendation(total_prompts)
        }

    def _get_batch_recommendation(self, num_prompts: int) -> str:
        """Get recommendation for batch processing."""
        if num_prompts <= 3:
            return "Quick processing - can be done in one session"
        elif num_prompts <= 10:
            return "Moderate batch - consider processing over 2-3 sessions"
        else:
            return "Large batch - recommend processing incrementally with breaks"
