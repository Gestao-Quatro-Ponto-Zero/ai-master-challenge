"""Validação dos ACs da SPEC do Prompt 03 contra scoring.py."""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np

from scoring import score_deal, score_pipeline, DealScore

DATA = Path(__file__).resolve().parent / "data"
TODAY = pd.Timestamp("2017-12-31")

print("=" * 70)
print("VALIDAÇÃO DOS CRITÉRIOS DE ACEITAÇÃO — SPEC Prompt 03")
print("=" * 70)

# Carregar dados
pipeline = pd.read_csv(DATA / "sales_pipeline.csv")
accounts = pd.read_csv(DATA / "accounts.csv")
products = pd.read_csv(DATA / "products.csv")
sales_teams = pd.read_csv(DATA / "sales_teams.csv")

scored = score_pipeline(pipeline, accounts, products, sales_teams, today=TODAY)

# AC1: todo deal aberto tem score em [0,100]
n_out_of_range = ((scored["score"] < 0) | (scored["score"] > 100)).sum()
print(f"\nAC1 — Score em [0,100]:")
print(f"  Deals scored: {len(scored)}")
print(f"  Fora do range [0,100]: {n_out_of_range}  → {'PASS' if n_out_of_range == 0 else 'FAIL'}")
print(f"  min={scored['score'].min():.2f}  mean={scored['score'].mean():.2f}  max={scored['score'].max():.2f}")

# AC8: top 10 deals por score, >=7 devem ser Engaging
top10 = scored.nlargest(10, "score")
engaging_count = (top10["deal_stage"] == "Engaging").sum()
print(f"\nAC8 — Top 10 deals por score, ≥7 Engaging:")
print(f"  Engaging no top 10: {engaging_count}/10  → {'PASS' if engaging_count >= 7 else 'FAIL'}")
print(f"  Stages no top 10: {top10['deal_stage'].value_counts().to_dict()}")

# AC5: determinismo — rodar 2x e comparar
scored2 = score_pipeline(pipeline, accounts, products, sales_teams, today=TODAY)
deterministic = scored["score"].round(2).equals(scored2["score"].round(2))
print(f"\nAC5 — Determinismo (rodar 2x → idêntico):")
print(f"  Determinístico: {deterministic}  → {'PASS' if deterministic else 'FAIL'}")

# AC2: components tem 6 chaves
sample_score = score_deal(scored.iloc[0], {a: 0.5 for a in scored["sales_agent"].unique()}, TODAY) if False else None
# usando o scored diretamente: pega primeiro deal e recombina
row = scored.iloc[0].copy()
agent_winrate = {a: 0.5 for a in pipeline["sales_agent"].unique()}
result = score_deal(row, agent_winrate, TODAY)
n_components = len(result.components)
print(f"\nAC2 — Breakdown com 6 componentes:")
print(f"  Componentes: {n_components}  → {'PASS' if n_components == 6 else 'FAIL'}")
print(f"  Nomes: {[c.name for c in result.components]}")

# AC3: subscores em [0,100], labels em PT-BR
all_subscores_ok = all(0 <= c.subscore <= 100 for c in result.components)
all_labels_ok = all(isinstance(c.label_ptbr, str) and len(c.label_ptbr) > 5 for c in result.components)
print(f"\nAC3 — Subscores [0,100] + labels PT-BR:")
print(f"  Subscores ok: {all_subscores_ok}  → {'PASS' if all_subscores_ok else 'FAIL'}")
print(f"  Labels ok: {all_labels_ok}  → {'PASS' if all_labels_ok else 'FAIL'}")

# AC4: score final = sum(subscore × weight)
recomputed = sum(c.contribution for c in result.components)
diff = abs(recomputed - result.total_score)
print(f"\nAC4 — Score = sum(subscore × weight):")
print(f"  Recomputado: {recomputed:.4f}  |  Retornado: {result.total_score:.4f}")
print(f"  Diferença: {diff:.6f}  → {'PASS' if diff < 0.01 else 'FAIL'}")

# AC7 / Edge E1: deal sem engage_date → velocity=0 e label específico
row_nat = row.copy()
row_nat["engage_date"] = pd.NaT
result_nat = score_deal(row_nat, agent_winrate, TODAY)
vel_comp = next(c for c in result_nat.components if c.name == "velocity")
print(f"\nAC7 / E1 — engage_date=NaT:")
print(f"  velocity subscore: {vel_comp.subscore}  → {'PASS' if vel_comp.subscore == 0.0 else 'FAIL'}")
print(f"  label: '{vel_comp.label_ptbr}'")
has_semdados = "sem data" in vel_comp.label_ptbr.lower()
print(f"  label menciona 'sem data': {has_semdados}  → {'PASS' if has_semdados else 'FAIL'}")

# Distribuição não-bimodal (sanity check 1)
q1 = scored["score"].quantile(0.25)
q3 = scored["score"].quantile(0.75)
print(f"\nSanity — Distribuição não-bimodal:")
print(f"  q1={q1:.1f}  median={scored['score'].median():.1f}  q3={q3:.1f}")
print(f"  std={scored['score'].std():.2f}")
unique_scores = scored["score"].nunique()
print(f"  Scores únicos: {unique_scores}  → {'PASS' if unique_scores > 50 else 'WARN'}")

print("\n" + "=" * 70)
print("VALIDAÇÃO COMPLETA")
print("=" * 70)
