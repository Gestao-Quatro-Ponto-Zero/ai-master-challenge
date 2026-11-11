"""PASSO 3d — Limiar de roteamento do transformer (DistilBERT).

Usa as probabilidades do holdout salvas em
solution/artifacts/transformer/test_predictions.npy ({"probs", "y_true", "y_pred"},
softmax do modelo salvo por train_transformer.py; índice das colunas = ordem
alfabética das classes, mesma do LabelEncoder do treino).

Curva precisão × cobertura: para limiar t em 0.50..0.99 (passo 0.01),
  - auto = amostras com max prob >= t
  - precisão = fração de acertos entre as auto-roteadas
  - cobertura = fração auto-roteada
Escolhe o MENOR t com precisão >= 0.95.

Saídas:
  - solution/artifacts/router_threshold.json  (limiar oficial do roteador)
  - solution/artifacts/transformer/precision_coverage.png (o antigo
    precision_coverage.png do passo 1 clássico fica na raiz de artifacts/)

Como rodar: solution/.venv/bin/python solution/scripts/pick_threshold.py
Determinístico (não há aleatoriedade: consome as probs já salvas).
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

SEED = 7
np.random.seed(SEED)

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
TF_ART = ART / "transformer"
TARGET_PRECISION = 0.95
THRESHOLDS = np.round(np.arange(0.50, 0.99 + 1e-9, 0.01), 2)

NAVY = "#001F35"
GOLD = "#B9915B"
BG = "#F5F4F3"

MODEL_NAME = "distilbert-base-uncased"


def register_font():
    font_path = ROOT / "brand" / "PPMuseum-Regular.ttf"
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        name = font_manager.FontProperties(fname=str(font_path)).get_name()
        matplotlib.rcParams["font.family"] = name


def main():
    register_font()
    data = np.load(TF_ART / "test_predictions.npy", allow_pickle=True).item()
    probs = np.asarray(data["probs"])
    y_true = np.asarray(data["y_true"])
    y_pred = np.asarray(data["y_pred"])
    conf = probs.max(axis=1)
    correct = y_pred == y_true

    precisions, coverages = [], []
    for t in THRESHOLDS:
        mask = conf >= t
        n_auto = int(mask.sum())
        cov = n_auto / len(conf)
        prec = float(correct[mask].mean()) if n_auto else 0.0
        precisions.append(prec)
        coverages.append(cov)
    precisions = np.array(precisions)
    coverages = np.array(coverages)

    eligible = np.flatnonzero(precisions >= TARGET_PRECISION)
    if eligible.size:
        i = int(eligible[0])  # MENOR limiar com precisão >= 0.95
        note = None
    else:
        i = int(np.argmax(precisions))
        note = f"precisão {TARGET_PRECISION:.2f} não atingida; melhor precisão alcançada reportada"
    out = {
        "threshold": float(THRESHOLDS[i]),
        "auto_precision": round(float(precisions[i]), 4),
        "coverage": round(float(coverages[i]), 4),
        "model": MODEL_NAME,
        "proba_source": "test_predictions.npy (softmax do holdout)",
    }
    if note:
        out["note"] = note
    (ART / "router_threshold.json").write_text(json.dumps(out, indent=2))

    fig, ax = plt.subplots(figsize=(8, 5.5), facecolor=BG)
    ax.set_facecolor(BG)
    ax.plot(coverages * 100, precisions, color=NAVY, lw=2, label="Precisão da fila automática")
    ax.axhline(TARGET_PRECISION, color=GOLD, ls="--", lw=1.5,
               label=f"Alvo: precisão ≥ {TARGET_PRECISION:.2f}")
    ax.scatter([coverages[i] * 100], [precisions[i]], color=GOLD, s=90, zorder=5,
               edgecolors=NAVY, label=f"Escolhido: t={THRESHOLDS[i]:.2f}")
    ax.annotate(
        f"t={THRESHOLDS[i]:.2f}\ncobertura={coverages[i]*100:.1f}%\nprecisão={precisions[i]:.3f}",
        xy=(coverages[i] * 100, precisions[i]),
        xytext=(coverages[i] * 100 - 22, TARGET_PRECISION + 0.025),
        color=NAVY, fontsize=9,
        arrowprops=dict(arrowstyle="->", color=GOLD, lw=1.2),
    )
    ax.set_xlabel("Cobertura — % de tickets auto-roteados", color=NAVY)
    ax.set_ylabel("Precisão do roteamento automático", color=NAVY)
    ax.set_title("Precisão × cobertura — DistilBERT (limiar = max prob)",
                 color=NAVY, fontsize=12)
    ax.set_xlim(0, 100)
    ax.tick_params(colors=NAVY)
    for spine in ax.spines.values():
        spine.set_color(NAVY)
    ax.legend(facecolor=BG, edgecolor=NAVY, fontsize=9)
    fig.tight_layout()
    fig.savefig(TF_ART / "precision_coverage.png", dpi=150, facecolor=BG)
    plt.close(fig)

    print(json.dumps(out, indent=2))
    print(f"curva salva em {TF_ART / 'precision_coverage.png'}")


if __name__ == "__main__":
    main()
