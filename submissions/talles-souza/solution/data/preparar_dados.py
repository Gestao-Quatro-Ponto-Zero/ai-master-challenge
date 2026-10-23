"""Camada de dados do Lead Scorer: junta as 4 tabelas do CRM e grava os fatos de cada deal
e o time de vendas inteiro (os 35 vendedores de sales_teams.csv, inclusive os sem negócio).

Uso: python -X utf8 preparar_dados.py <pasta crm-sales-predictive-analytics> [saida.json]

Só fatos do dataset, sem regra de score: normaliza nomes que não casam entre tabelas,
calcula a idade a partir do último fechamento do dataset e marca as lacunas.
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

# "Hoje" do dataset: o último close_date (o histórico termina em 2017-12-31).
# Contar a idade a partir da data real daria ~9 anos para todos os deals.
NORMALIZA_PRODUTO = {"GTXPro": "GTX Pro"}        # pipeline usa "GTXPro"; o catálogo, "GTX Pro"
NORMALIZA_SETOR = {"technolgy": "technology"}    # erro de digitação em accounts.csv


def carregar(pasta: Path) -> dict[str, pd.DataFrame]:
    return {
        "pipe": pd.read_csv(pasta / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"]),
        "acc": pd.read_csv(pasta / "accounts.csv"),
        "prod": pd.read_csv(pasta / "products.csv"),
        "team": pd.read_csv(pasta / "sales_teams.csv"),
    }


def preparar(t: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.Timestamp]:
    pipe = t["pipe"].copy()
    ref = pipe.close_date.max()

    pipe["produto_normalizado"] = pipe["product"].isin(NORMALIZA_PRODUTO)
    pipe["product"] = pipe["product"].replace(NORMALIZA_PRODUTO)

    acc = t["acc"].copy()
    acc["setor_normalizado"] = acc.sector.isin(NORMALIZA_SETOR)
    acc["sector"] = acc.sector.replace(NORMALIZA_SETOR)

    df = (pipe.merge(t["team"], on="sales_agent", how="left")
              .merge(acc, on="account", how="left")
              .merge(t["prod"], on="product", how="left"))

    aberto = df.deal_stage.isin(["Prospecting", "Engaging"])
    df["aberto"] = aberto
    df["idade_dias"] = (ref - df.engage_date).dt.days.where(aberto)            # só abertos com engage_date
    df["duracao_dias"] = (df.close_date - df.engage_date).dt.days.where(~aberto)  # só fechados
    df["sem_conta"] = df.account.isna()
    df["sem_engage_date"] = df.engage_date.isna()
    df["setor_normalizado"] = df.setor_normalizado.fillna(False).astype(bool)
    return df, ref


FORMATO = 2  # versão do formato do deals.json; o loader do app recusa outra (2 = com vendedores)


def vendedores(team: pd.DataFrame) -> list[dict]:
    """O time inteiro de sales_teams.csv, em ordem de nome: quem não tem negócio também aparece."""
    cols = ["sales_agent", "manager", "regional_office"]
    return team[cols].sort_values("sales_agent").to_dict(orient="records")


def para_json(df: pd.DataFrame, ref: pd.Timestamp, team: pd.DataFrame) -> dict:
    out = df.copy()
    for c in ["engage_date", "close_date"]:
        out[c] = out[c].dt.strftime("%Y-%m-%d")
    out = out.astype(object).where(out.notna(), None)
    return {"formato": FORMATO, "referencia": ref.strftime("%Y-%m-%d"), "total": len(out),
            "vendedores": vendedores(team), "deals": out.to_dict(orient="records")}


def gravar(df: pd.DataFrame, ref: pd.Timestamp, team: pd.DataFrame, saida: Path) -> str:
    """Grava o JSON e, ao lado, `<saida>.sha256` no formato do sha256sum; devolve o hash."""
    dados = json.dumps(para_json(df, ref, team), ensure_ascii=False).encode("utf-8")
    saida.write_bytes(dados)
    hash_hex = hashlib.sha256(dados).hexdigest()
    saida.with_name(saida.name + ".sha256").write_text(f"{hash_hex}  {saida.name}\n", encoding="utf-8")
    return hash_hex


def main():
    pasta = Path(sys.argv[1])
    saida = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).with_name("deals.json")
    tabelas = carregar(pasta)
    df, ref = preparar(tabelas)
    hash_hex = gravar(df, ref, tabelas["team"], saida)
    print(f"{len(df)} deals e {len(tabelas['team'])} vendedores → {saida} "
          f"(referência {ref.date()}, sha256 {hash_hex[:12]}…)")


if __name__ == "__main__":
    main()
