"""21 — Checagem dos pontos do relatório (D51) e lista de contas para o CS.

Uso: python -I 21_sinais_e_contas.py [caminho_do_banco]
Padrão: ../../solution/app/data/ravenstack.db (o banco gerado por solution/sql/build_db.py, commitado na D48).
Saídas: outputs/21_sinais_e_contas.txt (este print) e ../../solution/contas-em-risco.csv.
Só a biblioteca padrão do Python: os testes qui-quadrado são calculados aqui mesmo.
"""
import csv, math, os, sqlite3, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "..", "..", "solution", "app", "data", "ravenstack.db")
SAIDA_CSV = os.path.join(AQUI, "..", "..", "solution", "contas-em-risco.csv")
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
q = lambda s, *a: c.execute(s, a).fetchall()
CORTE = q("select valor from parametros where nome='data_corte'")[0][0][:10]


def chi2_sf(x, df):
    """P(X > x) para qui-quadrado com df graus de liberdade (gama incompleta regularizada)."""
    if x <= 0:
        return 1.0
    a, z = df / 2, x / 2
    if z < a + 1:  # série
        s = t = 1 / a
        k = a
        while abs(t) > 1e-14 * abs(s):
            k += 1
            t *= z / k
            s += t
        return 1 - s * math.exp(-z + a * math.log(z) - math.lgamma(a))
    b, cc, d = z + 1 - a, 1e300, 1 / (z + 1 - a)  # fração contínua
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2
        d = 1 / (an * d + b)
        cc = b + an / cc
        h *= d * cc
        if abs(d * cc - 1) < 1e-14:
            break
    return h * math.exp(-z + a * math.log(z) - math.lgamma(a))


def chi2_tabela(t):
    lin = [sum(r) for r in t]
    col = [sum(x) for x in zip(*t)]
    n = sum(lin)
    x = sum((t[i][j] - lin[i] * col[j] / n) ** 2 / (lin[i] * col[j] / n) for i in range(len(t)) for j in range(len(col)))
    return x, chi2_sf(x, (len(t) - 1) * (len(col) - 1))


def taxa_vs_resto(nome, g, r):
    x, p = chi2_tabela([[g[0], g[1] - g[0]], [r[0], r[1] - r[0]]])
    print(f"  {nome}: {g[0]}/{g[1]} = {g[0]/g[1]:.1%}  ×  resto {r[0]}/{r[1]} = {r[0]/r[1]:.1%}   qui2 = {x:.2f}  p = {p:.3f}")
    return p


print(f"banco: {os.path.relpath(DB, AQUI)}   data de corte: {CORTE}")

print("\n=== 1. Trial × pago (churn_flag da conta, D36)")
for t, n, ch in q("select is_trial, count(*), sum(churn_flag) from accounts group by 1"):
    print(f"  {'trial' if t else 'pago '}: {n} contas ({n/500:.1%} da base), {ch} com churn ({ch/110:.1%} do churn), taxa {ch/n:.1%}")
tr = q("select sum(churn_flag), count(*) from accounts where is_trial=1")[0]
pg = q("select sum(churn_flag), count(*) from accounts where is_trial=0")[0]
taxa_vs_resto("trial × pago", tr, pg)

print("\n=== 2. Setor (churn_flag)")
for ind, n, ch in q("select industry, count(*), sum(churn_flag) from accounts group by 1 order by 1.0*sum(churn_flag)/count(*) desc"):
    print(f"  {ind:14s} {ch:3d}/{n:3d} = {ch/n:.1%}")
x, p = chi2_tabela([[ch, n - ch] for _, n, ch in q("select industry, count(*), sum(churn_flag) from accounts group by 1")])
print(f"  5 setores juntos: qui2 = {x:.2f}  p = {p:.3f}")
p = taxa_vs_resto("DevTools × resto", q("select sum(churn_flag), count(*) from accounts where industry='DevTools'")[0],
                  q("select sum(churn_flag), count(*) from accounts where industry<>'DevTools'")[0])
print(f"  com Bonferroni (5 setores testados): p = {min(1, 5 * p):.3f}")
print("  o que os DevTools têm de diferente (taxa de erro %, escalação % dos tickets, satisfação, tickets por conta):")
for r in q("""with er as (select s.account_id, sum(u.error_count) e, sum(u.usage_count) n from feature_usage u join subscriptions s using(subscription_id) group by 1),
              tk as (select a.industry, avg(t.escalation_flag) esc, avg(t.satisfaction_score) sat, 1.0*count(*)/count(distinct t.account_id) tpc
                     from support_tickets t join accounts a using(account_id) group by 1)
              select a.industry, round(100.0*sum(e)/sum(n),2), round(100*tk.esc,1), round(tk.sat,2), round(tk.tpc,2)
              from accounts a join er using(account_id) join tk using(industry) group by 1 order by 1"""):
    print("   ", r)
print("  motivos dos eventos de churn em DevTools:", q("select reason_code, count(*) from churn_events join accounts using(account_id) where industry='DevTools' group by 1 order by 2 desc"))

print("\n=== 3. Plano (churn_flag)")
for r in q("select plan_tier, count(*), sum(churn_flag), round(100.0*avg(churn_flag),1) from accounts group by 1"):
    print("  ", r)

print("\n=== 4. Fricção de produto: beta × estável, por recurso")
tot = q("select is_beta_feature, sum(error_count), sum(usage_count) from feature_usage group by 1")
for b, e, n in tot:
    print(f"  {'beta   ' if b else 'estável'}: {e}/{n} = {e/n:.2%} de erro por uso")
rows = q("""select feature_name,
              1.0*sum(case when is_beta_feature=1 then error_count end)/sum(case when is_beta_feature=1 then usage_count end) b,
              1.0*sum(case when is_beta_feature=0 then error_count end)/sum(case when is_beta_feature=0 then usage_count end) s,
              sum(case when is_beta_feature=1 then usage_count end) nb
            from feature_usage group by 1 having b is not null and s is not null""")
mais = sorted([r for r in rows if r[1] > r[2]], key=lambda r: r[2] - r[1])
print(f"  {len(rows)} recursos têm uso beta e estável; o beta erra mais em {len(mais)}")
print("  maiores diferenças (recurso, erro beta %, erro estável %, usos beta):")
for r in mais[:5]:
    print(f"    {r[0]:11s} {100*r[1]:5.2f}  {100*r[2]:5.2f}  {r[3]}")
print("  churn_flag por taxa de erro da conta (quartis):")
for r in q("""with er as (select s.account_id, 1.0*sum(u.error_count)/sum(u.usage_count) t from feature_usage u join subscriptions s using(subscription_id) group by 1),
              r as (select a.churn_flag, er.t, ntile(4) over (order by er.t) qq from accounts a join er using(account_id))
              select qq, round(100*min(t),2), round(100*max(t),2), count(*), round(100.0*avg(churn_flag),1) from r group by qq"""):
    print("   ", r)
print("  churn_flag por adoção (recursos distintos usados, quartis):")
for r in q("""with k as (select s.account_id, count(distinct u.feature_name) f from feature_usage u join subscriptions s using(subscription_id) group by 1),
              r as (select a.churn_flag, k.f, ntile(4) over (order by k.f) qq from accounts a join k using(account_id))
              select qq, min(f), max(f), count(*), round(100.0*avg(churn_flag),1) from r group by qq"""):
    print("   ", r)

print("  recursos mais usados nas assinaturas longas (4º quartil de duração) que nas curtas (1º), usos por assinatura:")
rows = q("""with d as (select subscription_id, julianday(coalesce(end_date, ?)) - julianday(start_date) dur from subscriptions),
              r as (select subscription_id, ntile(4) over (order by dur) qq from d),
              tot as (select qq, count(*) subs from r group by qq),
              u as (select r.qq, u.feature_name, sum(u.usage_count) n from feature_usage u join r using(subscription_id) group by 1,2)
            select feature_name, 1.0*sum(case when qq=4 then n end)/(select subs from tot where qq=4),
                   1.0*sum(case when qq=1 then n end)/(select subs from tot where qq=1)
            from u group by 1""", CORTE)
rows = sorted([r for r in rows if r[1] and r[2]], key=lambda r: r[1] / r[2], reverse=True)
for r in rows[:5]:
    print(f"    {r[0]:11s} longa {r[1]:.2f}  curta {r[2]:.2f}  razão {r[1]/r[2]:.2f}")

print("\n=== 5. Suporte: volume, escalação e o cruzamento com a fricção de produto (churn_flag)")
for e, n, ch in q("""select coalesce(esc.e,0), count(*), sum(a.churn_flag) from accounts a
                     left join (select account_id, max(escalation_flag) e from support_tickets group by 1) esc using(account_id) group by 1"""):
    print(f"  {'com escalação' if e else 'sem escalação'}: {ch}/{n} = {ch/n:.1%}")
print("  tickets por conta:")
for r in q("""with k as (select a.account_id, a.churn_flag, count(t.ticket_id) n from accounts a left join support_tickets t using(account_id) group by 1)
              select case when n<=2 then '0-2' when n<=4 then '3-4' when n<=6 then '5-6' else '7+' end, count(*), sum(churn_flag), round(100.0*avg(churn_flag),1)
              from k group by 1 order by min(n)"""):
    print("   ", r)
rows = q("""with er as (select s.account_id, 1.0*sum(u.error_count)/sum(u.usage_count) t from feature_usage u join subscriptions s using(subscription_id) group by 1),
              med as (select t m from er order by t limit 1 offset (select count(*)/2 from er)),
              esc as (select account_id, max(escalation_flag) e from support_tickets group by 1)
            select coalesce(esc.e,0), er.t > (select m from med), count(*), sum(a.churn_flag)
            from accounts a join er using(account_id) left join esc using(account_id) group by 1,2 order by 1,2""")
print("  (escalou, erro acima da mediana, contas, com churn):")
for r in rows:
    print(f"    {r}  {r[3]/r[2]:.1%}")
amb = [r for r in rows if r[0] == 1 and r[1] == 1][0]
res = [sum(r[3] for r in rows if r is not amb), sum(r[2] for r in rows if r is not amb)]
taxa_vs_resto("escalou E erro alto × resto", (amb[3], amb[2]), res)

print("\n=== 6. Satisfação: o que ela acompanha")
n, sem, meia = q("select count(*), sum(satisfaction_score is null), sum(time(submitted_at)='00:00:00') from support_tickets")[0]
print(f"  {sem}/{n} tickets sem nota ({sem/n:.1%}); notas existentes: {[r[0] for r in q('select distinct satisfaction_score from support_tickets where satisfaction_score is not null order by 1')]}")
print(f"  tickets abertos exatamente à 00:00:00: {meia}/{n}")
print("  (nota, tickets, 1ª resposta min, resolução h, % escalados):")
for r in q("select satisfaction_score, count(*), round(avg(first_response_time_minutes),1), round(avg(resolution_time_hours),1), round(100.0*avg(escalation_flag),1) from support_tickets group by 1"):
    print("   ", r)
print("  satisfação média da conta por tercil da taxa de erro da conta:")
for r in q("""with er as (select s.account_id, 1.0*sum(u.error_count)/sum(u.usage_count) t from feature_usage u join subscriptions s using(subscription_id) group by 1),
              st as (select account_id, avg(satisfaction_score) sat from support_tickets where satisfaction_score is not null group by 1),
              j as (select er.t, st.sat, ntile(3) over (order by er.t) qq from er join st using(account_id))
              select qq, round(100*min(t),2), round(100*max(t),2), count(*), round(avg(sat),2) from j group by qq"""):
    print("   ", r)

print("\n=== 7. Motivo registrado × comentário do cliente")
fbs = [r[0] for r in q("select distinct feedback_text from churn_events where trim(coalesce(feedback_text,''))<>'' order by 1")]
mot = [r[0] for r in q("select distinct reason_code from churn_events order by 1")]
tab = [[q("select count(*) from churn_events where feedback_text=? and reason_code=?", f, m)[0][0] for m in mot] for f in fbs]
x, p = chi2_tabela(tab)
print(f"  textos distintos de comentário: {fbs}")
print(f"  motivo × comentário (sem os vazios): qui2 = {x:.2f}  p = {p:.3f}")
coer = q("""select count(*) from churn_events where (feedback_text='too expensive' and reason_code in ('pricing','budget'))
            or (feedback_text='missing features' and reason_code='features') or (feedback_text='switched to competitor' and reason_code='competitor')""")[0][0]
com = q("select count(*) from churn_events where trim(coalesce(feedback_text,''))<>''")[0][0]
print(f"  eventos com comentário: {com}; comentário coerente com o motivo: {coer} ({coer/com:.1%})")
print("  churn silencioso (sem comentário):", q("select count(*), count(distinct account_id) from churn_events where trim(coalesce(feedback_text,''))=''")[0], "(eventos, contas)")
print("  eventos por texto de comentário:", q("select coalesce(nullif(trim(feedback_text),''),'(vazio)'), count(*) from churn_events group by 1 order by 2 desc"))

print("\n=== 8. Contradição entre tabelas")
print("  contas com churn_flag = 1:", q("select count(*) from accounts where churn_flag=1")[0][0])
r = q("""select count(distinct a.account_id), sum(s.mrr_amount) from accounts a join subscriptions s using(account_id)
         where a.churn_flag=1 and s.end_date is null and s.is_trial=0""")[0]
print(f"  dessas, com assinatura paga em aberto: {r[0]} contas, US$ {r[1]:,} de MRR")
print("  contas com evento de churn:", q("select count(distinct account_id) from churn_events")[0][0],
      " | contas com evento e churn_flag = 0:", q("select count(distinct account_id) from churn_events join accounts using(account_id) where churn_flag=0")[0][0])

# ---------------------------------------------------------------- lista de contas
print("\n=== 9. Lista de contas para o CS: sinais acumulados × receita exposta")
SINAIS = ["devtools", "trial", "evento_90d", "escalacao", "erro_alto", "queda_uso", "renova_sem_auto", "muitos_tickets"]
NOMES = {
    "devtools": "setor DevTools",
    "trial": "conta em trial",
    "evento_90d": "evento de churn nos últimos 90 dias",
    "escalacao": "ticket escalado",
    "erro_alto": "taxa de erro no quartil mais alto",
    "queda_uso": "uso do 4º tri/2024 abaixo da metade do 3º tri",
    "renova_sem_auto": "aniversário de contrato anual em 90 dias sem auto-renew",
    "muitos_tickets": "7 tickets ou mais",
}
p75 = q("""with er as (select s.account_id, 1.0*sum(u.error_count)/sum(u.usage_count) t from feature_usage u join subscriptions s using(subscription_id) group by 1)
           select t from er order by t limit 1 offset (select 3*count(*)/4 from er)""")[0][0]
contas = {r[0]: dict(account_id=r[0], conta=r[1], setor=r[2], pais=r[3], plano=r[4], churn_flag=r[5], trial=r[6]) for r in
          q("select account_id, account_name, industry, country, plan_tier, churn_flag, is_trial from accounts")}
for a in contas.values():
    trial = a["trial"]
    a["mrr_ativo"] = 0
    a.update({s: 0 for s in SINAIS})
    a["devtools"] = int(a["setor"] == "DevTools")
    a["trial"] = trial
for aid, mrr in q("select account_id, sum(mrr_amount) from subscriptions where end_date is null and is_trial=0 group by 1"):
    contas[aid]["mrr_ativo"] = mrr
for (aid,) in q("select distinct account_id from churn_events where churn_date > date(?, '-90 days')", CORTE):
    contas[aid]["evento_90d"] = 1
for (aid,) in q("select distinct account_id from support_tickets where escalation_flag=1"):
    contas[aid]["escalacao"] = 1
for (aid,) in q("""select s.account_id from feature_usage u join subscriptions s using(subscription_id) group by 1
                   having 1.0*sum(u.error_count)/sum(u.usage_count) >= ?""", p75):
    contas[aid]["erro_alto"] = 1
for aid, t3, t4 in q("""select s.account_id,
                          sum(case when u.usage_date >= '2024-07-01' and u.usage_date < '2024-10-01' then u.usage_count else 0 end),
                          sum(case when u.usage_date >= '2024-10-01' then u.usage_count else 0 end)
                        from feature_usage u join subscriptions s using(subscription_id) group by 1"""):
    if t3 >= 10 and t4 < 0.5 * t3:
        contas[aid]["queda_uso"] = 1
# aniversário do contrato anual pago em aberto nos 90 dias após o corte (mesma regra da D8, em SQL)
for (aid,) in q("""with s as (select account_id, start_date, auto_renew_flag from subscriptions
                              where end_date is null and is_trial=0 and billing_frequency='annual' and auto_renew_flag=0),
                     a as (select account_id, date(start_date, '+' || (cast(strftime('%Y', ?) as int) - cast(strftime('%Y', start_date) as int)) || ' years') d from s)
                   select distinct account_id from a
                   where (case when d <= ? then date(d, '+1 year') else d end) <= date(?, '+90 days')""", CORTE, CORTE, CORTE):
    contas[aid]["renova_sem_auto"] = 1
for (aid,) in q("select account_id from support_tickets group by 1 having count(*) >= 7"):
    contas[aid]["muitos_tickets"] = 1
for a in contas.values():
    a["n_sinais"] = sum(a[s] for s in SINAIS)
    a["sinais"] = "; ".join(NOMES[s] for s in SINAIS if a[s])

print("  frequência de cada sinal nas 500 contas:", {s: sum(a[s] for a in contas.values()) for s in SINAIS})
print("  checagem de honestidade: a contagem de sinais (sem o evento de 90 dias, que já é churn) separa quem tem churn_flag?")
for k in range(0, 5):  # 4 = "4 ou mais"
    g = [a for a in contas.values() if min(4, a["n_sinais"] - a["evento_90d"]) == k]
    if g:
        print(f"    {k}{'+' if k == 4 else ' '} sinais: {len(g):3d} contas, churn_flag {sum(a['churn_flag'] for a in g)/len(g):.1%}")

ativas = [a for a in contas.values() if a["churn_flag"] == 0]
ativas.sort(key=lambda a: (-a["n_sinais"], -a["mrr_ativo"]))
fila = [a for a in ativas if a["n_sinais"] >= 3]
print(f"\n  contas com churn_flag = 0: {len(ativas)}; com 3 sinais ou mais: {len(fila)}, MRR ativo US$ {sum(a['mrr_ativo'] for a in fila):,}")
print(f"  com 2 sinais: {sum(1 for a in ativas if a['n_sinais']==2)} contas; com 1: {sum(1 for a in ativas if a['n_sinais']==1)}; com 0: {sum(1 for a in ativas if a['n_sinais']==0)}")
print("  as 15 primeiras da fila:")
for a in fila[:15]:
    print(f"    {a['account_id']} {a['conta']:12s} {a['setor']:13s} {a['plano']:10s} US$ {a['mrr_ativo']:>7,}  {a['n_sinais']}  {a['sinais']}")
reconc = sorted([a for a in contas.values() if a["churn_flag"] == 1 and a["mrr_ativo"] > 0], key=lambda a: -a["mrr_ativo"])
print(f"\n  lista B, conciliar: {len(reconc)} contas com churn_flag = 1 e assinatura paga em aberto, US$ {sum(a['mrr_ativo'] for a in reconc):,} de MRR")

CAMPOS = ["prioridade", "lista", "account_id", "conta", "setor", "pais", "plano", "mrr_ativo", "n_sinais", "sinais"] + SINAIS
with open(SAIDA_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
    w.writeheader()
    for i, a in enumerate(fila, 1):
        w.writerow({**a, "prioridade": i, "lista": "A: agir (3+ sinais)"})
    for i, a in enumerate(reconc, len(fila) + 1):
        w.writerow({**a, "prioridade": i, "lista": "B: conciliar (CRM diz churn, faturamento cobra)"})
print(f"\n  CSV: {os.path.relpath(SAIDA_CSV, AQUI)} ({len(fila)} + {len(reconc)} linhas)")
