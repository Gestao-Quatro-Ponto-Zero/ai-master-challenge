"""Primeira passada: estrutura, tipos, qualidade, relações entre tabelas."""
import pandas as pd
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

acc = pd.read_csv(DATA / "accounts.csv")
prod = pd.read_csv(DATA / "products.csv")
team = pd.read_csv(DATA / "sales_teams.csv")
pipe = pd.read_csv(DATA / "sales_pipeline.csv")

def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)

section("ACCOUNTS")
print(f"shape={acc.shape}")
print(acc.dtypes)
print("\nnulls:")
print(acc.isna().sum())
print("\nhead:")
print(acc.head(3))

section("PRODUCTS")
print(f"shape={prod.shape}")
print(prod.dtypes)
print(prod)

section("SALES_TEAMS")
print(f"shape={team.shape}")
print(team.dtypes)
print("\nnulls:")
print(team.isna().sum())
print("\nhead:")
print(team.head(5))
print(f"\nmanagers únicos: {team['manager'].nunique()}")
print(f"escritórios únicos: {team['regional_office'].nunique()}")
print("\nvendedores por manager:")
print(team.groupby("manager").size())
print("\nvendedores por escritório:")
print(team.groupby("regional_office").size())

section("SALES_PIPELINE")
print(f"shape={pipe.shape}")
print(pipe.dtypes)
print("\nnulls:")
print(pipe.isna().sum())
print("\nhead:")
print(pipe.head(3))
print(f"\ndeal_stage:")
print(pipe["deal_stage"].value_counts())

section("INTEGRIDADE REFERENCIAL")
# accounts ligado em pipe.account
unmatched_acc = set(pipe["account"].dropna()) - set(acc["account"])
print(f"contas no pipeline mas não em accounts: {len(unmatched_acc)}")
unmatched_prod = set(pipe["product"].dropna()) - set(prod["product"])
print(f"produtos no pipeline não em products: {unmatched_prod}")
unmatched_agent = set(pipe["sales_agent"].dropna()) - set(team["sales_agent"])
print(f"vendedores no pipeline não em teams: {unmatched_agent}")
print(f"\npipeline sem account: {pipe['account'].isna().sum()}")
print(f"pipeline sem product: {pipe['product'].isna().sum()}")
print(f"pipeline sem sales_agent: {pipe['sales_agent'].isna().sum()}")
