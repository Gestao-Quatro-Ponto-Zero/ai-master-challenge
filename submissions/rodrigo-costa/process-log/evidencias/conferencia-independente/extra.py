import sys, random, datetime as dt
from collections import defaultdict, Counter
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as B
res, pa, nl = B.run()
print('C_idade/B=%.3f C_idade/B_novo=%.3f' % (B.tot(res,'C_idade')/B.tot(res,'B'), B.tot(res,'C_idade')/B.tot(res,'B_novo')))
# parados no retrato e no top10 de A
rng = random.Random(7)
par_snap = par_A = par_C = tot_l = 0; won_par = 0
gtk = Counter()
for D in B.EVAL:
    mc = B.MAXC[D]
    by = defaultdict(list)
    for k in B.SNAP[D]:
        by[k['agent']].append(k)
        if k['age'] > mc: par_snap += 1; won_par += k['y']
    for ag, l in by.items():
        if len(l) < 10: continue
        tot_l += 1
        a = sorted(l, key=lambda k: (-k['price'], rng.random()))[:10]
        c = sorted(l, key=lambda k: (-B.chance(D, k['age'])*k['price'], rng.random()))[:10]
        par_A += sum(k['age'] > mc for k in a); par_C += sum(k['age'] > mc for k in c)
        for k in c:
            if k['y']: gtk[('C', k['product'])] += k['v']
        for k in a:
            if k['y']: gtk[('A', k['product'])] += k['v']
n = sum(len(B.SNAP[D]) for D in B.EVAL)
print('parados no retrato: %d de %d (%.1f%%), positivos entre parados=%d' % (par_snap, n, 100*par_snap/n, won_par))
print('parados por lista: A=%.2f C=%.2f' % (par_A/tot_l, par_C/tot_l))
print('receita por produto (1 sorteio):', sorted(gtk.items()))
# chance por faixa no ultimo modelo
cw, cm, cb, g = B.MODELS[B.EVAL[-1]]
print('taxa por faixa (modelo de 2017-11-27):', {b: (round(c[0]/c[1],3), c[1]) for b, c in sorted(cb.items())}, 'geral', round(g[0]/g[1],3))
cw, cm, cb, g = B.MODELS[B.EVAL[0]]
print('taxa por faixa (modelo de 2017-07-03):', {b: (round(c[0]/c[1],3), c[1]) for b, c in sorted(cb.items())})
print('celulas mes do trimestre (07-03):', {k: (round(c[0]/c[1],3), c[1]) for k, c in sorted(cm.items()) if k[0]==3})
# taxa de positivo por semana do trimestre em todas as segundas
wr = defaultdict(lambda: [0,0])
for m in B.mondays:
    for k in B.SNAP[m]:
        wr[B.wq(m)][0] += k['y']; wr[B.wq(m)][1] += 1
print('taxa y por semana do trimestre (todas as segundas):', {w: round(c[0]/c[1],3) for w, c in sorted(wr.items())})
# ciclos: distribuicao de close_date dentro do trimestre
cd = Counter(B.wq(k['c']) for k in B.deals if k['c'] and k['won'])
print('vendas por semana do trimestre do fechamento:', sorted(cd.items()))
# vazamento: quantas vezes o maior ciclo atingiu 138 pela primeira vez
first = min(k['c'] for k in B.deals if k['c'] and (k['c']-k['e']).days == 138)
print('primeiro fechamento com ciclo 138:', first)
print('quantos deals abertos no fim (sem close) com idade > 138 em 2017-12-31:', sum(1 for k in B.deals if k['c'] is None and (dt.date(2017,12,31)-k['e']).days > 138))
