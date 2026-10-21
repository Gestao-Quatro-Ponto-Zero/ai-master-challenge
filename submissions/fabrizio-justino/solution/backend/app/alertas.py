"""Alertas e lembretes por stage do pipeline.

Regra do crítico: só quando há ao mesmo tempo VALOR relevante, PRAZO e uma AÇÃO
concreta — e no máximo MAX_CRITICOS_POR_VENDEDOR por vendedor (o excedente é
rebaixado pra atenção). Alerta de stage em deal de valor baixo é lembrete. Antes dessa regra, 1.292 deals fora do ciclo geravam um
crítico cada e o crítico não significava mais nada.

Dois níveis:
- por deal (gerar_alertas_deal): 1 alerta de stage por deal (o mais urgente) + avisos
  de dado. Alertas com `na_fila=False` aparecem só no detalhe do deal — os zumbis,
  por exemplo, viram UM alerta agregado de limpeza pro manager;
- do recorte (gerar_lembretes_time): emergência, fim de trimestre, manager sem deal
  fechável, sobrecarga com sugestão de redistribuição, limpeza em massa, qualidade
  de dado.

Severidade: 'critico' (agir hoje) > 'atencao' (agir esta semana) > 'lembrete'."""
import pandas as pd

from . import config
from .scoring import Benchmarks, usd

ORDEM_SEVERIDADE = {"critico": 0, "atencao": 1, "lembrete": 2}


def _alerta(tipo: str, severidade: str, titulo: str, mensagem: str, acao: str,
            deal: dict | None = None, na_fila: bool = True, **extra) -> dict:
    a = {"tipo": tipo, "severidade": severidade, "titulo": titulo, "mensagem": mensagem,
         "acao_sugerida": acao, "na_fila": na_fila, **extra}
    if deal is not None:
        a.update({
            "opportunity_id": deal["opportunity_id"], "agente": deal["agente"], "stage": deal["stage"],
            "produto": deal["produto"], "conta": deal["conta"], "score": deal["score"],
            "valor_esperado": deal.get("valor_esperado"),
        })
    return a


def gerar_alertas_deal(deal: dict, bm: Benchmarks, ctx: dict) -> list[dict]:
    """ctx: valor_relevante (preço mínimo pra crítico), resgate (ids), esfriando
    (id → motivo), data_fim_trimestre (str)."""
    alertas = []
    idade, stage = deal["idade_dias"], deal["stage"]
    zona, teto = bm.zona_risco_dias, bm.ciclo_max_dias
    p75 = bm.ciclo_p75_produto.get(deal["produto"], teto)
    relevante = deal["valor"] >= ctx["valor_relevante"]
    oid = deal["opportunity_id"]

    if stage == "Prospecting":
        alertas.append(_alerta(
            "prospecting_parado", "lembrete", "Deal ainda não engajado",
            "Oportunidade em Prospecting sem data de engajamento — o relógio do ciclo ainda nem começou.",
            "Agende o primeiro contato e mova para Engaging.", deal,
        ))
    elif deal["fora_do_ciclo"]:
        requalificar = deal["acao"] == "Requalificar"
        alertas.append(_alerta(
            "fora_do_ciclo", "atencao" if requalificar else "lembrete", f"{idade} dias em Engaging",
            f"Nenhum deal do histórico fechou depois de {teto} dias. Este já passou {idade - teto} dias do limite.",
            "Pergunte ao cliente se o projeto continua. Se sim, encerre este deal e abra uma oportunidade nova "
            "(o relógio volta a zero); se não, encerre como Lost." if requalificar
            else "Encerre como Lost para limpar o pipeline.",
            deal, na_fila=False,
        ))
    elif oid in ctx["resgate"]:
        alertas.append(_alerta(
            "resgate", "critico", "Lista de resgate da meta",
            f"Este deal está entre os que fecham o gap da sua meta. Fechar até {ctx['data_fim_trimestre']} "
            f"vale {usd(deal['valor_liquido'])} (chance de ganhar no trimestre: {deal['prob_trimestre'] * 100:.0f}%).",
            "Peça a decisão do cliente esta semana.", deal,
        ))
    elif oid in ctx["esfriando"]:
        alertas.append(_alerta(
            "esfriando", "critico", "Deal grande esfriando",
            f"Top 10% de valor do pipeline e {ctx['esfriando'][oid]}.",
            "Retome o contato hoje — proposta, reunião com decisor ou condição de fechamento.", deal,
        ))
    elif idade is not None and idade <= zona:
        alertas.append(_alerta(
            "zona_de_risco", "critico" if relevante else "lembrete", f"Zona de risco: {idade}º dia",
            f"{bm.pct_perdidos_na_zona * 100:.0f}% dos deals perdidos morrem até o {zona}º dia de Engaging"
            + (f" — e este vale {usd(deal['valor'])}." if relevante else "."),
            f"Faça follow-up nos próximos {max(zona - idade, 1)} dias para passar da fase crítica.", deal,
        ))
    elif idade is not None and idade > p75:
        alertas.append(_alerta(
            "reta_final", "critico" if relevante else "lembrete", f"Reta final: faltam {teto - idade} dias",
            f"Já passou do ciclo típico de {deal['produto']} ({p75}d) e se aproxima do limite histórico ({teto}d)"
            + (f" — {usd(deal['valor'])} em jogo." if relevante else "."),
            "Envie proposta final / peça a decisão.", deal,
        ))

    if deal["conta"] is None:
        alertas.append(_alerta(
            "sem_conta", "lembrete", "Conta não preenchida",
            "Sem a conta, o score não usa o histórico do cliente e o manager não enxerga o relacionamento.",
            "Preencha a conta no CRM.", deal, na_fila=False,
        ))
    return alertas


def aplicar_teto_criticos(alertas_por_deal: list[list[dict]]) -> None:
    """No máximo N críticos por vendedor: mantém os de maior valor esperado e rebaixa
    o resto pra atenção (in place). Assim o crítico continua significando 'hoje'."""
    criticos = [a for lista in alertas_por_deal for a in lista if a["severidade"] == "critico"]
    por_agente: dict[str, list[dict]] = {}
    for a in criticos:
        por_agente.setdefault(a["agente"], []).append(a)
    for lista in por_agente.values():
        lista.sort(key=lambda a: a.get("valor_esperado") or 0, reverse=True)
        for a in lista[config.MAX_CRITICOS_POR_VENDEDOR:]:
            a["severidade"] = "atencao"
            a["rebaixado"] = True


def _redistribuicao(metricas: pd.DataFrame, deals: pd.DataFrame, bm: Benchmarks, agente: str, excesso: int) -> list[dict]:
    """Sugere passar os melhores deals vivos do vendedor sobrecarregado pra quem tem
    folga no MESMO escritório regional e melhor afinidade naquele produto."""
    regiao = metricas.loc[metricas.agente == agente, "regiao"].iloc[0]
    folga = metricas[(metricas.regiao == regiao) & (metricas.agente != agente)
                     & ((metricas.carga_rel < config.FATOR_FOLGA) | metricas.carga_rel.isna())
                     & (metricas.capacidade > 0)]
    if folga.empty:
        return []
    candidatos = deals[(deals.agente == agente) & ~deals.fora_do_ciclo & (deals.stage == "Engaging")
                       & deals.acao.isin(["Atacar agora", "Nutrir"])].head(min(excesso, 5))
    sugestoes = []
    for d in candidatos.itertuples():
        afinidade = {a: bm.win_agente_produto.get((a, d.produto), bm.win_agente.get(a, bm.win_rate_geral)) for a in folga.agente}
        destino = max(afinidade, key=afinidade.get)
        sugestoes.append({
            # int/float explícitos: itertuples devolve tipos numpy, que o JSON não aceita
            "opportunity_id": d.opportunity_id, "conta": d.conta, "produto": d.produto, "score": int(d.score),
            "valor_esperado": float(d.valor_esperado), "de": agente, "para": destino,
            "afinidade_destino": round(float(afinidade[destino]), 3),
        })
    return sugestoes


def gerar_lembretes_time(deals: pd.DataFrame, metricas: pd.DataFrame, emerg: dict, bm: Benchmarks) -> list[dict]:
    lembretes = []
    tri = emerg["trimestre"]

    # 1. Emergência (meta do recorte em risco na janela) / lembrete de fim de trimestre
    if emerg["ativa"]:
        r = emerg["resgate"]
        lembretes.append(_alerta(
            "emergencia", "critico", f"Meta em risco: faltam {usd(emerg['falta'])} em {tri['dias_restantes']} dias",
            f"Fechado no trimestre: {usd(emerg['fechado'])} de {usd(emerg['meta'])} ({emerg['pct_meta'] * 100:.0f}%), "
            f"com {tri['pct_decorrido'] * 100:.0f}% do trimestre decorrido. Projeção com o pipeline: {usd(emerg['projecao'])}. "
            + (f"Os {r['n']} deals da lista de resgate cobrem o que falta." if r["cobre_a_meta"]
               else "Nem fechando todo o pipeline que cabe no ciclo a meta é batida."),
            "Abra a lista de resgate e ataque na ordem.",
        ))
    elif emerg["na_janela"] and tri["dias_restantes"] >= 0:
        lembretes.append(_alerta(
            "fim_trimestre", "lembrete",
            "Fim de trimestre " + ("é hoje" if tri["dias_restantes"] == 0 else f"em {tri['dias_restantes']} dias"),
            f"Deals fechados no último mês do trimestre ganham {bm.win_fim_trimestre * 100:.0f}% das vezes, "
            f"contra {bm.win_fora_trimestre * 100:.0f}% nos outros meses.",
            "Priorize os deals de 'Atacar agora' até o fechamento do trimestre.",
        ))

    if metricas.empty:
        return lembretes

    # 2. Manager cujo time não tem deal fechável
    for manager, g in metricas.groupby("manager"):
        falta = g.falta.sum()
        cobertura = g.valor_esperado_trimestre.sum() / falta if falta > 0 else None
        if g.n_atacar.sum() == 0 and (cobertura is None or cobertura < 1):
            lembretes.append(_alerta(
                "time_sem_fechavel", "critico", f"Time de {manager} sem deal fechável",
                "Nenhum deal do time está em 'Atacar agora'"
                + (f" e o valor esperado até o fim do trimestre cobre {cobertura:.1f}× do que falta para a meta."
                   .replace(".", ",", 1) if cobertura is not None else "."),
                "Manager: revise a carteira com o time — requalifique os deals grandes e reative Prospecting.",
                manager=manager,
            ))

    # 3. Sobrecarga (carga vs capacidade histórica) + sugestão de redistribuição
    for linha in metricas[metricas.carga_rel >= config.FATOR_SOBRECARGA].sort_values("carga_rel", ascending=False).itertuples():
        sugestoes = _redistribuicao(metricas, deals, bm, linha.agente, int(linha.carga - linha.capacidade))
        lembretes.append(_alerta(
            "sobrecarga", "atencao", f"{linha.agente}: {linha.carga_rel:.1f}× a capacidade",
            f"{linha.carga} deals vivos em Engaging para uma capacidade histórica de ~{linha.capacidade:.0f} "
            f"({linha.throughput_mes:.0f} fechamentos/mês). Deals bons tendem a esfriar na fila.",
            "Manager: redistribua os melhores deals para quem tem folga." if sugestoes
            else "Manager: não há vendedor com folga no mesmo escritório — priorize pela lista.",
            agente=linha.agente, redistribuicao=sugestoes,
        ))

    # 4. Limpeza em massa dos zumbis (antes: 1 crítico por deal)
    if not deals.empty:
        zumbis = deals[deals.fora_do_ciclo]
        if len(zumbis):
            encerrar = zumbis[zumbis.acao == "Encerrar"]
            requalificar = zumbis[zumbis.acao == "Requalificar"]
            lembretes.append(_alerta(
                "limpeza", "atencao", f"{len(zumbis)} deals para limpar",
                f"Passaram de {bm.ciclo_max_dias} dias em Engaging — nenhum deal do histórico ganhou depois disso. "
                f"{len(encerrar)} de baixo valor para encerrar e {len(requalificar)} de valor alto "
                f"({usd(requalificar.valor.sum())} de tabela) para requalificar: perguntar ao cliente e, se o projeto "
                f"continuar, reabrir como oportunidade nova.",
                "Encerrar em lote libera atenção e deixa a cobertura e as taxas honestas.",
            ))

    # 5. Qualidade de dado por vendedor
    piores = metricas[metricas.pct_sem_conta >= 0.75].sort_values("pct_sem_conta", ascending=False)
    if len(piores):
        nomes = ", ".join(f"{r.agente} ({r.pct_sem_conta * 100:.0f}%)" for r in piores.head(3).itertuples())
        lembretes.append(_alerta(
            "qualidade_dado", "lembrete", f"{len(piores)} vendedores com ≥75% dos deals sem conta",
            f"Forecast menos confiável: {nomes}.",
            "Reserve 15 minutos para completar o CRM.",
        ))
    return lembretes


def ordenar(alertas: list[dict]) -> list[dict]:
    return sorted(alertas, key=lambda a: (ORDEM_SEVERIDADE[a["severidade"]], -(a.get("valor_esperado") or 0)))
