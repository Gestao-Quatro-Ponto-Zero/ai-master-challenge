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
from scoring.carga import CargaVendedorEstado, annotate_sobrecarga, compute_carga, index_by_agent_estado
from scoring.fit import FitContext, build_fit_context
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
    fit_ctx: FitContext
    default_carga: list[CargaVendedorEstado]
    default_scored_com_carga: pd.DataFrame
    settings: Settings
    _scored_cache: dict[str, pd.DataFrame] = field(default_factory=dict)
    _carga_cache: dict[str, list[CargaVendedorEstado]] = field(default_factory=dict)
    _scored_com_carga_cache: dict[str, pd.DataFrame] = field(default_factory=dict)

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

    def carga_as_of(self, as_of: pd.Timestamp | None) -> list[CargaVendedorEstado]:
        """Carga por vendedor/ESTADO contra `as_of` — recalculada por
        completo quando `as_of` muda, porque ESTADO (e portanto a carga)
        depende da idade em `as_of` (pipeline-api spec, Requirement
        "Análise de carga e sobrecarga por escritório")."""
        resolved = as_of if as_of is not None else self.default_as_of
        if resolved == self.default_as_of:
            return self.default_carga

        key = resolved.isoformat()
        if key not in self._carga_cache:
            self._carga_cache[key] = compute_carga(self.scored_as_of(resolved))
        return self._carga_cache[key]

    def carga_index_as_of(
        self, as_of: pd.Timestamp | None
    ) -> dict[tuple[str, str], CargaVendedorEstado]:
        return index_by_agent_estado(self.carga_as_of(as_of))

    def scored_com_carga_as_of(self, as_of: pd.Timestamp | None) -> pd.DataFrame:
        """`scored_as_of` com a coluna booleana `sobrecarregado` anexada —
        Requirement "Sinalizador de sobrecarga na listagem de
        oportunidades". Cacheada por `as_of`, como `scored_as_of`."""
        resolved = as_of if as_of is not None else self.default_as_of
        if resolved == self.default_as_of:
            return self.default_scored_com_carga

        key = resolved.isoformat()
        if key not in self._scored_com_carga_cache:
            scored = self.scored_as_of(resolved).copy()
            scored["sobrecarregado"] = annotate_sobrecarga(scored, self.carga_index_as_of(resolved))
            self._scored_com_carga_cache[key] = scored
        return self._scored_com_carga_cache[key]


def build_app_state(settings: Settings) -> AppState:
    scored_pipeline = pipeline_mod.load_and_score(str(settings.data_dir))
    export_mod.export_processed_dataset(scored_pipeline, settings.export_path)

    dataset = scored_pipeline.dataset
    closed = pipeline_mod.fechados(dataset)
    fit_ctx = build_fit_context(dataset, closed)
    export_mod.export_analysis_by_product(dataset, fit_ctx, settings.analysis_by_product_path)
    export_mod.export_analysis_by_sector(dataset, fit_ctx, settings.analysis_by_sector_path)

    default_carga = compute_carga(scored_pipeline.scored)
    default_carga_index = index_by_agent_estado(default_carga)
    default_scored_com_carga = scored_pipeline.scored.copy()
    default_scored_com_carga["sobrecarregado"] = annotate_sobrecarga(
        default_scored_com_carga, default_carga_index
    )

    return AppState(
        dataset=dataset,
        ctx=scored_pipeline.ctx,
        ref=scored_pipeline.ref,
        ages_won_ordenadas=scored_pipeline.ages_won_ordenadas,
        default_as_of=scored_pipeline.as_of,
        default_scored=scored_pipeline.scored,
        fit_ctx=fit_ctx,
        default_carga=default_carga,
        default_scored_com_carga=default_scored_com_carga,
        settings=settings,
    )
