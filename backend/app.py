"""
Phronesis LEX Backend API
FastAPI server for the Forensic Legal Investigation Platform
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List
import uuid
import shutil
from datetime import datetime

import logging

from config import HOST, PORT, DEBUG, CORS_ORIGINS, UPLOADS_DIR, ANTHROPIC_API_KEY
from db.connection import db, get_db, Database
from services.document_processor import get_document_processor, DocumentProcessor
from services.claude_service import get_claude_service, ClaudeService

# FCIP Engine imports
from fcip.services.analysis_service import FCIPAnalysisService, AnalysisResult
from fcip.engines.entity_resolution import EntityResolutionEngine, EntityRoster
from fcip.engines.argumentation import ArgumentationEngine, ArgumentPattern, LEGAL_RULES
from fcip.engines.bias import BiasDetectionEngine
from fcip.engines.temporal import TemporalParser

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    logger.info("Initializing Phronesis LEX Backend...")
    await db.initialize()
    logger.info(f"Database ready at {db.db_path}")
    logger.info(f"API Key configured: {'Yes' if ANTHROPIC_API_KEY else 'No'}")

    yield

    # Shutdown
    await db.disconnect()
    logger.info("Phronesis LEX Backend shutdown complete.")


app = FastAPI(
    title="Phronesis LEX API",
    description="Forensic Legal Investigation Platform - Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root - health check."""
    return {
        "service": "Phronesis LEX API",
        "status": "operational",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    processor = get_document_processor()
    return {
        "status": "healthy",
        "database": "connected",
        "ai_configured": bool(ANTHROPIC_API_KEY),
        "processing_capabilities": processor.get_capabilities(),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Cases Endpoints
# ============================================================================

@app.get("/api/cases")
async def list_cases():
    """List all cases."""
    cases = await db.fetch_all("SELECT * FROM cases ORDER BY created_at DESC")
    return {"cases": cases}


@app.post("/api/cases")
async def create_case(
    reference: str = Form(...),
    title: Optional[str] = Form(None),
    court: Optional[str] = Form(None),
    case_type: str = Form("family")
):
    """Create a new case."""
    case_id = str(uuid.uuid4())

    await db.insert("cases", {
        "id": case_id,
        "reference": reference,
        "title": title or f"Case {reference}",
        "court": court,
        "case_type": case_type,
        "status": "active"
    })

    return {"id": case_id, "reference": reference, "message": "Case created successfully"}


@app.get("/api/cases/{case_id}")
async def get_case(case_id: str):
    """Get case details with summary statistics."""
    case = await db.fetch_one("SELECT * FROM cases WHERE id = ?", (case_id,))
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Get related counts
    docs = await db.fetch_one(
        "SELECT COUNT(*) as count FROM documents WHERE case_id = ?", (case_id,)
    )
    claims = await db.fetch_one(
        "SELECT COUNT(*) as count FROM claims WHERE case_id = ?", (case_id,)
    )
    events = await db.fetch_one(
        "SELECT COUNT(*) as count FROM timeline_events WHERE case_id = ?", (case_id,)
    )
    biases = await db.fetch_one(
        "SELECT COUNT(*) as count FROM bias_indicators WHERE case_id = ?", (case_id,)
    )

    return {
        **case,
        "stats": {
            "documents": docs["count"] if docs else 0,
            "claims": claims["count"] if claims else 0,
            "timeline_events": events["count"] if events else 0,
            "bias_indicators": biases["count"] if biases else 0
        }
    }


# ============================================================================
# Documents Endpoints
# ============================================================================

@app.get("/api/cases/{case_id}/documents")
async def list_documents(case_id: str):
    """List all documents for a case."""
    docs = await db.fetch_all(
        """SELECT id, filename, folder, doc_type, word_count, page_count,
                  processed_at, ocr_quality
           FROM documents WHERE case_id = ? ORDER BY processed_at DESC""",
        (case_id,)
    )
    return {"documents": docs}


@app.post("/api/cases/{case_id}/documents")
async def upload_document(
    case_id: str,
    file: UploadFile = File(...),
    folder: Optional[str] = Form(None),
    doc_type: Optional[str] = Form(None)
):
    """Upload and process a document."""
    # Verify case exists
    case = await db.fetch_one("SELECT id FROM cases WHERE id = ?", (case_id,))
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Save uploaded file
    case_dir = UPLOADS_DIR / case_id
    case_dir.mkdir(exist_ok=True)

    file_path = case_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process document
    processor = get_document_processor()
    result = await processor.process_document(file_path)

    if result["errors"]:
        return JSONResponse(
            status_code=422,
            content={"errors": result["errors"], "partial_result": result}
        )

    # Store in database
    doc_id = result["id"]
    await db.insert("documents", {
        "id": doc_id,
        "case_id": case_id,
        "filename": result["filename"],
        "original_path": result["original_path"],
        "folder": folder,
        "doc_type": doc_type,
        "full_text": result["full_text"],
        "word_count": result["word_count"],
        "page_count": result["page_count"],
        "processed_at": result["processed_at"],
        "ocr_quality": result["ocr_quality"],
        "file_hash": result["file_hash"]
    })

    return {
        "id": doc_id,
        "filename": result["filename"],
        "word_count": result["word_count"],
        "page_count": result["page_count"],
        "message": "Document uploaded and processed successfully"
    }


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str, include_text: bool = False):
    """Get document details."""
    columns = "*" if include_text else """
        id, case_id, filename, folder, doc_type, word_count, page_count,
        processed_at, ocr_quality, file_hash
    """
    doc = await db.fetch_one(f"SELECT {columns} FROM documents WHERE id = ?", (doc_id,))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.get("/api/documents/{doc_id}/text")
async def get_document_text(doc_id: str):
    """Get full text of a document."""
    doc = await db.fetch_one(
        "SELECT full_text, word_count FROM documents WHERE id = ?", (doc_id,)
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"text": doc["full_text"], "word_count": doc["word_count"]}


# ============================================================================
# Analysis Endpoints
# ============================================================================

@app.post("/api/documents/{doc_id}/analyze")
async def analyze_document(doc_id: str):
    """Run Claude AI analysis on a document."""
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="AI analysis not configured - missing API key")

    doc = await db.fetch_one(
        "SELECT id, case_id, full_text, doc_type, filename FROM documents WHERE id = ?",
        (doc_id,)
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc["full_text"]:
        raise HTTPException(status_code=422, detail="Document has no extracted text")

    # Create analysis run record
    run_id = str(uuid.uuid4())
    await db.insert("analysis_runs", {
        "id": run_id,
        "case_id": doc["case_id"],
        "run_type": "document",
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "model_used": "claude-sonnet-4-20250514"
    })

    try:
        claude = get_claude_service()

        # Get case context
        case = await db.fetch_one(
            "SELECT reference, title, court FROM cases WHERE id = ?",
            (doc["case_id"],)
        )
        context = f"Case: {case['reference']} - {case['title']}" if case else None

        # Run analysis
        analysis = await claude.analyze_document(
            doc["full_text"],
            case_context=context,
            doc_type=doc["doc_type"]
        )

        # Store extracted claims
        claims_stored = 0
        for claim in analysis.get("claims", []):
            await db.insert("claims", {
                "id": str(uuid.uuid4()),
                "case_id": doc["case_id"],
                "document_id": doc_id,
                "claim_type": claim.get("claim_type"),
                "claim_text": claim.get("claim_text"),
                "claimant_capacity": claim.get("claimant"),
                "target_entity": claim.get("target"),
                "context": claim.get("page_paragraph"),
                "ai_extracted": True,
                "ai_confidence": claim.get("confidence")
            })
            claims_stored += 1

        # Store timeline events
        events_stored = 0
        for event in analysis.get("timeline_events", []):
            await db.insert("timeline_events", {
                "id": str(uuid.uuid4()),
                "case_id": doc["case_id"],
                "event_date": event.get("date"),
                "event_type": event.get("event_type"),
                "description": event.get("description"),
                "source_document_id": doc_id,
                "significance": event.get("significance")
            })
            events_stored += 1

        # Store potential issues as bias indicators
        biases_stored = 0
        for issue in analysis.get("potential_issues", []):
            if issue.get("issue_type") == "bias_indicator":
                await db.insert("bias_indicators", {
                    "id": str(uuid.uuid4()),
                    "case_id": doc["case_id"],
                    "document_id": doc_id,
                    "bias_type": "other",
                    "evidence_text": issue.get("quote", issue.get("description")),
                    "context": issue.get("description"),
                    "severity": issue.get("severity"),
                    "ai_confidence": 0.7
                })
                biases_stored += 1

        # Update analysis run
        usage = claude.get_usage_stats()
        await db.update("analysis_runs", run_id, {
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "documents_analyzed": 1,
            "claims_extracted": claims_stored,
            "biases_detected": biases_stored,
            "total_tokens": usage["total_tokens"]
        })

        return {
            "run_id": run_id,
            "status": "completed",
            "results": {
                "claims_extracted": claims_stored,
                "events_extracted": events_stored,
                "issues_detected": len(analysis.get("potential_issues", [])),
                "entities_found": len(analysis.get("entities", []))
            },
            "analysis": analysis
        }

    except Exception as e:
        await db.update("analysis_runs", run_id, {
            "status": "failed",
            "error_message": str(e),
            "completed_at": datetime.now().isoformat()
        })
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/documents/{doc_id}/detect-biases")
async def detect_document_biases(doc_id: str):
    """Run bias detection on a document."""
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="AI analysis not configured")

    doc = await db.fetch_one(
        "SELECT id, case_id, full_text FROM documents WHERE id = ?",
        (doc_id,)
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    claude = get_claude_service()
    biases = await claude.detect_biases(doc["full_text"])

    # Store detected biases
    stored = 0
    for bias in biases:
        await db.insert("bias_indicators", {
            "id": str(uuid.uuid4()),
            "case_id": doc["case_id"],
            "document_id": doc_id,
            "bias_type": bias.get("bias_type"),
            "evidence_text": bias.get("evidence_text"),
            "context": bias.get("context"),
            "severity": bias.get("severity"),
            "ai_confidence": bias.get("confidence"),
            "ai_reasoning": bias.get("explanation")
        })
        stored += 1

    return {"biases_detected": stored, "biases": biases}


# ============================================================================
# Claims Endpoints
# ============================================================================

@app.get("/api/cases/{case_id}/claims")
async def list_claims(case_id: str, claim_type: Optional[str] = None):
    """List all claims for a case."""
    query = """SELECT c.*, d.filename as source_document
               FROM claims c
               LEFT JOIN documents d ON c.document_id = d.id
               WHERE c.case_id = ?"""
    params = [case_id]

    if claim_type:
        query += " AND c.claim_type = ?"
        params.append(claim_type)

    query += " ORDER BY c.created_at DESC"

    claims = await db.fetch_all(query, tuple(params))
    return {"claims": claims}


# ============================================================================
# Timeline Endpoints
# ============================================================================

@app.get("/api/cases/{case_id}/timeline")
async def get_timeline(case_id: str):
    """Get chronological timeline for a case."""
    events = await db.fetch_all(
        """SELECT t.*, d.filename as source_document
           FROM timeline_events t
           LEFT JOIN documents d ON t.source_document_id = d.id
           WHERE t.case_id = ?
           ORDER BY t.event_date ASC""",
        (case_id,)
    )
    return {"events": events}


# ============================================================================
# Bias Indicators Endpoints
# ============================================================================

@app.get("/api/cases/{case_id}/biases")
async def list_biases(case_id: str):
    """List all detected bias indicators for a case."""
    biases = await db.fetch_all(
        """SELECT b.*, d.filename as source_document, p.name as professional_name
           FROM bias_indicators b
           LEFT JOIN documents d ON b.document_id = d.id
           LEFT JOIN professionals p ON b.professional_id = p.id
           WHERE b.case_id = ?
           ORDER BY
               CASE b.severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
               b.created_at DESC""",
        (case_id,)
    )
    return {"biases": biases}


# ============================================================================
# Professionals Endpoints
# ============================================================================

@app.get("/api/cases/{case_id}/professionals")
async def list_case_professionals(case_id: str):
    """List all professionals involved in a case."""
    professionals = await db.fetch_all(
        """SELECT p.*, pc.capacity, pc.party_represented
           FROM professionals p
           JOIN professional_capacities pc ON p.id = pc.professional_id
           WHERE pc.case_id = ?
           ORDER BY p.name""",
        (case_id,)
    )
    return {"professionals": professionals}


@app.post("/api/professionals")
async def create_professional(
    name: str = Form(...),
    profession: str = Form(...),
    registration_body: Optional[str] = Form(None),
    registration_number: Optional[str] = Form(None)
):
    """Create a new professional record."""
    prof_id = str(uuid.uuid4())
    normalized = name.lower().strip()

    await db.insert("professionals", {
        "id": prof_id,
        "name": name,
        "normalized_name": normalized,
        "profession": profession,
        "registration_body": registration_body,
        "registration_number": registration_number
    })

    return {"id": prof_id, "name": name}


# ============================================================================
# FCIP Analysis Endpoints
# ============================================================================

# Initialize FCIP service
_fcip_service = None


def get_fcip_service() -> FCIPAnalysisService:
    """Get or create FCIP analysis service singleton."""
    global _fcip_service
    if _fcip_service is None:
        _fcip_service = FCIPAnalysisService(anthropic_api_key=ANTHROPIC_API_KEY)
    return _fcip_service


@app.post("/api/fcip/analyze/{doc_id}")
async def fcip_analyze_document(doc_id: str):
    """
    Run full FCIP analysis on a document.

    This replaces the basic Claude analysis with comprehensive forensic analysis:
    - Epistemic claim extraction (modality, certainty, attribution)
    - Entity resolution with fuzzy matching
    - Temporal parsing and deadline detection
    - Statistical bias detection (z-scores)
    - Toulmin argument generation
    """
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="AI analysis not configured - missing API key")

    doc = await db.fetch_one(
        "SELECT id, case_id, full_text, doc_type, filename FROM documents WHERE id = ?",
        (doc_id,)
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc["full_text"]:
        raise HTTPException(status_code=422, detail="Document has no extracted text")

    # Get case professionals for entity seeding
    professionals = await db.fetch_all(
        """SELECT p.id, p.name, p.profession, p.normalized_name
           FROM professionals p
           JOIN professional_capacities pc ON p.id = pc.professional_id
           WHERE pc.case_id = ?""",
        (doc["case_id"],)
    )

    # Run FCIP analysis
    fcip = get_fcip_service()
    result = await fcip.analyze_document(
        document_id=doc_id,
        text=doc["full_text"],
        case_id=doc["case_id"],
        doc_type=doc["doc_type"],
        professionals=list(professionals)
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {result.error}")

    # Store extracted claims with FCIP metadata
    claims_stored = 0
    for claim in result.claims:
        await db.insert("claims", {
            "id": str(claim.claim_id),
            "case_id": doc["case_id"],
            "document_id": doc_id,
            "claim_type": claim.claim_type.value,
            "claim_text": claim.text,
            "target_entity": claim.subject,
            "context": claim.source_quote,
            "ai_extracted": True,
            "ai_confidence": claim.certainty,
            "modality": claim.modality.value,
            "polarity": claim.polarity.value,
            "certainty": claim.certainty,
            "certainty_markers": str(claim.certainty_markers),
            "asserted_by": claim.asserted_by,
            "time_expression": claim.time_expression,
            "extraction_prompt_hash": result.extraction_prompt_hash,
            "extractor_model": "fcip_v5"
        })
        claims_stored += 1

    # Store bias signals
    biases_stored = 0
    for signal in result.bias_signals:
        await db.insert("bias_indicators", {
            "id": str(signal.signal_id),
            "case_id": doc["case_id"],
            "document_id": doc_id,
            "bias_type": signal.signal_type,
            "evidence_text": signal.description,
            "severity": signal.severity.value,
            "ai_confidence": abs(signal.z_score) / 3.0,  # Normalize z-score to confidence
            "z_score": signal.z_score,
            "p_value": signal.p_value,
            "baseline_mean": signal.baseline_mean,
            "baseline_std": signal.baseline_std,
            "baseline_id": signal.baseline_id,
            "direction": signal.direction
        })
        biases_stored += 1

    # Store timeline events
    events_stored = 0
    for event in result.timeline_events:
        await db.insert("timeline_events", {
            "id": str(uuid.uuid4()),
            "case_id": doc["case_id"],
            "event_date": event.get("date"),
            "event_type": "other",
            "description": event.get("expression", ""),
            "source_document_id": doc_id,
            "significance": "routine"
        })
        events_stored += 1

    return {
        "status": "completed",
        "doc_type": result.doc_type,
        "doc_type_confidence": result.doc_type_confidence,
        "results": {
            "claims_extracted": claims_stored,
            "entities_found": len(result.entities),
            "timeline_events": events_stored,
            "bias_signals": biases_stored
        },
        "extraction_prompt_hash": result.extraction_prompt_hash
    }


@app.get("/api/cases/{case_id}/entity-graph")
async def get_entity_graph(case_id: str):
    """Get resolved entity graph for a case."""
    # Get all professionals for the case
    professionals = await db.fetch_all(
        """SELECT p.id, p.name, p.normalized_name, p.profession,
                  pc.capacity, pc.party_represented
           FROM professionals p
           JOIN professional_capacities pc ON p.id = pc.professional_id
           WHERE pc.case_id = ?""",
        (case_id,)
    )

    # Get entity aliases
    aliases = await db.fetch_all(
        """SELECT ea.* FROM entity_aliases ea
           JOIN professionals p ON ea.professional_id = p.id
           JOIN professional_capacities pc ON p.id = pc.professional_id
           WHERE pc.case_id = ?""",
        (case_id,)
    )

    # Build entity roster
    engine = EntityResolutionEngine()
    for prof in professionals:
        engine.seed_from_professionals([dict(prof)])

    nodes = []
    for prof in professionals:
        nodes.append({
            "id": prof["id"],
            "name": prof["name"],
            "profession": prof["profession"],
            "capacity": prof["capacity"],
            "party": prof["party_represented"],
            "aliases": [a["alias_text"] for a in aliases if a["professional_id"] == prof["id"]]
        })

    return {
        "case_id": case_id,
        "nodes": nodes,
        "total_entities": len(nodes),
        "total_aliases": len(aliases)
    }


@app.get("/api/cases/{case_id}/bias-report")
async def get_bias_report(case_id: str):
    """Get comprehensive statistical bias report for a case."""
    biases = await db.fetch_all(
        """SELECT * FROM bias_indicators WHERE case_id = ?
           ORDER BY ABS(z_score) DESC NULLS LAST""",
        (case_id,)
    )

    # Calculate summary statistics
    z_scores = [b["z_score"] for b in biases if b.get("z_score") is not None]

    report = {
        "case_id": case_id,
        "total_signals": len(biases),
        "by_severity": {
            "high": len([b for b in biases if b.get("severity") == "high"]),
            "medium": len([b for b in biases if b.get("severity") == "medium"]),
            "low": len([b for b in biases if b.get("severity") == "low"]),
        },
        "by_type": {},
        "statistical_summary": {
            "mean_z_score": sum(z_scores) / len(z_scores) if z_scores else None,
            "max_z_score": max(z_scores) if z_scores else None,
            "signals_above_critical": len([z for z in z_scores if abs(z) >= 2.0]),
            "signals_above_warning": len([z for z in z_scores if abs(z) >= 1.5]),
        },
        "signals": [
            {
                "id": b["id"],
                "type": b["bias_type"],
                "severity": b["severity"],
                "z_score": b.get("z_score"),
                "p_value": b.get("p_value"),
                "direction": b.get("direction"),
                "description": b["evidence_text"],
                "document_id": b["document_id"]
            }
            for b in biases
        ]
    }

    # Count by type
    for b in biases:
        btype = b["bias_type"] or "other"
        report["by_type"][btype] = report["by_type"].get(btype, 0) + 1

    return report


@app.get("/api/cases/{case_id}/arguments")
async def list_arguments(case_id: str):
    """List all Toulmin arguments for a case."""
    arguments = await db.fetch_all(
        "SELECT * FROM arguments WHERE case_id = ? ORDER BY created_at DESC",
        (case_id,)
    )
    return {"arguments": arguments}


@app.post("/api/cases/{case_id}/generate-arguments")
async def generate_arguments(case_id: str, finding_type: str = "welfare"):
    """Generate Toulmin arguments from case claims."""
    # Get high-confidence claims
    claims = await db.fetch_all(
        """SELECT * FROM claims WHERE case_id = ?
           AND (certainty >= 0.7 OR ai_confidence >= 0.7)
           ORDER BY certainty DESC LIMIT 50""",
        (case_id,)
    )

    if not claims:
        return {"arguments": [], "message": "No high-confidence claims found"}

    # Use argumentation engine
    engine = ArgumentationEngine()

    # Map finding type to pattern
    pattern_map = {
        "welfare": ArgumentPattern.WELFARE_ASSESSMENT,
        "threshold": ArgumentPattern.THRESHOLD_SATISFIED,
        "credibility": ArgumentPattern.CREDIBILITY_FINDING,
        "expert": ArgumentPattern.EXPERT_OPINION,
        "bias": ArgumentPattern.BIAS_FINDING,
    }
    pattern = pattern_map.get(finding_type, ArgumentPattern.WELFARE_ASSESSMENT)

    # Build arguments from claims
    # This is a simplified version - the full engine would do more
    from fcip.models.core import Claim as FCIPClaim, ClaimType, Modality, Polarity, Confidence

    fcip_claims = []
    for c in claims[:5]:
        try:
            fcip_claims.append(FCIPClaim(
                document_id=uuid.UUID(c["document_id"]) if c["document_id"] else uuid.uuid4(),
                case_id=case_id,
                text=c["claim_text"],
                claim_type=ClaimType.ASSERTION,
                modality=Modality.ASSERTED,
                polarity=Polarity.AFFIRM,
                certainty=c.get("certainty", c.get("ai_confidence", 0.5)),
                confidence=Confidence.llm_extracted(c.get("certainty", 0.5), "claude")
            ))
        except Exception:
            continue

    if not fcip_claims:
        return {"arguments": [], "message": "Could not process claims"}

    argument = engine.build_argument(
        claim_text=f"Based on analysis of {len(claims)} claims regarding {finding_type}",
        supporting_claims=fcip_claims,
        pattern=pattern,
        case_id=case_id
    )

    # Store argument
    arg_id = str(argument.argument_id)
    await db.insert("arguments", {
        "id": arg_id,
        "case_id": case_id,
        "claim_text": argument.claim_text,
        "grounds": str(argument.grounds),
        "warrant": argument.warrant,
        "warrant_rule_id": argument.warrant_rule_id,
        "backing": str(argument.backing),
        "qualifier": argument.qualifier,
        "rebuttal": str(argument.rebuttal),
        "falsifiability_conditions": str(argument.falsifiability_conditions),
        "missing_evidence": str(argument.missing_evidence),
        "alternative_explanations": str(argument.alternative_explanations),
        "confidence_lower": argument.confidence_lower,
        "confidence_upper": argument.confidence_upper,
        "confidence_mean": argument.confidence_mean
    })

    return {
        "argument_id": arg_id,
        "argument": {
            "claim": argument.claim_text,
            "grounds": argument.grounds,
            "warrant": argument.warrant,
            "warrant_rule_id": argument.warrant_rule_id,
            "backing": argument.backing,
            "qualifier": argument.qualifier,
            "rebuttal": argument.rebuttal,
            "falsifiability_conditions": argument.falsifiability_conditions,
            "confidence_bounds": {
                "lower": argument.confidence_lower,
                "mean": argument.confidence_mean,
                "upper": argument.confidence_upper
            }
        }
    }


@app.get("/api/cases/{case_id}/deadline-alerts")
async def get_deadline_alerts(case_id: str):
    """Get deadline alerts for a case."""
    alerts = await db.fetch_all(
        """SELECT * FROM deadline_alerts WHERE case_id = ?
           ORDER BY deadline_date ASC NULLS LAST""",
        (case_id,)
    )
    return {"alerts": alerts}


@app.get("/api/legal-rules")
async def list_legal_rules(category: Optional[str] = None):
    """List legal rules from the FCIP library."""
    rules = await db.fetch_all("SELECT * FROM legal_rules")

    if not rules:
        # Return from in-memory library if DB empty
        rules_list = []
        for rule_id, rule in LEGAL_RULES.items():
            if category and rule.category != category:
                continue
            rules_list.append({
                "rule_id": rule.rule_id,
                "short_name": rule.short_name,
                "full_citation": rule.full_citation,
                "text": rule.text,
                "category": rule.category
            })
        return {"rules": rules_list}

    if category:
        rules = [r for r in rules if r.get("category") == category]

    return {"rules": rules}


@app.get("/api/bias-baselines")
async def list_bias_baselines():
    """List all bias detection baselines."""
    baselines = await db.fetch_all("SELECT * FROM bias_baselines")
    return {"baselines": baselines}


@app.post("/api/bias-baselines")
async def create_baseline(
    doc_type: str = Form(...),
    metric: str = Form(...),
    mean: float = Form(...),
    std_dev: float = Form(...)
):
    """Create or update a bias baseline."""
    baseline_id = f"{doc_type}_{metric}"

    await db.execute(
        """INSERT OR REPLACE INTO bias_baselines
           (baseline_id, doc_type, metric, mean, std_dev, source)
           VALUES (?, ?, ?, ?, ?, 'calibrated')""",
        (baseline_id, doc_type, metric, mean, std_dev)
    )

    return {"baseline_id": baseline_id, "message": "Baseline saved"}


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)
