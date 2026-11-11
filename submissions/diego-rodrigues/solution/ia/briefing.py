"""Fatos para o briefing, templates deterministas e `gerar`: IA com validador, ou template como fallback."""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from ia.validar import marcadores_validos, preencher, validar

MODELO_FIXO = "claude-haiku-5-5"
LIMITE_TOKENS = {"vendedor": 250, "gestor": 150}
TENTATIVAS_POR_ITEM = 2
TETO_CHAMADAS = 60
PRECO_USD_POR_MTOK = {"entrada": 0.10, "saida": 0.50}
PROMPTS = Path(__file__).parent / "prompts"


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
        base = ("{nome}, não há nenhum deal vivo na sua carteira nesta semana "
                "(semana {semana_do_trimestre} do trimestre).")
        n = fatos.get("n_iniciar", 0)
        if n > 0:
            return base + " {n_iniciar} " + _deal(n) + " sem data de engajamento: comece registrando o primeiro contato."
        return base + " Também não há deals para iniciar."
    linhas = ["{nome}, semana {semana_do_trimestre} do trimestre."]
    n = fatos.get("n_fechar", 0)
    if n > 0:
        linhas.append("Você tem {n_fechar} " + _deal(n) + " com chance medida de decidir nas próximas semanas.")
    n = fatos.get("n_preparar", 0)
    if n > 0:
        linhas.append("{n_preparar} " + ("deal vivo decide" if n == 1 else "deals vivos decidem")
                      + " mais tarde no trimestre: vale avançar uma etapa.")
    n = fatos.get("n_iniciar", 0)
    if n > 0:
        linhas.append("{n_iniciar} " + _deal(n) + " sem data de engajamento: registre o primeiro contato.")
    n = fatos.get("n_encerrar", 0)
    if n > 0:
        linhas.append("{n_encerrar} " + _deal(n) + (" venceu" if n == 1 else " venceram")
                      + " a janela (valor de tabela {valor_encerrar}): confirme ou encerre no CRM.")
    return "\n".join(linhas)


def _deal(n: int) -> str:
    return "deal" if n == 1 else "deals"


def template_gestor(fatos: dict) -> str:
    linhas = ["Semana {semana_do_trimestre} do trimestre, {vendedores} vendedores no cadastro."]
    nf = fatos.get("n_fechar", 0)
    ne = fatos.get("n_encerrar", 0)
    if nf > 0:
        linhas.append("{n_fechar} " + _deal(nf) + " do time com chance medida de decidir nas próximas semanas; "
                      "{n_encerrar} " + _deal(ne) + " vencido" + ("" if ne == 1 else "s") + ".")
    else:
        linhas.append("{n_encerrar} " + _deal(ne) + " vencido" + ("" if ne == 1 else "s") + " no time.")
    linhas.append("Valor aberto {valor_aberto}, valor vivo {valor_vivo}, valor vencido {valor_vencido}.")
    return "\n".join(linhas)


def _gerar_um(texto_template: str, fatos: dict) -> dict:
    ok, motivo = validar(texto_template, fatos)
    if not ok:
        return {"texto": preencher(texto_template, fatos), "origem": "template", "motivo": f"template falhou a validação: {motivo}"}
    return {"texto": preencher(texto_template, fatos), "origem": "template", "motivo": None}


def _prompt_sistema(tipo: str) -> str:
    nome = "briefing_vendedor.md" if tipo == "vendedor" else "resumo_gestor.md"
    return (PROMPTS / nome).read_text(encoding="utf-8")


def _texto_da_resposta(resposta) -> str:
    return "".join(b.text for b in resposta.content if getattr(b, "type", None) == "text").strip()


def _chamar_modelo(cliente, tipo: str, fatos: dict, motivo_anterior: str | None):
    marcadores = sorted(marcadores_validos(fatos))
    pedido = (
        "Fatos (JSON):\n" + json.dumps(fatos, ensure_ascii=False, indent=1)
        + "\n\nMarcadores permitidos: " + ", ".join("{" + m + "}" for m in marcadores)
    )
    if motivo_anterior:
        pedido += f"\n\nA versão anterior foi recusada: {motivo_anterior}. Reescreva usando só os marcadores."
    return cliente.messages.create(
        model=MODELO_FIXO,
        max_tokens=LIMITE_TOKENS[tipo],
        system=_prompt_sistema(tipo),
        thinking={"type": "disabled"},
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": pedido}],
    )


def _gerar_com_ia(cliente, tipo: str, fatos: dict, uso: dict) -> tuple[str | None, str | None]:
    """Devolve (texto validado, None) ou (None, motivo da última recusa)."""
    motivo = None
    for _ in range(TENTATIVAS_POR_ITEM):
        if uso["chamadas"] >= TETO_CHAMADAS:
            return None, "teto de chamadas atingido"
        resposta = _chamar_modelo(cliente, tipo, fatos, motivo)
        uso["chamadas"] += 1
        uso["entrada"] += resposta.usage.input_tokens
        uso["saida"] += resposta.usage.output_tokens
        if resposta.stop_reason != "end_turn":
            motivo = f"parada incompleta ({resposta.stop_reason})"
            continue
        texto = _texto_da_resposta(resposta)
        ok, motivo = validar(texto, fatos)
        if ok:
            return preencher(texto, fatos), None
        if not motivo:
            motivo = "resposta vazia"
    return None, motivo


def _custo_usd(uso: dict) -> float:
    return round(
        uso["entrada"] * PRECO_USD_POR_MTOK["entrada"] / 1_000_000
        + uso["saida"] * PRECO_USD_POR_MTOK["saida"] / 1_000_000,
        6,
    )


def gerar(scored: dict, modelo: str = MODELO_FIXO, sem_ia: bool = False, cliente=None) -> dict:
    """Gera os briefings. Com chave e sem `sem_ia`, usa o Haiku 5.5 com validador; caso contrário, template.

    Qualquer item que a IA não consegue validar cai no template, com o motivo registrado em `recusas`.
    """
    if modelo != MODELO_FIXO:
        raise ValueError(f"modelo fixo nesta submissão: {MODELO_FIXO}")
    if sem_ia:
        usa_ia = False
    else:
        usa_ia = cliente is not None or bool(os.environ.get("ANTHROPIC_API_KEY"))
    if usa_ia and cliente is None:
        import anthropic
        cliente = anthropic.Anthropic()

    uso = {"chamadas": 0, "entrada": 0, "saida": 0}
    recusas = []

    def _um(texto_template: str, fatos: dict, nome: str, tipo: str) -> dict:
        if usa_ia:
            texto, motivo = _gerar_com_ia(cliente, tipo, fatos, uso)
            if texto is not None:
                return {"texto": texto, "origem": "ia", "motivo": None}
            recusas.append({"item": nome, "motivo": motivo})
        return _gerar_um(texto_template, fatos)

    vendedores_out = {}
    for v in scored["vendedores"]:
        fatos = fatos_vendedor(scored, v["vendedor"])
        vendedores_out[v["vendedor"]] = _um(template_vendedor(fatos), fatos, v["vendedor"], "vendedor")

    gestores_out = {}
    for gerente in sorted({v["gerente"] for v in scored["vendedores"]}):
        fatos = fatos_gestor(scored, gerente)
        gestores_out[gerente] = _um(template_gestor(fatos), fatos, gerente, "gestor")

    return {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "modelo": MODELO_FIXO if usa_ia else "template",
        "vendedores": vendedores_out,
        "gestores": gestores_out,
        "custo_estimado_usd": _custo_usd(uso) if usa_ia else 0.0,
        "chamadas": uso["chamadas"],
        "tokens_entrada": uso["entrada"],
        "tokens_saida": uso["saida"],
        "recusas": recusas,
    }
