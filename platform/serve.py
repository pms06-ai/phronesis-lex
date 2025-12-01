"""
Unified Platform Server
Serves the interactive evidence explorer.
"""

import http.server
import socketserver

PORT = 8888

class PlatformHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='platform', **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.serve_file('platform/interactive.html')
        else:
            super().do_GET()
    
    def serve_file(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))


def main():
    print("="*60)
    print("FCIP INTERACTIVE EVIDENCE EXPLORER")
    print("="*60)
    print(f"\n🖥️  Dashboard: http://localhost:{PORT}")
    print("⚠️  Make sure API server is running on port 9000!")
    print("\nPress Ctrl+C to stop.\n")
    
    with socketserver.TCPServer(("", PORT), PlatformHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()

