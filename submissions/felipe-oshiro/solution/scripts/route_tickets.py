"""PASSO 3d — CLI de roteamento com o transformer (DistilBERT).

Carrega o modelo HF de solution/artifacts/transformer/ e o limiar de
solution/artifacts/router_threshold.json (gerado por pick_threshold.py).

Regras de roteamento (nesta ordem):
  1. tópico previsto == "Administrative rights" → HUMANO, reason="sensitive_class"
  2. confiança (max softmax) < limiar            → HUMANO, reason="low_confidence"
  3. caso contrário                              → AUTO,   reason="ok"

Como rodar (solution/.venv/bin/python):
  # Texto único:
  solution/.venv/bin/python solution/scripts/route_tickets.py --text "my laptop will not turn on"
  # Lote (coluna 'Ticket Description' do CSV; salva artifacts/routed_tickets.csv):
  solution/.venv/bin/python solution/scripts/route_tickets.py --batch solution/datasources/customer_support_tickets.csv

Modo --text imprime UMA linha:  tópico | confiança | AUTO→equipe(topic) | HUMANO→triagem(reason)
Modo --batch mostra progresso a cada 10 batches, salva o CSV com as colunas
originais + predicted_topic + confidence + decision + reason e imprime no final
um resumo de impacto em JSON (% AUTO, % HUMANO, decisões por tópico previsto,
top-5 motivos de triagem humana = pares (reason, tópico previsto)).

Sem dependências novas (torch/transformers/pandas já no venv). Batch usa
batch_size=64 no MPS; seed 7 fixada onde há estocasticidade.
"""

import argparse
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

SEED = 7
np.random.seed(SEED)
torch.manual_seed(SEED)

ROOT = Path(__file__).resolve().parents[1]
TF_ART = ROOT / "artifacts" / "transformer"
THRESHOLD_JSON = ROOT / "artifacts" / "router_threshold.json"
BATCH_SIZE = 64
MAX_LENGTH = 192  # mesmo max_length do treino (step2_results.json)
SENSITIVE_CLASS = "Administrative rights"


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def load_model():
    tok = AutoTokenizer.from_pretrained(TF_ART)
    model = AutoModelForSequenceClassification.from_pretrained(TF_ART)
    model.to(get_device()).eval()
    classes = json.loads((TF_ART / "step2_results.json").read_text())["classes"]
    assert len(classes) == model.config.num_labels, "classes != num_labels do modelo"
    return tok, model, classes


@torch.no_grad()
def predict_probs(texts, tok, model, device):
    enc = tok(list(texts), truncation=True, max_length=MAX_LENGTH, padding=True,
              return_tensors="pt")
    enc = {k: v.to(device) for k, v in enc.items()}
    logits = model(**enc).logits
    return torch.softmax(logits, -1).cpu().numpy()


def decide(topic, conf, threshold):
    if topic == SENSITIVE_CLASS:
        return "HUMANO", "sensitive_class"
    if conf < threshold:
        return "HUMANO", "low_confidence"
    return "AUTO", "ok"


def run_single(args, tok, model, classes, threshold, device):
    probs = predict_probs([args.text], tok, model, device)[0]
    idx = int(probs.argmax())
    topic, conf = classes[idx], float(probs[idx])
    decision, reason = decide(topic, conf, threshold)
    if decision == "AUTO":
        tail = f"AUTO→equipe({topic})"
    else:
        tail = f"HUMANO→triagem({reason})"
    print(f"{topic} | {conf:.4f} | {tail}")


def run_batch(args, tok, model, classes, threshold, device):
    df = pd.read_csv(args.batch)
    texts = df["Ticket Description"].fillna("").astype(str).tolist()
    preds = np.empty(len(texts), dtype=object)
    confs = np.empty(len(texts), dtype=float)
    t0 = time.time()
    for start in range(0, len(texts), BATCH_SIZE):
        probs = predict_probs(texts[start:start + BATCH_SIZE], tok, model, device)
        idx = probs.argmax(axis=1)
        preds[start:start + len(idx)] = [classes[i] for i in idx]
        confs[start:start + len(idx)] = probs[np.arange(len(idx)), idx]
        done = min(start + BATCH_SIZE, len(texts))
        if (start // BATCH_SIZE) % 10 == 0:
            print(f"[roteamento] {done}/{len(texts)} textos ({time.time()-t0:.0f}s)",
                  flush=True)
    decisions, reasons = zip(*[decide(t, c, threshold) for t, c in zip(preds, confs)])
    df["predicted_topic"] = preds
    df["confidence"] = np.round(confs, 4)
    df["decision"] = decisions
    df["reason"] = reasons
    out = ROOT / "artifacts" / "routed_tickets.csv"
    df.to_csv(out, index=False)

    n = len(df)
    n_auto = int((df["decision"] == "AUTO").sum())
    n_human = n - n_auto
    per_topic = (df.groupby(["predicted_topic", "decision"]).size()
                 .unstack(fill_value=0).astype(int)
                 .to_dict(orient="index"))
    triage_pairs = Counter(zip(df.loc[df["decision"] == "HUMANO", "reason"],
                               df.loc[df["decision"] == "HUMANO", "predicted_topic"]))
    top5 = [{"reason": r, "predicted_topic": t, "count": int(c)}
            for (r, t), c in triage_pairs.most_common(5)]
    summary = {
        "n_tickets": n,
        "threshold": threshold,
        "auto_pct": round(n_auto / n * 100, 2),
        "humano_pct": round(n_human / n * 100, 2),
        "decisions_per_predicted_topic": per_topic,
        "top5_triage_reasons": top5,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"[roteamento] CSV salvo em {out}")


def main():
    ap = argparse.ArgumentParser(description="Roteamento AUTO/HUMANO com DistilBERT")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help='texto único, ex: --text "laptop not turning on"')
    g.add_argument("--batch", help="CSV com a coluna 'Ticket Description'")
    args = ap.parse_args()

    threshold = json.loads(THRESHOLD_JSON.read_text())["threshold"]
    tok, model, classes = load_model()
    device = get_device()
    print(f"[roteamento] modelo={TF_ART.name} device={device} threshold={threshold}",
          flush=True)
    if args.text:
        run_single(args, tok, model, classes, threshold, device)
    else:
        run_batch(args, tok, model, classes, threshold, device)


if __name__ == "__main__":
    main()
