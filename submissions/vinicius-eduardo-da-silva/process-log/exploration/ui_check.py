"""Drive the real page in a browser, check behavior, and save screenshots.

Usage: python ui_check.py <path to index.html> <screenshot dir>
"""
import csv
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

page_url = Path(sys.argv[1]).resolve().as_uri()
shots = Path(sys.argv[2])
shots.mkdir(parents=True, exist_ok=True)
failures = []


def check(name, condition, detail=""):
    print(("ok  " if condition else "FAIL"), name, detail)
    if not condition:
        failures.append(name)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(page_url)
    page.wait_for_selector(".deal")
    tile_numbers = page.locator(".tile .number").all_inner_texts()
    check("all-team tiles", tile_numbers == ["288", "1.301", "500"], str(tile_numbers))
    page.screenshot(path=shots / "01-visao-geral.png")

    page.select_option("#filter-agent", "Zane Levy")
    check("rep list shows top 10 first", page.locator(".deal").count() == 30, str(page.locator(".deal").count()))
    scores = [int(s.split()[0]) for s in page.locator(".score").all_inner_texts()]
    check("scores sorted", scores == sorted(scores, reverse=True), str(scores[:10]))
    page.screenshot(path=shots / "02-vendedor-foco.png")

    page.select_option("#filter-agent", "")
    page.select_option("#filter-region", "Central")
    check("central has no live deals", page.locator(".tile .number").first.inner_text() == "0")
    managers = page.locator("#filter-manager option").all_inner_texts()
    check("manager filter cascades", set(managers) == {"Todos", "Dustin Brinkmann", "Melvin Marxen"}, str(managers))
    page.select_option("#filter-agent", "Darcel Schlecht")
    check("empty rep gets guidance", "nenhum deal vivo" in page.locator("#briefing").inner_text())
    page.screenshot(path=shots / "03-vendedor-sem-deal-vivo.png")

    page.click('[data-tab="decidir"]')
    check("decide queue count", page.locator(".simple-row").count() == 30)
    page.locator('[data-decision="encerrar"]').first.click()
    check("decision updates progress", page.locator("#decision-progress").inner_text().startswith("1 de 83"))
    page.locator('[data-decision="vivo"]').nth(1).click()
    page.screenshot(path=shots / "04-fila-decidir.png")
    with page.expect_download() as download_info:
        page.click('[data-action="export"]')
    exported = Path(download_info.value.path()).read_text(encoding="utf-8-sig")
    rows = list(csv.DictReader(exported.splitlines()))
    check("csv export has both decisions", sorted(r["decisao"] for r in rows) == ["encerrar", "vivo"], str(rows[:1]))
    page.reload()
    page.wait_for_selector(".tile")
    page.click('[data-tab="decidir"]')
    check("decisions and rep survive reload", page.locator("#decision-progress").inner_text().startswith("2 de 83"))

    page.click('[data-tab="prospeccao"]')
    check("prospecting list", page.locator(".simple-row").count() == 30)
    check("prospecting says no score", "não recebem score" in page.locator(".view-intro").inner_text())

    page.select_option("#filter-agent", "")
    page.select_option("#filter-region", "")
    page.click('[data-tab="equipe"]')
    check("team table has 35 people", page.locator("tbody tr").count() == 35, str(page.locator("tbody tr").count()))
    page.screenshot(path=shots / "05-equipe.png")
    page.select_option("#filter-agent", "Donn Cantrell")
    check("rep with no open deals", "nenhum deal aberto" in page.locator("#briefing").inner_text())
    page.select_option("#filter-agent", "Carl Lin")
    check("rep with no deals at all", "nenhum deal aberto" in page.locator("#briefing").inner_text())
    page.select_option("#filter-agent", "")

    # Calculator: keeps focus while typing and uses the filtered selection.
    page.click('[data-tab="equipe"]')
    field = page.locator('[data-calc="weekly"]')
    check("calculator starts from stale deals", "1.301" in page.locator("#calc-result").inner_text())
    field.fill("10")
    check("calculator updates", "216,8 horas" in page.locator("#calc-result").inner_text(), page.locator("#calc-result").inner_text())
    check("calculator keeps focus", page.evaluate("document.activeElement.dataset.calc") == "weekly")
    check("calculator says it is an assumption", "premissa" in page.locator(".calculator").inner_text())
    field.fill("5")

    # Time machine: nothing about the outcome may show before the reveal.
    page.click('[data-tab="tempo"]')
    page.screenshot(path=shots / "08-maquina-do-tempo-antes.png", full_page=False)
    text = page.locator("#view").inner_text()
    check("no outcome before reveal", not any(w in text for w in ["Ganho:", "Perdido em", "Seguia aberto", "Conta em branco"]))
    page.click('[data-action="reveal"]')
    text = page.locator("#view").inner_text()
    check("reveal shows outcomes", "Ganho:" in text and "Lista por maior valor" in text)
    page.screenshot(path=shots / "09-maquina-do-tempo-depois.png")
    page.select_option("#replay-date", index=0)
    check("changing the Monday hides results again", "Ganho:" not in page.locator("#view").inner_text())
    check("reveal button returns", page.locator('[data-action="reveal"]').count() == 1)

    totals = page.evaluate(
        """() => {
          const sum = (pick) => window.LEAD_REPLAY.reduce((all, monday) =>
            all + Object.values(monday.agents).reduce((part, entry) => part + pick(entry), 0), 0) / window.LEAD_REPLAY.length;
          return {
            score: sum((entry) => entry.deals.reduce((part, row) => part + row[9], 0)),
            value: sum((entry) => entry.valueRevenue),
            official: window.LEAD_DATA.backtest.all,
          };
        }"""
    )
    check("machine matches official score result", round(totals["score"]) == round(totals["official"]["score"]["revenue"]))
    check("machine matches official value result", round(totals["value"]) == round(totals["official"]["maior_valor"]["revenue"]))

    page.select_option("#filter-agent", "Zane Levy")
    page.select_option("#replay-date", index=5)
    check("rep list has at most 10", 0 < page.locator(".deal").count() <= 10, str(page.locator(".deal").count()))
    page.click('[data-action="reveal"]')
    check("rep verdict appears", page.locator(".verdict").count() == 1)
    page.select_option("#filter-agent", "Carl Lin")
    check("rep with no deals gets an empty state", page.locator(".empty").count() == 1)
    page.select_option("#filter-agent", "")

    page.click('[data-tab="como"]')
    check("pilot section shows numbers", "Um trimestre completo" in page.locator("#view").inner_text())
    page.screenshot(path=shots / "06-como-funciona.png", full_page=True)

    mobile = browser.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark").new_page()
    mobile.goto(page_url)
    mobile.wait_for_selector(".deal")
    mobile.select_option("#filter-agent", "Zane Levy")
    overflow = mobile.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check("no horizontal scroll on phone", overflow <= 0, str(overflow))
    mobile.screenshot(path=shots / "07-celular-escuro.png")
    mobile.click('[data-tab="como"]')
    overflow = mobile.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check("explanation fits on phone", overflow <= 0, str(overflow))

    check("no console errors", not errors, str(errors[:3]))
    browser.close()

print("\nFAILED:" if failures else "\nALL PASSED", failures or "")
sys.exit(1 if failures else 0)
