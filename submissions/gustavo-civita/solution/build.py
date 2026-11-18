"""Gera app/data.js a partir dos CSVs. Uso: python build.py"""
import json
from pathlib import Path

import pandas as pd

import scoring
from backtest import run_backtest, segment_win_rates

OUT = Path(__file__).parent / "app" / "data.js"


def account_profiles(deals: pd.DataFrame, today: pd.Timestamp) -> dict:
    """Ficha de cada conta: cadastro + histórico de compras, para preparar o contato."""
    profiles = {}
    for account, rows in deals[deals["account"].notna()].groupby("account"):
        first = rows.iloc[0]
        won = rows[rows["deal_stage"] == "Won"]
        lost = rows[rows["deal_stage"] == "Lost"]
        by_agent = {
            agent: {
                "ganhos": int((group["deal_stage"] == "Won").sum()),
                "perdidos": int((group["deal_stage"] == "Lost").sum()),
            }
            for agent, group in rows[rows["deal_stage"].isin(["Won", "Lost"])].groupby("sales_agent")
        }
        profiles[account] = {
            "setor": first["sector"],
            "receitaMilhoes": float(first["revenue"]),
            "funcionarios": int(first["employees"]),
            "pais": first["office_location"],
            "grupo": None if pd.isna(first["subsidiary_of"]) else first["subsidiary_of"],
            "ganhos": int(len(won)),
            "perdidos": int(len(lost)),
            "receitaTotal": round(float(won["close_value"].sum())),
            "ultimaCompra": None if won.empty else won["close_date"].max().strftime("%Y-%m-%d"),
            "diasDesdeUltimaCompra": None if won.empty else int((today - won["close_date"].max()).days),
            "produtos": won["product"].value_counts().head(3).to_dict(),
            "abertas": int(rows["deal_stage"].isin(["Engaging", "Prospecting"]).sum()),
            "porVendedor": by_agent,
        }
    return profiles


def monthly_history(deals: pd.DataFrame) -> list[dict]:
    """Por mês e vendedor: receita ganha, ganhos, perdas e negociações iniciadas."""
    rows: dict[tuple[str, str], dict] = {}

    def row(month: str, agent: str) -> dict:
        return rows.setdefault(
            (month, agent),
            {"mes": month, "vendedor": agent, "receita": 0, "ganhos": 0, "perdidos": 0, "iniciadas": 0},
        )

    closed = deals[deals["close_date"].notna()]
    for (month, agent), group in closed.groupby([closed["close_date"].dt.strftime("%Y-%m"), "sales_agent"]):
        entry = row(month, agent)
        entry["receita"] = round(float(group["close_value"].sum()))
        entry["ganhos"] = int((group["deal_stage"] == "Won").sum())
        entry["perdidos"] = int((group["deal_stage"] == "Lost").sum())
    started = deals[deals["engage_date"].notna()]
    for (month, agent), group in started.groupby([started["engage_date"].dt.strftime("%Y-%m"), "sales_agent"]):
        row(month, agent)["iniciadas"] = int(len(group))
    return sorted(rows.values(), key=lambda r: (r["mes"], r["vendedor"]))


def seller_profiles(deals: pd.DataFrame) -> dict:
    """Todos os vendedores do cadastro, inclusive os que não têm negociação aberta."""
    teams = pd.read_csv(scoring.DATA_DIR / "sales_teams.csv")
    won = deals[deals["deal_stage"] == "Won"].copy()
    won["cycle"] = (won["close_date"] - won["engage_date"]).dt.days
    cycles = won.groupby("sales_agent")["cycle"].median()
    return {
        r.sales_agent: {
            "manager": r.manager,
            "regiao": r.regional_office,
            "cicloMedianoGanho": None if r.sales_agent not in cycles else int(cycles[r.sales_agent]),
        }
        for r in teams.itertuples()
    }


def main() -> None:
    deals = scoring.load_pipeline()
    today = scoring.reference_date(deals)
    scored, model = scoring.score_open_deals(deals, today)

    records = [
        {
            "id": r.opportunity_id,
            "vendedor": r.sales_agent,
            "manager": r.manager,
            "regiao": r.regional_office,
            "produto": r.product,
            "preco": int(r.sales_price),
            "conta": None if pd.isna(r.account) else r.account,
            "setor": None if pd.isna(r.sector) else r.sector,
            "inicio": None if pd.isna(r.engage_date) else r.engage_date.strftime("%Y-%m-%d"),
            "idade": None if pd.isna(r.age) else int(r.age),
            "lista": r.lista,
            "faixa": r.faixa,
            "fechaEsteMes": bool(r.chance_soon >= scoring.SOON_MIN_CHANCE),
            "valorEsperado": round(r.valor_esperado, 4),
            "score": int(r.score),
        }
        for r in scored.itertuples()
    ]
    closed = deals[deals["deal_stage"].isin(["Won", "Lost"])]
    payload = {
        "hoje": today.strftime("%Y-%m-%d"),
        "cicloMaisLongo": model["longest_cycle"],
        "chancePorIdade": [round(p, 4) for p in model["chance_by_age"][: model["longest_cycle"] + 1]],
        "regras": {
            "reativarAte": scoring.REACTIVATION_MAX_AGE,
            "reativarAteCaro": scoring.REACTIVATION_MAX_AGE_EXPENSIVE,
            "precoCaro": scoring.EXPENSIVE_PRICE,
            "diasEsteMes": scoring.SOON_DAYS,
        },
        "historico": {
            "fechados": int(len(closed)),
            "taxaGanho": round(float((closed["deal_stage"] == "Won").mean()), 3),
            "inicio": deals["engage_date"].min().strftime("%Y-%m-%d"),
        },
        "deals": records,
        "contas": account_profiles(deals, today),
        "historicoMensal": monthly_history(deals),
        "vendedores": seller_profiles(deals),
        "backtest": run_backtest(deals),
        "segmentos": segment_win_rates(deals),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        "window.LEAD_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    counts = scored["lista"].value_counts().to_dict()
    print(f"OK: {len(records)} deals abertos | hoje={payload['hoje']} | {counts}")
    print(f"Abra {OUT.parent / 'index.html'} no navegador.")


if __name__ == "__main__":
    main()
