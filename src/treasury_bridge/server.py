"""Loopback-only HTTP interface; no enterprise authentication or ERP access."""
import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from .demo import load_demo
from .engine import reconcile
from .ingest import read_bytes
from .store import Store
from .export import csv_report

WEB = Path(__file__).resolve().parent / "web"
MAX_BODY = 3_000_000

def handler(store):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def respond(self, body, status=200, content_type="application/json; charset=utf-8"):
            if isinstance(body, (dict, list)):
                body = json.dumps(body, ensure_ascii=False).encode()
            elif isinstance(body, str):
                body = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)

        def valid_host(self):
            return self.headers.get("Host") in (f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}")

        def do_GET(self):
            if not self.valid_host():
                return self.respond({"error":"Host não permitido"}, 403)
            parsed = urlparse(self.path)
            assets = {"/":("index.html","text/html; charset=utf-8"), "/app.js":("app.js","text/javascript; charset=utf-8"), "/style.css":("style.css","text/css; charset=utf-8")}
            if parsed.path in assets:
                filename, kind = assets[parsed.path]
                return self.respond((WEB/filename).read_bytes(), content_type=kind)
            try:
                rid = parse_qs(parsed.query).get("run", [""])[0]
                if parsed.path == "/api/report":
                    return self.respond(store.report(rid))
                if parsed.path == "/api/export.csv":
                    return self.respond(csv_report(store.report(rid)), content_type="text/csv; charset=utf-8")
                if parsed.path == "/api/export.json":
                    return self.respond(store.report(rid))
                self.respond({"error":"Não encontrado"}, 404)
            except ValueError as exc:
                self.respond({"error":str(exc)}, 400)

        def do_POST(self):
            origin = self.headers.get("Origin")
            allowed = (f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}")
            if not self.valid_host() or (origin and origin not in allowed):
                return self.respond({"error":"Origem não permitida"}, 403)
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_BODY:
                    raise ValueError("Requisição excede o limite local de 3 MB")
                if not self.headers.get("Content-Type", "").startswith("application/json"):
                    raise ValueError("Envie JSON")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Objeto JSON esperado")
                path = urlparse(self.path).path
                if path == "/api/demo":
                    bank, ledger = load_demo(Path(store.path).parent / "synthetic")
                    report = reconcile(bank, ledger)
                    store.save(report)
                    return self.respond(store.report(report["run_id"]))
                if path == "/api/import":
                    bank, ledger = [], []
                    files = data["files"]
                    if not isinstance(files, list) or not 2 <= len(files) <= 20:
                        raise ValueError("Envie 2..20 arquivos")
                    for file in files:
                        if file["side"] not in ("bank", "ledger"):
                            raise ValueError("Lado inválido")
                        rows = read_bytes(base64.b64decode(file["content"], validate=True), file["name"], file["side"])
                        (bank if file["side"] == "bank" else ledger).extend(rows)
                    report = reconcile(bank, ledger, int(data.get("window",2)))
                    store.save(report)
                    return self.respond(store.report(report["run_id"]))
                if path == "/api/review":
                    return self.respond(store.review(data["run_id"], data["bank_id"], data.get("ledger_id"), data["decision"], data["reviewer"], data["note"]))
                self.respond({"error":"Não encontrado"}, 404)
            except (ValueError, KeyError, TypeError) as exc:
                self.respond({"error":str(exc)}, 400)
    return Handler

def serve(port=8765, database="var/reviews.sqlite"):
    store = Store(database)
    server = HTTPServer(("127.0.0.1", port), handler(store))
    print(f"Treasury Bridge: http://127.0.0.1:{server.server_port} (Ctrl+C para encerrar)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
