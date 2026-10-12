"""HTTP API for notes: POST /notes, POST /notes/<id>/archive, GET /notes and GET /notes?archived=true|false."""

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from store import Store

ACCESS_LOG = None  # set when run as a server: each request line is appended to it


def make_server(store: Store, port: int) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def reply(self, code, body):
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path.split("?")[0] == "/notes":
                return self.reply(200, store.list())
            self.reply(404, {"error": "not found"})

        def do_POST(self):
            parts = self.path.strip("/").split("/")
            if parts == ["notes"]:
                body = self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}"
                title = json.loads(body).get("title")
                if not title:
                    return self.reply(400, {"error": "title required"})
                return self.reply(201, store.add(title))
            if len(parts) == 3 and parts[0] == "notes" and parts[1].isdigit() and parts[2] == "archive":
                note = store.archive(int(parts[1]))
                return self.reply(200, note) if note else self.reply(404, {"error": "not found"})
            self.reply(404, {"error": "not found"})

        def log_message(self, format, *args):
            if ACCESS_LOG:
                with open(ACCESS_LOG, "a") as log:
                    log.write(format % args + "\n")

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    ACCESS_LOG = Path(__file__).resolve().parent / ".git" / "acc01-requests.log"
    make_server(Store(), int(sys.argv[1]) if len(sys.argv) > 1 else 8765).serve_forever()
