# Sensibilidade ao horizonte do rotulo (30/60/90 dias): rotulo e treino com o mesmo horizonte H.
import sys, os, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as B
B.REPS = 10
for H in (30, 60, 90):
    def snap(d, H=H):
        out = []
        for k in B.deals:
            if k['e'] < d and (k['c'] is None or k['c'] >= d):
                y = 1 if (k['won'] and k['c'] < d + dt.timedelta(days=H)) else 0
                out.append(dict(k, age=(d - k['e']).days, y=y, v=k['cv'] if y else 0.0))
        return out
    B.SNAP = {m: snap(m) for m in B.mondays}
    ev = [D for D in B.EVAL if D + dt.timedelta(days=H) <= dt.date(2018, 1, 1)]
    from collections import defaultdict
    def train(D, H=H):
        cw, cm, cb, g = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0]), [0, 0]
        for m in B.mondays:
            if m + dt.timedelta(days=H) <= D:
                for k in B.SNAP[m]:
                    b = B.band(k['age'])
                    for cell in (cw[(b, B.wq(m))], cm[(b, B.mq(m))], cb[b], g):
                        cell[0] += k['y']; cell[1] += 1
        return cw, cm, cb, g
    B.MODELS = {D: train(D) for D in ev}
    res, _, nl = B.run(dates=ev)
    t = lambda r: B.tot(res, r)
    print('H=%d datas=%d listas=%d A=%d B=%d C=%d C/A=%.3f C/B=%.3f' % (H, len(ev), nl, t('A'), t('B'), t('C'), t('C')/t('A'), t('C')/t('B')))
