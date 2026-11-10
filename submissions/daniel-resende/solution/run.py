"""The one command: build every file and serve the app.

    python3 run.py --port 8000      then open http://127.0.0.1:8000/

Needs nothing beyond Python (3.10 or newer). Serves solution/web/ as the site,
solution/out/ under /out/ and the stored AI texts under /ai/textos.json.
"""
import argparse
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if clean.startswith("/out/") and "/" not in clean[5:] and ".." not in clean:
            return str(HERE / "out" / clean[5:])
        if clean == "/ai/textos.json":
            return str(HERE / "ai" / "textos.json")
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    build.main()
    handler = lambda *a, **k: Handler(*a, directory=str(HERE / "web"), **k)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Aberto em http://127.0.0.1:{args.port}/  (Ctrl+C para parar)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
