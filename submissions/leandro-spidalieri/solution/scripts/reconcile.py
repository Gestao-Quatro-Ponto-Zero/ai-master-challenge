"""Recalcula indicadores centrais sem Pandas, sklearn ou código da aplicação."""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
RAW = ROOT / "data" / "raw"


def json_file(name):
    return json.loads((ART / name).read_text())


def csv_file(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(actual, expected, field):
    if actual != expected:
        raise ValueError(f"{field}: obtido {actual!r}, esperado {expected!r}.")


def check_ratio(actual, expected, field):
    if abs(actual - float(expected)) > 1e-12:
        raise ValueError(f"{field}: obtido {actual!r}, esperado {expected!r}.")


def support(manifest):
    file = RAW / manifest["arquivo"]
    rows = csv_file(file)
    check(sha(file), manifest["sha256"], "SHA suporte")
    check(len(rows), manifest["linhas"], "linhas suporte")
    check(len({r["Ticket ID"] for r in rows}), len(rows), "IDs distintos suporte")
    diagnosis = json_file("diagnosis.json")
    total = diagnosis["total"]
    statuses = Counter(r["Ticket Status"] for r in rows)
    ratings = Counter(
        int(float(r["Customer Satisfaction Rating"]))
        for r in rows
        if r["Customer Satisfaction Rating"]
    )
    rated = sum(ratings.values())
    check(
        {f"nota_{n}": ratings[n] for n in range(1, 6)},
        {k: total[k] for k in (f"nota_{n}" for n in range(1, 6))},
        "histograma de notas",
    )
    check_ratio(total["cobertura_notas"], Fraction(rated, len(rows)), "cobertura CSAT")
    check_ratio(total["proporcao_4_5"], Fraction(ratings[4] + ratings[5], rated), "notas 4–5")
    pairs = [
        (
            datetime.fromisoformat(r["First Response Time"]),
            datetime.fromisoformat(r["Time to Resolution"]),
        )
        for r in rows
        if r["First Response Time"] and r["Time to Resolution"]
    ]
    inversions = sum(b < a for a, b in pairs)
    check(total["pares"], len(pairs), "pares de timestamps")
    check(total["inversoes"], inversions, "pares invertidos")
    check(
        {row["status"]: row["n"] for row in diagnosis["satisfacao_por_status"]},
        dict(statuses),
        "estoque por status",
    )
    channels_types = Counter((r["Ticket Channel"], r["Ticket Type"]) for r in rows)
    check(
        {(r["canal"], r["tipo"]): r["n"] for r in diagnosis["cortes"]["canal × tipo"]},
        dict(channels_types),
        "volume canal × tipo",
    )
    print(
        f"Suporte: {len(rows)} tickets, {rated} notas, {ratings[4] + ratings[5]} notas 4–5, {inversions}/{len(pairs)} inversões."
    )


def macro_f1(confusion, labels):
    values = []
    for label in labels:
        tp = confusion[label, label]
        denominator = sum(confusion[label, k] + confusion[k, label] for k in labels)
        values.append(Fraction(2 * tp, denominator) if denominator else 0)
    return sum(values) / len(labels)


def classifier(manifest):
    file = RAW / manifest["arquivo"]
    raw = csv_file(file)
    check(sha(file), manifest["sha256"], "SHA TI")
    check(len(raw), manifest["linhas"], "linhas TI")
    quality = json_file("it-quality.json")
    check(dict(Counter(r["Topic_group"] for r in raw)), quality["classes_raw"], "rótulos TI")
    evidence = json_file("evaluation.json")
    split_path = ART / "local" / "splits.csv"
    predictions_path = ART / "local" / "test-predictions.csv"
    check(sha(split_path), evidence["splits_sha256"], "SHA partições")
    parts = csv_file(split_path)
    check(len({r["id"] for r in parts}), len(parts), "IDs distintos TI")
    partitions = defaultdict(set)
    for row in parts:
        partitions[row["group"]].add(row["particao"])
    check(max(map(len, partitions.values())), 1, "nenhum grupo em partições distintas")
    check(len(partitions), quality["grupos"], "grupos TI")
    check(
        dict(Counter(r["particao"] for r in parts)),
        evidence["n_por_particao"],
        "tamanho das partições",
    )
    labels = {label for label in quality["classes_raw"]}
    majority = Counter(r["Topic_group"] for r in parts if r["particao"] == "treino").most_common(1)[
        0
    ][0]
    check(majority, evidence["classe_majoritaria_treino"], "maioria no treino")
    test = evidence["teste"]
    check(sha(predictions_path), test["predicoes_sha256"], "SHA predições")
    pred = csv_file(predictions_path)
    expected = {r["id"]: r["Topic_group"] for r in parts if r["particao"] == "teste"}
    check({r["id"]: r["real"] for r in pred}, expected, "rótulos do teste reservado")
    check(len(pred), len(expected), "sem predições repetidas")
    check({r["previsto"] for r in pred} <= labels, True, "somente classes conhecidas")
    threshold = evidence["limiar"]
    viable = [
        r
        for r in evidence["curva_validacao"]
        if r["aceitos"] >= evidence["criterio_validacao"]["minimo_aceitos"]
        and r["ic95_wilson_acerto"][0] >= evidence["criterio_validacao"]["limite_inferior_wilson"]
    ]
    selected = sorted(viable, key=lambda r: (-r["aceitos"], -r["acertos_aceitos"], r["limiar"]))
    check(threshold, selected[0]["limiar"] if selected else 1.01, "seleção do corte na validação")
    accepted = []
    for row in pred:
        decision = row["apto"] == "True" and float(row["score"]) >= threshold
        check(decision, row["aceito"] == "True", "decisão registrada")
        if decision:
            accepted.append(row)
    correct = sum(r["real"] == r["previsto"] for r in accepted)
    conf = Counter((r["real"], r["previsto"]) for r in pred)
    baseline = Counter((r["real"], majority) for r in pred)
    check(
        test["matriz_confusao"],
        [[conf[i, j] for j in test["classes"]] for i in test["classes"]],
        "matriz de confusão",
    )
    for key, matrix in [("tfidf_logit", conf), ("classe_majoritaria", baseline)]:
        check_ratio(
            test[key]["accuracy"],
            Fraction(sum(matrix[k, k] for k in labels), len(pred)),
            f"{key} accuracy",
        )
        check_ratio(test[key]["macro_f1"], macro_f1(matrix, labels), f"{key} macro-F1")
    check(test["politica"]["aceitos"], len(accepted), "sugestões")
    check(test["politica"]["acertos_aceitos"], correct, "sugestões corretas")
    check_ratio(test["politica"]["cobertura"], Fraction(len(accepted), len(pred)), "cobertura")
    if accepted:
        check_ratio(
            test["politica"]["acerto_nos_aceitos"],
            Fraction(correct, len(accepted)),
            "acerto em sugestões",
        )
    print(
        f"TI: teste {len(pred)}, {len(accepted)} sugestões e {correct} acertos entre sugestões. Partições disjuntas e métricas reconciliadas."
    )


def impact():
    base = json_file("impact.json")["Base"]["resultado"]
    # 2.500 × 1/2 × 3/5 × 4/5 = 600. Cada triagem poupa 4 − (1,5 + 0,5 + 4/20) = 1,8 min.
    check(base["processados_mes"], 600, "triagens base")
    check(base["horas_liquidas_mes"], 18, "horas base")
    check(base["valor_liquido_capacidade_mes"], 930, "valor base")
    check(base["caixa_liquido_12m"], -3300, "caixa anual base")
    check(base["payback_meses"], None, "payback base")
    print(
        "Impacto: cenário base conferido por cálculo manual, 18 h/mês e caixa anual de −R$ 3.300 nas premissas iniciais."
    )


def main():
    manifest = json_file("manifest.json")
    support(manifest["suporte"])
    classifier(manifest["ti"])
    impact()
    print("PASSOU · reconciliação independente")


if __name__ == "__main__":
    main()
