"""
Gerador de dataset sintético compatível com o challenge 003 — Lead Scorer.

ESTE ARQUIVO É UM FALLBACK: a intenção é usar os dados REAIS do Kaggle
(dataset `agungpambudi/crm-sales-predictive-analytics`).

Quando os CSVs reais estiverem em `data/`, este gerador NÃO é executado.
Ele só existe para destravar o desenvolvimento local quando o download
do Kaggle não está disponível (requer credenciais).

Documentação transparente desta decisão está em:
- process-log/PROCESS_LOG.md
- README.md principal da submissão
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(seed=42)
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# --- accounts.csv ----------------------------------------------------------
def gen_accounts(n: int = 85) -> pd.DataFrame:
    sectors = [
        "Technology", "Finance", "Healthcare", "Manufacturing",
        "Retail", "Education", "Media", "Logistics",
    ]
    countries = ["USA", "Brazil", "UK", "Germany", "Canada", "Australia"]
    acquisition_channels = ["Inbound", "Outbound", "Partner", "Event", "Referral"]
    parent_companies = ["Acme Corp", "Globex", "Initech", "Umbrella", "Stark Industries", None]

    rows = []
    for i in range(1, n + 1):
        revenue = int(RNG.lognormal(10, 1.2))  # ~$20k a $10M+
        employees = int(max(5, RNG.lognormal(6, 1.5)))
        rows.append({
            "account": f"account_{i:04d}",
            "industry": RNG.choice(sectors),
            "country": RNG.choice(countries),
            "acquisition_channel": RNG.choice(acquisition_channels),
            "revenue": revenue,
            "employees": employees,
            "parent_company": RNG.choice(parent_companies),
            "has_trial": bool(RNG.random() < 0.18),
        })
    return pd.DataFrame(rows)


# --- products.csv ----------------------------------------------------------
def gen_products() -> pd.DataFrame:
    # 7 produtos — catálogo de SaaS B2B
    catalog = [
        ("GTX Basic",    "S1", 1200),
        ("GTX Pro",      "S2", 5000),
        ("GTX Enterprise","S3", 25000),
        ("CRM Connect",  "S4", 800),
        ("Analytics Plus","S5", 3200),
        ("SecureShield", "S6", 1500),
        ("API Gateway",  "S7", 4500),
    ]
    rows = []
    for name, series, price in catalog:
        rows.append({
            "product": name,
            "series": series,
            "sales_price": price,
        })
    return pd.DataFrame(rows)


# --- sales_teams.csv -------------------------------------------------------
def gen_sales_teams(n: int = 35) -> pd.DataFrame:
    first_names = ["Anna", "Breno", "Carla", "Diego", "Eliane", "Felipe", "Gisele",
                   "Henrique", "Iara", "João", "Karen", "Leandro", "Maria", "Nuno",
                   "Olivia", "Paulo", "Renata", "Sandro", "Tatiana", "Ulisses",
                   "Vanessa", "Wagner", "Xuxa", "Yuri", "Zara", "Bianca",
                   "Caio", "Denis", "Eduarda", "Fábio", "Gabriel", "Heloísa",
                   "Igor", "Jacqueline", "Lívia"]
    managers = ["Diana Reinehr", "Melvin Marsac", "Kym Gladwell"]
    offices = ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba", "Recife"]

    rows = []
    for i in range(n):
        name = first_names[i % len(first_names)] + " " + RNG.choice(
            ["Silva", "Souza", "Alves", "Pereira", "Costa"]
        )
        rows.append({
            "sales_agent": name,
            "manager": RNG.choice(managers),
            "regional_office": RNG.choice(offices),
        })
    return pd.DataFrame(rows)


# --- sales_pipeline.csv ----------------------------------------------------
def gen_sales_pipeline(accounts: pd.DataFrame, products: pd.DataFrame,
                       sales_teams: pd.DataFrame, n: int = 8800) -> pd.DataFrame:
    acc_list = accounts["account"].tolist()
    prod_list = products["product"].tolist()
    agent_list = sales_teams["sales_agent"].tolist()

    # Cada agente tem win rate latente — usado depois na feature "agent track record"
    agent_winrate = {
        agent: float(np.clip(RNG.normal(0.48, 0.18), 0.10, 0.85))
        for agent in agent_list
    }

    stages_raw = RNG.choice(
        ["Prospecting", "Engaging", "Won", "Lost"],
        size=n,
        p=[0.25, 0.28, 0.27, 0.20],
    )

    # Datas: engage_date em 2024-01-01 a 2025-12-01
    base = pd.Timestamp("2024-01-01")
    engage_offsets = RNG.integers(0, 700, size=n)
    engage_dates = base + pd.to_timedelta(engage_offsets, unit="D")

    # close_date: média de 45 dias após engage; nulos para Prospecting/Engaging abertos
    close_offsets = RNG.integers(1, 120, size=n)
    close_dates = engage_dates + pd.to_timedelta(close_offsets, unit="D")
    close_dates = close_dates.where(
        np.isin(stages_raw, ["Won", "Lost"]), pd.NA
    )

    # close_value: depende do produto e do outcome
    rows = []
    for i in range(n):
        prod_name = RNG.choice(prod_list)
        prod_price = products.loc[products["product"] == prod_name, "sales_price"].iloc[0]
        # accounts influenciam valor
        acc = RNG.choice(acc_list)
        acc_row = accounts.loc[accounts["account"] == acc].iloc[0]
        size_factor = np.log1p(acc_row["employees"]) / 10
        base_value = int(prod_price * max(0.2, size_factor + RNG.normal(0, 0.3)))
        base_value = max(50, base_value)

        stage = stages_raw[i]
        close_val = 0
        if stage == "Won":
            close_val = base_value
        elif stage == "Lost":
            close_val = 0
        # Prospecting / Engaging: valor esperado (não realizado)
        else:
            close_val = int(base_value * 0.6)

        rows.append({
            "opportunity_id": f"OPP_{i:05d}",
            "sales_agent": RNG.choice(agent_list),
            "product": prod_name,
            "account": acc,
            "deal_stage": stage,
            "engage_date": engage_dates[i].strftime("%m/%d/%Y"),
            "close_date": close_dates[i].strftime("%m/%d/%Y")
            if pd.notna(close_dates[i]) else "",
            "close_value": close_val,
        })

    df = pd.DataFrame(rows)
    # Anexar o win_rate por agente para uso posterior (não faz parte do dataset original
    # mas deixamos como arquivo auxiliar)
    winrate_df = pd.DataFrame(
        [{"sales_agent": k, "win_rate": v} for k, v in agent_winrate.items()]
    )
    return df, winrate_df


def main() -> None:
    print("Gerando dataset sintético compatível com challenge 003...")

    accounts = gen_accounts()
    products = gen_products()
    sales_teams = gen_sales_teams()
    pipeline, winrate = gen_sales_pipeline(accounts, products, sales_teams)

    accounts.to_csv(DATA_DIR / "accounts.csv", index=False)
    products.to_csv(DATA_DIR / "products.csv", index=False)
    sales_teams.to_csv(DATA_DIR / "sales_teams.csv", index=False)
    pipeline.to_csv(DATA_DIR / "sales_pipeline.csv", index=False)

    # Auxiliar: win_rate por agente, calculado do dataset
    # (em produção seria derivado on-the-fly — aqui como sanity check)
    winrate_path = DATA_DIR / "_agent_winrate_synth.csv"
    winrate.to_csv(winrate_path, index=False)

    print(f"OK — arquivos gerados em {DATA_DIR}")
    for p in sorted(DATA_DIR.glob("*.csv")):
        print(f"  - {p.name}: {p.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
