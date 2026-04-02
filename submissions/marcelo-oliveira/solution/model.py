import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data")

def run_engine():

    # =========================
    # LOAD + MERGE
    # =========================
    sales = pd.read_csv(os.path.join(DATA_PATH, "sales_pipeline.csv"))
    accounts = pd.read_csv(os.path.join(DATA_PATH, "accounts.csv"))
    products = pd.read_csv(os.path.join(DATA_PATH, "products.csv"))
    teams = pd.read_csv(os.path.join(DATA_PATH, "sales_teams.csv"))

    df = sales.merge(accounts, on="account", how="left")
    df = df.merge(products, on="product", how="left")
    df = df.merge(teams, on="sales_agent", how="left")

    df_all = df.copy()

    # =========================
    # NORMALIZAÇÃO
    # =========================
    for col in ["sales_agent", "product", "sector", "office_location", "deal_stage", "manager", "regional_office"]:
        if col in df_all.columns:
            df_all[col] = df_all[col].astype(str).str.lower().str.strip()

    # =========================
    # TARGET
    # =========================
    df_all["won"] = (df_all["deal_stage"] == "won").astype(int)

    # =========================
    # CICLO
    # =========================
    df_all["engage_date"] = pd.to_datetime(df_all["engage_date"], errors="coerce")
    df_all["close_date"] = pd.to_datetime(df_all["close_date"], errors="coerce")

    df_all["sales_cycle"] = (
        df_all["close_date"] - df_all["engage_date"]
    ).dt.days

    # =========================
    # PIPELINE ATIVO
    # =========================
    df_agent = df_all[
        df_all["deal_stage"].isin(["engaging", "prospecting"])
    ].copy()

    df_agent["account"] = df_agent["account"].astype(str).str.strip().str.lower()

    # =========================
    # VALIDAÇÃO
    # =========================
    df_valid = df_agent[
        (df_agent["account"] != "") &
        (df_agent["account"] != "nan")
    ]

    if df_valid.empty:
        return pd.DataFrame()

    # =========================
    # BASE WON
    # =========================
    df_won = df_all[df_all["deal_stage"] == "won"].copy()
    df_won["price_ratio"] = df_won["close_value"] / df_won["sales_price"]

    product_max = df_all.groupby("product")["sales_price"].max().to_dict()

    # =========================
    # LOOP PRINCIPAL
    # =========================
    results = []

    for _, deal in df_valid.iterrows():

        product = deal["product"]
        sector = deal["sector"]
        region_loc = deal["office_location"]
        agent = deal["sales_agent"]

        deal_value = deal["sales_price"] if not pd.isna(deal["sales_price"]) else 0

        levels = [
            ["sales_agent", "product", "sector", "office_location"],
            ["sales_agent", "product", "sector"],
            ["sales_agent", "sector"],
            ["sales_agent", "product"],
            ["sales_agent"]
        ]

        win_rate = 0
        price_ratio = 0
        avg_cycle = np.nan

        for level in levels:

            temp = df_all.copy()
            temp = temp[temp["deal_stage"].isin(["won", "lost"])]
            temp = temp[temp["sales_agent"] == agent]

            if "product" in level:
                temp = temp[temp["product"] == product]
            if "sector" in level:
                temp = temp[temp["sector"] == sector]
            if "office_location" in level:
                temp = temp[temp["office_location"] == region_loc]

            if len(temp) >= 30:

                win_rate = temp["won"].mean()
                avg_cycle = temp["sales_cycle"].mean()

                price = df_won[df_won["sales_agent"] == agent]

                if "product" in level:
                    price = price[price["product"] == product]
                if "sector" in level:
                    price = price[price["sector"] == sector]
                if "office_location" in level:
                    price = price[price["office_location"] == region_loc]

                price_ratio = price["price_ratio"].mean()
                break

        max_value = product_max.get(product, deal_value)
        ticket_norm = deal_value / max_value if max_value > 0 else 0
        price_ratio = 0 if pd.isna(price_ratio) else price_ratio

        score = (
            0.5 * win_rate +
            0.3 * ticket_norm +
            0.2 * price_ratio
        )

        results.append({
            "account": deal["account"],
            "product": product,
            "stage": deal["deal_stage"],
            "sales_cycle": round(avg_cycle, 0) if not pd.isna(avg_cycle) else None,
            "sales_price": round(deal_value, 0),

            "price_target": round(price_ratio * 100, 1),
            "win_rate": round(win_rate * 100, 1),
            "score": round(score, 3),

            # 🔥 NOVOS CAMPOS (corrigem seu erro)
            "sector": deal["sector"],
            "office_location": deal["office_location"],

            "sales_agent": deal["sales_agent"],
            "manager": deal["manager"],
            "regional_office": deal["regional_office"]
        })

    df_result = pd.DataFrame(results)

    df_result = df_result.sort_values(
        by=["score", "sales_cycle"],
        ascending=[False, True]
    )

    df_result["rank"] = range(1, len(df_result) + 1)

    return df_result
