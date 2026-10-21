import argparse
import pickle
import sys
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

P = Path(__file__).parent
CSV = P / "data/all_tickets_processed_improved_v3.csv"
PKL = P / "modelo.pkl"

CONFIANCA_MIN = 0.70
SENSIVEIS = {"HR Support", "Administrative rights"}
TIPOS_SENIOR = {"Refund request", "Cancellation request"}


def fila(cat: str, conf: float, tipo: str | None, prioridade: str | None) -> str:
    if tipo in TIPOS_SENIOR:
        return "AGENTE_SENIOR"
    if cat in SENSIVEIS:
        return "HUMANA"
    if conf < CONFIANCA_MIN:
        return "HUMANA"
    if prioridade == "High":
        return "PRIORITARIA"
    return "L1"


def treinar() -> None:
    df = pd.read_csv(CSV).dropna(subset=["Document", "Topic_group"])
    xtr, xte, ytr, yte = train_test_split(
        df["Document"], df["Topic_group"], test_size=0.2, random_state=42, stratify=df["Topic_group"]
    )
    pipe = Pipeline(
        [("v", TfidfVectorizer(max_features=10000, min_df=3)), ("c", LogisticRegression(max_iter=400))]
    )
    pipe.fit(xtr, ytr)
    pred = pipe.predict(xte)
    proba = pipe.predict_proba(xte)
    confs = proba.max(axis=1)
    filas = [fila(c, float(conf), None, None) for c, conf in zip(pred, confs)]
    auto = [f in ("L1", "PRIORITARIA") for f in filas]
    n_te = len(yte)
    n_auto = sum(auto)
    acc_auto = sum(p == y for p, y, a in zip(pred, yte, auto) if a) / n_auto if n_auto else 0.0
    with PKL.open("wb") as f:
        pickle.dump(pipe, f)
    print(f"acuracia global (hold-out 20%): {pipe.score(xte, yte):.1%}")
    print(
        f"politica roteamento (DS2, sem metadados DS1): "
        f"{n_auto/n_te:.1%} auto (L1) | {1 - n_auto/n_te:.1%} humana | "
        f"acuracia categoria no auto: {acc_auto:.1%}"
    )
    print(classification_report(yte, pred))


def rotear(texto: str, tipo: str | None, prioridade: str | None) -> None:
    if not PKL.exists():
        sys.exit("Rode: python prototipo.py treinar")

    if tipo in TIPOS_SENIOR:
        print("categoria: (regra Dataset 1)")
        print("confianca: n/a")
        print("fila: AGENTE_SENIOR")
        print("motivo: tipo_refund_ou_cancelamento")
        return

    with PKL.open("rb") as f:
        pipe = pickle.load(f)
    cat = pipe.predict([texto])[0]
    conf = float(pipe.predict_proba([texto]).max())
    print(f"categoria: {cat}")
    print(f"confianca: {conf:.1%}")
    dest = fila(cat, conf, tipo, prioridade)
    print(f"fila: {dest}")
    if dest == "HUMANA":
        print("motivo: categoria_sensivel" if cat in SENSIVEIS else "motivo: confianca_baixa")
    elif dest == "PRIORITARIA":
        print("motivo: prioridade_alta")
    else:
        print("motivo: roteamento_padrao")


def main() -> None:
    parser = argparse.ArgumentParser(description="Protótipo: treinar classificador ou rotear ticket.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("treinar")
    p_rot = sub.add_parser("rotear")
    p_rot.add_argument("texto")
    p_rot.add_argument("--tipo", default=None)
    p_rot.add_argument("--prioridade", default=None)

    args = parser.parse_args()
    if args.cmd == "treinar":
        treinar()
    else:
        rotear(args.texto, args.tipo, args.prioridade)


if __name__ == "__main__":
    main()
