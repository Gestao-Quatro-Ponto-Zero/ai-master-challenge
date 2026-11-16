"""16 — Recalcula o "Churn Ratio" da aba Historico_Crescimento_Churn (V2) e o compara com a taxa mensal padrão. Uso: python -I 16_taxa_mensal_assinaturas.py <pasta_dados>"""
import sys, pandas as pd
s = pd.read_csv(f"{sys.argv[1]}/ravenstack_subscriptions.csv"); s["ini"] = pd.to_datetime(s.start_date); s["fim"] = pd.to_datetime(s.end_date)
ms = pd.date_range("2023-01-31", "2024-12-31", freq="ME"); rows = []
for t in ms:
    t0 = t - pd.offsets.MonthEnd(1)
    ativas_ini = ((s.ini <= t0) & (s.fim.isna() | (s.fim > t0))); ativas_fim = ((s.ini <= t) & (s.fim.isna() | (s.fim > t)))
    enc = (s.fim > t0) & (s.fim <= t); novas = (s.ini > t0) & (s.ini <= t)
    rows.append(dict(mes=t.strftime("%Y-%m"), ativas_fim=int(ativas_fim.sum()), encerradas_acum=int((s.fim <= t).sum()),
        ratio_V2=(s.fim <= t).sum()/max(ativas_fim.sum(),1), ativas_ini=int(ativas_ini.sum()), novas=int(novas.sum()), encerradas_mes=int(enc.sum()),
        taxa_mensal=enc.sum()/max(ativas_ini.sum(),1), mrr_perdido_pct=s[enc].mrr_amount.sum()/max(s[ativas_ini].mrr_amount.sum(),1), novas_por_encerrada=novas.sum()/max(enc.sum(),1)))
d = pd.DataFrame(rows).set_index("mes"); pd.set_option("display.width", 250)
print(d.to_string(float_format=lambda v: f"{v:.3f}"))
for y in ("2023","2024"):
    x = d[d.index.str.startswith(y)]; print(f"{y}: taxa mensal média {x.taxa_mensal.mean():.2%} | ponderada {x.encerradas_mes.sum()/x.ativas_ini.sum():.2%} | novas {x.novas.sum()} x encerradas {x.encerradas_mes.sum()}")
x = d.loc["2024-01":"2024-11"]; print(f"2024 sem dezembro: ponderada {x.encerradas_mes.sum()/x.ativas_ini.sum():.2%}")
