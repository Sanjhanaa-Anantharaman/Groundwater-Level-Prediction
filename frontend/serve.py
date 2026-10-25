"""Serve the dashboard and forward /api/* requests to the FastAPI backend.

    python frontend/serve.py          ->  open http://127.0.0.1:5500/

The browser only talks to this server, so the backend needs no CORS setup.
Start the backend first:  uvicorn app.main:app --reload   (port 8000)
Override with env vars:  BACKEND=http://127.0.0.1:8000  PORT=5500  HOST=127.0.0.1
"""
import os
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = os.environ.get("BACKEND", "http://127.0.0.1:8000").rstrip("/")
PORT = int(os.environ.get("PORT", "5500"))
HOST = os.environ.get("HOST", "127.0.0.1")   # 0.0.0.0 when hosted


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/"):
            return self.proxy()
        super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            return self.proxy()
        self.send_error(405)

    def proxy(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        req = urllib.request.Request(BACKEND + self.path, data=body, method=self.command,
                                     headers={"Content-Type": self.headers.get("Content-Type", "application/json")})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                status, ctype, data = r.status, r.headers.get("Content-Type"), r.read()
        except urllib.error.HTTPError as e:      # 4xx/5xx from the API: pass it through
            status, ctype, data = e.code, e.headers.get("Content-Type"), e.read()
        except urllib.error.URLError as e:       # backend not running
            status, ctype = 502, "application/json"
            data = ('{"detail": "Backend not reachable at %s (%s). Is uvicorn running?"}' % (BACKEND, e.reason)).encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype or "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), partial(Handler, directory=str(HERE)))
    print(f"Dashboard: http://{HOST}:{PORT}/   (API requests forwarded to {BACKEND})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
