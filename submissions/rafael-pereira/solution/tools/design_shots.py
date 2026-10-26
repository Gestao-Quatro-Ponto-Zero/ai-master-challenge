"""Screenshots do loop visual de design (matriz enxuta) e do conjunto final.

Uso (cwd = solution/):
    python tools/design_shots.py --round r1        # process-log/screenshots/design-r1/
    python tools/design_shots.py --final           # process-log/screenshots/final-*.png

Matriz da rodada: 2 perfis x {entrada, aba principal, terceira tela} x {390, 1280} x {claro, escuro}.
A terceira tela do vendedor é o card aberto com ações e simulador; a do manager é a pauta do 1:1.
Abre a página em file:// (sem servidor), como o avaliador abriria. Falha se houver erro de console.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from check_app import launch

sys.stdout.reconfigure(encoding="utf-8")

TOOLS = Path(__file__).resolve().parent
SOL = TOOLS.parent
SUB = SOL.parent
APP = SOL / "app" / "index.html"
SHOTS = SUB / "process-log" / "screenshots"
VENDEDOR = "Rosalina Dieter"
MANAGER = "Celia Rouche"
SIZES = {390: 844, 1280: 800}
THEMES = ["claro", "escuro"]


def open_page(browser, hash_: str, w: int, theme: str, errors: list[str]):
    ctx = browser.new_context(viewport={"width": w, "height": SIZES[w]}, color_scheme="dark" if theme == "escuro" else "light")
    page = ctx.new_page()
    page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("requestfailed", lambda r: errors.append(f"requestfailed: {r.url}"))
    page.goto(APP.resolve().as_uri() + ("#" + hash_ if hash_ else ""))
    page.wait_for_selector("#app:not([hidden])")
    page.wait_for_function("() => !document.querySelector('#entry').hidden || document.querySelector('#action-summary').textContent.trim().length > 0")
    page.evaluate("document.fonts.ready")
    return ctx, page


def settle(page):
    page.mouse.move(0, 0)
    page.wait_for_timeout(700)  # contagem animada e transições


def scene_entrada_vendedor(page):
    page.select_option("#entry-agent", label=VENDEDOR)


def scene_entrada_manager(page):
    page.select_option("#entry-mgr", label=f"{MANAGER} — West")


def scene_acoes(page):
    card = page.locator("[data-testid=deal-card]").first
    card.locator(".card-toggle").click()
    card.locator("[data-testid=act-contatei]").click()
    if card.locator("[data-testid=act-sim]").count():
        card.locator("[data-testid=act-sim]").click()
    page.wait_for_timeout(700)
    card.evaluate("e => e.scrollIntoView({block: 'start'})")
    page.evaluate("window.scrollBy(0, -80)")


def scene_pauta(page):
    page.locator("#pauta-title").scroll_into_view_if_needed()
    page.evaluate("window.scrollBy(0, -120)")


def scene_mapa_aberto(page):
    page.locator("[data-testid=open-agent]").first.click()
    page.wait_for_timeout(300)


SCENES = [
    # nome, hash, função extra
    ("vendedor-entrada", "", scene_entrada_vendedor),
    ("vendedor-semana", f"perfil=vendedor&nome={VENDEDOR.replace(' ', '+')}", None),
    ("vendedor-acoes", f"perfil=vendedor&nome={VENDEDOR.replace(' ', '+')}", scene_acoes),
    ("manager-entrada", "", scene_entrada_manager),
    ("manager-time", f"perfil=manager&nome={MANAGER.replace(' ', '+')}", None),
    ("manager-pauta", f"perfil=manager&nome={MANAGER.replace(' ', '+')}&ver={VENDEDOR.replace(' ', '+')}&pauta=1", scene_pauta),
]


def run_round(name: str) -> int:
    out = SHOTS / f"design-{name}"
    out.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    n = 0
    with sync_playwright() as p:
        browser = launch(p)
        for scene, h, extra in SCENES:
            for w in SIZES:
                for theme in THEMES:
                    ctx, page = open_page(browser, h, w, theme, errors)
                    if extra:
                        extra(page)
                    settle(page)
                    page.screenshot(path=str(out / f"{scene}-{w}-{theme}.png"))
                    n += 1
                    ctx.close()
        browser.close()
    print(f"{n} screenshots em {out}")
    return report(errors)


def run_final() -> int:
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    v = VENDEDOR.replace(" ", "+")
    m = MANAGER.replace(" ", "+")
    jobs = [
        ("final-entrada-{w}.png", "", None, "claro"),
        ("final-vendedor-{w}.png", f"perfil=vendedor&nome={v}", None, "claro"),
        ("final-manager-{w}.png", f"perfil=manager&nome={m}", None, "claro"),
        ("final-pauta-{w}.png", f"perfil=manager&nome={m}&ver={v}&pauta=1", scene_pauta, "claro"),
        ("final-escuro-vendedor-{w}.png", f"perfil=vendedor&nome={v}", None, "escuro"),
        ("final-escuro-manager-{w}.png", f"perfil=manager&nome={m}", None, "escuro"),
        ("final-escuro-pauta-{w}.png", f"perfil=manager&nome={m}&ver={v}&pauta=1", scene_pauta, "escuro"),
    ]
    n = 0
    with sync_playwright() as p:
        browser = launch(p)
        for pattern, h, extra, theme in jobs:
            for w in SIZES:
                ctx, page = open_page(browser, h, w, theme, errors)
                if extra:
                    extra(page)
                settle(page)
                page.screenshot(path=str(SHOTS / pattern.format(w=w)))
                n += 1
                ctx.close()
        browser.close()
    print(f"{n} screenshots finais em {SHOTS}")
    return report(errors)


def report(errors: list[str]) -> int:
    errs = sorted(set(errors))
    print("console: " + ("; ".join(errs[:5]) if errs else "nenhum erro"))
    return 1 if errs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--round", help="nome da rodada: r1, r2 ou r3")
    g.add_argument("--final", action="store_true")
    a = ap.parse_args()
    sys.exit(run_final() if a.final else run_round(a.round))
