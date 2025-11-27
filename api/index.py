"""
Phronesis LEX - Vercel Serverless API
Self-contained for serverless deployment
"""
import os
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncpg

# Environment
DATABASE_URL = os.getenv("DATABASE_URL", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
IS_VERCEL = os.getenv("VERCEL", "0") == "1"

app = FastAPI(
    title="Phronesis LEX API",
    description="Forensic Legal Investigation Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create database connection pool"""
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise HTTPException(status_code=503, detail="DATABASE_URL not configured")
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return _pool


async def fetch_all(query: str, *args) -> List[Dict]:
    """Fetch all rows"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]


async def fetch_one(query: str, *args) -> Optional[Dict]:
    """Fetch single row"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def execute(query: str, *args):
    """Execute query"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


# ============================================================================
# Health & Root
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
async def health():
    db_status = "configured" if DATABASE_URL else "not configured"
    ai_status = bool(ANTHROPIC_API_KEY)

    # Test database connection
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "ai_configured": ai_status,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Cases
# ============================================================================

@app.get("/api/cases")
async def list_cases():
    try:
        cases = await fetch_all("SELECT * FROM cases ORDER BY created_at DESC LIMIT 100")
        return {"cases": cases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cases")
async def create_case(
    reference: str = Form(...),
    title: Optional[str] = Form(None),
    court: Optional[str] = Form(None),
    case_type: str = Form("family")
):
    case_id = str(uuid.uuid4())
    try:
        await execute(
            """INSERT INTO cases (id, reference, title, court, case_type, status)
               VALUES ($1, $2, $3, $4, $5, 'active')""",
            uuid.UUID(case_id), reference, title or f"Case {reference}", court, case_type
        )
        return {"id": case_id, "reference": reference}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cases/{case_id}")
async def get_case(case_id: str):
    try:
        case = await fetch_one("SELECT * FROM cases WHERE id = $1", uuid.UUID(case_id))
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Get counts
        docs = await fetch_one(
            "SELECT COUNT(*) as count FROM documents WHERE case_id = $1", uuid.UUID(case_id)
        )
        claims = await fetch_one(
            "SELECT COUNT(*) as count FROM claims WHERE case_id = $1", uuid.UUID(case_id)
        )

        return {
            **{k: str(v) if isinstance(v, uuid.UUID) else v for k, v in case.items()},
            "stats": {
                "documents": docs["count"] if docs else 0,
                "claims": claims["count"] if claims else 0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Documents
# ============================================================================

@app.get("/api/cases/{case_id}/documents")
async def list_documents(case_id: str):
    try:
        docs = await fetch_all(
            """SELECT id, filename, folder, doc_type, word_count, page_count, processed_at
               FROM documents WHERE case_id = $1 ORDER BY processed_at DESC""",
            uuid.UUID(case_id)
        )
        return {"documents": [{k: str(v) if isinstance(v, uuid.UUID) else v for k, v in d.items()} for d in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Claims
# ============================================================================

@app.get("/api/cases/{case_id}/claims")
async def list_claims(case_id: str):
    try:
        claims = await fetch_all(
            """SELECT * FROM claims WHERE case_id = $1 ORDER BY created_at DESC""",
            uuid.UUID(case_id)
        )
        return {"claims": [{k: str(v) if isinstance(v, uuid.UUID) else v for k, v in c.items()} for c in claims]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Timeline
# ============================================================================

@app.get("/api/cases/{case_id}/timeline")
async def get_timeline(case_id: str):
    try:
        events = await fetch_all(
            """SELECT * FROM timeline_events WHERE case_id = $1 ORDER BY event_date ASC""",
            uuid.UUID(case_id)
        )
        return {"events": [{k: str(v) if isinstance(v, uuid.UUID) else v for k, v in e.items()} for e in events]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Biases
# ============================================================================

@app.get("/api/cases/{case_id}/biases")
async def list_biases(case_id: str):
    try:
        biases = await fetch_all(
            """SELECT * FROM bias_indicators WHERE case_id = $1 ORDER BY created_at DESC""",
            uuid.UUID(case_id)
        )
        return {"biases": [{k: str(v) if isinstance(v, uuid.UUID) else v for k, v in b.items()} for b in biases]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Vercel Handler
# ============================================================================

# For Vercel serverless
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    handler = None
