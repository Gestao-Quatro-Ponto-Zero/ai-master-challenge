"""Teste de ponta a ponta da tela do Lead Scorer, com cliques reais num navegador.

Uso:
    python fase4_teste_app.py <url_da_tela> <arquivo_json_do_motor> <pasta_prints>
Exemplo (app rodando localmente com `npm run dev`):
    python fase4_teste_app.py http://127.0.0.1:5173 ../../solution/motor/saida/deals_priorizados.json ../prints

Os valores esperados são calculados a partir do arquivo do motor, de forma independente da tela.
"""
import json
import re
import sys
from collections import Counter

from playwright.sync_api import sync_playwright

URL, JSON_MOTOR, PRINTS = sys.argv[1], sys.argv[2], sys.argv[3]
motor = json.load(open(JSON_MOTOR, encoding="utf-8"))
deals = motor["deals"]
LISTAS = ["Foco", "Requalificar ou encerrar", "Iniciar contato", "Automatizar"]
resultados = []


def check(nome, ok, detalhe=""):
    resultados.append((nome, bool(ok), detalhe))
    print(("✅" if ok else "❌"), nome, ("— " + detalhe if detalhe else ""))


def esperado(filtro=lambda d: True):
    sub = [d for d in deals if filtro(d)]
    return {
        "total": len(sub),
        "por_lista": Counter(d["lista"] for d in sub),
        "foco_top3": [d["id"] for d in sub if d["lista"] == "Foco"][:3],
        "soma_ev": round(sum(d["valor_esperado_usd"] for d in sub if d["lista"] == "Foco")),
    }


def fmt(n):
    return f"{n:,}".replace(",", ".")


def texto(page):
    return re.sub(r"\s+", " ", page.inner_text("body"))


def ids_visiveis(page, n=3):
    return re.findall(r"\d+º · ([A-Z0-9]{8})", page.inner_text("main"))[:n]


def escolher(page, rotulo, opcao):
    page.locator("label", has_text=rotulo).get_by_role("combobox").click()
    page.get_by_role("option", name=opcao, exact=True).click()
    page.wait_for_timeout(300)


with sync_playwright() as p:
    nav = p.chromium.launch()
    page = nav.new_page(viewport={"width": 1280, "height": 900})
    erros = []
    page.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    page.goto(URL)
    page.wait_for_selector("text=Avançar este deal", timeout=30000)
    T = texto(page)

    # 1. dados históricos em destaque
    data = "31/12/2017"
    check("Faixa histórica com a data de 31/12/2017",
          f"Dados históricos de demonstração: pipeline como estava em {data}. Não são dados atuais." in T)
    page.mouse.wheel(0, 5000); page.wait_for_timeout(300)
    faixa = page.get_by_text("Não são dados atuais").bounding_box()
    check("Faixa continua visível depois de rolar a página", faixa is not None and faixa["y"] < 60, f"y={faixa and round(faixa['y'])}")
    page.mouse.wheel(0, -5000)
    check("Nenhum 'hoje' ou 'agora' na tela", not re.search(r"\b(hoje|agora)\b", T, re.I))

    # 2. visão geral bate com o motor
    e = esperado()
    check("Subtítulo com total de deals", f"Situação em {data} · {fmt(e['total'])} deals abertos naquela data" in T)
    for l in LISTAS:
        check(f"Aba '{l}' com a contagem do motor", f"{l} ({e['por_lista'][l]})" in T, str(e["por_lista"][l]))
    check("Soma do valor esperado do Foco", f"US$ {fmt(e['soma_ev'])}" in T, f"US$ {fmt(e['soma_ev'])}")
    check("3 primeiros do Foco na ordem do motor", ids_visiveis(page) == e["foco_top3"], f"{ids_visiveis(page)}")
    d1 = next(d for d in deals if d["id"] == e["foco_top3"][0])
    check("'Porquê' do 1º deal idêntico ao do motor", d1["porque"] in T)
    check("Chance exibida = chance_texto do motor", f"Chance: {d1['chance_texto']}" in T, d1["chance_texto"])
    check("Aviso de empresa não cadastrada aparece", "Empresa não cadastrada: complete o cadastro no CRM" in T)

    # 3. filtro por vendedor (clique real)
    vend = "Zane Levy"
    escolher(page, "Vendedor", vend)
    e = esperado(lambda d: d["vendedor"] == vend)
    T = texto(page)
    check(f"Filtro '{vend}': total", f"{fmt(e['total'])} deals abertos naquela data" in T, str(e["total"]))
    check(f"Filtro '{vend}': contagens das 4 listas", all(f"{l} ({e['por_lista'][l]})" in T for l in LISTAS),
          str(dict(e["por_lista"])))
    check(f"Filtro '{vend}': 3 primeiros do Foco", ids_visiveis(page) == e["foco_top3"], f"{ids_visiveis(page)}")
    check(f"Filtro '{vend}': 1º deal aparece como '1º'", f"1º · {e['foco_top3'][0]}" in T)

    # 4. lista vazia
    if e["por_lista"]["Iniciar contato"] == 0:
        page.get_by_role("tab", name=re.compile(r"^Iniciar contato")).click(); page.wait_for_timeout(300)
        check("Mensagem de lista vazia", "Nenhum deal nesta lista para este filtro." in texto(page))

    # 5. cascata de filtros
    escolher(page, "Vendedor", "Todos")
    escolher(page, "Região", "East")
    page.locator("label", has_text="Gerente").get_by_role("combobox").click()
    gerentes = [o.inner_text().strip() for o in page.get_by_role("option").all()]
    page.keyboard.press("Escape")
    esp_ger = sorted({v["gerente"] for v in motor["vendedores"] if v["regiao"] == "East"})
    check("Cascata: gerentes da região East", gerentes[1:] == esp_ger, f"{gerentes[1:]}")
    e = esperado(lambda d: d["regiao"] == "East")
    check("Cascata: total da região East", f"{fmt(e['total'])} deals abertos naquela data" in texto(page), str(e["total"]))
    escolher(page, "Região", "Todos")

    # 6. requalificação e "mostrar mais"
    page.get_by_role("tab", name=re.compile(r"^Requalificar")).click(); page.wait_for_timeout(300)
    req = [d for d in deals if d["lista"] == "Requalificar ou encerrar"]
    T = texto(page)
    check("Requalificar: 1º deal do motor", f"1º · {req[0]['id']}" in T, req[0]["id"])
    check("Requalificar: 'Mostrar mais' com o restante certo", f"Mostrar mais ({len(req) - 25} restantes)" in T)
    page.get_by_role("button", name=re.compile(r"Mostrar mais")).click(); page.wait_for_timeout(300)
    check("'Mostrar mais' carrega mais 25", f"Mostrar mais ({len(req) - 50} restantes)" in texto(page))

    # 7. como a nota funciona
    page.get_by_role("tab", name="Como a nota funciona").click(); page.wait_for_timeout(500)
    T = texto(page)
    curva = {c["idade_dias"]: c["chance"] for c in motor["curva_chance"]}
    v = motor["validacao_volta_no_tempo"]
    check("Como funciona: chance aos 0 e 90 dias", f"ganhos {round(curva[0]*100)}% das vezes; com 90 dias, {round(curva[90]*100)}%" in T)
    check("Como funciona: limites US$ 100 e US$ 4.000", "US$ 100" in T and "US$ 4.000" in T)
    check("Como funciona: teste de volta no tempo",
          f"concentravam {round(v['captura_top20_nossa_logica']*100)}% da receita" in T and f"seriam {round(v['captura_top20_so_valor']*100)}%" in T)
    check("Como funciona: gráfico desenhado", page.locator(".recharts-line").count() > 0)
    page.get_by_role("tab", name=re.compile(r"^Foco")).click(); page.wait_for_timeout(300)
    page.screenshot(path=f"{PRINTS}/tela_teste_local_desktop.png", full_page=False)

    # 8. celular
    cel = nav.new_page(viewport={"width": 375, "height": 812}, is_mobile=True)
    cel.goto(URL); cel.wait_for_selector("text=Avançar este deal", timeout=30000)
    larg = cel.evaluate("document.documentElement.scrollWidth")
    check("Celular (375 px): sem rolagem horizontal", larg <= 376, f"largura do conteúdo = {larg}px")
    cel.screenshot(path=f"{PRINTS}/tela_teste_local_celular.png")

    check("Sem erros no console", not erros, "; ".join(erros)[:200])
    nav.close()

ok = sum(r[1] for r in resultados)
print(f"\nRESULTADO: {ok} de {len(resultados)} verificações aprovadas")
sys.exit(0 if ok == len(resultados) else 1)
