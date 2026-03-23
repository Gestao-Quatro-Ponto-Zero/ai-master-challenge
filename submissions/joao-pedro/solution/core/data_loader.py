"""
Data Loader - Carregamento de CSVs e Cálculo de Benchmarks

Este módulo:
1. Carrega os 4 CSVs (sales_pipeline, accounts, products, sales_teams)
2. Calcula benchmarks necessários para o scoring engine
3. Prepara lista de deals para processamento

Uso:
    from core.data_loader import load_benchmarks, load_deals
    
    benchmarks = load_benchmarks()
    deals = load_deals()
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Constantes
DATA_DIR = Path(__file__).parent.parent / "data" / "metrics"
SNAPSHOT_DATE = "2017-12-31"  # Data de corte do dataset


def load_raw_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Carrega os 4 CSVs brutos.
    
    Returns:
        Tuple com (pipeline_df, accounts_df, products_df, teams_df)
    """
    print("📊 Carregando CSVs...")
    
    # Sales Pipeline (principal)
    pipeline_df = pd.read_csv(DATA_DIR / "sales_pipeline.csv")
    
    # Contas
    accounts_df = pd.read_csv(DATA_DIR / "accounts.csv")
    
    # Produtos
    products_df = pd.read_csv(DATA_DIR / "products.csv")
    
    # Times de vendas
    teams_df = pd.read_csv(DATA_DIR / "sales_teams.csv")
    
    print(f"   ✓ Pipeline: {len(pipeline_df):,} deals")
    print(f"   ✓ Accounts: {len(accounts_df):,} contas")
    print(f"   ✓ Products: {len(products_df):,} produtos")
    print(f"   ✓ Teams: {len(teams_df):,} vendedores")
    print()
    
    return pipeline_df, accounts_df, products_df, teams_df


def estimate_close_value(deal: pd.Series, pipeline_df: pd.DataFrame, products_df: pd.DataFrame) -> float:
    """
    Estima close_value para deal aberto usando lógica híbrida.
    
    Prioridade (cascata):
    1. Média histórica do VENDEDOR neste PRODUTO (mais preciso)
    2. Média histórica do PRODUTO em geral (médio)
    3. Sales price do catálogo (fallback)
    4. Mediana geral (fallback final)
    
    Args:
        deal: Serie do deal
        pipeline_df: DataFrame completo do pipeline
        products_df: DataFrame de produtos
        
    Returns:
        Valor estimado
    """
    seller = deal['sales_agent']
    product = deal['product']
    
    # Filtrar apenas deals Won (que têm close_value real)
    won_df = pipeline_df[
        (pipeline_df['deal_stage'] == 'Won') & 
        (pipeline_df['close_value'].notna()) &
        (pipeline_df['close_value'] > 0)
    ]
    
    # Nível 1: Média histórica VENDEDOR × PRODUTO
    seller_product_deals = won_df[
        (won_df['sales_agent'] == seller) &
        (won_df['product'] == product)
    ]
    
    if len(seller_product_deals) >= 3:  # Mínimo 3 deals para confiabilidade
        return seller_product_deals['close_value'].mean()
    
    # Nível 2: Média histórica do PRODUTO (todos vendedores)
    product_deals = won_df[won_df['product'] == product]
    
    if len(product_deals) >= 5:  # Mínimo 5 deals
        return product_deals['close_value'].mean()
    
    # Nível 3: Sales price do catálogo
    product_row = products_df[products_df['product'] == product]
    
    if not product_row.empty:
        return float(product_row['sales_price'].iloc[0])
    
    # Nível 4: Mediana geral (fallback final)
    return won_df['close_value'].median()


def preprocess_pipeline(df: pd.DataFrame, products_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Processa o pipeline: converte datas, calcula campos derivados.
    
    Args:
        df: DataFrame do sales_pipeline.csv
        products_df: DataFrame do products.csv (para preencher close_value)
        
    Returns:
        DataFrame processado
    """
    print("🔧 Processando dados do pipeline...")
    
    df = df.copy()
    
    # Converter datas
    df['engage_date'] = pd.to_datetime(df['engage_date'], errors='coerce')
    df['close_date'] = pd.to_datetime(df['close_date'], errors='coerce')
    
    # Data de snapshot
    snapshot_date = pd.to_datetime(SNAPSHOT_DATE)
    
    # Calcular dias no pipeline
    df['days_in_pipeline'] = df.apply(
        lambda row: (
            (pd.to_datetime(row['close_date']) - pd.to_datetime(row['engage_date'])).days
            if pd.notna(row['close_date']) and row['deal_stage'] in ['Won', 'Lost']
            else (snapshot_date - pd.to_datetime(row['engage_date'])).days
            if pd.notna(row['engage_date']) and row['deal_stage'] == 'Engaging'
            else None
        ),
        axis=1
    )
    
    # Limpar valores negativos (dados inconsistentes)
    df.loc[df['days_in_pipeline'] < 0, 'days_in_pipeline'] = 0
    
    # PREENCHER close_value vazio com estimativa HÍBRIDA
    if products_df is not None:
        deals_corrigidos = 0
        
        for idx, row in df.iterrows():
            if pd.isna(row['close_value']) or row['close_value'] == 0:
                estimated_value = estimate_close_value(row, df, products_df)
                df.at[idx, 'close_value'] = estimated_value
                deals_corrigidos += 1
        
        print(f"   ✓ close_value estimado para {deals_corrigidos} deals abertos")
        print(f"     → Usando lógica híbrida: vendedor×produto → produto → catálogo")
    
    print(f"   ✓ Datas convertidas")
    print(f"   ✓ days_in_pipeline calculado")
    print()
    
    return df


def calculate_win_rates(df: pd.DataFrame) -> Dict:
    """
    Calcula win rates em várias dimensões.
    
    Args:
        df: DataFrame processado do pipeline
        
    Returns:
        Dict com win rates por dimensão
    """
    print("📈 Calculando win rates...")
    
    # Filtrar apenas deals fechados (Won ou Lost)
    closed_df = df[df['deal_stage'].isin(['Won', 'Lost'])].copy()
    
    # Global
    global_wr = (closed_df['deal_stage'] == 'Won').mean() * 100
    
    # Por vendedor
    seller_wr = closed_df.groupby('sales_agent').apply(
        lambda x: (x['deal_stage'] == 'Won').mean() * 100
    ).to_dict()
    
    # Por produto
    product_wr = closed_df.groupby('product').apply(
        lambda x: (x['deal_stage'] == 'Won').mean() * 100
    ).to_dict()
    
    # Por conta (mínimo 3 deals para ser confiável)
    account_counts = closed_df['account'].value_counts()
    reliable_accounts = account_counts[account_counts >= 3].index
    
    account_wr = closed_df[closed_df['account'].isin(reliable_accounts)].groupby('account').apply(
        lambda x: (x['deal_stage'] == 'Won').mean() * 100
    ).to_dict()
    
    print(f"   ✓ Win rate global: {global_wr:.2f}%")
    print(f"   ✓ Win rates por vendedor: {len(seller_wr)} vendedores")
    print(f"   ✓ Win rates por produto: {len(product_wr)} produtos")
    print(f"   ✓ Win rates por conta: {len(account_wr)} contas (≥3 deals)")
    print()
    
    return {
        'global': global_wr,
        'seller': seller_wr,
        'product': product_wr,
        'account': account_wr
    }


def calculate_region_win_rates(pipeline_df: pd.DataFrame, teams_df: pd.DataFrame) -> Dict:
    """
    Calcula win rates por região.
    
    Args:
        pipeline_df: DataFrame do pipeline
        teams_df: DataFrame dos times
        
    Returns:
        Dict com win rates por região
    """
    # Merge com teams para pegar regional_office
    merged = pipeline_df.merge(teams_df[['sales_agent', 'regional_office']], on='sales_agent', how='left')
    
    # Filtrar fechados
    closed = merged[merged['deal_stage'].isin(['Won', 'Lost'])]
    
    # Calcular por região
    region_wr = closed.groupby('regional_office').apply(
        lambda x: (x['deal_stage'] == 'Won').mean() * 100
    ).to_dict()
    
    return region_wr


def calculate_time_benchmarks(df: pd.DataFrame, *, verbose: bool = True) -> Dict:
    """
    Calcula medianas e médias de tempo por cohort.

    Args:
        df: DataFrame processado do pipeline
        verbose: Se True, imprime resumo (desligar em chamadas repetidas da API)

    Returns:
        Dict com benchmarks de tempo
    """
    if verbose:
        print("⏱️ Calculando benchmarks de tempo...")

    # Won
    won_df = df[df['deal_stage'] == 'Won']
    won_median = won_df['days_in_pipeline'].median()
    won_mean = won_df['days_in_pipeline'].mean()

    # Lost
    lost_df = df[df['deal_stage'] == 'Lost']
    lost_median = lost_df['days_in_pipeline'].median()
    lost_mean = lost_df['days_in_pipeline'].mean()

    # Engaging (ainda aberto)
    engaging_df = df[df['deal_stage'] == 'Engaging']
    engaging_median = engaging_df['days_in_pipeline'].median()
    engaging_mean = engaging_df['days_in_pipeline'].mean()

    if verbose:
        print(f"   ✓ Won: mediana {won_median:.0f}d, média {won_mean:.0f}d")
        print(f"   ✓ Lost: mediana {lost_median:.0f}d, média {lost_mean:.0f}d")
        print(f"   ✓ Engaging: mediana {engaging_median:.0f}d, média {engaging_mean:.0f}d")
        print()
    
    return {
        'won_median': won_median,
        'won_mean': won_mean,
        'lost_median': lost_median,
        'lost_mean': lost_mean,
        'engaging_median': engaging_median,
        'engaging_mean': engaging_mean
    }


def calculate_seller_metrics(df: pd.DataFrame) -> Dict:
    """
    Calcula métricas por vendedor: deals ativos, prospecting, ticket médio.
    
    Args:
        df: DataFrame processado do pipeline
        
    Returns:
        Dict com métricas por vendedor
    """
    print("👤 Calculando métricas por vendedor...")
    
    # Deals ativos (Prospecting + Engaging)
    active_df = df[df['deal_stage'].isin(['Prospecting', 'Engaging'])]
    seller_active_deals = active_df['sales_agent'].value_counts().to_dict()
    
    # Prospecting count
    prospecting_df = df[df['deal_stage'] == 'Prospecting']
    seller_prospecting = prospecting_df['sales_agent'].value_counts().to_dict()
    
    # Ticket médio (deals Won)
    won_df = df[df['deal_stage'] == 'Won']
    seller_avg_ticket = won_df.groupby('sales_agent')['close_value'].mean().to_dict()
    
    # Garantir que todos vendedores estão no dict (com 0 se não tiver)
    all_sellers = df['sales_agent'].unique()
    for seller in all_sellers:
        seller_active_deals.setdefault(seller, 0)
        seller_prospecting.setdefault(seller, 0)
        seller_avg_ticket.setdefault(seller, 0)
    
    print(f"   ✓ Deals ativos por vendedor calculados")
    print(f"   ✓ Prospecting por vendedor calculado")
    print(f"   ✓ Ticket médio por vendedor calculado")
    print()
    
    return {
        'active_deals': seller_active_deals,
        'prospecting': seller_prospecting,
        'avg_ticket': seller_avg_ticket
    }


def calculate_product_seller_specialization(df: pd.DataFrame) -> Dict:
    """
    Detecta especialização produto×vendedor.
    
    Args:
        df: DataFrame processado do pipeline
        
    Returns:
        Dict com win rates de combinações produto×vendedor
    """
    print("🎯 Calculando especialização produto×vendedor...")
    
    # Filtrar fechados
    closed_df = df[df['deal_stage'].isin(['Won', 'Lost'])]
    
    # Agrupar por (produto, vendedor)
    combo_wr = {}
    
    for (product, seller), group in closed_df.groupby(['product', 'sales_agent']):
        if len(group) >= 3:  # Mínimo 3 deals para confiabilidade
            wr = (group['deal_stage'] == 'Won').mean() * 100
            combo_key = f"{product}|{seller}"
            combo_wr[combo_key] = wr
    
    print(f"   ✓ {len(combo_wr)} combinações produto×vendedor detectadas")
    print()
    
    return combo_wr


def calculate_seller_qualitative_metrics(pipeline_df: pd.DataFrame, accounts_df: pd.DataFrame) -> Dict:
    """
    Calcula métricas qualitativas por vendedor:
    - Win rate por (vendedor × setor)
    - Ciclo médio de fechamento por (vendedor × produto)

    Args:
        pipeline_df: DataFrame processado do pipeline
        accounts_df: DataFrame de contas (com coluna 'sector')

    Returns:
        Dict com seller_sector_wr, seller_product_cycle e account_sector
    """
    print("🎯 Calculando métricas qualitativas por vendedor...")

    # Join pipeline com accounts para obter setor
    merged = pipeline_df.merge(accounts_df[['account', 'sector']], on='account', how='left')
    closed = merged[merged['deal_stage'].isin(['Won', 'Lost'])]

    # Win rate por (vendedor × setor) — mínimo 3 deals para confiabilidade
    seller_sector_wr = {}
    for (seller, sector), group in closed.groupby(['sales_agent', 'sector']):
        if pd.isna(sector):
            continue
        if len(group) >= 3:
            wr = (group['deal_stage'] == 'Won').mean() * 100
            seller_sector_wr[f"{seller}|{sector}"] = round(wr, 1)

    # Ciclo médio por (vendedor × produto) — apenas Won, mínimo 3 deals
    won = pipeline_df[
        (pipeline_df['deal_stage'] == 'Won') &
        pipeline_df['days_in_pipeline'].notna()
    ]
    seller_product_cycle = {}
    for (seller, product), group in won.groupby(['sales_agent', 'product']):
        if len(group) >= 3:
            avg_cycle = group['days_in_pipeline'].mean()
            seller_product_cycle[f"{product}|{seller}"] = round(avg_cycle, 0)

    # Mapeamento account → sector para lookup rápido no scoring engine
    account_sector = accounts_df.set_index('account')['sector'].dropna().to_dict()

    print(f"   ✓ Win rate por vendedor×setor: {len(seller_sector_wr)} combinações")
    print(f"   ✓ Ciclo médio por vendedor×produto: {len(seller_product_cycle)} combinações")
    print(f"   ✓ Mapeamento account→setor: {len(account_sector)} contas")
    print()

    return {
        'seller_sector_wr': seller_sector_wr,
        'seller_product_cycle': seller_product_cycle,
        'account_sector': account_sector,
    }


def calculate_top_accounts(df: pd.DataFrame) -> List[str]:
    """
    Identifica top 20 contas por volume de deals.
    
    Args:
        df: DataFrame processado do pipeline
        
    Returns:
        Lista com nomes das top 20 contas
    """
    top_20 = df['account'].value_counts().head(20).index.tolist()
    return top_20


def calculate_value_distribution(df: pd.DataFrame) -> List[float]:
    """
    Retorna distribuição de valores (para cálculo de percentil).
    
    Args:
        df: DataFrame processado do pipeline
        
    Returns:
        Lista ordenada de close_values
    """
    values = df['close_value'].dropna().tolist()
    return sorted(values)


def load_benchmarks() -> Dict:
    """
    Carrega dados e calcula todos os benchmarks necessários.
    
    Returns:
        Dict com todos os benchmarks para scoring
    """
    print("=" * 60)
    print("CARREGANDO BENCHMARKS")
    print("=" * 60)
    print()
    
    # 1. Carregar CSVs
    pipeline_df, accounts_df, products_df, teams_df = load_raw_data()
    
    # 2. Preprocessar pipeline (passar products_df para preencher close_value)
    pipeline_df = preprocess_pipeline(pipeline_df, products_df)
    
    # 3. Calcular win rates
    win_rates = calculate_win_rates(pipeline_df)
    
    # 4. Win rates por região
    region_wr = calculate_region_win_rates(pipeline_df, teams_df)
    
    # 5. Benchmarks de tempo
    time_benchmarks = calculate_time_benchmarks(pipeline_df)
    
    # 6. Métricas por vendedor
    seller_metrics = calculate_seller_metrics(pipeline_df)
    
    # 7. Especialização produto×vendedor
    product_seller_wr = calculate_product_seller_specialization(pipeline_df)

    # 8. Top 20 contas
    top_20_accounts = calculate_top_accounts(pipeline_df)

    # 9. Distribuição de valores
    value_distribution = calculate_value_distribution(pipeline_df)

    # 10. Métricas qualitativas por vendedor
    qualitative = calculate_seller_qualitative_metrics(pipeline_df, accounts_df)

    # Consolidar tudo
    benchmarks = {
        # Win Rates
        'global_wr': win_rates['global'],
        'seller_wr': win_rates['seller'],
        'product_wr': win_rates['product'],
        'account_wr': win_rates['account'],
        'region_wr': region_wr,

        # Tempo
        'won_median': time_benchmarks['won_median'],
        'won_mean': time_benchmarks['won_mean'],
        'lost_median': time_benchmarks['lost_median'],
        'lost_mean': time_benchmarks['lost_mean'],
        'engaging_median': time_benchmarks['engaging_median'],
        'engaging_mean': time_benchmarks['engaging_mean'],

        # Vendedor
        'seller_active_deals': seller_metrics['active_deals'],
        'seller_prospecting': seller_metrics['prospecting'],
        'seller_avg_ticket': seller_metrics['avg_ticket'],

        # Especialização
        'product_seller_wr': product_seller_wr,

        # Qualitativo
        'seller_sector_wr': qualitative['seller_sector_wr'],
        'seller_product_cycle': qualitative['seller_product_cycle'],
        'account_sector': qualitative['account_sector'],

        # Contas
        'top_20_accounts': top_20_accounts,

        # Valores
        'value_distribution': value_distribution,

        # Metadata
        'snapshot_date': SNAPSHOT_DATE,
        'total_deals': len(pipeline_df)
    }
    
    print("=" * 60)
    print("✅ BENCHMARKS CARREGADOS COM SUCESSO")
    print("=" * 60)
    print()
    
    return benchmarks


def load_deals(deal_stage: str = None) -> List[Dict]:
    """
    Carrega lista de deals para scoring.
    
    Args:
        deal_stage: Filtrar por estágio (None = todos, "Engaging" = só abertos)
        
    Returns:
        Lista de dicts com dados dos deals
    """
    print("📋 Carregando deals para scoring...")
    
    # Carregar e processar
    pipeline_df, _, products_df, teams_df = load_raw_data()
    pipeline_df = preprocess_pipeline(pipeline_df, products_df)
    
    # Merge com teams para pegar região
    pipeline_df = pipeline_df.merge(
        teams_df[['sales_agent', 'regional_office']], 
        on='sales_agent', 
        how='left'
    )
    
    # Filtrar por estágio se especificado
    if deal_stage:
        pipeline_df = pipeline_df[pipeline_df['deal_stage'] == deal_stage]
    
    # Converter para lista de dicts
    deals = pipeline_df.to_dict('records')
    
    print(f"   ✓ {len(deals):,} deals carregados")
    print()
    
    return deals


def get_deal_by_id(opportunity_id: str) -> Dict:
    """
    Busca deal específico por ID.
    
    Args:
        opportunity_id: ID da oportunidade
        
    Returns:
        Dict com dados do deal
    """
    deals = load_deals()
    
    for deal in deals:
        if deal['opportunity_id'] == opportunity_id:
            return deal
    
    return None


if __name__ == "__main__":
    # Teste básico
    benchmarks = load_benchmarks()
    
    print("\n📊 RESUMO DOS BENCHMARKS:")
    print(f"Win Rate Global: {benchmarks['global_wr']:.2f}%")
    print(f"Vendedores: {len(benchmarks['seller_wr'])}")
    print(f"Produtos: {len(benchmarks['product_wr'])}")
    print(f"Contas (≥3 deals): {len(benchmarks['account_wr'])}")
    print(f"Won Mediana: {benchmarks['won_median']:.0f} dias")
    print(f"Engaging Mediana: {benchmarks['engaging_median']:.0f} dias")
    print(f"Total de deals: {benchmarks['total_deals']:,}")