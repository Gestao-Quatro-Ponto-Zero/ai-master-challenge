"""Busca de sinais extras fora da amostra (rodar de solution/: python ../process-log/eda3_sinais.py)."""
import sys, datetime as dt, collections as C
sys.path.insert(0, '.')
import scorer as S
acc, prod, teams, deals = S.load()
closed = [d for d in deals if d['stage'] in ('Won', 'Lost')]
cut = dt.date(2017, 7, 1)
train = [d for d in closed if d['close'] < cut]; test = [d for d in closed if d['close'] >= cut]
y = [d['stage'] == 'Won' for d in test]
def a(name, f): print(f'{name:55s} AUC {S.auc([f(d) for d in test], y):.3f}')
won_pairs = {(d['account'], d['product']) for d in train if d['stage'] == 'Won'}
won_acc = {d['account'] for d in train if d['stage'] == 'Won'}
a('conta ja comprou este produto', lambda d: (d['account'], d['product']) in won_pairs)
load = C.Counter(d['agent'] for d in deals if d['engage'] and d['engage'] < cut)
a('carga do vendedor (menos deals = melhor)', lambda d: -load[d['agent']])
a('porte da conta (receita)', lambda d: float(acc[d['account']]['revenue']))
a('setor (taxa treino)', (lambda r: lambda d: r.get(acc[d['account']]['sector'], .63))({s: sum(d['stage']=='Won' for d in train if acc[d['account']]['sector']==s)/max(1,sum(1 for d in train if acc[d['account']]['sector']==s)) for s in {x['sector'] for x in acc.values()}}))
a('regiao (taxa treino)', (lambda r: lambda d: r[teams[d['agent']]['regional_office']])({g: sum(d['stage']=='Won' for d in train if teams[d['agent']]['regional_office']==g)/sum(1 for d in train if teams[d['agent']]['regional_office']==g) for g in ('East','West','Central')}))
a('preco do produto', lambda d: int(prod[d['product']]['sales_price']))
a('duracao do ciclo (so conhecida no fechamento)', S.cycle)
a('mes de fechamento e fim de trimestre', lambda d: d['close'].month % 3 == 0)
print('\nSobrevivencia treino vs teste: P(ganho | aberto >= t dias)')
for t in (0, 7, 14, 30, 60, 90, 120):
    r = lambda xs: (lambda s: f"{sum(d['stage']=='Won' for d in s)/len(s):.1%} (n={len(s)})")([d for d in xs if S.cycle(d) >= t])
    print(f'  t={t:3d}  treino {r(train):18s} teste {r(test)}')
