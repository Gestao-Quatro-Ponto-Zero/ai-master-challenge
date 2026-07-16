"""Capture real dashboard screenshots with a locally installed browser."""

from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "figures" / "dashboard"
URL = os.getenv("DASHBOARD_URL", "http://127.0.0.1:8765")
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")


def capture_view(page: Page, marker: str | None, filename: str, offset: int = 0) -> None:
    """Scroll to a heading when requested and capture the current viewport."""
    if marker:
        heading = page.get_by_text(marker, exact=True)
        heading.evaluate("element => element.scrollIntoView({block: 'start'})")
        page.evaluate("window.scrollBy(0, -24)")
        if offset:
            page.mouse.wheel(0, offset)
        page.wait_for_timeout(700)
    page.screenshot(path=str(OUTPUT / filename), full_page=False)


def capture_card(page: Page, marker: str, filename: str) -> None:
    """Capture the complete bordered answer card containing a heading."""
    heading = page.get_by_text(marker, exact=True)
    heading.scroll_into_view_if_needed()
    page.wait_for_timeout(2_500)
    card = heading.locator("xpath=ancestor::div[@data-testid='stVerticalBlock'][1]")
    card.wait_for()
    card.screenshot(path=str(OUTPUT / filename))


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not EDGE.exists():
        raise SystemExit(f"Edge executable not found: {EDGE}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=str(EDGE),
            args=["--force-device-scale-factor=1"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1050}, device_scale_factor=1)
        page.goto(URL, wait_until="networkidle", timeout=60_000)
        page.get_by_text("Respostas explícitas às perguntas do desafio", exact=True).wait_for()
        page.locator('[data-testid="stHeader"]').evaluate(
            "element => element.style.display = 'none'"
        )
        page.set_viewport_size({"width": 1440, "height": 1200})
        page.wait_for_timeout(800)

        capture_view(page, None, "dashboard-01-visao-geral.png")
        capture_card(page, "3. Qual audiência mais engaja?", "dashboard-02-audiencia.png")
        capture_view(page, "Exploração dos dados", "dashboard-03-exploracao.png")
        browser.close()

    for path in sorted(OUTPUT.glob("dashboard-0*.png")):
        print(f"captured={path.relative_to(ROOT)} bytes={path.stat().st_size}")


if __name__ == "__main__":
    main()
