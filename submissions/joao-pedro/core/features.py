"""
Features - Funções Auxiliares para Scoring

Funções utilitárias para:
- Cálculo de percentis
- Fatores multiplicativos
- Especialização produto×vendedor
- Penalidades
- Utilitários gerais

Uso:
    from core.features import calculate_percentile, get_seller_factor
"""

from typing import List, Dict, Optional


# =============================================================================
# UTILITÁRIOS GERAIS
# =============================================================================

def clamp(value: float, min_val: float = 0, max_val: float = 100) -> float:
    """
    Limita valor entre min e max.
    
    Args:
        value: Valor a limitar
        min_val: Mínimo (default 0)
        max_val: Máximo (default 100)
        
    Returns:
        Valor limitado
    """
    return max(min_val, min(max_val, value))


def safe_divide(numerator: float, denominator: float, default: float = 1.0) -> float:
    """
    Divisão segura (evita divisão por zero).
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor se denominador = 0
        
    Returns:
        Resultado da divisão ou default
    """
    if denominator == 0:
        return default
    return numerator / denominator


# =============================================================================
# CÁLCULO DE PERCENTIL
# =============================================================================

def calculate_percentile(value: float, distribution: List[float]) -> float:
    """
    Calcula percentil de um valor em uma distribuição.
    
    Args:
        value: Valor a calcular percentil
        distribution: Lista ordenada de valores
        
    Returns:
        Percentil (0-100)
        
    Example:
        >>> dist = [100, 200, 300, 400, 500]
        >>> calculate_percentile(300, dist)
        60.0  # 300 está no 60º percentil
    """
    if not distribution:
        return 50.0  # Default: meio
    
    # Contar quantos valores são menores ou iguais
    count_below = sum(1 for v in distribution if v <= value)
    
    # Percentil = (posição / total) * 100
    percentile = (count_below / len(distribution)) * 100
    
    return clamp(percentile, 0, 100)


# =============================================================================
# FATORES MULTIPLICATIVOS (PROBABILIDADE)
# =============================================================================

def get_seller_factor(seller: str, benchmarks: Dict, global_wr: float) -> float:
    """
    Fator de probabilidade baseado no win rate do vendedor.
    
    Args:
        seller: Nome do vendedor
        benchmarks: Dict de benchmarks
        global_wr: Win rate global
        
    Returns:
        Fator multiplicativo (ex: 1.11 para vendedor acima da média)
    """
    seller_wr = benchmarks['seller_wr'].get(seller, global_wr)
    return safe_divide(seller_wr, global_wr, 1.0)


def get_product_factor(product: str, benchmarks: Dict, global_wr: float) -> float:
    """
    Fator de probabilidade baseado no win rate do produto.
    
    Args:
        product: Nome do produto
        benchmarks: Dict de benchmarks
        global_wr: Win rate global
        
    Returns:
        Fator multiplicativo
    """
    product_wr = benchmarks['product_wr'].get(product, global_wr)
    return safe_divide(product_wr, global_wr, 1.0)


def get_account_factor(account: str, benchmarks: Dict, global_wr: float) -> float:
    """
    Fator de probabilidade baseado no histórico da conta.
    
    Args:
        account: Nome da conta
        benchmarks: Dict de benchmarks
        global_wr: Win rate global
        
    Returns:
        Fator multiplicativo (1.0 se conta não tem histórico)
    """
    if account not in benchmarks['account_wr']:
        return 1.0  # Neutro (conta nova)
    
    account_wr = benchmarks['account_wr'][account]
    return safe_divide(account_wr, global_wr, 1.0)


def get_region_factor(region: str, benchmarks: Dict, global_wr: float) -> float:
    """
    Fator de probabilidade baseado na região.
    
    Args:
        region: Nome da região (West, East, Central)
        benchmarks: Dict de benchmarks
        global_wr: Win rate global
        
    Returns:
        Fator multiplicativo
    """
    region_wr = benchmarks['region_wr'].get(region, global_wr)
    return safe_divide(region_wr, global_wr, 1.0)


def get_specialist_factor(seller: str, product: str, benchmarks: Dict) -> float:
    """
    Detecta se vendedor é especialista (ou mismatch) neste produto.
    
    Baseado em dados reais:
    - Rosalina em GTK 500: 83.3% vs 65.5% geral = +17.8 pts → Especialista
    - Garret em GTX Basic: 51.6% vs 61.0% geral = -9.4 pts → Mismatch
    
    Args:
        seller: Nome do vendedor
        product: Nome do produto
        benchmarks: Dict de benchmarks
        
    Returns:
        1.15 (especialista), 0.85 (mismatch), 1.0 (neutro)
    """
    combo_key = f"{product}|{seller}"
    
    # Verificar se temos dados dessa combinação (≥3 deals)
    if combo_key not in benchmarks['product_seller_wr']:
        return 1.0  # Neutro (sem dados suficientes)
    
    combo_wr = benchmarks['product_seller_wr'][combo_key]
    seller_avg_wr = benchmarks['seller_wr'].get(seller, benchmarks['global_wr'])
    
    # Delta
    delta = combo_wr - seller_avg_wr
    
    # Classificar
    if delta > 5:
        return 1.15  # Especialista (+15%)
    elif delta < -10:
        return 0.85  # Mismatch (-15%)
    else:
        return 1.0   # Neutro


# =============================================================================
# PENALIDADES (PROBABILIDADE)
# =============================================================================

def get_time_penalty(days_in_pipeline: int, lost_median: float, won_median: float) -> float:
    """
    Penalidade por tempo excessivo.
    
    Deal que ultrapassou MUITO o tempo típico de Lost tem prob reduzida.
    
    Args:
        days_in_pipeline: Dias no pipeline
        lost_median: Mediana de Lost
        won_median: Mediana de Won
        
    Returns:
        Fator de penalidade (0.75, 0.90, ou 1.0)
    """
    if days_in_pipeline > 2.5 * lost_median:  # > 35 dias (se lost_median=14)
        return 0.75  # -25% probabilidade
    elif days_in_pipeline > 1.5 * won_median:  # > 85.5 dias (se won_median=57)
        return 0.90  # -10% probabilidade
    else:
        return 1.0   # Sem penalidade


def get_oversize_penalty(close_value: float, seller_avg_ticket: float) -> float:
    """
    Penalidade para deal muito maior que experiência do vendedor.
    
    Args:
        close_value: Valor do deal
        seller_avg_ticket: Ticket médio do vendedor
        
    Returns:
        0.90 (deal oversized) ou 1.0 (normal)
    """
    if seller_avg_ticket == 0:
        return 1.0  # Vendedor sem histórico Won
    
    if close_value > 3 * seller_avg_ticket:
        return 0.90  # -10% probabilidade
    else:
        return 1.0   # Sem penalidade


def get_overload_penalty(seller_active_deals: int) -> float:
    """
    Penalidade por sobrecarga do vendedor.
    
    Args:
        seller_active_deals: Deals ativos do vendedor
        
    Returns:
        Fator de penalidade (0.85, 0.92, ou 1.0)
    """
    if seller_active_deals > 150:
        return 0.85  # -15% probabilidade
    elif seller_active_deals > 100:
        return 0.92  # -8% probabilidade
    else:
        return 1.0   # Sem penalidade


# =============================================================================
# MULTIPLICADORES (URGÊNCIA)
# =============================================================================

def get_seller_load_multiplier(seller_active_deals: int) -> float:
    """
    Multiplica urgência se vendedor está sobrecarregado.
    
    Args:
        seller_active_deals: Deals ativos do vendedor
        
    Returns:
        Multiplicador de urgência (1.0, 1.15, ou 1.3)
    """
    if seller_active_deals > 150:
        return 1.3   # +30% urgência
    elif seller_active_deals > 100:
        return 1.15  # +15% urgência
    else:
        return 1.0   # Neutro


def get_account_difficulty_multiplier(account_wr: Optional[float], global_wr: float) -> float:
    """
    Multiplica urgência para conta com histórico ruim.
    
    Args:
        account_wr: Win rate da conta (None se não tem histórico)
        global_wr: Win rate global
        
    Returns:
        1.2 (conta difícil) ou 1.0 (neutro)
    """
    if account_wr is None:
        return 1.0  # Conta sem histórico
    
    if account_wr < 40:
        return 1.2  # +20% urgência
    else:
        return 1.0  # Neutro


def get_oversize_urgency_multiplier(close_value: float, seller_avg_ticket: float) -> float:
    """
    Multiplica urgência para deal oversized (vendedor pode estar intimidado).
    
    Args:
        close_value: Valor do deal
        seller_avg_ticket: Ticket médio do vendedor
        
    Returns:
        1.15 (oversized) ou 1.0 (normal)
    """
    if seller_avg_ticket == 0:
        return 1.0
    
    if close_value > 3 * seller_avg_ticket:
        return 1.15  # +15% urgência
    else:
        return 1.0   # Neutro


# =============================================================================
# AJUSTES DE VALOR
# =============================================================================

def apply_premium_product_bonus(percentile: float, product: str) -> float:
    """
    Aplica bonus para produto premium (GTK 500).
    
    Args:
        percentile: Percentil base do valor
        product: Nome do produto
        
    Returns:
        Percentil ajustado
    """
    if product == 'GTK 500':
        return percentile * 1.20  # +20%
    else:
        return percentile


def apply_strategic_account_bonus(percentile: float, account: str, top_accounts: List[str]) -> float:
    """
    Aplica bonus para conta estratégica (top 20).
    
    Args:
        percentile: Percentil base do valor
        account: Nome da conta
        top_accounts: Lista das top 20 contas
        
    Returns:
        Percentil ajustado
    """
    if account in top_accounts:
        return percentile * 1.15  # +15%
    else:
        return percentile


def apply_probability_discount(percentile: float, probability: float) -> float:
    """
    Desconto de valor baseado em probabilidade baixa.
    
    Valor esperado = Valor × Probabilidade
    
    Args:
        percentile: Percentil base do valor
        probability: Probabilidade calculada (0-100)
        
    Returns:
        Percentil ajustado
    """
    if probability < 40:
        return percentile * 0.70  # -30%
    elif probability < 55:
        return percentile * 0.85  # -15%
    else:
        return percentile  # Sem desconto


# =============================================================================
# FATORES DE VIABILIDADE
# =============================================================================

def get_prospecting_viability_factor(prospecting_count: int) -> float:
    """
    Fator de viabilidade baseado em prospecting do vendedor.
    
    Args:
        prospecting_count: Número de deals em Prospecting
        
    Returns:
        Fator multiplicativo (0.5 a 1.3)
    """
    if prospecting_count == 0:
        return 0.5   # -50% viabilidade (SEM pipeline novo)
    elif prospecting_count < 10:
        return 0.8   # -20% viabilidade
    elif prospecting_count <= 30:
        return 1.0   # Neutro
    else:  # > 30
        return 1.3   # +30% viabilidade (pipeline saudável)


def get_load_viability_factor(active_deals: int) -> float:
    """
    Fator de viabilidade baseado em carga do vendedor.
    
    Args:
        active_deals: Deals ativos (Prospecting + Engaging)
        
    Returns:
        Fator multiplicativo (0.6 a 1.5)
    """
    if active_deals > 150:
        return 0.6   # -40% viabilidade (muito sobrecarregado)
    elif active_deals > 100:
        return 0.8   # -20% viabilidade
    elif active_deals >= 40:
        return 1.0   # Neutro
    elif active_deals > 0:
        return 1.3   # +30% viabilidade (tem tempo)
    else:  # 0 deals
        return 1.5   # +50% viabilidade (totalmente disponível)


def get_specialist_viability_factor(specialist_factor: float) -> float:
    """
    Converte fator de especialização (prob) para viabilidade.
    
    Args:
        specialist_factor: Fator do get_specialist_factor (1.15, 0.85, ou 1.0)
        
    Returns:
        Fator de viabilidade
    """
    if specialist_factor == 1.15:
        return 1.2   # Especialista
    elif specialist_factor == 0.85:
        return 0.8   # Mismatch
    else:
        return 1.0   # Neutro


# =============================================================================
# VALIDAÇÕES
# =============================================================================

def validate_deal(deal: Dict) -> bool:
    """
    Valida se deal tem campos mínimos necessários.
    
    Args:
        deal: Dict do deal
        
    Returns:
        True se válido, False caso contrário
    """
    required_fields = [
        'opportunity_id',
        'sales_agent',
        'product',
        'account',
        'deal_stage',
        'days_in_pipeline',
        'close_value'
    ]
    
    for field in required_fields:
        if field not in deal or deal[field] is None:
            return False
    
    return True


# =============================================================================
# TESTES (se executar módulo diretamente)
# =============================================================================

if __name__ == "__main__":
    print("🧪 Testando funções de features...")
    print()
    
    # Teste percentil
    dist = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    print("Percentil de 550 em [100..1000]:", calculate_percentile(550, dist))
    print("Percentil de 950 em [100..1000]:", calculate_percentile(950, dist))
    print()
    
    # Teste fatores
    print("Fator vendedor (70% vs 63.15% global):", safe_divide(70, 63.15, 1.0))
    print("Fator produto (60% vs 63.15% global):", safe_divide(60, 63.15, 1.0))
    print()
    
    # Teste clamp
    print("Clamp(120, 0, 100):", clamp(120, 0, 100))
    print("Clamp(-10, 0, 100):", clamp(-10, 0, 100))
    print()
    
    print("✅ Testes básicos concluídos!")