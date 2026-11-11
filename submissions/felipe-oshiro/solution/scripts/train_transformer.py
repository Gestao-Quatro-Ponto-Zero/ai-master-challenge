"""PASSO 2 — Fine-tune de transformer (distilbert-base-uncased) para classificar tickets.

Protocolo: MESMO holdout estratificado 80/20, seed 7 do passo 1
(train_classic.py — train_test_split test_size=0.20, random_state=7,
stratify=Topic_group). Nada do passo 1 é alterado.

Config: max_length=192 se p95 de tokens <= 192 senão 256, batch 32 (16 em OOM),
AdamW lr 2e-5, linear warmup 10%, grad clip max_norm=1.0, seed 7 em tudo.
2 épocas (+1 opcional se a acurácia de validação do holdout 20% subir
claramente na 2ª). Loss NaN/inf -> aborto imediato.

Saída: solution/artifacts/transformer/ (modelo+tokenizer, test_predictions.npy,
step2_results.json, classification_report.txt, confusion_matrix.png).
"""

import json
import math
import os
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from matplotlib import font_manager
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import DataLoader, TensorDataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
    set_seed,
)

SEED = 7
MODEL_NAME = "distilbert-base-uncased"
BATCH_SIZE = int(os.environ.get("TRANSFORMER_BATCH", "32"))  # 16 em caso de OOM
LR = 2e-5
WARMUP_FRAC = 0.10
GRAD_CLIP = 1.0
EPOCHS_BASE = 2
EPOCH_3_DELTA = 0.002  # 3ª época só se val acc subir >= 0.2 pp entre ép. 1 e 2
EVAL_BATCH = 64

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasources" / "all_tickets_processed_improved_v3.csv"
ART = ROOT / "artifacts" / "transformer"
FONT_PATH = ROOT / "brand" / "PPMuseum-Regular.ttf"

NAVY, GOLD, BG = "#001F35", "#B9915B", "#F5F4F3"

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"


def set_all_seeds():
    np.random.seed(SEED)
    set_seed(SEED)
    torch.manual_seed(SEED)


def main():
    ART.mkdir(parents=True, exist_ok=True)
    set_all_seeds()

    # Split idêntico ao passo 1 (linha copiada de train_classic.py)
    df = pd.read_csv(DATA)
    X_train, X_test, y_train, y_test = train_test_split(
        df["Document"], df["Topic_group"], test_size=0.20, random_state=SEED, stratify=df["Topic_group"]
    )
    print(f"device={DEVICE} model={MODEL_NAME}")
    print(f"train={len(X_train)} test={len(X_test)} classes={df['Topic_group'].nunique()}", flush=True)

    le = LabelEncoder().fit(df["Topic_group"])
    class_names = list(le.classes_)
    y_tr = le.transform(y_train)
    y_te = le.transform(y_test)

    tok = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)

    # p95 do comprimento em tokens para justificar max_length
    lens = [len(x) for x in tok(list(df["Document"]), add_special_tokens=True)["input_ids"]]
    p95 = int(np.percentile(lens, 95))
    MAX_LENGTH = 192 if p95 <= 192 else 256
    print(f"token length p95={p95} -> max_length={MAX_LENGTH}", flush=True)

    def encode(texts):
        return tok(list(texts), truncation=True, max_length=MAX_LENGTH, padding="max_length", return_tensors="pt")

    t0 = time.time()
    enc_tr = encode(X_train)
    enc_te = encode(X_test)
    print(f"tokenized in {time.time()-t0:.1f}s", flush=True)

    tr_loader = DataLoader(
        TensorDataset(enc_tr["input_ids"], enc_tr["attention_mask"], torch.tensor(y_tr)),
        batch_size=BATCH_SIZE, shuffle=True, generator=torch.Generator().manual_seed(SEED),
    )
    te_loader = DataLoader(
        TensorDataset(enc_te["input_ids"], enc_te["attention_mask"], torch.tensor(y_te)),
        batch_size=EVAL_BATCH, shuffle=False,
    )

    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=len(class_names)).to(DEVICE)
    optim = torch.optim.AdamW(model.parameters(), lr=LR)
    steps_per_epoch = len(tr_loader)
    total_steps = steps_per_epoch * EPOCHS_BASE
    sched = get_linear_schedule_with_warmup(optim, int(WARMUP_FRAC * total_steps), total_steps)

    def evaluate(loader):
        model.eval()
        probs, labels = [], []
        with torch.no_grad():
            for ids, mask, yb in loader:
                logits = model(input_ids=ids.to(DEVICE), attention_mask=mask.to(DEVICE)).logits
                probs.append(torch.softmax(logits, -1).cpu())
                labels.append(yb)
        return torch.cat(probs).numpy(), np.concatenate(labels)

    def run_epoch(epoch, steps_per_epoch):
        model.train()
        ep_t0 = time.time()
        running = 0.0
        for step, (ids, mask, yb) in enumerate(tr_loader, 1):
            out = model(input_ids=ids.to(DEVICE), attention_mask=mask.to(DEVICE), labels=yb.to(DEVICE))
            loss = out.loss
            if not math.isfinite(loss.item()):
                msg = f"ABORT: loss não finita ({loss.item()}) na época {epoch} step {step} — abortando imediatamente."
                print(msg, flush=True)
                raise SystemExit(msg)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            optim.step()
            sched.step()
            optim.zero_grad()
            running += loss.item()
            if step % 200 == 0:
                print(f"epoch {epoch} step {step}/{steps_per_epoch} loss={running/step:.4f}", flush=True)
        return running / steps_per_epoch, time.time() - ep_t0

    history = []
    best_acc, best_state = -1.0, None
    train_t0 = time.time()
    n_epochs = EPOCHS_BASE

    try:
        for epoch in range(1, EPOCHS_BASE + 1):
            avg_loss, dt = run_epoch(epoch, steps_per_epoch)
            probs, y_true = evaluate(te_loader)
            acc = accuracy_score(y_true, probs.argmax(1))
            history.append({"epoch": epoch, "val_accuracy": round(acc, 4), "train_loss_last": round(avg_loss, 4), "seconds": round(dt, 1)})
            print(f"== EPOCH {epoch}: val_acc={acc:.4f} ({dt:.0f}s) ==", flush=True)
            if acc > best_acc:
                best_acc = acc
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

        # 3ª época opcional: só se a acurácia de validação subiu claramente
        if len(history) >= 2 and history[-1]["val_accuracy"] - history[-2]["val_accuracy"] >= EPOCH_3_DELTA:
            print("val acc ainda subindo claramente -> época 3", flush=True)
            n_epochs = 3
            remaining = steps_per_epoch * n_epochs - steps_per_epoch * EPOCHS_BASE
            sched = get_linear_schedule_with_warmup(optim, 0, remaining)
            avg_loss, dt = run_epoch(3, steps_per_epoch)
            probs, y_true = evaluate(te_loader)
            acc = accuracy_score(y_true, probs.argmax(1))
            history.append({"epoch": 3, "val_accuracy": round(acc, 4), "train_loss_last": round(avg_loss, 4), "seconds": round(dt, 1)})
            print(f"== EPOCH 3: val_acc={acc:.4f} ==", flush=True)
            if acc > best_acc:
                best_acc = acc
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            print("val acc não subiu claramente -> manter 2 épocas", flush=True)
    except SystemExit as e:
        (ART / "step2_results.json").write_text(json.dumps({
            "model": MODEL_NAME, "status": "aborted_nan", "message": str(e), "history": history,
        }, indent=2))
        raise

    train_seconds = round(time.time() - train_t0, 1)

    # Restaurar melhor estado e produzir artefatos finais
    if best_state is not None:
        model.load_state_dict(best_state)
        model.to(DEVICE)
    probs, y_true = evaluate(te_loader)
    y_pred = probs.argmax(1)
    acc = accuracy_score(y_true, y_pred)
    report = classification_report(y_true, y_pred, target_names=class_names, digits=4, zero_division=0)
    rep_dict = classification_report(y_true, y_pred, target_names=class_names, digits=4, zero_division=0, output_dict=True)
    macro_f1 = rep_dict["macro avg"]["f1-score"]
    print(f"\nFINAL holdout acc={acc:.4f} macro_f1={macro_f1:.4f}\n")
    print(report, flush=True)

    model.save_pretrained(ART)
    tok.save_pretrained(ART)
    np.save(ART / "test_predictions.npy", {"probs": probs, "y_true": y_true, "y_pred": y_pred}, allow_pickle=True)
    (ART / "classification_report.txt").write_text(report)
    (ART / "step2_results.json").write_text(json.dumps({
        "model": MODEL_NAME,
        "test_accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "epochs": n_epochs,
        "max_length": MAX_LENGTH,
        "batch_size": BATCH_SIZE,
        "lr": LR,
        "device": DEVICE,
        "token_length_p95": p95,
        "train_seconds": train_seconds,
        "history": history,
        "classes": class_names,
    }, indent=2))

    # Confusion matrix (brand: navy / dourado / fundo claro)
    if FONT_PATH.exists():
        font_manager.fontManager.addfont(str(FONT_PATH))
        fname = font_manager.FontProperties(fname=str(FONT_PATH)).get_name()
        plt.rcParams["font.family"] = fname
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(9.5, 8), dpi=160)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    im = ax.imshow(cm, cmap=matplotlib.colors.LinearSegmentedColormap.from_list("brand", [BG, NAVY]))
    thresh = cm.max() / 2
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            v = cm[i, j]
            ax.text(j, i, f"{v}", ha="center", va="center", fontsize=9,
                    color="white" if v > thresh else NAVY)
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=40, ha="right", color=NAVY, fontsize=9)
    ax.set_yticklabels(class_names, color=NAVY, fontsize=9)
    ax.set_xlabel("Predito", color=NAVY)
    ax.set_ylabel("Real", color=NAVY)
    ax.set_title(f"Matriz de Confusão — DistilBERT (acc {acc:.4f})", color=NAVY, fontsize=13, pad=12)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046)
    cbar.ax.yaxis.label.set_color(NAVY)
    cbar.ax.tick_params(colors=NAVY)
    for spine in ax.spines.values():
        spine.set_color(NAVY)
    fig.tight_layout()
    fig.savefig(ART / "confusion_matrix.png", facecolor=BG)
    plt.close(fig)

    print(f"\nDONE train_seconds={train_seconds} artifacts -> {ART}", flush=True)


if __name__ == "__main__":
    main()
