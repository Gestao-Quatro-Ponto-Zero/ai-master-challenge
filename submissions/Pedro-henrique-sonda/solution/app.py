"""
Lead Scorer — Pipeline Intelligence  (v8)
Score = probabilidade + bônus de recorrência, normalizado 0-100.
Tema visual G4. Zona Limite. Histórico de fechamento na explicação detalhada.
"""

import os
import pandas as pd
import streamlit as st
from datetime import datetime

# ── Constantes ────────────────────────────────────────────────────────────────
MIN_TAXA_COMBO,  MAX_TAXA_COMBO  = 0.52,  0.73
MIN_TAXA_CONTA,  MAX_TAXA_CONTA  = 0.531, 0.750
TAXA_MEDIA_GERAL = 0.632
MIN_DEALS_COMBO  = 30
MIN_DEALS_CONTA  = 5

STATUS_FILE = "data/deal_status.csv"
STATUS_OPTIONS = {
    "nao_contatado": "⬜ Não contatado",
    "contatado":     "📞 Contatado — aguardando retorno",
    "em_negociacao": "🔄 Em negociação — retorno positivo",
    "sem_retorno":   "❌ Sem retorno — reagendar contato",
    "concluido":     "✅ Concluído — negócio avançou",
}
STATUS_COM_ACAO = {"contatado", "em_negociacao", "concluido"}
BADGE_STAGE = {"Prospecting": "🆕 Novo", "Engaging": "🔄 Em andamento"}

ORDENACAO_OPCOES = [
    "Probabilidade (maior chance de fechar)",
    "Valor (maior ticket)",
]
TOP5_TITULOS = {
    ORDENACAO_OPCOES[0]: "🔥 Top 5 — Maior Chance de Fechar",
    ORDENACAO_OPCOES[1]: "🔥 Top 5 — Maior Ticket",
}

FAIXAS_VALOR = [
    "Todos",
    "Premium (acima de $5.000)",
    "Médio ($1.000 a $5.000)",
    "Básico (até $1.000)",
]


# ══════════════════════════════════════════════════════════════════════════════
# 1. DADOS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def carregar_dados():
    pipeline = pd.read_csv("data/sales_pipeline.csv")
    accounts = pd.read_csv("data/accounts.csv")
    products  = pd.read_csv("data/products.csv")
    teams     = pd.read_csv("data/sales_teams.csv")

    pipeline["product"] = pipeline["product"].str.strip().replace({"GTXPro": "GTX Pro"})
    products["product"] = products["product"].str.strip()

    pipeline["engage_date"] = pd.to_datetime(pipeline["engage_date"], errors="coerce")
    pipeline["close_date"]  = pd.to_datetime(pipeline["close_date"],  errors="coerce")

    pipeline = pipeline.merge(accounts[["account","sector","revenue","employees"]], on="account",    how="left")
    pipeline = pipeline.merge(products[["product","series","sales_price"]],         on="product",    how="left")
    pipeline = pipeline.merge(teams[["sales_agent","manager","regional_office"]],   on="sales_agent",how="left")

    # Tratar contas e setores sem match no accounts.csv
    pipeline["account"] = pipeline["account"].fillna("Conta não identificada")
    pipeline["sector"]  = pipeline["sector"].fillna("Setor desconhecido")
    return pipeline


# ══════════════════════════════════════════════════════════════════════════════
# 2. SCORING v6 — Probabilidade + Boost de Recorrência (normalizado 0-100)
# ══════════════════════════════════════════════════════════════════════════════

def _data_referencia(pipeline):
    abertos = pipeline[pipeline["deal_stage"].isin(["Prospecting","Engaging"])]
    return abertos[abertos["engage_date"].notna()]["engage_date"].max()

def _taxas_combo(pipeline):
    f    = pipeline[pipeline["deal_stage"].isin(["Won","Lost"])]
    won  = f[f["deal_stage"]=="Won"].groupby(["sector","product"]).size().rename("won")
    lost = f[f["deal_stage"]=="Lost"].groupby(["sector","product"]).size().rename("lost")
    df   = pd.concat([won, lost], axis=1).fillna(0)
    df["total"] = df["won"] + df["lost"]
    df["taxa"]  = df["won"] / df["total"].replace(0,1)
    return {k: float(v) for k,v in df[df["total"]>=MIN_DEALS_COMBO]["taxa"].items()}

def _taxas_conta(pipeline):
    f    = pipeline[pipeline["deal_stage"].isin(["Won","Lost"])]
    won  = f[f["deal_stage"]=="Won"].groupby("account").size().rename("won")
    lost = f[f["deal_stage"]=="Lost"].groupby("account").size().rename("lost")
    df   = pd.concat([won, lost], axis=1).fillna(0)
    df["total"] = df["won"] + df["lost"]
    df["taxa"]  = df["won"] / df["total"].replace(0,1)
    return {k: float(v) for k,v in df[df["total"]>=MIN_DEALS_CONTA]["taxa"].items()}

def _f_sazonalidade(mes):
    if mes in (3,6,9,12): return 95
    if mes in (2,5,8,11): return 55
    return 35

def _f_tempo(deal_stage, engage_date, data_ref):
    if deal_stage == "Prospecting" or pd.isna(engage_date): return 50
    dias = (data_ref.date() - engage_date.date()).days
    if   dias <=  30: return 45   # deal cru, 57.4% conversão histórica
    elif dias <=  60: return 60   # amadurecendo, 65.6%
    elif dias <=  90: return 65   # zona forte, 66.4%
    elif dias <= 120: return 60   # viável mas se aproximando do limite, 70.6%
    elif dias <= 140: return 45   # limite — último Won histórico = 138 dias
    else:             return 20   # nenhum deal fechou após 138 dias

def _boost_recorrencia(vezes):
    if   vezes == 0:  return 0
    elif vezes <= 3:  return 5
    elif vezes <= 10: return 10
    else:             return 15

@st.cache_data
def calcular_historico_fechamento(pipeline):
    """Retorna dict {(conta, produto): {"media": X, "min": Y, "max": Z}} dos negócios ganhos (Won)."""
    won = pipeline[
        (pipeline["deal_stage"] == "Won") &
        pipeline["close_value"].notna() &
        (pipeline["close_value"] > 0)
    ]
    resultado = {}
    for (conta, produto), grupo in won.groupby(["account", "product"]):
        vals = grupo["close_value"]
        resultado[(conta, produto)] = {
            "media": vals.mean(),
            "min":   vals.min(),
            "max":   vals.max(),
            "n":     len(vals),
        }
    return resultado


@st.cache_data
def calcular_scores(pipeline):
    data_ref  = _data_referencia(pipeline)
    tc        = _taxas_combo(pipeline)
    ta        = _taxas_conta(pipeline)
    sazon_val = _f_sazonalidade(data_ref.month)

    # Histórico de recompras: Won por conta+produto
    recompras = (
        pipeline[pipeline["deal_stage"] == "Won"]
        .groupby(["account", "product"])
        .size()
        .to_dict()
    )

    ab = pipeline[pipeline["deal_stage"].isin(["Prospecting","Engaging"])].copy()

    ab["taxa_conta"] = ab["account"].map(ta).fillna(TAXA_MEDIA_GERAL)
    ab["taxa_combo"] = ab.apply(lambda r: tc.get((r["sector"],r["product"]), TAXA_MEDIA_GERAL), axis=1)

    ab["dias_no_pipeline"] = ab["engage_date"].apply(
        lambda d: (data_ref.date() - d.date()).days if pd.notna(d) else None
    )

    # Fatores brutos (0-100)
    ab["fator_setor_produto"]   = ((ab["taxa_combo"] - MIN_TAXA_COMBO) / (MAX_TAXA_COMBO - MIN_TAXA_COMBO) * 100).clip(0, 100)
    ab["fator_historico_conta"] = ((ab["taxa_conta"] - MIN_TAXA_CONTA) / (MAX_TAXA_CONTA - MIN_TAXA_CONTA) * 100).clip(0, 100)
    ab["fator_sazonalidade"]    = sazon_val
    ab["fator_tempo"]           = ab.apply(lambda r: _f_tempo(r["deal_stage"], r["engage_date"], data_ref), axis=1)

    # Score de probabilidade base (4 fatores, 0-100)
    ab["score_probabilidade"] = (
        ab["fator_setor_produto"]   * 0.35
        + ab["fator_historico_conta"] * 0.30
        + ab["fator_sazonalidade"]    * 0.20
        + ab["fator_tempo"]           * 0.15
    )

    # Recorrência: quantas vezes a conta comprou esse produto (Won)
    ab["recompras"] = ab.apply(
        lambda r: recompras.get((r["account"], r["product"]), 0), axis=1
    )
    ab["boost_recorrencia"] = ab["recompras"].apply(_boost_recorrencia)

    # Score final — normalização CONDICIONAL (boost nunca penaliza)
    def _score_final(row):
        prob  = row["score_probabilidade"]
        boost = row["boost_recorrencia"]
        if boost == 0:
            return round(min(100, prob), 1)
        score_norm = (prob + boost) / 115 * 100
        return round(min(100, max(prob, score_norm)), 1)

    ab["score"] = ab.apply(_score_final, axis=1)

    # Badge de stage (visual, não afeta score)
    ab["badge_stage"] = ab["deal_stage"].map(BADGE_STAGE)

    return ab.reset_index(drop=True), data_ref


def filtrar_por_valor(df, faixa):
    if faixa == "Premium (acima de $5.000)":
        return df[df["sales_price"] >= 5000]
    elif faixa == "Médio ($1.000 a $5.000)":
        return df[(df["sales_price"] >= 1000) & (df["sales_price"] < 5000)]
    elif faixa == "Básico (até $1.000)":
        return df[df["sales_price"] < 1000]
    return df  # "Todos"

def ordenar_df(df, criterio):
    if criterio == ORDENACAO_OPCOES[1]:   # Valor
        return df.sort_values(["sales_price","score"], ascending=[False,False]).reset_index(drop=True)
    return df.sort_values("score", ascending=False).reset_index(drop=True)  # Probabilidade (padrão)


# ══════════════════════════════════════════════════════════════════════════════
# 3. EXPLICAÇÕES
# ══════════════════════════════════════════════════════════════════════════════

def _class_conta(taxa):
    if taxa >= 0.68: return "acima da média"
    if taxa >= 0.58: return "na média"
    return "abaixo da média"

def _class_combo(taxa):
    if taxa >= 0.68: return "forte"
    if taxa >= 0.57: return "média"
    return "fraca"

def _label_sazon(mes):
    if mes in (3,6,9,12): return "mês de fechamento trimestral (boost)"
    if mes in (2,5,8,11): return "meio do trimestre"
    return "início do trimestre"

def _explicacao_curta(row, mes_ref):
    score = row["score"]
    nivel = "alta" if score > 70 else ("média" if score > 40 else "baixa")
    partes = [f"Probabilidade {nivel}"]
    if row["taxa_conta"] >= 0.68 or row["taxa_conta"] <= 0.58:
        partes.append(f"conta {row['account']} {_class_conta(row['taxa_conta'])} ({row['taxa_conta']*100:.0f}%)")
    if row["taxa_combo"] >= 0.68 or row["taxa_combo"] <= 0.57:
        partes.append(f"combo {row['sector']}+{row['product']} {_class_combo(row['taxa_combo'])} ({row['taxa_combo']*100:.0f}%)")
    if mes_ref in (3,6,9,12):
        partes.append("mês de fechamento trimestral")
    if row["deal_stage"] == "Prospecting":
        partes.append("ainda em prospecção")
    return ". ".join(partes) + "."

def _explicacao_detalhada(row, mes_ref, hist_fechamento=None):
    pts_sp = row["fator_setor_produto"]   * 0.35
    pts_ct = row["fator_historico_conta"] * 0.30
    pts_sz = row["fator_sazonalidade"]    * 0.20
    pts_tm = row["fator_tempo"]           * 0.15

    label_tempo = (
        f"{int(row['dias_no_pipeline'])} dias no pipeline"
        if pd.notna(row["dias_no_pipeline"])
        else "sem data de início (estágio: Prospecção)"
    )
    preco      = row["sales_price"] if pd.notna(row["sales_price"]) else 0
    recompras  = int(row.get("recompras", 0))
    boost      = int(row.get("boost_recorrencia", 0))
    prob_base  = row["score_probabilidade"]

    if recompras == 0:
        label_rec = "Primeira vez desta combinação conta + produto — neutro"
    else:
        label_rec = f"Esta conta já comprou este produto {recompras}x (bônus de fidelidade)"

    score_bruto    = prob_base + boost
    score_norm     = (score_bruto / 115) * 100 if boost > 0 else prob_base
    boost_efetivo  = boost > 0 and score_norm > prob_base

    linhas = [
        "📊 **Pontuação detalhada:**",
        "",
        "| Fator | Pontos | Detalhe |",
        "|-------|--------|---------|",
        f"| 🏷️ Produto + Setor | {pts_sp:.1f} / 35 | {row['sector']} + {row['product']} converte {row['taxa_combo']*100:.0f}% ({_class_combo(row['taxa_combo'])}) |",
        f"| 🏢 Histórico da conta | {pts_ct:.1f} / 30 | {row['account']} converte {row['taxa_conta']*100:.0f}% ({_class_conta(row['taxa_conta'])}) |",
        f"| 📅 Sazonalidade | {pts_sz:.1f} / 20 | {_label_sazon(mes_ref)} |",
        f"| ⏱️ Tempo pipeline | {pts_tm:.1f} / 15 | {label_tempo} |",
        f"| | | |",
        f"| 📈 **Probabilidade** | **{prob_base:.1f} / 100** | soma dos 4 fatores acima |",
        f"| 🔄 Recorrência | **+{boost:.1f} pts** | {label_rec} |",    ]

    if boost == 0:
        # Sem boost: score = probabilidade direta
        linhas.append(f"| **🎯 Score Final** | **{row['score']:.1f} / 100** | igual à probabilidade base (sem bônus) |")
    elif boost_efetivo:
        # Bônus efetivo: normalização elevou o score
        linhas.append(f"| | | |")
        linhas.append(f"| 📊 Score bruto | **{score_bruto:.1f}** | = {prob_base:.1f} + {boost:.1f} |")
        linhas.append(f"| **🎯 Score Final** | **{row['score']:.1f} / 100** | = {score_bruto:.1f} ÷ 115 × 100 (bônus aplicado) |")
    else:
        # Bônus insuficiente: normalização reduziria o score, mantém probabilidade base
        linhas.append(f"| **🎯 Score Final** | **{row['score']:.1f} / 100** | probabilidade base mantida (bônus pequeno demais para superar a normalização) |")

    linhas.append(f"| 💰 Valor do deal | ${int(preco):,} | (dado real, não entra no score) |")

    # Histórico de close_value Won para essa conta + produto
    if hist_fechamento is not None:
        chave = (row["account"], row["product"])
        h = hist_fechamento.get(chave)
        if h:
            linhas.append(
                f"| 💵 Histórico de fechamento | ${int(h['media']):,} em média | "
                f"Essa conta fecha {row['product']} por ${int(h['media']):,} em média "
                f"(preço tabela: ${int(preco):,}). Variação: ${int(h['min']):,} a ${int(h['max']):,} |"
            )
        else:
            linhas.append(
                f"| 💵 Histórico de fechamento | — | "
                f"Nenhum fechamento anterior desta conta com este produto |"
            )

    return "\n".join(linhas)


# ══════════════════════════════════════════════════════════════════════════════
# 4. STATUS DOS DEALS
# ══════════════════════════════════════════════════════════════════════════════

def load_deal_status():
    if os.path.exists(STATUS_FILE):
        return pd.read_csv(STATUS_FILE, dtype=str)
    return pd.DataFrame(columns=["opportunity_id","status","updated_at","vendedor"])

def get_deal_status(opportunity_id, df_status):
    row = df_status[df_status["opportunity_id"] == opportunity_id]
    return row.iloc[0]["status"] if not row.empty else "nao_contatado"

def save_deal_status(opportunity_id, status, vendedor):
    df  = load_deal_status()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    mask = df["opportunity_id"] == opportunity_id
    if mask.any():
        df.loc[mask, "status"]     = status
        df.loc[mask, "updated_at"] = now
        df.loc[mask, "vendedor"]   = vendedor
    else:
        df = pd.concat([df, pd.DataFrame([{
            "opportunity_id": opportunity_id,
            "status": status,
            "updated_at": now,
            "vendedor": vendedor,
        }])], ignore_index=True)
    df.to_csv(STATUS_FILE, index=False)

def get_top5_dinamico(df_ordenado, df_status):
    ids_com_acao = set(
        df_status[df_status["status"].isin(STATUS_COM_ACAO)]["opportunity_id"].tolist()
    ) if not df_status.empty else set()
    pendentes = df_ordenado[~df_ordenado["opportunity_id"].isin(ids_com_acao)]
    return pendentes.head(5).reset_index(drop=True)

def get_deals_acompanhamento(df_vis, df_status):
    if df_status.empty:
        return pd.DataFrame()
    ids_acao = set(df_status[df_status["status"].isin(STATUS_COM_ACAO)]["opportunity_id"].tolist())
    em_acomp = df_vis[df_vis["opportunity_id"].isin(ids_acao)].copy()
    if em_acomp.empty:
        return em_acomp
    em_acomp = em_acomp.merge(
        df_status[df_status["status"].isin(STATUS_COM_ACAO)][["opportunity_id","status","updated_at"]],
        on="opportunity_id", how="left"
    )
    return em_acomp.sort_values("score", ascending=False).reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# 5. KPIs POR VENDEDOR
# ══════════════════════════════════════════════════════════════════════════════

def calcular_kpis_vendedor(pipeline, filtro_vendedor):
    subset = pipeline if filtro_vendedor == "Todos" else pipeline[pipeline["sales_agent"] == filtro_vendedor]
    won    = subset[subset["deal_stage"] == "Won"]
    lost   = subset[subset["deal_stage"] == "Lost"]
    total  = len(won) + len(lost)

    taxa  = len(won) / total if total > 0 else None

    won_datas = won.dropna(subset=["engage_date","close_date"])
    ciclo = (won_datas["close_date"] - won_datas["engage_date"]).dt.days.mean() if len(won_datas) > 0 else None

    won_valor = won[won["close_value"] > 0] if "close_value" in won.columns else pd.DataFrame()
    ticket = won_valor["close_value"].mean() if len(won_valor) > 0 else None

    return taxa, ciclo, ticket


# ══════════════════════════════════════════════════════════════════════════════
# 6. COMPONENTES DE INTERFACE
# ══════════════════════════════════════════════════════════════════════════════

def _cor_score(v):
    if v > 70:  return "#2d9e2d"
    if v >= 40: return "#c49a00"
    return "#b02020"

def colorir_score(val):
    try:    v = float(val)
    except: return ""
    if v > 70:  return "background-color:#c8f7c5;color:#1a6b16;font-weight:bold"
    if v >= 40: return "background-color:#fff3cd;color:#856404"
    return      "background-color:#f8d7da;color:#842029"


def render_kpis(df_vis, pipeline, filtro_vendedor):
    c1, c2, c3 = st.columns(3)
    c1.metric("Negócios em Aberto",          len(df_vis))
    c2.metric("Alta Prioridade (score > 70)", int((df_vis["score"] > 70).sum()))
    valor_total = df_vis["sales_price"].sum() if len(df_vis) > 0 else 0
    c3.metric("Valor Potencial Total",        f"${int(valor_total):,}")

    taxa, ciclo, ticket = calcular_kpis_vendedor(pipeline, filtro_vendedor)
    label = f"Desempenho de {filtro_vendedor}" if filtro_vendedor != "Todos" else "Desempenho Geral"
    st.caption(f"📈 {label}")
    c4, c5, c6 = st.columns(3)
    c4.metric("Taxa de Conversão",         f"{taxa*100:.1f}%"    if taxa   is not None else "—")
    c5.metric("Ciclo Médio de Fechamento", f"{int(ciclo)} dias"   if ciclo  is not None else "—")
    c6.metric("Ticket Médio",              f"${int(ticket):,}"   if ticket is not None else "—")


def render_expander_como_funciona():
    with st.expander("ℹ️ Como funciona o Score? (clique para entender)"):
        st.markdown("""
## Como calculamos o Score de cada deal?

O score vai de **0 a 100** e mede a **probabilidade de fechar** o deal, com bônus para clientes que já compraram antes.

---

### Os 4 fatores da probabilidade

Analisamos todo o histórico de vendas (mais de 8.800 negociações passadas) para identificar quais fatores realmente influenciam se um deal fecha ou não. Testamos 13 hipóteses diferentes e apenas 4 fatores se mostraram estatisticamente relevantes. Os pesos refletem o impacto real de cada fator nos dados:

**🏷️ Produto + Setor do cliente (peso: 35%)**
Analisamos a taxa de conversão de cada combinação de produto e setor. A variação é de 52% a 73% — são 20 pontos de diferença, o segundo maior preditor nos dados. Por exemplo, MG Special para telecom fecha 73% das vezes, enquanto MG Advanced para serviços fecha só 52%. O peso de 35% reflete esse alto impacto.

**🏢 Histórico da conta (peso: 30%)**
Cada conta tem sua própria taxa de conversão histórica. Varia de 53% (Statholdings) a 75% (Rangreen) — são 22 pontos de diferença. Contas que historicamente fecham mais deals continuam fechando. O peso de 30% reflete que a conta é um preditor forte.

**📅 Momento do trimestre (peso: 20%)**
Descobrimos um padrão trimestral nos dados: meses de final de trimestre (março, junho, setembro, dezembro) convertem em torno de 80%, enquanto meses de início de trimestre caem para ~49%. São 34 pontos de diferença — o maior preditor em teoria. Porém, como esse fator é igual para todos os deals no mesmo momento, ele diferencia menos na prática, por isso o peso é 20% e não maior.

**⏱️ Tempo no pipeline (peso: 15%)**
Analisamos quanto tempo os deals levam para fechar. Descobrimos que:
- O ciclo médio de fechamento (Won) é de **52 dias**
- 75% dos deals que fecham, fecham em até **88 dias**
- **Nenhum deal na história fechou após 138 dias**

Isso significa que deals abertos há mais de 140 dias provavelmente estão mortos. O peso é 15% porque a relação entre tempo e conversão não é linear — deals muito novos (0-30 dias) também têm conversão mais baixa (57%) porque muitos ainda vão cair.

---

### Bônus de recorrência 🔄

Se a conta já comprou **esse mesmo produto** antes, o deal recebe pontos extras. Isso reflete a realidade: clientes recorrentes tendem a comprar de novo.

- Nunca comprou esse produto: **+0 pontos** (neutro, sem penalidade)
- 1 a 3 compras anteriores: **+5 pontos**
- 4 a 10 compras anteriores: **+10 pontos**
- 11 ou mais compras: **+15 pontos**

O bônus nunca reduz o score — apenas aumenta. Quem não tem recorrência fica exatamente com a probabilidade base.

Quando há bônus, o score é normalizado para manter a escala de 0 a 100 (dividido por 115 e multiplicado por 100, onde 115 é o máximo teórico: 100 da probabilidade + 15 do bônus).

---

### E o valor do deal?

O valor do deal **NÃO** está dentro do score — porque mede coisas diferentes. O score diz "qual a chance de fechar". O valor diz "quanto vale se fechar".

Use o filtro **💰 Faixa de Valor** na barra lateral para focar nos deals do tamanho que você quer trabalhar, e use o score para priorizar dentro dessa faixa.

---

### O que significam as cores:

🟢 **Verde (acima de 70)** — Alta probabilidade de fechar. Priorize.
🟡 **Amarelo (40 a 70)** — Probabilidade moderada. Acompanhe.
🔴 **Vermelho (abaixo de 40)** — Baixa probabilidade. Reavalie a abordagem.

---

### Sobre o estágio (🆕 Novo / 🔄 Em andamento):

O estágio **NÃO** afeta o score. O score mede **potencial**, não progresso. Um deal novo (Prospecting) com alto potencial aparece no topo — porque precisa urgentemente do seu primeiro contato antes de esfriar.
""")


def render_top5(df_ordenado, df_status, filtro_vendedor, mes_ref, criterio, hist_fechamento=None):
    titulo = TOP5_TITULOS.get(criterio, "🔥 Top 5 Prioridades")
    st.subheader(titulo + " — Deals Pendentes de Ação")

    top5 = get_top5_dinamico(df_ordenado, df_status)

    if top5.empty:
        st.success("🎉 Todos os negócios prioritários já foram trabalhados! Revise os negócios em acompanhamento abaixo.")
        return

    for rank, (_, row) in enumerate(top5.iterrows(), start=1):
        status_atual = get_deal_status(row["opportunity_id"], df_status)
        score        = row["score"]
        cor          = _cor_score(score)

        dias_str  = str(int(row["dias_no_pipeline"])) if pd.notna(row["dias_no_pipeline"]) else "—"
        preco_str = f"${int(row['sales_price']):,}"   if pd.notna(row["sales_price"])      else "—"
        badge     = row.get("badge_stage", "")

        with st.container():
            col_info, col_status = st.columns([4, 1])

            with col_info:
                st.markdown(
                    f"""<div style="border-left:5px solid {cor}; padding:10px 16px;
                                    background:#112240; border-radius:4px; margin-bottom:4px">
                        <div style="font-size:1.15em; font-weight:bold; color:#FFFFFF">
                            #{rank} — {row['account']}
                            &nbsp;&nbsp;
                            <span style="font-size:0.85em; font-weight:normal; color:#8892A0">{badge}</span>
                        </div>
                        <div style="color:#FFFFFF; margin:2px 0">
                            Score <strong style="color:{cor}">{score}</strong>
                            &nbsp;|&nbsp; {row['product']} · {preco_str} · {dias_str} dias
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                with st.expander("📊 Pontuação detalhada"):
                    st.markdown(_explicacao_detalhada(row, mes_ref, hist_fechamento))

            with col_status:
                st.write("")
                novo_status = st.selectbox(
                    "Status",
                    options=list(STATUS_OPTIONS.keys()),
                    format_func=lambda x: STATUS_OPTIONS[x],
                    index=list(STATUS_OPTIONS.keys()).index(status_atual),
                    key=f"status_{row['opportunity_id']}",
                    label_visibility="collapsed",
                )
                if novo_status != status_atual:
                    vendedor_deal = filtro_vendedor if filtro_vendedor != "Todos" else row.get("sales_agent","")
                    save_deal_status(row["opportunity_id"], novo_status, vendedor_deal)
                    st.rerun()


def render_acompanhamento(df_vis, df_status, mes_ref):
    em_acomp = get_deals_acompanhamento(df_vis, df_status)
    if em_acomp.empty:
        return

    with st.expander(f"📋 Deals em Acompanhamento ({len(em_acomp)} deals)"):
        for _, row in em_acomp.iterrows():
            status_label = STATUS_OPTIONS.get(row.get("status",""), row.get("status",""))
            updated      = row.get("updated_at","")
            score        = row["score"]
            cor          = _cor_score(score)

            dias_str  = str(int(row["dias_no_pipeline"])) if pd.notna(row["dias_no_pipeline"]) else "—"
            preco_str = f"${int(row['sales_price']):,}"   if pd.notna(row["sales_price"])      else "—"
            badge     = row.get("badge_stage","")

            st.markdown(
                f"""<div style="border-left:4px solid {cor}; padding:8px 14px;
                                background:#112240; border-radius:4px; margin-bottom:6px; opacity:0.9">
                    <strong style="color:#FFFFFF">{row['account']}</strong> &nbsp;
                    <span style="color:#8892A0">{badge}</span> &nbsp;
                    <span style="color:{cor}; font-weight:bold">Score {score}</span>
                    &nbsp;|&nbsp; <span style="color:#FFFFFF">{row['product']} · {preco_str} · {dias_str} dias</span>
                    <br>
                    <span style="font-size:0.85em; color:#C5A55A">{status_label}</span>
                    <span style="font-size:0.8em; color:#8892A0"> — atualizado em {updated}</span>
                </div>""",
                unsafe_allow_html=True,
            )


def render_zona_limite(df_vis, mes_ref, hist_fechamento):
    """Seção condicional: negócios entre 120-140 dias no pipeline — próximos do limite histórico."""
    zona_base = df_vis[
        df_vis["dias_no_pipeline"].notna() &
        (df_vis["dias_no_pipeline"] >= 120) &
        (df_vis["dias_no_pipeline"] <= 140)
    ].reset_index(drop=True)

    if zona_base.empty:
        return

    total = len(zona_base)
    st.divider()
    st.subheader(f"⚡ Deals na Zona Limite — {total} deal{'s' if total > 1 else ''}")

    criterio_zona = st.radio(
        "📊 Ordenar por:",
        options=ORDENACAO_OPCOES,
        horizontal=True,
        key="ordenar_zona_limite",
    )
    zona = ordenar_df(zona_base, criterio_zona)
    st.warning(
        "Historicamente, nenhum negócio foi fechado após 138 dias no pipeline. "
        "Estes negócios estão próximos do limite e precisam de ação imediata ou reavaliação."
    )

    # Controle de quantos exibir via session_state
    chave_ver_mais = "zona_limite_ver_mais"
    if chave_ver_mais not in st.session_state:
        st.session_state[chave_ver_mais] = False

    limite = total if st.session_state[chave_ver_mais] else min(10, total)
    df_exibir = zona.iloc[:limite]

    def _card_zona(row):
        score = row["score"]
        cor   = _cor_score(score)
        dias  = int(row["dias_no_pipeline"])
        preco = f"${int(row['sales_price']):,.0f}" if pd.notna(row.get("sales_price")) else "—"
        badge = row.get("badge_stage", "")
        st.markdown(
            f"""<div style="border-left:5px solid {cor}; padding:10px 16px;
                            background:#1a2a1a; border-radius:4px; margin-bottom:8px">
                <strong style="color:#FFFFFF">{row['account']}</strong> &nbsp;
                <span style="color:#8892A0">{badge}</span> &nbsp;
                <span style="color:{cor}; font-weight:bold">Score {score}</span>
                &nbsp;|&nbsp; <span style="color:#FFFFFF">{row['product']} · {preco} · {row.get('sales_agent','—')}</span>
                &nbsp;|&nbsp; <strong style="color:{cor}">{dias} dias no pipeline</strong>
            </div>""",
            unsafe_allow_html=True,
        )
        with st.expander(f"📊 Pontuação detalhada — {row['account']}"):
            st.markdown(_explicacao_detalhada(row, mes_ref, hist_fechamento))

    for _, row in df_exibir.iterrows():
        _card_zona(row)

    if total > 10 and not st.session_state[chave_ver_mais]:
        if st.button(f"Ver todos ({total - 10} negócios restantes)", key="btn_zona_ver_mais"):
            st.session_state[chave_ver_mais] = True
            st.rerun()
    elif st.session_state[chave_ver_mais] and total > 10:
        if st.button("Mostrar menos", key="btn_zona_ver_menos"):
            st.session_state[chave_ver_mais] = False
            st.rerun()


def render_tabela(df_ordenado, mes_ref, hist_fechamento=None):
    st.divider()
    st.subheader("📋 Pipeline Completo")

    # Seletor de ordenação independente
    criterio_pipeline = st.radio(
        "📊 Ordenar pipeline por:",
        options=ORDENACAO_OPCOES,
        horizontal=True,
        key="ordenar_pipeline",
    )
    df_pipeline = ordenar_df(df_ordenado, criterio_pipeline).reset_index(drop=True)

    st.caption(f"{len(df_pipeline)} negócios encontrados")

    if df_pipeline.empty:
        st.info("Nenhum negócio encontrado com os filtros selecionados.")
        return

    # Preparar df de exibição com colunas renomeadas
    df_pipeline = df_pipeline.copy()
    df_pipeline["recorrencia_fmt"] = df_pipeline["recompras"].apply(lambda x: f"{int(x)}x")
    df_pipeline["dias_fmt"] = df_pipeline["dias_no_pipeline"].apply(
        lambda x: int(x) if pd.notna(x) else None
    )

    colunas_map = {
        "score":            "Score",
        "badge_stage":      "Estágio",
        "account":          "Conta",
        "sector":           "Setor",
        "product":          "Produto",
        "sales_price":      "Valor ($)",
        "sales_agent":      "Vendedor",
        "dias_fmt":         "Dias",
        "recorrencia_fmt":  "Recorrência",
    }
    df_exib = df_pipeline[list(colunas_map.keys())].rename(columns=colunas_map).copy()

    # Coluna de checkbox no início
    df_exib.insert(0, "ver score", False)

    column_config = {
        "ver score":   st.column_config.CheckboxColumn("ver score", default=False, width="small"),
        "Score":       st.column_config.NumberColumn("Score", format="%.1f"),
        "Valor ($)":   st.column_config.NumberColumn("Valor ($)", format="$%d"),
        "Dias":        st.column_config.NumberColumn("Dias"),
    }

    edited = st.data_editor(
        df_exib,
        column_config=column_config,
        disabled=[col for col in df_exib.columns if col != "ver score"],
        use_container_width=True,
        hide_index=True,
        key="pipeline_editor",
    )

    # Mostrar explicação detalhada de cada deal marcado
    selecionados = edited[edited["ver score"] == True]
    if not selecionados.empty:
        for pos in selecionados.index:
            row = df_pipeline.iloc[pos]
            with st.container(border=True):
                st.subheader(f"📊 {row['account']} — {row['product']}")
                st.markdown(_explicacao_detalhada(row, mes_ref, hist_fechamento))
    # (se nenhum marcado, não mostra nada — tabela fala por si só)


# ══════════════════════════════════════════════════════════════════════════════
# 7. MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    st.set_page_config(page_title="Lead Scorer — G4", page_icon="🎯", layout="wide")

    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', 'Helvetica Neue', sans-serif;
    }

    .stApp {
        background-color: #0A1628;
    }

    [data-testid="stSidebar"] {
        background-color: #0D1B2A;
        border-right: 1px solid #1E3A5F;
    }

    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] h3 {
        color: #C5A55A;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }

    h1 {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
    }

    h2 {
        color: #C5A55A !important;
        font-weight: 700 !important;
    }

    h3 {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricValue"] {
        color: #C5A55A !important;
        font-weight: 700;
    }

    [data-testid="stMetricLabel"] {
        color: #8892A0 !important;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.08em;
    }

    [data-testid="stExpander"] {
        background-color: #112240;
        border: 1px solid #1E3A5F;
        border-radius: 8px;
    }

    .streamlit-expanderHeader {
        color: #FFFFFF !important;
        background-color: #112240 !important;
    }

    hr {
        border-color: #1E3A5F;
    }

    .stDataFrame, [data-testid="stDataEditor"] {
        border: 1px solid #1E3A5F;
        border-radius: 8px;
    }

    .stSelectbox [data-baseweb="select"] {
        background-color: #112240;
        border-color: #1E3A5F;
    }

    .stRadio [role="radiogroup"] label {
        color: #FFFFFF;
    }

    .stCaption, small {
        color: #8892A0 !important;
    }

    a {
        color: #C5A55A !important;
    }

    .stMarkdown table th {
        background-color: #112240;
        color: #C5A55A;
        padding: 8px 12px;
        border-bottom: 2px solid #C5A55A;
    }

    .stMarkdown table td {
        padding: 6px 12px;
        border-bottom: 1px solid #1E3A5F;
        color: #FFFFFF;
    }

    [data-testid="stContainer"] {
        border-color: #1E3A5F;
    }

    .stTextInput input {
        background-color: #112240;
        border-color: #1E3A5F;
        color: #FFFFFF;
    }

    .stNumberInput input {
        background-color: #112240;
        border-color: #1E3A5F;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

    st.title("🎯 Lead Scorer — Pipeline Intelligence")

    with st.spinner("Carregando dados e calculando scores..."):
        pipeline        = carregar_dados()
        df, data_ref    = calcular_scores(pipeline)
        hist_fechamento = calcular_historico_fechamento(pipeline)

    mes_ref = data_ref.month
    st.caption(
        f"📅 Data de referência dos dados: {data_ref.strftime('%d/%m/%Y')} "
        f"· {len(df)} negócios em aberto"
    )

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    st.sidebar.header("Filtros")

    # 1. Faixa de valor — PRIMEIRO (o vendedor define o foco)
    filtro_valor = st.sidebar.selectbox("💰 Faixa de Valor", FAIXAS_VALOR)

    # 2-4. Escritório → Gestor → Vendedor (encadeados)
    escritorios = ["Todos"] + sorted(df["regional_office"].dropna().unique().tolist())
    filtro_office = st.sidebar.selectbox("Escritório Regional", escritorios)

    df_off = df if filtro_office == "Todos" else df[df["regional_office"] == filtro_office]

    managers = ["Todos"] + sorted(df_off["manager"].dropna().unique().tolist())
    filtro_manager = st.sidebar.selectbox("Gestor", managers)

    df_mgr = df_off if filtro_manager == "Todos" else df_off[df_off["manager"] == filtro_manager]

    vendedores = ["Todos"] + sorted(df_mgr["sales_agent"].dropna().unique().tolist())
    filtro_vendedor = st.sidebar.selectbox("Vendedor", vendedores)

    # 5. Estágio
    filtro_stage = st.sidebar.selectbox("Estágio", ["Todos", "Prospecting", "Engaging"])

    # ── FILTROS ───────────────────────────────────────────────────────────────
    df_vis = df.copy()
    df_vis = filtrar_por_valor(df_vis, filtro_valor)
    if filtro_office   != "Todos": df_vis = df_vis[df_vis["regional_office"] == filtro_office]
    if filtro_manager  != "Todos": df_vis = df_vis[df_vis["manager"]         == filtro_manager]
    if filtro_vendedor != "Todos": df_vis = df_vis[df_vis["sales_agent"]     == filtro_vendedor]
    if filtro_stage    != "Todos": df_vis = df_vis[df_vis["deal_stage"]      == filtro_stage]

    # ── KPIs ──────────────────────────────────────────────────────────────────
    render_kpis(df_vis, pipeline, filtro_vendedor)
    st.divider()

    # ── COMO FUNCIONA ─────────────────────────────────────────────────────────
    render_expander_como_funciona()
    st.divider()

    # ── ORDENAÇÃO — no corpo principal, acima do Top 5 ────────────────────────
    criterio_ordem = st.radio(
        "📊 Ordenar deals por:",
        options=ORDENACAO_OPCOES,
        horizontal=True,
    )
    df_vis = ordenar_df(df_vis, criterio_ordem)

    # ── TOP 5 DINÂMICO ────────────────────────────────────────────────────────
    df_status = load_deal_status()
    render_top5(df_vis, df_status, filtro_vendedor, mes_ref, criterio_ordem, hist_fechamento)

    # ── DEALS EM ACOMPANHAMENTO ───────────────────────────────────────────────
    render_acompanhamento(df_vis, df_status, mes_ref)

    # ── ZONA LIMITE (condicional: 120-140 dias) ───────────────────────────────
    render_zona_limite(df_vis, mes_ref, hist_fechamento)

    # ── PIPELINE COMPLETO ─────────────────────────────────────────────────────
    render_tabela(df_vis, mes_ref, hist_fechamento)


if __name__ == "__main__":
    main()
