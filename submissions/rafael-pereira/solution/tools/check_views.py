"""Testes Playwright das visões por perfil (vendedor e manager), do tema e da acessibilidade (axe-core).

Uso (cwd = solution/):
    python tools/check_views.py [--skip-axe]

Cobre
- entrar como vendedor e NÃO ver outros vendedores (nem no HTML, nem nos filtros); trocar de perfil volta à entrada;
- ações (contatei, agendei, encerrar) salvas no localStorage, progresso e simulador "e se eu fechar este?";
- entrar como manager, ver só o próprio time, abrir um vendedor (modo leitura) e gerar/copiar a pauta do 1:1;
- totais da tela batendo com o data.js (todos os 35 vendedores, os 6 managers, modo hoje e modo teste);
- nenhuma taxa de vitória ou ranking por vendedor (decisão 4 do CLAUDE.md);
- alternância de tema (botão, preferência do sistema, persistência) e fontes auto-hospedadas carregadas;
- teclado, rolagem horizontal, alvos de toque;
- axe-core (tools/vendor/axe.min.js, 4.9.1, MPL-2.0) nas telas principais, nos dois temas e em 1280 e 390 px:
  zero violações serious/critical. O Lighthouse não roda aqui (sem Node).
Imprime PASSOU/FALHOU por checagem; exit 1 se algo falhar.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

from playwright.sync_api import sync_playwright

from check_app import CATS, Env, Report, launch, layout_problems, ready, run_check

sys.stdout.reconfigure(encoding="utf-8")

TOOLS = Path(__file__).resolve().parent
SOL = TOOLS.parent
APP = SOL / "app" / "index.html"
AXE = TOOLS / "vendor" / "axe.min.js"
BAD_IMPACT = ("serious", "critical")
ACT_KEYS = ["contatei", "agendei", "encerrar"]


def plus(name: str) -> str:
    return name.replace(" ", "+")


def load_data(env: Env) -> dict:
    with env.page("", profile="revops") as page:
        ready(page)
        return page.evaluate("window.LEAD_DATA")


def today(data: dict) -> dict:
    return [s for s in data["snapshots"] if s["mode"] == "hoje"][0]


def counts_of(snap: dict, **flt) -> dict[str, int]:
    out = {c: 0 for c in CATS}
    for d in snap["deals"]:
        if all(d[k] == v for k, v in flt.items()):
            out[d["cat"]] += 1
    return out


def tabs(page) -> dict[str, int]:
    return {c: int(page.get_attribute(f"[data-testid=count-{c}]", "data-count")) for c in CATS}


def goto(page, hash_: str) -> None:
    page.evaluate("(h) => { location.hash = h; }", "#" + hash_)
    page.wait_for_timeout(120)


def pick_agent(data: dict, want_cats=("Foque", "Reative"), manager: str | None = None) -> str:
    """Vendedor com deals em Foque e Reative (para testar ações e simulador)."""
    snap = today(data)
    c = Counter(d["agent"] for d in snap["deals"] if d["cat"] in want_cats and (manager is None or d["manager"] == manager))
    for name, _ in c.most_common():
        k = counts_of(snap, agent=name)
        if k["Foque"] and k["Reative"]:
            return name
    return c.most_common(1)[0][0]


# ----------------------------------------------------------------------------------------------- vendedor
def check_entrada(env: Env, data: dict):
    fails = []
    ag = "Rosalina Dieter"
    with env.page("", profile=None) as page:
        ready(page)
        for t in ("entry", "entry-agent", "entry-mgr", "enter-vendedor", "enter-manager", "enter-revops", "entry-note"):
            if not page.is_visible(f"[data-testid={t}]"):
                fails.append(f"{t} invisível na entrada")
        if "Quem é você" not in page.inner_text("[data-testid=entry]"):
            fails.append("sem 'Quem é você?'")
        note = page.inner_text("[data-testid=entry-note]")
        if "experiência, não de segurança" not in note:
            fails.append("aviso 'experiência, não de segurança' ausente na entrada")
        if page.is_visible("[data-testid=filter-agent]") or page.is_visible("[data-testid=deal-card]"):
            fails.append("a entrada mostra filtros ou deals")
        if page.is_visible("[data-testid=mode-select]"):
            fails.append("o seletor de modo aparece na entrada")
        # erro útil sem nome escolhido
        page.click("[data-testid=enter-vendedor]")
        if not page.locator("#entry-agent-err").count():
            fails.append("sem mensagem de erro ao entrar sem escolher o nome")
        page.select_option("[data-testid=entry-agent]", label=ag)
        page.click("[data-testid=enter-vendedor]")
        ready(page)
        h = page.evaluate("location.hash")
        if h != f"#perfil=vendedor&nome={plus(ag)}":
            fails.append(f"hash inesperado: {h!r}")
        if page.inner_text("[data-testid=who]") != ag:
            fails.append("identidade errada na barra de perfil")
        if page.text_content("[data-testid=eyebrow]") != "Minha semana":
            fails.append("título 'Minha semana' ausente")
        # lembra o último perfil, com try/catch: botão "Continuar como"
        page.click("[data-testid=switch-profile]")
        if page.evaluate("location.hash") not in ("", "#"):
            fails.append("trocar de perfil não limpou o hash")
        if not page.is_visible("[data-testid=entry]"):
            fails.append("trocar de perfil não voltou à entrada")
        if ag not in page.inner_text("[data-testid=entry-continue]"):
            fails.append("sem 'Continuar como' o último perfil")
        # perfil lembrado só no localStorage: abrir sem hash NÃO entra sozinho
        page.reload()
        ready(page)
        if not page.is_visible("[data-testid=entry]"):
            fails.append("abrir sem hash deveria mostrar a entrada")
        page.click("[data-testid=entry-continue]")
        ready(page)
        if page.inner_text("[data-testid=who]") != ag:
            fails.append("'Continuar como' não abriu o vendedor lembrado")
    with env.page("#vendedor=Rosalina+Dieter".lstrip("#"), profile=None) as page:   # link antigo
        ready(page)
        if not page.is_visible("[data-testid=filter-agent]"):
            fails.append("link antigo #vendedor= deveria abrir a visão completa")
    with env.page("perfil=vendedor&nome=Fulano+Inexistente", profile=None) as page:   # nome inválido
        ready(page)
        if not page.is_visible("[data-testid=entry]"):
            fails.append("nome inválido deveria voltar à entrada")
    return (not fails, "; ".join(fails) or "entrada com aviso de transparência, validação, 'Continuar como', hash e link antigo")


def check_vendedor_isolado(env: Env, data: dict):
    """O vendedor vê SÓ os próprios deals: contagens, cards, filtros, outros nomes."""
    snap = today(data)
    agents = data["people"]["agents"]
    fails = []
    with env.page(f"perfil=vendedor&nome={plus(agents[0]['name'])}", profile=None) as page:
        ready(page)
        for a in agents:
            goto(page, f"perfil=vendedor&nome={plus(a['name'])}")
            page.wait_for_function("(n) => document.querySelector('[data-testid=who]').textContent === n", arg=a["name"])
            want = counts_of(snap, agent=a["name"])
            if tabs(page) != want:
                fails.append(f"{a['name']}: abas {tabs(page)} != data.js {want}")
            if page.is_visible("[data-testid=filter-agent]") or page.is_visible("[data-testid=filter-manager]"):
                fails.append(f"{a['name']}: filtros de outros vendedores visíveis")
        # um vendedor com muitos deals: todo card é dele, e nenhum outro nome de vendedor aparece
        ag = pick_agent(data)
        goto(page, f"perfil=vendedor&nome={plus(ag)}")
        page.wait_for_function("(n) => document.querySelector('[data-testid=who]').textContent === n", arg=ag)
        page.click("[data-testid=tab-Limpe]")
        page.wait_for_timeout(100)
        owners = page.eval_on_selector_all("[data-testid=deal-card]", "els => els.map(e => e.dataset.id)")
        by_id = {d["id"]: d for d in snap["deals"]}
        if any(by_id[i]["agent"] != ag for i in owners):
            fails.append("há card de outro vendedor")
        body = page.inner_text("body") + page.inner_html("[data-testid=deal-card]")
        others = [a["name"] for a in agents if a["name"] != ag and a["name"] in body]
        if others:
            fails.append(f"nomes de outros vendedores na tela: {others[:3]}")
        if "Todos os vendedores" in page.inner_text("#session"):
            fails.append("texto 'Todos os vendedores' na visão do vendedor")
        # sem deals: estado vazio útil, na 2ª pessoa
        for a in [x for x in agents if not x["has_deals"]][:1]:
            goto(page, f"perfil=vendedor&nome={plus(a['name'])}")
            page.wait_for_function("(n) => document.querySelector('[data-testid=who]').textContent === n", arg=a["name"])
            msg = page.inner_text("[data-testid=empty-state]")
            if "Você não tem deals no CRM" not in msg or a["manager"] not in msg:
                fails.append(f"{a['name']}: estado vazio sem explicação útil: {msg[:80]!r}")
        closed = [x for x in agents if x["has_deals"] and x["n_open"] == 0]
        for a in closed[:1]:
            goto(page, f"perfil=vendedor&nome={plus(a['name'])}")
            page.wait_for_function("(n) => document.querySelector('[data-testid=who]').textContent === n", arg=a["name"])
            msg = page.inner_text("[data-testid=empty-state]")
            if "Você não tem deals abertos" not in msg:
                fails.append(f"{a['name']}: estado vazio de deals fechados ausente: {msg[:80]!r}")
    return (not fails, "; ".join(fails[:5]) or f"{len(agents)} vendedores: abas = data.js, só os próprios deals, sem filtros nem nomes de outros")


def check_vendedor_acoes(env: Env, data: dict):
    snap = today(data)
    ag = pick_agent(data)
    k = counts_of(snap, agent=ag)
    fails = []
    deals = [d for d in snap["deals"] if d["agent"] == ag]
    sales = [d for d in deals if d["cat"] in ("Foque", "Reative")]
    base = sum(d["ev"] for d in sales)
    with env.page(f"perfil=vendedor&nome={plus(ag)}", profile=None) as page:
        ready(page)
        total = int(page.inner_text("[data-testid=prog-total]").replace(".", ""))
        if total != k["Foque"] + k["Reative"]:
            fails.append(f"progresso total {total} != Foque+Reative {k['Foque'] + k['Reative']}")
        if int(page.get_attribute("[data-testid=week-value]", "data-value")) != round(base):
            fails.append(f"valor da semana {page.get_attribute('[data-testid=week-value]', 'data-value')} != soma de ev {round(base)}")
        if "só neste navegador" not in page.inner_text("[data-testid=save-note]"):
            fails.append("aviso 'salvo só neste navegador' ausente")
        first = page.locator("[data-testid=deal-card]").first
        did = first.get_attribute("data-id")
        d0 = [d for d in snap["deals"] if d["id"] == did][0]
        # contatei: feedback imediato e resumo atualizado
        first.locator("[data-testid=act-contatei]").click()
        if first.locator("[data-testid=act-contatei]").get_attribute("aria-pressed") != "true":
            fails.append("contatei não ficou pressionado")
        if "contatado" not in first.locator("[data-testid=card-marks]").inner_text():
            fails.append("sem selo 'contatado' no card")
        if page.inner_text("[data-testid=prog-done]") != "1":
            fails.append("o progresso não foi para 1")
        page.wait_for_timeout(120)
        if "contatado" not in page.text_content("[data-testid=live]"):
            fails.append("sem anúncio para leitor de tela")
        first.locator("[data-testid=act-agendei]").click()
        first.locator("[data-testid=act-encerrar]").click()
        if page.inner_text("[data-testid=prog-done]") != "1":
            fails.append("três marcas no mesmo deal contaram como mais de um tratado")
        first.locator("[data-testid=act-encerrar]").click()      # desmarca
        first.locator("[data-testid=act-agendei]").click()
        # persistência: localStorage
        stored = page.evaluate("localStorage.getItem('leadscorer:acoes:v1')")
        if not stored or did not in stored:
            fails.append("marcação não foi para o localStorage")
        page.reload()
        ready(page)
        again = page.locator(f"[data-testid=deal-card][data-id='{did}']")
        if again.locator("[data-testid=act-contatei]").get_attribute("aria-pressed") != "true" or page.inner_text("[data-testid=prog-done]") != "1":
            fails.append("a marcação não sobreviveu ao recarregar")
        # simulador: anima e soma (preço - esperado) ao valor da semana
        if d0["cat"] in ("Foque", "Reative"):
            again.locator("[data-testid=act-sim]").click()
            want = round(base + d0["price"] - d0["ev"])
            page.wait_for_function("(w) => Math.abs(Number(document.querySelector('[data-testid=week-value]').dataset.value) - w) <= 1", arg=want, timeout=3000)
            page.wait_for_timeout(700)                          # fim da contagem animada
            shown = page.inner_text("[data-testid=week-value]").replace("US$", "").replace(".", "").strip()
            if abs(int(shown) - want) > 1:
                fails.append(f"valor exibido {shown} != {want} depois da animação")
            if not page.is_visible("[data-testid=sim-clear]"):
                fails.append("sem 'Limpar simulação'")
            page.click("[data-testid=sim-clear]")
            if int(page.get_attribute("[data-testid=week-value]", "data-value")) != round(base):
                fails.append("Limpar simulação não voltou ao valor base")
        # teclado: Enter e Espaço nos botões de ação
        btn = page.locator(f"[data-testid=deal-card][data-id='{did}'] [data-testid=act-encerrar]")
        btn.focus()
        page.keyboard.press("Enter")
        on = btn.get_attribute("aria-pressed")
        page.keyboard.press("Space")
        off = btn.get_attribute("aria-pressed")
        if (on, off) != ("true", "false"):
            fails.append(f"teclado: Enter/Espaço no botão de ação deram {on}/{off}")
        # card expande com um clique e mostra o porquê
        card = page.locator(f"[data-testid=deal-card][data-id='{did}']")
        card.locator(".card-toggle").click()
        if card.locator("[data-testid=card-why] p:visible").count() < 2:
            fails.append("o card não mostrou o porquê ao expandir")
    # sem armazenamento (localStorage bloqueado): a página continua funcionando
    with env.page("", profile=None, collect=True) as page:
        page.add_init_script("Object.defineProperty(window, 'localStorage', {get() { throw new Error('bloqueado'); }});")
        page.goto(APP.resolve().as_uri() + f"#perfil=vendedor&nome={plus(ag)}")
        page.reload()
        ready(page)
        page.locator("[data-testid=deal-card]").first.locator("[data-testid=act-contatei]").click()
        if "valem só até fechar a página" not in page.inner_text("[data-testid=save-note]"):
            fails.append("sem aviso quando o localStorage falha")
    env.errors[:] = [e for e in env.errors if "bloqueado" not in e]
    return (not fails, "; ".join(fails[:5]) or f"{ag}: ações salvas e restauradas, progresso, simulador animado, teclado, localStorage bloqueado")


# ----------------------------------------------------------------------------------------------- manager
def check_manager(env: Env, data: dict):
    snap = today(data)
    people = data["people"]
    fails = []
    mgr = "Celia Rouche"
    team = sorted((a for a in people["agents"] if a["manager"] == mgr), key=lambda a: a["name"])
    other = [a for a in people["agents"] if a["manager"] != mgr]
    with env.page("", profile=None) as page:
        ready(page)
        page.select_option("[data-testid=entry-mgr]", value=mgr)
        page.click("[data-testid=enter-manager]")
        ready(page)
        if page.evaluate("location.hash") != f"#perfil=manager&nome={plus(mgr)}":
            fails.append("hash do manager inesperado")
        rows = page.eval_on_selector_all("[data-testid=team-map] tbody tr", "trs => trs.map(tr => tr.dataset.agent)")
        if sorted(rows) != [a["name"] for a in team]:
            fails.append(f"mapa com vendedores diferentes do time: {rows}")
        body = page.inner_text("body")
        leaked = [a["name"] for a in other if a["name"] in body]
        if leaked:
            fails.append(f"vendedores de outros times na tela: {leaked[:3]}")
        # contagens por vendedor e total do time = data.js
        tot = {c: 0 for c in CATS}
        for a in team:
            want = counts_of(snap, agent=a["name"])
            got = {c: int(page.locator(f"[data-agent='{a['name']}'] [data-testid=cell-{c}]").inner_text().replace(".", "")) for c in CATS}
            if got != want:
                fails.append(f"{a['name']}: mapa {got} != data.js {want}")
            for c in CATS:
                tot[c] += want[c]
        foot = {c: int(page.locator(f"[data-testid=team-map] tfoot [data-testid=cell-{c}]").inner_text().replace(".", "")) for c in CATS}
        if foot != tot or tot != counts_of(snap, manager=mgr):
            fails.append(f"total do time {foot} != data.js {counts_of(snap, manager=mgr)}")
        txt = page.inner_text("[data-testid=action-summary]")
        for c in ("Foque", "Reative", "Limpe"):
            if f"{tot[c]:,}".replace(",", ".") not in txt:
                fails.append(f"frase de resumo sem {tot[c]} ({c})")
        # decisão 4: nenhuma taxa de vitória ou porcentagem por vendedor no mapa
        if "%" in page.inner_text("[data-testid=team-map]") or re.search(r"win rate|taxa de vit", page.inner_text("[data-testid=team-map]"), re.I):
            fails.append("o mapa do time mostra porcentagem ou taxa de vitória")
        if "Higiene de carteira, não desempenho" not in page.inner_text("[data-testid=hygiene-note]"):
            fails.append("sem o rótulo 'higiene de carteira, não desempenho'")
        if page.is_visible("[data-testid=tab-Foque]") or page.is_visible("[data-testid=deal-card]"):
            fails.append("o manager vê cards antes de abrir um vendedor")
        # ordenação: por zumbis, desc; e de volta
        page.click("[data-testid=sort-Limpe]")
        order = page.eval_on_selector_all("[data-testid=team-map] tbody tr", "trs => trs.map(tr => tr.dataset.agent)")
        want_order = sorted(team, key=lambda a: (-counts_of(snap, agent=a["name"])["Limpe"], a["name"]))
        if order != [a["name"] for a in want_order]:
            fails.append(f"ordenar por zumbis: {order}")
        if page.get_attribute("[data-testid=sort-Limpe]", "data-sort") != "Limpe" or "ordem=Limpe" not in page.evaluate("location.hash"):
            fails.append("a ordenação não foi para o hash")
        if page.evaluate("document.activeElement.dataset.sort") != "Limpe":
            fails.append("o foco saiu do botão de ordenar")
        page.click("[data-testid=sort-Limpe]")
        order2 = page.eval_on_selector_all("[data-testid=team-map] tbody tr", "trs => trs.map(tr => tr.dataset.agent)")
        if order2 != list(reversed(order)) and sorted(order2) != sorted(order):
            fails.append("segundo clique não inverteu a ordem")
        page.click("[data-testid=sort-nome]")
        # abrir um vendedor: carteira em modo leitura
        ag = pick_agent(data) if pick_agent(data) in [a["name"] for a in team] else team[1]["name"]
        page.locator(f"[data-agent='{ag}'] [data-testid=open-agent]").click()
        if page.inner_text("[data-testid=wallet-title]") != f"Carteira de {ag}":
            fails.append("título da carteira errado")
        if tabs(page) != counts_of(snap, agent=ag):
            fails.append(f"abas da carteira {tabs(page)} != data.js")
        if page.locator("[data-testid=card-actions]").count() or page.locator("[data-testid=act-contatei]").count():
            fails.append("a carteira do manager tem botões de ação (deveria ser só leitura)")
        if "Modo leitura" not in page.text_content("[data-testid=wallet-head]"):
            fails.append("sem o rótulo 'Modo leitura'")
        ids = page.eval_on_selector_all("[data-testid=deal-card]", "els => els.map(e => e.dataset.id)")
        by = {d["id"]: d for d in snap["deals"]}
        if any(by[i]["agent"] != ag for i in ids):
            fails.append("a carteira aberta mostra deals de outro vendedor")
        # pauta
        page.click("[data-testid=pauta-btn]")
        if not page.is_visible("[data-testid=pauta]"):
            fails.append("a pauta não apareceu")
        k = counts_of(snap, agent=ag)
        push = page.locator("[data-testid=pauta-push] li").count()
        rescue = page.locator("[data-testid=pauta-rescue] li").count()
        if push != min(3, k["Foque"]) or rescue != min(3, k["Reative"]):
            fails.append(f"pauta com {push} a empurrar e {rescue} a resgatar (esperado {min(3, k['Foque'])} e {min(3, k['Reative'])})")
        if int(page.get_attribute("[data-testid=pauta-clean-n]", "data-n")) != k["Limpe"]:
            fails.append("a pauta não traz quantos limpar")
        want_ids = [d for d in snap["deals"] if d["agent"] == ag and d["cat"] == "Foque"][:3]
        titles = page.eval_on_selector_all("[data-testid=pauta-push] li .pauta-item-title", "els => els.map(e => e.textContent)")
        if titles != [f"{d['account'] or 'Conta não informada'} · {d['product']}" for d in want_ids]:
            fails.append(f"os deals a empurrar não são os 3 primeiros do Foque: {titles}")
        if "%" in page.inner_text("[data-testid=pauta-clean]"):
            fails.append("a pauta de limpeza mostra porcentagem")
        page.click("[data-testid=pauta-copy]")
        page.wait_for_function("() => document.querySelector('[data-testid=pauta-status]').textContent.length > 0", timeout=3000)
        st = page.inner_text("[data-testid=pauta-status]")
        if "copiada" not in st.lower() and "Selecione o texto" not in st:
            fails.append(f"'Copiar' sem retorno: {st!r}")
        # a pauta sobrevive a recarregar (hash) e fecha
        page.reload()
        ready(page)
        if not page.is_visible("[data-testid=pauta]"):
            fails.append("a pauta não voltou depois de recarregar")
        page.click("[data-testid=wallet-close]")
        if page.is_visible("[data-testid=wallet-head]") or "ver=" in page.evaluate("location.hash"):
            fails.append("'Voltar ao time' não fechou a carteira")
        # pauta direto pela linha
        page.locator(f"[data-agent='{team[0]['name']}'] [data-testid=row-pauta]").click()
        if not page.is_visible("[data-testid=pauta]") or team[0]["name"] not in page.inner_text("[data-testid=pauta]"):
            fails.append("o botão da linha não abriu a pauta do vendedor")
    # um manager não abre vendedor de outro time pelo endereço
    with env.page(f"perfil=manager&nome={plus(mgr)}&ver={plus(other[0]['name'])}&pauta=1", profile=None) as page:
        ready(page)
        if page.is_visible("[data-testid=wallet-head]") or other[0]["name"] in page.inner_text("body"):
            fails.append("ver= de outro time abriu a carteira")
    return (not fails, "; ".join(fails[:5]) or f"time de {mgr}: mapa = data.js, ordenação, carteira em leitura, pauta (3+3+limpar) e cópia")


def check_totais_managers_e_teste(env: Env, data: dict):
    fails, snaps = [], data["snapshots"]
    with env.page(f"perfil=manager&nome={plus(data['people']['managers'][0]['name'])}", profile=None) as page:
        ready(page)
        for snap in snaps:
            for m in data["people"]["managers"]:
                modo = "" if snap["mode"] == "hoje" else f"&modo={snap['date']}"
                goto(page, f"perfil=manager&nome={plus(m['name'])}{modo}")
                page.wait_for_function("(n) => document.querySelector('[data-testid=who]').textContent === n", arg=m["name"])
                page.wait_for_timeout(60)
                want = counts_of(snap, manager=m["name"])
                tot = {c: int(page.locator(f"[data-testid=team-map] tfoot [data-testid=cell-{c}]").inner_text().replace(".", "")) if not (snap["mode"] == "teste" and c == "Qualifique") else 0 for c in CATS}
                if snap["mode"] == "teste":
                    want["Qualifique"] = 0
                if tot != want:
                    fails.append(f"{m['name']} {snap['date']}: {tot} != {want}")
                if snap["mode"] == "teste":
                    for c in ("Foque", "Reative", "Limpe"):
                        ds = [d for d in snap["deals"] if d["manager"] == m["name"] and d["cat"] == c]
                        got = int(page.get_attribute(f"[data-testid=backtest-summary-{c}]", "data-n"))
                        won = int(page.get_attribute(f"[data-testid=backtest-summary-{c}]", "data-won"))
                        if got != len(ds) or won != sum(1 for d in ds if d["outcome"]["status"] == "Ganho"):
                            fails.append(f"{m['name']} {snap['date']} {c}: resultado {got}/{won} != data.js")
    # vendedor em modo teste: contagens, sem porcentagem
    ag = pick_agent(data)
    for snap in [s for s in snaps if s["mode"] == "teste"]:
        with env.page(f"perfil=vendedor&nome={plus(ag)}&modo={snap['date']}", profile=None) as page:
            ready(page)
            if page.locator("[data-testid=card-actions]").count():
                fails.append("ações aparecem no modo teste")
            if page.is_visible("[data-testid=stats]"):
                fails.append("progresso da semana aparece no modo teste")
            res = page.inner_text("[data-testid=backtest-results]")
            if "%" in res:
                fails.append(f"{snap['date']}: resumo do vendedor mostra porcentagem")
            want = counts_of(snap, agent=ag)
            want["Qualifique"] = 0
            if tabs(page) != want:
                fails.append(f"{snap['date']} {ag}: abas {tabs(page)} != {want}")
    return (not fails, "; ".join(fails[:5]) or f"{len(data['people']['managers'])} managers x {len(snaps)} fotos e vendedor em modo teste batem com o data.js")


def check_revops_preservada(env: Env, data: dict):
    fails = []
    snap = today(data)
    with env.page("", profile=None) as page:
        ready(page)
        page.click("[data-testid=enter-revops]")
        ready(page)
        if tabs(page) != {c: snap["summary"][c]["n"] for c in CATS}:
            fails.append("visão completa: abas != summary")
        for t in ("filter-agent", "filter-manager", "filter-region", "team-table"):
            if not page.is_visible(f"[data-testid={t}]") and t != "team-table":
                fails.append(f"{t} invisível na visão completa")
        txt = page.inner_text("[data-testid=how-transparency]") if page.is_visible("[data-testid=how-transparency]") else ""
        page.click("[data-testid=how-btn]")
        txt = page.inner_text("[data-testid=how-transparency]")
        if "experiência, não de segurança" not in txt or "ARQUITETURA_PRODUCAO" not in txt:
            fails.append("'Como funciona' sem a transparência sobre a separação")
    return (not fails, "; ".join(fails) or "visão completa com filtros e transparência no 'Como funciona'")


# ----------------------------------------------------------------------------------------------- tema e fontes
def check_tema(env: Env, data: dict):
    fails = []
    rgb = lambda page: page.evaluate("getComputedStyle(document.body).backgroundColor")  # noqa: E731
    with env.page("", profile=None, scheme="light") as page:
        ready(page)
        light = rgb(page)
        if light != "rgb(245, 244, 243)":
            fails.append(f"fundo claro {light} != off-white")
        label0 = page.get_attribute("[data-testid=theme-toggle]", "aria-label")
        page.click("[data-testid=theme-toggle]")
        page.wait_for_timeout(350)
        dark = rgb(page)
        if page.evaluate("document.documentElement.dataset.theme") != "dark" or dark != "rgb(3, 26, 38)":
            fails.append(f"alternar para escuro: data-theme/fundo = {page.evaluate('document.documentElement.dataset.theme')}/{dark}")
        if page.get_attribute("[data-testid=theme-toggle]", "aria-label") == label0:
            fails.append("o rótulo do botão de tema não mudou")
        if page.evaluate("localStorage.getItem('leadscorer:tema')") != "dark":
            fails.append("o tema não foi salvo")
        page.reload()
        ready(page)
        if page.evaluate("document.documentElement.dataset.theme") != "dark" or rgb(page) != "rgb(3, 26, 38)":
            fails.append("o tema escuro não persistiu ao recarregar")
        page.click("[data-testid=theme-toggle]")
        page.wait_for_timeout(350)
        if rgb(page) != "rgb(245, 244, 243)":
            fails.append("voltar ao claro falhou")
        # teclado
        page.focus("[data-testid=theme-toggle]")
        page.keyboard.press("Enter")
        page.wait_for_timeout(350)
        if page.evaluate("document.documentElement.dataset.theme") != "dark":
            fails.append("o botão de tema não responde ao Enter")
    with env.page("", profile=None, scheme="dark") as page:       # segue prefers-color-scheme, sem nada salvo
        ready(page)
        page.wait_for_timeout(350)
        if rgb(page) != "rgb(3, 26, 38)" or page.evaluate("document.documentElement.dataset.theme") not in (None, ""):
            fails.append(f"preferência escura do sistema ignorada: {rgb(page)}")
        page.click("[data-testid=theme-toggle]")                  # escolha explícita ganha do sistema
        page.wait_for_timeout(350)
        if rgb(page) != "rgb(245, 244, 243)":
            fails.append("a escolha explícita do claro não vale sobre o sistema escuro")
    with env.page("", profile=None, scheme="light") as page:      # sem armazenamento: renderiza e alterna
        page.add_init_script("Object.defineProperty(window, 'localStorage', {get() { throw new Error('bloqueado'); }});")
        page.goto(APP.resolve().as_uri())
        ready(page)
        page.click("[data-testid=theme-toggle]")
        page.wait_for_timeout(350)
        if rgb(page) != "rgb(3, 26, 38)":
            fails.append("sem localStorage o botão de tema não alterna")
    env.errors[:] = [e for e in env.errors if "bloqueado" not in e]
    return (not fails, "; ".join(fails) or "claro, escuro, preferência do sistema, escolha salva, teclado e localStorage bloqueado")


def check_fontes(env: Env, data: dict):
    fails = []
    with env.page(f"perfil=vendedor&nome={plus(pick_agent(data))}", profile=None) as page:
        ready(page)
        page.wait_for_timeout(400)
        loaded = page.evaluate("[...document.fonts].filter(f => f.status === 'loaded').map(f => f.family.replace(/\"/g, '') + ' ' + f.style)")
        for need in ("Manrope normal", "Libre Baskerville italic"):
            if need not in loaded:
                fails.append(f"fonte não carregada: {need} (carregadas: {loaded})")
        fam = page.evaluate("getComputedStyle(document.body).fontFamily")
        if not fam.startswith("Manrope"):
            fails.append(f"body não usa Manrope: {fam}")
        accent = page.evaluate("getComputedStyle(document.querySelector('.action-text .accent')).fontFamily")
        if "Libre Baskerville" not in accent:
            fails.append("a palavra editorial não usa Libre Baskerville")
        n = page.evaluate("getComputedStyle(document.querySelector('.tab-count')).fontVariantNumeric")
        if "tabular-nums" not in n:
            fails.append("números sem tabular-nums")
        # o itálico serifado nunca em números ou tabelas
        bad = page.evaluate("[...document.querySelectorAll('.accent')].filter(e => /\\d/.test(e.textContent) || e.closest('table')).length")
        if bad:
            fails.append("itálico editorial em número ou tabela")
    return (not fails, "; ".join(fails) or "Manrope e Libre Baskerville itálico carregadas de app/fonts (file://), tabular-nums, itálico só em palavras")


def check_layout_views(env: Env, data: dict):
    fails = []
    mgr = "Celia Rouche"
    ag = pick_agent(data, manager=mgr)
    scenes = [("entrada", "", None), ("vendedor", f"perfil=vendedor&nome={plus(ag)}", None),
              ("manager", f"perfil=manager&nome={plus(mgr)}", None), ("pauta", f"perfil=manager&nome={plus(mgr)}&ver={plus(ag)}&pauta=1", None)]
    for w, h in ((390, 844), (1280, 800)):
        for label, hs, _ in scenes:
            with env.page(hs, w, h, profile=None) as page:
                ready(page)
                fails += layout_problems(page, w, h, label)
                if label == "manager":
                    over = page.evaluate("(() => { const e = document.querySelector('.map-wrap'); return e.scrollWidth - e.clientWidth; })()")
                    if over > 1:
                        fails.append(f"manager@{w}: a tabela do mapa rola na horizontal ({over}px)")
                if label == "entrada" and w == 390:
                    box = page.locator("[data-testid=enter-vendedor]").bounding_box()
                    if box["y"] + box["height"] > h:
                        fails.append("entrada@390: o botão do vendedor fica abaixo da dobra")
    return (not fails, "; ".join(fails[:5]) or "sem rolagem horizontal, mapa sem rolagem em 1280, alvos de toque >= 44px nas 4 telas x 2 larguras")


# ----------------------------------------------------------------------------------------------- axe
def axe_scenes(data: dict):
    mgr = "Celia Rouche"
    ag = pick_agent(data, manager=mgr)
    empty = [a["name"] for a in data["people"]["agents"] if not a["has_deals"]][0]
    teste = [s for s in data["snapshots"] if s["mode"] == "teste"][0]["date"]

    def expand(page):
        c = page.locator("[data-testid=deal-card]").first
        c.locator(".card-toggle").click()
        c.locator("[data-testid=act-contatei]").click()
        c.locator("[data-testid=act-sim]").click()

    def pauta_copy(page):
        page.click("[data-testid=pauta-copy]")

    return [
        ("entrada", "", None),
        ("vendedor", f"perfil=vendedor&nome={plus(ag)}", None),
        ("vendedor-card-aberto-acao-simulacao", f"perfil=vendedor&nome={plus(ag)}", expand),
        ("vendedor-limpe", f"perfil=vendedor&nome={plus(ag)}&aba=Limpe", None),
        ("vendedor-sem-deals", f"perfil=vendedor&nome={plus(empty)}", None),
        ("vendedor-modo-teste", f"perfil=vendedor&nome={plus(ag)}&modo={teste}", None),
        ("manager", f"perfil=manager&nome={plus(mgr)}", None),
        ("manager-carteira-pauta", f"perfil=manager&nome={plus(mgr)}&ver={plus(ag)}&pauta=1", pauta_copy),
        ("visao-completa", "perfil=revops", None),
        ("visao-completa-modo-teste", f"perfil=revops&modo={teste}", None),
    ]


def run_axe(page) -> list[dict]:
    page.add_script_tag(path=str(AXE))
    page.add_style_tag(content="*, *::before, *::after { transition: none !important; animation: none !important; }")
    page.wait_for_timeout(150)
    return page.evaluate(
        """async () => {
          const r = await axe.run(document, { resultTypes: ['violations'] });
          return r.violations.map(v => ({ id: v.id, impact: v.impact, help: v.help, n: v.nodes.length,
                                         targets: v.nodes.slice(0, 3).map(n => n.target.join(' ') + ' | ' + (n.failureSummary || '').split('\\n')[1]) }));
        }""")


def check_axe(env: Env, data: dict, out: list):
    fails, minor, runs = [], [], 0
    for label, hs, extra in axe_scenes(data):
        for w, h in ((1280, 800), (390, 844)):
            for theme in ("claro", "escuro"):
                with env.page(hs, w, h, profile=None, collect=False, scheme="dark" if theme == "escuro" else "light") as page:   # o axe lê folhas de estilo por XHR e gera ruído em file://
                    ready(page)
                    page.evaluate(f"document.documentElement.setAttribute('data-theme', '{'dark' if theme == 'escuro' else 'light'}')")
                    if extra:
                        extra(page)
                    page.wait_for_timeout(400)
                    viol = run_axe(page)
                    runs += 1
                    for v in viol:
                        line = f"{label} {w}px {theme}: {v['id']} ({v['impact']}, {v['n']}x) {v['help']} -> {v['targets'][:1]}"
                        (fails if v["impact"] in BAD_IMPACT else minor).append(line)
    out.extend(minor)
    return (not fails, "; ".join(fails[:4]) or f"{runs} execuções do axe-core 4.9.1 (telas x 1280/390 x claro/escuro): zero violações serious ou critical; {len(minor)} de impacto menor")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--skip-axe", action="store_true")
    args = ap.parse_args()
    if not (APP.exists() and (SOL / "app" / "data.js").exists()):
        print("app/index.html ou app/data.js ausente: rode python -m scorer.build")
        return 2
    rep = Report()
    minor: list[str] = []
    with sync_playwright() as p:
        browser = launch(p)
        env = Env(browser, APP.resolve().as_uri())
        data = load_data(env)
        print(f"data.js: {len(data['snapshots'])} snapshots, {len(data['people']['agents'])} vendedores, {len(data['people']['managers'])} managers\n")
        run_check(rep, "entrada 'Quem é você?': validação, hash, 'Continuar como', link antigo, nome inválido", lambda: check_entrada(env, data))
        run_check(rep, "vendedor isolado: só os próprios deals, sem filtros nem outros nomes (35 vendedores)", lambda: check_vendedor_isolado(env, data))
        run_check(rep, "vendedor: ações no localStorage, progresso, simulador animado, teclado, storage bloqueado", lambda: check_vendedor_acoes(env, data))
        run_check(rep, "manager: só o time, mapa = data.js, ordenação, carteira em leitura e pauta do 1:1", lambda: check_manager(env, data))
        run_check(rep, "totais: 6 managers x 3 fotos e vendedor em modo teste = data.js (sem % por vendedor)", lambda: check_totais_managers_e_teste(env, data))
        run_check(rep, "visão completa preservada e transparência no 'Como funciona'", lambda: check_revops_preservada(env, data))
        run_check(rep, "tema: botão, preferência do sistema, persistência e teclado", lambda: check_tema(env, data))
        run_check(rep, "fontes auto-hospedadas e números tabulares", lambda: check_fontes(env, data))
        run_check(rep, "layout: sem rolagem horizontal, alvos de toque >= 44px", lambda: check_layout_views(env, data))
        if args.skip_axe:
            rep.add("axe-core nas telas principais, nos dois temas", None, "pulado (--skip-axe)")
        else:
            run_check(rep, "axe-core: zero violações serious/critical nos dois temas", lambda: check_axe(env, data, minor))
        errs = sorted(set(env.errors))
        rep.add("console: zero erros, pageerror e requestfailed (todas as páginas abertas)", not errs, "; ".join(errs[:5]) or "nenhum erro")
        browser.close()
    if minor:
        print("\nAxe, impacto menor (informativo):")
        for m in sorted(set(minor))[:15]:
            print("  - " + m)
    n_pass = sum(1 for s, _, _ in rep.rows if s == "PASSOU")
    print(f"\n{n_pass} passaram, {rep.failed} falharam, de {len(rep.rows)} checagens")
    print("RESULTADO: " + ("PASSOU" if rep.failed == 0 else "FALHOU"))
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
