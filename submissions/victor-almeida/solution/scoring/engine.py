"""
Scoring Engine — Orquestrador do calculo de score.

Combina os 5 componentes (stage, value, velocity, seller_fit, account_health)
para calcular o score final de cada deal ativo no pipeline.

Referencia: specs/scoring_engine.md, secoes 8-12.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from scoring.constants import (
    ACTIVE_STAGES,
    REFERENCE_DATE,
    STAGE_SCORES,
    WEIGHTS,
    ZOMBIE_THRESHOLD,
)
from scoring.velocity import calculate_velocity_score
from scoring.seller_fit import build_seller_fit_stats, calculate_seller_fit_score
from scoring.account_health import (
    build_account_health_stats,
    calculate_account_health_score,
)


class ScoringEngine:
    """Orquestrador do calculo de score.

    Inicializado uma vez com os DataFrames; calcula scores sob demanda.
    Pre-calcula estatisticas de seller fit e account health no __init__
    para evitar recalculo a cada chamada.
    """

    def __init__(
        self,
        pipeline_df: pd.DataFrame,
        accounts_df: pd.DataFrame,
        products_df: pd.DataFrame,
        sales_teams_df: pd.DataFrame,
        reference_date: pd.Timestamp = REFERENCE_DATE,
    ):
        """Inicializa o engine e pre-calcula estatisticas.

        Args:
            pipeline_df: Pipeline ja enriquecido (com JOINs feitos pelo data_loader).
            accounts_df: Tabela de contas.
            products_df: Tabela de produtos.
            sales_teams_df: Tabela de vendedores.
            reference_date: Data de referencia para calculos temporais.
        """
        self.reference_date = reference_date
        self.max_value = products_df["sales_price"].max()

        # Pre-calcular estatisticas
        self.fit_stats = build_seller_fit_stats(pipeline_df, accounts_df)
        self.account_stats = build_account_health_stats(pipeline_df, reference_date)

        # Armazenar pipeline enriquecido
        self.pipeline_df = pipeline_df

        # Filtrar deals ativos
        self.active_deals = pipeline_df[
            pipeline_df["deal_stage"].isin(ACTIVE_STAGES)
        ].copy()

    def score_pipeline(self) -> pd.DataFrame:
        """Calcula score para todos os deals ativos.

        Retorna DataFrame com colunas originais + colunas de scoring:
        score_final, score_stage, score_value, score_velocity,
        score_seller_fit, score_account_health, velocity_label,
        velocity_ratio, is_zombie, is_critical_zombie, effective_value,
        score_breakdown.
        """
        df = self.active_deals.copy()

        if df.empty:
            # Retornar DataFrame vazio com as colunas esperadas
            for col in [
                "score_final", "score_stage", "score_value",
                "score_velocity", "score_seller_fit", "score_account_health",
                "velocity_label", "velocity_ratio", "is_zombie",
                "is_critical_zombie", "effective_value", "score_breakdown",
            ]:
                df[col] = pd.Series(dtype="float64") if col != "score_breakdown" else pd.Series(dtype="object")
            return df

        # --- Stage Score (vectorized) ---
        df["score_stage"] = df["deal_stage"].map(STAGE_SCORES).fillna(0)

        # --- Value Score (vectorized) ---
        df["effective_value"] = df["sales_price"]
        df["score_value"] = (
            np.log1p(df["effective_value"]) / np.log1p(self.max_value) * 100
        ).clip(0, 100)

        # --- Velocity Score (apply — returns tuple) ---
        velocity_results = df.apply(
            lambda row: calculate_velocity_score(
                row["deal_stage"],
                row["days_in_stage"] if pd.notna(row["days_in_stage"]) else None,
            ),
            axis=1,
        )
        df["score_velocity"] = velocity_results.apply(lambda x: x[0])
        df["velocity_label"] = velocity_results.apply(lambda x: x[1])
        velocity_meta = velocity_results.apply(lambda x: x[2])
        df["velocity_ratio"] = velocity_meta.apply(lambda x: x.get("ratio"))

        # --- Seller Fit Score (apply — lookup in stats) ---
        seller_fit_results = df.apply(
            lambda row: calculate_seller_fit_score(
                row["sales_agent"],
                row["sector"] if pd.notna(row.get("sector")) else None,
                self.fit_stats,
            ),
            axis=1,
        )
        df["score_seller_fit"] = seller_fit_results.apply(lambda x: x[0])
        seller_fit_meta = seller_fit_results.apply(lambda x: x[1])

        # --- Account Health Score (apply — lookup in stats) ---
        account_health_results = df.apply(
            lambda row: calculate_account_health_score(
                row["account"] if pd.notna(row.get("account")) else None,
                self.account_stats,
            ),
            axis=1,
        )
        df["score_account_health"] = account_health_results.apply(lambda x: x[0])
        account_health_meta = account_health_results.apply(lambda x: x[1])

        # --- Score Final (vectorized) ---
        df["score_final"] = (
            df["score_stage"] * WEIGHTS["stage"]
            + df["score_value"] * WEIGHTS["expected_value"]
            + df["score_velocity"] * WEIGHTS["velocity"]
            + df["score_seller_fit"] * WEIGHTS["seller_fit"]
            + df["score_account_health"] * WEIGHTS["account_health"]
        ).clip(0, 100).round(1)

        # --- Flags ---
        df["is_zombie"] = df["velocity_ratio"].fillna(0) >= ZOMBIE_THRESHOLD
        if not df.empty:
            value_p75 = df["effective_value"].quantile(0.75)
            df["is_critical_zombie"] = df["is_zombie"] & (df["effective_value"] > value_p75)
        else:
            df["is_critical_zombie"] = False

        # --- Score Breakdown ---
        df["score_breakdown"] = df.apply(
            lambda row: self._build_breakdown(
                row,
                seller_fit_meta.loc[row.name],
                account_health_meta.loc[row.name],
            ),
            axis=1,
        )

        # Ordenar por score_final descendente
        df = df.sort_values("score_final", ascending=False).reset_index(drop=True)

        return df

    def score_single_deal(self, opportunity_id: str) -> dict:
        """Calcula score detalhado para um unico deal.

        Args:
            opportunity_id: ID da oportunidade.

        Returns:
            Dict com score, todos os componentes e metadados completos.
            Retorna None se o deal nao for encontrado.
        """
        deal_rows = self.active_deals[
            self.active_deals["opportunity_id"] == opportunity_id
        ]

        if deal_rows.empty:
            return None

        row = deal_rows.iloc[0]

        # Stage score
        score_stage = STAGE_SCORES.get(row["deal_stage"], 0)

        # Value score
        effective_value = row["sales_price"]
        if self.max_value > 0:
            score_value = min(
                np.log1p(effective_value) / np.log1p(self.max_value) * 100, 100.0
            )
        else:
            score_value = 0.0

        # Velocity score
        days_in_stage = row["days_in_stage"] if pd.notna(row["days_in_stage"]) else None
        score_velocity, velocity_label, velocity_meta = calculate_velocity_score(
            row["deal_stage"], days_in_stage
        )

        # Seller fit score
        sector = row["sector"] if pd.notna(row.get("sector")) else None
        score_seller_fit, fit_meta = calculate_seller_fit_score(
            row["sales_agent"], sector, self.fit_stats
        )

        # Account health score
        account = row["account"] if pd.notna(row.get("account")) else None
        score_account_health, health_meta = calculate_account_health_score(
            account, self.account_stats
        )

        # Score final
        score_final = round(
            min(
                max(
                    score_stage * WEIGHTS["stage"]
                    + score_value * WEIGHTS["expected_value"]
                    + score_velocity * WEIGHTS["velocity"]
                    + score_seller_fit * WEIGHTS["seller_fit"]
                    + score_account_health * WEIGHTS["account_health"],
                    0,
                ),
                100,
            ),
            1,
        )

        # Flags
        velocity_ratio = velocity_meta.get("ratio")
        is_zombie = (velocity_ratio or 0) >= ZOMBIE_THRESHOLD
        is_critical_zombie = False
        if is_zombie and not self.active_deals.empty:
            value_p75 = self.active_deals["sales_price"].quantile(0.75)
            is_critical_zombie = effective_value > value_p75

        # Breakdown
        breakdown = self._build_breakdown_from_components(
            score_final=score_final,
            score_stage=score_stage,
            score_value=score_value,
            score_velocity=score_velocity,
            score_seller_fit=score_seller_fit,
            score_account_health=score_account_health,
            deal_stage=row["deal_stage"],
            product=row.get("product", ""),
            effective_value=effective_value,
            velocity_label=velocity_label,
            velocity_ratio=velocity_ratio,
            days_in_stage=days_in_stage,
            fit_meta=fit_meta,
            health_meta=health_meta,
            is_zombie=is_zombie,
            is_critical_zombie=is_critical_zombie,
        )

        return {
            "opportunity_id": opportunity_id,
            "score_final": score_final,
            "score_stage": score_stage,
            "score_value": round(score_value, 1),
            "score_velocity": score_velocity,
            "score_seller_fit": score_seller_fit,
            "score_account_health": score_account_health,
            "velocity_label": velocity_label,
            "velocity_ratio": velocity_ratio,
            "is_zombie": is_zombie,
            "is_critical_zombie": is_critical_zombie,
            "effective_value": effective_value,
            "deal_stage": row["deal_stage"],
            "sales_agent": row["sales_agent"],
            "product": row.get("product", ""),
            "account": row.get("account", ""),
            "score_breakdown": breakdown,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_breakdown(
        self,
        row: pd.Series,
        fit_meta: dict,
        health_meta: dict,
    ) -> dict:
        """Constroi o score_breakdown dict para uma row do DataFrame."""
        return self._build_breakdown_from_components(
            score_final=row["score_final"],
            score_stage=row["score_stage"],
            score_value=row["score_value"],
            score_velocity=row["score_velocity"],
            score_seller_fit=row["score_seller_fit"],
            score_account_health=row["score_account_health"],
            deal_stage=row["deal_stage"],
            product=row.get("product", ""),
            effective_value=row["effective_value"],
            velocity_label=row["velocity_label"],
            velocity_ratio=row["velocity_ratio"],
            days_in_stage=row["days_in_stage"] if pd.notna(row.get("days_in_stage")) else None,
            fit_meta=fit_meta,
            health_meta=health_meta,
            is_zombie=row["is_zombie"],
            is_critical_zombie=row["is_critical_zombie"],
        )

    def _build_breakdown_from_components(
        self,
        score_final: float,
        score_stage: float,
        score_value: float,
        score_velocity: float,
        score_seller_fit: float,
        score_account_health: float,
        deal_stage: str,
        product: str,
        effective_value: float,
        velocity_label: str,
        velocity_ratio,
        days_in_stage,
        fit_meta: dict,
        health_meta: dict,
        is_zombie: bool,
        is_critical_zombie: bool,
    ) -> dict:
        """Constroi o breakdown dict completo para explicabilidade."""
        # Stage detail
        if deal_stage == "Engaging":
            stage_detail = "Deal em Engaging — ja qualificado"
        elif deal_stage == "Prospecting":
            stage_detail = "Deal em Prospecting — ainda em qualificacao"
        else:
            stage_detail = f"Deal em {deal_stage}"

        # Value detail
        if score_value > 75:
            value_level = "alto"
        elif score_value > 25:
            value_level = "medio"
        else:
            value_level = "baixo"
        value_detail = f"Valor {value_level} ({product}, ${effective_value:,.0f})"

        # Velocity detail
        velocity_detail = self._velocity_detail(
            deal_stage, days_in_stage, velocity_label, velocity_ratio
        )

        # Seller fit detail
        seller_fit_detail = self._seller_fit_detail(fit_meta)

        # Account health detail
        account_health_detail = self._account_health_detail(health_meta)

        # Zombie detail
        zombie_detail = None
        if is_zombie:
            if is_critical_zombie:
                zombie_detail = (
                    f"CRITICO: deal zumbi de alto valor "
                    f"({velocity_ratio:.1f}x acima do esperado, ${effective_value:,.0f})"
                )
            else:
                zombie_detail = (
                    f"Deal zumbi: {velocity_ratio:.1f}x acima do tempo esperado"
                )

        return {
            "score_final": score_final,
            "components": {
                "stage": {
                    "score": score_stage,
                    "weight": WEIGHTS["stage"],
                    "weighted": round(score_stage * WEIGHTS["stage"], 2),
                    "detail": stage_detail,
                },
                "expected_value": {
                    "score": round(score_value, 1),
                    "weight": WEIGHTS["expected_value"],
                    "weighted": round(score_value * WEIGHTS["expected_value"], 2),
                    "detail": value_detail,
                },
                "velocity": {
                    "score": score_velocity,
                    "weight": WEIGHTS["velocity"],
                    "weighted": round(score_velocity * WEIGHTS["velocity"], 2),
                    "detail": velocity_detail,
                    "ratio": velocity_ratio,
                    "label": velocity_label,
                },
                "seller_fit": {
                    "score": score_seller_fit,
                    "weight": WEIGHTS["seller_fit"],
                    "weighted": round(score_seller_fit * WEIGHTS["seller_fit"], 2),
                    "detail": seller_fit_detail,
                },
                "account_health": {
                    "score": score_account_health,
                    "weight": WEIGHTS["account_health"],
                    "weighted": round(score_account_health * WEIGHTS["account_health"], 2),
                    "detail": account_health_detail,
                },
            },
            "flags": {
                "is_zombie": is_zombie,
                "is_critical_zombie": is_critical_zombie,
                "zombie_detail": zombie_detail,
            },
        }

    @staticmethod
    def _velocity_detail(
        deal_stage: str,
        days_in_stage,
        velocity_label: str,
        velocity_ratio,
    ) -> str:
        """Gera texto explicativo para o componente velocity."""
        if deal_stage == "Prospecting":
            return "Em Prospecting — sem dados temporais"

        if days_in_stage is None:
            return "Sem dados temporais disponiveis"

        days = int(days_in_stage)
        return f"{days} dias em Engaging ({velocity_label}, referencia: 88 dias)"

    @staticmethod
    def _seller_fit_detail(fit_meta: dict) -> str:
        """Gera texto explicativo para o componente seller fit."""
        reason = fit_meta.get("reason", "")

        if reason in ("sem_setor", "dados_insuficientes", "sem_referencia_time"):
            return "Poucos deals neste setor para avaliar fit"

        if reason == "calculado":
            seller_wr = fit_meta.get("seller_winrate", 0)
            team_wr = fit_meta.get("team_winrate", 0)
            seller_pct = f"{seller_wr * 100:.1f}"
            team_pct = f"{team_wr * 100:.1f}"

            if seller_wr > team_wr:
                return (
                    f"Sua taxa de conversao neste setor ({seller_pct}%) "
                    f"esta acima da media do time ({team_pct}%)"
                )
            else:
                return (
                    f"Sua taxa de conversao neste setor ({seller_pct}%) "
                    f"esta abaixo da media do time ({team_pct}%)"
                )

        return "Poucos deals neste setor para avaliar fit"

    @staticmethod
    def _account_health_detail(health_meta: dict) -> str:
        """Gera texto explicativo para o componente account health."""
        reason = health_meta.get("reason", "")

        if reason in ("sem_conta", "dados_insuficientes"):
            return "Pouco historico desta conta"

        if reason == "calculado":
            winrate = health_meta.get("winrate", 0)
            total = health_meta.get("total_deals", 0)
            losses = health_meta.get("losses", 0)
            wr_pct = f"{winrate * 100:.0f}"

            if winrate >= 0.65:
                return f"Conta com bom historico ({wr_pct}% de conversao em {total} negociacoes)"
            elif winrate < 0.40:
                return (
                    f"Conta com historico desfavoravel "
                    f"({wr_pct}% de conversao, {losses} perdidos)"
                )
            else:
                return f"Conta com historico ({wr_pct}% de conversao em {total} negociacoes)"

        return "Pouco historico desta conta"
