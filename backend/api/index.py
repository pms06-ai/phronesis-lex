"""
Vercel Serverless API Handler
Wraps FastAPI app for Vercel deployment
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
from typing import Optional
import uuid
from datetime import datetime

# Import services
from services.claude_service import get_claude_service, ClaudeService
from services.document_processor import get_document_processor

# Environment detection
IS_VERCEL = os.getenv("VERCEL", "0") == "1"
DATABASE_URL = os.getenv("DATABASE_URL", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Use Supabase connection if DATABASE_URL is PostgreSQL
if DATABASE_URL.startswith("postgres"):
    from db.supabase_connection import db, get_db
else:
    from db.connection import db, get_db

# CORS origins
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8080,http://127.0.0.1:8080,https://*.vercel.app"
).split(",")

app = FastAPI(
    title="Phronesis LEX API",
    description="Forensic Legal Investigation Platform - Serverless API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Vercel handles origin restrictions
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize database connection on cold start"""
    try:
        await db.initialize()
        print("Database initialized")
    except Exception as e:
        print(f"Database initialization error: {e}")


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {
        "service": "Phronesis LEX API",
        "status": "operational",
        "version": "1.0.0",
        "deployment": "vercel" if IS_VERCEL else "local"
    }


@app.get("/health")
async def health_check():
    processor = get_document_processor()
    return {
        "status": "healthy",
        "database": "supabase" if DATABASE_URL.startswith("postgres") else "sqlite",
        "ai_configured": bool(ANTHROPIC_API_KEY),
        "processing_capabilities": processor.get_capabilities(),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Cases Endpoints
# ============================================================================

@app.get("/api/cases")
async def list_cases():
    cases = await db.fetch_all("SELECT * FROM cases ORDER BY created_at DESC")
    return {"cases": cases}


@app.post("/api/cases")
async def create_case(
    reference: str = Form(...),
    title: Optional[str] = Form(None),
    court: Optional[str] = Form(None),
    case_type: str = Form("family")
):
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
    case = await db.fetch_one("SELECT * FROM cases WHERE id = $1", case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Get related counts
    docs = await db.fetch_one(
        "SELECT COUNT(*) as count FROM documents WHERE case_id = $1", case_id
    )
    claims = await db.fetch_one(
        "SELECT COUNT(*) as count FROM claims WHERE case_id = $1", case_id
    )
    events = await db.fetch_one(
        "SELECT COUNT(*) as count FROM timeline_events WHERE case_id = $1", case_id
    )
    biases = await db.fetch_one(
        "SELECT COUNT(*) as count FROM bias_indicators WHERE case_id = $1", case_id
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
    docs = await db.fetch_all(
        """SELECT id, filename, folder, doc_type, word_count, page_count,
                  processed_at, ocr_quality
           FROM documents WHERE case_id = $1 ORDER BY processed_at DESC""",
        case_id
    )
    return {"documents": docs}


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str, include_text: bool = False):
    if include_text:
        doc = await db.fetch_one("SELECT * FROM documents WHERE id = $1", doc_id)
    else:
        doc = await db.fetch_one(
            """SELECT id, case_id, filename, folder, doc_type, word_count, page_count,
                      processed_at, ocr_quality, file_hash
               FROM documents WHERE id = $1""",
            doc_id
        )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.get("/api/documents/{doc_id}/text")
async def get_document_text(doc_id: str):
    doc = await db.fetch_one(
        "SELECT full_text, word_count FROM documents WHERE id = $1", doc_id
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"text": doc["full_text"], "word_count": doc["word_count"]}


# ============================================================================
# Analysis Endpoints
# ============================================================================

@app.post("/api/documents/{doc_id}/analyze")
async def analyze_document(doc_id: str):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="AI analysis not configured")

    doc = await db.fetch_one(
        "SELECT id, case_id, full_text, doc_type, filename FROM documents WHERE id = $1",
        doc_id
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc["full_text"]:
        raise HTTPException(status_code=422, detail="Document has no extracted text")

    # Create analysis run
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
            "SELECT reference, title, court FROM cases WHERE id = $1",
            doc["case_id"]
        )
        context = f"Case: {case['reference']} - {case['title']}" if case else None

        # Run analysis
        analysis = await claude.analyze_document(
            doc["full_text"],
            case_context=context,
            doc_type=doc["doc_type"]
        )

        # Store claims
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

        # Update analysis run
        usage = claude.get_usage_stats()
        await db.update("analysis_runs", run_id, {
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "documents_analyzed": 1,
            "claims_extracted": claims_stored,
            "total_tokens": usage["total_tokens"]
        })

        return {
            "run_id": run_id,
            "status": "completed",
            "results": {
                "claims_extracted": claims_stored,
                "events_extracted": events_stored,
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


# ============================================================================
# Claims, Timeline, Biases Endpoints
# ============================================================================

@app.get("/api/cases/{case_id}/claims")
async def list_claims(case_id: str, claim_type: Optional[str] = None):
    if claim_type:
        claims = await db.fetch_all(
            """SELECT c.*, d.filename as source_document
               FROM claims c
               LEFT JOIN documents d ON c.document_id = d.id
               WHERE c.case_id = $1 AND c.claim_type = $2
               ORDER BY c.created_at DESC""",
            case_id, claim_type
        )
    else:
        claims = await db.fetch_all(
            """SELECT c.*, d.filename as source_document
               FROM claims c
               LEFT JOIN documents d ON c.document_id = d.id
               WHERE c.case_id = $1
               ORDER BY c.created_at DESC""",
            case_id
        )
    return {"claims": claims}


@app.get("/api/cases/{case_id}/timeline")
async def get_timeline(case_id: str):
    events = await db.fetch_all(
        """SELECT t.*, d.filename as source_document
           FROM timeline_events t
           LEFT JOIN documents d ON t.source_document_id = d.id
           WHERE t.case_id = $1
           ORDER BY t.event_date ASC""",
        case_id
    )
    return {"events": events}


@app.get("/api/cases/{case_id}/biases")
async def list_biases(case_id: str):
    biases = await db.fetch_all(
        """SELECT b.*, d.filename as source_document, p.name as professional_name
           FROM bias_indicators b
           LEFT JOIN documents d ON b.document_id = d.id
           LEFT JOIN professionals p ON b.professional_id = p.id
           WHERE b.case_id = $1
           ORDER BY
               CASE b.severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
               b.created_at DESC""",
        case_id
    )
    return {"biases": biases}


# ============================================================================
# Vercel Handler
# ============================================================================

# Mangum adapter for AWS Lambda / Vercel
handler = Mangum(app, lifespan="off")
