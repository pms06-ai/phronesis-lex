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

from config import HOST, PORT, DEBUG, CORS_ORIGINS, UPLOADS_DIR, ANTHROPIC_API_KEY
from db.connection import db, get_db, Database
from services.document_processor import get_document_processor, DocumentProcessor
from services.claude_service import get_claude_service, ClaudeService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    print("Initializing Phronesis LEX Backend...")
    await db.initialize()
    print(f"Database ready at {db.db_path}")
    print(f"API Key configured: {'Yes' if ANTHROPIC_API_KEY else 'No'}")

    yield

    # Shutdown
    await db.disconnect()
    print("Phronesis LEX Backend shutdown complete.")


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
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)
