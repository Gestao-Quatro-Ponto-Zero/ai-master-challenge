"""Valida as suposições feitas sobre os 2 datasets do Challenge 002 antes de decidir a abordagem."""
import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 140)

D1 = r"D:\Projetos\Case G4\data\challenge-002-support\customer_support_tickets.csv"
D2 = r"D:\Projetos\Case G4\data\challenge-002-support\all_tickets_processed_improved_v3.csv"


def section(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


# ---------------------------------------------------------------------------
section("DATASET 1 — customer_support_tickets.csv")
# ---------------------------------------------------------------------------
df1 = pd.read_csv(D1)
print(f"Shape: {df1.shape[0]} linhas x {df1.shape[1]} colunas")
print(f"\nColunas: {list(df1.columns)}")

print("\n--- Nulls por coluna ---")
print(df1.isnull().sum())

print("\n--- Ticket Type ---")
print(df1["Ticket Type"].value_counts())

print("\n--- Ticket Priority ---")
print(df1["Ticket Priority"].value_counts())

print("\n--- Ticket Channel ---")
print(df1["Ticket Channel"].value_counts())

print("\n--- Ticket Status ---")
print(df1["Ticket Status"].value_counts())

print("\n--- Customer Satisfaction Rating ---")
print(df1["Customer Satisfaction Rating"].describe())
print(df1["Customer Satisfaction Rating"].value_counts(dropna=False))

# Templating check
placeholder_desc = df1["Ticket Description"].str.contains(r"\{product_purchased\}", regex=True, na=False)
print(f"\n--- Templating check (Ticket Description) ---")
print(f"Linhas com literal '{{product_purchased}}' não substituído: {placeholder_desc.sum()} / {len(df1)} ({placeholder_desc.mean()*100:.1f}%)")

if "Resolution" in df1.columns:
    placeholder_res = df1["Resolution"].astype(str).str.contains(r"\{product_purchased\}", regex=True, na=False)
    print(f"Mesmo check em Resolution: {placeholder_res.sum()} / {df1['Resolution'].notna().sum()} não-nulos ({placeholder_res.mean()*100:.1f}% do total)")

# Unique description check — quão repetitivo é o texto de fato?
print(f"\nDescrições únicas: {df1['Ticket Description'].nunique()} / {len(df1)} ({df1['Ticket Description'].nunique()/len(df1)*100:.1f}%)")
print(f"Comprimento médio da descrição: {df1['Ticket Description'].str.len().mean():.0f} caracteres")

print("\n--- First Response Time / Time to Resolution (amostra + tipo) ---")
print(df1[["First Response Time", "Time to Resolution"]].head(5))
print(df1[["First Response Time", "Time to Resolution"]].dtypes)

print("\n--- Amostra de 3 Resolutions (tickets fechados) ---")
closed = df1[df1["Resolution"].notna()]
for txt in closed["Resolution"].head(3):
    print("-", str(txt)[:150])


# ---------------------------------------------------------------------------
section("DATASET 2 — all_tickets_processed_improved_v3.csv")
# ---------------------------------------------------------------------------
df2 = pd.read_csv(D2)
print(f"Shape: {df2.shape[0]} linhas x {df2.shape[1]} colunas")
print(f"Colunas: {list(df2.columns)}")

print("\n--- Nulls por coluna ---")
print(df2.isnull().sum())

print("\n--- Topic_group (distribuição de classes) ---")
counts = df2["Topic_group"].value_counts()
pct = df2["Topic_group"].value_counts(normalize=True) * 100
dist = pd.DataFrame({"count": counts, "pct": pct.round(1)})
print(dist)

print(f"\nComprimento médio do Document: {df2['Document'].astype(str).str.len().mean():.0f} caracteres")
print(f"Documents únicos: {df2['Document'].nunique()} / {len(df2)} ({df2['Document'].nunique()/len(df2)*100:.1f}%)")

# Preprocessing check — texto tem stopwords comuns (the, is, a) ou não?
import re
sample_text = " ".join(df2["Document"].astype(str).head(200).tolist()).lower()
stopwords_check = {"the": len(re.findall(r"\bthe\b", sample_text)), "is": len(re.findall(r"\bis\b", sample_text)), "a ": len(re.findall(r"\ba\b", sample_text))}
print(f"\nOcorrências de stopwords comuns em amostra de 200 docs: {stopwords_check}")
print("(se muito baixo/zero, confirma que o texto já passou por remoção de stopwords)")

print("\n--- Amostra de 3 Documents por categoria (2 categorias) ---")
for cat in df2["Topic_group"].value_counts().index[:2]:
    print(f"\n[{cat}]")
    for txt in df2[df2["Topic_group"] == cat]["Document"].head(2):
        print("-", str(txt)[:150])

section("FIM DA VALIDAÇÃO")
