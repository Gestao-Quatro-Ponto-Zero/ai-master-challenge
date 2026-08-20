"""Estado da aplicação: dados carregados uma vez na inicialização.

`ctx` (p̂_produto) e `ref` (distribuição de referência de SCORE) dependem
só dos negócios FECHADOS — nunca da data de referência (`as_of`) usada para
calcular idade dos abertos — então são computados uma única vez e
reaproveitados mesmo quando uma rota recebe um `as_of` diferente do padrão.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from scoring import export as export_mod
from scoring import pipeline as pipeline_mod
from scoring.reference import ReferenceDistribution
from scoring.repository import Dataset, load_dataset

from config import Settings


@dataclass
class AppState:
    dataset: Dataset
    ctx: pipeline_mod.model.ScoringContext
    ref: ReferenceDistribution
    ages_won_ordenadas: list[float]
    default_as_of: pd.Timestamp
    default_scored: pd.DataFrame
    settings: Settings
    _scored_cache: dict[str, pd.DataFrame] = field(default_factory=dict)

    def scored_as_of(self, as_of: pd.Timestamp | None) -> pd.DataFrame:
        """Oportunidades abertas pontuadas contra `as_of` (padrão se None)."""
        resolved = as_of if as_of is not None else self.default_as_of
        if resolved == self.default_as_of:
            return self.default_scored

        key = resolved.isoformat()
        if key not in self._scored_cache:
            self._scored_cache[key] = pipeline_mod.score_open_pipeline(
                self.dataset, self.ctx, self.ref, self.ages_won_ordenadas, resolved
            )
        return self._scored_cache[key]


def build_app_state(settings: Settings) -> AppState:
    scored_pipeline = pipeline_mod.load_and_score(str(settings.data_dir))
    export_mod.export_processed_dataset(scored_pipeline, settings.export_path)

    return AppState(
        dataset=scored_pipeline.dataset,
        ctx=scored_pipeline.ctx,
        ref=scored_pipeline.ref,
        ages_won_ordenadas=scored_pipeline.ages_won_ordenadas,
        default_as_of=scored_pipeline.as_of,
        default_scored=scored_pipeline.scored,
        settings=settings,
    )
