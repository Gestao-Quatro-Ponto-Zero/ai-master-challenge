"""Limpa os CSVs do CRM e gera os arquivos de carga (seed) para o Supabase.

Uso:
    python scripts/preparar_dados.py

Entradas:  data/*.csv (originais do dataset CRM Sales Predictive Analytics)
Saídas:    data_limpa/*.csv  e  sql/seed/*.sql
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "data"
DESTINO_CSV = RAIZ / "data_limpa"
DESTINO_SQL = RAIZ / "sql" / "seed"
LOTE = 1500  # linhas por arquivo de INSERT

# Correções encontradas na análise exploratória (seção 2 do notebook)
CORRECOES_PRODUTO = {"GTXPro": "GTX Pro"}
CORRECOES_SETOR = {"technolgy": "technology"}
CORRECOES_PAIS = {"Philipines": "Philippines"}


def carregar():
    accounts = pd.read_csv(ORIGEM / "accounts.csv")
    products = pd.read_csv(ORIGEM / "products.csv")
    teams = pd.read_csv(ORIGEM / "sales_teams.csv")
    pipeline = pd.read_csv(ORIGEM / "sales_pipeline.csv")

    pipeline["product"] = pipeline["product"].replace(CORRECOES_PRODUTO)
    accounts["sector"] = accounts["sector"].replace(CORRECOES_SETOR)
    accounts["office_location"] = accounts["office_location"].replace(CORRECOES_PAIS)

    # Integridade: toda chave estrangeira precisa existir
    assert set(pipeline["product"]) <= set(products["product"]), "produto fora do catálogo"
    assert set(pipeline["sales_agent"]) <= set(teams["sales_agent"]), "vendedor fora do cadastro"
    assert set(pipeline["account"].dropna()) <= set(accounts["account"]), "conta fora do cadastro"
    assert pipeline["opportunity_id"].is_unique, "opportunity_id duplicado"
    return {"products": products, "sales_teams": teams, "accounts": accounts, "sales_pipeline": pipeline}


def literal(valor):
    if pd.isna(valor):
        return "null"
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return repr(int(valor)) if float(valor).is_integer() else repr(float(valor))
    return "'" + str(valor).replace("'", "''") + "'"


def gerar_inserts(nome, df):
    colunas = ", ".join(df.columns)
    linhas = ["(" + ", ".join(literal(v) for v in registro) + ")" for registro in df.itertuples(index=False)]
    arquivos = []
    for i in range(0, len(linhas), LOTE):
        parte = linhas[i:i + LOTE]
        sql = f"insert into public.{nome} ({colunas}) values\n" + ",\n".join(parte) + "\non conflict do nothing;\n"
        arquivos.append(sql)
    return arquivos


def main():
    DESTINO_CSV.mkdir(exist_ok=True)
    DESTINO_SQL.mkdir(parents=True, exist_ok=True)
    tabelas = carregar()
    ordem = ["products", "sales_teams", "accounts", "sales_pipeline"]  # respeita as chaves estrangeiras
    n = 0
    for nome in ordem:
        df = tabelas[nome]
        df.to_csv(DESTINO_CSV / f"{nome}.csv", index=False)
        for parte in gerar_inserts(nome, df):
            n += 1
            (DESTINO_SQL / f"{n:02d}_{nome}.sql").write_text(parte, encoding="utf-8")
        print(f"{nome:<15} {len(df):>5} linhas")
    print(f"{n} arquivos de carga em {DESTINO_SQL}")


if __name__ == "__main__":
    main()
