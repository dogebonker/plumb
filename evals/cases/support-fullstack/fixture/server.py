"""Launch scaffold: replace with your chosen full-stack implementation."""
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200 if self.path == '/health' else 501)
        self.end_headers()
        self.wfile.write(b'{"ready":true}' if self.path == '/health' else b'{"error":"Implementation needed"}')

HTTPServer((os.environ.get('HOST', '127.0.0.1'), int(os.environ.get('PORT', '8000'))), Handler).serve_forever()
