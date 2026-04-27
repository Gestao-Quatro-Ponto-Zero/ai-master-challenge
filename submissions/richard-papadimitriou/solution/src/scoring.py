import pandas as pd
import numpy as np
from datetime import datetime

def generate_suggested_message(row):
    """
    Generates a rule-based suggested message (WhatsApp/Email template).
    """
    account = str(row.get('account', 'Cliente'))
    product = str(row.get('product', 'Produto'))
    stage = str(row.get('deal_stage', 'Prospecção'))
    score = row.get('score', 0)
    
    # Template Selection
    if score >= 90:
        return f"🚨 *Ação Imediata*: Olá, time da {account}. Revisando nossas prioridades, o projeto do {product} se destaca pelo impacto. Podemos agendar 15 min hoje para finalizarmos os próximos passos?"
    elif stage == 'Prospecting':
        return f"👋 *Abordagem*: Olá! Estou entrando em contato com a {account} para apresentar como o {product} tem ajudado empresas do seu setor. Teria disponibilidade para uma breve conversa na quarta-feira?"
    elif stage == 'Engaging':
        return f"📈 *Follow-up*: Olá! Com base no que discutimos sobre o {product}, preparei um resumo de como podemos acelerar a implementação na {account}. Vamos marcar um follow-up?"
    return f"☕ *Retomada*: Olá! Gostaria de retomar nosso contato sobre o {product}. Como estão as prioridades na {account} para este trimestre?"

def generate_ai_memo(row):
    """
    Generates an executive AI Decision Memo (Natural Language).
    Upgrade: Executive, decisional, natural phrasing.
    """
    factors = str(row.get('reason', 'fatores favoráveis')).replace(";", " e")
    age = int(row.get('deal_age', 0))
    risk = str(row.get('commercial_risk', 'esfriamento do interesse'))
    action = str(row.get('next_action', 'realizar follow-up imediato'))
    
    memo = f"Este deal combina {factors}, porém está há {age} dias sem evolução significativa no pipeline. "
    memo += f"Se não houver ação imediata, há risco de {risk.lower()} e perda de timing estratégico. "
    memo += f"Recomenda-se {action.lower()} para destravar esta receita."
    return memo

def bayesian_smooth_rate(count_won, count_total, prior_rate, prior_weight=30):
    """
    Applies Bayesian Smoothing to win rates to avoid bias in small samples.
    """
    return (count_won + (prior_weight * prior_rate)) / (count_total + prior_weight)

def calculate_scores(df):
    """
    Calculates priority scores with Financial Impact Layer and Strategic Insights.
    """
    # 1. Global Metrics for Bayesian Prior
    global_win_rate = len(df[df['deal_stage'] == 'Won']) / len(df[df['deal_stage'].isin(['Won', 'Lost'])])

    # 2. Historical Analysis with Bayesian Smoothing
    def get_smooth_wr(groupby_col):
        stats = df.groupby(groupby_col)['deal_stage'].value_counts().unstack().fillna(0)
        if 'Won' not in stats: stats['Won'] = 0
        if 'Lost' not in stats: stats['Lost'] = 0
        stats['total'] = stats['Won'] + stats['Lost']
        return stats.apply(lambda x: bayesian_smooth_rate(x['Won'], x['total'], global_win_rate), axis=1)

    agent_wr_smooth = get_smooth_wr('sales_agent')
    product_wr_smooth = get_smooth_wr('product')
    sector_wr_smooth = get_smooth_wr('sector')

    # 3. Filter Open Opportunities
    open_stages = ['Prospecting', 'Engaging']
    df_open = df[df['deal_stage'].isin(open_stages)].copy()
    if df_open.empty: return df_open

    # 4. Dates and Age
    df['engage_date'] = pd.to_datetime(df['engage_date'], errors='coerce')
    current_date = df['engage_date'].max()
    if pd.isna(current_date):
        current_date = datetime.now()
        
    df_open['engage_date'] = pd.to_datetime(df_open['engage_date'], errors='coerce')
    df_open['deal_age'] = (current_date - df_open['engage_date']).dt.days.fillna(0).astype(int)
    
    # Map Smoothed Rates
    df_open['agent_wr'] = df_open['sales_agent'].map(agent_wr_smooth).fillna(global_win_rate)
    df_open['product_wr'] = df_open['product'].map(product_wr_smooth).fillna(global_win_rate)
    df_open['sector_wr'] = df_open['sector'].map(sector_wr_smooth).fillna(global_win_rate)

    # 5. Scoring Loop
    scores, reasons, next_actions, urgency_levels, risks, no_action_risks = [], [], [], [], [], []
    pressures, ignored_flags, strategic_insights, roi_potential, is_zombie = [], [], [], [], []
    should_be_closing, lost_attention = [], []

    # Thresholds
    DEAD_ZONE_THRESHOLD = 138

    for idx, row in df_open.iterrows():
        score = 0
        reason_list = []
        risk_list = []
        age = row['deal_age']
        stage = row['deal_stage']
        
        # Dead Zone Check
        zombie = (age > DEAD_ZONE_THRESHOLD)
            
        # Stage (20)
        if stage == 'Engaging':
            score += 20
            reason_list.append("estágio avançado")
        else:
            score += 10
            reason_list.append("prospecção ativa")
            
        # Win Rates (30)
        wr_score = (row['agent_wr'] * 10) + (row['product_wr'] * 10) + (row['sector_wr'] * 10)
        score += wr_score
        if wr_score > 20: reason_list.append("histórico favorável")
        elif wr_score < 10: risk_list.append("baixa probabilidade")

        # Account Size (15)
        rev = row.get('revenue', 0)
        if rev > 500:
            score += 10
            reason_list.append("conta estratégica")
        elif rev > 100: score += 5
        if row.get('employees', 0) > 1000:
            score += 5
            reason_list.append("empresa de grande porte")

        # Value (15)
        price = row.get('sales_price', 0)
        if price > 3000:
            score += 15
            reason_list.append("ticket premium")
        elif price > 1000: score += 10
        elif price > 500: score += 5

        # Momentum (20)
        momentum_score = 20
        if age > 180:
            momentum_score = 0
            risk_list.append("Estagnação crítica")
        elif age > 90:
            momentum_score = 10
            risk_list.append("Perda de momentum")
        else:
            reason_list.append("momentum positivo")
            
        score += momentum_score
        
        # Apply Zombie Penalty
        if zombie:
            score = score * 0.2
            reason_list = ["ZOMBIE ZONE (> 138 dias)"]
            
        score = min(100, max(0, score))
        scores.append(round(score, 1))
        is_zombie.append(zombie)
        
        # ROI Potential
        roi = price * (score / 100)
        roi_potential.append(roi)

        # Opportunity Pressure
        pressure = 0
        if score > 80 and age > 30: pressure += 20
        if score > 90: pressure += 10
        if age > 90: pressure += 15
        pressures.append(pressure)
        
        # Ignored Flag
        is_ignored = (score > 75 and age > 45)
        ignored_flags.append(is_ignored)

        # NEW: Should Be Closing Now
        closing_flag = (score > 80 and roi > 2000 and stage == 'Engaging' and age > 30)
        should_be_closing.append(closing_flag)
        
        # NEW: Lost Attention
        lost_att = (score > 80 and age > 60)
        lost_attention.append(lost_att)

        # Strategic Insight
        insight = "Fluxo padrão."
        if row['agent_wr'] > 0.6 and age > 60:
            insight = "Gap de Execução: Agente sênior com deal estagnado."
        elif row['product_wr'] < 0.2 and score > 80:
            insight = "Desafio de Produto: Baixa conversão para este produto em conta VIP."
        elif closing_flag:
            insight = "Receita Imediata: Deal em fase final com alto ROI ignorado."
        elif zombie:
            insight = "Zombie Zone: Risco de perda por inércia operacional."
        strategic_insights.append(insight)

        # Classification
        if zombie: classif, urgency, action = "Revisar / Zombie", "Baixa", "Arquivar ou re-qualificar"
        elif score >= 90: classif, urgency, action = "Atacar hoje", "Crítica", "Agendar call de fechamento"
        elif score >= 75: classif, urgency, action = "Prioridade da semana", "Alta", "Enviar proposta personalizada"
        elif score >= 50: classif, urgency, action = "Nutrir", "Média", "Enviar case de sucesso"
        else: classif, urgency, action = "Baixa prioridade", "Baixa", "Manter em cadência"
            
        reasons.append("; ".join(reason_list[:3]))
        next_actions.append(action)
        urgency_levels.append(urgency)
        risks.append("; ".join(risk_list) if risk_list else "Baixo risco")
        
    df_open['score'] = scores
    df_open['is_zombie'] = is_zombie
    df_open['roi_potential'] = roi_potential
    df_open['classification'] = [
        "Revisar / Zombie" if z else 
        ("Atacar hoje" if s >= 90 else 
         "Prioridade da semana" if s >= 75 else 
         "Nutrir" if s >= 50 else 
         "Baixa prioridade") for s, z in zip(scores, is_zombie)
    ]
    df_open['reason'] = reasons
    df_open['next_action'] = next_actions
    df_open['urgency'] = urgency_levels
    df_open['commercial_risk'] = risks
    df_open['opportunity_pressure'] = pressures
    df_open['deals_being_ignored'] = ignored_flags
    df_open['should_be_closing_now'] = should_be_closing
    df_open['lost_attention_flag'] = lost_attention
    df_open['strategic_insight'] = strategic_insights
    
    # NEW: Pipeline Insight per Agent/Manager
    # (Calculated in app.py for easier grouping, but adding placeholders here)
    df_open['suggested_message'] = df_open.apply(generate_suggested_message, axis=1)
    df_open['ai_decision_memo'] = df_open.apply(generate_ai_memo, axis=1)

    return df_open.sort_values(by='score', ascending=False)
