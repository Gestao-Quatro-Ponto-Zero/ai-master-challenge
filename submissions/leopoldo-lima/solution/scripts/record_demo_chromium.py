"""Grava demo do Focus Score Cockpit em Chromium (Playwright).

Sobe Uvicorn numa porta local, navega pelo cockpit (KPIs, filtros, pesquisa,
combobox de gestor com digitação visível). Após cada alteração de filtros
clica **Aplicar filtros**, espera o ranking e **rola** até à tabela / contagem
para evidenciar mudança de dados. Grava WebM e/ou PNG em
``artifacts/process-log/screen-recordings/``.

Pré-requisitos::

    pip install playwright
    python -m playwright install chromium

Dataset oficial esperado em ``data/`` (modo ``real_dataset`` por omissão).

Uso::

    python scripts/record_demo_chromium.py
    python scripts/record_demo_chromium.py --pace fast

Opções::

    --port 8808
    --pace slow|fast   (slow = pausas e teclas mais lentas, melhor para vídeo)
    --no-video
    --no-screenshots
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "process-log" / "screen-recordings"
DEFAULT_PORT = "8808"


def _wait_health(base: str, timeout_s: float = 90.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base}/health", timeout=2) as r:
                if r.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(0.35)
    raise RuntimeError(f"Servidor não respondeu em {base}/health a tempo.")


def _fetch_json(base: str, path: str) -> dict[str, Any]:
    with urllib.request.urlopen(f"{base}{path}", timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def _fetch_filter_options(base: str) -> dict[str, Any]:
    return _fetch_json(base, "/api/dashboard/filter-options")


def _sample_search_snippet(base: str) -> str:
    """Primeiros caracteres de conta/título/agente a partir do ranking atual."""
    data = _fetch_json(base, "/api/opportunities?limit=25")
    items = data.get("items") or []
    for it in items:
        for key in ("account", "title", "sales_agent", "seller"):
            s = str(it.get(key) or "").strip()
            if len(s) < 3:
                continue
            token = re.split(r"[\s/]+", s, maxsplit=1)[0]
            token = re.sub(r"[^0-9A-Za-zÀ-ÿ]", "", token)
            if len(token) >= 3:
                return token[:8]
    return "Op"


def _type_slow(page: Any, text: str, *, delay_ms: int) -> None:
    """Digitação caractere a caractere (visível no vídeo)."""
    for ch in text:
        page.keyboard.type(ch, delay=delay_ms)


def _scroll_section(page: Any, section: str, *, settle_ms: int, smooth: bool) -> None:
    """Rola a página para a secção indicada (evidência visual de «onde olhar»)."""
    selectors = {
        "kpi": ".kpi-deck",
        "filters": ".filters-panel",
        "ranking": ".ranking-panel",
        "detail": ".detail-panel",
    }
    sel = selectors[section]
    if smooth:
        page.evaluate(
            """(s) => {
              const el = document.querySelector(s);
              if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
            }""",
            sel,
        )
        page.wait_for_timeout(max(settle_ms, 600))
    else:
        page.locator(sel).first.scroll_into_view_if_needed()
        page.wait_for_timeout(settle_ms)


def _wait_ranking_idle(page: Any, *, timeout_ms: int = 60000) -> None:
    """Espera o ranking sair do estado «a carregar»."""
    page.wait_for_function(
        """() => {
          const st = document.getElementById('ranking-state');
          if (!st) return true;
          const t = st.textContent || '';
          const loading = st.classList.contains('state-loading') || t.includes('A carregar');
          return !loading;
        }""",
        timeout=timeout_ms,
    )


def _apply_filters_and_wait(page: Any, *, timeout_ms: int = 60000) -> None:
    """Submete o formulário de filtros e espera o ranking atualizar."""
    page.locator("#filters-form button[type='submit']").click()
    _wait_ranking_idle(page, timeout_ms=timeout_ms)


def _after_filter_change(
    page: Any,
    *,
    slow: bool,
    pause_filter: int,
    pause_short: int,
) -> None:
    """Aplica filtros, espera dados e rola até ao ranking (mostra que o resultado mudou)."""
    _apply_filters_and_wait(page)
    page.wait_for_timeout(pause_short)
    _scroll_section(page, "ranking", settle_ms=pause_filter // 2, smooth=slow)
    rc = page.locator("#result-count")
    rc.scroll_into_view_if_needed()
    if slow:
        page.evaluate(
            """() => {
              const el = document.getElementById('result-count');
              if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""",
        )
        page.wait_for_timeout(550)
    page.wait_for_timeout(pause_short)


def _run_demo(
    *,
    base: str,
    record_video: bool,
    take_screenshots: bool,
    pace: str,
) -> int:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
    except ImportError:
        print("Instale playwright: pip install playwright", file=sys.stderr)
        print("Depois: python -m playwright install chromium", file=sys.stderr)
        return 1

    slow = pace == "slow"
    pause_intro = 2800 if slow else 900
    pause_filter = 2000 if slow else 1200
    pause_short = 1200 if slow else 450
    key_delay = 95 if slow else 35

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    opts = _fetch_filter_options(base)
    managers: list[str] = list(opts.get("managers") or [])
    stages: list[str] = list(opts.get("deal_stages") or [])

    search_snippet = _sample_search_snippet(base)
    first_manager = managers[0] if managers else ""
    type_for_list = first_manager[: min(12, len(first_manager))] if first_manager else "zzz"

    if not managers:
        print("AVISO: lista de gestores vazia; combobox usará empty state.", file=sys.stderr)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx_kwargs: dict = {"viewport": {"width": 1366, "height": 900}}
        if record_video:
            ctx_kwargs["record_video_dir"] = str(OUT_DIR)
        context = browser.new_context(**ctx_kwargs)
        page = context.new_page()

        page.goto(f"{base}/", wait_until="networkidle", timeout=120000)
        page.wait_for_selector("#kpi-strip:not([hidden])", timeout=120000)
        page.wait_for_selector("#ranking-list tr", timeout=120000)
        page.wait_for_timeout(pause_intro)
        _scroll_section(page, "kpi", settle_ms=pause_short, smooth=slow)
        _scroll_section(page, "ranking", settle_ms=pause_filter // 2, smooth=slow)

        if take_screenshots:
            page.screenshot(path=str(OUT_DIR / "demo-01-kpis-ranking.png"), full_page=True)

        # Escritório regional (se existir)
        office_opts = page.locator('#filter-region option:not([value=""])')
        if office_opts.count() > 0:
            pick_idx = 1 if office_opts.count() > 1 else 0
            val = office_opts.nth(pick_idx).get_attribute("value") or ""
            if val:
                _scroll_section(page, "filters", settle_ms=pause_short, smooth=slow)
                page.select_option("#filter-region", val)
                _after_filter_change(
                    page,
                    slow=slow,
                    pause_filter=pause_filter,
                    pause_short=pause_short,
                )

        if take_screenshots:
            page.screenshot(path=str(OUT_DIR / "demo-02-filtro-escritorio.png"), full_page=True)

        # Estágio: preferir Engaging / Prospecting
        stage_pick = ""
        for want in ("Engaging", "Prospecting", "Won"):
            if want in stages:
                stage_pick = want
                break
        if not stage_pick:
            stage_opts = page.locator('#filter-deal-stage option:not([value=""])')
            if stage_opts.count() > 0:
                stage_pick = stage_opts.nth(0).get_attribute("value") or ""
        if stage_pick:
            _scroll_section(page, "filters", settle_ms=pause_short, smooth=slow)
            page.select_option("#filter-deal-stage", stage_pick)
            _after_filter_change(
                page,
                slow=slow,
                pause_filter=pause_filter,
                pause_short=pause_short,
            )

        if take_screenshots:
            page.screenshot(path=str(OUT_DIR / "demo-03-filtro-estagio.png"), full_page=True)

        # Faixa de prioridade
        _scroll_section(page, "filters", settle_ms=pause_short, smooth=slow)
        page.select_option("#priority-band", "high")
        _after_filter_change(
            page,
            slow=slow,
            pause_filter=pause_filter,
            pause_short=pause_short,
        )

        # Pesquisa texto (conta / título / agente) — digitação lenta
        _scroll_section(page, "filters", settle_ms=pause_short, smooth=slow)
        q = page.locator("#search-q")
        q.click()
        q.fill("")
        _type_slow(page, search_snippet, delay_ms=key_delay)
        _after_filter_change(
            page,
            slow=slow,
            pause_filter=pause_filter,
            pause_short=pause_short,
        )

        if take_screenshots:
            page.screenshot(path=str(OUT_DIR / "demo-04-pesquisa-texto.png"), full_page=True)

        # Combobox gestor: digitar nome e escolher da lista
        _scroll_section(page, "filters", settle_ms=pause_short, smooth=slow)
        search = page.locator("#manager-search")
        search.click()
        page.wait_for_timeout(pause_short // 2)
        search.fill("")
        if managers:
            _type_slow(page, type_for_list, delay_ms=key_delay)
            page.wait_for_timeout(pause_short)
            page.wait_for_selector(
                "#manager-listbox .combobox-option",
                state="visible",
                timeout=25000,
            )
            page.locator("#manager-listbox .combobox-option").first.click()
            _after_filter_change(
                page,
                slow=slow,
                pause_filter=pause_filter,
                pause_short=pause_short,
            )
        else:
            _type_slow(page, "zzz", delay_ms=key_delay)
            page.wait_for_timeout(pause_short)
            page.wait_for_selector("#manager-empty:not([hidden])", timeout=15000)
            _after_filter_change(
                page,
                slow=slow,
                pause_filter=pause_filter,
                pause_short=pause_short,
            )

        if take_screenshots:
            page.screenshot(path=str(OUT_DIR / "demo-05-combobox-gestor.png"), full_page=True)
            page.locator(".filters-panel").screenshot(
                path=str(OUT_DIR / "demo-06-painel-filtros.png")
            )

        _scroll_section(page, "ranking", settle_ms=pause_filter // 2, smooth=slow)
        if page.locator("#ranking-list tr").count() == 0:
            _scroll_section(page, "filters", settle_ms=pause_short, smooth=slow)
            page.locator("#filters-clear").click()
            _wait_ranking_idle(page)
            page.wait_for_timeout(pause_short)
            _scroll_section(page, "ranking", settle_ms=pause_filter // 2, smooth=slow)
        page.wait_for_selector("#ranking-list tr", timeout=60000)
        page.locator("#ranking-list tr").first.click()
        page.wait_for_selector(".detail-hero", timeout=60000)
        page.wait_for_timeout(600 if slow else 250)
        _scroll_section(page, "detail", settle_ms=pause_filter // 2, smooth=slow)
        page.wait_for_timeout(1600 if slow else 500)

        if take_screenshots:
            page.screenshot(path=str(OUT_DIR / "demo-07-detalhe.png"), full_page=True)

        page.wait_for_timeout(1800 if slow else 600)
        context.close()
        browser.close()

    if record_video:
        candidates = [p for p in OUT_DIR.glob("*.webm") if p.name != "demo-cockpit.webm"]
        if not candidates:
            print("AVISO: gravação ativada mas nenhum .webm encontrado.", file=sys.stderr)
            return 1
        latest = max(candidates, key=lambda p: p.stat().st_mtime)
        dest = OUT_DIR / "demo-cockpit.webm"
        if dest.exists():
            dest.unlink()
        shutil.move(str(latest), str(dest))
        for leftover in OUT_DIR.glob("*.webm"):
            if leftover.name != "demo-cockpit.webm":
                leftover.unlink(missing_ok=True)
        print(f"Vídeo: {dest}")

    if take_screenshots:
        print(f"PNG: {OUT_DIR}/demo-*.png")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Demo Chromium + gravação Focus Score Cockpit")
    parser.add_argument("--port", default=DEFAULT_PORT, help="Porta Uvicorn (default 8808)")
    parser.add_argument(
        "--pace",
        choices=("slow", "fast"),
        default="slow",
        help="slow = pausas longas e teclas lentas (recomendado para vídeo)",
    )
    parser.add_argument("--no-video", action="store_true", help="Não grava WebM")
    parser.add_argument("--no-screenshots", action="store_true", help="Não gera PNG")
    args = parser.parse_args()
    port = str(args.port).strip()
    base = f"http://127.0.0.1:{port}"
    record_video = not args.no_video
    take_shots = not args.no_screenshots

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            port,
        ],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_health(base)
        return _run_demo(
            base=base,
            record_video=record_video,
            take_screenshots=take_shots,
            pace=args.pace,
        )
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
