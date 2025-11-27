"""
Phronesis LEX - Vercel Serverless API
Simple handler format for Vercel
"""
from http.server import BaseHTTPRequestHandler
import json
import os


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        path = self.path

        if path == '/health' or path == '/api/health':
            response = {
                "status": "healthy",
                "database_url_set": bool(os.getenv("DATABASE_URL")),
                "anthropic_key_set": bool(os.getenv("ANTHROPIC_API_KEY")),
                "vercel": os.getenv("VERCEL", "0")
            }
        elif path == '/' or path == '/api':
            response = {
                "service": "Phronesis LEX API",
                "status": "operational",
                "version": "1.0.0"
            }
        elif path == '/api/cases':
            response = {"cases": [], "message": "Connect to Supabase"}
        else:
            response = {"path": path, "message": "Phronesis API"}

        self.wfile.write(json.dumps(response).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
