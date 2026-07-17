import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Usa DATASET_DIR do env (Docker) ou relativo (local)
DATASET_DIR = os.environ.get('DATASET_DIR', os.path.join(BASE_DIR, 'dataset'))

def load_data():
    accounts = pd.read_csv(os.path.join(DATASET_DIR, 'accounts.csv'))
    products = pd.read_csv(os.path.join(DATASET_DIR, 'products.csv'))
    sales_teams = pd.read_csv(os.path.join(DATASET_DIR, 'sales_teams.csv'))
    pipeline = pd.read_csv(os.path.join(DATASET_DIR, 'sales_pipeline.csv'))
    
    df = pipeline.merge(accounts, on='account', how='left')
    df = df.merge(products, on='product', how='left')
    df = df.merge(sales_teams, on='sales_agent', how='left')
    
    df['engage_date'] = pd.to_datetime(df['engage_date'])
    df['close_date'] = pd.to_datetime(df['close_date'])
    
    df['valor_esperado'] = df['close_value'].fillna(df['sales_price']).fillna(0)
    
    simulated_today = pd.to_datetime('2017-12-31')
    df['dias_no_funil'] = (df['close_date'].fillna(simulated_today) - df['engage_date']).dt.days
    
    return df

def calculate_score(row):
    score = 40
    explicacoes = []
    tags = []
    
    # 1. Lógica de Estágio (Sinal Quente)
    if row['deal_stage'] == 'Engaging':
        score += 20
        explicacoes.append("🟢 +20 pts: O cliente respondeu e está engajado na negociação.")
        if pd.notna(row['dias_no_funil']) and row['dias_no_funil'] < 10:
            tags.append("🔥 SINAL QUENTE")
    elif row['deal_stage'] == 'Prospecting':
        explicacoes.append("⚪ +0 pts: A oportunidade ainda está em fase de prospecção fria.")
        
    # 2. Lógica de Produto
    if row['product'] in ['MG Special', 'GTX Plus Pro']:
        score += 10
        explicacoes.append(f"🟢 +10 pts: Produto Premium ({row['product']}) possui alta conversão histórica (65%).")
    else:
        explicacoes.append(f"⚪ O produto {row['product']} possui conversão padrão.")
        
    # 3. Lógica de Setor
    if pd.notna(row['sector']):
        if row['sector'] in ['marketing', 'software', 'entertainment']:
            score += 10
            explicacoes.append(f"🟢 +10 pts: O setor de {row['sector'].capitalize()} está altamente aquecido e tem ciclo mais rápido.")
        
    # 4. Burocracia e Faturamento Ideal (Sweet Spot)
    if pd.notna(row['revenue']):
        if 1500 <= row['revenue'] <= 3000:
            score += 10
            explicacoes.append("🟢 +10 pts: Cliente no 'Sweet Spot' (Faturamento Médio). Contato mais direto com os decisores.")
        elif row['revenue'] > 3000:
            explicacoes.append("🟡 Empresa Enterprise. O comitê de compras maior pode atrasar o fechamento.")
            
    # 5. Penalidade de Estagnação
    dias = row['dias_no_funil']
    if pd.notna(dias):
        if dias > 85:
            score -= 20
            explicacoes.append(f"🔴 -20 pts: Estagnação Absoluta! O lead está aberto há {int(dias)} dias (o limite de sucesso na base é 85).")
            tags.append("🚨 ESTAGNADO")
        elif row['deal_stage'] == 'Prospecting' and dias > 20:
            score -= 10
            explicacoes.append(f"🔴 -10 pts: Prospecção sem resposta há {int(dias)} dias.")
            tags.append("🚨 SEM RESPOSTA")
            
    # Sugestão de Ação
    action = "Continuar follow-up consultivo."
    if "🚨 SEM RESPOSTA" in tags:
        action = "Acionar IA Auto-Responder para tentar reacender o contato, ou marcar como Perdido."
    elif "🚨 ESTAGNADO" in tags:
        action = "Ligar diretamente para o tomador de decisão final."
    elif "🔥 SINAL QUENTE" in tags:
        action = "Entrar em contato AGORA! O lead acabou de interagir."
    elif score > 70:
        action = "Focar em preparar proposta comercial e agendar reunião final."
        
    score = max(0, min(100, score))
    
    return {
        'pontuacao': score,
        'explicacoes': explicacoes,
        'tags': tags,
        'acao_sugerida': action
    }

def get_scored_pipeline(agent_name=None):
    df = load_data()
    active = df[df['deal_stage'].isin(['Prospecting', 'Engaging'])].copy()
    
    if agent_name:
        active = active[active['sales_agent'] == agent_name]
        
    scores_data = active.apply(calculate_score, axis=1)
    
    active['pontuacao'] = [x['pontuacao'] for x in scores_data]
    active['explicacoes'] = [x['explicacoes'] for x in scores_data]
    active['tags'] = [x['tags'] for x in scores_data]
    active['acao_sugerida'] = [x['acao_sugerida'] for x in scores_data]
    
    active = active.sort_values(by='pontuacao', ascending=False)
    
    active = active.astype(object).where(pd.notnull(active), None)
    
    return active.to_dict(orient='records')
