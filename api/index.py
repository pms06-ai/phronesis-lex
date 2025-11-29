"""
Phronesis LEX - Vercel Serverless API
With Supabase PostgreSQL connection
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import asyncio
from datetime import datetime, date
from urllib.parse import urlparse, parse_qs
import uuid

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# CORS - defaults to * for development, set to specific origin in production
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "*")


def json_serial(obj):
    """JSON serializer for objects not serializable by default"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


async def db_query(query: str, *args):
    """Execute a database query and return results"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def db_query_one(query: str, *args):
    """Execute a database query and return single result"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None
    finally:
        await conn.close()


async def db_execute(query: str, *args):
    """Execute a database command"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        return await conn.execute(query, *args)
    finally:
        await conn.close()


async def test_db():
    """Test database connection"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        result = await conn.fetchval("SELECT 1")
        return True, "connected"
    except Exception as e:
        return False, str(e)[:100]
    finally:
        await conn.close()


class handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', CORS_ORIGIN)
        self.end_headers()
        self.wfile.write(json.dumps(data, default=json_serial).encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        try:
            # Health check
            if path in ['/health', '/api/health']:
                if DATABASE_URL:
                    ok, msg = asyncio.run(test_db())
                    db_status = msg
                else:
                    db_status = "not configured"

                self.send_json({
                    "status": "healthy" if db_status == "connected" else "degraded",
                    "database": db_status,
                    "ai_configured": bool(ANTHROPIC_API_KEY),
                    "timestamp": datetime.now().isoformat()
                })

            # Root
            elif path in ['/', '/api', '/api/']:
                self.send_json({
                    "service": "Phronesis LEX API",
                    "status": "operational",
                    "version": "1.0.0",
                    "endpoints": ["/health", "/api/cases", "/api/cases/{id}"]
                })

            # List cases
            elif path == '/api/cases':
                cases = asyncio.run(db_query(
                    "SELECT * FROM cases ORDER BY created_at DESC LIMIT 50"
                ))
                self.send_json({"cases": cases})

            # Get single case
            elif path.startswith('/api/cases/') and len(path.split('/')) == 4:
                case_id = path.split('/')[3]
                case = asyncio.run(db_query_one(
                    "SELECT * FROM cases WHERE id = $1",
                    uuid.UUID(case_id)
                ))
                if case:
                    # Get stats
                    docs = asyncio.run(db_query_one(
                        "SELECT COUNT(*) as count FROM documents WHERE case_id = $1",
                        uuid.UUID(case_id)
                    ))
                    claims = asyncio.run(db_query_one(
                        "SELECT COUNT(*) as count FROM claims WHERE case_id = $1",
                        uuid.UUID(case_id)
                    ))
                    case["stats"] = {
                        "documents": docs["count"] if docs else 0,
                        "claims": claims["count"] if claims else 0
                    }
                    self.send_json(case)
                else:
                    self.send_json({"error": "Case not found"}, 404)

            # Case documents
            elif '/documents' in path:
                parts = path.split('/')
                case_id = parts[3]
                docs = asyncio.run(db_query(
                    "SELECT * FROM documents WHERE case_id = $1 ORDER BY processed_at DESC",
                    uuid.UUID(case_id)
                ))
                self.send_json({"documents": docs})

            # Case claims
            elif '/claims' in path:
                parts = path.split('/')
                case_id = parts[3]
                claims = asyncio.run(db_query(
                    "SELECT * FROM claims WHERE case_id = $1 ORDER BY created_at DESC",
                    uuid.UUID(case_id)
                ))
                self.send_json({"claims": claims})

            # Case timeline
            elif '/timeline' in path:
                parts = path.split('/')
                case_id = parts[3]
                events = asyncio.run(db_query(
                    "SELECT * FROM timeline_events WHERE case_id = $1 ORDER BY event_date ASC",
                    uuid.UUID(case_id)
                ))
                self.send_json({"events": events})

            # Case biases
            elif '/biases' in path:
                parts = path.split('/')
                case_id = parts[3]
                biases = asyncio.run(db_query(
                    "SELECT * FROM bias_indicators WHERE case_id = $1 ORDER BY created_at DESC",
                    uuid.UUID(case_id)
                ))
                self.send_json({"biases": biases})

            else:
                self.send_json({"path": path, "message": "Unknown endpoint"}, 404)

        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else '{}'

        try:
            data = json.loads(body) if body else {}

            # Create case
            if path == '/api/cases':
                case_id = str(uuid.uuid4())
                reference = data.get('reference', f'CASE-{case_id[:8]}')
                title = data.get('title', f'Case {reference}')
                court = data.get('court')
                case_type = data.get('case_type', 'family')

                asyncio.run(db_execute(
                    """INSERT INTO cases (id, reference, title, court, case_type, status)
                       VALUES ($1, $2, $3, $4, $5, 'active')""",
                    uuid.UUID(case_id), reference, title, court, case_type
                ))

                self.send_json({"id": case_id, "reference": reference}, 201)

            else:
                self.send_json({"error": "Unknown endpoint"}, 404)

        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', CORS_ORIGIN)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
