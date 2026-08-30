"""Motor de priorização de pipeline — pacote Python puro, sem dependência
web. Importado por `api/`, `validation/` e pela exportação CSV.
"""

from . import (
    confianca,
    constants,
    curves,
    estado,
    explicacao,
    export,
    model,
    pipeline,
    reference,
    repository,
    shrinkage,
)
from .pipeline import ScoredPipeline, load_and_score, score_row
from .repository import Dataset, load_dataset

__all__ = [
    "confianca",
    "constants",
    "curves",
    "estado",
    "explicacao",
    "export",
    "model",
    "pipeline",
    "reference",
    "repository",
    "shrinkage",
    "ScoredPipeline",
    "load_and_score",
    "score_row",
    "Dataset",
    "load_dataset",
]
