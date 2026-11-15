"""Backtest independente de priorizacao de oportunidades (parte 1 + parte 2).
Uso: python3 -I backtest.py <pasta dos dados>
"""
import csv, sys, random, datetime as dt
from collections import defaultdict

DATA = sys.argv[1].rstrip('/')
P = dt.date.fromisoformat
LIMITS = (14, 30, 45, 60, 75, 90, 105, 120, 138)
REPS = 20

# ---------- carga ----------
price = {}
for r in csv.DictReader(open(DATA + '/products.csv')):
    price[r['product']] = float(r['sales_price'])
deals = []
for r in csv.DictReader(open(DATA + '/sales_pipeline.csv')):
    if not r['engage_date']:
        continue
    prod = 'GTX Pro' if r['product'] == 'GTXPro' else r['product']
    won = r['deal_stage'] == 'Won'
    deals.append(dict(
        id=r['opportunity_id'], agent=r['sales_agent'], product=prod,
        e=P(r['engage_date']), c=P(r['close_date']) if r['close_date'] else None,
        won=won, cv=float(r['close_value']) if won else 0.0, price=price[prod]))

mondays = []
d = dt.date(2017, 3, 6)
while d <= dt.date(2017, 12, 25):
    mondays.append(d); d += dt.timedelta(days=7)

def band(a):
    for i, l in enumerate(LIMITS):
        if a <= l:
            return i
    return len(LIMITS)

def qstart(x):
    return dt.date(x.year, 3 * ((x.month - 1) // 3) + 1, 1)

def wq(x):
    return (x - qstart(x)).days // 7

def mq(x):
    return (x.month - 1) % 3

def snapshot(d):
    out = []
    for k in deals:
        if k['e'] < d and (k['c'] is None or k['c'] >= d):
            y = 1 if (k['won'] and k['c'] < d + dt.timedelta(days=30)) else 0
            out.append(dict(k, age=(d - k['e']).days, y=y, v=k['cv'] if y else 0.0))
    return out

SNAP = {m: snapshot(m) for m in mondays}
EVAL = [D for D in mondays if dt.date(2017, 7, 3) <= D <= dt.date(2017, 12, 1)]

def train(D):
    cw, cm, cb, g = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0]), [0, 0]
    for m in mondays:
        if m + dt.timedelta(days=30) <= D:
            for k in SNAP[m]:
                b = band(k['age'])
                for cell in (cw[(b, wq(m))], cm[(b, mq(m))], cb[b], g):
                    cell[0] += k['y']; cell[1] += 1
    return cw, cm, cb, g

MODELS = {D: train(D) for D in EVAL}

def chance(D, age, nmin=30, only_age=False):
    cw, cm, cb, g = MODELS[D]
    b = band(age)
    cells = [cb.get(b)] if only_age else [cw.get((b, wq(D))), cm.get((b, mq(D))), cb.get(b)]
    for c in cells:
        if c and c[1] >= nmin:
            return c[0] / c[1]
    return g[0] / g[1]

def maxcycle(D):
    return max((k['c'] - k['e']).days for k in deals if k['c'] is not None and k['c'] < D)

MAXC = {D: maxcycle(D) for D in EVAL}

# ---------- regras ----------
def rules_for(D, nmin=30):
    mc = MAXC[D]
    def key(name):
        if name == 'A':
            return lambda k: (-k['price'],)
        if name == 'B':
            return lambda k: (k['age'] > mc, -k['price'])
        if name == 'B_novo':
            return lambda k: (k['age'] > mc, -k['price'], k['age'])
        if name == 'B_velho':
            return lambda k: (k['age'] > mc, -k['price'], -k['age'])
        if name == 'C':
            return lambda k: (-chance(D, k['age'], nmin) * k['price'],)
        if name == 'C_idade':
            return lambda k: (-chance(D, k['age'], nmin, True) * k['price'],)
        if name == 'D':
            return lambda k: ()
        if name == 'E':
            return lambda k: (-k['v'],)
    return key

RULES = ['A', 'B', 'B_novo', 'B_velho', 'C', 'C_idade', 'D', 'E']

def run(topn=10, nmin=30, seed=12345, dates=None):
    """devolve res[D][rule] = (soma y, soma v) medias das reps; e por vendedor"""
    rng = random.Random(seed)
    res, per_agent, nlists = {}, defaultdict(lambda: defaultdict(float)), 0
    for D in (dates or EVAL):
        keyf = rules_for(D, nmin)
        byag = defaultdict(list)
        for k in SNAP[D]:
            byag[k['agent']].append(k)
        res[D] = {r: [0.0, 0.0] for r in RULES}
        for ag in sorted(byag):
            lst = byag[ag]
            if len(lst) < topn:
                continue
            nlists += 1
            for r in RULES:
                kf = keyf(r)
                sy = sv = 0.0
                for _ in range(REPS):
                    top = sorted(lst, key=lambda k: kf(k) + (rng.random(),))[:topn]
                    sy += sum(k['y'] for k in top); sv += sum(k['v'] for k in top)
                res[D][r][0] += sy / REPS; res[D][r][1] += sv / REPS
                per_agent[ag][r] += sv / REPS
    return res, per_agent, nlists

def tot(res, r, dates=None, i=1):
    return sum(res[D][r][i] for D in (dates or res))

def auc(scores_labels):
    s = sorted(scores_labels, key=lambda t: t[0])
    npos = sum(l for _, l in s); nneg = len(s) - npos
    rank_sum, i = 0.0, 0
    while i < len(s):
        j = i
        while j < len(s) and s[j][0] == s[i][0]:
            j += 1
        avg = (i + 1 + j) / 2.0
        rank_sum += avg * sum(l for _, l in s[i:j])
        i = j
    return (rank_sum - npos * (npos + 1) / 2) / (npos * nneg), len(s), npos, npos * nneg

def main():
    print('deals com engage_date:', len(deals))
    res, per_agent, nl = run()
    print('\n=== PARTE 1 ===')
    print('datas de avaliacao:', len(EVAL), EVAL[0], '->', EVAL[-1], '| listas:', nl)
    names = {'A': 'valor', 'B': 'valor sem parados', 'C': 'score', 'D': 'aleatorio', 'E': 'oraculo'}
    for r in 'ABCDE':
        print('%s %-18s vendas/lista=%.4f  receita=%d' % (r, names[r], tot(res, r, i=0) / nl, round(tot(res, r))))
    print('C/A=%.3f  C/B=%.3f' % (tot(res, 'C') / tot(res, 'A'), tot(res, 'C') / tot(res, 'B')))
    sl_c, sl_a, sl_p = [], [], []
    for D in EVAL:
        for k in SNAP[D]:
            sl_c.append((chance(D, k['age']), k['y']))
            sl_a.append((chance(D, k['age'], only_age=True), k['y']))
            sl_p.append((k['price'], k['y']))
    for nm, sl in (('chance item6', sl_c), ('so idade', sl_a), ('preco', sl_p)):
        a, n, npos, pairs = auc(sl)
        print('AUC %-13s %.3f  (obs deal x data=%d, positivos=%d, pares pos x neg=%d)' % (nm, a, n, npos, pairs))

    print('\n=== PARTE 2 ===')
    print('maior ciclo conhecido por D:', {str(D): MAXC[D] for D in EVAL})
    print('maior ciclo no dataset inteiro:', max((k['c'] - k['e']).days for k in deals if k['c']))
    print('\nSerie por data (receita A, B, C, B_novo, B_velho, oraculo) e listas:')
    winA = winB = 0
    for D in EVAL:
        a, b, c = res[D]['A'][1], res[D]['B'][1], res[D]['C'][1]
        winA += c > a; winB += c > b
        print(D, round(a), round(b), round(c), round(res[D]['B_novo'][1]), round(res[D]['B_velho'][1]), round(res[D]['E'][1]),
              '| C-A=%d C-B=%d' % (round(c - a), round(c - b)))
    print('C>A em %d/%d datas; C>B em %d/%d' % (winA, len(EVAL), winB, len(EVAL)))
    q3 = [D for D in EVAL if D.month <= 9]; q4 = [D for D in EVAL if D.month >= 10]
    for nm, ds in (('jul-set', q3), ('out-nov', q4)):
        print('%s (%d datas): A=%d B=%d C=%d  C/A=%.3f C/B=%.3f' % (nm, len(ds), tot(res, 'A', ds), tot(res, 'B', ds), tot(res, 'C', ds),
              tot(res, 'C', ds) / tot(res, 'A', ds), tot(res, 'C', ds) / tot(res, 'B', ds)))
    print('\nDesempate B: B(acaso)=%d B_novo=%d B_velho=%d | C/B_novo=%.3f C/B_velho=%.3f | C_idade=%d C_idade/A=%.3f'
          % (tot(res, 'B'), tot(res, 'B_novo'), tot(res, 'B_velho'), tot(res, 'C') / tot(res, 'B_novo'),
             tot(res, 'C') / tot(res, 'B_velho'), tot(res, 'C_idade'), tot(res, 'C_idade') / tot(res, 'A')))
    print('vendas/lista B_novo=%.4f B_velho=%.4f' % (tot(res, 'B_novo', i=0) / nl, tot(res, 'B_velho', i=0) / nl))

    print('\nTamanho da lista:')
    for n in (5, 10, 20):
        rr, _, nln = run(topn=n)
        print(' top%d listas=%d A=%d B=%d B2=%d C=%d D=%d E=%d C/A=%.3f C/B=%.3f C/B2=%.3f' % (
            n, nln, tot(rr, 'A'), tot(rr, 'B'), tot(rr, 'B_novo'), tot(rr, 'C'), tot(rr, 'D'), tot(rr, 'E'),
            tot(rr, 'C') / tot(rr, 'A'), tot(rr, 'C') / tot(rr, 'B'), tot(rr, 'C') / tot(rr, 'B_novo')))
    print('\nMinimo por celula:')
    for nmin in (10, 30, 100):
        rr, _, _ = run(nmin=nmin)
        sl = [(chance(D, k['age'], nmin), k['y']) for D in EVAL for k in SNAP[D]]
        print(' nmin=%d C=%d C/A=%.3f C/B=%.3f AUC=%.3f' % (nmin, tot(rr, 'C'), tot(rr, 'C') / tot(rr, 'A'), tot(rr, 'C') / tot(rr, 'B'), auc(sl)[0]))

    print('\nSementes (C/A, C/B) com 5 sementes do desempate:')
    for s in (1, 2, 3, 4, 5):
        rr, _, _ = run(seed=s)
        print(' seed %d: A=%d B=%d C=%d C/A=%.3f C/B=%.3f' % (s, tot(rr, 'A'), tot(rr, 'B'), tot(rr, 'C'), tot(rr, 'C') / tot(rr, 'A'), tot(rr, 'C') / tot(rr, 'B')))

    # bootstrap por data
    rng = random.Random(2024)
    ra, rb = [], []
    for _ in range(2000):
        ds = [rng.choice(EVAL) for _ in EVAL]
        a = sum(res[D]['A'][1] for D in ds); b = sum(res[D]['B'][1] for D in ds); c = sum(res[D]['C'][1] for D in ds)
        ra.append(c / a); rb.append(c / b)
    ra.sort(); rb.sort()
    print('\nBootstrap datas (2000, seed 2024): C/A IC95=[%.3f, %.3f] P(<=1)=%.3f ; C/B IC95=[%.3f, %.3f] P(<=1)=%.3f' % (
        ra[49], ra[1949], sum(x <= 1 for x in ra) / 2000, rb[49], rb[1949], sum(x <= 1 for x in rb) / 2000))

    # concentracao
    gainA = sorted(((res[D]['C'][1] - res[D]['A'][1], D) for D in EVAL), reverse=True)
    gainB = sorted(((res[D]['C'][1] - res[D]['B'][1], D) for D in EVAL), reverse=True)
    totA = sum(g for g, _ in gainA); totB = sum(g for g, _ in gainB)
    print('\nGanho total C-A=%d ; top3 datas=%d (%s)' % (totA, sum(g for g, _ in gainA[:3]), [str(D) for _, D in gainA[:3]]))
    print('Ganho total C-B=%d ; top3 datas=%d (%s)' % (totB, sum(g for g, _ in gainB[:3]), [str(D) for _, D in gainB[:3]]))
    ag = sorted(((per_agent[a]['C'] - per_agent[a]['A'], per_agent[a]['C'] - per_agent[a]['B'], a) for a in per_agent), reverse=True)
    print('vendedores: %d ; C>A em %d ; C>B em %d' % (len(ag), sum(x[0] > 0 for x in ag), sum(x[1] > 0 for x in ag)))
    print('top3 vendedores (ganho C-A, C-B):', [(round(x[0]), round(x[1]), x[2]) for x in ag[:3]])
    print('piores 3:', [(round(x[0]), round(x[1]), x[2]) for x in ag[-3:]])
    # leave-one-agent-out min ratios
    tA, tB, tC = tot(res, 'A'), tot(res, 'B'), tot(res, 'C')
    looA = min(((tC - per_agent[a]['C']) / (tA - per_agent[a]['A']), a) for a in per_agent)
    looB = min(((tC - per_agent[a]['C']) / (tB - per_agent[a]['B']), a) for a in per_agent)
    print('pior leave-one-agent-out: C/A=%.3f (sem %s) ; C/B=%.3f (sem %s)' % (looA[0], looA[1], looB[0], looB[1]))
    # top-2 agents removed
    top2 = [x[2] for x in ag[:2]]
    print('sem os 2 vendedores de maior ganho C-A: C/A=%.3f' % ((tC - sum(per_agent[a]['C'] for a in top2)) / (tA - sum(per_agent[a]['A'] for a in top2))))
    # leave-one-date-out
    print('pior leave-one-date-out: C/A=%.3f C/B=%.3f' % (
        min((tC - res[D]['C'][1]) / (tA - res[D]['A'][1]) for D in EVAL),
        min((tC - res[D]['C'][1]) / (tB - res[D]['B'][1]) for D in EVAL)))

if __name__ == '__main__':
    main()
