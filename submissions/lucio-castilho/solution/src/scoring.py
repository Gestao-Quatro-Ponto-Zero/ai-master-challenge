from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from src.data_loader import validate_data_dir

SNAPSHOT_DATE = pd.Timestamp('2017-12-31')
PRODUCT_FIXES = {'GTXPro': 'GTX Pro'}

ACTION_RANK = {
    'Focus Now': 1,
    'Review Now': 2,
    'Follow Up': 3,
    'Re-engage': 4,
    'Requalify': 5,
    'Qualify or Drop': 6,
    'High-Potential Prospect': 7,
    'Prioritize Qualification': 8,
    'Qualify': 9,
    'Monitor': 10,
    'Keep Warm': 11,
    'Low-Priority Qualification': 12,
    'Low Priority': 13,
}


@dataclass(frozen=True)
class FitEvidence:
    product_rate: float
    seller_product_rate: float
    product_sector_rate: float | None
    product_n: int
    seller_product_n: int
    product_sector_n: int


def _smoothed_rate(wins: int, n: int, global_rate: float, prior_strength: int) -> float:
    return (wins + prior_strength * global_rate) / (n + prior_strength)


def _fit_score_from_relative(relative_fit: float) -> float:
    x = np.array([0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15])
    y = np.array([0, 20, 35, 50, 65, 80, 100])
    return float(np.clip(np.interp(relative_fit, x, y), 0, 100))


def _fit_category(score: float) -> str:
    if score < 35:
        return 'Baixa Aderência Histórica'
    if score < 45:
        return 'Abaixo da Média'
    if score <= 55:
        return 'Típica'
    if score < 70:
        return 'Acima da Média'
    return 'Alta Aderência Histórica'


def _confidence(seller_product_n: int, product_sector_n: int, has_account_context: bool) -> str:
    if seller_product_n < 15:
        return 'Limited'
    if has_account_context and seller_product_n >= 30 and product_sector_n >= 30:
        return 'High'
    return 'Medium'


def load_data(data_dir: str | Path) -> Dict[str, pd.DataFrame]:
    data_dir = validate_data_dir(data_dir)
    accounts = pd.read_csv(data_dir / 'accounts.csv')
    products = pd.read_csv(data_dir / 'products.csv')
    teams = pd.read_csv(data_dir / 'sales_teams.csv')
    pipeline = pd.read_csv(data_dir / 'sales_pipeline.csv')

    pipeline['product'] = pipeline['product'].replace(PRODUCT_FIXES)
    pipeline['engage_date'] = pd.to_datetime(pipeline['engage_date'], errors='coerce')
    pipeline['close_date'] = pd.to_datetime(pipeline['close_date'], errors='coerce')
    accounts['sector'] = accounts['sector'].replace({'technolgy': 'technology'})

    enriched = (
        pipeline
        .merge(products, on='product', how='left', validate='many_to_one')
        .merge(teams, on='sales_agent', how='left', validate='many_to_one')
        .merge(accounts, on='account', how='left', validate='many_to_one')
    )
    return {
        'accounts': accounts,
        'products': products,
        'teams': teams,
        'pipeline': pipeline,
        'enriched': enriched,
    }


def build_historical_reference(enriched: pd.DataFrame) -> dict:
    closed = enriched[enriched['deal_stage'].isin(['Won', 'Lost'])].copy()
    closed['won'] = (closed['deal_stage'] == 'Won').astype(int)
    global_rate = float(closed['won'].mean())

    product_stats = closed.groupby('product')['won'].agg(['sum', 'count'])
    seller_product_stats = closed.groupby(['sales_agent', 'product'])['won'].agg(['sum', 'count'])
    product_sector_stats = closed.dropna(subset=['sector']).groupby(['product', 'sector'])['won'].agg(['sum', 'count'])

    # Historical cycle duration is only used to contextualize open Engaging deals.
    closed_with_dates = closed.dropna(subset=['engage_date', 'close_date']).copy()
    closed_with_dates['cycle_days'] = (closed_with_dates['close_date'] - closed_with_dates['engage_date']).dt.days.clip(lower=0)
    global_cycles = np.sort(closed_with_dates['cycle_days'].to_numpy())

    product_cycles = {
        key: np.sort(group['cycle_days'].to_numpy())
        for key, group in closed_with_dates.groupby('product')
    }
    product_sector_cycles = {
        key: np.sort(group['cycle_days'].to_numpy())
        for key, group in closed_with_dates.dropna(subset=['sector']).groupby(['product', 'sector'])
    }

    return {
        'global_rate': global_rate,
        'product_stats': product_stats,
        'seller_product_stats': seller_product_stats,
        'product_sector_stats': product_sector_stats,
        'global_cycles': global_cycles,
        'product_cycles': product_cycles,
        'product_sector_cycles': product_sector_cycles,
    }


def _group_smoothed_rate(stats: pd.DataFrame, key, global_rate: float, prior: int) -> Tuple[float, int]:
    try:
        row = stats.loc[key]
        return _smoothed_rate(int(row['sum']), int(row['count']), global_rate, prior), int(row['count'])
    except KeyError:
        return global_rate, 0


def compute_historical_fit(row: pd.Series, ref: dict) -> tuple[float, str, str, FitEvidence]:
    global_rate = ref['global_rate']
    product_rate, product_n = _group_smoothed_rate(ref['product_stats'], row['product'], global_rate, 100)
    seller_product_rate, seller_product_n = _group_smoothed_rate(
        ref['seller_product_stats'], (row['sales_agent'], row['product']), global_rate, 30
    )

    has_sector = pd.notna(row.get('sector'))
    if has_sector:
        product_sector_rate, product_sector_n = _group_smoothed_rate(
            ref['product_sector_stats'], (row['product'], row['sector']), global_rate, 30
        )
        relative = (
            0.50 * seller_product_rate / global_rate
            + 0.35 * product_sector_rate / global_rate
            + 0.15 * product_rate / global_rate
        )
    else:
        product_sector_rate, product_sector_n = None, 0
        relative = 0.70 * seller_product_rate / global_rate + 0.30 * product_rate / global_rate

    score = round(_fit_score_from_relative(relative), 1)
    category = _fit_category(score)
    confidence = _confidence(seller_product_n, product_sector_n, has_sector)
    evidence = FitEvidence(
        product_rate=product_rate,
        seller_product_rate=seller_product_rate,
        product_sector_rate=product_sector_rate,
        product_n=product_n,
        seller_product_n=seller_product_n,
        product_sector_n=product_sector_n,
    )
    return score, category, confidence, evidence


def _percentile_rank(value: float, reference: np.ndarray) -> float:
    if len(reference) == 0:
        return np.nan
    return float(np.searchsorted(reference, value, side='right') / len(reference) * 100)


def compute_attention(row: pd.Series, ref: dict) -> tuple[float | None, str, float | None]:
    if row['deal_stage'] != 'Engaging' or pd.isna(row['engage_date']):
        return None, 'Prazo indisponível', None

    age_days = max(int((SNAPSHOT_DATE - row['engage_date']).days), 0)
    reference = None
    if pd.notna(row.get('sector')):
        candidate = ref['product_sector_cycles'].get((row['product'], row['sector']))
        if candidate is not None and len(candidate) >= 30:
            reference = candidate
    if reference is None:
        candidate = ref['product_cycles'].get(row['product'])
        if candidate is not None and len(candidate) >= 30:
            reference = candidate
    if reference is None:
        reference = ref['global_cycles']

    percentile = _percentile_rank(age_days, reference)
    if percentile < 50:
        return 20.0, 'Normal', percentile
    if percentile < 75:
        return 40.0, 'Watch', percentile
    if percentile < 90:
        return 70.0, 'Needs Attention', percentile
    if percentile < 95:
        return 100.0, 'Urgent Review', percentile
    return 60.0, 'Stale', percentile


def action_category(stage: str, fit_score: float, attention_state: str) -> str:
    if stage == 'Prospecting':
        if fit_score >= 70:
            return 'High-Potential Prospect'
        if fit_score >= 56:
            return 'Prioritize Qualification'
        if fit_score >= 45:
            return 'Qualify'
        return 'Low-Priority Qualification'

    if stage != 'Engaging':
        return 'Low Priority'

    if fit_score >= 70:
        fit_band = 'strong'
    elif fit_score >= 56:
        fit_band = 'positive'
    elif fit_score >= 45:
        fit_band = 'typical'
    else:
        fit_band = 'weak'

    matrix = {
        'Normal': {
            'strong': 'Keep Warm', 'positive': 'Keep Warm', 'typical': 'Monitor', 'weak': 'Low Priority'
        },
        'Watch': {
            'strong': 'Monitor', 'positive': 'Monitor', 'typical': 'Monitor', 'weak': 'Low Priority'
        },
        'Needs Attention': {
            'strong': 'Focus Now', 'positive': 'Focus Now', 'typical': 'Follow Up', 'weak': 'Requalify'
        },
        'Urgent Review': {
            'strong': 'Focus Now', 'positive': 'Focus Now', 'typical': 'Review Now', 'weak': 'Requalify'
        },
        'Stale': {
            'strong': 'Re-engage', 'positive': 'Re-engage', 'typical': 'Qualify or Drop', 'weak': 'Qualify or Drop'
        },
    }
    return matrix.get(attention_state, {}).get(fit_band, 'Monitor')


def _explanation_lines(row: pd.Series, ref: dict, evidence: FitEvidence) -> list[str]:
    global_rate = ref['global_rate']
    lines: list[str] = []

    seller_delta = evidence.seller_product_rate / global_rate - 1
    if seller_delta >= 0.03:
        lines.append(f"O histórico do vendedor com o produto está {seller_delta:.0%} acima da referência do portfólio.")
    elif seller_delta <= -0.03:
        lines.append(f"O histórico do vendedor com o produto está {abs(seller_delta):.0%} abaixo da referência do portfólio.")
    else:
        lines.append('O histórico do vendedor com o produto está próximo da referência do portfólio.')

    if evidence.product_sector_rate is not None:
        sector_delta = evidence.product_sector_rate / global_rate - 1
        if sector_delta >= 0.03:
            lines.append(f"O histórico do produto no setor está {sector_delta:.0%} acima da referência do portfólio.")
        elif sector_delta <= -0.03:
            lines.append(f"O histórico do produto no setor está {abs(sector_delta):.0%} abaixo da referência do portfólio.")
        else:
            lines.append('O histórico do produto no setor está próximo da referência do portfólio.')
    else:
        lines.append('O contexto da conta não está disponível; a aderência utiliza apenas as evidências históricas principais.')

    product_delta = evidence.product_rate / global_rate - 1
    if abs(product_delta) >= 0.03:
        direction = 'above' if product_delta > 0 else 'below'
        lines.append(f"O histórico do produto está {abs(product_delta):.0%} {direction} da referência do portfólio.")

    return lines


def recommended_action(action: str) -> str:
    mapping = {
        'Focus Now': 'Faça o acompanhamento agora e confirme um próximo passo concreto.',
        'Review Now': 'Revise a oportunidade hoje e defina se ela deve avançar, ser requalificada ou ser encerrada.',
        'Follow Up': 'Agende um acompanhamento e confirme o próximo marco.',
        'Re-engage': 'Tente uma reativação focada; se não houver resposta, revise o status da oportunidade no pipeline.',
        'Requalify': 'Revalide a necessidade, o momento e o processo de decisão antes de investir mais esforço comercial.',
        'Qualify or Drop': 'Tome uma decisão explícita sobre o pipeline: requalifique com base em evidências ou remova da fila de foco ativo.',
        'Monitor': 'Mantenha a oportunidade visível e revise-a na próxima rodada de revisão do pipeline.',
        'Keep Warm': 'Mantenha o ritmo sem dedicar atenção excessiva.',
        'Low Priority': 'Reduza a prioridade em relação a oportunidades mais promissoras ou urgentes.',
        'High-Potential Prospect': 'Priorize a qualificação inicial com base em um contexto histórico mais favorável.',
        'Prioritize Qualification': 'Avance este prospect para a qualificação antes de prospects com menor aderência.',
        'Qualify': 'Qualifique a oportunidade; a urgência em relação ao prazo não pode ser avaliada com os dados disponíveis.',
        'Low-Priority Qualification': 'Qualifique somente após os prospects de maior prioridade; o contexto histórico é menos favorável.',
    }
    return mapping.get(action, 'Revise a oportunidade e defina a próxima ação concreta.')


def score_open_pipeline(enriched: pd.DataFrame) -> pd.DataFrame:
    ref = build_historical_reference(enriched)
    open_deals = enriched[enriched['deal_stage'].isin(['Prospecting', 'Engaging'])].copy()

    records = []
    for _, row in open_deals.iterrows():
        fit_score, fit_category, confidence, evidence = compute_historical_fit(row, ref)
        attention_score, attention_state, age_percentile = compute_attention(row, ref)
        if row['deal_stage'] == 'Engaging':
            priority_score = round(0.35 * fit_score + 0.65 * float(attention_score), 1)
        else:
            priority_score = fit_score
        action = action_category(row['deal_stage'], fit_score, attention_state)
        explanations = _explanation_lines(row, ref, evidence)
        if row['deal_stage'] == 'Engaging':
            age_days = max(int((SNAPSHOT_DATE - row['engage_date']).days), 0)
            explanations.append(
                f"Esta oportunidade está em negociação há {age_days} dias, aproximadamente no percentil {age_percentile:.0f} dos ciclos históricos comparáveis."
            )
        else:
            age_days = np.nan
            explanations.append('Não há uma data de criação disponível para oportunidades em Prospecção, portanto a urgência em relação ao prazo não é estimada.')

        rec = row.to_dict()
        rec.update({
            'historical_fit': fit_score,
            'fit_category': fit_category,
            'evidence_confidence': confidence,
            'attention_need': attention_score,
            'attention_state': attention_state,
            'age_percentile': age_percentile,
            'days_in_engaging': age_days,
            'priority_score': priority_score,
            'action_category': action,
            'action_rank': ACTION_RANK.get(action, 99),
            'recommended_action': recommended_action(action),
            'explanation_1': explanations[0] if len(explanations) > 0 else '',
            'explanation_2': explanations[1] if len(explanations) > 1 else '',
            'explanation_3': explanations[2] if len(explanations) > 2 else '',
            'explanation_4': explanations[3] if len(explanations) > 3 else '',
        })
        records.append(rec)

    scored = pd.DataFrame(records)
    return scored.sort_values(['action_rank', 'priority_score'], ascending=[True, False]).reset_index(drop=True)


def scoring_summary(scored: pd.DataFrame) -> dict:
    need_decision = {'Requalify', 'Qualify or Drop', 'Re-engage', 'Review Now'}
    return {
        'open_deals': int(len(scored)),
        'focus_now': int((scored['action_category'] == 'Focus Now').sum()),
        'need_decision': int(scored['action_category'].isin(need_decision).sum()),
        'limited_evidence': int((scored['evidence_confidence'] == 'Limited').sum()),
    }
