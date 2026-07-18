import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_csv("master_table.csv")

results = []

def add_result(h, title, content):
    results.append(f"### {h}: {title}\n{content}\n")

# H1: Uso cresce em volume mas se concentra em poucas features
growing_usage = df[df['usage_trend'] == 'Growing']
distinct_feat_growing = growing_usage['distinct_features'].mean()
distinct_feat_others = df[df['usage_trend'] != 'Growing']['distinct_features'].mean()
churn_growing_usage = growing_usage['churn_flag'].mean()
add_result("H1", "Volume vs Concentração de Features",
           f"Contas com 'Uso Crescente' usam em média {distinct_feat_growing:.1f} features distintas, vs {distinct_feat_others:.1f} para outras contas.\n"
           f"Taxa de churn para 'Uso Crescente': {churn_growing_usage:.1%}")

# H2: Taxa de erro correlaciona com tickets e churn
corr_error_tickets = df['total_error_count'].corr(df['num_tickets'])
error_churned = df[df['churn_flag'] == True]['total_error_count'].mean()
error_active = df[df['churn_flag'] == False]['total_error_count'].mean()
add_result("H2", "Erros vs Tickets e Churn",
           f"Correlação Pearson Erros x Tickets: {corr_error_tickets:.2f}\n"
           f"Média de erros em churned: {error_churned:.1f} | Em ativas: {error_active:.1f}")

# H3: Piora no tempo de resposta para churned
res_churned = df[df['churn_flag'] == True]['avg_resolution_hours'].mean()
res_active = df[df['churn_flag'] == False]['avg_resolution_hours'].mean()
frt_churned = df[df['churn_flag'] == True]['avg_first_response_mins'].mean()
frt_active = df[df['churn_flag'] == False]['avg_first_response_mins'].mean()
add_result("H3", "Tempo de Resposta",
           f"Tempo Médio de Resolução (h): Churned = {res_churned:.1f} | Ativas = {res_active:.1f}\n"
           f"First Response Time (m): Churned = {frt_churned:.1f} | Ativas = {frt_active:.1f}")

# H4: Downgrade como preditor de churn
churn_rate_downgrader = df[df['num_downgrades'] > 0]['churn_flag'].mean()
churn_rate_no_downgrade = df[df['num_downgrades'] == 0]['churn_flag'].mean()
add_result("H4", "Downgrade antes do Churn",
           f"Taxa de churn para contas com downgrade prévio: {churn_rate_downgrader:.1%}\n"
           f"Taxa de churn sem downgrade: {churn_rate_no_downgrade:.1%}")

# H5: Churn desproporcional por segmentos
churn_overall = df['churn_flag'].mean()
ch_ind = df.groupby('industry')['churn_flag'].mean().sort_values(ascending=False).head(2)
ch_src = df.groupby('referral_source')['churn_flag'].mean().sort_values(ascending=False).head(2)
add_result("H5", "Segmentos com Churn Desproporcional",
           f"Média global de churn: {churn_overall:.1%}\n"
           f"Piores indústrias:\n{ch_ind}\n"
           f"Piores canais:\n{ch_src}")

# H6: Reason codes vs realidade (Ex: Price vs Errors)
price_churners = df[(df['churn_flag'] == True) & (df['reason_code'].str.contains('Price|Cost|Budget', case=False, na=False))]
other_churners = df[(df['churn_flag'] == True) & (~df['reason_code'].str.contains('Price|Cost|Budget', case=False, na=False))]
add_result("H6", "Reason Code 'Preço' vs Realidade",
           f"Média de erros para churn por 'Preço': {price_churners['total_error_count'].mean():.1f}\n"
           f"Média de erros para outros churns: {other_churners['total_error_count'].mean():.1f}\n"
           f"Média CSAT para churn por 'Preço': {price_churners['avg_csat'].mean():.2f}")

# H7: Features Beta e Erros
err_beta = df[df['used_beta'] == True]['total_error_count'].mean()
err_no_beta = df[df['used_beta'] == False]['total_error_count'].mean()
churn_beta = df[df['used_beta'] == True]['churn_flag'].mean()
churn_no_beta = df[df['used_beta'] == False]['churn_flag'].mean()
add_result("H7", "Features Beta vs Erros e Churn",
           f"Média de erros (Usuários Beta): {err_beta:.1f} | Não Beta: {err_no_beta:.1f}\n"
           f"Taxa de churn (Usuários Beta): {churn_beta:.1%} | Não Beta: {churn_no_beta:.1%}")

with open('phase3_results.txt', 'w', encoding='utf-8') as f:
    f.writelines(results)
