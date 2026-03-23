"""Evaluation script for OpenAI fine-tuned gpt-4o-mini classifier."""
import pandas as pd
import numpy as np
import json
import os
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (classification_report, confusion_matrix,
                             accuracy_score, f1_score)
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv(".env.local")

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Constants (same as notebook 07 and 11)
RANDOM_STATE = 42
SAMPLE_FRACTION = 0.20
TRAIN_FRACTION = 0.80
FINE_TUNED_MODEL = "ft:gpt-4o-mini-2024-07-18:mcury:optiflow-tickets:DM09m89K"
VALID_CATEGORIES = ["Access", "Administrative rights", "HR Support", "Hardware",
                    "Internal Project", "Miscellaneous", "Purchase", "Storage"]
SYSTEM_PROMPT = ("You are an IT ticket classifier. Classify the ticket into exactly ONE category: "
                 "Access, Administrative rights, HR Support, Hardware, Internal Project, "
                 "Miscellaneous, Purchase, Storage. Respond with ONLY the category name.")

# ── Section 1: Rebuild the same validation set ──
print("=" * 60)
print("PREPARAÇÃO DA AMOSTRA")
print("=" * 60)

csv_path = "data/it_service_tickets.csv"
df = pd.read_csv(csv_path)
print(f"Dataset: {len(df)} tickets")

# Same few-shot exclusion as notebook 07
np.random.seed(RANDOM_STATE)
fewshot_indices = []
for cat in VALID_CATEGORIES:
    cat_data = df[df["Topic_group"] == cat]
    sample_idx = cat_data.sample(n=5, random_state=RANDOM_STATE).index
    fewshot_indices.extend(sample_idx.tolist())

df_remaining = df.drop(index=fewshot_indices)

# Same 20% sample
sample = df_remaining.groupby("Topic_group", group_keys=False).apply(
    lambda x: x.sample(frac=SAMPLE_FRACTION, random_state=RANDOM_STATE)
).reset_index(drop=True)
sample = sample.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

# Same 80/20 split
train_df, val_df = train_test_split(
    sample, test_size=1-TRAIN_FRACTION, random_state=RANDOM_STATE, stratify=sample["Topic_group"]
)
val_df = val_df.reset_index(drop=True)
print(f"Validação: {len(val_df)} tickets")
print(f"Modelo: {FINE_TUNED_MODEL}")

# ── Section 2: Inference with checkpoint ──
print("\n" + "=" * 60)
print("INFERÊNCIA")
print("=" * 60)

def normalize_prediction(pred):
    pred = pred.strip().strip(".").strip()
    for cat in VALID_CATEGORIES:
        if pred.lower() == cat.lower():
            return cat
    for cat in VALID_CATEGORIES:
        if cat.lower() in pred.lower():
            return cat
    return pred

BATCH_SIZE = 200
checkpoint_path = "data/openai_ft_checkpoint.csv"

if os.path.exists(checkpoint_path):
    done = pd.read_csv(checkpoint_path)
    start_idx = len(done)
    all_results = done.to_dict("records")
    print(f"Checkpoint: {start_idx} já processados")
else:
    start_idx = 0
    all_results = []

errors = 0
start_time = time.time()

for i in range(start_idx, len(val_df)):
    row = val_df.iloc[i]
    try:
        response = client.chat.completions.create(
            model=FINE_TUNED_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": str(row["Document"])}
            ],
            max_tokens=10,
            temperature=0
        )
        pred = normalize_prediction(response.choices[0].message.content)
        all_results.append({"true_label": row["Topic_group"], "predicted": pred})
    except Exception as e:
        all_results.append({"true_label": row["Topic_group"], "predicted": "ERROR"})
        errors += 1
        if "rate_limit" in str(e).lower():
            time.sleep(10)
        else:
            time.sleep(3)

    processed = i - start_idx + 1
    if processed % BATCH_SIZE == 0 or i == len(val_df) - 1:
        pd.DataFrame(all_results).to_csv(checkpoint_path, index=False)
        elapsed = time.time() - start_time
        rate = processed / elapsed * 60 if elapsed > 0 else 0
        remaining = (len(val_df) - i - 1) / (rate / 60) if rate > 0 else 0
        print(f"  [{i+1}/{len(val_df)}] {rate:.0f}/min, erros={errors}, "
              f"restante~{remaining/60:.0f}min [checkpoint]")

results_df = pd.DataFrame(all_results)
elapsed = time.time() - start_time
print(f"\nConcluído em {elapsed/60:.1f}min, {errors} erros")

# ── Section 3: Metrics ──
print("\n" + "=" * 60)
print("RESULTADOS: gpt-4o-mini FINE-TUNED")
print("=" * 60)

ft_eval = results_df[results_df["predicted"] != "ERROR"]
ft_acc = accuracy_score(ft_eval["true_label"], ft_eval["predicted"])
ft_f1_macro = f1_score(ft_eval["true_label"], ft_eval["predicted"], average="macro", zero_division=0)
ft_f1_weighted = f1_score(ft_eval["true_label"], ft_eval["predicted"], average="weighted", zero_division=0)

print(f"Acurácia:    {ft_acc:.1%}")
print(f"F1 Macro:    {ft_f1_macro:.3f}")
print(f"F1 Weighted: {ft_f1_weighted:.3f}")
print(f"Erros API:   {len(results_df) - len(ft_eval)}")
print()
print(classification_report(ft_eval["true_label"], ft_eval["predicted"], zero_division=0))

# ── Section 4: Comparison ──
gemini_acc = 0.462
gemini_f1m = 0.476
gemini_f1w = 0.475

print("\n" + "=" * 60)
print("COMPARAÇÃO: Gemini Few-Shot vs OpenAI Fine-Tuned")
print("=" * 60)
print(f"{'Métrica':<20} {'Gemini FS':<15} {'OpenAI FT':<15} {'Delta':<10}")
print("-" * 60)
print(f"{'Acurácia':<20} {gemini_acc:.1%}{'':9} {ft_acc:.1%}{'':9} {ft_acc-gemini_acc:+.1%}")
print(f"{'F1 Macro':<20} {gemini_f1m:.3f}{'':10} {ft_f1_macro:.3f}{'':10} {ft_f1_macro-gemini_f1m:+.3f}")
print(f"{'F1 Weighted':<20} {gemini_f1w:.3f}{'':10} {ft_f1_weighted:.3f}{'':10} {ft_f1_weighted-gemini_f1w:+.3f}")

# Scenario assessment
print(f"\n{'='*60}")
if ft_acc >= 0.70:
    print(f"✅ CENÁRIO B ATINGIDO ({ft_acc:.1%} ≥ 70%) — viável para auto-roteamento parcial")
elif ft_acc >= 0.50:
    print(f"⚠️  ENTRE CENÁRIO A E B ({ft_acc:.1%}) — melhor que few-shot, precisa refinamento")
else:
    print(f"❌ ABAIXO DE 50% ({ft_acc:.1%}) — fine-tuning não foi suficiente")
print(f"{'='*60}")

# ── Section 5: Charts ──
# Confusion matrices
fig, axes = plt.subplots(1, 2, figsize=(18, 8))

gemini_path = "data/llm_checkpoint_few_shot.csv"
if os.path.exists(gemini_path):
    gemini_results = pd.read_csv(gemini_path)
    gemini_eval = gemini_results[gemini_results["predicted"] != "ERROR"]
    cm_gemini = confusion_matrix(gemini_eval["true_label"], gemini_eval["predicted"], labels=VALID_CATEGORIES)
    sns.heatmap(cm_gemini, annot=True, fmt="d", cmap="Oranges",
                xticklabels=VALID_CATEGORIES, yticklabels=VALID_CATEGORIES, ax=axes[0])
    axes[0].set_title(f"Gemini Few-Shot (Acc: {gemini_acc:.1%})")
else:
    axes[0].text(0.5, 0.5, "Gemini results not found", ha="center")
    axes[0].set_title("Gemini Few-Shot (sem dados)")
axes[0].set_xlabel("Predito")
axes[0].set_ylabel("Real")
axes[0].tick_params(axis="x", rotation=45)

cm_ft = confusion_matrix(ft_eval["true_label"], ft_eval["predicted"], labels=VALID_CATEGORIES)
sns.heatmap(cm_ft, annot=True, fmt="d", cmap="Blues",
            xticklabels=VALID_CATEGORIES, yticklabels=VALID_CATEGORIES, ax=axes[1])
axes[1].set_xlabel("Predito")
axes[1].set_ylabel("Real")
axes[1].set_title(f"OpenAI Fine-Tuned (Acc: {ft_acc:.1%})")
axes[1].tick_params(axis="x", rotation=45)

plt.tight_layout()
plt.savefig("process-log/screenshots/p13_openai_vs_gemini_confusion.png", dpi=150, bbox_inches="tight")
print("Salvo: process-log/screenshots/p13_openai_vs_gemini_confusion.png")

# F1 per category
fig, ax = plt.subplots(figsize=(14, 7))
x = np.arange(len(VALID_CATEGORIES))
width = 0.35

ft_cat_f1 = []
for c in VALID_CATEGORIES:
    ft_sub = ft_eval[ft_eval["true_label"] == c]
    ft_correct = (ft_sub["predicted"] == c).sum()
    ft_pred_as_c = (ft_eval["predicted"] == c).sum()
    precision = ft_correct / ft_pred_as_c if ft_pred_as_c > 0 else 0
    recall = ft_correct / len(ft_sub) if len(ft_sub) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    ft_cat_f1.append(f1)

gemini_f1_by_cat = {
    "Access": 0.45, "Administrative rights": 0.22, "HR Support": 0.47,
    "Hardware": 0.54, "Internal Project": 0.64, "Miscellaneous": 0.32,
    "Purchase": 0.77, "Storage": 0.39
}
gemini_cat_f1 = [gemini_f1_by_cat[c] for c in VALID_CATEGORIES]

ax.bar(x - width/2, gemini_cat_f1, width, label="Gemini Few-Shot", color="#f97316", alpha=0.8)
ax.bar(x + width/2, ft_cat_f1, width, label="OpenAI Fine-Tuned", color="#3b82f6", alpha=0.8)
ax.set_xticks(x)
ax.set_xticklabels(VALID_CATEGORIES, rotation=45, ha="right")
ax.set_ylabel("F1 Score")
ax.set_title("F1 por Categoria: Gemini Few-Shot vs OpenAI Fine-Tuned")
ax.legend()
ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
ax.axhline(y=0.7, color="green", linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig("process-log/screenshots/p13_f1_comparison_by_category.png", dpi=150, bbox_inches="tight")
print("Salvo: process-log/screenshots/p13_f1_comparison_by_category.png")

# ── Section 6: Cost ──
print(f"\n{'='*60}")
print("CUSTO")
print(f"{'='*60}")

job = client.fine_tuning.jobs.retrieve('ftjob-66cUigFVpDbozsZaZEppvV8R')
if hasattr(job, 'trained_tokens') and job.trained_tokens:
    train_cost = job.trained_tokens / 1_000_000 * 3.00
    print(f"Tokens treinados: {job.trained_tokens:,}")
    print(f"Custo treino: ~US${train_cost:.2f}")
else:
    print("Tokens treinados: verificar dashboard OpenAI")

val_input_tokens = len(val_df) * 130
val_output_tokens = len(val_df) * 3
inference_cost = val_input_tokens / 1_000_000 * 0.30 + val_output_tokens / 1_000_000 * 1.20
print(f"Custo inferência ({len(val_df)} tickets): ~US${inference_cost:.4f}")

print(f"\n{'Abordagem':<35} {'Custo':<15} {'Acurácia':<10}")
print("-" * 60)
print(f"{'Gemini ZS (20% amostra)':<35} {'~US$0.12':<15} {'40.9%':<10}")
print(f"{'Gemini FS (20% amostra)':<35} {'~US$1.42':<15} {'46.2%':<10}")
print(f"{'OpenAI FT treino (20% dataset)':<35} {'~US$9':<15} {'—':<10}")
print(f"{'OpenAI FT inferência (20% val)':<35} {f'~US${inference_cost:.2f}':<15} {f'{ft_acc:.1%}':<10}")

# Save results
results_df.to_csv("data/openai_ft_results.csv", index=False)
print(f"\nResultados salvos: data/openai_ft_results.csv")

if os.path.exists(checkpoint_path):
    os.remove(checkpoint_path)
    print("Checkpoint removido")

# Per-category F1 summary
print(f"\n{'='*60}")
print("F1 POR CATEGORIA")
print(f"{'='*60}")
print(f"{'Categoria':<25} {'Gemini FS':<12} {'OpenAI FT':<12} {'Delta':<10}")
print("-" * 60)
for i, c in enumerate(VALID_CATEGORIES):
    delta = ft_cat_f1[i] - gemini_cat_f1[i]
    print(f"{c:<25} {gemini_cat_f1[i]:.2f}{'':8} {ft_cat_f1[i]:.2f}{'':8} {delta:+.2f}")

print(f"\nModelo: {FINE_TUNED_MODEL}")
