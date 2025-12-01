#!/usr/bin/env python3
"""
FCIP API Server - Serves REAL data from the database.
Every endpoint returns actual evidence, not mock data.
"""

import http.server
import socketserver
import json
import sqlite3
import os
import re
from urllib.parse import urlparse, parse_qs
from pathlib import Path

PORT = 9000
DB_PATH = 'Phronesis/data/db/phronesis.db'


class APIHandler(http.server.BaseHTTPRequestHandler):
    
    def send_json(self, data, status=200):
        response = json.dumps(data, indent=2, default=str, ensure_ascii=False)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def get_db(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        try:
            if path == '/api/stats':
                self.send_json(self.get_stats())
            elif path == '/api/claims':
                self.send_json(self.get_claims(params))
            elif path == '/api/claims/search':
                self.send_json(self.search_claims(params))
            elif path == '/api/documents':
                self.send_json(self.get_documents(params))
            elif path == '/api/document':
                self.send_json(self.get_document(params))
            elif path == '/api/breaches':
                self.send_json(self.get_breaches(params))
            elif path == '/api/breach/evidence':
                self.send_json(self.get_breach_evidence(params))
            elif path == '/api/contradictions':
                self.send_json(self.get_contradictions(params))
            elif path == '/api/entities':
                self.send_json(self.get_entities())
            elif path == '/api/timeline':
                self.send_json(self.get_timeline())
            elif path == '/api/person':
                self.send_json(self.get_person_claims(params))
            else:
                self.send_json({'error': 'Unknown endpoint', 'path': path}, 404)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)
    
    def get_stats(self):
        """Get overall statistics."""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        docs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM claims")
        claims = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM entities")
        entities = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cases")
        cases = cursor.fetchone()[0]
        
        # Document breakdown
        cursor.execute("""
            SELECT document_category, COUNT(*) as cnt 
            FROM documents 
            GROUP BY document_category 
            ORDER BY cnt DESC
        """)
        doc_breakdown = {row[0] or 'unknown': row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'documents': docs,
            'claims': claims,
            'entities': entities,
            'cases': cases,
            'document_breakdown': doc_breakdown
        }
    
    def get_claims(self, params):
        """Get claims with optional filtering."""
        conn = self.get_db()
        cursor = conn.cursor()
        
        limit = int(params.get('limit', ['50'])[0])
        offset = int(params.get('offset', ['0'])[0])
        doc_type = params.get('doc_type', [None])[0]
        
        if doc_type:
            cursor.execute("""
                SELECT c.id, c.claim_text, c.asserted_by, c.modality, c.certainty,
                       d.filename, d.document_category, d.title
                FROM claims c
                LEFT JOIN documents d ON c.document_id = d.id
                WHERE d.document_category = ?
                ORDER BY c.created_at DESC
                LIMIT ? OFFSET ?
            """, (doc_type, limit, offset))
        else:
            cursor.execute("""
                SELECT c.id, c.claim_text, c.asserted_by, c.modality, c.certainty,
                       d.filename, d.document_category, d.title
                FROM claims c
                LEFT JOIN documents d ON c.document_id = d.id
                ORDER BY c.created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
        
        claims = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {'claims': claims, 'count': len(claims)}
    
    def search_claims(self, params):
        """Search claims by keyword."""
        conn = self.get_db()
        cursor = conn.cursor()
        
        query = params.get('q', [''])[0].lower()
        limit = int(params.get('limit', ['30'])[0])
        
        if not query:
            return {'error': 'No query provided', 'claims': []}
        
        # Search in claim text
        cursor.execute("""
            SELECT c.id, c.claim_text, c.asserted_by, c.modality,
                   d.filename, d.document_category, d.title
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE LOWER(c.claim_text) LIKE ?
            LIMIT ?
        """, (f'%{query}%', limit))
        
        claims = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            'query': query,
            'count': len(claims),
            'claims': claims
        }
    
    def get_documents(self, params):
        """Get documents with optional filtering."""
        conn = self.get_db()
        cursor = conn.cursor()
        
        limit = int(params.get('limit', ['50'])[0])
        category = params.get('category', [None])[0]
        
        if category:
            cursor.execute("""
                SELECT id, title, filename, document_category, word_count, created_at
                FROM documents
                WHERE document_category = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (category, limit))
        else:
            cursor.execute("""
                SELECT id, title, filename, document_category, word_count, created_at
                FROM documents
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        
        docs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {'documents': docs, 'count': len(docs)}
    
    def get_document(self, params):
        """Get a single document with its claims."""
        conn = self.get_db()
        cursor = conn.cursor()
        
        doc_id = params.get('id', [None])[0]
        if not doc_id:
            return {'error': 'No document ID provided'}
        
        cursor.execute("""
            SELECT id, title, filename, raw_text, document_category, word_count
            FROM documents WHERE id = ?
        """, (doc_id,))
        
        doc = cursor.fetchone()
        if not doc:
            return {'error': 'Document not found'}
        
        doc_dict = dict(doc)
        
        # Get claims from this document
        cursor.execute("""
            SELECT id, claim_text, asserted_by, modality, certainty
            FROM claims WHERE document_id = ?
        """, (doc_id,))
        
        doc_dict['claims'] = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return doc_dict
    
    def get_breaches(self, params):
        """Get accountability breaches from audit report."""
        report_path = Path('data/accountability_audit_report.json')
        
        if not report_path.exists():
            return {'error': 'Audit report not found'}
        
        with open(report_path, encoding='utf-8') as f:
            report = json.load(f)
        
        agency = params.get('agency', [None])[0]
        
        if agency:
            agency_data = report.get('agency_results', {}).get(agency.lower(), {})
            return {
                'agency': agency,
                'breaches': agency_data.get('breaches', []),
                'count': len(agency_data.get('breaches', []))
            }
        
        return report
    
    def get_breach_evidence(self, params):
        """Get actual evidence for a specific breach."""
        conn = self.get_db()
        cursor = conn.cursor()
        
        indicator = params.get('indicator', [''])[0].lower()
        agency = params.get('agency', [''])[0].lower()
        limit = int(params.get('limit', ['20'])[0])
        
        if not indicator:
            return {'error': 'No indicator provided', 'evidence': []}
        
        # Search for claims matching this breach indicator
        cursor.execute("""
            SELECT c.claim_text, c.asserted_by, d.filename, d.document_category, d.title
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE LOWER(c.claim_text) LIKE ?
            LIMIT ?
        """, (f'%{indicator}%', limit))
        
        evidence = []
        for row in cursor.fetchall():
            evidence.append({
                'quote': row[0],
                'author': row[1],
                'document': row[2] or row[4],
                'category': row[3]
            })
        
        conn.close()
        
        return {
            'indicator': indicator,
            'agency': agency,
            'count': len(evidence),
            'evidence': evidence
        }
    
    def get_contradictions(self, params):
        """Get TRUE contradictions and source consistency analysis."""
        # Load the true contradictions report
        true_path = Path('data/TRUE_CONTRADICTIONS_REPORT.json')
        source_path = Path('data/SOURCE_CONSISTENCY_REPORT.json')
        
        result = {
            'true_contradictions': [],
            'source_consistency': [],
            'summary': {}
        }
        
        if true_path.exists():
            with open(true_path, encoding='utf-8') as f:
                true_report = json.load(f)
                result['true_contradictions'] = true_report.get('contradictions', [])
                result['summary'] = true_report.get('summary', {})
        
        if source_path.exists():
            with open(source_path, encoding='utf-8') as f:
                source_report = json.load(f)
                result['source_consistency'] = source_report.get('details', [])
        
        return result
    
    def get_entities(self):
        """Get all entities."""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM entities")
        entities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Also load network data if available
        network_path = Path('data/analysis/entity_network.json')
        network = {}
        if network_path.exists():
            with open(network_path, encoding='utf-8') as f:
                network = json.load(f)
        
        return {
            'entities': entities,
            'network': network
        }
    
    def get_timeline(self):
        """Get timeline events."""
        timeline_path = Path('data/analysis/cross_reference_timeline.json')
        
        if timeline_path.exists():
            with open(timeline_path, encoding='utf-8') as f:
                return json.load(f)
        
        return []
    
    def get_person_claims(self, params):
        """Get all claims by or about a person."""
        conn = self.get_db()
        cursor = conn.cursor()
        
        name = params.get('name', [''])[0].lower()
        limit = int(params.get('limit', ['50'])[0])
        
        if not name:
            return {'error': 'No name provided'}
        
        # Claims by this person
        cursor.execute("""
            SELECT c.claim_text, c.asserted_by, d.filename, d.document_category
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE LOWER(c.asserted_by) LIKE ?
            LIMIT ?
        """, (f'%{name}%', limit))
        
        authored = [dict(row) for row in cursor.fetchall()]
        
        # Claims about this person
        cursor.execute("""
            SELECT c.claim_text, c.asserted_by, d.filename, d.document_category
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE LOWER(c.claim_text) LIKE ? AND (c.asserted_by IS NULL OR LOWER(c.asserted_by) NOT LIKE ?)
            LIMIT ?
        """, (f'%{name}%', f'%{name}%', limit))
        
        about = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'name': name,
            'claims_authored': authored,
            'claims_about': about,
            'authored_count': len(authored),
            'about_count': len(about)
        }


def main():
    print("="*60)
    print("FCIP API SERVER - Serving REAL Data")
    print("="*60)
    print(f"\n🔌 API running on http://localhost:{PORT}")
    print("\nEndpoints:")
    print("  /api/stats              - Overall statistics")
    print("  /api/claims             - Get claims (?limit=50&doc_type=...)")
    print("  /api/claims/search      - Search claims (?q=keyword)")
    print("  /api/documents          - Get documents")
    print("  /api/document           - Get single document (?id=...)")
    print("  /api/breaches           - Get breaches (?agency=police)")
    print("  /api/breach/evidence    - Get evidence (?indicator=...)")
    print("  /api/contradictions     - Get contradictions (?type=...)")
    print("  /api/entities           - Get entities")
    print("  /api/timeline           - Get timeline")
    print("  /api/person             - Get person's claims (?name=...)")
    print("\nPress Ctrl+C to stop.\n")
    
    with socketserver.TCPServer(("", PORT), APIHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nAPI server stopped.")


if __name__ == "__main__":
    main()

