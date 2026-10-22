"""
RavenStack | Ferramenta de CS: fila de contas em risco com ações por conta
---------------------------------------------------------------------------
Uso (a cada ciclo, por exemplo todo mês):
    python churn_model.py                      # gera model_scores_<data>.csv (risco de churn em 90 dias)
    python cs_risk_tool.py [csvs] [saida] [data]

Entradas: os 5 CSVs do RavenStack e model_scores_<data>.csv.
Saídas:
    cs_fila_acoes.csv      uma linha por conta ativa, ordenada por prioridade, com gatilhos e ações
    cs_gatilhos.csv        uma linha por (conta, gatilho), com a evidência que disparou cada um
    cs_tickets_contexto.csv tickets dos últimos 90 dias das contas da fila
    cs_regras.csv          as regras usadas, com a base de cada uma nos dados

Regras de honestidade:
- A PRIORIDADE vem só do modelo de idade da conta, o único fator que previu churn
  num período que o modelo não viu (AUC 0,645).
- Os demais gatilhos são fatos da conta que dão motivo e assunto ao contato.
  Sozinhos, eles NÃO anteciparam churn nos dados; cada regra traz esse aviso.
- Nenhuma ação tem efeito comprovado sobre o churn: os dados não têm registro de ações do CS.
- Limiares são percentis calculados nos próprios dados, não metas escolhidas.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DATA as _DATA, OUT as _OUT
import sys, numpy as np, pandas as pd
IN  = sys.argv[1] if len(sys.argv) > 1 else _DATA
OUT = sys.argv[2] if len(sys.argv) > 2 else _OUT
D   = pd.Timestamp(sys.argv[3] if len(sys.argv) > 3 else '2025-01-01')

a = pd.read_csv(f'{IN}/ravenstack_accounts.csv', parse_dates=['signup_date'])
s = pd.read_csv(f'{IN}/ravenstack_subscriptions.csv', parse_dates=['start_date','end_date'])
f = pd.read_csv(f'{IN}/ravenstack_feature_usage.csv', parse_dates=['usage_date'])
t = pd.read_csv(f'{IN}/ravenstack_support_tickets.csv', parse_dates=['submitted_at','closed_at'])
sc = pd.read_csv(f'{OUT}/model_scores_{D:%Y-%m-%d}.csv')

# ---------- limiares tirados dos próprios dados ----------
P75_RESOL = t.resolution_time_hours.quantile(.75)
P75_RESP  = t.first_response_time_minutes.quantile(.75)
u = f.merge(s[['subscription_id','account_id']], on='subscription_id').merge(a[['account_id','signup_date']], on='account_id')
u = u[(u.usage_date >= u.signup_date) & (u.usage_date <= D)]          # só uso válido, até a data
dd = (D - u.usage_date).dt.days
uso90  = u[dd < 90].groupby('account_id').usage_count.sum()
uso90a = u[(dd >= 90) & (dd < 180)].groupby('account_id').usage_count.sum()
ult_uso = u.groupby('account_id').usage_date.max()
ativas = sc.account_id
dias_sem_uso = (D - ult_uso.reindex(ativas)).dt.days
P75_SEM_USO = dias_sem_uso.quantile(.75)
svp = s[(s.start_date <= D) & (s.end_date.isna() | (s.end_date > D)) & (~s.is_trial)]
pct_sem_renov = (svp[~svp.auto_renew_flag].groupby('account_id').mrr_amount.sum() / svp.groupby('account_id').mrr_amount.sum()).reindex(ativas).fillna(0)
P75_SEM_RENOV = pct_sem_renov.quantile(.75)

# ---------- regras ----------
REGRAS = [
 dict(id='R1', gatilho='Conta nova (até 90 dias)', acao='Fazer contato de acompanhamento do início de uso',
      base='Contas com até 30 dias tiveram 50% de churn em 90 dias no período de teste, contra 18% nas com mais de um ano', preditor='sim'),
 dict(id='R2', gatilho='Ticket escalado nos últimos 90 dias', acao='Revisar com o cliente o ticket escalado e confirmar a solução',
      base='Fato da conta. Sozinho, não antecedeu churn: escalação 5,1% vs 4,0% (p = 0,33)', preditor='não'),
 dict(id='R3', gatilho='Ticket urgente ou alto nos últimos 90 dias', acao='Confirmar que o problema urgente foi resolvido',
      base='Fato da conta. Sozinho, não antecedeu churn: tickets em 90 dias 0,53 vs 0,52 (p = 0,76)', preditor='não'),
 dict(id='R4', gatilho=f'Resolução acima do percentil 75 ({P75_RESOL:.0f} h) ou 1ª resposta acima do percentil 75 ({P75_RESP:.0f} min)',
      acao='Retomar o caso que demorou e perguntar se ficou pendência', base='Fato da conta. Tempo de resolução não diferiu entre quem saiu e quem ficou (p = 0,70)', preditor='não'),
 dict(id='R5', gatilho='Ticket dos últimos 90 dias sem nota de satisfação', acao='Pedir a avaliação do atendimento',
      base='41,2% dos tickets não têm nota: cada nota coletada reduz essa lacuna', preditor='não'),
 dict(id='R6', gatilho='Nota de satisfação 3 (a menor que aparece nos dados)', acao='Perguntar o que faltou no atendimento',
      base='Fato da conta. CSAT não diferiu entre quem saiu e quem ficou (p = 0,83)', preditor='não'),
 dict(id='R7', gatilho='Downgrade em assinatura iniciada nos últimos 90 dias', acao='Entender o motivo da redução de plano',
      base='Fato da conta. Sozinho, não antecedeu churn: 73,4% vs 68,7% (p = 0,32)', preditor='não'),
 dict(id='R8', gatilho=f'Parcela do MRR vigente sem renovação automática acima do percentil 75 das contas ativas ({100*P75_SEM_RENOV:.0f}%)', acao='Confirmar a intenção de renovar',
      base='Fato da conta. Auto-renovação não diferiu entre assinaturas encerradas e ativas (p = 0,98)', preditor='não'),
 dict(id='R9', gatilho=f'Uso válido 40% menor que nos 90 dias anteriores, ou sem uso há mais de {P75_SEM_USO:.0f} dias (percentil 75)',
      acao='Verificar a adoção do produto com o cliente', base='Fato da conta. Sozinho, não antecedeu churn: 50,0% vs 56,8% (p = 0,56)', preditor='não'),
]
R = pd.DataFrame(REGRAS)

# ---------- avaliar cada conta ----------
tk = t[t.submitted_at <= D].copy(); tk['dias'] = (D - tk.submitted_at).dt.days
t90 = tk[tk.dias < 90]
sv = s[(s.start_date <= D) & (s.end_date.isna() | (s.end_date > D))]
G = []
def add(acc, rid, evid): G.append(dict(account_id=acc, regra=rid, evidencia=evid))
for _, c in sc.iterrows():
    acc = c.account_id; tt = t90[t90.account_id == acc]
    if c.idade_dias <= 90: add(acc,'R1', f'{int(c.idade_dias)} dias desde o cadastro')
    e = tt[tt.escalation_flag]
    if len(e): add(acc,'R2', '; '.join(f'{r.ticket_id} ({r.submitted_at:%d/%m}, {r.priority})' for r in e.itertuples()))
    ur = tt[tt.priority.isin(['urgent','high'])]
    if len(ur): add(acc,'R3', '; '.join(f'{r.ticket_id} ({r.submitted_at:%d/%m}, {r.priority})' for r in ur.itertuples()))
    lo = tt[(tt.resolution_time_hours > P75_RESOL) | (tt.first_response_time_minutes > P75_RESP)]
    if len(lo): add(acc,'R4', '; '.join(f'{r.ticket_id} ({r.resolution_time_hours:.0f} h, 1ª resp. {r.first_response_time_minutes} min)' for r in lo.itertuples()))
    sn = tt[tt.satisfaction_score.isna()]
    if len(sn): add(acc,'R5', '; '.join(f'{r.ticket_id} ({r.submitted_at:%d/%m})' for r in sn.itertuples()))
    c3 = tt[tt.satisfaction_score == 3]
    if len(c3): add(acc,'R6', '; '.join(f'{r.ticket_id} ({r.submitted_at:%d/%m})' for r in c3.itertuples()))
    ss = s[(s.account_id == acc) & (s.start_date <= D)]
    dg = ss[ss.downgrade_flag & ((D - ss.start_date).dt.days < 90)]
    if len(dg): add(acc,'R7', '; '.join(f'{r.subscription_id} ({r.plan_tier}, início {r.start_date:%d/%m/%Y})' for r in dg.itertuples()))
    ar = sv[(sv.account_id == acc) & (~sv.is_trial) & (~sv.auto_renew_flag)]
    if pct_sem_renov.get(acc, 0) > P75_SEM_RENOV: add(acc,'R8', f'{100*pct_sem_renov[acc]:.0f}% do MRR vigente sem renovação automática ({len(ar)} assinatura(s), US$ {ar.mrr_amount.sum():,.0f})')
    a90, b90 = uso90.get(acc, 0), uso90a.get(acc, 0); dsu = dias_sem_uso.get(acc, np.nan)
    if (b90 > 0 and (a90 - b90) / b90 < -0.4) or (pd.notna(dsu) and dsu > P75_SEM_USO):
        partes = []
        if b90 > 0 and (a90 - b90) / b90 < -0.4: partes.append(f'uso 90 dias {int(a90)} vs {int(b90)} antes ({100*(a90-b90)/b90:+.0f}%)')
        if pd.notna(dsu) and dsu > P75_SEM_USO: partes.append(f'{int(dsu)} dias sem uso')
        add(acc,'R9', '; '.join(partes))
G = pd.DataFrame(G).merge(R[['id','gatilho','acao','base','preditor']], left_on='regra', right_on='id').drop(columns='id')

# ---------- fila ----------
Q = sc[['account_id','industry','referral_source','plan_tier','idade_dias','mrr_vivo','prob_churn_90d','faixa_risco','mrr_esperado_em_risco']].copy()
gg = G.groupby('account_id')
Q['n_gatilhos'] = Q.account_id.map(gg.size()).fillna(0).astype(int)
Q['gatilhos'] = Q.account_id.map(gg.regra.apply(lambda x: ', '.join(sorted(x)))).fillna('')
Q['acoes_sugeridas'] = Q.account_id.map(gg.acao.apply(lambda x: ' | '.join(x))).fillna('Sem gatilho: acompanhar pela faixa de risco')
Q['tickets_90d'] = Q.account_id.map(t90.groupby('account_id').size()).fillna(0).astype(int)
Q['ultimo_ticket'] = Q.account_id.map(tk.groupby('account_id').submitted_at.max()).dt.strftime('%Y-%m-%d')
Q = Q.sort_values(['mrr_esperado_em_risco','prob_churn_90d'], ascending=False).reset_index(drop=True)
Q.insert(0, 'prioridade', np.arange(1, len(Q) + 1))
Q['data_referencia'] = f'{D:%Y-%m-%d}'

ctx = t90[t90.account_id.isin(Q.account_id)].sort_values(['account_id','submitted_at'], ascending=[True,False])
ctx = ctx[['account_id','ticket_id','submitted_at','priority','escalation_flag','resolution_time_hours','first_response_time_minutes','satisfaction_score']].copy()
ctx['submitted_at'] = ctx.submitted_at.dt.strftime('%Y-%m-%d')

R['contas_acionadas'] = R.id.map(G.groupby('regra').account_id.nunique()).fillna(0).astype(int)
R.to_csv(f'{OUT}/cs_regras.csv', index=False)
G.to_csv(f'{OUT}/cs_gatilhos.csv', index=False)
Q.to_csv(f'{OUT}/cs_fila_acoes.csv', index=False)
ctx.to_csv(f'{OUT}/cs_tickets_contexto.csv', index=False)
print(f'Fila de {D:%d/%m/%Y}: {len(Q)} contas | com gatilho: {(Q.n_gatilhos>0).sum()} | MRR esperado em risco: US$ {Q.mrr_esperado_em_risco.sum():,.0f}')
print(R[['id','gatilho','contas_acionadas']].to_string(index=False))
print(Q.head(8)[['prioridade','account_id','idade_dias','mrr_vivo','prob_churn_90d','faixa_risco','mrr_esperado_em_risco','gatilhos']].to_string(index=False))
