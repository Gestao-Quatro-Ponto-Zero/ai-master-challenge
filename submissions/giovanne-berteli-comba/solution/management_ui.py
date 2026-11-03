"""Reviewer-facing aggregate views, prospective actions and capacity sandbox."""

import json
import altair as alt
import pandas as pd
import streamlit as st

from diagnose_support import scenario
from management import ROOT, business_actions, load_reports

SCENARIOS = {"downside": "Desfavorável", "conservative": "Conservador", "reference": "Referência", "optimistic": "Otimista"}


def number(value, digits=0):
    return f"{value:,.{digits}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def select_audience():
    return st.selectbox("Perfil de visualização", ["company", "instructor"], key="audience",
                        format_func=lambda value: {"company": "Empresa", "instructor": "Instrutor"}[value])


def horizontal_counts(rows, category, value, series=None):
    """Keep long category names upright and complete, including narrow screens."""
    frame = pd.DataFrame(rows)
    base = alt.Chart(frame).encode(
        y=alt.Y(field=category, type="nominal", sort=None, title=None,
                  axis=alt.Axis(labelAngle=0, labelLimit=0)),
        x=alt.X(field=value, type="quantitative", title="Tickets",
                  scale=alt.Scale(domain=[0, float(frame[value].max()) * 1.18 or 1])),
        tooltip=[alt.Tooltip(field=category, type="nominal"), alt.Tooltip(field=value, type="quantitative", format=",")])
    bars = base.mark_bar(cornerRadiusEnd=3, color="#86c5f4")
    if series:
        bars = bars.encode(yOffset=alt.YOffset(field=series), color=alt.Color(field=series, title=None,
                           scale=alt.Scale(domain=["Encerrados", "Não encerrados"], range=["#1e8b76", "#e4a64c"])))
        return bars.properties(height=max(160, 58 * frame[category].nunique()))
    labels = base.mark_text(align="right", baseline="middle", dx=-8, color="#112237", fontSize=12).encode(text=alt.Text(field=value, type="quantitative", format=","))
    return (bars + labels).properties(height=max(150, 42 * len(frame)))


def render_company(root=ROOT, operations=False):
    if operations:
        from batch_ui import render_batch_workspace
        results, batch, capacity = st.tabs(["Resultados do suporte", "Triagem em lote", "Capacidade"])
        with batch:
            render_batch_workspace()
    else:
        results, capacity = st.tabs(["Resultados do suporte", "Capacidade"])
    with results:
        render_overview(root, audience="company")
    with capacity:
        render_capacity(root, audience="company")


def render_instructor_guide(aggregate_only=False):
    st.header("Guia do instrutor")
    from batch_ui import render_learning
    render_learning()
    st.write("Comece pelo diagnóstico, teste o fluxo e confira as evidências. A visão Empresa reúne resultados e decisões; esta visão explica o desenvolvimento e a validação.")
    st.subheader("Quem fez o quê")
    st.markdown("**Humano:** escolheu o desafio, definiu requisitos de anomalias e evidências, confrontou setup/CodeTour e direcionou clareza e valor de negócio.\n\n"
                "**IA:** auditou dados, propôs métodos, implementou código, calculou resultados e executou testes sob essa direção. A triagem usa TF-IDF e regressão logística.")
    st.subheader("Percurso para testar")
    st.markdown("1. **Diagnóstico e resultados:** confira contagens, fontes, ações e a comparação do classificador.\n"
                "2. **Triagem em lote:** inicie o cronômetro, importe o CSV, confira/corrija linhas e exporte. **Experimento:** realize as duas etapas com casos distintos. A triagem individual continua disponível para inspecionar um exemplo.\n"
                "3. **Revisão e anomalias:** registre uma decisão, recarregue, filtre e exporte.\n"
                "4. **Capacidade:** altere premissas e experimente o cenário desfavorável.\n"
                "5. **Evoluções planejadas:** veja as ideias deixadas para continuidade.")
    if aggregate_only:
        st.info("Esta é a consulta de agregados. Para habilitar Triagem e Revisão, encerre o servidor com Ctrl+C e execute o comando completo abaixo; depois selecione Instrutor.")
        st.code("bash submissions/giovanne-berteli-comba/run.sh", language="bash")
    st.subheader("Revisar o código com CodeTour")
    st.write("Na raiz do repositório, com VS Code instalado, execute:")
    st.code("bash submissions/giovanne-berteli-comba/review.sh", language="bash")
    st.caption("Abre o workspace correto e confere/instala a extensão oficial. Clique em Start CodeTour; são 13 paradas. A instalação da extensão requer rede. Alternativa sem extensão: docs/code-tour.md.")
    st.subheader("Como julgar a força da entrega")
    st.dataframe([
        {"Dimensão": "Classificação retrospectiva", "Evidência": "Macro F1 0,844612 vs 0,646094 do baseline; 7.175 casos", "Leitura": "Melhoria demonstrada neste benchmark IT"},
        {"Dimensão": "Fluxo funcional", "Evidência": "Persistência, revisão, falhas e exportação verificadas por software", "Leitura": "Protótipo verificável; não é validação de produção"},
        {"Dimensão": "Diagnóstico operacional", "Evidência": "Fila e notas quantificadas; sem abertura/esforço ativo confiáveis", "Leitura": "Parcial para responder duração, causas e desperdício real"},
        {"Dimensão": "Benefício para o negócio", "Evidência": "Cenários de −26,67 a +74,75 h/mês", "Leitura": "Hipótese; falta piloto representativo e ganho medido"},
        {"Dimensão": "Uso de IA e direção humana", "Evidência": "Decisões, correções e conversas preservadas com limites", "Leitura": "Processo rastreável; avaliação humana do candidato permanece com o instrutor"},
    ], hide_index=True)
    st.caption("Esta leitura das evidências não é uma nota do processo seletivo. O baseline comparado é o modelo de texto do projeto; o baseline privado da seleção não foi acessado.")
    st.write("Fontes para aprofundar: README.md · docs/start-here.md · docs/demo-guide.md · docs/final-evaluation.md · process-log/README.md.")


def render_overview(root=ROOT, audience="instructor"):
    instructor = audience == "instructor"
    st.header("Diagnóstico e resultados")
    st.write("A decisão proposta é validar a fila, instrumentar esforço e testar triagem assistida com confirmação humana.")
    try:
        diagnosis, evaluation, _ = load_reports(root)
    except (OSError, ValueError):
        st.error("Resultados agregados indisponíveis. Confira os arquivos data/diagnosis.json, data/final-evaluation.json e data/diagnosis-assumptions.json da submissão.")
        return
    overall = diagnosis["overall"]
    st.subheader("Atendimento ao cliente · retrato dos dados")
    cols = st.columns(4)
    cols[0].metric("Tickets na base", number(overall["tickets"]))
    cols[1].metric("Não encerrados", number(overall["nonclosed"]))
    cols[2].metric("Notas 1–2 entre avaliados", number(100 * overall["low_csat_count"] / overall["rated_closed"], 2) + "%")
    cols[3].metric("Cobertura das notas", number(100 * overall["rated_closed"] / overall["tickets"], 2) + "%")
    st.caption(f"Notas: {number(overall['rated_closed'])} encerrados avaliados / {number(overall['tickets'])} tickets. Os não encerrados não têm nota.")
    st.write(f"Média das notas: **{number(overall['csat_mean'], 2)}/5**, somente entre encerrados avaliados.")
    with st.expander("Distribuição das notas dos encerrados"):
        st.bar_chart(pd.DataFrame([{"Nota": str(i), "Respostas": overall[f"score_{i}"]} for i in range(1,6)]).set_index("Nota"))
    st.info("O arquivo não registra abertura nem esforço ativo. Não permite medir idade da fila, SLA, duração total ou horas desperdiçadas. Status e prioridades precisam de conferência com a operação.")
    dimension = st.selectbox("Comparar composição por", ["Ticket Channel", "Ticket Priority", "Ticket Type"],
                             format_func=lambda k: {"Ticket Channel": "Canal", "Ticket Priority": "Prioridade", "Ticket Type": "Tipo"}[k])
    groups = [r for r in diagnosis["single_dimension_groups"] if r["grouping"] == dimension]
    rows = [{"Grupo": r[dimension], "Situação": label, "Tickets": r[key]} for r in groups
            for key, label in [("closed", "Encerrados"), ("nonclosed", "Não encerrados")]]
    st.altair_chart(horizontal_counts(rows, "Grupo", "Tickets", "Situação"), width="stretch")
    st.dataframe(pd.DataFrame([{"Grupo": r[dimension], "Tickets": r["tickets"], "Não encerrados": r["nonclosed"],
                                "% não encerrados": round(100*r["nonclosed"]/r["tickets"], 2), "Notas": r["rated_closed"],
                                "Média da nota": round(r["csat_mean"], 2)} for r in groups]), hide_index=True)
    st.caption(("Fonte: data/diagnosis.json · " if instructor else "") + "Contagem do retrato, não taxa no tempo. Cada dimensão divide a mesma base; não somar os recortes. As associações examinadas com notas não demonstram causas.")
    st.subheader("O que fazer com isso")
    actions = business_actions(diagnosis, evaluation, include_benchmark=instructor)
    st.dataframe(actions, hide_index=True)
    st.caption("Ações e responsáveis são propostas. O piloto deve medir o fluxo atual e o assistido, com critérios de qualidade e ganho líquido definidos antes dos resultados.")
    if not instructor:
        st.download_button("Baixar resumo dos resultados", json.dumps({"scope": "Customer support snapshot and proposed actions; no measured savings",
                            "source": "data/diagnosis.json", "overall": overall, "proposed_actions": actions}, ensure_ascii=False, indent=2),
                           "resumo-suporte.json", "application/json", on_click="ignore")
        return
    st.subheader("Benchmark IT · população distinta do atendimento")
    assisted = evaluation["assisted"]
    cols = st.columns(3)
    cols[0].metric("Macro F1 · modelo", number(evaluation["classifier_metrics"][evaluation["selected_model"]]["macro_f1"], 6))
    cols[1].metric("Macro F1 · baseline de texto", number(evaluation["classifier_metrics"]["multinomial_nb"]["macro_f1"], 6))
    cols[2].metric("Casos avaliados", number(evaluation["population"]))
    queue_names = {"standard_review": "Confirmação padrão", "specialist_review": "Especialista", "triage_review": "Triagem"}
    rows = [{"Fila": queue_names[k], "Casos": assisted["queue_counts"][k]} for k in ["standard_review", "specialist_review", "triage_review"]]
    st.altair_chart(horizontal_counts(rows, "Fila", "Casos"), width="stretch")
    st.dataframe(rows, hide_index=True)
    gain = evaluation["classifier_metrics"][evaluation["selected_model"]]["macro_f1"] - evaluation["classifier_metrics"]["multinomial_nb"]["macro_f1"]
    st.write(f"O classificador superou o baseline de texto em **{number(gain, 6)} de macro F1** neste dataset. Isso demonstra melhora de classificação retrospectiva; o ganho operacional ainda precisa ser medido.")
    st.write(f"**{number(100*assisted['standard_coverage'], 2)}% de cobertura padrão** ({number(assisted['standard_cases'])}/{number(evaluation['population'])}) · "
             f"**{number(100*assisted['standard_accuracy'], 2)}% de concordância** apenas nesse subconjunto ({number(assisted['standard_correct'])}/{number(assisted['standard_cases'])}).")
    specialist = sum(v["standard_cases"]-v["standard_correct"] for k,v in assisted["standard_by_true_class"].items()
                     if k in evaluation["policy"]["specialist_categories"])
    st.warning(f"{assisted['standard_errors']} divergências na fila padrão; {specialist} tinham rótulo de classe especializada. Todas as filas exigem confirmação humana. Cobertura não é resolução automática.")
    st.caption("Fonte: data/final-evaluation.json · teste retrospectivo já consumido. Os agregados são lidos sem inferência. Não há transferência de desempenho para clientes nem economia operacional medida.")
    with st.expander("Qualidade por categoria IT"):
        st.dataframe([{"Classe": k, "Casos": v["support"], "Precisão": v["precision"], "Recall": v["recall"], "F1": v["f1-score"]}
                      for k,v in evaluation["classifier_metrics"][evaluation["selected_model"]]["per_class"].items() if k in evaluation["classes"]], hide_index=True)
    with st.expander("Quem fez o quê e como conferir"):
        st.markdown("**Humano:** escolheu o desafio, definiu requisitos de anomalias, finalidade das evidências e estes critérios de revisão; confrontou setup e descoberta do CodeTour.\n\n"
                    "**IA:** auditou dados, propôs métodos, calculou resultados, implementou código e testes sob essa direção. A triagem local usa TF-IDF e regressão logística.\n\n"
                    "**Evidências:** README.md, docs/demo-guide.md e process-log/README.md preservam decisões e correções. Não houve adjudicação humana dos rótulos.")
    st.download_button("Baixar resumo com fontes", json.dumps({"sources": ["data/diagnosis.json", "data/final-evaluation.json"],
                        "scope": "Aggregate retrospective results and proposed actions; no measured savings or automatic resolution",
                        "overall": overall, "assisted": assisted, "proposed_actions": actions}, ensure_ascii=False, indent=2),
                       "resumo-resultados.json", "application/json", on_click="ignore")


def render_capacity(root=ROOT, audience="instructor"):
    st.header("Simulador de capacidade")
    st.warning("Cenários hipotéticos · não são horas medidas, economia de caixa ou ROI financeiro. A cobertura de clientes não é preenchida com o benchmark IT.")
    try:
        config = json.loads((root / "data/diagnosis-assumptions.json").read_text())
    except (OSError, ValueError):
        st.error("Premissas indisponíveis: data/diagnosis-assumptions.json.")
        return
    selected = st.selectbox("Cenário de partida", config["scenarios"], index=2, format_func=lambda c: SCENARIOS[c["name"]], key="capacity_scenario_choice")
    values = {"name": "interactive", "review_share": 1}
    fields = [("tickets", "Tickets/mês", False), ("eligible_share", "Elegíveis (%)", True),
              ("assisted_share", "Assistidos entre elegíveis (%)", True), ("manual_minutes", "Minutos manuais por caso", False),
              ("assisted_minutes", "Minutos assistidos sem revisão", False), ("review_minutes", "Revisão adicional por caso (min)", False),
              ("error_share", "Casos com retrabalho (%)", True), ("rework_minutes", "Minutos por retrabalho", False),
              ("fixed_minutes", "Preparação/monitoramento no mês (min)", False), ("hourly_value_brl", "Valor hipotético da capacidade (R$/h)", False)]
    with st.form("capacity_form"):
        cols = st.columns(2)
        for i, (field, label, rate) in enumerate(fields):
            value = cols[i%2].number_input(label, min_value=0.0, max_value=100.0 if rate else 1e9,
                                           value=float(selected[field])*(100 if rate else 1), key=f"capacity_{selected['name']}_{field}")
            values[field] = value / 100 if rate else value
        submitted = st.form_submit_button("Calcular cenário")
    st.caption("Revisão humana em 100% dos casos assistidos." + (" Fonte das premissas iniciais: data/diagnosis-assumptions.json; fórmula: solution/diagnose_support.py." if audience == "instructor" else " Os valores iniciais são hipóteses para planejar um piloto."))
    if submitted or "capacity_result" not in st.session_state or st.session_state.get("capacity_scenario") != selected["name"]:
        st.session_state["capacity_result"] = scenario(values if submitted else {**selected, "review_share": 1})
        st.session_state["capacity_scenario"] = selected["name"]
    result = st.session_state["capacity_result"]
    st.caption("Resultado das premissas confirmadas abaixo. Para aplicar campos editados, clique em Calcular cenário.")
    a,b,c = st.columns(3)
    a.metric("Casos assistidos hipotéticos", number(result["assisted_cases"], 1))
    b.metric("Capacidade líquida (h/mês)", number(result["net_capacity_hours"], 2))
    c.metric("Equivalente hipotético (R$/mês)", number(result["capacity_value_at_assumed_rate_brl"], 2))
    if result["net_capacity_hours"] < 0:
        st.error("Neste cenário, assistência, revisão, retrabalho e esforço fixo consomem mais capacidade do que recuperam.")
    break_even = result["break_even_manual_minutes_per_assisted_case"]
    st.write("Ponto de equilíbrio: " + (f"{number(break_even,2)} minutos manuais por caso assistido, mantendo as demais premissas." if break_even is not None else "indefinido sem casos assistidos; o esforço fixo permanece."))
    st.dataframe([{"Componente": label, "Horas/mês": result[key]/60} for key,label in [
        ("gross_minutes_saved", "Ganho bruto"), ("incremental_review_minutes", "Revisão adicional"),
        ("incremental_rework_minutes", "Retrabalho adicional"), ("fixed_minutes", "Esforço fixo")]], hide_index=True)
    with st.expander("Premissas usadas neste resultado"):
        if audience == "instructor":
            st.json(result["assumptions"])
        else:
            st.dataframe([{"Premissa": label, "Valor": result["assumptions"][field] * (100 if rate else 1)}
                          for field, label, rate in fields], hide_index=True)
    st.download_button("Baixar cenário e premissas", json.dumps({"scope":"Hypothetical capacity, not measured savings", **result}, ensure_ascii=False, indent=2),
                       "cenario-capacidade.json", "application/json", on_click="ignore")


def render_future():
    st.header("Evoluções planejadas")
    st.write("Ideias pensadas para a continuidade do projeto e deixadas fora do escopo desta entrega. A prioridade foi concluir diagnóstico, triagem verificável e uma experiência reproduzível; estas integrações não foram implementadas.")
    st.dataframe([
        {"Evolução": "Piloto com novos dados", "Benefício": "Medir qualidade, esforço e ganho líquido", "Pré-requisito": "Eventos, rótulos e critérios acordados com a operação"},
        {"Evolução": "IA analista", "Benefício": "Explicar métricas e levantar inconsistências com fontes", "Pré-requisito": "Cálculos determinísticos, populações/versões e avaliação das explicações"},
        {"Evolução": "Google Sheets", "Benefício": "Compartilhar fila e revisões", "Pré-requisito": "Acesso autorizado, IDs, deduplicação e reconciliação"},
        {"Evolução": "Email e Discord/canal interno", "Benefício": "Resumos e alertas acionáveis", "Pré-requisito": "Destinatários, autenticação, entrega observável e controle de repetição"},
        {"Evolução": "Bot e helpdesk", "Benefício": "Consultar, atribuir e registrar decisões no fluxo habitual", "Pré-requisito": "Papéis, auditoria, taxonomia e avaliação com dados novos"},
    ], hide_index=True)
    st.caption("Planejamento: docs/future-roadmap.md. A IA analista explicaria resultados calculados por código; concordância entre IAs não valida a verdade dos rótulos.")
