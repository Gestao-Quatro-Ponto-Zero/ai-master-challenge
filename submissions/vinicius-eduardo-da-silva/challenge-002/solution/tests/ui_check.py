"""Drive the real prototype in a browser, and prove the browser model matches Python.

Needs Playwright and Microsoft Edge: pip install playwright

Usage: python ui_check.py <path to index.html> <screenshot dir>
"""
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


PARITY = """() => {
  const all = [...window.TRIAGE_DATA.samples, ...window.TRIAGE_DATA.customerSamples].filter((t) => t.fullText);
  let laneMismatch = 0, reasonMismatch = 0, categoryMismatch = 0, largestGap = 0;
  for (const ticket of all) {
    const result = classify(ticket.text);
    if (result.lane !== ticket.lane) laneMismatch += 1;
    if (result.reason !== ticket.reason) reasonMismatch += 1;
    if (result.top.name !== ticket.predicted) categoryMismatch += 1;
    largestGap = Math.max(largestGap, Math.abs(result.top.probability - ticket.confidence));
  }
  return { tickets: all.length, laneMismatch, reasonMismatch, categoryMismatch, largestGap };
}"""

SLIDER = """() => {
  const policy = policyAt(window.TRIAGE_MODEL.routeConfidence);
  const official = window.TRIAGE_DATA.results.lanes;
  return { routed: policy.routedShare, accuracy: policy.accuracy, officialRouted: official.rotear.share, officialAccuracy: official.rotear.accuracy, human: policy.humanShare, officialHuman: official.humano.share };
}"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_context(viewport={"width": 1360, "height": 900}).new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(page_url)
    page.wait_for_selector("#live-lane")

    parity = page.evaluate(PARITY)
    check("browser and python agree on lane", parity["laneMismatch"] == 0, str(parity))
    check("browser and python agree on reason", parity["reasonMismatch"] == 0)
    check("browser and python agree on category", parity["categoryMismatch"] == 0)
    check("confidence differs by rounding only", parity["largestGap"] < 0.005, str(parity["largestGap"]))
    check("parity covers many tickets", parity["tickets"] > 200, str(parity["tickets"]))

    slider = page.evaluate(SLIDER)
    check("batch policy matches official routed share", abs(slider["routed"] - slider["officialRouted"]) < 0.001, str(slider))
    check("batch policy matches official accuracy", abs(slider["accuracy"] - slider["officialAccuracy"]) < 0.001)
    check("batch policy matches official human share", abs(slider["human"] - slider["officialHuman"]) < 0.001)

    expected = {0: "Rotear", 1: "Sugerir", 2: "humano", 3: "Sugerir", 4: "humano"}
    for index, word in expected.items():
        page.locator("[data-example]").nth(index).click()
        check(f"example {index} goes to {word}", word in page.locator("#live-lane").inner_text(), page.locator("#live-lane").inner_text())
    page.screenshot(path=shots / "1-triagem.png")

    field = page.locator("#ticket-text")
    field.fill("my laptop screen is broken and the keyboard does not work please send a replacement")
    check("typing updates the result", "Hardware" in page.locator("#live-bars").inner_text(), page.locator("#live-bars").inner_text())
    check("typing keeps focus", page.evaluate("document.activeElement.id") == "ticket-text")
    field.fill("laptop screen broken, this is about my termination")
    check("sensitive word goes to a human", "humano" in page.locator("#live-lane").inner_text())
    field.fill("")
    check("empty ticket asks for text", "Cole um ticket" in page.locator("#live-result").inner_text())
    field.fill("<script>window.hacked = 1</script> <img src=x onerror=window.hacked=1>")
    check("ticket text is not executed", page.evaluate("window.hacked") is None)
    field.fill("قال مرحبا 你好 ¿qué?")
    check("unknown language goes to a human", "humano" in page.locator("#live-lane").inner_text())

    page.click('[data-tab="lote"]')
    start = page.locator("#slider-coverage").inner_text()
    check("slider starts at official coverage", start.startswith("51,7"), start)
    page.locator("#threshold").fill("0.6")
    lower = page.locator("#slider-coverage").inner_text()
    check("lower threshold routes more", float(lower.replace("%", "").replace(",", ".")) > 51.7, lower)
    check("lower threshold is less accurate", float(page.locator("#slider-accuracy").inner_text().replace("%", "").replace(",", ".")) < 92.7)
    page.locator("#threshold").fill("0.9")
    page.screenshot(path=shots / "2-teste-em-lote.png")
    page.click('[data-filter="erros"]')
    check("error filter shows only wrong tickets", page.locator(".ticket .right").count() == 0 and page.locator(".ticket .wrong").count() > 0)
    page.click('[data-filter="clientes"]')
    check("customer filter has no fake comparison", "Sem categoria real" in page.locator("#batch-list").inner_text())
    page.click('[data-filter="todos"]')
    page.locator("[data-try]").first.click()
    check("try button opens the live triage", page.locator("#live-lane").count() == 1)

    page.click('[data-tab="diagnostico"]')
    text = page.locator("#view").inner_text()
    check("diagnosis shows the asked answer and the proof", all(w in text for w in ["Chat + High + Refund request", "p = 0,38", "49%", "O que capturar"]), text[:100])
    page.screenshot(path=shots / "3-diagnostico.png", full_page=True)

    page.click('[data-tab="fluxo"]')
    check("flow lists what not to automate", "O que não automatizar" in page.locator("#view").inner_text())
    check("flow gives real examples", page.locator("#view article.ticket").count() == 4, str(page.locator("#view article.ticket").count()))
    page.screenshot(path=shots / "4-fluxo.png", full_page=True)

    page.click('[data-tab="roi"]')
    net = page.locator("#roi-net").inner_text()
    check("roi shows a scenario", "horas por ano" in net, net)
    check("roi says it is not a measurement", "não uma medição" in page.locator("#view").inner_text())
    rework = page.locator('[data-roi="rework"]')
    rework.fill("500")
    check("expensive errors can turn into a loss", "Perda" in page.locator("#roi-net").inner_text(), page.locator("#roi-net").inner_text())
    check("roi keeps focus", page.evaluate("document.activeElement.dataset.roi") == "rework")
    rework.fill("15")
    page.screenshot(path=shots / "5-roi.png")

    page.click('[data-tab="como"]')
    check("limits are stated", "Os limites foram escolhidos vendo o teste" in page.locator("#view").inner_text())

    # Timed trial: fixed design, runs to the end, and exports every answer.
    page.goto(Path(sys.argv[1]).resolve().parent.joinpath("ensaio.html").as_uri())
    page.wait_for_selector("#intro")
    design = page.evaluate("({ n: window.ENSAIO_DATA.tickets.length, manual: window.ENSAIO_DATA.tickets.filter((t) => t.arm === 'manual').length })")
    check("trial has 40 tickets, 20 manual", design["n"] == 40 and design["manual"] == 20, str(design))
    page.click("#start-fresh")
    for _ in range(40):
        if page.locator("#use-suggestion").count():
            page.click("#use-suggestion")
        else:
            page.locator(".cat-button").first.click()
    check("trial ends with a summary", page.locator("#done").is_visible())
    answers = page.evaluate("JSON.parse(document.getElementById('trial-json').value).results.length")
    check("trial exports 40 answers", answers == 40, str(answers))

    mobile = browser.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark").new_page()
    mobile.on("pageerror", lambda e: errors.append(str(e)))
    mobile.goto(page_url)
    mobile.wait_for_selector("#live-lane")
    for tab in ("triagem", "lote", "diagnostico", "fluxo", "roi", "como"):
        mobile.click(f'[data-tab="{tab}"]')
        overflow = mobile.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        check(f"no horizontal scroll on phone: {tab}", overflow <= 0, str(overflow))

    check("no console errors", not errors, str(errors[:3]))
    browser.close()

print("\nFAILED:" if failures else "\nALL PASSED", failures or "")
sys.exit(1 if failures else 0)
