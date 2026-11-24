"""Liga as 5 tabelas da RavenStack numa visão única por conta (account_360) e por assinatura
(subscription_360), com as colunas separadas por categoria via prefixo:

    perfil_   quem é a conta (accounts)
    receita_  o que ela paga (subscriptions)
    uso_      como usa o produto (feature_usage, via subscription_id -> account_id)
    suporte_  como foi atendida (support_tickets)
    churn_    se e como saiu (churn_events + flags)

Decisão de modelagem: as chaves ligam 100%, mas as DATAS entre tabelas não são coerentes
(ver docs/auditoria_dados.md, gerado por este script). Por isso a ligação é por chave e
os agregados são do histórico inteiro da conta, sem janela "antes do churn".

Uso:  uv run --with pandas python -I solution/scripts/01_build_dataset.py <dir_raw> <dir_saida> <dir_docs>
"""
import sys
from pathlib import Path

import pandas as pd

RAW, OUT, DOCS = (Path(p) for p in sys.argv[1:4])
OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)
REF = pd.Timestamp("2024-12-31")  # última data presente nos dados

acc = pd.read_csv(RAW / "ravenstack_accounts.csv", parse_dates=["signup_date"])
sub = pd.read_csv(RAW / "ravenstack_subscriptions.csv", parse_dates=["start_date", "end_date"])
use = pd.read_csv(RAW / "ravenstack_feature_usage.csv", parse_dates=["usage_date"])
tkt = pd.read_csv(RAW / "ravenstack_support_tickets.csv", parse_dates=["submitted_at", "closed_at"])
chn = pd.read_csv(RAW / "ravenstack_churn_events.csv", parse_dates=["churn_date"])

# ---------------------------------------------------------------- auditoria de ligação
audit = []
def check(nome, valor, nota=""):
    audit.append((nome, valor, nota))

check("Contas", len(acc))
check("Assinaturas / contas com assinatura", f"{len(sub)} / {sub.account_id.nunique()}")
check("Assinaturas órfãs (account_id inexistente)", int((~sub.account_id.isin(acc.account_id)).sum()))
check("Linhas de uso órfãs (subscription_id inexistente)", int((~use.subscription_id.isin(sub.subscription_id)).sum()))
check("Tickets órfãos", int((~tkt.account_id.isin(acc.account_id)).sum()))
check("Eventos de churn órfãos", int((~chn.account_id.isin(acc.account_id)).sum()))
check("Contas sem nenhum ticket", int((~acc.account_id.isin(tkt.account_id)).sum()))
check("Assinaturas sem nenhum uso", int((~sub.subscription_id.isin(use.subscription_id)).sum()))

s_ac = sub.groupby("account_id").agg(n=("subscription_id", "size"), n_end=("churn_flag", "sum"),
                                     last_start=("start_date", "max"), first_start=("start_date", "min"))
a_ = acc.merge(s_ac, left_on="account_id", right_index=True)
check("Contas com churn_flag=True", int(acc.churn_flag.sum()), f"{acc.churn_flag.mean():.1%} da base")
check("...dessas, com TODAS as assinaturas encerradas", int((a_.churn_flag & (a_.n == a_.n_end)).sum()),
      "conta 'churnada' continua com assinaturas ativas")
ev_acc = set(chn.account_id)
check("Contas com ≥1 evento em churn_events", len(ev_acc), f"{len(chn)} eventos")
check("Contas com churn_flag E evento", int(acc[acc.churn_flag].account_id.isin(ev_acc).sum()))
check("Contas com churn_flag SEM evento", int((acc.churn_flag & ~acc.account_id.isin(ev_acc)).sum()))
check("Contas com evento SEM churn_flag", int((~acc.churn_flag & acc.account_id.isin(ev_acc)).sum()))
last_ev = chn.groupby("account_id").churn_date.max()
check("Contas com assinatura iniciada após o último churn",
      int((a_.set_index("account_id").last_start.reindex(last_ev.index) > last_ev).sum()), f"de {len(last_ev)}")
m = chn.merge(sub[["account_id", "end_date"]].dropna(), on="account_id")
m["d"] = (m.churn_date - m.end_date).dt.days.abs()
check("Eventos de churn com assinatura encerrada ±7 dias", int((m.groupby("churn_event_id").d.min() <= 7).sum()), f"de {len(chn)}")
uu = use.merge(sub[["subscription_id", "start_date", "end_date"]])
fora = (uu.usage_date < uu.start_date) | (uu.end_date.notna() & (uu.usage_date > uu.end_date))
check("Uso fora da vigência da assinatura", f"{fora.mean():.1%}")
tt = tkt.merge(acc[["account_id", "signup_date"]])
check("Tickets abertos antes do signup da conta", f"{(tt.submitted_at < tt.signup_date).mean():.1%}")
last_plan = sub.sort_values("start_date").groupby("account_id").plan_tier.last()
check("Plano da conta = plano da assinatura mais recente",
      f"{(last_plan.reindex(acc.account_id).values == acc.plan_tier.values).mean():.1%}", "acaso seria ~33%")
check("Notas de satisfação 1 ou 2", int(tkt.satisfaction_score.isin([1, 2]).sum()), "escala 1–5")
check("Tickets sem nota de satisfação", f"{tkt.satisfaction_score.isna().mean():.1%}")
ct = pd.crosstab(chn.reason_code, chn.feedback_text.fillna("(vazio)"))
from math import sqrt
chi = ((ct - ct.sum(axis=1).values[:, None] * ct.sum(axis=0).values / ct.values.sum()) ** 2 /
       (ct.sum(axis=1).values[:, None] * ct.sum(axis=0).values / ct.values.sum())).values.sum()
check("Associação reason_code × feedback_text (V de Cramér)",
      f"{sqrt(chi / (ct.values.sum() * (min(ct.shape) - 1))):.2f}", "0 = nenhuma; motivo e comentário não conversam")
check("Assinaturas trial com MRR=0", f"{int((sub.is_trial & (sub.mrr_amount == 0)).sum())} de {int(sub.is_trial.sum())}")

# ---------------------------------------------------------------- uso por assinatura
use["erro_flag"] = use.error_count > 0
u_sub = use.groupby("subscription_id").agg(
    uso_registros=("usage_id", "size"), uso_eventos=("usage_count", "sum"),
    uso_duracao_h=("usage_duration_secs", lambda x: x.sum() / 3600), uso_erros=("error_count", "sum"),
    uso_features_distintas=("feature_name", "nunique"), uso_registros_beta=("is_beta_feature", "sum"))
subx = sub.merge(u_sub, left_on="subscription_id", right_index=True, how="left")
subx[u_sub.columns] = subx[u_sub.columns].fillna(0)
subx = subx.merge(acc.add_prefix("conta_").rename(columns={"conta_account_id": "account_id"}), on="account_id")
subx["duracao_dias"] = ((subx.end_date.fillna(REF)) - subx.start_date).dt.days
subx.to_csv(OUT / "subscription_360.csv", index=False)

# ---------------------------------------------------------------- PERFIL
perfil = acc.set_index("account_id")[["account_name", "industry", "country", "referral_source",
                                      "plan_tier", "seats", "is_trial", "signup_date"]]
perfil = perfil.rename(columns=lambda c: f"perfil_{c}")
perfil["perfil_coorte_signup"] = perfil.perfil_signup_date.dt.to_period("Q").astype(str)
perfil["perfil_dias_desde_signup"] = (REF - perfil.perfil_signup_date).dt.days

# ---------------------------------------------------------------- RECEITA
ativa = sub.end_date.isna()
paga = ~sub.is_trial
rec = sub.assign(mrr_ativo=sub.mrr_amount.where(ativa, 0), seats_ativos=sub.seats.where(ativa, 0),
                 ativa=ativa, anual=sub.billing_frequency.eq("annual"),
                 mrr_perdido=sub.mrr_amount.where(~ativa, 0)).groupby("account_id").agg(
    receita_assinaturas=("subscription_id", "size"),
    receita_assinaturas_ativas=("ativa", "sum"),
    receita_assinaturas_encerradas=("churn_flag", "sum"),
    receita_assinaturas_trial=("is_trial", "sum"),
    receita_mrr_ativo=("mrr_ativo", "sum"),
    receita_mrr_perdido=("mrr_perdido", "sum"),
    receita_mrr_medio_assinatura=("mrr_amount", "mean"),
    receita_seats_ativos=("seats_ativos", "sum"),
    receita_pct_anual=("anual", "mean"),
    receita_pct_auto_renew=("auto_renew_flag", "mean"),
    receita_upgrades=("upgrade_flag", "sum"),
    receita_downgrades=("downgrade_flag", "sum"),
    receita_primeira_assinatura=("start_date", "min"),
)
rec["receita_arr_ativo"] = rec.receita_mrr_ativo * 12
rec["receita_pct_mrr_perdido"] = rec.receita_mrr_perdido / (rec.receita_mrr_perdido + rec.receita_mrr_ativo)
for tier in ["Basic", "Pro", "Enterprise"]:
    rec[f"receita_pct_assin_{tier.lower()}"] = sub[sub.plan_tier == tier].groupby("account_id").size() \
        .reindex(rec.index).fillna(0) / rec.receita_assinaturas

# ---------------------------------------------------------------- USO
ux = use.merge(sub[["subscription_id", "account_id"]])
ux["ano"] = ux.usage_date.dt.year
uso = ux.groupby("account_id").agg(
    uso_registros=("usage_id", "size"), uso_eventos=("usage_count", "sum"),
    uso_duracao_h=("usage_duration_secs", lambda x: x.sum() / 3600),
    uso_erros=("error_count", "sum"), uso_registros_com_erro=("erro_flag", "sum"),
    uso_features_distintas=("feature_name", "nunique"), uso_registros_beta=("is_beta_feature", "sum"),
    uso_ultimo_registro=("usage_date", "max"))
uso["uso_taxa_erro"] = uso.uso_erros / uso.uso_eventos
uso["uso_pct_registros_com_erro"] = uso.uso_registros_com_erro / uso.uso_registros
uso["uso_pct_beta"] = uso.uso_registros_beta / uso.uso_registros
uso["uso_duracao_media_min"] = uso.uso_duracao_h * 60 / uso.uso_registros
por_ano = ux.pivot_table(index="account_id", columns="ano", values="usage_count", aggfunc="sum").fillna(0)
uso["uso_eventos_2023"], uso["uso_eventos_2024"] = por_ano.get(2023, 0), por_ano.get(2024, 0)
uso["uso_variacao_2024_vs_2023"] = (uso.uso_eventos_2024 - uso.uso_eventos_2023) / uso.uso_eventos_2023.replace(0, pd.NA)
uso["uso_dias_desde_ultimo"] = (REF - uso.uso_ultimo_registro).dt.days

# ---------------------------------------------------------------- SUPORTE
tk = tkt.assign(urgente_alta=tkt.priority.isin(["urgent", "high"]), sem_nota=tkt.satisfaction_score.isna())
sup = tk.groupby("account_id").agg(
    suporte_tickets=("ticket_id", "size"),
    suporte_pct_urgente_alta=("urgente_alta", "mean"),
    suporte_resolucao_media_h=("resolution_time_hours", "mean"),
    suporte_resolucao_max_h=("resolution_time_hours", "max"),
    suporte_primeira_resposta_media_min=("first_response_time_minutes", "mean"),
    suporte_escalonamentos=("escalation_flag", "sum"),
    suporte_satisfacao_media=("satisfaction_score", "mean"),
    suporte_pct_sem_nota=("sem_nota", "mean"),
    suporte_ultimo_ticket=("submitted_at", "max"))
sup["suporte_pct_escalonados"] = sup.suporte_escalonamentos / sup.suporte_tickets

# ---------------------------------------------------------------- CHURN
ch = chn.groupby("account_id").agg(
    churn_eventos=("churn_event_id", "size"),
    churn_primeiro=("churn_date", "min"), churn_ultimo=("churn_date", "max"),
    churn_reembolso_total=("refund_amount_usd", "sum"),
    churn_reativacoes=("is_reactivation", "sum"),
    churn_upgrade_previo=("preceding_upgrade_flag", "sum"),
    churn_downgrade_previo=("preceding_downgrade_flag", "sum"),
    churn_motivo_ultimo=("reason_code", "last"),
    churn_feedback_ultimo=("feedback_text", "last"))
mot = pd.crosstab(chn.account_id, chn.reason_code).add_prefix("churn_motivo_n_")

# ---------------------------------------------------------------- junta tudo
base = perfil.join([rec, uso, sup, ch, mot], how="left")
for c in ["suporte_tickets", "suporte_escalonamentos", "churn_eventos", "churn_reembolso_total",
          "churn_reativacoes", "churn_upgrade_previo", "churn_downgrade_previo", *mot.columns]:
    base[c] = base[c].fillna(0)
base["churn_flag_conta"] = acc.set_index("account_id").churn_flag
base["churn_tem_evento"] = base.churn_eventos > 0
base.index.name = "account_id"
cols = ["perfil", "receita", "uso", "suporte", "churn"]
base = base[[c for p in cols for c in base.columns if c.startswith(p + "_")]]
base.to_csv(OUT / "account_360.csv")

# ---------------------------------------------------------------- dicionário e auditoria
fonte = {"perfil": "accounts", "receita": "subscriptions", "uso": "feature_usage → subscriptions",
         "suporte": "support_tickets", "churn": "churn_events + accounts.churn_flag"}
dic = ["# Dicionário — account_360.csv\n", "Uma linha por conta (500). Colunas agrupadas por categoria.\n"]
for p in cols:
    cs = [c for c in base.columns if c.startswith(p + "_")]
    dic.append(f"\n## {p} — fonte: `{fonte[p]}` ({len(cs)} colunas)\n\n| coluna | tipo | nulos | exemplo |\n|---|---|---|---|")
    for c in cs:
        ex = base[c].dropna()
        ex = ex.iloc[0] if len(ex) else ""
        if isinstance(ex, float):
            ex = round(ex, 3)
        dic.append(f"| `{c}` | {base[c].dtype} | {base[c].isna().sum()} | {ex} |")
(DOCS / "dicionario_account_360.md").write_text("\n".join(dic) + "\n", encoding="utf-8")

aud = ["# Auditoria de ligação entre as tabelas\n",
       "Gerado por `solution/scripts/01_build_dataset.py`. Chaves ligam 100%; **datas entre tabelas não**.\n",
       "| checagem | resultado | leitura |", "|---|---|---|"]
aud += [f"| {n} | {v} | {o} |" for n, v, o in audit]
(DOCS / "auditoria_dados.md").write_text("\n".join(aud) + "\n", encoding="utf-8")

print(f"account_360: {base.shape}  subscription_360: {subx.shape}")
for n, v, o in audit:
    print(f"  {n}: {v}  {o}")
