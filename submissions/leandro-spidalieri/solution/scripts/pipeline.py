"""Operações explícitas. Execute com python scripts/pipeline.py <etapa>."""

import argparse
import os
import platform
import sys
import time
from dataclasses import asdict
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supportops.analytics import diagnostic  # noqa: E402
from supportops.classifier import (  # noqa: E402
    MIN_ACCEPTED,
    MIN_WILSON,
    classify,
    coverage,
    fit,
    load_local,
    prepare,
    provenance,
    score_rows,
    select_threshold,
    split,
)
from supportops.impact import SCENARIOS, calculate  # noqa: E402
from supportops.ingest import (  # noqa: E402
    ARTIFACTS,
    IT,
    IT_FIELDS,
    LOCAL,
    SUPPORT,
    SUPPORT_FIELDS,
    acquire,
    digest,
    load,
    write_json,
)
from supportops.policy import DOMAIN_IT, SUGGEST  # noqa: E402


def audit():
    frame, manifest_support = load(SUPPORT, SUPPORT_FIELDS)
    it, manifest_it = load(IT, IT_FIELDS)
    write_json(ARTIFACTS / "manifest.json", {"suporte": manifest_support, "ti": manifest_it})
    write_json(ARTIFACTS / "diagnosis.json", diagnostic(frame, SUPPORT.sha256))
    _, quality = prepare(it, IT.sha256)
    write_json(ARTIFACTS / "it-quality.json", {"dataset_sha256": IT.sha256, **quality})
    write_json(
        ARTIFACTS / "impact.json",
        {
            name: {"premissas": asdict(value), "resultado": calculate(value)}
            for name, value in SCENARIOS.items()
        },
    )
    print(f"Auditoria gerada: suporte {len(frame):,}, TI {len(it):,}.")


def train():
    raw, _ = load(IT, IT_FIELDS)
    clean, _ = prepare(raw, IT.sha256)
    parts = split(clean)
    data = clean.join(parts["particao"])
    train_rows = data[data["particao"].eq("treino")]
    val_rows = data[data["particao"].eq("validacao")]
    pipeline = fit(train_rows)
    validation = score_rows(pipeline, val_rows)
    threshold, curve = select_threshold(validation)
    env = provenance(IT.sha256)
    LOCAL.mkdir(parents=True, exist_ok=True)
    splits = parts.to_csv(index=False).encode()
    splits_sha = digest(splits)
    # Treino e avaliação são etapas separadas. Metadados escritos por último.
    path = LOCAL / "model.joblib"
    temp = path.with_name(f".model-{os.getpid()}.joblib")
    try:
        joblib.dump(pipeline, temp, compress=3)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    (LOCAL / "splits.csv").write_bytes(splits)
    model_version = f"tfidf-logit-{env['codigo_e_lock_sha256'][:10]}-{IT.sha256[:10]}"
    meta = {
        "modelo_versao": model_version,
        "proveniencia": env,
        "limiar": threshold,
        "binario_sha256": digest(path.read_bytes()),
        "splits_sha256": splits_sha,
        "classe_majoritaria_treino": str(train_rows["Topic_group"].mode().iloc[0]),
        "n_por_particao": {str(k): int(v) for k, v in parts["particao"].value_counts().items()},
        "classes_por_particao": {
            str(name): dict(zip(sub["Topic_group"], sub["n"].astype(int), strict=True))
            for name, sub in parts.value_counts(["particao", "Topic_group"])
            .rename("n")
            .reset_index()
            .groupby("particao")
        },
        "criterio_validacao": {
            "minimo_aceitos": MIN_ACCEPTED,
            "limite_inferior_wilson": MIN_WILSON,
        },
        "curva_validacao": curve,
        "validacao_no_limiar": coverage(validation, threshold),
    }
    write_json(LOCAL / "model.json", meta)
    print(
        f"Política congelada antes do teste: {model_version}, limiar {threshold}, {meta['n_por_particao']}."
    )


def evaluate():
    pipeline, meta = load_local(LOCAL)
    raw, _ = load(IT, IT_FIELDS)
    clean, _ = prepare(raw, IT.sha256)
    parts_file = LOCAL / "splits.csv"
    if digest(parts_file.read_bytes()) != meta["splits_sha256"]:
        raise ValueError("Partições divergentes do treino.")
    parts = pd.read_csv(parts_file, dtype=str)
    test_ids = parts.loc[parts["particao"].eq("teste"), "id"]
    test = clean.set_index("id", drop=False).loc[test_ids]
    predictions = score_rows(pipeline, test)
    threshold = meta["limiar"]
    predictions["aceito"] = predictions["apto"] & predictions["score"].ge(threshold)
    y, p = predictions["real"], predictions["previsto"]
    labels = list(pipeline.classes_)
    majority = [meta["classe_majoritaria_treino"]] * len(y)
    # Amostra sem depender do acerto. Mede a função de inferência, sem I/O ou UI.
    latency_sample = test.sample(n=min(200, len(test)), random_state=meta["proveniencia"]["seed"])
    classify(pipeline, meta, latency_sample.iloc[0]["Document"], DOMAIN_IT, "Normal")
    latencies = []
    for row in latency_sample.to_dict(orient="records"):
        result = classify(pipeline, meta, row["Document"], DOMAIN_IT, "Normal", row["id"])
        expected = bool(predictions.loc[predictions["id"].eq(row["id"]), "aceito"].iloc[0])
        if (result["decisao"] == SUGGEST) != expected:
            raise ValueError("Política de lote e decisão individual divergentes.")
        latencies.append(result["latencia_ms"])
    latency = pd.Series(latencies)
    examples = predictions.assign(acerto=y.eq(p)).sort_values("id")
    cases = {}
    for name, mask in {
        "sugestao_correta": examples["aceito"] & examples["acerto"],
        "sugestao_incorreta": examples["aceito"] & ~examples["acerto"],
        "revisao": ~examples["aceito"],
        "erro_modelo": ~examples["acerto"],
    }.items():
        cases[name] = (
            examples.loc[mask, ["id", "real", "previsto", "score", "guardas"]]
            .head(3)
            .to_dict("records")
        )
    csv = predictions.to_csv(index=False).encode()
    (LOCAL / "test-predictions.csv").write_bytes(csv)
    result = {
        **{k: v for k, v in meta.items() if k != "binario_sha256"},
        "teste": {
            "n": len(y),
            "classe_majoritaria": {
                "accuracy": accuracy_score(y, majority),
                "macro_f1": f1_score(y, majority, labels=labels, average="macro", zero_division=0),
            },
            "tfidf_logit": {
                "accuracy": accuracy_score(y, p),
                "macro_f1": f1_score(y, p, average="macro"),
            },
            "classes": labels,
            "por_classe": {
                label: metrics
                for label, metrics in classification_report(
                    y, p, labels=labels, output_dict=True, zero_division=0
                ).items()
                if label in labels
            },
            "matriz_confusao": confusion_matrix(y, p, labels=labels).tolist(),
            "politica": coverage(predictions, threshold),
            "politica_por_classe_real": {
                str(label): coverage(group, threshold)
                for label, group in predictions.groupby("real")
            },
            "predicoes_sha256": digest(csv),
            "exemplos_por_id": cases,
            "latencia_ms": {
                "n": len(latencies),
                "p50": float(latency.median()),
                "p95": float(latency.quantile(0.95)),
                "ambiente": f"{platform.system()} {platform.machine()}, Python {platform.python_version()}",
                "escopo": "Decisão individual local, modelo em memória, amostra fixa, após aquecimento.",
            },
        },
    }
    write_json(ARTIFACTS / "evaluation.json", result)
    print("Teste reservado:", result["teste"]["tfidf_logit"], result["teste"]["politica"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=["acquire", "audit", "train", "evaluate"])
    args = parser.parse_args()
    start = time.perf_counter()
    try:
        if args.step == "acquire":
            for source in (SUPPORT, IT):
                print(f"{source.file}: {acquire(source)}")
        else:
            {"audit": audit, "train": train, "evaluate": evaluate}[args.step]()
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Falha na etapa {args.step}: {exc}\n")
    print(f"Tempo decorrido na etapa {args.step}: {time.perf_counter() - start:.2f} s.")


if __name__ == "__main__":
    main()
