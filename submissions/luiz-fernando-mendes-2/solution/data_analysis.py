import pandas as pd
import numpy as np

# 1. Carregamento dos dados
# Certifique-se de que o caminho aponta para onde está o seu CSV
try:
    df = pd.read_csv('../data/sales_pipeline.csv')
except:
    df = pd.read_csv('sales_pipeline.csv')

# 2. Limpeza e conversão de datas
df['created_date'] = pd.to_datetime(df['created_date'])
df['close_date'] = pd.to_datetime(df['close_date'])

# 3. Cálculo do Ciclo de Venda (em dias)
df['cycle_days'] = (df['close_date'] - df['created_date']).dt.days

# 4. Filtrar apenas negócios fechados (Won ou Lost) para calcular Win Rate
closed_deals = df[df['deal_stage'].isin(['Won', 'Lost'])].copy()

# 5. Definição das Janelas Temporais para análise
bins = [0, 30, 120, 365, 1000]
labels = ['0-30 dias', '30-120 dias (Zona de Ouro)', '120-365 dias', 'Acima de 1 ano']
closed_deals['temp_group'] = pd.cut(closed_deals['cycle_days'], bins=bins, labels=labels)

# 6. Cálculo do Win Rate por Grupo
analysis = closed_deals.groupby('temp_group')['deal_stage'].value_counts(normalize=True).unstack().fillna(0)
analysis['win_rate'] = analysis['Won'] * 100

print("--- ANÁLISE DE DERIVAÇÃO DE DADOS (REV OPS) ---")
print("\nTaxa de Conversão (Win Rate) por Janela de Tempo:")
print(analysis[['Won', 'win_rate']])

# 7. Prova dos "229 leads de Alta Prioridade"
# Filtro baseado na lógica aplicada no Dashboard (Maturidade + Score Elevado)
high_priority = df[(df['deal_stage'] == 'Engaging') & 
                   (df['cycle_days'] >= 30) & 
                   (df['cycle_days'] <= 120)]

print(f"\nTotal de Leads na 'Zona de Ouro' (Engaging): {len(high_priority)}")
print("-" * 50)
