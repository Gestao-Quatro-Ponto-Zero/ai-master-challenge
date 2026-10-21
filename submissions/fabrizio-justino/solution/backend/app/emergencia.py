"""Modo emergência: meta em risco no fim do trimestre.

Dispara quando, ao mesmo tempo:
- estamos na janela de emergência (último mês do trimestre — onde o histórico
  concentra os ganhos), e
- a projeção (fechado no trimestre + valor esperado do que ainda cabe no ciclo) não
  bate a meta (média trimestral fechada × META_FATOR).

Entrega a LISTA DE RESGATE: o menor conjunto de deals, do maior valor esperado no
trimestre pro menor, restrito aos que ainda têm chance real de ganhar até o fim do
trimestre, cujo valor (se fecharem) cobre o que falta. É o "Atacar agora" da
emergência, com nome e valor.

Gatilho complementar, independente da janela: deal grande (top 10% de valor) que
passou da mediana de ciclo do produto ou caiu de faixa desde a semana passada."""
import pandas as pd

from . import config
from .metricas import Trimestre
from .scoring import ORDEM_ACOES, Benchmarks

MAX_RESGATE_EXIBIDO = 15
# Deal com chance de ganhar no trimestre abaixo disso não "cabe" mais no trimestre
PROB_MIN_RESGATE = 0.05


def _vivos_engaging(deals: pd.DataFrame) -> pd.DataFrame:
    if deals.empty:
        return deals
    return deals[(deals.stage == "Engaging") & ~deals.fora_do_ciclo]


def _cabem_no_trimestre(deals: pd.DataFrame) -> pd.DataFrame:
    vivos = _vivos_engaging(deals)
    if vivos.empty:
        return vivos
    return vivos[vivos.prob_trimestre >= PROB_MIN_RESGATE].sort_values("valor_esperado_trimestre", ascending=False)


def lista_resgate(deals: pd.DataFrame, falta: float) -> pd.DataFrame:
    """Menor prefixo (por valor esperado no trimestre) cujo valor líquido cobre `falta`."""
    cabem = _cabem_no_trimestre(deals)
    if falta <= 0 or cabem.empty:
        return cabem.iloc[0:0]
    acumulado = cabem.valor_liquido.cumsum()
    n = int((acumulado < falta).sum()) + 1
    return cabem.head(n)


def avaliar(deals: pd.DataFrame, metricas: pd.DataFrame, tri: Trimestre) -> dict:
    meta = metricas.meta.sum(min_count=1)
    tem_meta = pd.notna(meta) and meta > 0
    fechado = float(metricas.fechado_trimestre.sum())
    esperado = float(metricas.valor_esperado_trimestre.sum())
    projecao = fechado + esperado
    falta = (meta - fechado) if tem_meta else 0.0
    gap = (meta - projecao) if tem_meta else 0.0
    na_janela = tri.dias_restantes <= config.JANELA_EMERGENCIA_DIAS
    em_risco = bool(tem_meta and gap > 0)

    resgate = lista_resgate(deals, falta)
    return {
        # No último dia não há mais o que resgatar — sem emergência, só o lembrete
        "ativa": bool(na_janela and em_risco and tri.dias_restantes > 0),
        "na_janela": bool(na_janela),
        "em_risco": em_risco,
        "trimestre": tri.como_dict(),
        "meta": float(meta) if tem_meta else None,
        "fechado": fechado,
        "valor_esperado": esperado,
        "projecao": projecao,
        "falta": max(falta, 0.0),
        "gap": max(gap, 0.0),
        "pct_meta": fechado / meta if tem_meta else None,
        "resgate": {
            "n": len(resgate),
            "valor": float(resgate.valor_liquido.sum()) if len(resgate) else 0.0,
            "cobre_a_meta": bool(len(resgate) and resgate.valor_liquido.sum() >= falta),
            "deals": resgate.head(MAX_RESGATE_EXIBIDO),
        },
    }


def ids_resgate_por_vendedor(deals: pd.DataFrame, metricas: pd.DataFrame, tri: Trimestre) -> set:
    """Deals que estão na lista de resgate DO PRÓPRIO vendedor (meta individual) —
    viram alerta crítico no deal. Só vale dentro da janela de emergência."""
    if tri.dias_restantes > config.JANELA_EMERGENCIA_DIAS or deals.empty:
        return set()
    ids = set()
    for linha in metricas.itertuples():
        if pd.isna(linha.meta) or linha.projecao >= linha.meta:
            continue
        ids |= set(lista_resgate(deals[deals.agente == linha.agente], linha.meta - linha.fechado_trimestre).opportunity_id)
    return ids


def deals_esfriando(deals: pd.DataFrame, deals_antes: pd.DataFrame, bm: Benchmarks) -> dict:
    """opportunity_id → motivo, para deals grandes que estão esfriando."""
    if deals.empty:
        return {}
    limite = deals.valor.quantile(config.QUANTIL_DEAL_GRANDE)
    grandes = _vivos_engaging(deals)
    grandes = grandes[grandes.valor >= limite]
    ordem = {a: i for i, a in enumerate(ORDEM_ACOES)}
    acao_antes = deals_antes.set_index("opportunity_id").acao.to_dict() if not deals_antes.empty else {}

    motivos = {}
    for d in grandes.itertuples():
        mediana = bm.ciclo_mediano_produto.get(d.produto)
        partes = []
        if mediana is not None and d.idade_dias > mediana:
            partes.append(f"{d.idade_dias} dias, acima do ciclo mediano de {d.produto} ({mediana}d)")
        antes = acao_antes.get(d.opportunity_id)
        if antes and ordem[d.acao] > ordem[antes]:
            partes.append(f"caiu de '{antes}' para '{d.acao}' desde a semana passada")
        if partes:
            motivos[d.opportunity_id] = "; ".join(partes)
    return motivos
