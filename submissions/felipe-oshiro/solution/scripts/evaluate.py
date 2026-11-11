"""PASSO 1b — Avaliação do melhor modelo clássico (artifacts/model_best.joblib).

Gera em solution/artifacts/:
  i)  confusion_matrix.png — matriz 8x8 (paleta: navy #001F35 / dourado #B9915B /
      fundo #F5F4F3; fonte PPMuseum registrada via font_manager).
  ii) per_class_metrics.csv — precision/recall/f1/support por classe.
  iii) precision_coverage.png — precisão do roteamento automático vs cobertura
      ao varrer o limiar de confiança.
  iv) router_threshold.json — menor/melhor limiar com precisão >= 0.95 e
      máxima cobertura.

Escolha do caminho de probabilidade: o melhor modelo do passo 1 foi
TF-IDF word 1-2g + LogisticRegression, que expõe `predict_proba` nativamente.
Portanto usamos max(predict_proba) diretamente como score de confiança —
sem CalibratedClassifierCV (desnecessário aqui). Se o joblib salvo for um
LinearSVC, o script faz fallback: fit de CalibratedClassifierCV(sigmoid) no
próprio split de treino para normalizar o decision_function.

Split: holdout estratificado 80/20, seed 7 (o mesmo protocolo do passo 1).
"""

import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import train_test_split

SEED = 7
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasources" / "all_tickets_processed_improved_v3.csv"
ART = ROOT / "artifacts"
TARGET_PRECISION = 0.95

NAVY = "#001F35"
GOLD = "#B9915B"
BG = "#F5F4F3"


def register_font():
    font_path = ROOT / "brand" / "PPMuseum-Regular.ttf"
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        name = font_manager.FontProperties(fname=str(font_path)).get_name()
        matplotlib.rcParams["font.family"] = name


def get_proba(model, X_train, y_train, X_test):
    """max-proba nativa de LogReg/Voting; fallback CalibratedClassifierCV p/ LinearSVC."""
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X_test)
        return proba.max(axis=1), proba.argmax(axis=1), "predict_proba"
    cal = CalibratedClassifierCV(model, method="sigmoid", cv="prefit")
    cal.fit(X_train, y_train)
    proba = cal.predict_proba(X_test)
    return proba.max(axis=1), proba.argmax(axis=1), "CalibratedClassifierCV(sigmoid) sobre decision_function"


def main():
    register_font()
    model = joblib.load(ART / "model_best.joblib")

    df = pd.read_csv(DATA)
    X_train, X_test, y_train, y_test = train_test_split(
        df["Document"], df["Topic_group"], test_size=0.20, random_state=SEED, stratify=df["Topic_group"]
    )
    labels = sorted(df["Topic_group"].unique())
    y_pred = model.predict(X_test)

    # (i) Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(9, 7.5), facecolor=BG)
    ax.set_facecolor(BG)
    im = ax.imshow(cm, cmap=matplotlib.colors.LinearSegmentedColormap.from_list(
        "g4", [BG, GOLD, NAVY]))
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    thresh = cm.max() / 2
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=9,
                    color="white" if cm[i, j] > thresh else NAVY)
    ax.set_xlabel("Predito")
    ax.set_ylabel("Real")
    ax.set_title("Matriz de confusão — TF-IDF word 1-2g + LogReg (holdout 80/20, seed 7)")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(ART / "confusion_matrix.png", dpi=150, facecolor=BG)
    plt.close(fig)

    # (ii) Per-class metrics
    report = classification_report(y_test, y_pred, labels=labels, output_dict=True)
    per_class = pd.DataFrame(report).T.loc[labels]
    per_class[["precision", "recall", "f1-score"]] = per_class[["precision", "recall", "f1-score"]].astype(float)
    per_class["support"] = per_class["support"].astype(int)
    per_class.index.name = "class"
    per_class.to_csv(ART / "per_class_metrics.csv")

    # (iii) Precision vs coverage
    conf, pred_idx, proba_path = get_proba(model, X_train, y_train, X_test)
    correct = pred_idx == pd.Categorical(y_test, categories=labels).codes
    thresholds = np.linspace(0.30, 0.999, 1401)
    precisions, coverages = [], []
    for t in thresholds:
        mask = conf >= t
        cov = mask.mean()
        covages = correct[mask].mean() if correct[mask].size else 0.0
        precisions.append(covages)
        coverages.append(cov)
    precisions = np.array(precisions)
    coverages = np.array(coverages)

    fig, ax = plt.subplots(figsize=(8, 5.5), facecolor=BG)
    ax.set_facecolor(BG)
    ax.plot(coverages * 100, precisions, color=NAVY, lw=2, label="Precisão da fila automática")
    ax.axhline(TARGET_PRECISION, color=GOLD, ls="--", lw=1.5, label=f"Alvo: precisão ≥ {TARGET_PRECISION:.2f}")
    ax.axvline(coverages[np.argmax(precisions >= TARGET_PRECISION)] * 100, color=GOLD, ls=":", lw=1.5)
    ax.set_xlabel("Cobertura — % de tickets auto-roteados")
    ax.set_ylabel("Precisão do roteamento automático")
    ax.set_title("Precisão × cobertura (limiar = max probabilidade)")
    ax.set_xlim(0, 100)
    ax.legend(facecolor=BG)
    fig.tight_layout()
    fig.savefig(ART / "precision_coverage.png", dpi=150, facecolor=BG)
    plt.close(fig)

    # (iv) Threshold com precisão >= 0.95 e máxima cobertura
    eligible = np.flatnonzero(precisions >= TARGET_PRECISION)
    if eligible.size:
        i = eligible[np.argmax(coverages[eligible])]
        out = {
            "threshold": round(float(thresholds[i]), 4),
            "auto_precision": round(float(precisions[i]), 4),
            "coverage": round(float(coverages[i]), 4),
            "model": "tfidf_word12_logreg",
            "proba_source": proba_path,
        }
    else:
        # nenhuma faixa atinge 0.95: reporta o limiar mais confiável (maior precisão alcançada)
        i = int(np.argmax(precisions))
        out = {
            "threshold": round(float(thresholds[i]), 4),
            "auto_precision": round(float(precisions[i]), 4),
            "coverage": round(float(coverages[i]), 4),
            "model": "tfidf_word12_logreg",
            "proba_source": proba_path,
            "note": f"precisão {TARGET_PRECISION:.2f} não atingida; melhor precisão alcançada reportada",
        }
    (ART / "router_threshold.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    print(f"\naccuracy={report['accuracy']:.4f} macro_f1={report['macro avg']['f1-score']:.4f}")


if __name__ == "__main__":
    main()
