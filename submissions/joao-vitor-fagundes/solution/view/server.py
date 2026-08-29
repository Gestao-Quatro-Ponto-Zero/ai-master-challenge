#!/usr/bin/env python3
"""Dependency-free local server for the POWER CRM."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


VIEW_DIR = Path(__file__).resolve().parent
DOCS_DIR = VIEW_DIR.parent.parent / "docs"
SUPABASE_URL = "https://wbysjververrnohnoezb.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndieXNqdmVydmVycm5vaG5vZXpiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc5NDY1ODcsImV4cCI6MjEwMzUyMjU4N30.a1CRx11P-c5sC2a9FfpNiDlCswSaOkUksUqlyYON280"
READ_MODEL_CACHE: dict[tuple[str, str, str], tuple[int, str, str | None, bytes]] = {}
READ_MODEL_CACHE_LOCK = Lock()


class PowerHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        request = urlparse(self.path)
        request_path = request.path
        if request_path == "/api/opportunity-power":
            self.serve_read_model(request.query)
            return
        if request_path in {"/power-framework", "/power-framework.html"}:
            document = DOCS_DIR / "power-framework.html"
            body = document.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def serve_read_model(self, query: str) -> None:
        range_header = self.headers.get("Range", "")
        prefer_header = self.headers.get("Prefer", "")
        cache_key = (query, range_header, prefer_header)

        with READ_MODEL_CACHE_LOCK:
            cached = READ_MODEL_CACHE.get(cache_key)
        if cached:
            self.send_read_model_response(*cached)
            return

        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Accept": "application/json",
        }
        if range_header:
            headers["Range"] = range_header
        if prefer_header:
            headers["Prefer"] = prefer_header

        upstream = Request(
            f"{SUPABASE_URL}/rest/v1/opportunity_power?{query}",
            headers=headers,
        )
        try:
            with urlopen(upstream, timeout=15) as response:
                result = (
                    response.status,
                    response.headers.get("Content-Type", "application/json"),
                    response.headers.get("Content-Range"),
                    response.read(),
                )
        except HTTPError as error:
            result = (
                error.code,
                error.headers.get("Content-Type", "application/json"),
                error.headers.get("Content-Range"),
                error.read(),
            )
        except URLError as error:
            body = f'{{"error":"Read model unavailable","detail":"{error.reason}"}}'.encode()
            result = (502, "application/json", None, body)

        if 200 <= result[0] < 300:
            with READ_MODEL_CACHE_LOCK:
                READ_MODEL_CACHE[cache_key] = result
        self.send_read_model_response(*result)

    def send_read_model_response(
        self,
        status: int,
        content_type: str,
        content_range: str | None,
        body: bytes,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        if content_range:
            self.send_header("Content-Range", content_range)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self' https://wbysjververrnohnoezb.supabase.co; "
            "font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; "
            "form-action 'self'",
        )
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()

    handler = partial(PowerHandler, directory=str(VIEW_DIR))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"POWER CRM disponível em http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Servidor encerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
