"""Cross-sell: contas que já compraram uma série e nunca compraram outra viram uma
lista de "próximo produto". Prioridade = quanto a conta já comprou com a gente
(cliente que gasta mais é o melhor candidato a expandir)."""
import pandas as pd

from .dados import Dados


def sugerir(dados: Dados, deals: pd.DataFrame) -> pd.DataFrame:
    f = dados.fechados
    ganhos = f[(f.ganhou == 1) & f.account.notna()]
    if ganhos.empty:
        return pd.DataFrame()

    todas_series = set(dados.pipeline.series.dropna())
    # Produto de entrada sugerido em cada série = o mais vendido dela no histórico
    produto_da_serie = ganhos.groupby("series")["product"].agg(lambda s: s.value_counts().index[0]).to_dict()
    # Quem já tem deal aberto naquela série não entra (já está sendo trabalhado)
    em_aberto = (deals.dropna(subset=["conta"]).groupby("conta").serie.apply(set).to_dict() if not deals.empty else {})

    linhas = []
    for conta, g in ganhos.groupby("account"):
        compradas = set(g.series)
        # Vendedor sugerido = quem mais fechou com essa conta (já tem o relacionamento)
        dono = g.sales_agent.value_counts().index[0]
        dono_info = g[g.sales_agent == dono].iloc[0]
        for serie in sorted(todas_series - compradas - em_aberto.get(conta, set())):
            linhas.append({
                "conta": conta,
                "setor": g.sector.iloc[0],
                "series_compradas": sorted(compradas),
                "serie_sugerida": serie,
                "produto_sugerido": produto_da_serie.get(serie),
                "valor_historico": float(g.close_value.sum()),
                "n_compras": len(g),
                "ultima_compra": g.close_date.max().date().isoformat(),
                "agente": dono,
                "manager": dono_info.manager,
                "regiao": dono_info.regional_office,
            })
    if not linhas:
        return pd.DataFrame()
    return pd.DataFrame(linhas).sort_values("valor_historico", ascending=False).reset_index(drop=True)
