import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
"""
Challenge 001 — Passo 4: churn ponderado por RECEITA + watchlist honesta.
Como churn e imprevisivel (AUC~0.5), a watchlist ranqueia por RECEITA-EM-RISCO
(nao por probabilidade fake) + sinais fracos de atencao para contato humano.
"""
import pandas as pd, numpy as np
pd.set_option('display.width',200); pd.set_option('display.max_columns',60)
DATA=os.path.join(_ROOT,'data')
OUT =os.path.join(_ROOT,'solution','outputs')
m = pd.read_csv(f'{OUT}/account_master_clean.csv')

print("="*80); print("CHURN: CONTAGEM vs RECEITA"); print("="*80)
tot_accts=len(m); churned=m[m.churn_flag]; active=m[~m.churn_flag]
print(f"churn por contagem: {m.churn_flag.mean():.1%} ({len(churned)}/{tot_accts})")
print(f"MRR perdido (churnados): ${churned.mrr_amount.sum():,.0f}/mes | ARR ${churned.arr_amount.sum():,.0f}")
print(f"MRR total da base:       ${m.mrr_amount.sum():,.0f}/mes")
print(f"churn por RECEITA (MRR churnado / MRR total): {churned.mrr_amount.sum()/m.mrr_amount.sum():.1%}")

# concentracao de receita (regra 80/20) — onde focar retencao
mm = m.sort_values('mrr_amount', ascending=False)
mm['cum_mrr_pct'] = mm.mrr_amount.cumsum()/mm.mrr_amount.sum()
top20n = int(len(mm)*0.2)
print(f"\nConcentracao: top 20% das contas ({top20n}) = {mm.head(top20n).mrr_amount.sum()/mm.mrr_amount.sum():.0%} do MRR")

print("\n--- churn por faixa de valor (MRR) ---")
m['tier'] = pd.cut(m.mrr_amount, [-1,0,1000,2500,100000], labels=['$0 (trial/free)','$1-1k','$1k-2.5k','$2.5k+'])
g = m.groupby('tier', observed=True).agg(contas=('account_id','count'),
        churn_rate=('churn_flag', lambda s: round(s.mean()*100,1)),
        MRR_em_risco_ativo=('account_id', lambda idx: 0))
# MRR em risco entre ATIVOS por tier
risco = active.groupby(pd.cut(active.mrr_amount,[-1,0,1000,2500,100000],
        labels=['$0 (trial/free)','$1-1k','$1k-2.5k','$2.5k+']), observed=True).mrr_amount.sum()
g['MRR_ativo_no_tier'] = risco.astype(int)
print(g.to_string())

print("\n" + "="*80); print("WATCHLIST — contas ATIVAS priorizadas por RECEITA-EM-RISCO + sinais fracos"); print("="*80)
w = active.copy()
# sinais fracos de atencao (transparentes, NAO um modelo preditivo)
peer_usage = active.usage_events.median()
w['flag_escalation']   = (w.escalations.fillna(0) > 0).astype(int)
w['flag_low_usage']    = (w.usage_events.fillna(0) < peer_usage*0.5).astype(int)
w['flag_no_autorenew'] = (~w.auto_renew_flag.astype(bool)).astype(int)
w['flag_trial']        = (w.is_trial.astype(bool)).astype(int)
w['flag_lowsat']       = (w.avg_satisfaction.fillna(5) <= 3).astype(int)
flag_cols=['flag_escalation','flag_low_usage','flag_no_autorenew','flag_trial','flag_lowsat']
w['attention_flags'] = w[flag_cols].sum(axis=1)
# prioridade = receita-em-risco (MRR) ponderada por atencao (transparente)
w['priority_score'] = w.mrr_amount * (1 + 0.15*w.attention_flags)
w = w.sort_values('priority_score', ascending=False)
cols_show=['account_id','account_name','industry','mrr_amount','arr_amount','attention_flags',
           'flag_escalation','flag_low_usage','flag_no_autorenew','flag_trial','flag_lowsat']
watch = w[cols_show].head(25).reset_index(drop=True)
print(watch.to_string())
watch.to_csv(f'{OUT}/watchlist_top25.csv', index=False)
w[cols_show+['priority_score']].to_csv(f'{OUT}/watchlist_full.csv', index=False)
print(f"\nMRR coberto pela watchlist top-25: ${watch.mrr_amount.sum():,.0f}/mes "
      f"({watch.mrr_amount.sum()/active.mrr_amount.sum():.0%} do MRR ativo)")
print("Salvos: watchlist_top25.csv, watchlist_full.csv")
