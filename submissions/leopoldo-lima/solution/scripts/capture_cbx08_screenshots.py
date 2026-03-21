"""Gera PNGs de evidência CRP-CBX-08 (combobox «Gestor comercial»).

Requisitos: `pip install playwright` e `python -m playwright install chromium`.
Sobe o servidor FastAPI numa porta livre, captura a secção de filtros e encerra.

Uso:
  python scripts/capture_cbx08_screenshots.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "process-log" / "ui-captures" / "cbx-08"
PORT = "8799"
BASE = f"http://127.0.0.1:{PORT}"


def _wait_health(timeout_s: float = 90.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/health", timeout=2) as r:
                if r.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(0.35)
    raise RuntimeError(f"Servidor não respondeu em {BASE}/health a tempo.")


def _fetch_managers() -> list[str]:
    with urllib.request.urlopen(f"{BASE}/api/dashboard/filter-options", timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    return list(data.get("managers") or [])


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
    except ImportError:
        print("Instale playwright: pip install playwright", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            PORT,
        ],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_health()
        managers = _fetch_managers()
        if not managers:
            print("AVISO: lista de gestores vazia; alguns passos podem falhar.", file=sys.stderr)
        sample = managers[0] if managers else "Mgr"
        prefix3 = sample[:3] if len(sample) >= 3 else sample.ljust(3, "x")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(f"{BASE}/", wait_until="networkidle", timeout=120000)
            page.wait_for_function(
                """() => {
                  const el = document.getElementById('manager-hint');
                  const t = (el && el.textContent ? el.textContent : '').toLowerCase();
                  return t.includes('todos') && t.includes('gestores');
                }""",
                timeout=120000,
            )

            panel = page.locator(".filters-panel")

            panel.screenshot(path=str(OUT_DIR / "cbx-08-01-combobox-inicial.png"))

            search = page.locator("#manager-search")
            search.click()
            page.wait_for_timeout(400)
            panel.screenshot(path=str(OUT_DIR / "cbx-08-01c-lista-completa.png"))

            search.fill("")
            search.type("zz")
            page.wait_for_timeout(350)
            panel.screenshot(path=str(OUT_DIR / "cbx-08-01b-filtro-incremental.png"))

            search.fill("")
            search.click()
            page.wait_for_timeout(200)
            search.type(prefix3)
            page.wait_for_timeout(350)
            page.wait_for_selector(
                "#manager-listbox .combobox-option", state="visible", timeout=15000
            )
            panel.screenshot(path=str(OUT_DIR / "cbx-08-02-tres-letras-sugestoes.png"))

            search.fill("")
            search.click()
            page.wait_for_timeout(200)
            search.type("zzz")
            page.wait_for_timeout(350)
            page.wait_for_selector("#manager-empty:not([hidden])", timeout=10000)
            panel.screenshot(path=str(OUT_DIR / "cbx-08-03-sem-resultados.png"))

            search.fill("")
            search.click()
            page.wait_for_timeout(200)
            search.type(prefix3)
            page.wait_for_timeout(350)
            page.locator("#manager-listbox .combobox-option").nth(1).click()
            page.wait_for_timeout(200)
            panel.screenshot(path=str(OUT_DIR / "cbx-08-04-gestor-selecionado.png"))

            page.locator("#filters-clear").click()
            page.wait_for_function(
                """() => {
                  const s = document.getElementById('manager-search');
                  return s && !s.value;
                }""",
                timeout=30000,
            )
            page.wait_for_timeout(300)
            panel.screenshot(path=str(OUT_DIR / "cbx-08-05-apos-limpar.png"))

            browser.close()

        print("PNG gravados em:", OUT_DIR)
        return 0
    except Exception as exc:
        print("Falha:", exc, file=sys.stderr)
        return 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
