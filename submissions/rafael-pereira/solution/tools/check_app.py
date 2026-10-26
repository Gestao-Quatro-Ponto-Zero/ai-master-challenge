"""Verifica a interface (app/index.html) abrindo-a em file:// com Playwright + Edge.

Uso (cwd = solution/):
    python tools/check_app.py --prefix antes|depois|final [--app-dir app] [--shots-dir DIR] [--skip-numbers]
                              [--agent "Nome do vendedor"]

O que faz
- Abre Path(app_dir, "index.html").resolve().as_uri() (sem servidor) e exige zero erros de console,
  pageerror e requestfailed em todas as páginas abertas.
- Checagens (a)-(f) do plano E7, mais checagens que dependem só do próprio data.js (contagens das abas
  contra `summary`, filtros contra uma recontagem a partir de `deals`, modo teste contra `outcome_summary`),
  cascata dos filtros, hash, teclado, "Mostrar mais", carteira do time, layout (rolagem horizontal, ação acima
  da dobra, alvos de toque), contraste AA dos tokens do CSS e ausência de números escritos à mão.
- As checagens numéricas que dependem de arquivos gerados depois (backtest_metrics.json,
  snapshot_<data>.csv, docs/SCORING.md) ficam nas funções numbers_*; --skip-numbers as pula. Sem a flag,
  arquivo ausente = FALHOU.
- Tira screenshots {prefix}_{vista}_{largura}.png (1280x800 e 390x844) das vistas inicio, vendedor,
  card-aberto, modo-teste e como-funciona.
- Imprime PASSOU/FALHOU por checagem; exit 1 se algo falhar.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import json
import re
import shutil
import sys
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

TOOLS_DIR = Path(__file__).resolve().parent
SOL = TOOLS_DIR.parent
SUB = SOL.parent
CATS = ["Foque", "Reative", "Limpe", "Qualifique"]
SIZES = [(1280, 800), (390, 844)]          # larguras do plano: desktop e celular
PAGE = 30                                   # cards por vez (especificado no plano E6 item 4)
MIN_TOUCH = 44                              # alvo de toque mínimo, em px
VIEWS = ["inicio", "vendedor", "card-aberto", "modo-teste", "como-funciona"]


# ---------------------------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------------------------
def fmt_int(n) -> str:
    return f"{int(round(n)):,}".replace(",", ".")


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def sort_key(name: str):
    return strip_accents(name).lower()


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def add(self, name: str, ok: bool | None, detail: str = "") -> None:
        status = "PULADO" if ok is None else ("PASSOU" if ok else "FALHOU")
        self.rows.append((status, name, detail))
        print(f"[{status}] {name}" + (f" - {detail}" if detail else ""), flush=True)

    @property
    def failed(self) -> int:
        return sum(1 for s, _, _ in self.rows if s == "FALHOU")


def run_check(rep: Report, name: str, fn) -> None:
    """Roda uma checagem que devolve (ok, detalhe); exceção vira FALHOU."""
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001 - qualquer erro do navegador é falha da checagem
        ok, detail = False, f"exceção {type(exc).__name__}: {str(exc).splitlines()[0][:300]}"
    rep.add(name, ok, detail)


# ---------------------------------------------------------------------------------------------
# dados do data.js
# ---------------------------------------------------------------------------------------------
def match(d: dict, agent=None, manager=None, region=None) -> bool:
    return ((not agent or d["agent"] == agent) and (not manager or d["manager"] == manager)
            and (not region or d["region"] == region))


def expected_counts(snap: dict, **flt) -> dict[str, int]:
    out = {c: 0 for c in CATS}
    for d in snap["deals"]:
        if match(d, **flt):
            out[d["cat"]] += 1
    return out


def snap_of(data: dict, mode: str) -> dict:
    return [s for s in data["snapshots"] if s["mode"] == mode][0]


def top_of(snap: dict, key: str) -> str:
    return Counter(d[key] for d in snap["deals"]).most_common(1)[0][0]


def pick_showcase_agent(snap: dict) -> str:
    """Vendedor que mais tem deals em Foque + Reative (mostra a tela principal); senão, o com mais deals."""
    c = Counter(d["agent"] for d in snap["deals"] if d["cat"] in ("Foque", "Reative"))
    return c.most_common(1)[0][0] if c else top_of(snap, "agent")


# ---------------------------------------------------------------------------------------------
# ambiente do navegador
# ---------------------------------------------------------------------------------------------
class Env:
    def __init__(self, browser, uri: str) -> None:
        self.browser = browser
        self.uri = uri
        self.errors: list[str] = []

    @contextlib.contextmanager
    def page(self, hash_: str = "", width: int = 1280, height: int = 800, collect: bool = True, uri: str | None = None,
             profile: str | None = "revops", scheme: str | None = None):
        """Abre a página. Por padrão entra na visão completa (perfil=revops), onde ficam os filtros e a carteira do time
        que estas checagens exercitam; passe profile=None para abrir a tela de entrada ("Quem é você?")."""
        if profile and "perfil=" not in hash_:
            hash_ = f"perfil={profile}" + (f"&{hash_}" if hash_ else "")
        ctx = self.browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme or "light")
        page = ctx.new_page()
        if collect:
            page.on("console", lambda m: self.errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
            page.on("pageerror", lambda e: self.errors.append(f"pageerror: {e}"))
            page.on("requestfailed", lambda r: self.errors.append(f"requestfailed: {r.url}"))
        page.goto((uri or self.uri) + (("#" + hash_) if hash_ else ""))
        try:
            yield page
        finally:
            ctx.close()


def ready(page) -> None:
    """A página montou: ou a tela de entrada está visível, ou a frase de ação tem texto."""
    page.wait_for_function(
        "() => { const en = document.querySelector('#entry'); if (en && !en.hidden) return true;"
        " const e = document.querySelector('[data-testid=action-summary]'); return !!e && e.textContent.trim().length > 0; }",
        timeout=15000)
    page.evaluate("document.fonts.ready")


def tab_counts(page) -> dict[str, int]:
    return {c: int(page.get_attribute(f"[data-testid=count-{c}]", "data-count")) for c in CATS}


def active_cat(page) -> str:
    return page.get_attribute("[role=tab][aria-selected=true]", "data-testid").replace("tab-", "")


def card_ids(page) -> list[str]:
    return page.eval_on_selector_all("[data-testid=deal-card]", "els => els.map(e => e.dataset.id)")


def select(page, testid: str, value: str) -> None:
    page.select_option(f"[data-testid={testid}]", value=value)


def option_values(page, testid: str) -> list[str]:
    vals = page.eval_on_selector_all(f"[data-testid={testid}] option", "els => els.map(e => e.value)")
    return [v for v in vals if v]


# ---------------------------------------------------------------------------------------------
# checagens que só dependem do data.js e da página
# ---------------------------------------------------------------------------------------------
def check_a_contagens_hoje(env: Env, data: dict):
    snap = snap_of(data, "hoje")
    with env.page() as page:
        ready(page)
        got, want = tab_counts(page), {c: snap["summary"][c]["n"] for c in CATS}
        fails = [] if got == want else [f"abas {got} != summary {want}"]
        txt = page.inner_text("[data-testid=action-summary]")
        for c, n in want.items():
            if n and fmt_int(n) not in txt:
                fails.append(f"frase de ação não contém {fmt_int(n)} ({c})")
        if want["Limpe"] and ("US$ " + fmt_int(snap["summary"]["Limpe"]["valor_tabela"])) not in txt:
            fails.append("frase de ação sem o valor parado de Limpe")
        return (not fails, "; ".join(fails) or f"abas = summary de {snap['date']}: {want}")


def check_filtros(env: Env, data: dict):
    snap = snap_of(data, "hoje")
    cases = [("vendedor", "filter-agent", {"agent": top_of(snap, "agent")}),
             ("manager", "filter-manager", {"manager": top_of(snap, "manager")}),
             ("região", "filter-region", {"region": top_of(snap, "region")})]
    fails, ok_txt = [], []
    for label, testid, flt in cases:
        with env.page() as page:
            ready(page)
            select(page, testid, list(flt.values())[0])
            got, want = tab_counts(page), expected_counts(snap, **flt)
            if got != want:
                fails.append(f"{label} {list(flt.values())[0]}: abas {got} != recontagem {want}")
                continue
            # ordem preservada: os primeiros cards da aba aberta são os primeiros do data.js filtrado
            cat = active_cat(page)
            exp_ids = [d["id"] for d in snap["deals"] if d["cat"] == cat and match(d, **flt)]
            ids = card_ids(page)
            if ids != exp_ids[:PAGE]:
                fails.append(f"{label}: cards da aba {cat} fora da ordem do data.js")
            ok_txt.append(f"{label}={list(flt.values())[0]} {want}")
    return (not fails, "; ".join(fails) or " | ".join(ok_txt))


def check_cascata(env: Env, data: dict):
    people = data["people"]
    regions = people["regions"]
    mgr_by_region = {r: sorted(m["name"] for m in people["managers"] if m["region"] == r) for r in regions}
    fails = []
    with env.page() as page:
        ready(page)
        r0 = regions[0]
        select(page, "filter-region", r0)
        if sorted(option_values(page, "filter-manager")) != mgr_by_region[r0]:
            fails.append(f"managers da região {r0} não batem")
        want_ag = sorted(a["name"] for a in people["agents"] if a["region"] == r0)
        if sorted(option_values(page, "filter-agent")) != want_ag:
            fails.append(f"vendedores da região {r0} não batem")
        m0 = mgr_by_region[r0][0]
        select(page, "filter-manager", m0)
        want_ag = sorted(a["name"] for a in people["agents"] if a["manager"] == m0)
        if sorted(option_values(page, "filter-agent")) != want_ag:
            fails.append(f"vendedores do manager {m0} não batem")
        ag = want_ag[0]
        select(page, "filter-agent", ag)
        # trocar o manager por outro derruba o vendedor que não pertence a ele
        others = [m for m in mgr_by_region[r0] if m != m0]
        if others:
            select(page, "filter-manager", others[0])
            if page.input_value("[data-testid=filter-agent]") != "":
                fails.append("vendedor ficou selecionado depois de trocar para outro manager")
        # região incompatível derruba o manager
        if len(regions) > 1:
            select(page, "filter-region", regions[1])
            if page.input_value("[data-testid=filter-manager]") not in ("",) and people_region(people, page.input_value("[data-testid=filter-manager]")) != regions[1]:
                fails.append("manager de outra região ficou selecionado")
        # Limpar zera os três filtros
        page.click("[data-testid=filter-clear]")
        vals = [page.input_value(f"[data-testid={t}]") for t in ("filter-agent", "filter-manager", "filter-region")]
        if any(vals):
            fails.append(f"Limpar não zerou os filtros: {vals}")
    return (not fails, "; ".join(fails) or "região -> manager -> vendedor em cascata; Limpar zera")


def people_region(people: dict, manager: str) -> str:
    return [m["region"] for m in people["managers"] if m["name"] == manager][0]


def check_hash(env: Env, data: dict):
    snap = snap_of(data, "hoje")
    ag = pick_showcase_agent(snap)
    fails = []
    with env.page() as page:
        ready(page)
        select(page, "filter-agent", ag)
        page.click("[data-testid=tab-Limpe]")
        h = page.evaluate("location.hash")
        if "vendedor=" not in h or "aba=Limpe" not in h:
            fails.append(f"hash não guarda o estado: {h!r}")
        want = tab_counts(page)
        page.reload()
        ready(page)
        if page.input_value("[data-testid=filter-agent]") != ag:
            fails.append("depois de recarregar, o vendedor não voltou")
        if active_cat(page) != "Limpe":
            fails.append("depois de recarregar, a aba não voltou")
        if tab_counts(page) != want:
            fails.append("contagens mudaram depois de recarregar")
    tests = [s for s in data["snapshots"] if s["mode"] == "teste"]
    if tests:
        with env.page(f"modo={tests[0]['date']}") as page:
            ready(page)
            if page.input_value("[data-testid=mode-select]") != tests[0]["date"]:
                fails.append("#modo=... não abriu o snapshot de teste")
            # editar o hash à mão (ou usar um link) também atualiza a tela
            page.evaluate("location.hash = '#perfil=revops&aba=Reative'")
            page.wait_for_function("(d) => document.querySelector('[data-testid=mode-select]').value !== d", arg=tests[0]["date"], timeout=5000)
            if active_cat(page) != "Reative":
                fails.append("mudar o hash à mão não trocou a aba")
    return (not fails, "; ".join(fails) or f"{h} restaura vendedor, aba e modo")


def check_c_modo_teste(env: Env, data: dict):
    fails, ok_txt = [], []
    for snap in [s for s in data["snapshots"] if s["mode"] == "teste"]:
        with env.page() as page:
            ready(page)
            select(page, "mode-select", snap["date"])
            if not page.is_visible("[data-testid=test-banner]"):
                fails.append(f"{snap['date']}: faixa 'Modo teste' ausente")
            want = {c: snap["summary"][c]["n"] for c in CATS}
            if tab_counts(page) != want:
                fails.append(f"{snap['date']}: abas {tab_counts(page)} != summary {want}")
            for c, o in snap["outcome_summary"].items():
                loc = f"[data-testid=backtest-summary-{c}]"
                n, pct = int(page.get_attribute(loc, "data-n")), float(page.get_attribute(loc, "data-pct"))
                if n != o["n"] or abs(pct - o["pct_ganhos"] * 100) > 0.051:
                    fails.append(f"{snap['date']} {c}: data-n/data-pct ({n}, {pct}) != outcome_summary ({o['n']}, {o['pct_ganhos'] * 100:.1f})")
            # selo de desfecho em cada card da lista aberta, coerente com o data.js
            cat = active_cat(page)
            by_id = {d["id"]: d for d in snap["deals"]}
            ids = card_ids(page)
            badges = page.eval_on_selector_all("[data-testid=deal-card]",
                                               "els => els.map(e => { const b = e.querySelector('[data-testid=outcome-badge]'); return b ? b.dataset.status : null; })")
            if not ids or any(b is None for b in badges):
                fails.append(f"{snap['date']}: card sem selo de desfecho")
            elif any(by_id[i]["outcome"]["status"] != b for i, b in zip(ids, badges)):
                fails.append(f"{snap['date']}: selo de desfecho diferente do data.js")
            # Qualifique indisponível
            page.click("[data-testid=tab-Qualifique]")
            msg = page.inner_text("[data-testid=empty-state]")
            if "Indisponível no modo teste" not in msg or page.locator("[data-testid=deal-card]").count() != 0:
                fails.append(f"{snap['date']}: aba Qualifique deveria estar indisponível")
            ok_txt.append(f"{snap['date']} {cat}: " + ", ".join(f"{c} n={o['n']} {o['pct_ganhos'] * 100:.1f}%" for c, o in snap["outcome_summary"].items()))
    return (not fails and bool(ok_txt), "; ".join(fails) or " | ".join(ok_txt))


def outcome_stats(snap: dict, **flt) -> dict[str, dict]:
    """n, ganhos e receita ganha por lista, recontados dos deals do snapshot de teste com os filtros dados."""
    out = {c: {"n": 0, "won": 0, "revenue": 0} for c in ("Foque", "Reative", "Limpe")}
    for d in snap["deals"]:
        if match(d, **flt) and d["cat"] in out:
            o = out[d["cat"]]
            o["n"] += 1
            if d["outcome"]["status"] == "Ganho":
                o["won"] += 1
                o["revenue"] += d["outcome"]["close_value"] or 0
    return out


def check_resumos_filtrados(env: Env, data: dict):
    """Modo teste: abas, frase de ação e resumos por lista (n, ganhos, receita) seguem os filtros e batem com a recontagem dos deals.
    Com um vendedor escolhido não pode haver porcentagem (sem taxa de vitória por vendedor)."""
    fails, ok_txt = [], []
    for snap in [s for s in data["snapshots"] if s["mode"] == "teste"]:
        cases = [("sem filtro", "", {}), ("manager", "filter-manager", {"manager": top_of(snap, "manager")}),
                 ("região", "filter-region", {"region": top_of(snap, "region")}),
                 ("vendedor", "filter-agent", {"agent": top_of(snap, "agent")})]
        for label, testid, flt in cases:
            with env.page(f"modo={snap['date']}") as page:
                ready(page)
                if testid:
                    select(page, testid, list(flt.values())[0])
                want = outcome_stats(snap, **flt)
                want_tabs = expected_counts(snap, **flt)
                if {c: v for c, v in tab_counts(page).items() if c != "Qualifique"} != {c: v for c, v in want_tabs.items() if c != "Qualifique"}:
                    fails.append(f"{snap['date']} {label}: abas {tab_counts(page)} != recontagem {want_tabs}")
                for c, w in want.items():
                    loc = f"[data-testid=backtest-summary-{c}]"
                    got = {k: page.get_attribute(loc, f"data-{k}") for k in ("n", "won", "revenue", "pct")}
                    if (int(got["n"]), int(got["won"]), round(float(got["revenue"]))) != (w["n"], w["won"], round(w["revenue"])):
                        fails.append(f"{snap['date']} {label} {c}: UI {got} != recontagem {w}")
                    if label == "vendedor":
                        if got["pct"] is not None or "%" in page.inner_text(loc):
                            fails.append(f"{snap['date']} vendedor {c}: o resumo mostra porcentagem (proibido: taxa de vitória por vendedor)")
                    elif w["n"] and (got["pct"] is None or abs(float(got["pct"]) - 100 * w["won"] / w["n"]) > 0.051):
                        fails.append(f"{snap['date']} {label} {c}: data-pct {got['pct']} != {100 * w['won'] / w['n']:.1f}")
                if label == "sem filtro":
                    for c, o in snap["outcome_summary"].items():
                        if (want[c]["n"], want[c]["won"]) != (o["n"], round(o["pct_ganhos"] * o["n"])):
                            fails.append(f"{snap['date']} {c}: recontagem != outcome_summary")
                if label != "sem filtro":
                    ok_txt.append(f"{snap['date']} {label}")
    return (not fails and bool(ok_txt), "; ".join(fails[:6]) or "resumos do modo teste recalculados com os filtros: " + ", ".join(ok_txt))


def check_optgroup(env: Env, data: dict):
    """O seletor 'Quem é você?' é agrupado por manager (optgroup), com os vendedores certos em cada grupo."""
    people = data["people"]
    fails = []
    with env.page() as page:
        ready(page)
        groups = page.eval_on_selector_all(
            "[data-testid=filter-agent] optgroup",
            "gs => gs.map(g => [g.label, [...g.querySelectorAll('option')].map(o => o.value)])")
        got = {label: vals for label, vals in groups}
        for m in people["managers"]:
            label = f"Time de {m['name']} — {m['region']}"
            want = sorted(a["name"] for a in people["agents"] if a["manager"] == m["name"])
            if label not in got:
                fails.append(f"sem optgroup '{label}'")
            elif sorted(got[label]) != want:
                fails.append(f"optgroup '{label}' com vendedores diferentes do cadastro")
        loose = page.eval_on_selector_all("[data-testid=filter-agent] > option", "os => os.map(o => o.value).filter(v => v)")
        if loose:
            fails.append(f"vendedores fora de optgroup: {loose[:3]}")
    return (not fails, "; ".join(fails) or f"{len(groups)} optgroups, um por manager, com os vendedores do time")


def check_sem_atencao(env: Env, data: dict):
    """A caixa 'Atenção' do Foque sumiu (a correção está na curva, não num aviso)."""
    fails = []
    for h in ("aba=Foque", "aba=Reative", "aba=Limpe"):
        with env.page(h) as page:
            ready(page)
            if page.locator("[data-testid=foque-warning]").count() or page.locator(".foque-warning").count():
                fails.append(f"{h}: elemento foque-warning ainda existe")
            if "Atenção" in page.inner_text("[data-testid=instruction]"):
                fails.append(f"{h}: a instrução ainda traz 'Atenção'")
    return (not fails, "; ".join(fails) or "sem caixa 'Atenção' nas abas Foque, Reative e Limpe")


def check_d_como_funciona(env: Env, data: dict):
    fails = []
    for snap in data["snapshots"][:2]:
        with env.page() as page:
            ready(page)
            select(page, "mode-select", snap["date"])
            page.click("[data-testid=how-btn]")
            if not page.is_visible("[data-testid=how-it-works] li"):
                fails.append(f"{snap['date']}: 'Como funciona' não abriu")
                continue
            lis = page.locator("[data-testid=how-it-works] li")
            n = lis.count()
            if n != 5:
                fails.append(f"{snap['date']}: {n} linhas em vez de 5")
            texts = [lis.nth(i).inner_text().strip() for i in range(n)]
            if texts != [t.strip() for t in snap["how_it_works"]]:
                fails.append(f"{snap['date']}: texto diferente do data.js")
    return (not fails, "; ".join(fails) or "abre com exatamente 5 linhas iguais ao data.js")


def check_e_card(env: Env, data: dict):
    snap = snap_of(data, "hoje")
    fails = []
    with env.page() as page:
        ready(page)
        first = page.locator("[data-testid=deal-card]").first
        d0 = [d for d in snap["deals"] if d["id"] == first.get_attribute("data-id")][0]
        txt0 = first.locator("[data-testid=card-why]").inner_text().strip()
        if txt0 != d0["why"][0]:
            fails.append("1ª frase do card diferente de why[0]")
        first.locator(".card-toggle").click()
        if first.locator(".card-toggle").get_attribute("aria-expanded") != "true":
            fails.append("aria-expanded não virou true")
        n = first.locator("[data-testid=card-why] p:visible").count()
        if not 2 <= n <= 4:
            fails.append(f"{n} frases visíveis (esperado 2 a 4)")
        detail = first.locator(".card-detail").inner_text()
        for must in (d0["id"], d0["agent"], d0["manager"]):
            if must not in detail:
                fails.append(f"detalhe sem {must}")
        if d0["engage_date"]:
            y, m, d = d0["engage_date"].split("-")
            if f"{d}/{m}/{y}" not in detail:
                fails.append("detalhe sem a data de engajamento dd/mm/aaaa")
        if d0["ev"] is not None and ("US$ " + fmt_int(d0["ev"])) not in detail:
            fails.append("detalhe sem o valor esperado")
        first.locator(".card-toggle").click()
        if first.locator(".card-toggle").get_attribute("aria-expanded") != "false" or first.locator("[data-testid=card-why] p:visible").count() != 1:
            fails.append("segundo clique não recolhe")
        # teclado: foco no botão + Enter e Espaço
        first.locator(".card-toggle").focus()
        page.keyboard.press("Enter")
        if first.locator(".card-toggle").get_attribute("aria-expanded") != "true":
            fails.append("Enter não expande o card")
        page.keyboard.press("Space")
        if first.locator(".card-toggle").get_attribute("aria-expanded") != "false":
            fails.append("Espaço não recolhe o card")
    return (not fails, "; ".join(fails) or f"card {d0['id']}: 1ª frase + expande com {len(d0['why'])} frases, detalhes e teclado")


def check_f_sem_deals(env: Env, data: dict):
    ags = [a for a in data["people"]["agents"] if not a["has_deals"]]
    if not ags:
        return False, "o data.js não traz vendedor sem deals (esperado: 5 no cadastro)"
    fails = []
    with env.page() as page:
        ready(page)
        labels = page.eval_on_selector_all("[data-testid=filter-agent] option", "els => els.map(e => e.textContent)")
        for a in ags:
            if not any(a["name"] in l and "(sem deals no CRM)" in l for l in labels):
                fails.append(f"{a['name']}: sem o sufixo '(sem deals no CRM)' no seletor")
            select(page, "filter-agent", a["name"])
            msg = page.inner_text("[data-testid=empty-state]") if page.is_visible("[data-testid=empty-state]") else ""
            if a["name"] not in msg or "não tem deals no CRM" not in msg:
                fails.append(f"{a['name']}: estado vazio explicativo ausente")
            if page.locator("[data-testid=deal-card]").count() != 0:
                fails.append(f"{a['name']}: não deveria haver cards")
            if any(tab_counts(page).values()):
                fails.append(f"{a['name']}: contagens deveriam ser zero")
        # vendedor com deals só fechados: aparece como 'sem deals abertos'
    closed_only = [a for a in data["people"]["agents"] if a["has_deals"] and a["n_open"] == 0]
    with env.page() as page:
        ready(page)
        for a in closed_only:
            select(page, "filter-agent", a["name"])
            msg = page.inner_text("[data-testid=empty-state]") if page.is_visible("[data-testid=empty-state]") else ""
            if "deals abertos" not in msg:
                fails.append(f"{a['name']}: esperado aviso 'sem deals abertos'")
    return (not fails, "; ".join(fails) or f"{len(ags)} vendedores sem deals e {len(closed_only)} só com fechados mostram o estado vazio")


def check_mostrar_mais(env: Env, data: dict):
    snap = snap_of(data, "hoje")
    cat = max(CATS, key=lambda c: snap["summary"][c]["n"])
    n = snap["summary"][cat]["n"]
    if n <= PAGE:
        return None, "nenhuma lista com mais de 30 deals neste data.js"
    with env.page() as page:
        ready(page)
        page.click(f"[data-testid=tab-{cat}]")
        first = len(card_ids(page))
        fails = []
        if first != PAGE:
            fails.append(f"{first} cards na 1ª página (esperado {PAGE})")
        page.click("[data-testid=show-more]")
        second = len(card_ids(page))
        if second != min(n, 2 * PAGE):
            fails.append(f"{second} cards depois de 'Mostrar mais' (esperado {min(n, 2 * PAGE)})")
        exp = [d["id"] for d in snap["deals"] if d["cat"] == cat][:second]
        if card_ids(page) != exp:
            fails.append("ordem dos cards diferente do data.js")
        label = page.inner_text("[data-testid=show-more]") if page.is_visible("[data-testid=show-more]") else ""
        return (not fails, "; ".join(fails) or f"{cat}: {first} -> {second} de {fmt_int(n)}; botão: {label!r}")


def check_carteira(env: Env, data: dict):
    snap = snap_of(data, "hoje")
    mgr = top_of(snap, "manager")
    ag_of = sorted([a for a in data["people"]["agents"] if a["manager"] == mgr], key=lambda a: sort_key(a["name"]))
    fails = []
    with env.page() as page:
        ready(page)
        if page.locator("[data-testid=team-table]").count() == 0:
            fails.append("sem 'Carteira do time' sem filtro")
        select(page, "filter-manager", mgr)
        rows = page.eval_on_selector_all("[data-testid=team-table] tbody tr",
                                         "trs => trs.map(tr => [tr.dataset.agent, [...tr.querySelectorAll('td')].map(td => td.textContent.trim()), tr.textContent])")
        if [r[0] for r in rows] != [a["name"] for a in ag_of]:
            fails.append("linhas da carteira fora de ordem alfabética ou incompletas")
        for (name, cells, text), a in zip(rows, ag_of):
            want = expected_counts(snap, agent=a["name"])
            got = dict(zip(CATS, [int(c) for c in cells]))
            if got != want:
                fails.append(f"carteira de {name}: {got} != {want}")
            if not a["has_deals"] and "Sem deals no CRM" not in text:
                fails.append(f"{name}: sem alerta 'Sem deals no CRM'")
        if "%" in page.inner_text("[data-testid=team-table]"):
            fails.append("a carteira do time mostra porcentagem (proibido: sem taxa de vitória)")
        # com um vendedor único, a carteira some
        select(page, "filter-agent", ag_of[0]["name"])
        if page.locator("[data-testid=team-table]").count() != 0:
            fails.append("a carteira deveria sumir com um vendedor único")
    return (not fails, "; ".join(fails) or f"time de {mgr}: {len(ag_of)} linhas em ordem alfabética, só contagens")


def check_sem_lixo(env: Env, data: dict):
    """Nenhuma tela mostra 'undefined', 'NaN' ou 'null' como texto."""
    bad = re.compile(r"\b(undefined|NaN|null|\[object)", re.I)
    fails = []
    snap_t = [s for s in data["snapshots"] if s["mode"] == "teste"]
    states = [("hoje", ""), ("hoje Reative", "aba=Reative"), ("hoje Limpe", "aba=Limpe"), ("hoje Qualifique", "aba=Qualifique")]
    if snap_t:
        states += [("teste", f"modo={snap_t[0]['date']}"), ("teste Reative", f"modo={snap_t[0]['date']}&aba=Reative")]
    for label, h in states:
        with env.page(h) as page:
            ready(page)
            page.click("[data-testid=how-btn]")
            page.locator("[data-testid=backtest-panel] summary").click()
            m = bad.search(page.inner_text("body"))
            if m:
                fails.append(f"{label}: aparece {m.group(0)!r}")
    return (not fails, "; ".join(fails) or f"{len(states)} telas sem undefined/NaN/null")


def check_teclado_abas(env: Env, data: dict):
    with env.page() as page:
        ready(page)
        page.click("[data-testid=tab-Foque]")
        page.focus("[data-testid=tab-Foque]")
        page.keyboard.press("ArrowRight")
        a = active_cat(page)
        page.keyboard.press("End")
        b = active_cat(page)
        ok = a == "Reative" and b == "Qualifique"
        return ok, f"ArrowRight -> {a}, End -> {b}"


# ---------------------------------------------------------------------------------------------
# checagens estáticas (sem navegador)
# ---------------------------------------------------------------------------------------------
def check_sem_numeros_a_mao(app_dir: Path):
    html = (app_dir / "index.html").read_text(encoding="utf-8")
    js = (app_dir / "app.js").read_text(encoding="utf-8")
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text).replace("1:1", "")     # "1:1" é o nome do ritual (pauta do 1:1), não um dado
    fails = []
    if re.search(r"\d", text):
        fails.append("dígitos no texto visível do index.html: " + ", ".join(sorted(set(re.findall(r"\S*\d\S*", text)))[:5]))
    for fname, src in (("index.html", html), ("app.js", js)):
        for pat, what in ((r"\d{2}/\d{2}/\d{4}", "data dd/mm/aaaa"), (r"US\$\s?\d", "valor em US$"), (r"\b\d+[.,]?\d*\s?%", "porcentagem")):
            if re.search(pat, src):
                fails.append(f"{fname}: {what} escrito à mão")
    # strings do app.js (texto que vai para a tela) sem números soltos
    offenders = []
    for s in js_strings(js):
        s2 = re.sub(r"&#\d+;", "", s)                      # entidades HTML (&#39;)
        if re.fullmatch(r"[01]", s2):                      # "0"/"1" estruturais (atributos, índices)
            continue
        s2 = s2.replace("1:1", "")                         # "1:1" é o nome do ritual (pauta do 1:1), não um dado
        if re.search(r"(?<![A-Za-z_-])\d", s2):            # dígito que não faz parte de um nome (l1, l2)
            offenders.append(s2[:50])
    if offenders:
        fails.append("strings do app.js com números soltos: " + "; ".join(sorted(set(offenders))[:6]))
    return (not fails, "; ".join(fails) or "nenhum número ou data escrito à mão no HTML/JS (só PAGE_SIZE, parâmetro de layout)")


def js_strings(src: str) -> list[str]:
    """Extrai o conteúdo dos literais de string de um JS simples (ignora comentários e literais de regex)."""
    out, i, n = [], 0, len(src)
    last = ""                                              # último caractere significativo (para distinguir / de regex)
    while i < n:
        c = src[i]
        if src.startswith("//", i):
            i = src.find("\n", i)
            i = n if i < 0 else i
        elif src.startswith("/*", i):
            i = src.find("*/", i) + 2
        elif c in "'\"`":
            j, buf = i + 1, []
            while j < n and src[j] != c:
                if src[j] == "\\":
                    buf.append(src[j:j + 2])
                    j += 2
                    continue
                buf.append(src[j])
                j += 1
            out.append("".join(buf))
            i, last = j + 1, "x"
        elif c == "/" and last in "(,=:[!&|?{};" + "":
            j, in_class = i + 1, False                     # literal de regex
            while j < n and (src[j] != "/" or in_class):
                if src[j] == "\\":
                    j += 1
                elif src[j] == "[":
                    in_class = True
                elif src[j] == "]":
                    in_class = False
                j += 1
            i, last = j + 1, "x"
        else:
            if not c.isspace():
                last = c
            i += 1
    return out


def check_contrato(data: dict):
    """Invariantes do data-contract.md que a interface assume (barato, só olha o data.js)."""
    fails = []
    snaps = data["snapshots"]
    people = data["people"]
    names = {a["name"] for a in people["agents"]}
    mgrs = {m["name"]: m["region"] for m in people["managers"]}
    if snaps[0]["mode"] != "hoje" or snaps[0]["date"] != data["meta"]["reference_date"]:
        fails.append("o 1º snapshot deve ser o 'hoje' e ter a data de referência")
    for a in people["agents"]:
        if a["manager"] not in mgrs or mgrs[a["manager"]] != a["region"]:
            fails.append(f"{a['name']}: manager/região inconsistentes com people.managers")
        if not a["has_deals"] and a["n_open"]:
            fails.append(f"{a['name']}: has_deals=false com n_open>0")
    hoje_counts = Counter(d["agent"] for d in snaps[0]["deals"])
    for a in people["agents"]:
        if hoje_counts.get(a["name"], 0) != a["n_open"]:
            fails.append(f"{a['name']}: n_open={a['n_open']} != deals do hoje ({hoje_counts.get(a['name'], 0)})")
    for s in snaps:
        if len(s["how_it_works"]) != 5:
            fails.append(f"{s['date']}: how_it_works com {len(s['how_it_works'])} linhas")
        ids = [d["id"] for d in s["deals"]]
        if len(ids) != len(set(ids)):
            fails.append(f"{s['date']}: ids repetidos")
        cats = Counter(d["cat"] for d in s["deals"])
        for c in CATS:
            if cats.get(c, 0) != s["summary"][c]["n"]:
                fails.append(f"{s['date']}: summary[{c}].n != deals")
            vt = sum(d["price"] for d in s["deals"] if d["cat"] == c)
            if abs(vt - s["summary"][c]["valor_tabela"]) > 0.5:
                fails.append(f"{s['date']}: summary[{c}].valor_tabela != soma de price")
        order = [CATS.index(d["cat"]) for d in s["deals"]]
        if order != sorted(order):
            fails.append(f"{s['date']}: deals fora do agrupamento por categoria")
        for d in s["deals"]:
            if d["agent"] not in names:
                fails.append(f"{d['id']}: agent fora de people.agents")
                break
            if not 2 <= len(d["why"]) <= 4:
                fails.append(f"{d['id']}: why com {len(d['why'])} frases")
                break
            if d["cat"] == "Qualifique" and (d["p"] is not None or d["score"] is not None or d["ev"] is not None):
                fails.append(f"{d['id']}: Qualifique com p/score/ev")
                break
            if s["mode"] == "teste" and d["outcome"] is None:
                fails.append(f"{d['id']}: snapshot de teste com outcome nulo")
                break
            if s["mode"] == "hoje" and d["outcome"] is not None:
                fails.append(f"{d['id']}: snapshot de hoje com outcome")
                break
        if s["mode"] == "teste":
            if "outcome_summary" not in s or any(s["outcome_summary"][c]["n"] != s["summary"][c]["n"] for c in ("Foque", "Reative", "Limpe")):
                fails.append(f"{s['date']}: outcome_summary ausente ou com n diferente de summary")
        elif "outcome_summary" in s:
            fails.append(f"{s['date']}: outcome_summary só existe no modo teste")
    for s in snaps:
        miss = [k for k in ("knot_days", "p_fresh", "limpe_after_days", "limpe_rule", "limpe_min_chance", "max_won_cycle_days") if k not in s["model"]]
        if miss:
            fails.append(f"{s['date']}: model sem {miss}")
        if not s["model"]["knot_days"] <= s["model"]["limpe_after_days"]:
            fails.append(f"{s['date']}: fim do Foque depois do fim do Reative")
    bt = data["backtest"]
    if not bt.get("metrics") or not bt.get("rows") or not bt.get("headline"):
        fails.append("backtest sem metrics, rows ou headline")
    return (not fails, "; ".join(fails[:6]) or f"{len(snaps)} snapshots, {sum(len(s['deals']) for s in snaps)} deals: invariantes do contrato ok")


def check_estrutura(app_dir: Path):
    """Funciona em file:// e no GitHub Pages: sem fetch, sem CDN, sem módulos ES, sem build."""
    html = (app_dir / "index.html").read_text(encoding="utf-8")
    js = (app_dir / "app.js").read_text(encoding="utf-8")
    css = (app_dir / "style.css").read_text(encoding="utf-8")
    fails = []
    for what, pat, src in (("fetch()", r"\bfetch\s*\(", js), ("XMLHttpRequest", r"XMLHttpRequest", js), ("import/export ES", r"(?m)^\s*(import|export)\s", js),
                           ("type=module", r"type\s*=\s*[\"']module", html), ("URL absoluta no JS", r"https?://", js),
                           ("URL absoluta no HTML", r"(src|href)\s*=\s*[\"'](https?:)?//", html), ("@import/url() externo no CSS", r"@import|url\(\s*[\"']?(https?:)?//", css)):
        if re.search(pat, src):
            fails.append(f"usa {what}")
    for what, pat in (("lang=\"pt-BR\"", r"<html[^>]*lang=\"pt-BR\""), ("meta charset utf-8", r"<meta charset=\"utf-8\">"), ("meta viewport", r"<meta name=\"viewport\""),
                      ("scripts clássicos data.js e app.js, nessa ordem", r"<script src=\"data\.js\"></script>\s*<script src=\"app\.js\"></script>")):
        if not re.search(pat, html):
            fails.append(f"index.html sem {what}")
    return (not fails, "; ".join(fails) or "sem fetch/CDN/módulos; lang, charset, viewport e scripts clássicos no lugar")


def check_testids(env: Env, data: dict):
    need = ["mode-select", "filter-agent", "filter-manager", "filter-region", "filter-clear", "action-summary", "how-it-works", "team-table", "deal-card", "card-why"]
    need += [f"{p}-{c}" for p in ("count", "tab") for c in CATS]
    missing = []
    with env.page() as page:
        ready(page)
        missing += [t for t in need if page.locator(f"[data-testid={t}]").count() == 0]
        if any(not page.get_attribute(f"[data-testid=count-{c}]", "data-count") for c in CATS):
            missing.append("data-count")
        if not page.get_attribute("[data-testid=deal-card]", "data-id"):
            missing.append("deal-card[data-id]")
    tests = [s for s in data["snapshots"] if s["mode"] == "teste"]
    if tests:
        with env.page(f"modo={tests[0]['date']}") as page:
            ready(page)
            for t in ["outcome-badge"] + [f"backtest-summary-{c}" for c in ("Foque", "Reative", "Limpe")]:
                if page.locator(f"[data-testid={t}]").count() == 0:
                    missing.append(t + " (modo teste)")
            for c in ("Foque", "Reative", "Limpe"):
                for attr in ("data-n", "data-pct"):
                    if not page.get_attribute(f"[data-testid=backtest-summary-{c}]", attr):
                        missing.append(f"backtest-summary-{c}[{attr}]")
    return (not missing, "faltam: " + ", ".join(missing) if missing else f"{len(need)} data-testid do plano presentes (e os do modo teste)")


def _lum(h: str) -> float:
    h = h.lstrip("#")
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _ratio(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def load_tokens(css: str) -> tuple[dict[str, str], dict[str, str]]:
    """Tokens de cor (#rrggbb) do tema claro (:root) e do escuro (:root[data-theme=dark], já com os do claro por baixo).
    O bloco do escuro dentro de @media (prefers-color-scheme: dark) tem de ter exatamente os mesmos valores."""
    tok = lambda block: dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", block))  # noqa: E731
    light = tok(re.search(r":root \{(.*?)\n\}", css, re.S).group(1))
    dark_over = tok(re.search(r':root\[data-theme="dark"\] \{(.*?)\n\}', css, re.S).group(1))
    media_over = tok(re.search(r'prefers-color-scheme: dark\) \{\s*:root:not\(\[data-theme="light"\]\) \{(.*?)\n  \}', css, re.S).group(1))
    if dark_over != media_over:
        raise AssertionError("o tema escuro explícito e o automático (prefers-color-scheme) têm tokens diferentes")
    return light, {**light, **dark_over}


# (texto ou elemento, fundo, mínimo, onde é usado). 4,5:1 para texto; 3:1 para elementos gráficos.
def contrast_pairs() -> list[tuple[str, str, float, str]]:
    pairs = [
        ("text", "bg", 4.5, "texto da página"), ("text", "surface", 4.5, "texto em cards"), ("text", "soft", 4.5, "texto em fundos suaves"),
        ("muted", "bg", 4.5, "texto secundário"), ("muted", "surface", 4.5, "texto secundário em cards"), ("muted", "soft", 4.5, "texto secundário em fundos suaves"),
        ("link", "bg", 4.5, "links"), ("link", "surface", 4.5, "links em cards"),
        ("focus", "bg", 3.0, "anel de foco na página"), ("focus", "surface", 3.0, "anel de foco em cards"), ("focus-hi", "hero", 3.0, "anel de foco na barra e no resumo"),
        ("control", "bg", 3.0, "borda de campos"), ("control", "surface", 3.0, "borda de campos e botões"),
        ("gold-ink", "gold", 4.5, "texto do botão primário"), ("gold", "hero", 3.0, "marca dourada na barra"),
        ("hero-text", "hero", 4.5, "texto da barra e do resumo"), ("hero-muted", "hero", 4.5, "texto secundário do resumo"),
        ("hero-accent", "hero", 4.5, "palavra editorial em itálico"),
        ("inv-text", "inv-bg", 4.5, "botão de ação marcado e etiqueta do perfil"),
        ("note-text", "note-bg", 4.5, "faixa do modo teste e avisos"), ("note-line", "note-bg", 3.0, "borda dos avisos"),
        ("bad", "surface", 4.5, "alertas em cards"), ("bad", "bg", 4.5, "alertas na página"),
        ("limpe-c", "border", 3.0, "barra de higiene sobre a trilha"),
    ]
    for c in ("foque", "reative", "limpe", "qualifique"):
        pairs += [(f"{c}-c", "surface", 4.5, f"{c}: texto em cards"), (f"{c}-c", "bg", 4.5, f"{c}: texto na página"),
                  (f"{c}-c", f"{c}-t", 4.5, f"{c}: texto no fundo suave"), ("text", f"{c}-t", 4.5, f"{c}: texto principal no fundo suave"),
                  ("muted", f"{c}-t", 4.5, f"{c}: texto secundário no fundo suave"), (f"{c}-l", "surface", 3.0, f"{c}: linha gráfica em cards"),
                  (f"{c}-l", "bg", 3.0, f"{c}: linha gráfica na página"), (f"{c}-h", "hero", 4.5, f"{c}: número sobre o marinho")]
    return pairs


def contrast_rows(css: str) -> list[tuple[str, str, str, float, float, float, str]]:
    """Linhas (a, b, onde, mínimo, razão no claro, razão no escuro, falha)."""
    light, dark = load_tokens(css)
    rows = []
    for a, b, need, where in contrast_pairs():
        for pal in (light, dark):
            if a not in pal or b not in pal:
                raise KeyError(f"token ausente no CSS: {a} ou {b}")
        rl, rd = _ratio(light[a], light[b]), _ratio(dark[a], dark[b])
        rows.append((a, b, where, need, rl, rd, "" if min(rl, rd) >= need else "FALHA"))
    return rows


def check_contraste(app_dir: Path):
    css = (app_dir / "style.css").read_text(encoding="utf-8")
    rows = contrast_rows(css)
    fails = [f"{a} em {b}: claro {rl:.2f}, escuro {rd:.2f} (< {need})" for a, b, _, need, rl, rd, bad in rows if bad]
    return (not fails, "; ".join(fails) or f"{len(rows)} pares de cor, claro e escuro, todos >= AA")


def check_sem_dados(env: Env, app_dir: Path):
    """Sem data.js, a página mostra a instrução 'Rode python -m scorer.build'."""
    tmp = Path(tempfile.mkdtemp(prefix="lead-scorer-nodata-"))
    try:
        for f in ("index.html", "style.css", "app.js"):
            shutil.copy(app_dir / f, tmp / f)
        with env.page(uri=(tmp / "index.html").resolve().as_uri(), collect=False) as page:
            page.wait_for_selector("[data-testid=no-data]", state="visible", timeout=10000)
            msg = page.inner_text("[data-testid=no-data]")
            ok = "python -m scorer.build" in msg and not page.is_visible("[data-testid=action-summary]")
            return ok, f"mensagem: {msg.splitlines()[-1]!r}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------------------------
# checagens numéricas (dependem de arquivos gerados depois: --skip-numbers as pula)
# ---------------------------------------------------------------------------------------------
def _find_cat_table(obj):
    """Procura {Foque: {...}, Reative: {...}, Limpe: {...}} (ou lista com chave de categoria) e devolve {cat: {...}}."""
    if isinstance(obj, dict):
        if all(c in obj and isinstance(obj[c], (dict, int, float)) for c in ("Foque", "Reative", "Limpe")):
            return {c: (v if isinstance(v, dict) else {"n": v}) for c, v in obj.items() if c in CATS}
        for v in obj.values():
            r = _find_cat_table(v)
            if r:
                return r
    elif isinstance(obj, list):
        rows = [x for x in obj if isinstance(x, dict)]
        key = next((k for k in ("categoria", "category", "cat") if rows and all(k in x for x in rows)), None)
        if key and {"Foque", "Reative", "Limpe"} <= {x[key] for x in rows}:
            return {x[key]: x for x in rows}
        for v in obj:
            r = _find_cat_table(v)
            if r:
                return r
    return None


def _pick(d: dict, keys: tuple[str, ...]):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _load_metrics(sol: Path) -> dict:
    p = sol / "data" / "processed" / "backtest_metrics.json"
    if not p.exists():
        raise FileNotFoundError(f"{p} não existe (rode python -m scorer.validate / scorer.build)")
    return json.loads(p.read_text(encoding="utf-8"))


def _load_snapshot_csv(sol: Path, date: str) -> list[dict]:
    p = sol / "data" / "processed" / f"snapshot_{date}.csv"
    if not p.exists():
        raise FileNotFoundError(f"{p} não existe (rode python -m scorer.build)")
    with p.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    norm = lambda s: strip_accents(s).strip().lower()  # noqa: E731
    cols = {norm(k): k for k in rows[0]} if rows else {}

    def col(*names):
        for n in names:
            if n in cols:
                return cols[n]
        raise KeyError(f"coluna {names} ausente em {p.name}; colunas: {list(rows[0])}")
    ka, km, kr, kc = col("vendedor", "agent", "sales_agent"), col("manager"), col("regiao", "region", "regional_office"), col("categoria", "cat", "category")
    return [{"agent": r[ka], "manager": r[km], "region": r[kr], "cat": r[kc]} for r in rows]


def numbers_a(env: Env, data: dict, sol: Path):
    """(a) contagens da UI = backtest_metrics.json['hoje'] e o bloco AUTO:scoring-hoje do SCORING.md."""
    m = _load_metrics(sol)
    cats = _find_cat_table(m.get("hoje", {}))
    if not cats:
        return False, "backtest_metrics.json['hoje'] sem tabela por categoria reconhecível (ajuste _find_cat_table)"
    want = {c: int(_pick(cats[c], ("n", "count", "contagem"))) for c in CATS if c in cats}
    with env.page() as page:
        ready(page)
        got = tab_counts(page)
    fails = [f"UI {got} != backtest_metrics {want}"] if any(got[c] != want.get(c) for c in want) else []
    scoring = SUB / "docs" / "SCORING.md"
    if not scoring.exists():
        fails.append(f"{scoring} não existe")
    else:
        mt = re.search(r"<!-- AUTO:scoring-hoje -->(.*?)<!-- /AUTO:scoring-hoje -->", scoring.read_text(encoding="utf-8"), re.S)
        if not mt:
            fails.append("bloco AUTO:scoring-hoje ausente no SCORING.md")
        else:
            for c, n in got.items():
                if fmt_int(n) not in mt.group(1):
                    fails.append(f"AUTO:scoring-hoje sem {fmt_int(n)} ({c})")
    return (not fails, "; ".join(fails) or f"UI = backtest_metrics['hoje'] = SCORING (AUTO:scoring-hoje): {got}")


def numbers_b(env: Env, data: dict, sol: Path):
    """(b) filtros da UI = o mesmo filtro aplicado ao snapshot_<hoje>.csv (vendedor com mais deals abertos, 1 manager, 1 região)."""
    date = snap_of(data, "hoje")["date"]
    rows = _load_snapshot_csv(sol, date)
    top = lambda k: Counter(r[k] for r in rows).most_common(1)[0][0]  # noqa: E731
    cases = [("vendedor", "filter-agent", "agent"), ("manager", "filter-manager", "manager"), ("região", "filter-region", "region")]
    fails, ok_txt = [], []
    for label, testid, key in cases:
        val = top(key)
        want = {c: sum(1 for r in rows if r[key] == val and r["cat"] == c) for c in CATS}
        with env.page() as page:
            ready(page)
            select(page, testid, val)
            got = tab_counts(page)
        if got != want:
            fails.append(f"{label} {val}: UI {got} != CSV {want}")
        else:
            ok_txt.append(f"{label}={val}")
    return (not fails, "; ".join(fails) or "UI = " + date + " CSV para " + ", ".join(ok_txt))


def numbers_c(env: Env, data: dict, sol: Path):
    """(c) no modo de cada corte da UI, data-n/data-pct = categorias do corte em backtest_metrics.json."""
    m = _load_metrics(sol)
    cuts = m.get("cuts")
    if not isinstance(cuts, list):
        return False, "backtest_metrics.json sem a lista 'cuts'"
    fails, ok_txt = [], []
    for snap in [s for s in data["snapshots"] if s["mode"] == "teste"]:
        cut = next((c for c in cuts if snap["date"] in [str(v) for v in c.values() if isinstance(v, str)]), None)
        if cut is None:
            fails.append(f"corte {snap['date']} ausente em backtest_metrics.json")
            continue
        cats = _find_cat_table(cut)
        if not cats:
            fails.append(f"corte {snap['date']}: tabela de categorias não reconhecida (ajuste _find_cat_table)")
            continue
        with env.page() as page:
            ready(page)
            select(page, "mode-select", snap["date"])
            for c in ("Foque", "Reative", "Limpe"):
                loc = f"[data-testid=backtest-summary-{c}]"
                n, pct = int(page.get_attribute(loc, "data-n")), float(page.get_attribute(loc, "data-pct"))
                want_n = _pick(cats[c], ("n", "count"))
                want_pct = _pick(cats[c], ("pct_ganhos", "pct_won", "win_rate", "taxa_ganho", "pct_won_of_all"))
                if want_n is None or want_pct is None:
                    fails.append(f"{snap['date']} {c}: chaves n/pct_ganhos não encontradas em {list(cats[c])}")
                    continue
                want_pct = want_pct * 100 if want_pct <= 1 else want_pct
                if n != int(want_n) or abs(pct - want_pct) > 0.051:
                    fails.append(f"{snap['date']} {c}: UI ({n}, {pct}) != JSON ({want_n}, {want_pct:.1f})")
                else:
                    ok_txt.append(f"{snap['date']} {c} ({n}, {pct})")
    return (not fails, "; ".join(fails) or "UI = categorias dos cortes: " + ", ".join(ok_txt))


# ---------------------------------------------------------------------------------------------
# layout + screenshots
# ---------------------------------------------------------------------------------------------
def layout_problems(page, width: int, height: int, label: str, above_fold: bool = False, fold_testid: str = "action-summary") -> list[str]:
    out = []
    sw = page.evaluate("document.documentElement.scrollWidth")
    if sw > width:
        out.append(f"{label}@{width}: rolagem horizontal (scrollWidth {sw} > {width})")
    if above_fold:
        box = page.locator(f"[data-testid={fold_testid}]").first.bounding_box()
        if not box or box["y"] + box["height"] > height:
            out.append(f"{label}@{width}: [{fold_testid}] abaixo da dobra (termina em y={box and round(box['y'] + box['height'])}, dobra={height})")
    small = page.evaluate(
        """() => [...document.querySelectorAll('button, select, summary, [role=tab]')]
            .filter(e => e.offsetParent !== null && !e.closest('[hidden]'))
            .map(e => { const r = e.getBoundingClientRect(); return [e.getAttribute('data-testid') || e.id || e.textContent.trim().slice(0, 20), r.width, r.height]; })
            .filter(x => x[1] > 0 && (x[1] < 43.5 || x[2] < 43.5))""")
    if small:
        out.append(f"{label}@{width}: alvos de toque < {MIN_TOUCH}px: " + ", ".join(f"{n} ({w:.0f}x{h:.0f})" for n, w, h in small[:5]))
    return out


def screenshots(env: Env, data: dict, shots_dir: Path, prefix: str, agent: str | None) -> tuple[list[str], list[str]]:
    shots_dir.mkdir(parents=True, exist_ok=True)
    snap = snap_of(data, "hoje")
    ag = agent or pick_showcase_agent(snap)
    tests = [s for s in data["snapshots"] if s["mode"] == "teste"]
    layout, files = [], []

    def shot(page, view, w):
        page.mouse.move(0, 0)                                  # tira o hover do último clique da imagem
        p = shots_dir / f"{prefix}_{view}_{w}.png"
        page.screenshot(path=str(p))
        files.append(p.name)

    me = "perfil=vendedor&nome=" + ag.replace(" ", "+")
    for w, h in SIZES:
        with env.page("", w, h, profile=None) as page:         # inicio = tela de entrada "Quem é você?"
            ready(page)
            layout += layout_problems(page, w, h, "inicio", above_fold=True, fold_testid="enter-vendedor")
            shot(page, "inicio", w)
        with env.page(me, w, h, profile=None) as page:         # vendedor ("Minha semana")
            ready(page)
            layout += layout_problems(page, w, h, "vendedor", above_fold=True)
            shot(page, "vendedor", w)
            card = page.locator("[data-testid=deal-card]").first          # card-aberto (mesmo vendedor)
            if card.count():
                card.locator(".card-toggle").click()
                card.evaluate("e => e.scrollIntoView({block: 'start'})")
                page.evaluate("window.scrollBy(0, -70)")
            layout += layout_problems(page, w, h, "card-aberto")
            shot(page, "card-aberto", w)
        if tests:
            with env.page(f"{me}&modo={tests[0]['date']}", w, h, profile=None) as page:   # modo-teste (como vendedor)
                ready(page)
                layout += layout_problems(page, w, h, "modo-teste", above_fold=True)
                shot(page, "modo-teste", w)
        with env.page("", w, h) as page:                       # como-funciona
            ready(page)
            page.click("[data-testid=how-btn]")
            layout += layout_problems(page, w, h, "como-funciona")
            shot(page, "como-funciona", w)
            page.locator("[data-testid=backtest-panel] summary").click()
            page.locator("[data-testid=backtest-panel]").evaluate("e => e.scrollIntoView({block: 'start'})")
            layout += layout_problems(page, w, h, "teste-no-passado")
    return layout, files


# ---------------------------------------------------------------------------------------------
def launch(p):
    try:
        return p.chromium.launch(channel="msedge", headless=True)
    except Exception as exc:  # noqa: BLE001
        print(f"Edge indisponível ({str(exc).splitlines()[0]}); usando o Chromium do Playwright.")
        return p.chromium.launch(headless=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--prefix", required=True, help="prefixo dos PNGs: antes | depois | final | ...")
    ap.add_argument("--app-dir", default="app", help="pasta com index.html (padrão: app, em relação a solution/)")
    ap.add_argument("--shots-dir", default=str(SUB / "process-log" / "screenshots"))
    ap.add_argument("--skip-numbers", action="store_true", help="pula as checagens que dependem de arquivos gerados depois")
    ap.add_argument("--agent", default=None, help="vendedor das vistas 'vendedor'/'card-aberto' (padrão: o com mais Foque+Reative)")
    args = ap.parse_args()

    app_dir = Path(args.app_dir)
    if not app_dir.is_absolute() and not (app_dir / "index.html").exists():
        app_dir = SOL / app_dir
    app_dir = app_dir.resolve()
    if not (app_dir / "index.html").exists():
        print(f"index.html não encontrado em {app_dir}")
        return 2
    if not (app_dir / "data.js").exists():
        print(f"{app_dir / 'data.js'} não existe: rode python -m scorer.build (a interface mostra o aviso, mas não há o que checar)")
        return 2
    uri = (app_dir / "index.html").resolve().as_uri()
    rep = Report()
    print(f"app: {uri}\nsaída dos PNGs: {args.shots_dir}  prefixo: {args.prefix}\n")

    run_check(rep, "estático: nenhum número escrito à mão no HTML/JS", lambda: check_sem_numeros_a_mao(app_dir))
    run_check(rep, "estático: contraste AA dos tokens de cor (claro e escuro)", lambda: check_contraste(app_dir))
    run_check(rep, "estático: funciona em file:// (sem fetch, CDN ou módulos) e HTML bem formado", lambda: check_estrutura(app_dir))

    with sync_playwright() as p:
        browser = launch(p)
        env = Env(browser, uri)
        with env.page() as page:
            ready(page)
            data = page.evaluate("window.LEAD_DATA")
        n_deals = sum(len(s["deals"]) for s in data["snapshots"])
        print(f"data.js: {len(data['snapshots'])} snapshots, {n_deals} deals, {len(data['people']['agents'])} vendedores\n")

        run_check(rep, "data.js obedece ao data-contract.md (somas, ordem, nulos, outcome)", lambda: check_contrato(data))
        run_check(rep, "data-testid do plano presentes (modo hoje e modo teste)", lambda: check_testids(env, data))
        run_check(rep, "(a) sem filtro, modo hoje: abas = summary do data.js e frase de ação", lambda: check_a_contagens_hoje(env, data))
        run_check(rep, "(b) filtros vendedor/manager/região = recontagem do data.js (ordem preservada)", lambda: check_filtros(env, data))
        run_check(rep, "filtros em cascata (região > manager > vendedor) e Limpar", lambda: check_cascata(env, data))
        run_check(rep, "estado no location.hash (vendedor, aba, modo) sobrevive a recarregar", lambda: check_hash(env, data))
        run_check(rep, "(c) modo teste: data-n/data-pct = outcome_summary; selos; Qualifique indisponível", lambda: check_c_modo_teste(env, data))
        run_check(rep, "modo teste: resumos por lista seguem os filtros (sem % por vendedor)", lambda: check_resumos_filtrados(env, data))
        run_check(rep, "seletor de vendedores agrupado por manager (optgroup)", lambda: check_optgroup(env, data))
        run_check(rep, "sem a caixa 'Atenção' no Foque", lambda: check_sem_atencao(env, data))
        run_check(rep, "(d) 'Como funciona' abre com exatamente 5 linhas", lambda: check_d_como_funciona(env, data))
        run_check(rep, "(e) 1º card expande (2 a 4 frases, detalhes) e funciona por teclado", lambda: check_e_card(env, data))
        run_check(rep, "(f) vendedor sem deals mostra o estado vazio explicativo", lambda: check_f_sem_deals(env, data))
        run_check(rep, "'Mostrar mais' acrescenta a próxima página na mesma ordem", lambda: check_mostrar_mais(env, data))
        run_check(rep, "'Carteira do time': só contagens, ordem alfabética, some com vendedor único", lambda: check_carteira(env, data))
        run_check(rep, "abas navegáveis por setas/Home/End", lambda: check_teclado_abas(env, data))
        run_check(rep, "nenhuma tela mostra undefined/NaN/null", lambda: check_sem_lixo(env, data))
        run_check(rep, "sem data.js: aviso 'Rode python -m scorer.build'", lambda: check_sem_dados(env, app_dir))

        if args.skip_numbers:
            for name in ("(a) contagens = backtest_metrics.json['hoje'] e SCORING.md", "(b) filtros = snapshot_<hoje>.csv", "(c) modo teste = cortes do backtest_metrics.json"):
                rep.add("numérica " + name, None, "pulado (--skip-numbers)")
        else:
            run_check(rep, "numérica (a) contagens = backtest_metrics.json['hoje'] e SCORING.md", lambda: numbers_a(env, data, SOL))
            run_check(rep, "numérica (b) filtros = snapshot_<hoje>.csv", lambda: numbers_b(env, data, SOL))
            run_check(rep, "numérica (c) modo teste = cortes do backtest_metrics.json", lambda: numbers_c(env, data, SOL))

        try:
            layout, files = screenshots(env, data, Path(args.shots_dir), args.prefix, args.agent)
            rep.add("layout: sem rolagem horizontal, ação acima da dobra, alvos de toque >= 44px", not layout, "; ".join(layout) or "1280x800 e 390x844 em 5 vistas")
            rep.add(f"screenshots {args.prefix}_<vista>_<largura>.png", len(files) >= len(VIEWS) * len(SIZES) - (0 if any(s["mode"] == "teste" for s in data["snapshots"]) else 2),
                    f"{len(files)} arquivos em {args.shots_dir}")
        except Exception as exc:  # noqa: BLE001
            rep.add("layout e screenshots", False, f"exceção {type(exc).__name__}: {str(exc).splitlines()[0][:300]}")

        errs = sorted(set(env.errors))
        rep.add("console: zero erros, pageerror e requestfailed (todas as páginas abertas)", not errs,
                "; ".join(errs[:5]) or "nenhum erro")
        browser.close()

    n_pass = sum(1 for s, _, _ in rep.rows if s == "PASSOU")
    n_skip = sum(1 for s, _, _ in rep.rows if s == "PULADO")
    print(f"\n{n_pass} passaram, {rep.failed} falharam, {n_skip} puladas, de {len(rep.rows)} checagens")
    print("RESULTADO: " + ("PASSOU" if rep.failed == 0 else "FALHOU"))
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
