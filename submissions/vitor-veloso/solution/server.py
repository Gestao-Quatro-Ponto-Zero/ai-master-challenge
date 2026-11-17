#!/usr/bin/env python3
"""
Server interativo para o Lead Scorer Dashboard
Permite que o vendedor/RevOps execute e visualize o dashboard interativo no navegador em http://localhost:8050.
"""

import http.server
import socketserver
import webbrowser
from pathlib import Path
import sys
from lead_scorer_app import main as run_scorer

PORT = 8050

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).resolve().parent), **kwargs)

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.path = '/lead_scorer_dashboard.html'
        return super().do_GET()

def start_server():
    base_dir = Path(__file__).resolve().parent
    html_file = base_dir / "lead_scorer_dashboard.html"
    
    if not html_file.exists():
        print("Gerando dashboard inicial a partir dos dados do CRM...")
        sys.argv = [sys.argv[0]]
        run_scorer()

    print(f"\n========================================================")
    print(f"🚀 Lead Scorer Hub rodando com sucesso!")
    print(f"🔗 Acesse no navegador: http://localhost:{PORT}")
    print(f"========================================================\n")

    # Permite reuso da porta
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor encerrado pelo usuário.")

if __name__ == "__main__":
    start_server()
