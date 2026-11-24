"""Gera o JSON que alimenta o dashboard React (solution/dashboard/src/data.json).

Reaproveita as saídas dos scripts 01–03 e calcula a série mensal (churn absoluto × taxa sobre a base).
Uso: uv run --with pandas,scipy python -I solution/scripts/04_export_dashboard.py <raw> <outputs> <json_saida>
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RAW, OUT, DEST = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
acc = pd.read_csv(RAW / "ravenstack_accounts.csv", parse_dates=["signup_date"])
sub = pd.read_csv(RAW / "ravenstack_subscriptions.csv", parse_dates=["start_date", "end_date"])
use = pd.read_csv(RAW / "ravenstack_feature_usage.csv", parse_dates=["usage_date"])
tkt = pd.read_csv(RAW / "ravenstack_support_tickets.csv")
chn = pd.read_csv(RAW / "ravenstack_churn_events.csv", parse_dates=["churn_date"])
b = pd.read_csv(OUT / "account_360.csv")
corr = pd.read_csv(OUT / "correlacoes_por_categoria.csv")
corr_s = pd.read_csv(OUT / "correlacoes_assinatura.csv")
sp = pd.read_csv(OUT / "spearman_entre_categorias.csv", index_col=0)


def r(x, n=4):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)


# ------------------------------------------------------------ série mensal
paga = sub[~sub.is_trial]
mensal = []
for m in pd.period_range("2023-01", "2024-12", freq="M"):
    ini, fim = m.start_time, m.end_time
    ativas_ini = paga[(paga.start_date < ini) & (paga.end_date.isna() | (paga.end_date >= ini))]
    encerradas = paga[(paga.end_date >= ini) & (paga.end_date <= fim)]
    contas_base = int((acc.signup_date <= fim).sum())
    ev = int(((chn.churn_date >= ini) & (chn.churn_date <= fim)).sum())
    uso_m = use[(use.usage_date >= ini) & (use.usage_date <= fim)].usage_count.sum()
    ativas_m = paga[(paga.start_date <= fim) & (paga.end_date.isna() | (paga.end_date >= ini))]
    mensal.append(dict(
        mes=str(m), eventos_churn=ev, contas_base=contas_base,
        taxa_eventos_por_conta=r(ev / contas_base if contas_base else None),
        assinaturas_ativas=len(ativas_ini), assinaturas_encerradas=len(encerradas),
        taxa_churn_assinaturas=r(len(encerradas) / len(ativas_ini) if len(ativas_ini) else None),
        mrr_ativo=r(ativas_ini.mrr_amount.sum(), 0), mrr_perdido=r(encerradas.mrr_amount.sum(), 0),
        taxa_churn_mrr=r(encerradas.mrr_amount.sum() / ativas_ini.mrr_amount.sum() if len(ativas_ini) else None),
        uso_eventos=int(uso_m), uso_por_assinatura_ativa=r(uso_m / len(ativas_m) if len(ativas_m) else None, 2),
    ))
mdf = pd.DataFrame(mensal)
# tendência das taxas em 2024 (base já madura): Spearman mês × taxa
tend = {}
m24 = mdf[mdf.mes >= "2024-01"]
for col in ["eventos_churn", "taxa_eventos_por_conta", "taxa_churn_assinaturas", "taxa_churn_mrr", "uso_eventos",
            "uso_por_assinatura_ativa"]:
    rho, p = stats.spearmanr(range(len(m24)), m24[col])
    tend[col] = dict(rho=r(rho, 3), p=r(p, 4))

# ------------------------------------------------------------ segmentos com IC de Wilson
def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    ph = k / n; d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d; h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (r(c - h), r(c + h))


segs = {}
for col, nome in [("perfil_industry", "Indústria"), ("perfil_referral_source", "Canal de aquisição"),
                  ("perfil_plan_tier", "Plano"), ("perfil_country", "País"), ("perfil_is_trial", "Trial")]:
    g = b.groupby(col).agg(n=("churn_flag_conta", "size"), k=("churn_flag_conta", "sum"),
                           mrr=("receita_mrr_ativo", "sum")).reset_index()
    tab = pd.crosstab(b[col], b.churn_flag_conta); _, p, *_ = stats.chi2_contingency(tab)
    segs[nome] = dict(p=r(p), itens=[dict(nivel=str(x[col]), n=int(x.n), churn=int(x.k), taxa=r(x.k / x.n),
                                          ic=wilson(x.k, x.n), mrr_ativo=r(x.mrr, 0)) for _, x in g.iterrows()])


# ------------------------------------------------------------ safras (coortes): a proporção que sai muda?
pg = sub[~sub.is_trial].copy()
pg["q"] = pg.start_date.dt.to_period("Q").astype(str)
pg["dur"] = (pg.end_date - pg.start_date).dt.days
pg["dias_disp"] = (pd.Timestamp("2024-12-31") - pg.start_date).dt.days
saf = pg.groupby("q").agg(n=("subscription_id", "size"), encerradas=("churn_flag", "sum"),
                          dias_disp=("dias_disp", "median")).reset_index()
saf["dur_mediana"] = saf.q.map(pg[pg.churn_flag].groupby("q").dur.median())
safras = [dict(tri=x.q, n=int(x.n), encerradas=int(x.encerradas), pct=r(x.encerradas / x.n), ic=wilson(x.encerradas, x.n),
               dias_disponiveis=r(x.dias_disp, 0), duracao_mediana=r(x.dur_mediana, 0)) for x in saf.itertuples()]
_, p_saf, *_ = stats.chi2_contingency(pd.crosstab(pg.q, pg.churn_flag))
_, p_saf23, *_ = stats.chi2_contingency(pd.crosstab(pg[pg.q != "2023Q1"].q, pg[pg.q != "2023Q1"].churn_flag))
ev_conta = chn.groupby("account_id").size().reindex(acc.account_id).fillna(0)
sq = acc.signup_date.dt.to_period("Q").astype(str).values
safras_contas = [dict(tri=q, contas=int((sq == q).sum()), eventos_por_conta=r(ev_conta.values[sq == q].mean(), 2))
                 for q in sorted(set(sq))]
anuais = pg[pg.churn_flag & pg.billing_frequency.eq("annual")]
datas = dict(anuais_encerradas=len(anuais), anuais_menos_1_ano=int((anuais.dur < 365).sum()),
             anuais_menos_30_dias=int((anuais.dur < 30).sum()), p_safras=r(p_saf), p_safras_sem_2023q1=r(p_saf23),
             fracao_janela_mediana=r((pg[pg.churn_flag].dur / pg[pg.churn_flag].dias_disp.clip(lower=1)).median(), 2))

# ------------------------------------------------------------ definições de churn
f = set(acc[acc.churn_flag].account_id); e = set(chn.account_id)
sub_enc = set(sub[sub.churn_flag].account_id)
definicoes = dict(
    so_flag=len(f - e), so_evento=len(e - f), ambos=len(f & e), nenhum=len(acc) - len(f | e),
    contas_com_assinatura_encerrada=len(sub_enc), contas_flag_todas_encerradas=0,
    spearman_flag_evento=r(b[["churn_flag_conta", "churn_tem_evento"]].astype(float).corr("spearman").iloc[0, 1], 3),
)

# ------------------------------------------------------------ satisfação e motivos
sat = tkt.satisfaction_score.fillna(0).astype(int).value_counts().reindex([0, 1, 2, 3, 4, 5], fill_value=0)
satisfacao = [dict(nota="Sem nota" if k == 0 else str(k), tickets=int(v)) for k, v in sat.items()]
ct = pd.crosstab(chn.reason_code, chn.feedback_text.fillna("(sem comentário)"))
motivos = dict(linhas=list(ct.index), colunas=list(ct.columns), valores=ct.values.tolist())

# ------------------------------------------------------------ auditoria (mesma lógica do script 01)
aud_md = (Path(sys.argv[2]).parent.parent / "docs" / "auditoria_dados.md").read_text(encoding="utf-8")
auditoria = []
for ln in aud_md.splitlines():
    if ln.startswith("| ") and not ln.startswith("| checagem") and not ln.startswith("|---"):
        c = [x.strip() for x in ln.strip("|").split("|")]
        auditoria.append(dict(checagem=c[0], resultado=c[1], leitura=c[2]))

# ------------------------------------------------------------ correlações
def corr_rows(df, base, alvo_col=None):
    """Linhas de correlação com números estruturados (a formatação pt-BR fica no front)."""
    out = []
    for x in df.to_dict("records"):
        v = x["variavel"]; alvo = x.get("alvo", "assinatura_encerrada")
        y = base[alvo_col or alvo].astype(bool); col = base[v]
        row = dict(alvo=alvo, categoria=x["categoria"], variavel=v, forca=r(x["forca"], 3), p=r(x["p"]), q=r(x["q_bh"]))
        if pd.api.types.is_bool_dtype(col) or not pd.api.types.is_numeric_dtype(col):
            g = y.groupby(col.astype(str)).agg(["mean", "size"])
            row["niveis"] = [dict(nivel=k, taxa=r(t.iloc[0]), n=int(t.iloc[1])) for k, t in g.iterrows()]
        else:
            c = pd.to_numeric(col, errors="coerce").astype(float)
            row["media_churn"], row["media_retida"] = r(c[y].mean()), r(c[~y].mean())
        out.append(row)
    return out


sx = pd.read_csv(OUT / "subscription_360.csv")
sx = sx[~sx.is_trial].copy()
sx["anual"] = sx.billing_frequency.eq("annual")
sx["taxa_erro"] = sx.uso_erros / sx.uso_eventos.replace(0, np.nan)
sx["pct_beta"] = sx.uso_registros_beta / sx.uso_registros.replace(0, np.nan)
sx["eventos_por_seat"] = sx.uso_eventos / sx.seats.replace(0, np.nan)

# ------------------------------------------------------------ contas (tabela exploratória)
cols = ["account_id", "perfil_account_name", "perfil_industry", "perfil_country", "perfil_referral_source",
        "perfil_plan_tier", "receita_mrr_ativo", "receita_assinaturas_ativas", "uso_eventos", "uso_taxa_erro",
        "suporte_tickets", "suporte_satisfacao_media", "suporte_pct_sem_nota", "churn_flag_conta", "churn_eventos"]
contas = b[cols].copy()
for c in contas.select_dtypes("float").columns:
    contas[c] = contas[c].round(3)
contas = json.loads(contas.to_json(orient="records"))

# ------------------------------------------------------------ KPIs
kpis = dict(
    contas=len(acc), assinaturas=len(sub), registros_uso=len(use), tickets=len(tkt), eventos_churn=len(chn),
    churn_flag=int(acc.churn_flag.sum()), contas_com_evento=len(e),
    mrr_ativo=r(sub[sub.end_date.isna()].mrr_amount.sum(), 0),
    mrr_perdido=r(sub[sub.end_date.notna()].mrr_amount.sum(), 0),
    pct_sem_nota=r(tkt.satisfaction_score.isna().mean()),
    variaveis_testadas=int(len(corr) + len(corr_s)), variaveis_significativas=int((corr.q_bh < .05).sum() + (corr_s.q_bh < .05).sum()),
)

data = dict(safras=safras, safras_contas=safras_contas, datas=datas, gerado_em=pd.Timestamp.now().isoformat(timespec="minutes"), kpis=kpis, mensal=mensal, tendencia_2024=tend,
            segmentos=segs, definicoes=definicoes, satisfacao=satisfacao, motivos=motivos, auditoria=auditoria,
            correlacoes=corr_rows(corr, b), correlacoes_assinatura=corr_rows(corr_s, sx, "churn_flag"),
            spearman=dict(variaveis=list(sp.columns), valores=[[r(v, 3) for v in row] for row in sp.values]),
            contas=contas)
DEST.parent.mkdir(parents=True, exist_ok=True)
DEST.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
print("ok", DEST, f"{DEST.stat().st_size/1024:.0f} KB")
print(mdf[["mes", "eventos_churn", "taxa_eventos_por_conta", "assinaturas_ativas", "assinaturas_encerradas",
           "taxa_churn_assinaturas", "taxa_churn_mrr", "uso_por_assinatura_ativa"]].to_string(index=False))
print(json.dumps(tend, indent=0))
