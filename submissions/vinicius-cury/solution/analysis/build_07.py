import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata["kernelspec"] = {"display_name": "optiflow", "language": "python", "name": "optiflow"}

cells = []

def md(src):
    cells.append(nbf.v4.new_markdown_cell(src))

def code(src):
    cells.append(nbf.v4.new_code_cell(src))

# Cell 0: Title
md("""# 07 — Classificação por LLM: Dataset 2 (IT Service Tickets)

## Objetivo
Testar classificação de tickets de TI usando **Gemini 2.5 Flash Lite** com duas abordagens:
1. **Zero-shot** — apenas instrução, sem exemplos
2. **Few-shot** — 5 exemplos aleatórios por categoria no prompt

Usamos 20% do dataset (~9.500 tickets) para controle de custo.

### Sistema de Fila com Checkpoint
- Processa em lotes de 200 tickets
- Salva progresso após cada lote em `data/llm_checkpoint_{round}.csv`
- Se interrompido, retoma de onde parou
- Sem risco de timeout""")

# Cell 1: Setup
code("""import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (classification_report, confusion_matrix, 
                            accuracy_score, f1_score)
import time
import os
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv(".env.local")
api_key = os.getenv("GOOGLE_AI_API_KEY")

import google.generativeai as genai
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")
print("Gemini 2.5 Flash Lite configurado")

RANDOM_STATE = 42
SAMPLE_FRACTION = 0.20
BATCH_SIZE = 200
CHECKPOINT_DIR = "data"

csv_path = "data/it_service_tickets.csv"
df = pd.read_csv(csv_path)
print(f"Dataset carregado: {len(df)} tickets")
print(f"Distribuicao de categorias:")
print(df["Topic_group"].value_counts().to_string())""")

# Cell 2: MD
md("## Secao 1: Exploracao do Dataset")

# Cell 3: Exploration
code("""fig, axes = plt.subplots(1, 2, figsize=(16, 6))

cat_counts = df["Topic_group"].value_counts()
axes[0].barh(cat_counts.index, cat_counts.values, color="#3b82f6")
axes[0].set_title("Distribuicao de Categorias")
axes[0].set_xlabel("Quantidade de Tickets")
axes[0].invert_yaxis()

df["text_len"] = df["Document"].str.len()
axes[1].hist(df["text_len"], bins=50, color="#f97316", alpha=0.7)
axes[1].set_title("Distribuicao do Tamanho dos Textos")
axes[1].set_xlabel("Caracteres")
axes[1].set_ylabel("Frequencia")

plt.tight_layout()
plt.savefig("process-log/screenshots/p5_llm_dataset_overview.png", dpi=150, bbox_inches="tight")
plt.show()

print("Exemplos por categoria:")
for cat in sorted(df["Topic_group"].unique()):
    samples = df[df["Topic_group"] == cat]["Document"].head(2).tolist()
    print(f"\\n--- {cat} ---")
    for s in samples:
        print(f'  "{s[:120]}..."')""")

# Cell 4: MD
md("## Secao 2: Preparacao da Amostra e Exemplos Few-Shot")

# Cell 5: Sample prep
code("""VALID_CATEGORIES = ["Access", "Administrative rights", "HR Support", "Hardware", 
                    "Internal Project", "Miscellaneous", "Purchase", "Storage"]

np.random.seed(RANDOM_STATE)
fewshot_examples = []
fewshot_indices = []
for cat in VALID_CATEGORIES:
    cat_data = df[df["Topic_group"] == cat]
    sample_idx = cat_data.sample(n=5, random_state=RANDOM_STATE).index
    fewshot_indices.extend(sample_idx.tolist())
    for idx in sample_idx:
        fewshot_examples.append({"text": df.loc[idx, "Document"], "category": cat})

print(f"Exemplos few-shot reservados: {len(fewshot_examples)} ({len(VALID_CATEGORIES)} x 5)")

df_remaining = df.drop(index=fewshot_indices)
sample = df_remaining.groupby("Topic_group", group_keys=False).apply(
    lambda x: x.sample(frac=SAMPLE_FRACTION, random_state=RANDOM_STATE)
).reset_index(drop=True)
sample = sample.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

print(f"Amostra de teste: {len(sample)} tickets ({len(sample)/len(df)*100:.1f}%)")
print(f"Distribuicao:")
print(sample["Topic_group"].value_counts().to_string())""")

# Cell 6: MD
md("## Secao 3: Prompts e Sistema de Fila")

# Cell 7: Prompts + queue system
code('''ZERO_SHOT_PROMPT = """Classify the following IT support ticket into exactly ONE of these categories:
1. Access
2. Administrative rights
3. HR Support
4. Hardware
5. Internal Project
6. Miscellaneous
7. Purchase
8. Storage

Respond with ONLY the category name, nothing else.

Ticket: {text}"""

examples_text = "\\n".join([
    'Ticket: "' + ex["text"][:200] + '"\\nCategory: ' + ex["category"]
    for ex in fewshot_examples
])

FEW_SHOT_PROMPT = """Classify the following IT support ticket into exactly ONE of these categories:
1. Access
2. Administrative rights
3. HR Support
4. Hardware
5. Internal Project
6. Miscellaneous
7. Purchase
8. Storage

Here are examples of each category:

""" + examples_text + """

Now classify this ticket. Respond with ONLY the category name, nothing else.

Ticket: {text}"""

print(f"Prompt zero-shot: {len(ZERO_SHOT_PROMPT)} chars")
print(f"Prompt few-shot: {len(FEW_SHOT_PROMPT)} chars")

def normalize_prediction(pred):
    pred = pred.strip().strip(".").strip()
    for cat in VALID_CATEGORIES:
        if pred.lower() == cat.lower():
            return cat
    for cat in VALID_CATEGORIES:
        if cat.lower() in pred.lower():
            return cat
    return pred

def classify_with_checkpoint(data, prompt_template, round_name, batch_size=BATCH_SIZE, delay=0.05):
    """Classifica em lotes com checkpoint. Retoma se interrompido."""
    checkpoint_path = os.path.join(CHECKPOINT_DIR, f"llm_checkpoint_{round_name}.csv")
    
    # Carregar checkpoint se existir
    if os.path.exists(checkpoint_path):
        done = pd.read_csv(checkpoint_path)
        start_idx = len(done)
        print(f"  Checkpoint encontrado: {start_idx} tickets ja processados. Retomando...")
        all_results = done.to_dict("records")
    else:
        start_idx = 0
        all_results = []
    
    total = len(data)
    if start_idx >= total:
        print(f"  Ja concluido! {total} tickets processados.")
        return pd.DataFrame(all_results)
    
    errors = 0
    start_time = time.time()
    
    for i in range(start_idx, total):
        row = data.iloc[i]
        try:
            response = model.generate_content(prompt_template.format(text=row["Document"]))
            pred = normalize_prediction(response.text)
            all_results.append({"true_label": row["Topic_group"], "predicted": pred})
        except Exception as e:
            all_results.append({"true_label": row["Topic_group"], "predicted": "ERROR"})
            errors += 1
            time.sleep(3)
        
        processed = i - start_idx + 1
        # Checkpoint a cada batch_size
        if processed % batch_size == 0 or i == total - 1:
            pd.DataFrame(all_results).to_csv(checkpoint_path, index=False)
            elapsed = time.time() - start_time
            rate = processed / elapsed * 60 if elapsed > 0 else 0
            remaining = (total - i - 1) / (rate / 60) if rate > 0 else 0
            print(f"  [{round_name}] {i+1}/{total} — {rate:.0f}/min, erros={errors}, "
                  f"restante~{remaining/60:.0f}min [checkpoint salvo]")
        
        time.sleep(delay)
    
    elapsed = time.time() - start_time
    print(f"  [{round_name}] Concluido em {elapsed/60:.1f}min, {errors} erros")
    return pd.DataFrame(all_results)

# Quick test
print("\\nTeste rapido (3 tickets, zero-shot):")
for _, row in sample.head(3).iterrows():
    response = model.generate_content(ZERO_SHOT_PROMPT.format(text=row["Document"]))
    pred = normalize_prediction(response.text)
    correct = "V" if pred == row["Topic_group"] else "X"
    print(f"  Real: {row['Topic_group']:<25} Predito: {pred:<25} {correct}")
    time.sleep(0.5)''')

# Cell 8: MD
md("## Secao 4: Rodada 1 — Zero-Shot (com checkpoint)")

# Cell 9: Zero-shot with queue
code("""print("=" * 60)
print("RODADA 1: CLASSIFICACAO ZERO-SHOT")
print("=" * 60)

zs_results = classify_with_checkpoint(sample, ZERO_SHOT_PROMPT, "zero_shot")
zs_eval = zs_results[zs_results["predicted"] != "ERROR"]
zs_acc = accuracy_score(zs_eval["true_label"], zs_eval["predicted"])
zs_f1 = f1_score(zs_eval["true_label"], zs_eval["predicted"], average="macro", zero_division=0)

print(f"\\nZero-Shot: Acuracia={zs_acc:.1%}, F1 Macro={zs_f1:.3f}")
print(f"Erros API: {len(zs_results) - len(zs_eval)}")
print(classification_report(zs_eval["true_label"], zs_eval["predicted"], zero_division=0))""")

# Cell 10: MD
md("## Secao 5: Rodada 2 — Few-Shot (com checkpoint)")

# Cell 11: Few-shot with queue
code("""print("=" * 60)
print("RODADA 2: CLASSIFICACAO FEW-SHOT")
print("=" * 60)

fs_results = classify_with_checkpoint(sample, FEW_SHOT_PROMPT, "few_shot")
fs_eval = fs_results[fs_results["predicted"] != "ERROR"]
fs_acc = accuracy_score(fs_eval["true_label"], fs_eval["predicted"])
fs_f1 = f1_score(fs_eval["true_label"], fs_eval["predicted"], average="macro", zero_division=0)

print(f"\\nFew-Shot: Acuracia={fs_acc:.1%}, F1 Macro={fs_f1:.3f}")
print(f"Erros API: {len(fs_results) - len(fs_eval)}")
print(classification_report(fs_eval["true_label"], fs_eval["predicted"], zero_division=0))""")

# Cell 12: MD
md("## Secao 6: Comparacao Zero-Shot vs Few-Shot")

# Cell 13: Comparison
code("""print("=" * 60)
print("COMPARACAO")
print("=" * 60)
zs_f1w = f1_score(zs_eval["true_label"], zs_eval["predicted"], average="weighted", zero_division=0)
fs_f1w = f1_score(fs_eval["true_label"], fs_eval["predicted"], average="weighted", zero_division=0)

print(f"{'Metrica':<20} {'Zero-Shot':<15} {'Few-Shot':<15}")
print("-" * 50)
print(f"{'Acuracia':<20} {zs_acc:.1%}{'':10} {fs_acc:.1%}")
print(f"{'F1 Macro':<20} {zs_f1:.3f}{'':10} {fs_f1:.3f}")
print(f"{'F1 Weighted':<20} {zs_f1w:.3f}{'':10} {fs_f1w:.3f}")

fig, axes = plt.subplots(1, 2, figsize=(18, 8))
for ax_idx, (eval_data, title) in enumerate([
    (zs_eval, "Zero-Shot (Acc: " + f"{zs_acc:.1%}" + ")"),
    (fs_eval, "Few-Shot (Acc: " + f"{fs_acc:.1%}" + ")")
]):
    cm = confusion_matrix(eval_data["true_label"], eval_data["predicted"], labels=VALID_CATEGORIES)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=VALID_CATEGORIES, yticklabels=VALID_CATEGORIES, ax=axes[ax_idx])
    axes[ax_idx].set_xlabel("Predito")
    axes[ax_idx].set_ylabel("Real")
    axes[ax_idx].set_title("Matriz de Confusao - " + title)
    axes[ax_idx].tick_params(axis="x", rotation=45)
plt.tight_layout()
plt.savefig("process-log/screenshots/p5_llm_confusion_comparison.png", dpi=150, bbox_inches="tight")
plt.show()

fig, ax = plt.subplots(figsize=(14, 7))
x = np.arange(len(VALID_CATEGORIES))
width = 0.35
zs_cat_acc = []
fs_cat_acc = []
for c in VALID_CATEGORIES:
    zs_sub = zs_eval[zs_eval["true_label"]==c]
    fs_sub = fs_eval[fs_eval["true_label"]==c]
    zs_cat_acc.append((zs_sub["predicted"]==c).mean() if len(zs_sub)>0 else 0)
    fs_cat_acc.append((fs_sub["predicted"]==c).mean() if len(fs_sub)>0 else 0)
ax.bar(x - width/2, zs_cat_acc, width, label="Zero-Shot", color="#3b82f6", alpha=0.8)
ax.bar(x + width/2, fs_cat_acc, width, label="Few-Shot", color="#f97316", alpha=0.8)
ax.set_xticks(x)
ax.set_xticklabels(VALID_CATEGORIES, rotation=45, ha="right")
ax.set_ylabel("Acuracia")
ax.set_title("Acuracia por Categoria: Zero-Shot vs Few-Shot")
ax.legend()
ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("process-log/screenshots/p5_llm_category_comparison.png", dpi=150, bbox_inches="tight")
plt.show()

winner = "Few-Shot" if fs_acc > zs_acc else "Zero-Shot"
print(f"\\nVencedor: {winner} ({max(fs_acc,zs_acc):.1%} vs {min(fs_acc,zs_acc):.1%})")""")

# Cell 14: MD
md("## Secao 7: Analise de Erros")

# Cell 15: Error analysis
code("""best_eval = fs_eval if fs_acc >= zs_acc else zs_eval
best_label = "Few-Shot" if fs_acc >= zs_acc else "Zero-Shot"
wrong = best_eval[best_eval["true_label"] != best_eval["predicted"]]
print(f"Erros ({best_label}): {len(wrong)} ({len(wrong)/len(best_eval)*100:.1f}%)")
if len(wrong) > 0:
    misclass = wrong.groupby(["true_label", "predicted"]).size().reset_index(name="count")
    misclass = misclass.sort_values("count", ascending=False)
    print(f"\\nTop 10 confusoes:")
    print(misclass.head(10).to_string(index=False))
unrecognized = best_eval[~best_eval["predicted"].isin(VALID_CATEGORIES)]
if len(unrecognized) > 0:
    print(f"\\nPrevisoes fora das categorias: {len(unrecognized)}")
    print(unrecognized["predicted"].value_counts().head(10).to_string())
else:
    print("\\nTodas previsoes mapearam para categorias validas.")""")

# Cell 16: MD
md("## Secao 8: Custo e Viabilidade")

# Cell 17: Cost
code("""avg_text_len = sample["Document"].str.len().mean()
avg_input_zs = avg_text_len / 4 + 80
avg_input_fs = avg_text_len / 4 + len(FEW_SHOT_PROMPT) / 4
avg_output = 5
# Gemini 2.5 Flash Lite pricing (~$0.075/1M input, ~$0.30/1M output)
def calc_cost(n, inp, out):
    return n * inp / 1e6 * 0.075 + n * out / 1e6 * 0.30
cost_zs = calc_cost(len(sample), avg_input_zs, avg_output)
cost_fs = calc_cost(len(sample), avg_input_fs, avg_output)
print("=" * 60)
print("CUSTO - Gemini 2.5 Flash Lite")
print("=" * 60)
print(f"Esta rodada: ZS ~US${cost_zs:.4f} + FS ~US${cost_fs:.4f} = ~US${cost_zs+cost_fs:.4f}")
full_zs = cost_zs * len(df) / len(sample)
full_fs = cost_fs * len(df) / len(sample)
print(f"Dataset completo ({len(df)}): ZS ~US${full_zs:.2f} | FS ~US${full_fs:.2f}")""")

# Cell 18: MD
md("## Secao 9: Conclusoes")

# Cell 19: Conclusions
code("""best_results = fs_results if fs_acc >= zs_acc else zs_results
best_results.to_csv("data/llm_classification_results.csv", index=False)
print("Resultados salvos em data/llm_classification_results.csv")

print("\\n" + "=" * 60)
print("CONCLUSOES - CLASSIFICACAO POR LLM")
print("=" * 60)
print(f"\\n1. ACURACIA: ZS={zs_acc:.1%} | FS={fs_acc:.1%} | Vencedor: {winner}")
print(f"2. CUSTO DATASET COMPLETO: ~US${full_fs:.2f}")
best_acc = max(zs_acc, fs_acc)
viab = "VIAVEL para deploy" if best_acc >= 0.7 else "PARCIAL - refinar prompt" if best_acc >= 0.5 else "PRECISA REFINAMENTO"
print(f"3. VIABILIDADE: {viab}")
print(f"4. PROXIMOS PASSOS:")
print("   - Refinar prompt para categorias fracas")
print("   - Classificar dataset completo se aprovado")
print("   - Integrar ao prototipo")
print("=" * 60)

# Limpar checkpoints
for f in ["llm_checkpoint_zero_shot.csv", "llm_checkpoint_few_shot.csv"]:
    p = os.path.join(CHECKPOINT_DIR, f)
    if os.path.exists(p):
        os.remove(p)
        print(f"Checkpoint removido: {f}")""")

nb.cells = cells
nbf.write(nb, "analysis/07_llm_classification.ipynb")
print(f"Notebook criado: {len(cells)} cells")
