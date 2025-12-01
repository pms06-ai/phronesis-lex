"""
FCIP Dashboard Server
Serves the interactive dashboard and provides API endpoints for case data.
"""

import http.server
import socketserver
import json
import sqlite3
import os
from urllib.parse import urlparse, parse_qs
from pathlib import Path

PORT = 8080
DB_PATH = 'Phronesis/data/db/phronesis.db'

class FCIPHandler(http.server.SimpleHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='.', **kwargs)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        # API Routes
        if parsed.path.startswith('/api/'):
            self.handle_api(parsed)
        # Serve dashboard
        elif parsed.path == '/' or parsed.path == '/index.html':
            self.serve_file('dashboard/index.html')
        # Serve static files
        else:
            super().do_GET()
    
    def handle_api(self, parsed):
        path = parsed.path
        
        try:
            if path == '/api/stats':
                self.send_json(self.get_stats())
            elif path == '/api/timeline':
                self.send_json(self.get_timeline())
            elif path == '/api/breaches':
                self.send_json(self.get_breaches())
            elif path == '/api/contradictions':
                self.send_json(self.get_contradictions())
            elif path == '/api/documents':
                self.send_json(self.get_documents())
            elif path == '/api/claims':
                self.send_json(self.get_claims(parse_qs(parsed.query)))
            elif path == '/api/entities':
                self.send_json(self.get_entities())
            elif path == '/api/cases':
                self.send_json(self.get_cases())
            else:
                self.send_error(404, 'API endpoint not found')
        except Exception as e:
            self.send_json({'error': str(e)}, 500)
    
    def send_json(self, data, status=200):
        response = json.dumps(data, indent=2, default=str)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def serve_file(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(200)
            if filepath.endswith('.html'):
                self.send_header('Content-Type', 'text/html')
            elif filepath.endswith('.json'):
                self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, 'File not found')
    
    def get_db(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_stats(self):
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        documents = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM claims")
        claims = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM entities")
        entities = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cases")
        cases = cursor.fetchone()[0]
        
        conn.close()
        
        # Load breach data
        breaches = 0
        contradictions = 0
        
        if os.path.exists('data/accountability_audit_report.json'):
            with open('data/accountability_audit_report.json') as f:
                audit = json.load(f)
                breaches = audit.get('total_breaches', 58)
        
        if os.path.exists('data/contradiction_report_PE23C50095.json'):
            with open('data/contradiction_report_PE23C50095.json') as f:
                contra = json.load(f)
                contradictions = contra.get('total_contradictions', 1903)
        
        return {
            'documents': documents,
            'claims': claims,
            'entities': entities,
            'cases': cases,
            'breaches': breaches,
            'contradictions': contradictions
        }
    
    def get_timeline(self):
        if os.path.exists('data/analysis/cross_reference_timeline.json'):
            with open('data/analysis/cross_reference_timeline.json') as f:
                return json.load(f)
        return []
    
    def get_breaches(self):
        if os.path.exists('data/accountability_audit_report.json'):
            with open('data/accountability_audit_report.json') as f:
                return json.load(f)
        return {}
    
    def get_contradictions(self):
        if os.path.exists('data/contradiction_report_PE23C50095.json'):
            with open('data/contradiction_report_PE23C50095.json') as f:
                return json.load(f)
        return {}
    
    def get_documents(self):
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, filename, document_category, word_count, created_at
            FROM documents
            ORDER BY created_at DESC
            LIMIT 100
        """)
        docs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return docs
    
    def get_claims(self, params):
        conn = self.get_db()
        cursor = conn.cursor()
        
        topic = params.get('topic', [None])[0]
        limit = int(params.get('limit', ['50'])[0])
        
        if topic:
            # Search claims by topic keywords
            keywords = {
                'MURDER': ['murder', 'kill', 'alderton', 'dunmore'],
                'CUSTODY': ['custody', 'care', 'placement'],
                'CREDIBILITY': ['credibility', 'lie', 'false'],
                'POLICE': ['police', 'arrest', 'investigation'],
            }
            kw_list = keywords.get(topic, [topic.lower()])
            conditions = ' OR '.join([f"claim_text LIKE '%{kw}%'" for kw in kw_list])
            cursor.execute(f"""
                SELECT id, claim_text, asserted_by, modality
                FROM claims
                WHERE {conditions}
                LIMIT ?
            """, (limit,))
        else:
            cursor.execute("""
                SELECT id, claim_text, asserted_by, modality
                FROM claims
                LIMIT ?
            """, (limit,))
        
        claims = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return claims
    
    def get_entities(self):
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entities")
        entities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return entities
    
    def get_cases(self):
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases")
        cases = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return cases


def main():
    print("="*60)
    print("FCIP - Forensic Case Intelligence Platform")
    print("="*60)
    print(f"\nStarting dashboard server on http://localhost:{PORT}")
    print("\nOpen your browser to view the interactive dashboard.")
    print("Press Ctrl+C to stop.\n")
    
    with socketserver.TCPServer(("", PORT), FCIPHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()

