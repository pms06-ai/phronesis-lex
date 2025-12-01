"""
Phronesis LEX Backend API
FastAPI server for the Forensic Legal Investigation Platform

Features:
- JWT Authentication (can be disabled with AUTH_DISABLED=true)
- Rate limiting
- Audit logging
- FCIP analysis engines
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List
import uuid
import shutil
import os
from datetime import datetime, timedelta

import logging

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import HOST, PORT, DEBUG, CORS_ORIGINS, UPLOADS_DIR, ANTHROPIC_API_KEY
from db.connection import db, get_db, Database
from services.document_processor import get_document_processor, DocumentProcessor
from services.claude_service import get_claude_service, ClaudeService

# Authentication
from auth import (
    get_current_user, get_optional_user, User, Token, UserLogin,
    authenticate_user, create_access_token, get_password_hash
)

# Audit logging
from audit import log_audit, AuditAction, get_audit_logs, AUDIT_TABLE_SQL

# FCIP Engine imports
from fcip.services.analysis_service import FCIPAnalysisService, AnalysisResult
from fcip.engines.entity_resolution import EntityResolutionEngine, EntityRoster
from fcip.engines.argumentation import ArgumentationEngine, ArgumentPattern, LEGAL_RULES
from fcip.engines.bias import BiasDetectionEngine
from fcip.engines.temporal import TemporalParser
from fcip.engines.contradiction import ContradictionDetectionEngine, ContradictionType, LEGAL_SIGNIFICANCE
from fcip.models.core import Claim as FCIPClaim, ClaimType, Modality, Polarity, Confidence

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    logger.info("Initializing Phronesis LEX Backend...")
    await db.initialize()

    # Create audit logs table
    try:
        await db.execute_script(AUDIT_TABLE_SQL)
        logger.info("Audit logging initialized")
    except Exception as e:
        logger.warning(f"Could not initialize audit table: {e}")

    logger.info(f"Database ready at {db.db_path}")
    logger.info(f"API Key configured: {'Yes' if ANTHROPIC_API_KEY else 'No'}")
    logger.info(f"Auth disabled: {os.getenv('AUTH_DISABLED', 'false')}")

    yield

    # Shutdown
    await db.disconnect()
    logger.info("Phronesis LEX Backend shutdown complete.")


app = FastAPI(
    title="Phronesis LEX API",
    description="Forensic Legal Investigation Platform - Backend API",
    version="2.0.0",
    lifespan=lifespan
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/token", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, login_data: UserLogin):
    """
    Authenticate and get JWT token.

    For personal use, default credentials are:
    - username: admin
    - password: phronesis2024 (or value of ADMIN_PASSWORD env var)

    Set AUTH_DISABLED=true to skip authentication entirely.
    """
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        await log_audit(
            user=login_data.username,
            action=AuditAction.LOGIN,
            resource_type="auth",
            description="Failed login attempt",
            ip_address=get_client_ip(request),
            success=False,
            error="Invalid credentials"
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, expires_at = create_access_token(
        data={"sub": user.username}
    )

    await log_audit(
        user=user.username,
        action=AuditAction.LOGIN,
        resource_type="auth",
        description="Successful login",
        ip_address=get_client_ip(request),
        success=True
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at.isoformat()
    )


@app.get("/api/auth/user")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return {
        "username": current_user.username,
        "is_active": current_user.is_active
    }


@app.get("/api/audit-logs")
async def list_audit_logs(
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get audit logs (admin only)."""
    logs = await get_audit_logs(
        resource_type=resource_type,
        action=action,
        limit=limit
    )
    return {"logs": logs}


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
# Contradiction Detection Endpoints
# ============================================================================

@app.get("/api/cases/{case_id}/contradictions")
async def detect_contradictions(case_id: str, refresh: bool = False):
    """
    Detect contradictions across all claims in a case.
    
    This is the revolutionary capability: systematic cross-referencing
    of claims to find inconsistencies that would take humans hours.
    
    Args:
        case_id: The case to analyze
        refresh: If True, re-run analysis even if cached results exist
    
    Returns:
        ContradictionReport with all detected contradictions
    """
    # Verify case exists
    case = await db.fetch_one("SELECT id FROM cases WHERE id = ?", (case_id,))
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Check for cached results
    if not refresh:
        cached = await db.fetch_all(
            "SELECT * FROM contradictions WHERE case_id = ? ORDER BY severity ASC, confidence DESC",
            (case_id,)
        )
        if cached:
            return {
                "case_id": case_id,
                "source": "cached",
                "total_contradictions": len(cached),
                "contradictions": [dict(c) for c in cached]
            }
    
    # Get all claims for the case
    claims_data = await db.fetch_all(
        """SELECT c.*, d.filename as source_document
           FROM claims c
           LEFT JOIN documents d ON c.document_id = d.id
           WHERE c.case_id = ?""",
        (case_id,)
    )
    
    if not claims_data:
        return {
            "case_id": case_id,
            "source": "analysis",
            "total_contradictions": 0,
            "message": "No claims found in case",
            "contradictions": []
        }
    
    # Convert to FCIP Claim objects
    fcip_claims = []
    for c in claims_data:
        try:
            fcip_claims.append(FCIPClaim(
                claim_id=uuid.UUID(c["id"]) if c["id"] else uuid.uuid4(),
                document_id=uuid.UUID(c["document_id"]) if c["document_id"] else uuid.uuid4(),
                case_id=case_id,
                text=c["claim_text"] or "",
                claim_type=ClaimType(c["claim_type"]) if c["claim_type"] else ClaimType.ASSERTION,
                source_quote=c.get("context"),
                subject=c.get("target_entity"),
                modality=Modality(c["modality"]) if c.get("modality") else Modality.ASSERTED,
                polarity=Polarity(c["polarity"]) if c.get("polarity") else Polarity.AFFIRM,
                certainty=c.get("certainty") or c.get("ai_confidence") or 0.5,
                asserted_by=c.get("claimant_capacity"),
                time_expression=c.get("time_expression"),
                confidence=Confidence.llm_extracted(c.get("ai_confidence") or 0.5, "claude")
            ))
        except Exception as e:
            logger.warning(f"Could not convert claim {c.get('id')}: {e}")
            continue
    
    if not fcip_claims:
        return {
            "case_id": case_id,
            "source": "analysis",
            "total_contradictions": 0,
            "message": "No valid claims to analyze",
            "contradictions": []
        }
    
    # Run contradiction detection
    engine = ContradictionDetectionEngine(
        semantic_threshold=0.6,
        polarity_threshold=0.7,
        enable_semantic=True
    )
    
    report = engine.detect_contradictions(fcip_claims, case_id)
    
    # Store results in database
    for c in report.contradictions:
        try:
            await db.execute(
                """INSERT OR REPLACE INTO contradictions
                   (id, case_id, claim_a_id, claim_b_id, contradiction_type, severity,
                    claim_a_text, claim_b_text, claim_a_source, claim_b_source,
                    claim_a_author, claim_b_author, same_author,
                    semantic_similarity, confidence, explanation,
                    legal_significance, recommended_action, case_law_reference,
                    detection_method, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (
                    str(c.contradiction_id), case_id,
                    str(c.claim_a_id), str(c.claim_b_id),
                    c.contradiction_type.value, c.severity.value,
                    c.claim_a_text[:500], c.claim_b_text[:500],
                    c.claim_a_source, c.claim_b_source,
                    c.claim_a_author, c.claim_b_author, c.same_author,
                    c.semantic_similarity, c.confidence, c.explanation,
                    c.legal_significance, c.recommended_action, c.case_law_reference,
                    c.detection_method
                )
            )
        except Exception as e:
            logger.warning(f"Could not store contradiction {c.contradiction_id}: {e}")
    
    return {
        "case_id": case_id,
        "source": "analysis",
        "total_contradictions": report.total_contradictions,
        "by_type": {k.value: v for k, v in report.by_type.items()},
        "by_severity": {k.value: v for k, v in report.by_severity.items()},
        "critical_count": len(report.critical_findings),
        "self_contradiction_count": len(report.self_contradictions),
        "authors_with_self_contradictions": report.authors_with_self_contradictions,
        "documents_with_most_contradictions": report.documents_with_most_contradictions,
        "contradictions": [
            {
                "id": str(c.contradiction_id),
                "type": c.contradiction_type.value,
                "severity": c.severity.value,
                "claim_a": {
                    "id": str(c.claim_a_id),
                    "text": c.claim_a_text,
                    "source": c.claim_a_source,
                    "author": c.claim_a_author,
                    "date": c.claim_a_date
                },
                "claim_b": {
                    "id": str(c.claim_b_id),
                    "text": c.claim_b_text,
                    "source": c.claim_b_source,
                    "author": c.claim_b_author,
                    "date": c.claim_b_date
                },
                "same_author": c.same_author,
                "semantic_similarity": round(c.semantic_similarity, 3),
                "confidence": round(c.confidence, 3),
                "explanation": c.explanation,
                "legal_significance": c.legal_significance,
                "recommended_action": c.recommended_action,
                "case_law_reference": c.case_law_reference
            }
            for c in report.contradictions
        ]
    }


@app.get("/api/cases/{case_id}/contradiction-summary")
async def get_contradiction_summary(case_id: str):
    """
    Get a quick summary of contradictions for dashboard display.
    
    Returns counts and severity breakdown without full details.
    """
    # Check for cached results
    contradictions = await db.fetch_all(
        "SELECT * FROM contradictions WHERE case_id = ?",
        (case_id,)
    )
    
    if not contradictions:
        return {
            "case_id": case_id,
            "total": 0,
            "analyzed": False,
            "by_severity": {},
            "by_type": {},
            "critical_issues": []
        }
    
    # Count by severity
    by_severity = {}
    by_type = {}
    critical_issues = []
    
    for c in contradictions:
        severity = c.get("severity", "low")
        ctype = c.get("contradiction_type", "direct")
        
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_type[ctype] = by_type.get(ctype, 0) + 1
        
        if severity == "critical":
            critical_issues.append({
                "id": c["id"],
                "type": ctype,
                "explanation": c.get("explanation", "")[:100],
                "same_author": c.get("same_author", False)
            })
    
    return {
        "case_id": case_id,
        "total": len(contradictions),
        "analyzed": True,
        "by_severity": by_severity,
        "by_type": by_type,
        "critical_issues": critical_issues[:5]  # Top 5 critical
    }


@app.get("/api/contradiction-types")
async def list_contradiction_types():
    """
    List all contradiction types with their legal significance.
    
    Useful for UI explanations and help text.
    """
    return {
        "types": [
            {
                "type": ctype.value,
                "severity": sig.get("severity", "medium").value if hasattr(sig.get("severity"), "value") else sig.get("severity", "medium"),
                "case_law": sig.get("case_law", ""),
                "explanation": sig.get("explanation", ""),
                "recommended_action": sig.get("recommended_action", "")
            }
            for ctype, sig in LEGAL_SIGNIFICANCE.items()
        ]
    }


@app.post("/api/claims/compare")
async def compare_two_claims(
    claim_a_id: str = Form(...),
    claim_b_id: str = Form(...)
):
    """
    Compare two specific claims for contradiction.
    
    Useful for targeted analysis or UI interactions.
    """
    # Fetch both claims
    claim_a = await db.fetch_one("SELECT * FROM claims WHERE id = ?", (claim_a_id,))
    claim_b = await db.fetch_one("SELECT * FROM claims WHERE id = ?", (claim_b_id,))
    
    if not claim_a or not claim_b:
        raise HTTPException(status_code=404, detail="One or both claims not found")
    
    # Convert to FCIP Claims
    try:
        fcip_a = FCIPClaim(
            claim_id=uuid.UUID(claim_a["id"]),
            document_id=uuid.UUID(claim_a["document_id"]) if claim_a["document_id"] else uuid.uuid4(),
            case_id=claim_a["case_id"],
            text=claim_a["claim_text"] or "",
            claim_type=ClaimType(claim_a["claim_type"]) if claim_a["claim_type"] else ClaimType.ASSERTION,
            modality=Modality(claim_a["modality"]) if claim_a.get("modality") else Modality.ASSERTED,
            polarity=Polarity(claim_a["polarity"]) if claim_a.get("polarity") else Polarity.AFFIRM,
            certainty=claim_a.get("certainty") or claim_a.get("ai_confidence") or 0.5,
            asserted_by=claim_a.get("claimant_capacity"),
            confidence=Confidence.llm_extracted(0.5, "claude")
        )
        
        fcip_b = FCIPClaim(
            claim_id=uuid.UUID(claim_b["id"]),
            document_id=uuid.UUID(claim_b["document_id"]) if claim_b["document_id"] else uuid.uuid4(),
            case_id=claim_b["case_id"],
            text=claim_b["claim_text"] or "",
            claim_type=ClaimType(claim_b["claim_type"]) if claim_b["claim_type"] else ClaimType.ASSERTION,
            modality=Modality(claim_b["modality"]) if claim_b.get("modality") else Modality.ASSERTED,
            polarity=Polarity(claim_b["polarity"]) if claim_b.get("polarity") else Polarity.AFFIRM,
            certainty=claim_b.get("certainty") or claim_b.get("ai_confidence") or 0.5,
            asserted_by=claim_b.get("claimant_capacity"),
            confidence=Confidence.llm_extracted(0.5, "claude")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid claim data: {str(e)}")
    
    # Run comparison
    engine = ContradictionDetectionEngine()
    result = engine.compare_claims(fcip_a, fcip_b, claim_a["case_id"])
    
    if result:
        return {
            "is_contradiction": True,
            "type": result.contradiction_type.value,
            "severity": result.severity.value,
            "confidence": round(result.confidence, 3),
            "semantic_similarity": round(result.semantic_similarity, 3),
            "same_author": result.same_author,
            "explanation": result.explanation,
            "legal_significance": result.legal_significance,
            "recommended_action": result.recommended_action,
            "case_law_reference": result.case_law_reference
        }
    else:
        return {
            "is_contradiction": False,
            "message": "No contradiction detected between these claims"
        }


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)
