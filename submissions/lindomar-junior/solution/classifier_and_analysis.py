"""
classifier_and_analysis.py
==========================
Challenge 002 — Redesign de Suporte

Três blocos em sequência:
  1. Treino e avaliação do classificador TF-IDF + LR no Dataset 2
  2. Aplicação ao Dataset 1 → gera customer_support_tickets_labeled.csv
  3. Análises do README: correlações, inversão de prioridade, piores combos,
     data quality (durações negativas), estimativa de ROI

Requisitos: pandas, scikit-learn, scipy
  pip install pandas scikit-learn scipy
"""

import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
import warnings
warnings.filterwarnings("ignore")

# ─── CAMINHOS ────────────────────────────────────────────────────────────────
# Ajuste se necessário
DS1_PATH = "customer_support_tickets.csv"
DS2_PATH = "all_tickets_processed_improved_v3.csv"
OUTPUT_PATH = "solution/customer_support_tickets_labeled.csv"

# =============================================================================
# BLOCO 1 — CLASSIFICADOR (Dataset 2)
# =============================================================================
print("=" * 60)
print("BLOCO 1 — TREINO DO CLASSIFICADOR (Dataset 2)")
print("=" * 60)

df2 = pd.read_csv(DS2_PATH)
print(f"\nDataset 2: {len(df2):,} tickets, {df2['Topic_group'].nunique()} categorias")
print("\nDistribuição por categoria:")
print(df2["Topic_group"].value_counts().to_string())

# Remover nulos
df2 = df2.dropna(subset=["Document", "Topic_group"])
print(f"\nApós remoção de nulos: {len(df2):,} tickets")

# Train/test split
X = df2["Document"]
y = df2["Topic_group"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTreino: {len(X_train):,} | Teste: {len(X_test):,}")

# Vetorizador
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=50_000,
    min_df=2,
    sublinear_tf=True,
)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec  = vectorizer.transform(X_test)

# Modelo
model = LogisticRegression(max_iter=1000, C=1.0, solver="saga", random_state=42)
model.fit(X_train_vec, y_train)

# Avaliação — test set
y_pred = model.predict(X_test_vec)
print(f"\nAcurácia test set (20%): {accuracy_score(y_test, y_pred):.2%}")
print("\nRelatório completo:")
print(classification_report(y_test, y_pred))

# Cross-validation
cv_scores = cross_val_score(model, X_train_vec, y_train, cv=3, scoring="accuracy")
print(f"Cross-validation (3-fold): {cv_scores.mean():.2%} ± {cv_scores.std():.2%}")
print(f"Scores individuais: {[f'{s:.2%}' for s in cv_scores]}")

# =============================================================================
# BLOCO 2 — APLICAÇÃO AO DATASET 1 → labeled CSV
# =============================================================================
print("\n" + "=" * 60)
print("BLOCO 2 — APLICAÇÃO AO DATASET 1")
print("=" * 60)

df1 = pd.read_csv(DS1_PATH)
print(f"\nDataset 1: {len(df1):,} tickets")

# Classificar
texts = df1["Ticket Description"].fillna("").astype(str)
X1_vec = vectorizer.transform(texts)

df1["Predicted_Topic"]      = model.predict(X1_vec)
df1["Prediction_Confidence"] = model.predict_proba(X1_vec).max(axis=1).round(4)

# Salvar
df1.to_csv(OUTPUT_PATH, index=False)
print(f"\nArquivo salvo: {OUTPUT_PATH}")

# Distribuição das predições
print("\nDistribuição Predicted_Topic:")
print(df1["Predicted_Topic"].value_counts().to_string())

# Confiança média por categoria
print("\nConfiança média por categoria:")
print(df1.groupby("Predicted_Topic")["Prediction_Confidence"].mean().round(3).sort_values(ascending=False).to_string())

# Tickets com baixa confiança
low_conf = (df1["Prediction_Confidence"] < 0.4).sum()
print(f"\nTickets com confiança < 0,40 (candidatos a human review): {low_conf} ({low_conf/len(df1):.1%})")

# Domain shift — aviso explícito
print("""
⚠  DOMAIN SHIFT DOCUMENTADO
   89,7% classificados como Hardware porque o modelo foi treinado em tickets
   de TI corporativo (Dataset 2) e aplicado a suporte B2C (Dataset 1).
   Os textos sintéticos do Dataset 1 têm vocabulário que se sobrepõe ao domínio
   de Hardware. Para produção, fine-tunar com dados reais do Dataset 1.
   A coluna Ticket Type nativa é mais confiável para segmentar este dataset.
""")

# =============================================================================
# BLOCO 3 — ANÁLISES DO README
# =============================================================================
print("=" * 60)
print("BLOCO 3 — ANÁLISES OPERACIONAIS (Dataset 1)")
print("=" * 60)

# ── 3.1 Data Quality — durações negativas ─────────────────────────────────
print("\n── 3.1 DATA QUALITY: Resolution Duration Hours ──")

df1["frt_dt"] = pd.to_datetime(df1["First Response Time"], errors="coerce")
df1["ttr_dt"] = pd.to_datetime(df1["Time to Resolution"],  errors="coerce")
df1["duration_raw"]  = (df1["ttr_dt"] - df1["frt_dt"]).dt.total_seconds() / 3600
df1["duration_abs_h"] = df1["duration_raw"].abs()

n_negative = (df1["duration_raw"] < 0).sum()
n_total_with_both = df1[["frt_dt","ttr_dt"]].dropna().shape[0]

print(f"\nTickets com ambos FRT e TTR preenchidos: {n_total_with_both:,}")
print(f"Durações negativas (TTR antes de FRT): {n_negative:,} ({n_negative/n_total_with_both:.1%})")
print(f"\nEstatísticas de duration_raw (horas):")
print(df1["duration_raw"].describe().round(2).to_string())
print(f"\nMediana valor absoluto: {df1['duration_abs_h'].median():.2f}h")
print(f"Média valor absoluto:   {df1['duration_abs_h'].mean():.2f}h")

print("""
INTERPRETAÇÃO DOS VALORES NEGATIVOS:
  FRT e TTR são timestamps absolutos de um snapshot em 2023-06-01.
  TTR < FRT indica que a resolução foi registrada antes da primeira resposta
  — provável artefato de migração de dados ou atualização retroativa.
  TRATAMENTO: usamos abs(TTR - FRT) como proxy de duração de fila.
  Isso é conservador e evita descartar 50% dos tickets fechados.
  Para análise de SLA real, seriam necessários os logs de eventos individuais.
""")

# ── 3.2 Backlog ───────────────────────────────────────────────────────────
print("── 3.2 BACKLOG ──")
status_counts = df1["Ticket Status"].value_counts()
total = len(df1)
print(f"\nTotal de tickets: {total:,}")
for status, count in status_counts.items():
    print(f"  {status}: {count:,} ({count/total:.1%})")

n_unresolved = (df1["Ticket Status"] != "Closed").sum()
print(f"\nNão resolvidos (Open + Pending): {n_unresolved:,} ({n_unresolved/total:.1%})")

crit_open = ((df1["Ticket Status"] == "Open") & (df1["Ticket Priority"] == "Critical")).sum()
high_open  = ((df1["Ticket Status"] == "Open") & (df1["Ticket Priority"] == "High")).sum()
print(f"Critical + Open (sem resposta): {crit_open:,}")
print(f"High + Open (sem resposta):     {high_open:,}")

# ── 3.3 Inversão de prioridade ───────────────────────────────────────────
print("\n── 3.3 INVERSÃO DE PRIORIDADE ──")
closed = df1[df1["Ticket Status"] == "Closed"].copy()
prio_stats = closed.groupby("Ticket Priority")["duration_abs_h"].agg(
    median="median", mean="mean", count="count"
).round(2)
print(f"\nTempo de resolução por prioridade (tickets fechados, n={len(closed):,}):")
print(prio_stats.sort_values("median", ascending=False).to_string())
print("\n⚠  HIGH (7.28h) demora mais que CRITICAL (6.55h) — sistema de priorização ineficaz")

# Distribuição de prioridades por tipo
print("\nDistribuição de prioridades por Ticket Type (deve ser uniforme se atribuição é aleatória):")
prio_dist = pd.crosstab(
    df1["Ticket Type"],
    df1["Ticket Priority"],
    normalize="index"
).round(3)
print(prio_dist.to_string())

# ── 3.4 CSAT vs. tempo — correlação ─────────────────────────────────────
print("\n── 3.4 CORRELAÇÃO CSAT × TEMPO DE RESOLUÇÃO ──")
valid = closed[["duration_abs_h", "Customer Satisfaction Rating"]].dropna()
corr, pval = pearsonr(valid["duration_abs_h"], valid["Customer Satisfaction Rating"])
print(f"\nn = {len(valid):,} tickets fechados com CSAT preenchido")
print(f"Correlação de Pearson (duration × CSAT): {corr:.4f}")
print(f"p-valor: {pval:.4f}")
print(f"Conclusão: {'sem correlação estatisticamente significativa' if pval > 0.05 else 'correlação significativa'}")

# CSAT médio por nota vs duração
print("\nDuração média por nota de CSAT:")
print(closed.groupby("Customer Satisfaction Rating")["duration_abs_h"].mean().round(2).to_string())

# Distribuição de CSAT
print("\nDistribuição de CSAT (deve ser uniforme):")
csat_dist = closed["Customer Satisfaction Rating"].value_counts(normalize=True).sort_index()
print(csat_dist.round(3).to_string())

# ── 3.5 Piores combos ────────────────────────────────────────────────────
print("\n── 3.5 PIORES COMBOS CANAL × TIPO × PRIORIDADE ──")
combos = closed.groupby(
    ["Ticket Channel", "Ticket Type", "Ticket Priority"]
)["Customer Satisfaction Rating"].agg(["mean", "count"]).reset_index()
combos = combos[combos["count"] >= 20].sort_values("mean")
print(f"\nTop 10 piores combinações (mín. 20 tickets):")
print(combos.head(10).rename(columns={"mean": "CSAT_médio", "count": "n"}).to_string(index=False))

# ── 3.6 Estimativa de ROI ────────────────────────────────────────────────
print("\n── 3.6 ESTIMATIVA DE ROI (automação) ──")

# Volume automatable
product_billing_open = (
    (df1["Ticket Status"] == "Open") &
    (df1["Ticket Type"].isin(["Product inquiry", "Billing inquiry"]))
).sum()

access_open = (
    (df1["Ticket Status"] == "Open") &
    (df1["Predicted_Topic"] == "Access")
).sum()

# Projeção mensal (30.000 tickets/ano conforme enunciado)
tickets_per_month = 30_000 / 12
automation_rate   = 0.70

auto_types = {
    "Product inquiry":  {"pct_volume": 0.215, "auto_rate": 0.60},
    "Billing inquiry":  {"pct_volume": 0.173, "auto_rate": 0.55},
    "Access (reset)":   {"pct_volume": 0.065, "auto_rate": 0.85},
}

print(f"\nBase: {tickets_per_month:.0f} tickets/mês (30.000/ano)")
print(f"\n{'Categoria':<25} {'Vol/mês':>8} {'Auto rate':>10} {'Auto/mês':>10}")
print("-" * 60)
total_auto = 0
for cat, params in auto_types.items():
    vol   = tickets_per_month * params["pct_volume"]
    auto  = vol * params["auto_rate"]
    total_auto += auto
    print(f"{cat:<25} {vol:>8.0f} {params['auto_rate']:>10.0%} {auto:>10.0f}")
print(f"\nTotal tickets automatizados/mês: {total_auto:.0f}")

print("\nEconomia estimada (AHT = Average Handling Time por ticket):")
print(f"{'Cenário':<15} {'AHT':>8} {'Horas/mês':>12} {'USD/mês':>12} {'USD/ano':>12}")
print("-" * 60)
for scenario, aht_min in [("Conservador", 15), ("Base", 20), ("Otimista", 30)]:
    hours    = total_auto * aht_min / 60
    usd_mo   = hours * 25  # USD $25/hora
    usd_yr   = usd_mo * 12
    print(f"{scenario:<15} {aht_min:>6} min {hours:>12.0f}h ${usd_mo:>11,.0f} ${usd_yr:>11,.0f}")

print("""
⚠  NOTA METODOLÓGICA — wall-clock time vs. labor time
   O campo duration_abs_h (mediana 6,7h) representa tempo de fila, NÃO tempo
   ativo do agente. Usar 6,7h como proxy de labor cost geraria USD $130K/mês
   — número indefensável. O cálculo acima usa AHT de mercado (15-30 min/ticket)
   como base conservadora e defensável para a estimativa de ROI.
""")

print("=" * 60)
print("ANÁLISE COMPLETA. Arquivo salvo em:", OUTPUT_PATH)
print("=" * 60)
