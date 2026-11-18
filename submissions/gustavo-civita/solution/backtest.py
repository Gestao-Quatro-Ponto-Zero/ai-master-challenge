"""Prova de que a priorização funciona, e de onde ela não funciona.

Uso: python backtest.py

Método: volta no tempo, semana a semana, calcula tudo só com o que era sabido
naquele dia e compara com o que aconteceu depois. Quatro verificações:

1. Receita: os 10 primeiros deals de cada vendedor geraram mais receita do que
   regras simples? A comparação justa é "preço, só entre deals recentes";
   "só preço" inclui deals mortos e é fácil de bater. Há também "preço, só
   entre os deals que a ferramenta mantém na lista": ela isola o que a chance
   acrescenta à ORDEM, além do corte. E a comparação justa é repetida com
   outros cortes de idade, para mostrar o quanto o resultado depende dos 90 dias.

   Desempate: vários produtos têm o mesmo preço, então uma regra "por preço" tem
   muitos empates. As regras de comparação desempatam por sorteio (média de
   TIE_RUNS sorteios), que é neutro. Uma versão anterior desempatava pela ordem
   do arquivo, que põe a negociação mais velha primeiro: era o pior caso para a
   regra simples e inflava a vantagem da ferramenta. Há também a regra simples
   mais esperta, "preço, depois a mais nova", e uma medida sem recontagem (só a
   receita ganha nos 7 dias seguintes a cada foto).
2. Parados: algum deal que a ferramenta tirou da lista de ligação foi ganho?
3. Faixas de chance: deals de faixa alta foram mais ganhos que os de faixa baixa?
4. Este mês: os deals marcados como "pode fechar este mês" foram mais ganhos em
   30 dias do que os não marcados?

O teste começa em julho: antes disso a base tem menos de um trimestre de
fechamentos e não há com o que comparar (ver LIMITACOES no README).
"""
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

import scoring

SNAPSHOTS = [d.strftime("%Y-%m-%d") for d in pd.date_range("2017-07-01", "2017-12-09", freq="7D")]
TOP_N = 10
RECENT_DAYS = 90  # regra simples de comparação: ignorar deals mais velhos que isso
RANDOM_RUNS = 50
SENSITIVITY_DAYS = [45, 60, 75, 90, 100, 120, 138]  # outros cortes para a regra simples
TIE_RUNS = 20  # sorteios para desempatar as regras de comparação
WEEK_DAYS = 7  # medida sem recontagem: só o que foi ganho até a foto seguinte


def snapshot_with_predictions(deals: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """Deals abertos em `as_of`, com a chance prevista e o que aconteceu depois."""
    chance_by_age = scoring.win_chance_by_age(deals, as_of)
    soon_by_age = scoring.win_chance_by_age(deals, as_of, within_days=scoring.SOON_DAYS)
    snap = scoring.open_at(deals, as_of)
    snap["chance"] = [scoring.chance_for(chance_by_age, age) for age in snap["age"]]
    snap["soon"] = [scoring.chance_for(soon_by_age, age) for age in snap["age"]]
    snap["valor_esperado"] = snap["chance"] * snap["sales_price"]
    snap["preco_recentes"] = snap["sales_price"].where(snap["age"] <= RECENT_DAYS, 0)
    snap["preco_vivas"] = snap["sales_price"].where(snap["chance"] >= scoring.MIN_CHANCE, 0)
    snap["won_after"] = snap["deal_stage"] == "Won"
    snap["lost_after"] = snap["deal_stage"] == "Lost"
    snap["revenue_after"] = snap["close_value"].fillna(0)
    limit = as_of + pd.Timedelta(days=scoring.SOON_DAYS)
    snap["won_soon"] = snap["won_after"] & (snap["close_date"] <= limit)
    next_photo = as_of + pd.Timedelta(days=WEEK_DAYS)
    snap["revenue_week"] = snap["revenue_after"].where(snap["won_after"] & (snap["close_date"] <= next_photo), 0)
    return snap


def _top(pool: pd.DataFrame, order_by: str, tie_column: str, tie_ascending: bool) -> pd.DataFrame:
    ordered = pool.sort_values([order_by, tie_column], ascending=[False, tie_ascending], kind="stable")
    return ordered.groupby("sales_agent").head(TOP_N)


def _captured(snap: pd.DataFrame, order_by: str, tie: str = "preco", rng=None, column: str = "revenue_after") -> float:
    """Receita gerada depois pelos TOP_N deals de cada vendedor, nessa ordenação.

    Só entram deals que a regra considera (chave > 0): uma regra que ignora deals
    velhos não leva crédito por eles. `tie` diz como desempatar:
      "preco"   pelo preço e depois pela ordem do arquivo (a ferramenta, em que
                quase não há empate; trocar por sorteio muda o total em 0,2%);
      "sorteio" média de TIE_RUNS sorteios (neutro; as regras de comparação);
      "nova"    a negociação mais nova primeiro (a regra simples mais esperta).
    """
    pool = snap[snap[order_by] > 0]
    if tie == "sorteio":
        total = 0.0
        for _ in range(TIE_RUNS):
            total += float(_top(pool.assign(_tie=rng.random(len(pool))), order_by, "_tie", False)[column].sum())
        return total / TIE_RUNS
    if tie == "nova":
        return float(_top(pool, order_by, "age", True)[column].sum())
    return float(_top(pool, order_by, "sales_price", False)[column].sum())


def run_backtest(deals: pd.DataFrame) -> dict:
    """Roda todas as semanas e devolve o detalhe e os resumos."""
    weeks, bands, soon = [], [], []
    sensitivity = {days: {} for days in SENSITIVITY_DAYS}
    ties = np.random.default_rng(7)  # semente fixa: o resultado é o mesmo a cada execução
    parked_ids: set[str] = set()
    for date in SNAPSHOTS:
        as_of = pd.Timestamp(date)
        snap = snapshot_with_predictions(deals, as_of)
        rng = np.random.default_rng(42)
        random_runs = [
            snap.sample(frac=1, random_state=int(rng.integers(1e9)))
            .groupby("sales_agent")
            .head(TOP_N)["revenue_after"]
            .sum()
            for _ in range(RANDOM_RUNS)
        ]
        parked = snap[snap["chance"] < scoring.MIN_CHANCE]
        parked_ids.update(parked["opportunity_id"])
        weeks.append(
            {
                "data": date,
                "trimestre": f"{as_of.quarter}º trimestre",
                "ferramenta": round(_captured(snap, "valor_esperado")),
                "precoRecentes": round(_captured(snap, "preco_recentes", "sorteio", ties)),
                "precoRecentesNova": round(_captured(snap, "preco_recentes", "nova")),
                "precoVivas": round(_captured(snap, "preco_vivas", "sorteio", ties)),
                "soPreco": round(_captured(snap, "sales_price", "sorteio", ties)),
                "ferramenta7": round(_captured(snap, "valor_esperado", column="revenue_week")),
                "precoRecentes7": round(_captured(snap, "preco_recentes", "sorteio", ties, column="revenue_week")),
                "acaso": round(float(np.mean(random_runs))),
                "parados": int(len(parked)),
                "paradosGanhos": int(parked["won_after"].sum()),
                "paradosPerdidos": int(parked["lost_after"].sum()),
            }
        )
        quarter = f"{as_of.quarter}º trimestre"
        for days in SENSITIVITY_DAYS:
            snap["preco_corte"] = snap["sales_price"].where(snap["age"] <= days, 0)
            tool, rule = sensitivity[days].get(quarter, (0.0, 0.0))
            sensitivity[days][quarter] = (tool + _captured(snap, "valor_esperado"), rule + _captured(snap, "preco_corte", "sorteio", ties))
        live = snap[snap["chance"] >= scoring.MIN_CHANCE].copy()
        live["faixa"] = live["chance"].map(scoring.band)
        bands.append(live[["faixa", "won_after"]])
        soon.append(snap[["soon", "won_soon", "chance"]])

    table = pd.DataFrame(weeks)
    summary = []
    for quarter, rows in table.groupby("trimestre"):
        summary.append(
            {
                "trimestre": quarter,
                "semanas": int(len(rows)),
                "ferramenta": int(rows["ferramenta"].sum()),
                "precoRecentes": int(rows["precoRecentes"].sum()),
                "precoRecentesNova": int(rows["precoRecentesNova"].sum()),
                "precoVivas": int(rows["precoVivas"].sum()),
                "ferramenta7": int(rows["ferramenta7"].sum()),
                "precoRecentes7": int(rows["precoRecentes7"].sum()),
                "soPreco": int(rows["soPreco"].sum()),
                "acaso": int(rows["acaso"].sum()),
                "semanasGanhas": int((rows["ferramenta"] > rows["precoRecentes"]).sum()),
                "semanasGanhasVivas": int((rows["ferramenta"] > rows["precoVivas"]).sum()),
                "semanasGanhasNova": int((rows["ferramenta"] > rows["precoRecentesNova"]).sum()),
            }
        )

    all_bands = pd.concat(bands)
    band_rows = [
        {
            "faixa": name,
            "deals": int((all_bands["faixa"] == name).sum()),
            "ganhos": round(float(all_bands.loc[all_bands["faixa"] == name, "won_after"].mean()), 3),
        }
        for name in ("alta", "media", "baixa")
    ]

    all_soon = pd.concat(soon)
    flagged = all_soon["soon"] >= scoring.SOON_MIN_CHANCE
    live_unflagged = ~flagged & (all_soon["chance"] >= scoring.MIN_CHANCE)
    return {
        "semanas": weeks,
        "resumo": summary,
        "parados": {
            "total": int(table["parados"].sum()),
            "distintos": len(parked_ids),
            "ganhos": int(table["paradosGanhos"].sum()),
            "perdidos": int(table["paradosPerdidos"].sum()),
        },
        "faixas": band_rows,
        "esteMes": {
            "marcados": int(flagged.sum()),
            "ganhosMarcados": round(float(all_soon.loc[flagged, "won_soon"].mean()), 3),
            "naoMarcados": int((~flagged).sum()),
            "ganhosNaoMarcados": round(float(all_soon.loc[~flagged, "won_soon"].mean()), 3),
            # comparação mais justa: não marcadas que ainda tinham chance (sem as já mortas)
            "naoMarcadosVivas": int(live_unflagged.sum()),
            "ganhosNaoMarcadosVivas": round(float(all_soon.loc[live_unflagged, "won_soon"].mean()), 3),
        },
        "regraSimplesDias": RECENT_DAYS,
        # vantagem da ferramenta (em %) sobre "preço entre deals de até N dias", por trimestre
        "sensibilidade": [
            {"dias": days, **{quarter: round((tool / rule - 1) * 100, 1) for quarter, (tool, rule) in sorted(by_quarter.items())}}
            for days, by_quarter in sensitivity.items()
        ],
        "topN": TOP_N,
    }


def segment_win_rates(deals: pd.DataFrame) -> list[dict]:
    """Taxa de ganho por segmento entre os deals fechados + teste qui-quadrado.

    p alto = a diferença entre os grupos é compatível com o acaso. Vale só para
    "ganho x perda"; não mede quem deixa deal aberto sem fechar.
    """
    closed = deals[deals["deal_stage"].isin(["Won", "Lost"])].copy()
    closed["won"] = closed["deal_stage"] == "Won"
    labels = {
        "sales_agent": "Vendedor",
        "product": "Produto",
        "sector": "Setor da conta",
        "account": "Conta",
        "manager": "Manager",
        "regional_office": "Região",
    }
    # Porte da conta: números contínuos, comparados em quatro faixas de mesmo tamanho.
    for column, name in (("revenue", "porte_faturamento"), ("employees", "porte_funcionarios")):
        closed[name] = pd.qcut(closed[column], 4, labels=False, duplicates="drop")
    labels["porte_faturamento"] = "Porte da conta (faturamento)"
    labels["porte_funcionarios"] = "Porte da conta (funcionários)"
    out = []
    for column, label in labels.items():
        rates = closed.groupby(column)["won"].agg(["size", "mean"])
        rates = rates[rates["size"] >= 30]
        p_value = chi2_contingency(pd.crosstab(closed[column], closed["won"]))[1]
        out.append(
            {
                "fator": label,
                "grupos": int(len(rates)),
                "min": round(float(rates["mean"].min()), 3),
                "max": round(float(rates["mean"].max()), 3),
                "p": round(float(p_value), 3),
            }
        )
    return out


if __name__ == "__main__":
    all_deals = scoring.load_pipeline()
    result = run_backtest(all_deals)
    print(f"Data de referência: {scoring.reference_date(all_deals).date()}")
    print(f"Semanas testadas: {len(result['semanas'])} ({SNAPSHOTS[0]} a {SNAPSHOTS[-1]})\n")
    print(f"1. Receita dos top {TOP_N} por vendedor, soma por trimestre (regras de comparação desempatadas por sorteio):")
    summary = pd.DataFrame(result["resumo"])
    print(summary.to_string(index=False))
    for name, column in (("preço até 90 dias, desempate por sorteio", "precoRecentes"),
                         ("preço até 90 dias, depois a mais nova", "precoRecentesNova"),
                         ("preço entre as que a ferramenta mantém", "precoVivas"),
                         ("só preço", "soPreco")):
        gains = ", ".join(f"{q}: {(a / b - 1) * 100:+.1f}%" for q, a, b in zip(summary["trimestre"], summary["ferramenta"], summary[column]))
        print(f"   Ferramenta contra '{name}': {gains}")
    week = ", ".join(f"{q}: {(a / b - 1) * 100:+.1f}%" for q, a, b in zip(summary["trimestre"], summary["ferramenta7"], summary["precoRecentes7"]))
    print(f"   Sem recontagem (só o ganho nos {WEEK_DAYS} dias seguintes a cada foto), contra 'preço até 90 dias': {week}")
    lost_weeks = [w["data"] for w in result["semanas"] if w["ferramenta"] <= w["precoRecentes"]]
    print(f"   Semanas em que a ferramenta NÃO ganhou da regra simples: {lost_weeks or 'nenhuma'}")
    print("   Vantagem (%) da ferramenta sobre 'preço entre deals de até N dias', por trimestre:")
    print(pd.DataFrame(result["sensibilidade"]).to_string(index=False))
    print(f"\n2. Deals tirados da lista de ligação: {result['parados']}")
    print("\n3. Ganho real por faixa de chance:")
    print(pd.DataFrame(result["faixas"]).to_string(index=False))
    print(f"\n4. Pode fechar este mês: {result['esteMes']}")
    print("\nTaxa de ganho por fator entre os fechados (p > 0,05 = sem diferença real):")
    print(pd.DataFrame(segment_win_rates(all_deals)).to_string(index=False))
