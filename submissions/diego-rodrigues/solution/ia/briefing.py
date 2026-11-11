"""Fatos para o briefing, templates deterministas, e `gerar` (por ora, só template)."""
from __future__ import annotations

import os
from datetime import datetime

from ia.validar import preencher, validar

MODELO_PADRAO = "claude-sonnet-5-5"


def fatos_vendedor(scored: dict, vendedor: str) -> dict:
    v = next(x for x in scored["vendedores"] if x["vendedor"] == vendedor)
    deals = [d for d in scored["deals"] if d["vendedor"] == vendedor]
    foco = sorted((d for d in deals if d.get("em_foco")), key=lambda d: d["posicao"])[:5]
    ve_trimestre = sum(d.get("ve_trimestre") or 0 for d in deals)
    return {
        "nome": vendedor,
        "semana_do_trimestre": scored["semana_do_trimestre"],
        "n_fechar": v["por_fila"]["fechar"],
        "n_preparar": v["por_fila"]["preparar"],
        "n_iniciar": v["por_fila"]["iniciar"],
        "n_encerrar": v["por_fila"]["encerrar"],
        "valor_encerrar": v["valor_por_fila"]["encerrar"],
        "ve_trimestre": ve_trimestre,
        "sem_nada_vivo": v["vivos"] == 0,
        "foco": [
            {
                "produto": d["produto"], "conta": d["conta"], "valor": d["valor_tabela"],
                "idade": d["idade"], "dias_restantes": d["dias_restantes"], "fila": d["fila"],
            }
            for d in foco
        ],
    }


def fatos_gestor(scored: dict, gerente: str) -> dict:
    vendedores = [v for v in scored["vendedores"] if v["gerente"] == gerente]
    por_gerente = scored["time"]["por_gerente"].get(gerente, {})
    sem_deal = sum(1 for v in vendedores if not v["tem_deal"])
    return {
        "gerente": gerente,
        "semana_do_trimestre": scored["semana_do_trimestre"],
        "vendedores": len(vendedores),
        "vendedores_sem_deal": sem_deal,
        "n_fechar": sum(v["por_fila"]["fechar"] for v in vendedores),
        "n_encerrar": sum(v["por_fila"]["encerrar"] for v in vendedores),
        "valor_aberto": por_gerente.get("valor_aberto", 0.0),
        "valor_vivo": por_gerente.get("valor_vivo", 0.0),
        "valor_vencido": por_gerente.get("valor_vencido", 0.0),
        "sem_nada_vivo": False,
        "foco": [],
    }


def template_vendedor(fatos: dict) -> str:
    if fatos.get("sem_nada_vivo"):
        return (
            "{nome}, não há nenhum deal vivo na sua carteira nesta semana "
            "(semana {semana_do_trimestre} do trimestre). "
            "Se houver deals em iniciar, comece por eles no CRM."
        )
    linhas = ["{nome}, semana {semana_do_trimestre} do trimestre."]
    if fatos.get("n_fechar", 0) > 0:
        linhas.append("Você tem {n_fechar} deal(s) com chance medida de decidir nas próximas semanas.")
    if fatos.get("n_preparar", 0) > 0:
        linhas.append("{n_preparar} deal(s) decidem mais tarde no trimestre: vale avançar uma etapa.")
    if fatos.get("n_iniciar", 0) > 0:
        linhas.append("{n_iniciar} deal(s) sem data de engajamento: registre o primeiro contato.")
    if fatos.get("n_encerrar", 0) > 0:
        linhas.append("{n_encerrar} deal(s) venceram a janela, valor de tabela {valor_encerrar}: confirme ou encerre no CRM.")
    for i, item in enumerate(fatos.get("foco", []), start=1):
        linhas.append(f"- {{produto_{i}}} em {{conta_{i}}}, fila {{fila_{i}}}, {{dias_restantes_{i}}} dias restantes.")
    return "\n".join(linhas)


def template_gestor(fatos: dict) -> str:
    linhas = ["Resumo do time de {gerente}, semana {semana_do_trimestre} do trimestre."]
    if fatos.get("n_fechar", 0) > 0:
        linhas.append(
            "{vendedores} vendedores no cadastro; {n_fechar} deal(s) do time com chance medida de "
            "decidir nas próximas semanas; {n_encerrar} vencido(s)."
        )
    else:
        linhas.append("{vendedores} vendedores no cadastro; {n_encerrar} deal(s) vencido(s) no time.")
    linhas.append("Valor aberto {valor_aberto}, valor vivo {valor_vivo}, valor vencido {valor_vencido}.")
    return "\n".join(linhas)


def _gerar_um(texto_template: str, fatos: dict) -> dict:
    ok, motivo = validar(texto_template, fatos)
    if not ok:
        return {"texto": preencher(texto_template, fatos), "origem": "template", "motivo": f"template falhou a validação: {motivo}"}
    return {"texto": preencher(texto_template, fatos), "origem": "template", "motivo": None}


def gerar(scored: dict, modelo: str = MODELO_PADRAO, sem_ia: bool = False) -> dict:
    """Gera os briefings. Por ora, `sem_ia` é o único caminho: sem ANTHROPIC_API_KEY, tudo vem de template."""
    usa_ia = (not sem_ia) and bool(os.environ.get("ANTHROPIC_API_KEY"))
    if usa_ia:
        raise NotImplementedError("chamada à API ainda não implementada nesta versão; use sem_ia=True")

    vendedores_out = {}
    for v in scored["vendedores"]:
        fatos = fatos_vendedor(scored, v["vendedor"])
        vendedores_out[v["vendedor"]] = _gerar_um(template_vendedor(fatos), fatos)

    gestores_out = {}
    for gerente in sorted({v["gerente"] for v in scored["vendedores"]}):
        fatos = fatos_gestor(scored, gerente)
        gestores_out[gerente] = _gerar_um(template_gestor(fatos), fatos)

    return {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "modelo": modelo if usa_ia else "template",
        "vendedores": vendedores_out,
        "gestores": gestores_out,
        "custo_estimado_usd": 0.0,
        "recusas": [],
    }
