"""Capture the README screenshots and the demo animation of the prototype page with Playwright (challenge 002).

Starts the page on 127.0.0.1 in a background process, drives it in headless Chromium and saves:
  <screenshots-dir>/001-ticket-encaminhado-sozinho.png  a ticket routed alone
  <screenshots-dir>/002-ticket-fila-humana.png          human queue: suggestions, similar tickets and an AI draft
  <screenshots-dir>/003-aba-avaliacao.png               the evaluation tab
  <video-dir>/001-prototipo.gif                         the same steps as a 60 to 90 s animation (WebM -> ffmpeg)
Every text the page shows is checked for the OpenRouter key, local paths and e-mail addresses, and the run stops if
one appears. The AI draft needs OPENROUTER_API_KEY in .env. No step clicks "Aprovar": approval stays with a person.

Usage (Playwright stays outside the project dependencies):
  uv run --no-project --python 3.12 --with-requirements requirements.txt --with playwright==1.62.0 \
    python -I scripts/013-capture-media.py --screenshots-dir DIR --video-dir DIR [--skip-video]
"""
import argparse
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGE_SCRIPT = ROOT / "scripts" / "008-triage-app.py"
ENV_PATH = ROOT / ".env"
HOST = "127.0.0.1"
STARTUP_TIMEOUT_SECONDS = 90
RUN_TIMEOUT_MS = 120_000
SCREENSHOT_VIEWPORT = {"width": 1440, "height": 2400}
VIDEO_VIEWPORT = {"width": 1280, "height": 800}
HUMAN_QUEUE_DRAWS = 1  # 1st draw with seed 42: line 5050, human queue (the same ticket as docs/006, annex A.2)
ROUTED_ALONE_DRAWS = 4  # 4th draw: line 18493, routed alone to Access
MIN_VIDEO_SECONDS = 65
GIF_FPS = 6
GIF_WIDTH = 1024
SUMMARY_BUTTON = "Gerar resumo para o atendente"
DECISION_HUMAN = "Fila humana com sugestões"
DECISION_AUTO = "Encaminhado automaticamente"
FORBIDDEN_PATTERNS = {"caminho local": r"/Users/|/Volumes/|/home/|[A-Za-z]:\\",
                      "e-mail": r"[\w.+-]+@[\w-]+\.[\w.]+",
                      "chave": r"sk-or-"}
HIGHLIGHT_CSS = "el => { el.style.outline = '3px solid #e8590c'; el.style.outlineOffset = '3px'; }"
# The draft box is resizable on the page; for the capture it is stretched to show the whole draft, as a person
# would by dragging its corner. Only the height changes, never the text.
EXPAND_CSS = ("el => { let node = el; for (let i = 0; i < 4 && node; i++, node = node.parentElement) {"
              " node.style.height = 'auto'; node.style.maxHeight = 'none'; }"
              " el.style.height = (el.scrollHeight + 8) + 'px'; }")


def read_api_key():
    if not ENV_PATH.exists():
        return None
    for line in ENV_PATH.read_text().splitlines():
        name, _, value = line.partition("=")
        if name.strip() == "OPENROUTER_API_KEY" and value.strip():
            return value.strip()
    return None


def free_port():
    with socket.socket() as probe:
        probe.bind((HOST, 0))
        return probe.getsockname()[1]


def start_page(port):
    command = [sys.executable, "-m", "streamlit", "run", str(PAGE_SCRIPT), "--server.address", HOST,
               "--server.port", str(port), "--server.headless", "true", "--client.toolbarMode", "viewer",
               "--browser.gatherUsageStats", "false"]
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        with socket.socket() as probe:
            if probe.connect_ex((HOST, port)) == 0:
                return process
        time.sleep(0.5)
    process.terminate()
    raise SystemExit("A página não abriu a tempo.")


class Checker:
    """Collects every text the page shows and fails on the key, local paths or e-mail addresses."""

    def __init__(self, api_key):
        self.api_key = api_key
        self.checked = 0

    def check(self, page, step):
        values = page.eval_on_selector_all("textarea, input", "elements => elements.map(e => e.value).join('\\n')")
        text = page.inner_text("body") + "\n" + values
        self.checked += 1
        problems = [name for name, pattern in FORBIDDEN_PATTERNS.items() if re.search(pattern, text)]
        if self.api_key and self.api_key in text:
            problems.append("valor da chave")
        if problems:
            raise SystemExit(f"Parado no passo '{step}': a página mostrou {', '.join(problems)}.")


def wait_for_run(page):
    page.wait_for_timeout(400)  # give the rerun time to start before waiting for it to end
    page.wait_for_selector('[data-testid="stApp"][data-test-script-state="notRunning"]', timeout=RUN_TIMEOUT_MS)
    page.wait_for_timeout(300)


def click(page, locator, highlight=False, pause_ms=0):
    locator.scroll_into_view_if_needed()
    if highlight:
        locator.evaluate(HIGHLIGHT_CSS)
        page.wait_for_timeout(600)
    locator.click()
    wait_for_run(page)
    if highlight and locator.count():
        locator.evaluate("el => { el.style.outline = ''; }")
    page.wait_for_timeout(pause_ms)


def button(page, name):
    return page.get_by_role("button", name=name, exact=True)


def open_page(page, url):
    page.goto(url)
    page.get_by_role("button", name="Sortear ticket do teste").wait_for(timeout=RUN_TIMEOUT_MS)
    wait_for_run(page)


def triage_after_draws(page, draws, expected, checker, highlight=False, pause_ms=0):
    for _ in range(draws):
        click(page, button(page, "Sortear ticket do teste"), highlight, pause_ms)
    click(page, button(page, "Triar"), highlight, pause_ms)
    page.get_by_text(expected).first.wait_for()
    checker.check(page, f"triagem: {expected}")


def generate_summary(page, checker, highlight=False, pause_ms=0):
    click(page, button(page, SUMMARY_BUTTON), highlight, pause_ms)
    if page.get_by_text(re.compile(r"^(Erro \d+ da API|Falha ao gerar o rascunho)")).count():
        raise SystemExit("A chamada da IA generativa falhou; veja a página.")
    draft = page.get_by_label(re.compile("^Rascunho")).first
    draft.wait_for()
    draft.evaluate(EXPAND_CSS)
    page.wait_for_timeout(300)
    checker.check(page, "rascunho da IA generativa")
    return draft


def main_box(page):
    box = page.locator('[data-testid="stMain"]').bounding_box()
    return box or {"x": 0, "width": SCREENSHOT_VIEWPORT["width"]}


def clip_between(page, top_locator, bottom_locator, padding=16, full_width=False):
    top = top_locator.bounding_box()["y"] - padding
    bottom_box = bottom_locator.bounding_box()
    bottom = bottom_box["y"] + bottom_box["height"] + padding
    area = {"x": 0, "width": SCREENSHOT_VIEWPORT["width"]} if full_width else main_box(page)
    return {"x": area["x"], "y": max(top, 0), "width": area["width"], "height": bottom - max(top, 0)}


def take_screenshots(browser, url, folder, checker):
    folder.mkdir(parents=True, exist_ok=True)
    page = browser.new_page(viewport=SCREENSHOT_VIEWPORT)
    open_page(page, url)
    checker.check(page, "abertura")

    triage_after_draws(page, ROUTED_ALONE_DRAWS, DECISION_AUTO, checker)
    title = page.get_by_role("heading", name="Triagem de tickets: protótipo")
    similar = page.get_by_text("Tickets parecidos do histórico")
    person = page.get_by_text("Decisão da pessoa: confirmar ou corrigir a categoria")
    clip = clip_between(page, title, similar, full_width=True)
    clip["height"] = person.bounding_box()["y"] - clip["y"] - 8
    page.screenshot(path=folder / "001-ticket-encaminhado-sozinho.png", clip=clip)

    page.reload()
    open_page(page, url)
    triage_after_draws(page, HUMAN_QUEUE_DRAWS, DECISION_HUMAN, checker)
    draft = generate_summary(page, checker)
    decision = page.get_by_role("heading", name="Decisão", exact=True)
    page.screenshot(path=folder / "002-ticket-fila-humana.png", clip=clip_between(page, decision, draft))

    page.get_by_role("tab", name="Avaliação no teste").click()
    wait_for_run(page)
    checker.check(page, "aba de avaliação")
    first = page.get_by_text(re.compile("^Avaliação em"))
    last = page.get_by_text(re.compile("^Horas de triagem economizadas"))
    page.screenshot(path=folder / "003-aba-avaliacao.png", clip=clip_between(page, first, last))
    page.close()


def scroll(page, total, steps=6, pause_ms=250):
    page.mouse.move(VIDEO_VIEWPORT["width"] * 0.6, VIDEO_VIEWPORT["height"] * 0.6)
    for _ in range(steps):
        page.mouse.wheel(0, total / steps)
        page.wait_for_timeout(pause_ms)


def record_video(browser, url, folder, checker):
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as raw_dir:
        context = browser.new_context(viewport=VIDEO_VIEWPORT, record_video_dir=raw_dir,
                                      record_video_size=VIDEO_VIEWPORT)
        page = context.new_page()
        started = time.monotonic()
        open_page(page, url)
        ready = time.monotonic() - started
        page.wait_for_timeout(3000)

        triage_after_draws(page, HUMAN_QUEUE_DRAWS, DECISION_HUMAN, checker, highlight=True, pause_ms=1500)
        scroll(page, 450)
        page.wait_for_timeout(4000)
        draft = generate_summary(page, checker, highlight=True)
        draft.scroll_into_view_if_needed()
        page.wait_for_timeout(7000)

        scroll(page, -3000, steps=4)
        # The draw counter lives in the session, so the routed-alone ticket is a few draws ahead of the first one.
        triage_after_draws(page, ROUTED_ALONE_DRAWS - HUMAN_QUEUE_DRAWS, DECISION_AUTO, checker, highlight=True,
                           pause_ms=700)
        scroll(page, 450)
        page.wait_for_timeout(4000)
        page.get_by_text("Registro (campos do docs/003)").scroll_into_view_if_needed()
        page.wait_for_timeout(4000)

        scroll(page, -3000, steps=4)
        click(page, page.get_by_role("tab", name="Avaliação no teste"), highlight=True, pause_ms=3500)
        checker.check(page, "aba de avaliação")
        scroll(page, 500)
        page.wait_for_timeout(3500)
        minutes = page.get_by_label("Minutos de triagem manual por ticket (m)")
        minutes.scroll_into_view_if_needed()
        minutes.evaluate(HIGHLIGHT_CSS)
        minutes.fill("5")
        minutes.press("Enter")
        wait_for_run(page)
        checker.check(page, "minutos alterados")
        remaining = MIN_VIDEO_SECONDS - (time.monotonic() - started - ready)
        page.wait_for_timeout(max(4000, remaining * 1000))
        context.close()
        raw_video = Path(page.video.path())
        return convert_to_gif(raw_video, folder / "001-prototipo.gif", max(ready - 0.5, 0))


def convert_to_gif(raw_video, target, skip_seconds):
    filters = (f"fps={GIF_FPS},scale={GIF_WIDTH}:-1:flags=lanczos,split[a][b];"
               "[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{skip_seconds:.1f}", "-i", str(raw_video),
                    "-vf", filters, str(target)], check=True)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            str(target)], capture_output=True, text=True, check=True)
    return float(probe.stdout.strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--screenshots-dir", required=True, type=Path)
    parser.add_argument("--video-dir", required=True, type=Path)
    parser.add_argument("--skip-video", action="store_true")
    args = parser.parse_args()
    api_key = read_api_key()
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY ausente no .env: o print da fila humana precisa de um rascunho real.")
    checker = Checker(api_key)
    port = free_port()
    server = start_page(port)
    url = f"http://{HOST}:{port}"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            take_screenshots(browser, url, args.screenshots_dir, checker)
            for path in sorted(args.screenshots_dir.glob("*.png")):
                print(f"{path.name}: {path.stat().st_size / 1e3:.0f} KB")
            if not args.skip_video:
                seconds = record_video(browser, url, args.video_dir, checker)
                gif = args.video_dir / "001-prototipo.gif"
                print(f"{gif.name}: {gif.stat().st_size / 1e6:.2f} MB, {seconds:.1f} s")
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=30)
    print(f"Textos da página conferidos em {checker.checked} passos: sem chave, caminho local ou e-mail.")


if __name__ == "__main__":
    main()
