"""01 — Perfil do Dataset 1 (Customer Support Tickets).

Objetivo: antes de procurar gargalos, verificar se os dados aguentam a análise.
Uso: python 01_profile_ds1.py <caminho/customer_support_tickets.csv>
"""
import sys
import pandas as pd

path = sys.argv[1]
df = pd.read_csv(path)
pd.set_option("display.width", 200, "display.max_columns", 30, "display.max_colwidth", 120)

print("== shape", df.shape)
print("\n== missing por coluna")
print(df.isna().sum())

print("\n== missing por status")
print(df.groupby("Ticket Status")[["First Response Time", "Time to Resolution",
                                    "Customer Satisfaction Rating", "Resolution"]]
      .apply(lambda g: g.isna().mean().round(3)))

for c in ["Ticket Type", "Ticket Status", "Ticket Priority", "Ticket Channel",
          "Customer Gender", "Product Purchased", "Ticket Subject"]:
    print(f"\n== {c} (n únicos={df[c].nunique()})")
    print(df[c].value_counts().head(20).to_string())

print("\n== satisfação")
print(df["Customer Satisfaction Rating"].value_counts().sort_index())

# Tempos: são durações ou timestamps?
print("\n== amostra de First Response Time / Time to Resolution")
print(df[["First Response Time", "Time to Resolution", "Date of Purchase"]].dropna().head(8))
frt = pd.to_datetime(df["First Response Time"], errors="coerce")
ttr = pd.to_datetime(df["Time to Resolution"], errors="coerce")
dop = pd.to_datetime(df["Date of Purchase"], errors="coerce")
print("\nFRT range:", frt.min(), "->", frt.max())
print("TTR range:", ttr.min(), "->", ttr.max())
print("Date of Purchase range:", dop.min(), "->", dop.max())
both = frt.notna() & ttr.notna()
delta_h = (ttr - frt)[both].dt.total_seconds() / 3600
print(f"\nTickets com FRT e TTR: {both.sum()}")
print(f"TTR ANTES da primeira resposta (delta<0): {(delta_h < 0).sum()} ({(delta_h < 0).mean():.1%})")
print("delta (TTR - FRT) em horas:\n", delta_h.describe().round(2))

# Texto: placeholders e padrão das resoluções
desc = df["Ticket Description"].astype(str)
print("\n== Ticket Description")
print("contém '{product_purchased}':", desc.str.contains(r"\{product_purchased\}").mean().round(3))
print("contém algum '{...}':", desc.str.contains(r"\{[^}]+\}").mean().round(3))
placeholders = desc.str.findall(r"\{[^}]+\}").explode().value_counts()
print("placeholders:\n", placeholders.head(10).to_string())
# a descrição tem relação com o subject / produto?
first_sent = desc.str.split(r"(?<=[.!?])\s", n=1, regex=True).str[0]
print("frases iniciais distintas:", first_sent.nunique(), "de", len(first_sent))
print("top frases iniciais:\n", first_sent.value_counts().head(8).to_string())
mentions_product = [p.lower() in d.lower() for p, d in zip(df["Product Purchased"], desc)]
print("descrição menciona o produto comprado (literal):", round(sum(mentions_product) / len(df), 3))

print("\n== amostras completas (5)")
for _, r in df.sample(5, random_state=7).iterrows():
    print(f"\n[{r['Ticket Type']} | {r['Ticket Subject']} | {r['Product Purchased']} | {r['Ticket Priority']} | {r['Ticket Channel']}]")
    print("DESC:", r["Ticket Description"][:400])
    print("RESOLUTION:", r["Resolution"])

res = df["Resolution"].dropna().astype(str)
print("\n== Resolution: n", len(res), "| únicos", res.nunique(),
      "| nº palavras médio", res.str.split().str.len().mean().round(1))
