from common import *
d = load()
c = d[d.closed]
em = d.engage_date.dt.to_period("M"); cm = d.close_date.dt.to_period("M")
print("N por mes inicio x mes fechamento"); print(pd.crosstab(em, cm))
print("WR por mes inicio x mes fechamento"); print(c.pivot_table(index=em, columns=cm, values="won", aggfunc="mean").round(2))
print("never closed share por mes inicio"); print((~d[d.engage_date.notna()].closed).groupby(em).mean().round(3))
# dia do mes de fechamento
print(c.groupby(c.close_date.dt.day).agg(n=("won","size"), wr=("won","mean")).T.round(2))
print(c.groupby(c.close_date.dt.dayofweek).agg(n=("won","size"), wr=("won","mean")).round(3))
print(d.groupby(d.engage_date.dt.dayofweek).agg(n=("won","size"), wr=("won","mean"), zombie=("closed", lambda s: 1-s.mean())).round(3))
print(d.groupby(d.engage_date.dt.day).agg(n=("won","size"), wr=("won","mean"), zombie=("closed", lambda s: 1-s.mean())).round(3).T)
# cycle distribution won vs lost
bins=[0,3,7,14,21,30,45,60,75,90,105,120,140]
print(pd.crosstab(pd.cut(c.cycle,bins), c.deal_stage))
# position in quarter of engage
d["eq_day"] = (d.engage_date - d.engage_date.dt.to_period("Q").dt.start_time).dt.days
print(d[d.engage_date>="2017-01-01"].groupby(pd.cut(d.eq_day,[-1,14,29,44,59,74,92])).agg(n=("won","size"), closed=("closed","mean"), wr=("won","mean"), cyc=("cycle","median")).round(3))
