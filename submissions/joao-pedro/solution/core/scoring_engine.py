"""
Scoring Engine - Motor Principal de Scoring

Implementação completa do modelo de scoring:
- Urgência (50%): Tempo sem decisão
- Probabilidade (30%): Chance de fechar
- Valor (20%): Importância relativa
- Viabilidade (separada): Capacidade do vendedor
- Ações: Matriz score × viabilidade

Uso:
    from core.data_loader import load_benchmarks, load_deals
    from core.scoring_engine import calculate_score
    
    benchmarks = load_benchmarks()
    deal = load_deals()[0]
    result = calculate_score(deal, benchmarks)
"""

from typing import Dict, List, Optional
from core.features import (
    clamp, calculate_percentile,
    get_seller_factor, get_product_factor, get_account_factor, get_region_factor,
    get_specialist_factor, get_time_penalty, get_oversize_penalty, get_overload_penalty,
    get_seller_load_multiplier, get_account_difficulty_multiplier, get_oversize_urgency_multiplier,
    apply_premium_product_bonus, apply_strategic_account_bonus, apply_probability_discount,
    get_prospecting_viability_factor, get_load_viability_factor, get_specialist_viability_factor,
    validate_deal
)


# =============================================================================
# CONSTANTES
# =============================================================================

# Pesos do score
WEIGHT_URGENCY = 0.50
WEIGHT_PROBABILITY = 0.30
WEIGHT_VALUE = 0.20

# Thresholds de urgência (baseados nas medianas reais)
URGENCY_THRESHOLDS = [
    (200, 100),  # ≥200 dias: CRÍTICO
    (165, 80),   # ≥165 dias: CONGELADO (mediana Engaging)
    (85, 60),    # ≥85 dias: ATRASADO (1.5× Won mediana)
    (57, 40),    # ≥57 dias: LIMITE (Won mediana)
    (28, 20),    # ≥28 dias: NORMAL (0.5× Won)
    (0, 10)      # <28 dias: RECENTE
]


# =============================================================================
# CÁLCULO DE URGÊNCIA (50%)
# =============================================================================

def calculate_urgency_base(days_in_pipeline: int) -> float:
    """
    Calcula urgência base baseada em thresholds de tempo.
    
    Args:
        days_in_pipeline: Dias no pipeline
        
    Returns:
        Urgência base (0-100)
    """
    for threshold_days, urgency_value in URGENCY_THRESHOLDS:
        if days_in_pipeline >= threshold_days:
            return urgency_value
    
    return 10  # Fallback (muito recente)


def calculate_urgency(deal: Dict, benchmarks: Dict) -> float:
    """
    Calcula urgência final com multiplicadores.
    
    Fórmula:
        urgency = urgency_base × seller_load × account_difficulty × oversize
    
    Args:
        deal: Dict com dados do deal
        benchmarks: Dict com benchmarks
        
    Returns:
        Urgência (0-100)
    """
    # Base
    urgency_base = calculate_urgency_base(deal['days_in_pipeline'])
    
    # Multiplicadores
    seller_active = benchmarks['seller_active_deals'].get(deal['sales_agent'], 0)
    seller_mult = get_seller_load_multiplier(seller_active)
    
    account_wr = benchmarks['account_wr'].get(deal['account'], None)
    account_mult = get_account_difficulty_multiplier(account_wr, benchmarks['global_wr'])
    
    seller_avg_ticket = benchmarks['seller_avg_ticket'].get(deal['sales_agent'], 0)
    oversize_mult = get_oversize_urgency_multiplier(deal['close_value'], seller_avg_ticket)
    
    # Aplicar multiplicadores
    urgency = urgency_base * seller_mult * account_mult * oversize_mult
    
    # Clamp
    return clamp(urgency, 0, 100)


# =============================================================================
# CÁLCULO DE PROBABILIDADE (30%)
# =============================================================================

def calculate_probability(deal: Dict, benchmarks: Dict) -> float:
    """
    Calcula probabilidade de fechar com fatores e penalidades.
    
    Fórmula:
        prob = global_wr × seller × product × account × region × specialist
               × time_penalty × oversize_penalty × overload_penalty
    
    Args:
        deal: Dict com dados do deal
        benchmarks: Dict com benchmarks
        
    Returns:
        Probabilidade (0-100)
    """
    # Base (prior bayesiano)
    prob = benchmarks['global_wr']
    
    # Fatores multiplicativos
    prob *= get_seller_factor(deal['sales_agent'], benchmarks, benchmarks['global_wr'])
    prob *= get_product_factor(deal['product'], benchmarks, benchmarks['global_wr'])
    prob *= get_account_factor(deal['account'], benchmarks, benchmarks['global_wr'])
    
    # Região (se disponível)
    if 'regional_office' in deal and deal['regional_office']:
        prob *= get_region_factor(deal['regional_office'], benchmarks, benchmarks['global_wr'])
    
    # Especialização produto×vendedor
    prob *= get_specialist_factor(deal['sales_agent'], deal['product'], benchmarks)
    
    # Penalidades
    prob *= get_time_penalty(
        deal['days_in_pipeline'],
        benchmarks['lost_median'],
        benchmarks['won_median']
    )
    
    seller_avg_ticket = benchmarks['seller_avg_ticket'].get(deal['sales_agent'], 0)
    prob *= get_oversize_penalty(deal['close_value'], seller_avg_ticket)
    
    seller_active = benchmarks['seller_active_deals'].get(deal['sales_agent'], 0)
    prob *= get_overload_penalty(seller_active)
    
    # Clamp
    return clamp(prob, 0, 100)


# =============================================================================
# CÁLCULO DE VALOR (20%)
# =============================================================================

def calculate_value(deal: Dict, benchmarks: Dict, probability: float) -> float:
    """
    Calcula valor relativo do deal (percentil + ajustes).
    
    Args:
        deal: Dict com dados do deal
        benchmarks: Dict com benchmarks
        probability: Probabilidade já calculada (para desconto)
        
    Returns:
        Valor (0-100)
    """
    # Percentil base
    value = calculate_percentile(deal['close_value'], benchmarks['value_distribution'])
    
    # Ajustes
    value = apply_premium_product_bonus(value, deal['product'])
    value = apply_strategic_account_bonus(value, deal['account'], benchmarks['top_20_accounts'])
    value = apply_probability_discount(value, probability)
    
    # Clamp
    return clamp(value, 0, 100)


# =============================================================================
# CÁLCULO DE VIABILIDADE (SEPARADA)
# =============================================================================

def calculate_viability(deal: Dict, benchmarks: Dict) -> float:
    """
    Calcula viabilidade do vendedor resolver este deal.
    
    Baseado em:
    - Prospecting (pipeline novo)
    - Carga (deals ativos)
    - Especialização (match produto×vendedor)
    
    Args:
        deal: Dict com dados do deal
        benchmarks: Dict com benchmarks
        
    Returns:
        Viabilidade (0-100)
    """
    viability_base = 50  # Ponto neutro
    
    # Fator 1: Prospecting
    prospecting_count = benchmarks['seller_prospecting'].get(deal['sales_agent'], 0)
    prospecting_factor = get_prospecting_viability_factor(prospecting_count)
    
    # Fator 2: Carga
    active_deals = benchmarks['seller_active_deals'].get(deal['sales_agent'], 0)
    load_factor = get_load_viability_factor(active_deals)
    
    # Fator 3: Especialização
    specialist_prob_factor = get_specialist_factor(deal['sales_agent'], deal['product'], benchmarks)
    specialist_factor = get_specialist_viability_factor(specialist_prob_factor)
    
    # Aplicar fatores
    viability = viability_base * prospecting_factor * load_factor * specialist_factor
    
    # Clamp
    return clamp(viability, 0, 100)


# =============================================================================
# AGREGAÇÃO DO SCORE
# =============================================================================

def calculate_score(deal: Dict, benchmarks: Dict) -> Dict:
    """
    Calcula score final agregando componentes.
    
    Args:
        deal: Dict com dados do deal
        benchmarks: Dict com benchmarks
        
    Returns:
        Dict com score, componentes, viabilidade e ação
    """
    # Validar deal
    if not validate_deal(deal):
        return {
            'error': 'Invalid deal: missing required fields',
            'score': 0,
            'urgency': 0,
            'probability': 0,
            'value': 0,
            'viability': 0
        }
    
    # Calcular componentes
    urgency = calculate_urgency(deal, benchmarks)
    probability = calculate_probability(deal, benchmarks)
    value = calculate_value(deal, benchmarks, probability)
    
    # Score agregado
    score = (
        WEIGHT_URGENCY * urgency +
        WEIGHT_PROBABILITY * probability +
        WEIGHT_VALUE * value
    )
    
    # Viabilidade (separada)
    viability = calculate_viability(deal, benchmarks)
    
    # Sugerir ação
    action = suggest_action(score, urgency, probability, viability, deal, benchmarks)
    
    return {
        'opportunity_id': deal['opportunity_id'],
        'score': round(score, 1),
        'urgency': round(urgency, 1),
        'probability': round(probability, 1),
        'value': round(value, 1),
        'viability': round(viability, 1),
        'action': action,
        'deal_info': {
            'sales_agent': deal['sales_agent'],
            'product': deal['product'],
            'account': deal['account'],
            'close_value': deal['close_value'],
            'days_in_pipeline': deal['days_in_pipeline'],
            'deal_stage': deal.get('deal_stage', 'Unknown'),
            'regional_office': deal.get('regional_office', 'Unknown')
        }
    }


# =============================================================================
# SUGESTÃO DE AÇÃO (MATRIZ SCORE × VIABILIDADE)
# =============================================================================

def suggest_action(score: float, urgency: float, probability: float, 
                   viability: float, deal: Dict, benchmarks: Dict) -> Dict:
    """
    Deriva ação baseada em score × viabilidade com explicações detalhadas.
    
    Args:
        score: Score calculado
        urgency: Urgência
        probability: Probabilidade
        viability: Viabilidade
        deal: Deal original
        benchmarks: Benchmarks (para encontrar melhor vendedor)
        
    Returns:
        Dict com tipo de ação, mensagem, razão detalhada e contexto
    """
    # Coletar contexto para explicações
    days = deal['days_in_pipeline']
    seller = deal['sales_agent']
    product = deal['product']
    value = deal['close_value']
    
    prospecting = benchmarks['seller_prospecting'].get(seller, 0)
    active_deals = benchmarks['seller_active_deals'].get(seller, 0)
    won_median = benchmarks['won_median']
    engaging_median = benchmarks['engaging_median']
    
    # Construir explicações contextuais
    urgency_context = []
    if days >= 200:
        urgency_context.append(f"frozen {days} days (3.5× typical Won time)")
    elif days >= engaging_median:
        urgency_context.append(f"stuck {days} days (above Engaging median {engaging_median:.0f}d)")
    elif days >= won_median:
        urgency_context.append(f"{days} days in pipeline (exceeded Won median {won_median:.0f}d)")
    
    viability_context = []
    if prospecting == 0:
        viability_context.append("no new prospects")
    elif prospecting < 10:
        viability_context.append(f"low prospecting ({prospecting})")
    
    if active_deals > 150:
        viability_context.append(f"overloaded ({active_deals} active deals)")
    elif active_deals > 100:
        viability_context.append(f"high load ({active_deals} deals)")
    
    probability_context = []
    if probability < 40:
        probability_context.append(f"low probability ({probability:.0f}%)")
    elif probability < 55:
        probability_context.append(f"medium probability ({probability:.0f}%)")
    
    # =========================================================================
    # CASO 1: Score ALTO (≥70) - Deals críticos/importantes
    # =========================================================================
    if score >= 70:
        
        # 1A: Alta viabilidade - VENDEDOR PODE RESOLVER
        if viability >= 60:
            reason_parts = [f"Deal parado há {days} dias com alta urgência"]
            if urgency_context:
                reason_parts.append(f"({', '.join(urgency_context)})")
            reason_parts.append("e você tem capacidade para agir agora — não deixe essa janela fechar")

            return {
                'type': 'PUSH_HARD',
                'icon': '🔥',
                'message': 'Deal crítico — priorize o fechamento esta semana',
                'reason': ' '.join(reason_parts),
                'priority': 1,
                'details': {
                    'urgency_level': 'critical' if urgency >= 80 else 'high',
                    'days_in_pipeline': days,
                    'your_capacity': 'good',
                    'action_steps': [
                        'Agende uma ligação com o tomador de decisão ainda esta semana',
                        'Confirme orçamento, prazo e autoridade para avançar',
                        'Conduza para o compromisso — ou mova para Perdido sem meio-termo'
                    ]
                }
            }
        
        # 1B: Viabilidade média - REQUALIFICAR ANTES
        elif viability >= 40:
            reason_parts = ["Deal com alta urgência"]
            if urgency_context:
                reason_parts.append(f"({', '.join(urgency_context)})")
            reason_parts.append("mas sua capacidade está limitada")
            if viability_context:
                reason_parts.append(f"({', '.join(viability_context)})")
            reason_parts.append("— requalificar agora evita esforço perdido em um deal que pode não fechar")

            return {
                'type': 'RE_QUALIFY',
                'icon': '🔄',
                'message': 'Antes de investir mais tempo, confirme se esse deal ainda está vivo',
                'reason': ' '.join(reason_parts),
                'priority': 2,
                'details': {
                    'urgency_level': 'high',
                    'your_capacity': 'limited',
                    'action_steps': [
                        'Faça uma ligação rápida de qualificação (máx. 15 min)',
                        'Confirme: orçamento aprovado? Prazo realista? Decisor engajado?',
                        'Se sim → empurre para fechar. Se não → descarte ou transfira agora'
                    ]
                }
            }
        
        # 1C: Viabilidade baixa - TRANSFERIR OU DESCARTAR
        else:  # viability < 40
            
            # Se probabilidade é boa (≥60%) - VALE TRANSFERIR
            if probability >= 60:
                best_seller_tagged, transfer_context = find_best_seller_for_transfer(deal, benchmarks)
                best_seller = best_seller_tagged.split(' (')[0] if '(' in best_seller_tagged else best_seller_tagged
                
                # Calcular viabilidade do target para comparação
                target_deal = deal.copy()
                target_deal['sales_agent'] = best_seller
                target_viability = calculate_viability(target_deal, benchmarks)
                
                # Contexto do target
                target_prospecting = benchmarks['seller_prospecting'].get(best_seller, 0)
                target_active = benchmarks['seller_active_deals'].get(best_seller, 0)
                
                reason_parts = [f"Deal com {probability:.0f}% de probabilidade"]
                reason_parts.append("mas sua carga atual impede a dedicação necessária")

                # Focar em CARGA, não prospecting
                capacity_issues = []
                if active_deals > 150:
                    capacity_issues.append(f"sobrecarregado: {active_deals} deals ativos")
                elif active_deals > 100:
                    capacity_issues.append(f"carga alta: {active_deals} deals ativos")

                # Só mencionar prospecting se for círculo vicioso
                if active_deals > 100 and prospecting == 0:
                    capacity_issues.append("sem crescimento de pipeline")

                if capacity_issues:
                    reason_parts.append(f"({', '.join(capacity_issues)})")
                
                # Why this helps (não "who is better")
                transfer_benefits = []
                
                # Carga
                if target_active < active_deals * 0.6:  # Target tem <60% da sua carga
                    ratio = active_deals / max(target_active, 1)
                    transfer_benefits.append(f"Carga {ratio:.1f}× menor que a sua ({target_active} vs {active_deals} deals ativos)")
                elif target_active < active_deals:
                    transfer_benefits.append(f"Carga menor que a sua ({target_active} deals ativos)")

                # Prospecting
                if prospecting == 0 and target_prospecting > 0:
                    transfer_benefits.append(f"Pipeline ativo em crescimento ({target_prospecting} prospects)")

                # Capacidade geral
                if target_viability > viability + 20:
                    transfer_benefits.append("O vendedor sugerido pode dedicar atenção focada a esse deal crítico")

                # Especialização no produto
                product = deal['product']
                product_key = f"{product}|{best_seller}"
                target_product_wr = benchmarks.get('product_seller_wr', {}).get(product_key)
                if target_product_wr and target_product_wr > benchmarks['global_wr'] + 5:
                    transfer_benefits.append(f"{target_product_wr:.0f}% de win rate em {product}")

                # Especialização no setor da conta
                sector = benchmarks.get('account_sector', {}).get(deal.get('account', ''))
                if sector:
                    sector_key = f"{best_seller}|{sector}"
                    target_sector_wr = benchmarks.get('seller_sector_wr', {}).get(sector_key)
                    if target_sector_wr and target_sector_wr > benchmarks['global_wr']:
                        transfer_benefits.append(f"Histórico forte no setor {sector} — {target_sector_wr:.0f}% de win rate")

                # Ciclo de fechamento mais rápido
                cycle_key = f"{product}|{best_seller}"
                target_cycle = benchmarks.get('seller_product_cycle', {}).get(cycle_key)
                if target_cycle and target_cycle < benchmarks['won_median'] * 0.85:
                    transfer_benefits.append(f"Ciclo médio de {target_cycle:.0f} dias nesse produto — mais rápido que a média")

                # Benefício para VOCÊ
                if active_deals > 100:
                    transfer_benefits.append(f"Libera você para focar nos seus outros {active_deals - 1} deals")

                return {
                    'type': 'TRANSFER',
                    'icon': '🔀',
                    'message': f'Esse deal tem potencial, mas precisa de mais atenção do que você consegue dar agora — considere transferi-lo para {best_seller_tagged}',
                    'reason': ' '.join(reason_parts) + ' — transferir agora protege a oportunidade',
                    'priority': 1,
                    'details': {
                        'target_seller': best_seller,
                        'transfer_level': transfer_context['transfer_level'],
                        'hierarchy_explanation': transfer_context['hierarchy_reason'],

                        # Your context
                        'your_context': {
                            'viability': round(viability, 1),
                            'active_deals': active_deals,
                            'prospecting': prospecting,
                            'capacity_assessment': 'insuficiente para esse deal crítico'
                        },

                        # Target context
                        'target_context': {
                            'viability': round(target_viability, 1),
                            'active_deals': target_active,
                            'prospecting': target_prospecting,
                            'capacity_assessment': 'adequada' if target_viability >= 50 else 'moderada'
                        },

                        # WHY THIS HELPS (não "who is better")
                        'why_this_helps': transfer_benefits,

                        'expected_impact': f'Probabilidade de fechamento {probability:.0f}% → ~{min(probability + 15, 95):.0f}%',
                        'action_steps': [
                            f'Repasse o histórico da conta e do deal para {best_seller}',
                            'Transfira a propriedade no CRM',
                            f'Apresente {best_seller} aos principais stakeholders, se necessário'
                        ]
                    }
                }
            
            # Se probabilidade é baixa (<60%) - NÃO VALE NEM TRANSFERIR
            else:
                reason_parts = ["Deal parado"]
                if urgency_context:
                    reason_parts.append(f"({', '.join(urgency_context)})")
                reason_parts.append(f"com probabilidade baixa ({probability:.0f}%)")
                if viability_context:
                    reason_parts.append(f"e sem capacidade para mudar esse cenário ({', '.join(viability_context)})")
                reason_parts.append("— manter aberto só ocupa espaço mental que poderia ir para deals com chance real")

                return {
                    'type': 'DISCARD',
                    'icon': '❌',
                    'message': 'Mova para Perdido — libere energia para oportunidades reais',
                    'reason': ' '.join(reason_parts),
                    'priority': 2,
                    'details': {
                        'why_discard': f'Probabilidade baixa demais ({probability:.0f}%) para justificar transferência',
                        'opportunity_cost': f'Libera foco para {prospecting} prospects em andamento' if prospecting > 0 else 'Tempo melhor investido em prospecção',
                        'action_steps': [
                            'Mova para Perdido no CRM',
                            'Registre o motivo: baixa probabilidade + capacidade insuficiente',
                            'Salve o contexto para reativação futura se o cenário mudar'
                        ]
                    }
                }
    
    # =========================================================================
    # CASO 2: Score MÉDIO (60-69) - Deals importantes mas não críticos
    # =========================================================================
    elif score >= 60:
        
        # 2A: Alta viabilidade - ACELERAR
        if viability >= 60:
            reason_parts = [f"Probabilidade de {probability:.0f}% e capacidade disponível"]
            if days >= won_median:
                reason_parts.append(f"— deal em {days} dias, já é hora de fechar")
            reason_parts.append("— esse deal está maduro, esperar só aumenta o risco de perder o momento")

            return {
                'type': 'ACCELERATE',
                'icon': '⚡',
                'message': 'As condições estão favoráveis — acelere para o fechamento',
                'reason': ' '.join(reason_parts),
                'priority': 2,
                'details': {
                    'your_capacity': 'good',
                    'action_steps': [
                        'Agende a chamada de fechamento nos próximos 3 dias',
                        'Prepare proposta ou contrato para envio',
                        'Mapeie e enderece objeções pendentes antes da reunião'
                    ]
                }
            }
        
        # 2B: Viabilidade baixa - CONSIDERAR TRANSFER
        elif viability < 40:
            best_seller_tagged, transfer_context = find_best_seller_for_transfer(deal, benchmarks)
            best_seller = best_seller_tagged.split(' (')[0] if '(' in best_seller_tagged else best_seller_tagged
            
            # Calcular viabilidade do target
            target_deal = deal.copy()
            target_deal['sales_agent'] = best_seller
            target_viability = calculate_viability(target_deal, benchmarks)
            
            # Contexto do target
            target_prospecting = benchmarks['seller_prospecting'].get(best_seller, 0)
            target_active = benchmarks['seller_active_deals'].get(best_seller, 0)
            
            reason_parts = ["Deal com potencial"]

            # Focar em CARGA
            capacity_issues = []
            if active_deals > 150:
                capacity_issues.append(f"sobrecarregado: {active_deals} deals ativos")
            elif active_deals > 100:
                capacity_issues.append(f"carga alta: {active_deals} deals ativos")

            # Só mencionar prospecting se círculo vicioso
            if active_deals > 100 and prospecting == 0:
                capacity_issues.append("sem crescimento de pipeline")
            elif prospecting == 0:
                capacity_issues.append("sem novos prospects")

            if capacity_issues:
                reason_parts.append(f"mas sua capacidade limitada ({', '.join(capacity_issues)}) pode atrasar o progresso")

            reason_parts.append("— ainda dá tempo de decidir sem pressão")
            
            # Why this helps
            transfer_benefits = []
            
            if target_active < active_deals * 0.6:
                ratio = active_deals / max(target_active, 1)
                transfer_benefits.append(f"Carga {ratio:.1f}× menor que a sua ({target_active} vs {active_deals} deals ativos)")
            elif target_active < active_deals:
                transfer_benefits.append(f"Carga menor que a sua ({target_active} deals ativos)")

            if prospecting == 0 and target_prospecting > 0:
                transfer_benefits.append(f"Pipeline ativo em crescimento ({target_prospecting} prospects)")
            
            if target_viability > viability + 15:
                transfer_benefits.append("O vendedor sugerido pode oferecer atenção mais focada a esse deal")

            # Especialização no produto
            product = deal['product']
            product_key = f"{product}|{best_seller}"
            target_product_wr = benchmarks.get('product_seller_wr', {}).get(product_key)
            if target_product_wr and target_product_wr > benchmarks['global_wr'] + 5:
                transfer_benefits.append(f"{target_product_wr:.0f}% de win rate em {product}")

            # Especialização no setor da conta
            sector = benchmarks.get('account_sector', {}).get(deal.get('account', ''))
            if sector:
                sector_key = f"{best_seller}|{sector}"
                target_sector_wr = benchmarks.get('seller_sector_wr', {}).get(sector_key)
                if target_sector_wr and target_sector_wr > benchmarks['global_wr']:
                    transfer_benefits.append(f"Histórico forte no setor {sector} — {target_sector_wr:.0f}% de win rate")

            # Ciclo de fechamento mais rápido
            cycle_key = f"{product}|{best_seller}"
            target_cycle = benchmarks.get('seller_product_cycle', {}).get(cycle_key)
            if target_cycle and target_cycle < benchmarks['won_median'] * 0.85:
                transfer_benefits.append(f"Ciclo médio de {target_cycle:.0f} dias nesse produto — mais rápido que a média")

            return {
                'type': 'CONSIDER_TRANSFER',
                'icon': '🔀',
                'message': f'Avalie com honestidade se você consegue dar a atenção que esse deal precisa — se não, transfira para {best_seller_tagged}',
                'reason': ' '.join(reason_parts),
                'priority': 3,
                'details': {
                    'target_seller': best_seller,
                    'transfer_level': transfer_context['transfer_level'],
                    'hierarchy_explanation': transfer_context['hierarchy_reason'],

                    # Your context
                    'your_context': {
                        'viability': round(viability, 1),
                        'active_deals': active_deals,
                        'prospecting': prospecting,
                        'capacity_assessment': 'limitada'
                    },

                    # Target context
                    'target_context': {
                        'viability': round(target_viability, 1),
                        'active_deals': target_active,
                        'prospecting': target_prospecting,
                        'capacity_assessment': 'adequada' if target_viability >= 50 else 'moderada'
                    },

                    # Why this helps
                    'why_this_helps': transfer_benefits,

                    'why_consider': 'Ainda não é urgente, mas sua capacidade limitada pode atrasar o progresso',
                    'action_steps': [
                        'Seja honesto: você consegue dedicar atenção real a esse deal este mês?',
                        f'Se não → transfira para {best_seller} enquanto ainda há tempo',
                        'Se sim → trate como Acelerar e agende as atividades de fechamento'
                    ]
                }
            }
        
        # 2C: Viabilidade média - INVESTIGAR
        else:
            reason_parts = ["Esse deal parou"]
            if days >= won_median:
                reason_parts.append(f"— {days} dias em pipeline, acima do tempo típico de fechamento")
            reason_parts.append("— algo está travando o avanço e precisa ser identificado agora antes de virar perda")

            return {
                'type': 'INVESTIGATE',
                'icon': '🔍',
                'message': 'Esse deal parou — descubra o motivo antes que esfrie de vez',
                'reason': ' '.join(reason_parts),
                'priority': 3,
                'details': {
                    'action_steps': [
                        'Revise o histórico: quando foi o último contato e o que foi discutido?',
                        'Identifique o bloqueio: orçamento, prazo, decisor ou interesse real?',
                        'Enderece o bloqueio — ou mova para Perdido se não tiver solução'
                    ]
                }
            }
    
    # =========================================================================
    # CASO 3: Score BAIXO (<60) - Deals não urgentes
    # =========================================================================
    else:
        if days < won_median:
            message = 'Deal no caminho certo — mantenha o ritmo'
            reason_parts = [f"Deal recente ({days} dias)"]
            if probability >= 60:
                reason_parts.append(f"com probabilidade de {probability:.0f}%")
            reason_parts.append("— siga o processo e não force o ritmo agora")
        else:
            message = 'Deal ainda no radar, mas fique de olho — o tempo está passando'
            reason_parts = [f"Deal em {days} dias, já acima do tempo mediano de fechamento"]
            if probability >= 60:
                reason_parts.append(f"com probabilidade de {probability:.0f}%")
            reason_parts.append("— ainda não é urgente, mas precisa de atenção ativa para não virar problema")

        return {
            'type': 'MONITOR',
            'icon': '⏸',
            'message': message,
            'reason': ' '.join(reason_parts),
            'priority': 4,
            'details': {
                'status': 'on_track' if days < won_median else 'needs_attention_soon',
                'action_steps': [
                    'Mantenha os touchpoints regulares com o contato principal',
                    'Nutra o relacionamento sem pressionar fechamento ainda',
                    'Reavalie a prioridade se passar 90 dias sem avanço concreto'
                ]
            }
        }


def find_best_seller_for_transfer(deal: Dict, benchmarks: Dict) -> tuple:
    """
    Encontra melhor vendedor para transferir o deal.
    
    HIERARQUIA DE PRIORIDADE:
    1. Mesmo time (mesmo manager) - minimiza atrito
    2. Mesma região, outro time - proximidade geográfica
    3. Outra região - último recurso
    
    Dentro de cada prioridade, critérios:
    - Tem prospecting (não está protegendo deals)
    - Carga leve (<100 deals)
    - Especialista no produto (se possível)
    - Win rate alto
    
    Args:
        deal: Deal a transferir
        benchmarks: Benchmarks
        
    Returns:
        Tuple (nome_vendedor_com_tag, dict_com_contexto)
    """
    current_seller = deal['sales_agent']
    current_region = deal.get('regional_office', None)
    
    # Precisamos do teams_df para pegar manager
    from pathlib import Path
    import pandas as pd
    DATA_DIR = Path(__file__).parent.parent / "data" / "metrics"
    teams_df = pd.read_csv(DATA_DIR / "sales_teams.csv")
    
    # Dict: seller → (manager, region)
    seller_info = {}
    for _, row in teams_df.iterrows():
        seller_info[row['sales_agent']] = {
            'manager': row['manager'],
            'region': row['regional_office']
        }
    
    # Info do vendedor atual
    current_manager = seller_info.get(current_seller, {}).get('manager', None)
    current_region = seller_info.get(current_seller, {}).get('region', current_region)

    # Função auxiliar para pontuar candidato
    def score_candidate(seller: str, product: str) -> int:
        prospecting = benchmarks['seller_prospecting'].get(seller, 0)
        active_deals = benchmarks['seller_active_deals'].get(seller, 0)
        seller_wr = benchmarks['seller_wr'].get(seller, 0)
        global_wr = benchmarks['global_wr']

        score = 0

        # Prospecting
        if prospecting > 20:
            score += 30
        elif prospecting > 10:
            score += 20
        else:
            score += 10

        # Carga
        if active_deals < 50:
            score += 30
        elif active_deals < 100:
            score += 20
        else:
            score += 10

        # Especialização no produto
        combo_key = f"{product}|{seller}"
        if combo_key in benchmarks['product_seller_wr']:
            combo_wr = benchmarks['product_seller_wr'][combo_key]
            if combo_wr > seller_wr + 5:
                score += 40

        # Especialização no setor da conta
        account = deal.get('account', '')
        sector = benchmarks.get('account_sector', {}).get(account)
        if sector:
            sector_key = f"{seller}|{sector}"
            sector_wr = benchmarks.get('seller_sector_wr', {}).get(sector_key)
            if sector_wr and sector_wr > global_wr + 10:
                score += 25

        # Win rate geral
        score += (seller_wr / global_wr) * 20

        return score
    
    # Coletar candidatos por prioridade
    priority_1 = []  # Mesmo time
    priority_2 = []  # Mesma região, outro time
    priority_3 = []  # Outra região
    
    for seller in benchmarks['seller_wr'].keys():
        # Ignorar vendedor atual
        if seller == current_seller:
            continue
        
        # Filtros eliminatórios
        prospecting = benchmarks['seller_prospecting'].get(seller, 0)
        active_deals = benchmarks['seller_active_deals'].get(seller, 0)
        
        if prospecting == 0:  # Sem prospecting
            continue
        
        if active_deals > 150:  # Sobrecarregado
            continue
        
        # Calcular score
        candidate_score = score_candidate(seller, deal['product'])
        
        # Classificar por prioridade
        seller_manager = seller_info.get(seller, {}).get('manager', None)
        seller_region = seller_info.get(seller, {}).get('region', None)
        
        if seller_manager and seller_manager == current_manager:
            # Prioridade 1: Mesmo time
            priority_1.append((seller, candidate_score, 'same_team', seller_manager, seller_region))
        
        elif seller_region and seller_region == current_region:
            # Prioridade 2: Mesma região, outro time
            priority_2.append((seller, candidate_score, 'same_region', seller_manager, seller_region))
        
        else:
            # Prioridade 3: Outra região
            priority_3.append((seller, candidate_score, 'other_region', seller_manager, seller_region))
    
    # Ordenar cada lista por score
    priority_1.sort(key=lambda x: x[1], reverse=True)
    priority_2.sort(key=lambda x: x[1], reverse=True)
    priority_3.sort(key=lambda x: x[1], reverse=True)
    
    # Contexto de hierarquia para explicação
    hierarchy_context = {
        'current_manager': current_manager,
        'current_region': current_region,
        'candidates_same_team': len(priority_1),
        'candidates_same_region': len(priority_2),
        'candidates_other_region': len(priority_3)
    }
    
    # Retornar melhor candidato seguindo prioridades
    if priority_1:
        best = priority_1[0]
        return (
            f"{best[0]} (same team)",
            {
                'transfer_level': 'same_team',
                'target_manager': best[3],
                'target_region': best[4],
                'hierarchy_reason': f'Found available seller in same team (manager: {current_manager})',
                **hierarchy_context
            }
        )
    
    if priority_2:
        best = priority_2[0]
        return (
            f"{best[0]} (same region)",
            {
                'transfer_level': 'same_region',
                'target_manager': best[3],
                'target_region': best[4],
                'hierarchy_reason': f'No available sellers in same team. Found in same region ({current_region}), different team (manager: {best[3]})',
                **hierarchy_context
            }
        )
    
    if priority_3:
        best = priority_3[0]
        return (
            f"{best[0]} (other region)",
            {
                'transfer_level': 'other_region',
                'target_manager': best[3],
                'target_region': best[4],
                'hierarchy_reason': f'No available sellers in same team or same region ({current_region}). Transferring to {best[4]} region (manager: {best[3]})',
                **hierarchy_context
            }
        )
    
    # Fallback: nenhum candidato encontrado
    return (
        f"{current_manager if current_manager else 'Manager'} (escalate)",
        {
            'transfer_level': 'escalate',
            'hierarchy_reason': f'No available sellers found in any region with adequate capacity. Escalate to manager ({current_manager})',
            **hierarchy_context
        }
    )
    """
    Encontra melhor vendedor para transferir o deal.
    
    HIERARQUIA DE PRIORIDADE:
    1. Mesmo time (mesmo manager) - minimiza atrito
    2. Mesma região, outro time - proximidade geográfica
    3. Outra região - último recurso
    
    Dentro de cada prioridade, critérios:
    - Tem prospecting (não está protegendo deals)
    - Carga leve (<100 deals)
    - Especialista no produto (se possível)
    - Win rate alto
    
    Args:
        deal: Deal a transferir
        benchmarks: Benchmarks
        
    Returns:
        Nome do melhor vendedor
    """
    current_seller = deal['sales_agent']
    current_region = deal.get('regional_office', None)
    
    # Precisamos do teams_df para pegar manager
    # Vamos criar um dict seller → (manager, region) a partir dos benchmarks
    # (assumption: essa info está disponível via load dos dados)
    
    # Por simplicidade, vamos buscar do CSV novamente (cacheável)
    from pathlib import Path
    import pandas as pd
    DATA_DIR = Path(__file__).parent.parent / "data" / "metrics"
    teams_df = pd.read_csv(DATA_DIR / "sales_teams.csv")
    
    # Dict: seller → (manager, region)
    seller_info = {}
    for _, row in teams_df.iterrows():
        seller_info[row['sales_agent']] = {
            'manager': row['manager'],
            'region': row['regional_office']
        }
    
    # Info do vendedor atual
    current_manager = seller_info.get(current_seller, {}).get('manager', None)
    current_region = seller_info.get(current_seller, {}).get('region', current_region)

    # Função auxiliar para pontuar candidato
    def score_candidate(seller: str, product: str) -> int:
        prospecting = benchmarks['seller_prospecting'].get(seller, 0)
        active_deals = benchmarks['seller_active_deals'].get(seller, 0)
        seller_wr = benchmarks['seller_wr'].get(seller, 0)
        global_wr = benchmarks['global_wr']

        score = 0

        # Prospecting
        if prospecting > 20:
            score += 30
        elif prospecting > 10:
            score += 20
        else:
            score += 10

        # Carga
        if active_deals < 50:
            score += 30
        elif active_deals < 100:
            score += 20
        else:
            score += 10

        # Especialização no produto
        combo_key = f"{product}|{seller}"
        if combo_key in benchmarks['product_seller_wr']:
            combo_wr = benchmarks['product_seller_wr'][combo_key]
            if combo_wr > seller_wr + 5:
                score += 40

        # Especialização no setor da conta
        account = deal.get('account', '')
        sector = benchmarks.get('account_sector', {}).get(account)
        if sector:
            sector_key = f"{seller}|{sector}"
            sector_wr = benchmarks.get('seller_sector_wr', {}).get(sector_key)
            if sector_wr and sector_wr > global_wr + 10:
                score += 25

        # Win rate geral
        score += (seller_wr / global_wr) * 20

        return score
    
    # Coletar candidatos por prioridade
    priority_1 = []  # Mesmo time
    priority_2 = []  # Mesma região, outro time
    priority_3 = []  # Outra região
    
    for seller in benchmarks['seller_wr'].keys():
        # Ignorar vendedor atual
        if seller == current_seller:
            continue
        
        # Filtros eliminatórios
        prospecting = benchmarks['seller_prospecting'].get(seller, 0)
        active_deals = benchmarks['seller_active_deals'].get(seller, 0)
        
        if prospecting == 0:  # Sem prospecting
            continue
        
        if active_deals > 150:  # Sobrecarregado
            continue
        
        # Calcular score
        candidate_score = score_candidate(seller, deal['product'])
        
        # Classificar por prioridade
        seller_manager = seller_info.get(seller, {}).get('manager', None)
        seller_region = seller_info.get(seller, {}).get('region', None)
        
        if seller_manager and seller_manager == current_manager:
            # Prioridade 1: Mesmo time
            priority_1.append((seller, candidate_score, 'same_team'))
        
        elif seller_region and seller_region == current_region:
            # Prioridade 2: Mesma região, outro time
            priority_2.append((seller, candidate_score, 'same_region'))
        
        else:
            # Prioridade 3: Outra região
            priority_3.append((seller, candidate_score, 'other_region'))
    
    # Ordenar cada lista por score
    priority_1.sort(key=lambda x: x[1], reverse=True)
    priority_2.sort(key=lambda x: x[1], reverse=True)
    priority_3.sort(key=lambda x: x[1], reverse=True)
    
    # Retornar melhor candidato seguindo prioridades
    if priority_1:
        best = priority_1[0]
        return f"{best[0]} (same team)"
    
    if priority_2:
        best = priority_2[0]
        return f"{best[0]} (same region)"
    
    if priority_3:
        best = priority_3[0]
        return f"{best[0]} (other region)"
    
    # Fallback: nenhum candidato encontrado
    return f"{current_manager if current_manager else 'Manager'} (escalate)"


# =============================================================================
# BATCH SCORING
# =============================================================================

def score_all_deals(deals: List[Dict], benchmarks: Dict, 
                    min_score: float = 0) -> List[Dict]:
    """
    Calcula score de múltiplos deals.
    
    Args:
        deals: Lista de deals
        benchmarks: Benchmarks
        min_score: Filtrar deals com score >= min_score
        
    Returns:
        Lista de resultados ordenada por score (decrescente)
    """
    results = []

    for deal in deals:
        deal_stage = deal.get('deal_stage', '').lower()
        if deal_stage in ('lost', 'won'):
            continue

        result = calculate_score(deal, benchmarks)
        
        if result['score'] >= min_score:
            results.append(result)
    
    # Ordenar por score (maior primeiro)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results


# =============================================================================
# EXPLICAÇÃO DO SCORE
# =============================================================================

def explain_score(result: Dict, benchmarks: Dict) -> str:
    """
    Gera explicação textual do score.
    
    Args:
        result: Resultado do calculate_score
        benchmarks: Benchmarks
        
    Returns:
        String formatada com explicação
    """
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"SCORE: {result['score']:.1f}/100")
    lines.append(f"{'='*60}")
    lines.append("")
    
    lines.append(f"📊 BREAKDOWN:")
    lines.append(f"  • Urgência:      {result['urgency']:.1f}/100 (50% do score)")
    lines.append(f"  • Probabilidade: {result['probability']:.1f}/100 (30% do score)")
    lines.append(f"  • Valor:         {result['value']:.1f}/100 (20% do score)")
    lines.append(f"  • Viabilidade:   {result['viability']:.1f}/100 (separada)")
    lines.append("")
    
    lines.append(f"🎯 AÇÃO SUGERIDA:")
    action = result['action']
    lines.append(f"  {action['icon']} {action['type']}")
    lines.append(f"  → {action['message']}")
    lines.append(f"  Razão: {action['reason']}")
    lines.append("")
    
    lines.append(f"📋 DEAL INFO:")
    info = result['deal_info']
    lines.append(f"  • ID: {result['opportunity_id']}")
    lines.append(f"  • Vendedor: {info['sales_agent']}")
    lines.append(f"  • Produto: {info['product']}")
    lines.append(f"  • Conta: {info['account']}")
    lines.append(f"  • Valor: ${info['close_value']:,.0f}")
    lines.append(f"  • Dias no pipeline: {info['days_in_pipeline']}")
    lines.append(f"  • Estágio: {info['deal_stage']}")
    lines.append("")
    
    return "\n".join(lines)


# =============================================================================
# TESTES (se executar módulo diretamente)
# =============================================================================

if __name__ == "__main__":
    from core.data_loader import load_benchmarks, load_deals
    
    print("=" * 60)
    print("SCORING ENGINE - TESTE")
    print("=" * 60)
    print()
    
    # Carregar dados
    print("📊 Carregando benchmarks e deals...")
    benchmarks = load_benchmarks()
    deals = load_deals(deal_stage='Engaging')
    print(f"   ✓ {len(deals)} deals em Engaging")
    print()
    
    # Testar alguns deals
    print("🧪 Calculando score dos primeiros 5 deals:")
    print()
    
    for i, deal in enumerate(deals[:5], 1):
        result = calculate_score(deal, benchmarks)
        print(f"{i}. {result['opportunity_id']} - Score: {result['score']:.1f}")
        print(f"   {result['action']['icon']} {result['action']['type']}: {result['action']['message']}")
        print()
    
    # Estatísticas
    print("=" * 60)
    print("ESTATÍSTICAS")
    print("=" * 60)
    
    all_results = score_all_deals(deals, benchmarks)
    
    scores = [r['score'] for r in all_results]
    print(f"Deals processados: {len(all_results)}")
    print(f"Score médio: {sum(scores)/len(scores):.1f}")
    print(f"Score mínimo: {min(scores):.1f}")
    print(f"Score máximo: {max(scores):.1f}")
    print()
    
    # Distribuição por ação
    actions_count = {}
    for r in all_results:
        action_type = r['action']['type']
        actions_count[action_type] = actions_count.get(action_type, 0) + 1
    
    print("Distribuição de ações:")
    for action, count in sorted(actions_count.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(all_results)) * 100
        print(f"  {action}: {count} deals ({pct:.1f}%)")