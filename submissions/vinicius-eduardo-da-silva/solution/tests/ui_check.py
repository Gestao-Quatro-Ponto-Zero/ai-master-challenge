"""Drive the real page in a browser, check behavior, and save screenshots.

Needs Playwright and Microsoft Edge: pip install playwright

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


def nav_count(page, tab):
    return page.locator(f'[data-tab="{tab}"] .nav-count').inner_text()


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(viewport={"width": 1360, "height": 900}, accept_downloads=True)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(page_url)
    page.wait_for_selector(".deal")
    check("team counts", [nav_count(page, t) for t in ("foco", "decidir", "prospeccao")] == ["288", "1.301", "500"])

    # A rep's week
    page.select_option("#filter-agent", "Zane Levy")
    check("all live deals listed", page.locator(".deal").count() == 30, str(page.locator(".deal").count()))
    check("three highlighted deals", page.locator(".hero-deals .deal").count() == 3)
    scores = [int(s) for s in page.locator(".ring span").all_inner_texts()]
    check("scores sorted", scores == sorted(scores, reverse=True), str(scores[:10]))
    check("plan has three steps", page.locator(".step").count() == 3)
    page.screenshot(path=shots / "1-minha-semana.png")

    page.locator(".why summary").first.click()
    check("score explanation opens", "Momento" in page.locator(".why-body").first.inner_text())

    first_title = page.locator(".hero-deals h3").first.inner_text()
    page.locator('[data-focus="feito"]').first.click()
    check("marked deal leaves the to-do list", page.locator(".hero-deals h3").first.inner_text() != first_title)
    check("step progress updates", "1 de 10 feitos" in page.locator(".step").first.inner_text())
    check("pending count drops", nav_count(page, "foco") == "29")
    page.locator('[data-focus="adiado"]').first.click()
    check("review count", nav_count(page, "revisar") == "2")

    # Review
    page.click('[data-tab="revisar"]')
    check("review shows done and postponed", "Feitos nesta semana" in page.locator("#view").inner_text() and "Adiados" in page.locator("#view").inner_text())
    page.screenshot(path=shots / "3-revisar.png")
    page.locator("[data-undo-focus]").first.click()
    check("undo works in review", nav_count(page, "revisar") == "1")

    # Rep with no live deals
    page.click('[data-tab="foco"]')
    page.select_option("#filter-agent", "")
    page.select_option("#filter-region", "Central")
    check("central has no live deals", nav_count(page, "foco") == "0")
    managers = page.locator("#filter-manager option").all_inner_texts()
    check("manager filter cascades", set(managers) == {"Todos", "Dustin Brinkmann", "Melvin Marxen"}, str(managers))
    page.select_option("#filter-agent", "Darcel Schlecht")
    check("empty rep gets guidance", "nenhum deal vivo" in page.locator("#briefing").inner_text())

    # Triage
    page.click('[data-tab="decidir"]')
    check("decide list", page.locator(".simple-row").count() == 30)
    page.locator('.triage [data-decision="encerrar"]').click()
    check("decision updates progress", page.locator("#decision-progress").inner_text().startswith("1 de 83"))
    page.locator('.triage [data-decision="vivo"]').click()
    check("triage moves to the next deal", page.locator("#decision-progress").inner_text().startswith("2 de 83"))
    page.keyboard.press("e")
    check("keyboard decides", page.locator("#decision-progress").inner_text().startswith("3 de 83"))
    page.keyboard.press("u")
    check("keyboard undoes", page.locator("#decision-progress").inner_text().startswith("2 de 83"))
    before = page.locator(".triage h2").inner_text()
    page.keyboard.press("p")
    check("skip shows another deal", page.locator(".triage h2").inner_text() != before or "2 de 83" in page.locator("#decision-progress").inner_text())
    page.screenshot(path=shots / "2-decidir.png")
    with page.expect_download() as download_info:
        page.click('[data-action="export"]')
    exported = Path(download_info.value.path()).read_text(encoding="utf-8-sig")
    rows = [r for r in csv.DictReader(exported.splitlines()) if r["tipo"] == "parado"]
    check("csv export has both decisions", sorted(r["decisao"] for r in rows) == ["encerrar", "vivo"], str(rows[:1]))
    page.reload()
    page.wait_for_selector(".nav-count")
    page.click('[data-tab="decidir"]')
    check("decisions and rep survive reload", page.locator("#decision-progress").inner_text().startswith("2 de 83"))

    page.click('[data-tab="prospeccao"]')
    check("prospecting list", page.locator(".simple-row").count() == 30)
    check("prospecting says no score", "não recebem score" in page.locator(".page-head").inner_text())

    # Team
    page.select_option("#filter-agent", "")
    page.select_option("#filter-region", "")
    page.click('[data-tab="equipe"]')
    check("team table has 35 people", page.locator("tbody tr").count() == 35, str(page.locator("tbody tr").count()))
    check("three region cards", page.locator(".region").count() == 3)
    check("central flagged", "Sem deal vivo" in page.locator(".region", has_text="Central").inner_text())
    page.screenshot(path=shots / "4-equipe.png")
    page.click('[data-tab="foco"]')
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
    text = page.locator("#view").inner_text()
    check("no outcome before reveal", not any(w in text for w in ["Ganho:", "Perdido em", "Seguia aberto", "Conta em branco", "à frente"]))
    check("no strip before reveal", page.locator(".strip").count() == 0)
    page.click('[data-action="reveal"]')
    text = page.locator("#view").inner_text()
    check("reveal shows outcomes", "Ganho:" in text and "Lista por maior valor" in text)
    check("strip has all Mondays", page.locator(".strip-col").count() == 22)
    page.screenshot(path=shots / "5-maquina-do-tempo.png", full_page=True, clip={"x": 0, "y": 0, "width": 1360, "height": 1000})
    page.locator(".strip-col").nth(3).hover()
    check("strip tooltip", "à frente" in page.locator("#tooltip").inner_text())
    page.locator(".strip-col").nth(3).click()
    check("strip changes the Monday", page.locator("#replay-date").input_value() == "3")
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
            live: sum((entry) => entry.liveValueRevenue),
            official: window.LEAD_DATA.backtest.all,
          };
        }"""
    )
    check("machine matches official score result", round(totals["score"]) == round(totals["official"]["score"]["revenue"]))
    check("machine matches official value result", round(totals["value"]) == round(totals["official"]["maior_valor"]["revenue"]))
    check("machine matches official rival result", round(totals["live"]) == round(totals["official"]["maior_valor_sem_parados"]["revenue"]))

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
    check("age curve drawn", page.locator(".curve-col").count() == 10, str(page.locator(".curve-col").count()))
    page.screenshot(path=shots / "6-como-funciona.png", full_page=True)

    mobile = browser.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark").new_page()
    mobile.on("pageerror", lambda e: errors.append(str(e)))
    mobile.goto(page_url)
    mobile.wait_for_selector(".deal")
    mobile.select_option("#filter-agent", "Zane Levy")
    for tab in ("foco", "decidir", "prospeccao", "revisar", "equipe", "tempo", "como"):
        mobile.click(f'[data-tab="{tab}"]')
        overflow = mobile.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        check(f"no horizontal scroll on phone: {tab}", overflow <= 0, str(overflow))
    mobile.click('[data-tab="foco"]')

    check("no console errors", not errors, str(errors[:3]))
    browser.close()

print("\nFAILED:" if failures else "\nALL PASSED", failures or "")
sys.exit(1 if failures else 0)
