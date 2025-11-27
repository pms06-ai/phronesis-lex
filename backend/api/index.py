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
# Professionals
# ============================================================================

@app.get("/api/cases/{case_id}/professionals")
async def list_professionals(case_id: str):
    try:
        professionals = await fetch_all(
            """SELECT p.*, pc.capacity, pc.party_represented
               FROM professionals p
               JOIN professional_capacities pc ON p.id = pc.professional_id
               WHERE pc.case_id = $1
               ORDER BY p.name""",
            uuid.UUID(case_id)
        )
        return {"professionals": [{k: str(v) if isinstance(v, uuid.UUID) else v for k, v in p.items()} for p in professionals]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/professionals")
async def create_professional(
    name: str = Form(...),
    profession: str = Form(...),
    case_id: Optional[str] = Form(None),
    capacity: Optional[str] = Form(None)
):
    prof_id = str(uuid.uuid4())
    try:
        # Insert professional
        await execute(
            """INSERT INTO professionals (id, name, normalized_name, profession)
               VALUES ($1, $2, $3, $4)""",
            uuid.UUID(prof_id), name, name.lower().strip(), profession
        )

        # Link to case if provided
        if case_id and capacity:
            cap_id = str(uuid.uuid4())
            await execute(
                """INSERT INTO professional_capacities (id, case_id, professional_id, capacity)
                   VALUES ($1, $2, $3, $4)""",
                uuid.UUID(cap_id), uuid.UUID(case_id), uuid.UUID(prof_id), capacity
            )

        return {"id": prof_id, "name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Document Details
# ============================================================================

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str, include_text: bool = False):
    try:
        if include_text:
            doc = await fetch_one("SELECT * FROM documents WHERE id = $1", uuid.UUID(doc_id))
        else:
            doc = await fetch_one(
                """SELECT id, case_id, filename, folder, doc_type, word_count, page_count,
                   processed_at, ocr_quality, file_hash FROM documents WHERE id = $1""",
                uuid.UUID(doc_id)
            )

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        return {k: str(v) if isinstance(v, uuid.UUID) else v for k, v in doc.items()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{doc_id}/text")
async def get_document_text(doc_id: str):
    try:
        doc = await fetch_one(
            "SELECT full_text, word_count FROM documents WHERE id = $1",
            uuid.UUID(doc_id)
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "text": doc["full_text"],
            "word_count": doc["word_count"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AI Analysis Endpoints
# ============================================================================

@app.post("/api/documents/{doc_id}/analyze")
async def analyze_document(doc_id: str):
    """Analyze document using Claude AI"""
    try:
        # Get document
        doc = await fetch_one(
            "SELECT id, case_id, full_text, filename, doc_type FROM documents WHERE id = $1",
            uuid.UUID(doc_id)
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if not ANTHROPIC_API_KEY:
            raise HTTPException(status_code=503, detail="AI service not configured")

        # Initialize Anthropic client
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Build analysis prompt
        prompt = f"""Analyze this legal document and extract structured information in JSON format.

Document: {doc['filename']}
Type: {doc['doc_type'] or 'unknown'}

Text:
{doc['full_text'][:50000]}

Provide a JSON response with:
{{
    "summary": "Brief executive summary",
    "key_points": ["list of key points"],
    "claims": [
        {{
            "claim_text": "the claim",
            "claim_type": "assertion|allegation|finding|order",
            "claimant": "who made it",
            "confidence": 0.0-1.0
        }}
    ],
    "entities": [
        {{
            "entity_type": "person|organization|date|location|case_law",
            "text": "entity text",
            "context": "surrounding context"
        }}
    ],
    "timeline_events": [
        {{
            "date": "YYYY-MM-DD or description",
            "event": "what happened",
            "significance": "why it matters"
        }}
    ]
}}"""

        # Call Claude
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        result_text = response.content[0].text

        # Try to extract JSON
        import re
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {"summary": result_text}

        # Store analysis results
        analysis_id = str(uuid.uuid4())
        await execute(
            """INSERT INTO analysis_runs (id, document_id, case_id, analysis_type, result_data, created_at)
               VALUES ($1, $2, $3, 'comprehensive', $4, $5)""",
            uuid.UUID(analysis_id),
            uuid.UUID(doc_id),
            uuid.UUID(str(doc['case_id'])),
            json.dumps(result),
            datetime.now()
        )

        # Store extracted claims
        for claim in result.get("claims", []):
            claim_id = str(uuid.uuid4())
            await execute(
                """INSERT INTO claims (id, case_id, document_id, claim_text, claim_type,
                   claimant, confidence, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                uuid.UUID(claim_id),
                uuid.UUID(str(doc['case_id'])),
                uuid.UUID(doc_id),
                claim.get("claim_text", ""),
                claim.get("claim_type", "assertion"),
                claim.get("claimant"),
                claim.get("confidence", 0.8),
                datetime.now()
            )

        return {
            "analysis_id": analysis_id,
            "summary": result.get("summary"),
            "claims_extracted": len(result.get("claims", [])),
            "entities_extracted": len(result.get("entities", [])),
            "timeline_events": len(result.get("timeline_events", [])),
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/{doc_id}/detect-biases")
async def detect_biases(doc_id: str):
    """Detect cognitive biases in document using Claude AI"""
    try:
        # Get document
        doc = await fetch_one(
            "SELECT id, case_id, full_text, filename FROM documents WHERE id = $1",
            uuid.UUID(doc_id)
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if not ANTHROPIC_API_KEY:
            raise HTTPException(status_code=503, detail="AI service not configured")

        # Initialize Anthropic client
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Build bias detection prompt
        prompt = f"""Analyze this legal document for cognitive biases and logical fallacies.

Document: {doc['filename']}

Text:
{doc['full_text'][:50000]}

Identify cognitive biases in JSON format:
{{
    "biases": [
        {{
            "bias_type": "confirmation_bias|anchoring_bias|availability_bias|outcome_bias|hindsight_bias|authority_bias",
            "description": "what bias was detected",
            "evidence": "quote from text showing the bias",
            "severity": "low|medium|high",
            "confidence": 0.0-1.0
        }}
    ]
}}"""

        # Call Claude
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        result_text = response.content[0].text

        # Try to extract JSON
        import re
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {"biases": []}

        # Store bias indicators
        for bias in result.get("biases", []):
            bias_id = str(uuid.uuid4())
            await execute(
                """INSERT INTO bias_indicators (id, case_id, document_id, bias_type,
                   description, evidence_quote, severity, confidence, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                uuid.UUID(bias_id),
                uuid.UUID(str(doc['case_id'])),
                uuid.UUID(doc_id),
                bias.get("bias_type", "other"),
                bias.get("description", ""),
                bias.get("evidence", ""),
                bias.get("severity", "medium"),
                bias.get("confidence", 0.7),
                datetime.now()
            )

        return {
            "biases_detected": len(result.get("biases", [])),
            "biases": result.get("biases", [])
        }

    except HTTPException:
        raise
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
