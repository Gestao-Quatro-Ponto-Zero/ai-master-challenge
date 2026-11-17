"""
scoring_engine.py - Motor de Scoring e Priorização de Oportunidades (Lead Scorer)
Case 003 G4 AI Master — Vitor Veloso
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

def load_and_prepare_data(data_dir: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Carrega as 4 tabelas do CRM, corrige divergências de nomenclatura e
    calcula benchmarks históricos (win rates de contas, vendedores, produtos, ciclo médio).
    """
    accounts = pd.read_csv(data_dir / "accounts.csv")
    products = pd.read_csv(data_dir / "products.csv")
    teams = pd.read_csv(data_dir / "sales_teams.csv")
    pipeline = pd.read_csv(data_dir / "sales_pipeline.csv")

    # Correção de nomenclatura: 'GTXPro' no pipeline corresponde a 'GTX Pro' no catálogo de produtos
    pipeline['product_clean'] = pipeline['product'].replace({'GTXPro': 'GTX Pro'})

    # Merge das tabelas
    df = pipeline.merge(products.rename(columns={'product': 'product_clean'}), on='product_clean', how='left')
    df = df.merge(accounts, on='account', how='left')
    df = df.merge(teams, on='sales_agent', how='left')

    # Benchmark histórico de deals fechados (Won vs Lost)
    closed = df[df['deal_stage'].isin(['Won', 'Lost'])].copy()
    closed['is_won'] = (closed['deal_stage'] == 'Won').astype(int)
    closed['engage_dt'] = pd.to_datetime(closed['engage_date'])
    closed['close_dt'] = pd.to_datetime(closed['close_date'])
    closed['cycle_days'] = (closed['close_dt'] - closed['engage_dt']).dt.days

    overall_win_rate = float(closed['is_won'].mean())

    # Taxa de conversão por vendedor
    agent_wr = closed.groupby('sales_agent')['is_won'].agg(['count', 'mean']).to_dict('index')

    # Taxa de conversão por conta
    account_wr = closed.dropna(subset=['account']).groupby('account')['is_won'].agg(['count', 'mean']).to_dict('index')

    # Taxa de conversão por produto
    product_wr = closed.groupby('product_clean')['is_won'].agg(['count', 'mean']).to_dict('index')

    benchmarks = {
        'overall_win_rate': overall_win_rate,
        'agent_win_rate': agent_wr,
        'account_win_rate': account_wr,
        'product_win_rate': product_wr,
        'avg_won_cycle_days': float(closed[closed['is_won'] == 1]['cycle_days'].mean()),
        'median_won_cycle_days': float(closed[closed['is_won'] == 1]['cycle_days'].median())
    }

    return df, benchmarks

def score_opportunity(row: pd.Series, benchmarks: Dict[str, Any], ref_date_str: str = "2017-12-31") -> Dict[str, Any]:
    """
    Calcula o score de 0 a 100 de uma oportunidade ativa, acompanhado de:
    - Tier de prioridade (Alta / Média / Baixa / Em Risco)
    - Decomposição pontuada por pilar (Explainability quantitativa)
    - Justificativa textual clara (Explainability qualitativa para o vendedor)
    - Recomendação acionável de próximo passo
    - Valor esperado ponderado (Expected Value = Score% * Valor)
    """
    ref_date = pd.to_datetime(ref_date_str)
    reasons_positive = []
    reasons_negative = []
    alerts = []

    # 1. Pilar Estágio do Funil (Peso máximo: 25 pts)
    stage = row['deal_stage']
    if stage == 'Engaging':
        stage_pts = 25
        reasons_positive.append("Em negociação ativa (Engaging) [+25 pts]")
    elif stage == 'Prospecting':
        stage_pts = 10
        reasons_positive.append("Em prospecção inicial (Prospecting) [+10 pts]")
    else:
        stage_pts = 0

    # 2. Pilar Ajuste por Recorrência / Frescor / Tempo de Pipeline (Peso: -25 a +20 pts)
    # Deals recentes têm muito mais tração; deals parados há >90 dias têm alto risco de estagnação.
    if pd.notnull(row['engage_date']):
        engage_dt = pd.to_datetime(row['engage_date'])
        days_in_pipeline = (ref_date - engage_dt).days
    else:
        days_in_pipeline = 0

    if days_in_pipeline <= 20:
        time_pts = 20
        reasons_positive.append(f"Deal fresco e de alta tração ({days_in_pipeline} dias) [+20 pts]")
    elif days_in_pipeline <= 45:
        time_pts = 15
        reasons_positive.append(f"Tempo de maturação ideal ({days_in_pipeline} dias) [+15 pts]")
    elif days_in_pipeline <= 75:
        time_pts = 5
        reasons_positive.append(f"Tempo de ciclo moderado ({days_in_pipeline} dias) [+5 pts]")
    elif days_in_pipeline <= 120:
        time_pts = -10
        reasons_negative.append(f"Alerta de lentidão: {days_in_pipeline} dias sem fechamento [-10 pts]")
        alerts.append("Deal esfriando (>75 dias)")
    else:
        time_pts = -25
        reasons_negative.append(f"Crítico: deal estagnado há {days_in_pipeline} dias [-25 pts]")
        alerts.append("Crítico: risco iminente de perda por inatividade (>120 dias)")

    # 3. Pilar Perfil e Fit da Conta (Peso: 0 a 20 pts)
    account = row['account']
    account_pts = 0
    if pd.isnull(account):
        account_pts = 5
        reasons_negative.append("Lead sem conta associada no CRM (prospect frio/incompleto) [5 pts]")
        alerts.append("Cadastro incompleto (sem conta)")
    else:
        account_pts = 10  # Base por ser conta cadastrada
        reasons_positive.append(f"Conta corporativa mapeada: {account} [+10 pts]")
        # Histórico da conta
        acct_stat = benchmarks['account_win_rate'].get(account)
        if acct_stat and acct_stat['count'] >= 5:
            if acct_stat['mean'] >= 0.68:
                account_pts += 10
                reasons_positive.append(f"Cliente com altíssima taxa de conversão histórica ({acct_stat['mean']*100:.0f}%) [+10 pts]")
            elif acct_stat['mean'] >= 0.60:
                account_pts += 5
                reasons_positive.append(f"Cliente com boa conversão histórica ({acct_stat['mean']*100:.0f}%) [+5 pts]")
            else:
                account_pts -= 3
                reasons_negative.append(f"Histórico difícil com a conta ({acct_stat['mean']*100:.0f}% win rate) [-3 pts]")

    # 4. Pilar Potencial de Receita e Produto (Peso: 0 a 20 pts)
    sales_price = row['sales_price'] if pd.notnull(row['sales_price']) else 0
    product = row['product_clean']
    value_pts = 0

    if sales_price >= 10000:
        value_pts = 20
        reasons_positive.append(f"Ticket Enterprise/Estratégico (${sales_price:,.0f}) [+20 pts]")
    elif sales_price >= 3000:
        value_pts = 15
        reasons_positive.append(f"Ticket Alto (${sales_price:,.0f} - {product}) [+15 pts]")
    elif sales_price >= 500:
        value_pts = 10
        reasons_positive.append(f"Ticket Médio (${sales_price:,.0f}) [+10 pts]")
    else:
        value_pts = 5
        reasons_negative.append(f"Ticket Baixo (${sales_price:,.0f} - {product}) [+5 pts]")

    # 5. Pilar Desempenho do Vendedor (Peso: 0 a 15 pts)
    agent = row['sales_agent']
    agent_stat = benchmarks['agent_win_rate'].get(agent)
    agent_pts = 10  # Base padrão
    if agent_stat:
        if agent_stat['mean'] >= 0.66:
            agent_pts = 15
            reasons_positive.append(f"Vendedor com histórico acima da média ({agent_stat['mean']*100:.0f}% win rate) [+15 pts]")
        elif agent_stat['mean'] <= 0.58:
            agent_pts = 6
            reasons_negative.append(f"Vendedor com desafio de conversão ({agent_stat['mean']*100:.0f}% win rate) [+6 pts]")

    # Cálculo final do Score bruto (limitado rigorosamente entre 1 e 99)
    raw_score = stage_pts + time_pts + account_pts + value_pts + agent_pts
    final_score = int(np.clip(raw_score, 1, 99))

    # Classificação em Tiers
    if days_in_pipeline > 90 and final_score < 50:
        tier = "Em Risco"
    elif final_score >= 75:
        tier = "Prioridade Alta"
    elif final_score >= 50:
        tier = "Prioridade Média"
    else:
        tier = "Prioridade Baixa"

    # Recomendação de Ação Acionável (Próximo Passo)
    if tier == "Prioridade Alta":
        action = f"Agendar call de fechamento imediatamente; alinhar proposta técnica de {product}."
    elif tier == "Em Risco":
        action = f"Realizar diagnóstico de destravamento ou desqualificar para evitar desperdício de tempo."
    elif stage == "Prospecting":
        action = f"Qualificar tomador de decisão e mover para Engaging nos próximos 5 dias."
    elif pd.isnull(account):
        action = f"Identificar e cadastrar a empresa cliente no CRM para habilitar proposta."
    else:
        action = f"Follow-up de rotina para apresentação de ROI e validação de cronograma."

    # Valor esperado (Expected Deal Value)
    expected_value = (final_score / 100.0) * sales_price

    return {
        'score': final_score,
        'tier': tier,
        'days_in_pipeline': days_in_pipeline,
        'expected_value': expected_value,
        'stage_pts': stage_pts,
        'time_pts': time_pts,
        'account_pts': account_pts,
        'value_pts': value_pts,
        'agent_pts': agent_pts,
        'reasons_positive': reasons_positive,
        'reasons_negative': reasons_negative,
        'alerts': alerts,
        'recommended_action': action,
        'explainability_text': " | ".join(reasons_positive + reasons_negative)
    }

def score_pipeline(df: pd.DataFrame, benchmarks: Dict[str, Any], ref_date_str: str = "2017-12-31") -> pd.DataFrame:
    """
    Aplica o algoritmo a todas as oportunidades ativas (ou pipeline completo).
    """
    scores_list = []
    for _, row in df.iterrows():
        sc = score_opportunity(row, benchmarks, ref_date_str)
        scores_list.append(sc)

    scored_meta = pd.DataFrame(scores_list)
    result_df = pd.concat([df.reset_index(drop=True), scored_meta], axis=1)
    return result_df

if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parent / "data"
    print(f"Carregando dados de: {data_dir}")
    df, benchmarks = load_and_prepare_data(data_dir)
    active = df[df['deal_stage'].isin(['Prospecting', 'Engaging'])].copy()
    scored_active = score_pipeline(active, benchmarks)
    print("\nResumo das Oportunidades Ativas Priorizadas:")
    print(scored_active['tier'].value_counts())
    print("\nExemplo das 3 principais oportunidades de Prioridade Alta:")
    top3 = scored_active.sort_values(by='score', ascending=False).head(3)
    for _, r in top3.iterrows():
        print(f"ID: {r['opportunity_id']} | Score: {r['score']} | {r['sales_agent']} | Conta: {r['account']} | Valor: ${r['sales_price']:,.0f}")
        print(f"  Explainability: {r['explainability_text']}")
        print(f"  Ação Recomendada: {r['recommended_action']}\n")
