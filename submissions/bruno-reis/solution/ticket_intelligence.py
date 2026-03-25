#!/usr/bin/env python3
"""Ticket intelligence pipeline for Challenge 002.

Uses Dataset 2 (all_tickets_processed_improved_v3.csv) to train a text
classifier and similarity search, then links findings to Dataset 1
operational pain points for an automation proposal.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics.pairwise import cosine_similarity


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
)
DATASET2_PATH = os.path.join(PROJECT_ROOT, "data", "all_tickets_processed_improved_v3.csv")
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


@dataclass
class Dataset2Summary:
    shape: Tuple[int, int]
    columns: List[str]
    class_counts: pd.Series
    text_length_stats: pd.Series
    duplicate_ratio: float


def load_dataset2(path: str = DATASET2_PATH) -> pd.DataFrame:
    if not os.path.isfile(path):
        print(f"Dataset não encontrado em: {path}")
        print("Verifique se a pasta 'data/' está na raiz do projeto.")
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    df = df.rename(columns={"Document": "text", "Topic_group": "label"})
    return df


def clean_text_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["text"] = df["text"].astype(str).str.lower().str.replace("\s+", " ", regex=True).str.strip()
    df = df.drop_duplicates(subset=["text", "label"]).reset_index(drop=True)
    return df


def _draw_bar_chart(series: pd.Series, path: Path, title: str):
    """Renderiza um bar chart simples com PIL para evitar dependência pesada de Matplotlib."""
    series = series.sort_values(ascending=False)
    width, height = 900, 520
    margin = 60
    bar_space = 12
    bar_height = int((height - 2 * margin - bar_space * (len(series) - 1)) / len(series))
    max_val = series.max()

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    # título
    draw.text((margin, 20), title, fill="black", font=font)

    for i, (label, val) in enumerate(series.items()):
        y = margin + i * (bar_height + bar_space)
        bar_len = int((width - 2 * margin) * (val / max_val))
        draw.rectangle([margin, y, margin + bar_len, y + bar_height], fill="#4C78A8")
        draw.text((margin + bar_len + 8, y), f"{val}", fill="black", font=font)
        draw.text((10, y), label, fill="black", font=font)

    img.save(path)


def _draw_confusion_heatmap(matrix: np.ndarray, labels: List[str], path: Path):
    """Renderiza matriz de confusão em estilo heatmap usando PIL."""
    n = len(labels)
    cell = 46
    margin = 140
    width = margin + n * cell + 20
    height = margin + n * cell + 40
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    max_val = matrix.max() if matrix.size else 1

    # eixos
    draw.text((margin, 15), "Predito →", fill="black", font=font)
    draw.text((20, margin), "Verdadeiro ↓", fill="black", font=font)

    for i, label in enumerate(labels):
        draw.text((margin + i * cell + 12, margin - 18), label[:10], fill="black", font=font)
        draw.text((margin - 120, margin + i * cell + 14), label[:15], fill="black", font=font)

    # células
    for i in range(n):
        for j in range(n):
            val = matrix[i, j]
            intensity = int(255 - 180 * (val / max_val))  # mais escuro para valores altos
            color = (70, intensity, 200)
            x0 = margin + j * cell
            y0 = margin + i * cell
            draw.rectangle([x0, y0, x0 + cell, y0 + cell], fill=color, outline="white")
            draw.text((x0 + 10, y0 + 14), str(val), fill="black", font=font)

    img.save(path)


def inspect_class_distribution(df: pd.DataFrame, outputs: Path) -> Dataset2Summary:
    class_counts = df["label"].value_counts()
    text_length_stats = df["text"].str.len().describe()
    duplicates = 1 - len(df.drop_duplicates(subset=["text"])) / len(df)

    outputs.mkdir(parents=True, exist_ok=True)
    _draw_bar_chart(class_counts, outputs / "dataset2_class_distribution.png", "Distribuição de categorias (Dataset 2)")

    return Dataset2Summary(
        shape=df.shape,
        columns=list(df.columns),
        class_counts=class_counts,
        text_length_stats=text_length_stats,
        duplicate_ratio=duplicates,
    )


def train_baseline_classifier(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
    print("[INFO] Iniciando split e treinamento do classificador (Linear SVM via SGD)...", flush=True)
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=test_size, stratify=df["label"], random_state=random_state
    )
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 1), min_df=2, max_features=50_000, sublinear_tf=True, strip_accents="unicode"
                ),
            ),
            (
                "clf",
                SGDClassifier(
                    loss="hinge",
                    alpha=1e-4,
                    max_iter=2000,
                    n_jobs=-1,
                    random_state=random_state,
                ),
            ),
        ]
    )
    model = pipeline.fit(X_train, y_train)
    return model, X_test, y_test


def evaluate_classifier(model: Pipeline, X_test: pd.Series, y_test: pd.Series, outputs: Path) -> Dict[str, object]:
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    macro_f1 = f1_score(y_test, preds, average="macro")
    report = classification_report(y_test, preds, output_dict=True)
    labels = list(model.classes_)
    conf = confusion_matrix(y_test, preds, labels=labels)

    outputs.mkdir(parents=True, exist_ok=True)
    conf_path = outputs / "classifier_confusion_matrix.png"
    _draw_confusion_heatmap(conf, list(model.classes_), conf_path)

    metrics = {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "report": report,
        "confusion_matrix": conf,
        "confusion_path": conf_path,
        "labels": labels,
    }
    return metrics


def build_similarity_index(model: Pipeline, corpus: List[str], labels: List[str]) -> Dict[str, object]:
    vectorizer: TfidfVectorizer = model.named_steps["tfidf"]
    tfidf_matrix = vectorizer.transform(corpus)
    return {"vectorizer": vectorizer, "matrix": tfidf_matrix, "corpus": corpus, "labels": labels}


def predict_ticket(text: str, model: Pipeline, sim_index: Dict[str, object], top_k: int = 5) -> Dict[str, object]:
    vectorizer: TfidfVectorizer = model.named_steps["tfidf"]
    clf = model.named_steps["clf"]
    X = vectorizer.transform([text])
    pred = clf.predict(X)[0]
    scores = clf.decision_function(X)
    scores = scores if scores.ndim == 1 else scores[0]
    exp_scores = np.exp(scores - scores.max())
    proba = float(exp_scores.max() / exp_scores.sum())

    similarities = cosine_similarity(X, sim_index["matrix"]).flatten()
    top_idx = similarities.argsort()[-top_k:][::-1]
    similar = []
    for idx in top_idx:
        similar.append(
            {
                "text": sim_index["corpus"][idx][:180],
                "label": sim_index["labels"][idx],
                "score": float(similarities[idx]),
            }
        )

    return {"prediction": pred, "confidence": proba, "similar": similar}


def recommend_next_action(pred_label: str, confidence: float) -> str:
    high_risk = {"Administrative rights", "Purchase", "Access"}
    if confidence < 0.55:
        return "Baixa confiança: encaminhar para revisão humana imediata."
    if pred_label in high_risk:
        return "Confiança moderada: roteamento assistido e validação humana obrigatória."
    if confidence >= 0.75:
        return "Alta confiança: auto-rotear e sugerir resposta, com opção de revisão humana."
    return "Confiança média: sugerir classificação e similares, agente decide roteamento."


def estimate_operational_roi(automation_share: float = 0.3, time_reduction: float = 0.2) -> Dict[str, float]:
    total_hours = 37098.1  # do diagnóstico Dataset 1
    recoverable = 5337.5   # benchmark P25
    saved = total_hours * automation_share * time_reduction
    recovered = recoverable * time_reduction
    return {
        "hours_saved": saved,
        "recoverable_hours_reduced": recovered,
        "automation_share": automation_share,
        "time_reduction": time_reduction,
    }


def save_classifier_report(summary: Dataset2Summary, metrics: Dict[str, object], outputs: Path, path: Path):
    report_dict = metrics["report"]
    per_class = {k: v for k, v in report_dict.items() if k not in {"accuracy", "macro avg", "weighted avg"}}
    best = max(per_class.items(), key=lambda kv: kv[1]["f1-score"])
    worst = min(per_class.items(), key=lambda kv: kv[1]["f1-score"])
    labels = metrics.get("labels", list(per_class.keys()))
    conf = metrics.get("confusion_matrix")
    confusions = []
    if conf is not None:
        for i, true_lbl in enumerate(labels):
            for j, pred_lbl in enumerate(labels):
                if i != j and conf[i, j] > 0:
                    confusions.append((conf[i, j], true_lbl, pred_lbl))
    confusions = sorted(confusions, key=lambda x: x[0], reverse=True)[:5]

    lines = []
    lines.append("# Classificador de tickets - Dataset 2")
    lines.append("")
    lines.append(f"Shape do dataset: {summary.shape}, colunas: {summary.columns}")
    lines.append(f"Distribuição de classes:\n{summary.class_counts.to_string()}")
    lines.append(f"Duplicidade aproximada: {summary.duplicate_ratio:.3f}")
    lines.append("")
    lines.append("## Métricas principais")
    lines.append(f"- Accuracy: {metrics['accuracy']:.3f}")
    lines.append(f"- Macro F1: {metrics['macro_f1']:.3f}")
    lines.append(f"- Melhor classe (F1): {best[0]} = {best[1]['f1-score']:.3f}")
    lines.append(f"- Pior classe (F1): {worst[0]} = {worst[1]['f1-score']:.3f}")
    if confusions:
        lines.append("- Principais confusões:")
        for c, t, p in confusions:
            lines.append(f"  - {t} rotulado como {p}: {c} casos")
    lines.append("")
    lines.append("## Classification report")
    for cls, vals in per_class.items():
        lines.append(f"- {cls}: precision {vals['precision']:.3f}, recall {vals['recall']:.3f}, f1 {vals['f1-score']:.3f}")
    lines.append("")
    lines.append(f"Matriz de confusão: ver {metrics['confusion_path'].relative_to(PROJECT_ROOT)}")
    path.write_text("\n".join(lines), encoding="utf-8")


def export_strategy_markdown(metrics: Dict[str, object], roi: Dict[str, float], path: Path):
    report_dict = metrics["report"]
    per_class = {k: v for k, v in report_dict.items() if k not in {"accuracy", "macro avg", "weighted avg"}}
    best = max(per_class.items(), key=lambda kv: kv[1]["f1-score"])
    worst = min(per_class.items(), key=lambda kv: kv[1]["f1-score"])
    labels = metrics.get("labels", list(per_class.keys()))
    conf = metrics.get("confusion_matrix")
    confusions = []
    if conf is not None:
        for i, true_lbl in enumerate(labels):
            for j, pred_lbl in enumerate(labels):
                if i != j and conf[i, j] > 0:
                    confusions.append((conf[i, j], true_lbl, pred_lbl))
    confusions = sorted(confusions, key=lambda x: x[0], reverse=True)[:3]

    lines = []
    lines.append("# Estratégia de automação assistida - Challenge 002")
    lines.append("")
    lines.append("## 1. Resumo executivo")
    lines.append(
        "Dataset 1 mostra gargalos comparativos em Chat/Refund High e Social Media/ Billing/Product Inquiry (medianas ~15-17h, tempo proxy)."
    )
    lines.append(
        "Dataset 2 fornece classificador TF-IDF + Linear SVM (SGD) treinado em 47.8k tickets (8 categorias). "
        f"Macro F1 {metrics['macro_f1']:.3f}, accuracy {metrics['accuracy']:.3f}."
    )
    lines.append(
        "Proposta: automação assistida para triagem e similares, focada em grupos de maior dor; revisão humana obrigatória em baixa confiança e categorias sensíveis (Access/Admin/Purchase)."
    )

    lines.append("\n## 2. O que o Dataset 2 permite fazer")
    lines.append("- Categorizar tickets de TI em 8 grupos com F1 macro ~0.85 (baseline atual).")
    lines.append("- Recuperar tickets similares via TF-IDF/cosseno para sugerir resolução ou especialista.")
    lines.append("- Medir confiança por ticket para decidir automação vs revisão humana.")
    lines.append(
        "- Alvos priorizados do Dataset 1 (conceitual): Chat/Refund High e Social Media/ Billing/Product Inquiry podem receber triagem/roteamento assistido para reduzir TTR proxy."
    )

    lines.append("\n## 3. Performance do classificador")
    lines.append(f"- Melhor classe: {best[0]} (F1 {best[1]['f1-score']:.3f}).")
    lines.append(f"- Pior classe: {worst[0]} (F1 {worst[1]['f1-score']:.3f}).")
    if confusions:
        lines.append("- Principais confusões (ver matriz em outputs):")
        for c, t, p in confusions:
            lines.append(f"  - {t} → {p}: {c} casos")

    lines.append("\n## 4. Onde IA ajuda no fluxo")
    lines.append("- Classificação automática inicial com limiar de confiança.")
    lines.append("- Roteamento assistido para especialistas (ex.: Access, Hardware, Storage).")
    lines.append("- Busca de similares para sugerir solução rápida e reduzir retrabalho.")
    lines.append(
        "- Priorização sugerida: quando confiança alta e categoria é baixa criticidade, acelerar resposta; aplicar primeiro nos grupos lentos do Dataset 1."
    )

    lines.append("\n## 5. Onde humano deve permanecer")
    lines.append("- Baixa confiança (<0.55) ou categoria sensível (Administrative rights, Purchase, Access).")
    lines.append("- Casos fora das 8 classes ou com texto ruidoso.")
    lines.append("- Revisão final de respostas automáticas em canais críticos (aprendizado supervisionado).")

    lines.append("\n## 6. Fluxo proposto ponta a ponta")
    lines.append("1) Receber ticket -> classificador retorna categoria + confiança.")
    lines.append("2) Recuperar top similares e sugerir resolução/owner.")
    lines.append("3) Se confiança >=0.75 e categoria baixa criticidade: auto-rotear com sugestão de resposta.")
    lines.append("4) Se confiança entre 0.55-0.75 ou categoria sensível: roteamento assistido + checagem humana.")
    lines.append("5) Se confiança <0.55: fila de revisão humana e feedback para re-treino.")

    lines.append("\n## 7. Estimativa de ROI (cenário ilustrativo)")
    lines.append(
        "Base no diagnóstico do Dataset 1: 37,098 h totais e 5,338 h de desperdício recuperável (proxy de tempo relativo)."
    )
    lines.append(
        f"Se automação assistida cobrir {roi['automation_share']*100:.0f}% dos tickets de menor criticidade e reduzir o tempo em {roi['time_reduction']*100:.0f}%, economiza ~{roi['hours_saved']:.0f} h/mês (proxy)."
    )
    lines.append(
        f"Aplicando {roi['time_reduction']*100:.0f}% de redução sobre o desperdício comparativo, recuperamos ~{roi['recoverable_hours_reduced']:.0f} h/mês (proxy)."
    )
    lines.append("(Estimativas comparativas, não SLA real; dependem de aderência do fluxo e qualidade do texto).")

    lines.append("\n## 8. Limitações")
    lines.append("- Dataset 1 e 2 têm taxonomias diferentes; mapeamento conceitual, não 1:1.")
    lines.append("- Métricas de tempo são proxies relativas; ganhos reais dependem do fluxo produtivo.")
    lines.append("- Classificador depende de texto limpo; entradas ruidosas derrubam confiança.")

    lines.append("\n## 9. Próximos passos")
    lines.append("- Ajustar limiares por categoria com feedback humano.")
    lines.append("- Testar embeddings locais para aumentar recall das classes menores.")
    lines.append("- Integrar motor de similares na ferramenta do agente com captura de feedback.")

    path.write_text("\n".join(lines), encoding="utf-8")


def main(text: str | None = None):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("[INFO] Carregando Dataset 2...")
    df_raw = load_dataset2()
    df = clean_text_data(df_raw)
    summary = inspect_class_distribution(df, OUTPUT_DIR)

    model, X_test, y_test = train_baseline_classifier(df)
    print("[INFO] Avaliando classificador...")
    metrics = evaluate_classifier(model, X_test, y_test, OUTPUT_DIR)

    print("[INFO] Construindo índice de similaridade...")
    sim_index = build_similarity_index(model, corpus=df["text"].tolist(), labels=df["label"].tolist())

    print("[INFO] Salvando relatórios...")
    save_classifier_report(summary, metrics, OUTPUT_DIR, Path(__file__).resolve().parent / "ticket_classifier_report.md")

    roi = estimate_operational_roi()
    export_strategy_markdown(metrics, roi, Path(__file__).resolve().parent / "ticket_automation_strategy.md")

    if text:
        result = predict_ticket(text, model, sim_index)
        action = recommend_next_action(result["prediction"], result["confidence"])
        print("\n=== Inferência ===")
        print(f"Texto: {text[:200]}")
        print(f"Predição: {result['prediction']} | confiança: {result['confidence']:.3f}")
        print(f"Ação sugerida: {action}")
        print("Top similares:")
        for sim in result["similar"]:
            print(f" - ({sim['score']:.3f}) [{sim['label']}] {sim['text']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Treina classificador e opcionalmente roda inferência em um texto.")
    parser.add_argument("--text", type=str, help="Texto de ticket para inferência opcional", default=None)
    args = parser.parse_args()
    main(text=args.text)
