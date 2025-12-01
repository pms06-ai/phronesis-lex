"""
Model Router for Phronesis LEX
Intelligent task routing between Gemini (document analysis) and Claude (reasoning).

Architecture:
- Gemini Pro: Document analysis, entity extraction, claims, timeline, bias detection
- Claude: Cross-document synthesis, contradiction analysis, evidence chains, hypothesis generation
"""
import json
from typing import Optional, Dict, Any, List, Literal
from enum import Enum
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import GOOGLE_API_KEY, ANTHROPIC_API_KEY


class TaskType(Enum):
    """Analysis task types routed to different models."""
    # Gemini tasks (document-level, extraction)
    DOCUMENT_ANALYSIS = "document_analysis"
    ENTITY_EXTRACTION = "entity_extraction"
    CLAIMS_EXTRACTION = "claims_extraction"
    TIMELINE_EXTRACTION = "timeline_extraction"
    BIAS_DETECTION = "bias_detection"
    BATCH_DOCUMENT_ANALYSIS = "batch_document_analysis"
    
    # Claude tasks (reasoning, cross-document)
    CROSS_DOC_SYNTHESIS = "cross_doc_synthesis"
    CONTRADICTION_DETECTION = "contradiction_detection"
    EVIDENCE_CHAIN_ANALYSIS = "evidence_chain_analysis"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    COMPETING_CLAIMS_ANALYSIS = "competing_claims_analysis"
    EXECUTIVE_SUMMARY = "executive_summary"


@dataclass
class TaskResult:
    """Result from a routed task."""
    success: bool
    data: Dict[str, Any]
    model_used: str
    task_type: TaskType
    error: Optional[str] = None


# Task routing configuration
GEMINI_TASKS = {
    TaskType.DOCUMENT_ANALYSIS,
    TaskType.ENTITY_EXTRACTION,
    TaskType.CLAIMS_EXTRACTION,
    TaskType.TIMELINE_EXTRACTION,
    TaskType.BIAS_DETECTION,
    TaskType.BATCH_DOCUMENT_ANALYSIS,
}

CLAUDE_TASKS = {
    TaskType.CROSS_DOC_SYNTHESIS,
    TaskType.CONTRADICTION_DETECTION,
    TaskType.EVIDENCE_CHAIN_ANALYSIS,
    TaskType.HYPOTHESIS_GENERATION,
    TaskType.COMPETING_CLAIMS_ANALYSIS,
    TaskType.EXECUTIVE_SUMMARY,
}


class ModelRouter:
    """
    Routes analysis tasks to the appropriate LLM.
    
    Gemini Pro: Large context window, good for bulk document processing
    Claude: Superior reasoning, good for synthesis and complex logic
    """
    
    def __init__(self):
        self._gemini_service = None
        self._claude_service = None
        self.usage_stats = {
            "gemini": {"calls": 0, "tasks": []},
            "claude": {"calls": 0, "tasks": []}
        }
    
    @property
    def gemini(self):
        """Lazy load Gemini service."""
        if self._gemini_service is None:
            if not GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not configured")
            from .gemini_service import GeminiService
            self._gemini_service = GeminiService()
        return self._gemini_service
    
    @property
    def claude(self):
        """Lazy load Claude service."""
        if self._claude_service is None:
            if not ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            from .claude_service import ClaudeService
            self._claude_service = ClaudeService()
        return self._claude_service
    
    def get_model_for_task(self, task: TaskType) -> Literal["gemini", "claude"]:
        """Determine which model should handle a task."""
        if task in GEMINI_TASKS:
            return "gemini"
        elif task in CLAUDE_TASKS:
            return "claude"
        else:
            # Default to Claude for unknown tasks (better reasoning)
            return "claude"
    
    async def route(self, task: TaskType, **kwargs) -> TaskResult:
        """
        Route a task to the appropriate model and execute it.
        
        Args:
            task: The type of task to execute
            **kwargs: Task-specific arguments
            
        Returns:
            TaskResult with the outcome
        """
        model = self.get_model_for_task(task)
        
        try:
            if model == "gemini":
                result = await self._execute_gemini_task(task, **kwargs)
            else:
                result = await self._execute_claude_task(task, **kwargs)
            
            # Track usage
            self.usage_stats[model]["calls"] += 1
            self.usage_stats[model]["tasks"].append(task.value)
            
            return TaskResult(
                success=True,
                data=result,
                model_used=model,
                task_type=task
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                data={},
                model_used=model,
                task_type=task,
                error=str(e)
            )
    
    async def _execute_gemini_task(self, task: TaskType, **kwargs) -> Dict[str, Any]:
        """Execute a task using Gemini."""
        if task == TaskType.DOCUMENT_ANALYSIS:
            return await self.gemini.analyze_document(
                document_text=kwargs["document_text"],
                case_context=kwargs.get("case_context"),
                doc_type=kwargs.get("doc_type")
            )
        
        elif task == TaskType.ENTITY_EXTRACTION:
            entities = await self.gemini.extract_entities(
                document_text=kwargs["document_text"],
                doc_type=kwargs.get("doc_type")
            )
            return {"entities": entities}
        
        elif task == TaskType.CLAIMS_EXTRACTION:
            claims = await self.gemini.extract_claims(
                document_text=kwargs["document_text"],
                professional_context=kwargs.get("professional_context")
            )
            return {"claims": claims}
        
        elif task == TaskType.TIMELINE_EXTRACTION:
            events = await self.gemini.extract_timeline(
                document_text=kwargs["document_text"],
                existing_events=kwargs.get("existing_events")
            )
            return {"events": events}
        
        elif task == TaskType.BIAS_DETECTION:
            biases = await self.gemini.detect_biases(
                text=kwargs["text"],
                professional=kwargs.get("professional"),
                capacity=kwargs.get("capacity")
            )
            return {"biases": biases}
        
        elif task == TaskType.BATCH_DOCUMENT_ANALYSIS:
            return await self.gemini.analyze_documents_batch(
                documents=kwargs["documents"],
                case_context=kwargs.get("case_context")
            )
        
        else:
            raise ValueError(f"Unknown Gemini task: {task}")
    
    async def _execute_claude_task(self, task: TaskType, **kwargs) -> Dict[str, Any]:
        """Execute a task using Claude."""
        if task == TaskType.CONTRADICTION_DETECTION:
            # Use FCIP contradiction engine instead of non-existent Claude method
            from fcip.engines.contradiction import detect_contradictions_from_db
            claims = kwargs.get("claims", [])
            case_id = kwargs.get("case_id", "")
            report = detect_contradictions_from_db(claims, case_id)
            return {
                "contradictions": [
                    {
                        "id": str(c.contradiction_id),
                        "type": c.contradiction_type.value,
                        "severity": c.severity.value,
                        "description": c.description,
                        "claim_a": c.claim_a_text,
                        "claim_b": c.claim_b_text,
                        "confidence": c.confidence
                    }
                    for c in report.contradictions
                ],
                "total": report.total_contradictions,
                "self_contradictions": len(report.self_contradictions)
            }
        
        elif task == TaskType.COMPETING_CLAIMS_ANALYSIS:
            return await self.claude.analyze_competing_claims(
                claim_a=kwargs["claim_a"],
                claim_b=kwargs["claim_b"]
            )
        
        elif task == TaskType.EXECUTIVE_SUMMARY:
            summary = await self.claude.generate_executive_summary(
                case_data=kwargs["case_data"]
            )
            return {"summary": summary}
        
        elif task == TaskType.CROSS_DOC_SYNTHESIS:
            return await self._synthesize_across_documents(**kwargs)
        
        elif task == TaskType.EVIDENCE_CHAIN_ANALYSIS:
            return await self._analyze_evidence_chain(**kwargs)
        
        elif task == TaskType.HYPOTHESIS_GENERATION:
            return await self._generate_hypotheses(**kwargs)
        
        else:
            raise ValueError(f"Unknown Claude task: {task}")
    
    async def _synthesize_across_documents(
        self,
        all_claims: List[Dict],
        all_entities: List[Dict],
        timeline: List[Dict],
        case_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesize findings across multiple documents.
        Claude's strength: connecting dots, finding patterns.
        """
        prompt = f"""Synthesize these findings from multiple case documents.

CASE CONTEXT: {case_context or 'Not provided'}

CLAIMS EXTRACTED ({len(all_claims)} total):
{json.dumps(all_claims[:50], indent=2)}

ENTITIES FOUND ({len(all_entities)} total):
{json.dumps(all_entities[:30], indent=2)}

TIMELINE ({len(timeline)} events):
{json.dumps(timeline[:30], indent=2)}

Analyze and return JSON:
{{
  "narrative_summary": "synthesized narrative of what happened",
  "key_findings": [
    {{
      "finding": "what you found",
      "evidence": ["supporting claims/events"],
      "confidence": 0.0-1.0,
      "significance": "critical|important|routine"
    }}
  ],
  "entity_patterns": [
    {{
      "entity": "name",
      "pattern": "observed pattern across documents",
      "documents_involved": ["list"]
    }}
  ],
  "timeline_gaps": ["periods with missing information"],
  "inconsistencies": [
    {{
      "description": "what's inconsistent",
      "sources": ["where the inconsistency appears"]
    }}
  ],
  "recommended_focus_areas": ["areas needing deeper investigation"]
}}"""

        response = self.claude.client.messages.create(
            model=self.claude.model,
            max_tokens=self.claude.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self.claude._parse_json_response(response.content[0].text)
    
    async def _analyze_evidence_chain(
        self,
        claim: Dict,
        available_evidence: List[Dict]
    ) -> Dict[str, Any]:
        """
        Trace the evidence chain for a claim.
        Claude's strength: logical chain reasoning.
        """
        prompt = f"""Trace the evidence chain for this claim.

CLAIM TO ANALYZE:
{json.dumps(claim, indent=2)}

AVAILABLE EVIDENCE:
{json.dumps(available_evidence[:30], indent=2)}

Return JSON:
{{
  "claim": "the claim being analyzed",
  "evidence_chain": [
    {{
      "level": 1,
      "evidence": "what supports this",
      "source": "where it comes from",
      "strength": "strong|moderate|weak"
    }}
  ],
  "chain_issues": [
    {{
      "issue_type": "circular|hearsay|missing_link|assumption",
      "description": "what's wrong",
      "severity": "high|medium|low"
    }}
  ],
  "ultimate_sources": ["primary sources at end of chain"],
  "overall_strength": "strong|moderate|weak|broken",
  "recommendations": ["how to strengthen"]
}}"""

        response = self.claude.client.messages.create(
            model=self.claude.model,
            max_tokens=self.claude.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self.claude._parse_json_response(response.content[0].text)
    
    async def _generate_hypotheses(
        self,
        claims: List[Dict],
        entities: List[Dict],
        issues: List[Dict],
        case_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate investigative hypotheses based on case data.
        Claude's strength: creative reasoning, hypothesis formation.
        """
        prompt = f"""Based on this case data, generate investigative hypotheses.

CASE CONTEXT: {case_context or 'Not provided'}

KEY CLAIMS:
{json.dumps(claims[:30], indent=2)}

KEY ENTITIES:
{json.dumps(entities[:20], indent=2)}

DETECTED ISSUES:
{json.dumps(issues[:20], indent=2)}

Generate and return JSON:
{{
  "hypotheses": [
    {{
      "hypothesis": "what might be true",
      "type": "misconduct|bias|procedural_failure|factual_error|coordination",
      "supporting_evidence": ["evidence that supports this"],
      "contradicting_evidence": ["evidence against"],
      "confidence": 0.0-1.0,
      "test_by": "how to verify or refute this hypothesis",
      "if_true_implications": "what it would mean if true"
    }}
  ],
  "evidence_gaps": [
    {{
      "gap": "what information is missing",
      "why_important": "why it matters",
      "how_to_obtain": "suggested approach"
    }}
  ],
  "recommended_next_steps": [
    {{
      "action": "what to do",
      "priority": "high|medium|low",
      "rationale": "why"
    }}
  ]
}}"""

        response = self.claude.client.messages.create(
            model=self.claude.model,
            max_tokens=self.claude.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self.claude._parse_json_response(response.content[0].text)
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Get usage statistics for both models."""
        return {
            "gemini": self.usage_stats["gemini"],
            "claude": self.usage_stats["claude"],
            "total_calls": (
                self.usage_stats["gemini"]["calls"] + 
                self.usage_stats["claude"]["calls"]
            )
        }
    
    def get_available_tasks(self) -> Dict[str, List[str]]:
        """List available tasks by model."""
        return {
            "gemini_tasks": [t.value for t in GEMINI_TASKS],
            "claude_tasks": [t.value for t in CLAUDE_TASKS]
        }


# Singleton instance
_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get or create model router instance."""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router

