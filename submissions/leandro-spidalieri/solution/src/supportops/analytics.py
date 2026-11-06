"""Cubo agregado sem textos livres e denominadores reutilizados na interface."""

from collections import Counter

import pandas as pd

from .quality import DIMENSIONS, support_quality

MIN_RATINGS = 30
STATS = (
    "n",
    "respostas_ts",
    "resolucoes_ts",
    "pares",
    "inversoes",
    "resolucao_texto",
    "descricao_texto",
    "nota_invalida",
    "nota_1",
    "nota_2",
    "nota_3",
    "nota_4",
    "nota_5",
)


def summarize(stats: dict) -> dict:
    n = stats["n"]
    votes = {i: stats[f"nota_{i}"] for i in range(1, 6)}
    rated = sum(votes.values())
    good = votes[4] + votes[5]
    return {
        **stats,
        "n_notas": rated,
        "n_4_5": good,
        "cobertura_notas": rated / n if n else None,
        "proporcao_4_5": good / rated if rated else None,
        "mediana_ordinal": ordinal_median(votes),
        "amostra_pequena": rated < MIN_RATINGS,
    }


def ordinal_median(votes):
    total = sum(votes.values())
    if not total:
        return None
    running = 0
    for score, n in votes.items():
        running += n
        if running * 2 >= total:
            return score


def group_stats(cube: list[dict], dimensions=()) -> list[dict]:
    groups = {}
    for row in cube:
        key = tuple(row[d] for d in dimensions)
        values = groups.setdefault(key, Counter())
        values.update({stat: row[stat] for stat in STATS})
    return [
        {**dict(zip(dimensions, key, strict=True)), **summarize(values)}
        for key, values in sorted(groups.items())
    ]


def diagnostic(frame: pd.DataFrame, sha256: str) -> dict:
    clean, quality = support_quality(frame)
    for n in range(1, 6):
        clean[f"nota_{n}"] = clean["nota"].eq(n)
    clean["n"] = 1
    clean = clean.rename(
        columns={
            "timestamp_resposta": "respostas_ts",
            "timestamp_resolucao": "resolucoes_ts",
            "par_completo": "pares",
            "par_invertido": "inversoes",
            "resolucao_presente": "resolucao_texto",
            "descricao_presente": "descricao_texto",
        }
    )
    cube = clean.groupby(list(DIMENSIONS), sort=True)[list(STATS)].sum().to_dict(orient="records")
    keys = clean.groupby(list(DIMENSIONS), sort=True).size().index
    cube = [
        dict(zip(DIMENSIONS, key, strict=True), **row) for key, row in zip(keys, cube, strict=True)
    ]
    return {
        "dataset_sha256": sha256,
        "qualidade": quality,
        "cubo": cube,
        "total": summarize({stat: sum(row[stat] for row in cube) for stat in STATS}),
        "satisfacao_por_status": group_stats(cube, ("status",)),
        "cortes": {
            " × ".join(dims): group_stats(cube, dims)
            for dims in [*((d,) for d in DIMENSIONS), ("canal", "prioridade"), ("canal", "tipo")]
        },
    }
