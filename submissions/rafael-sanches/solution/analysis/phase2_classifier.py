"""
FASE 2a — Classificador de tickets (Dataset 2, texto real).
Treina TF-IDF + Regressao Logistica, avalia com metrica HONESTA (por classe),
mede o gate de confianca (auto-rotear vs humano) e salva o modelo pra Streamlit.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score
import joblib

D2 = r"D:\Projetos\Case G4\data\challenge-002-support\all_tickets_processed_improved_v3.csv"
FIG = r"D:\Projetos\Case G4\solution-draft\figures"
MODEL = r"D:\Projetos\Case G4\solution-draft\model\ticket_classifier.joblib"

df = pd.read_csv(D2).dropna(subset=["Document", "Topic_group"])
df = df[df["Document"].astype(str).str.strip() != ""]
X, y = df["Document"].astype(str), df["Topic_group"]
print(f"Dados: {len(df)} tickets | {y.nunique()} categorias")

# Split estratificado (preserva a proporcao das classes no teste)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
print(f"Treino: {len(Xtr)} | Teste: {len(Xte)}")

pipe = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=5, sublinear_tf=True)),
    ("clf", LogisticRegression(max_iter=1000, C=3.0)),
])
print("\nTreinando...")
pipe.fit(Xtr, ytr)

pred = pipe.predict(Xte)
proba = pipe.predict_proba(Xte)
classes = pipe.classes_

print("\n" + "=" * 78)
print("RELATORIO POR CLASSE (dados de teste — nunca vistos no treino)")
print("=" * 78)
print(classification_report(yte, pred, digits=3))
print(f"Acuracia global : {accuracy_score(yte, pred):.3f}")
print(f"F1 macro (media simples entre classes, penaliza falha nas pequenas): {f1_score(yte, pred, average='macro'):.3f}")
print(f"F1 ponderado    : {f1_score(yte, pred, average='weighted'):.3f}")

# --- Matriz de confusao (normalizada por linha = recall) -------------------
cm = confusion_matrix(yte, pred, labels=classes, normalize="true")
fig, ax = plt.subplots(figsize=(8.2, 6.8))
im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=1)
ax.set_xticks(range(len(classes))); ax.set_yticks(range(len(classes)))
ax.set_xticklabels(classes, rotation=40, ha="right", fontsize=8)
ax.set_yticklabels(classes, fontsize=8)
for i in range(len(classes)):
    for j in range(len(classes)):
        v = cm[i, j]
        if v >= 0.01:
            ax.text(j, i, f"{v*100:.0f}", ha="center", va="center",
                    color="white" if v > 0.5 else "#333", fontsize=8)
ax.set_xlabel("Categoria prevista"); ax.set_ylabel("Categoria real")
ax.set_title("Matriz de confusao (% por categoria real)\ndiagonal = acertos", fontweight="bold", fontsize=11)
fig.colorbar(im, fraction=0.046, pad=0.04)
fig.tight_layout(); fig.savefig(f"{FIG}\\05_matriz_confusao.png", bbox_inches="tight"); plt.close(fig)
print("\n[salvo] 05_matriz_confusao.png")

# --- Gate de confianca: precisao vs cobertura ------------------------------
conf = proba.max(axis=1)
correct = (pred == yte.values)
taus = np.linspace(0, 0.99, 100)
cov, prec = [], []
for t in taus:
    m = conf >= t
    cov.append(m.mean())
    prec.append(correct[m].mean() if m.sum() else np.nan)
cov, prec = np.array(cov), np.array(prec)

# Ponto de operacao: maior cobertura com precisao >= 95%
ok = np.where(prec >= 0.95)[0]
if len(ok):
    i = ok[np.argmax(cov[ok])]
    t95, cov95, prec95 = taus[i], cov[i], prec[i]
    print(f"\nPonto de operacao (precisao >= 95%): limiar={t95:.2f} -> "
          f"auto-roteia {cov95*100:.0f}% dos tickets a {prec95*100:.1f}% de precisao; "
          f"os {100-cov95*100:.0f}% restantes vao pra humano.")
else:
    t95 = cov95 = prec95 = None
    print("\nNenhum limiar atinge 95% de precisao.")

fig, ax = plt.subplots(figsize=(7.6, 4.4))
ax.plot(cov * 100, prec * 100, color="#4C72B0", lw=2)
ax.axhline(95, color="#C44E52", ls="--", lw=1, label="Meta de precisao 95%")
if t95 is not None:
    ax.scatter([cov95 * 100], [prec95 * 100], color="#C44E52", zorder=5, s=60)
    ax.annotate(f"limiar {t95:.2f}\n{cov95*100:.0f}% automatizado @ {prec95*100:.0f}%",
                (cov95 * 100, prec95 * 100), textcoords="offset points", xytext=(-10, -45),
                fontsize=9, ha="center", color="#C44E52")
ax.set_xlabel("Cobertura — % de tickets auto-roteados")
ax.set_ylabel("Precisao dos auto-roteados (%)")
ax.set_title("Quanto mais alto o limiar de confianca, mais preciso — porem menos cobre",
             fontweight="bold", fontsize=11, loc="left")
ax.grid(True, color="#e6e6e6"); ax.legend(fontsize=9)
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(f"{FIG}\\06_gate_confianca.png", bbox_inches="tight"); plt.close(fig)
print("[salvo] 06_gate_confianca.png")

# --- Explicabilidade: top termos por classe --------------------------------
feats = np.array(pipe.named_steps["tfidf"].get_feature_names_out())
coefs = pipe.named_steps["clf"].coef_
print("\n" + "=" * 78)
print("TOP 8 TERMOS QUE DEFINEM CADA CATEGORIA (explicabilidade)")
print("=" * 78)
for ci, cls in enumerate(classes):
    top = feats[np.argsort(coefs[ci])[-8:][::-1]]
    print(f"{cls:22s}: {', '.join(top)}")

joblib.dump(pipe, MODEL)
print(f"\n[salvo] modelo -> {MODEL}")
