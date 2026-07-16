import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
"""
Challenge 001 - Passo 10: robustez do metodo de MRR + cenarios de impacto em $.
(a) A tabela de assinaturas nunca fecha registros antigos, entao o MRR por conta
    depende de uma escolha de metodo. Aqui eu comparo os dois metodos e mostro
    o que resiste e o que muda.
(b) Cenarios de impacto: quanto vale, em ARR preservado, um programa de retencao
    proativa nas contas de maior valor.
"""
import pandas as pd

DATA = os.path.join(_ROOT, 'data')
sub = pd.read_csv(f'{DATA}/ravenstack_subscriptions.csv', parse_dates=['start_date','end_date'])
acc = pd.read_csv(f'{DATA}/ravenstack_accounts.csv')

sub['active'] = sub.end_date.isna()
print("="*80); print("(a) ROBUSTEZ DO METODO DE MRR"); print("="*80)
n_active = sub[sub.active].groupby('account_id').size()
print(f"contas com 2+ assinaturas 'ativas' simultaneas: {(n_active>=2).sum()} de {n_active.shape[0]}")
print("-> a tabela nunca encerra registros; somar 'ativas' contaria renovacoes em dobro.")
print("   Metodo principal do relatorio: assinatura mais recente por conta (proxy conservador).\n")

m_latest = sub.sort_values('start_date').groupby('account_id').tail(1).set_index('account_id').mrr_amount
m_sum    = sub[sub.active].groupby('account_id').mrr_amount.sum()
df = pd.DataFrame({'latest': m_latest, 'soma_ativas': m_sum}).dropna()
df = df.join(acc.set_index('account_id')[['churn_flag']])

print(f"correlacao de ranking entre metodos (Spearman): {df.latest.corr(df.soma_ativas, method='spearman'):.3f}")
for col in ['latest','soma_ativas']:
    s = df.sort_values(col, ascending=False)
    top20 = s.head(int(len(s)*0.2))[col].sum()/s[col].sum()
    share_churn = df.loc[df.churn_flag, col].sum()/df[col].sum()
    print(f"[{col:12s}] MRR total=${df[col].sum():>10,.0f} | top-20% concentra {top20:.0%} | fatia churnada {share_churn:.0%}")
act = df[~df.churn_flag]
t1 = set(act.sort_values('latest',ascending=False).head(25).index)
t2 = set(act.sort_values('soma_ativas',ascending=False).head(25).index)
print(f"overlap da watchlist top-25 entre metodos: {len(t1&t2)}/25")
print("CONCLUSAO: a fatia de receita churnada e ROBUSTA (~20-21% nos dois metodos);")
print("a concentracao e a composicao exata da watchlist dependem do metodo (declarado no relatorio).")

print("\n" + "="*80); print("(b) CENARIOS DE IMPACTO EM $ (retencao proativa no topo)"); print("="*80)
top100 = act.sort_values('latest', ascending=False).head(100)
mrr100 = top100.latest.sum(); arr100 = mrr100*12
print(f"top-100 contas ATIVAS por MRR: ${mrr100:,.0f}/mes  (ARR ${arr100:,.0f})")
base_churn = 0.12  # ~22% em 2 anos anualizado (ver relatorio, secao 1)
print(f"churn anualizado da base: ~{base_churn:.0%} (22% acumulado em 2 anos)")
print(f"\npremissas: churn de receita do top-100 = churn da base ({base_churn:.0%});")
print("custo de 2-3 CSMs dedicados: US$150k-240k/ano (mercado EUA); reducao de churn")
print("no grupo tratado vinda da literatura (health scoring proativo ~-23% churn, Totango).\n")
rows = [("conservador", 0.10, "-2 p.p. (reducao ~17%)"),
        ("base",        0.08, "-4 p.p. (reducao ~33%)"),
        ("otimista",    0.06, "-6 p.p. (reducao 50%)")]
print(f"{'cenario':<12} {'churn novo':<11} {'ARR preservado/ano':<20} {'custo CSM':<14} {'retorno liquido'}")
for nome, novo, obs in rows:
    saved = arr100*(base_churn-novo)
    cost_lo, cost_hi = 150_000, 240_000
    print(f"{nome:<12} {novo:<11.0%} ${saved:>12,.0f}       $150k-240k     ${saved-cost_hi:,.0f} a ${saved-cost_lo:,.0f}  ({obs})")
print("\n-> no cenario conservador o programa fica no zero-a-zero; nos cenarios base e otimista, se paga")
print("   com folga. Estes numeros vao na secao 6 do relatorio como ESTIMATIVA com premissas declaradas,")
print("   nao como previsao (dado sintetico, ver Limitacoes).")
