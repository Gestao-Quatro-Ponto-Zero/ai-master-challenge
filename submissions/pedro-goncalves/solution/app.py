from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.support_copilot.audit import append_record, build_record
from src.support_copilot.inference import TicketClassifier
from src.support_copilot.policy import (
    POLICY_VERSION,
    TAXONOMY_VERSION,
    OperatingMode,
    decide,
)
from src.support_copilot.privacy import mask_pii
from src.support_copilot.roi import (
    REFERENCE_SCENARIOS,
    CapacityScenario,
    calculate_capacity,
)


ROOT = Path(__file__).resolve().parent
APP_VERSION = "1.2.0"
MODEL_PATH = ROOT / "artifacts/models/ticket_classifier.joblib"
LOG_PATH = ROOT / "artifacts/logs/decisions.jsonl"
METRICS_PATH = ROOT / "artifacts/classifier_metrics.json"
THRESHOLDS_PATH = ROOT / "artifacts/tables/classifier_coverage_accuracy.csv"
DEMO_TICKETS = {
    "Escrever meu próprio ticket": "",
    "Falha de equipamento": (
        "The laptop assigned to the sales team overheats and shuts down "
        "during customer calls."
    ),
    "Acesso sensível": (
        "Please grant administrative access to the payroll folder for a new employee."
    ),
    "Solicitação pouco específica": (
        "The service is not working as expected and I need help with my account."
    ),
}


st.set_page_config(page_title="Copiloto de Suporte", page_icon="🧭", layout="wide")


@st.cache_resource
def load_classifier() -> TicketClassifier:
    return TicketClassifier(MODEL_PATH)


@st.cache_data
def load_metrics() -> tuple[dict, pd.DataFrame]:
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    thresholds = pd.read_csv(THRESHOLDS_PATH)
    return metrics, thresholds


classifier = load_classifier()
metrics, thresholds = load_metrics()
selected_threshold = float(metrics["threshold_selection"]["selected_threshold"])


def load_demo_ticket() -> None:
    st.session_state.ticket_text = DEMO_TICKETS[st.session_state.demo_ticket]


st.title("Copiloto de Suporte")
st.caption("Decisão operacional, prova técnica e controle humano no mesmo fluxo.")
st.info(
    "**Recomendação:** aprovar um piloto em shadow mode, condicionado à correção "
    "da telemetria. O protótipo não responde clientes nem altera sistemas."
)

with st.sidebar:
    st.header("Controle")
    mode = OperatingMode(
        st.selectbox("Modo operacional", [item.value for item in OperatingMode], index=0)
    )
    threshold = st.slider(
        "Threshold de confiança", 0.50, 0.95, selected_threshold, 0.05
    )
    kill_switch = st.toggle("Kill switch", value=False)
    st.info(
        "Shadow mode é o padrão. Automação simulada não envia mensagens nem altera sistemas."
    )

executive_tab, triage_tab, evidence_tab, roi_tab, limits_tab = st.tabs(
    ["Decisão", "Triagem", "Evidência", "Cenários", "Limites"]
)

with executive_tab:
    st.subheader("As três respostas para o Diretor de Operações")
    first, second, third = st.columns(3)
    with first:
        st.metric("Onde perdemos tempo?", "Não mensurável")
        st.write(
            "**Gargalo comprovado:** telemetria operacional inválida. "
            "49,3% dos pares temporais estão invertidos."
        )
    with second:
        st.metric("O que automatizar?", "Triagem assistida")
        st.write(
            "**Primeiro uso:** classificação em shadow mode, com abstenção "
            "e humano obrigatório nos casos sensíveis."
        )
    with third:
        st.metric("O que já funciona?", "18 testes")
        st.write(
            f"**Prova técnica:** macro-F1 0,868. Threshold {selected_threshold:.2f}, "
            "69,7% de cobertura e 96,6% de acurácia seletiva no teste final."
        )

    st.subheader("Plano de 30 dias")
    rollout = pd.DataFrame(
        [
            {
                "Janela": "Dias 1 a 5",
                "DRI sugerido": "Ops + Dados",
                "Entrega": "Eventos e taxonomia instrumentados",
                "Gate": "Timestamps e touch time válidos",
            },
            {
                "Janela": "Dias 6 a 15",
                "DRI sugerido": "AI Master",
                "Entrega": "Shadow mode no domínio real",
                "Gate": "Erro por classe e calibração medidos",
            },
            {
                "Janela": "Dias 16 a 25",
                "DRI sugerido": "Líder de Suporte",
                "Entrega": "Assistência para pequena equipe",
                "Gate": "Override, retrabalho e reabertura estáveis",
            },
            {
                "Janela": "Dias 26 a 30",
                "DRI sugerido": "Diretor de Operações",
                "Entrega": "Decisão de canário ou interrupção",
                "Gate": "Qualidade preservada e capacidade comprovada",
            },
        ]
    )
    st.dataframe(rollout, hide_index=True, width="stretch")
    st.warning(
        "**Decisão de gestão:** não aprovar resposta autônoma. Aprovar apenas "
        "instrumentação e shadow mode. Autonomia cresce depois da evidência."
    )

with triage_tab:
    if "demo_ticket" not in st.session_state:
        st.session_state.demo_ticket = "Falha de equipamento"
    if "ticket_text" not in st.session_state:
        st.session_state.ticket_text = DEMO_TICKETS[st.session_state.demo_ticket]
    st.selectbox(
        "Cenário de demonstração",
        list(DEMO_TICKETS),
        key="demo_ticket",
        on_change=load_demo_ticket,
    )
    ticket_text = st.text_area(
        "Texto do ticket",
        height=160,
        key="ticket_text",
        placeholder="Cole um ticket de teste sem dados pessoais reais.",
    )
    st.caption(
        "Os exemplos estão em inglês porque a prova técnica foi treinada no Dataset 2."
    )
    if st.button("Analisar ticket", type="primary", disabled=not ticket_text.strip()):
        masked_text, pii_counts = mask_pii(ticket_text)
        prediction = classifier.predict(masked_text)
        decision = decide(
            category=prediction["category"],
            confidence=prediction["confidence"],
            threshold=threshold,
            mode=mode,
            kill_switch=kill_switch,
        )
        record = build_record(
            pii_counts=pii_counts,
            prediction=prediction,
            decision=decision.to_dict(),
            mode=mode.value,
            threshold=threshold,
            kill_switch=kill_switch,
            model_sha256=classifier.model_sha256,
            policy_version=POLICY_VERSION,
            taxonomy_version=TAXONOMY_VERSION,
            app_version=APP_VERSION,
        )
        append_record(LOG_PATH, record)

        left, right = st.columns([1, 1])
        with left:
            st.metric("Categoria sugerida", prediction["category"])
            st.metric("Confiança calibrada", f"{prediction['confidence']:.1%}")
            st.metric("Decisão da política", decision.action)
        with right:
            st.write("**Justificativa**")
            st.write(decision.reason)
            st.write("**Padrões de PII detectados e mascarados**")
            st.json(pii_counts)

        if decision.action in {"HUMAN_REVIEW", "ABSTAIN"}:
            st.warning("Encaminhar para decisão humana. Nenhuma ação foi executada.")
        elif decision.action == "SHADOW_RECOMMENDATION":
            st.info("Sugestão registrada em shadow mode. O fluxo humano permanece intacto.")
        else:
            st.success("Roteamento apenas simulado. Nenhuma ação externa foi executada.")

        probability_frame = pd.DataFrame(prediction["top_predictions"])
        st.plotly_chart(
            px.bar(
                probability_frame,
                x="probability",
                y="category",
                orientation="h",
                range_x=[0, 1],
                title="Três categorias mais prováveis",
            ),
            width="stretch",
        )
        with st.expander("Registro de auditoria"):
            st.json(record)

with evidence_tab:
    model = metrics["model_final_test"]
    baseline = metrics["baseline_final_test"]
    first, second, third, fourth = st.columns(4)
    first.metric("Macro-F1", f"{model['macro_f1']:.3f}")
    second.metric("Acurácia", f"{model['accuracy']:.3f}")
    third.metric("Baseline", f"{baseline['accuracy']:.3f}")
    fourth.metric("ECE", f"{model['ece_10_bins']:.3f}")

    st.plotly_chart(
        px.line(
            thresholds,
            x="coverage",
            y="accuracy_when_covered",
            markers=True,
            hover_data=["threshold", "covered_tickets", "errors_when_covered"],
            labels={
                "coverage": "Cobertura",
                "accuracy_when_covered": "Acurácia no subconjunto coberto",
            },
            title="Validação de threshold: cobertura e acurácia",
        ),
        width="stretch",
    )
    st.caption(
        "Curva na validação de threshold. Métricas superiores no teste final. "
        "Nenhum resultado representa desempenho no suporte da G4 ou no Dataset 1."
    )

with roi_tab:
    st.subheader("Capacidade potencial")
    st.caption(
        "Calculadora parametrizada. Os valores são entradas do usuário, não resultados observados."
    )
    reference_rows = []
    for name, reference in REFERENCE_SCENARIOS:
        reference_result = calculate_capacity(reference)
        reference_rows.append(
            {
                "Cenário": name,
                "Tickets no período": reference.total_tickets,
                "Elegível": f"{reference.eligible_share:.0%}",
                "Adoção": f"{reference.adoption:.0%}",
                "Taxa segura": f"{reference.safe_success_rate:.0%}",
                "Minutos poupados": reference.minutes_saved_per_eligible_ticket,
                "Revisão (min)": reference.review_minutes_per_routed_ticket,
                "Retrabalho (min)": reference.rework_minutes_per_adopted_ticket,
                "Horas líquidas": round(reference_result.net_hours_released, 1),
            }
        )
    st.dataframe(pd.DataFrame(reference_rows), hide_index=True, width="stretch")
    st.caption(
        "Sensibilidade ilustrativa usando os 30 mil tickets do contexto do brief. "
        "Não é resultado observado no Dataset 1."
    )
    left, right = st.columns(2)
    with left:
        total_tickets = st.number_input("Tickets no período", min_value=0, value=1000, step=100)
        eligible_share = st.slider("Parcela elegível", 0.0, 1.0, 0.25, 0.05)
        adoption = st.slider("Adoção do fluxo", 0.0, 1.0, 0.50, 0.05)
        minutes_saved = st.number_input(
            "Minutos ativos poupados por ticket elegível",
            min_value=0.0,
            value=5.0,
            step=0.5,
        )
    with right:
        safe_success_rate = st.slider("Taxa segura de sucesso", 0.0, 1.0, 0.90, 0.05)
        review_minutes = st.number_input(
            "Minutos de revisão por ticket roteado",
            min_value=0.0,
            value=1.0,
            step=0.5,
        )
        rework_minutes = st.number_input(
            "Minutos de retrabalho por ticket adotado",
            min_value=0.0,
            value=0.0,
            step=0.5,
        )
        loaded_cost = st.number_input(
            "Custo carregado por hora, opcional",
            min_value=0.0,
            value=0.0,
            step=5.0,
        )
        solution_cost = st.number_input(
            "Custo total da solução no período, opcional",
            min_value=0.0,
            value=0.0,
            step=100.0,
        )

    scenario = CapacityScenario(
        total_tickets=int(total_tickets),
        eligible_share=eligible_share,
        adoption=adoption,
        minutes_saved_per_eligible_ticket=minutes_saved,
        safe_success_rate=safe_success_rate,
        review_minutes_per_routed_ticket=review_minutes,
        rework_minutes_per_adopted_ticket=rework_minutes,
        loaded_cost_per_hour=loaded_cost,
        solution_cost_for_period=solution_cost,
    )
    result = calculate_capacity(scenario)
    first, second, third = st.columns(3)
    first.metric("Tickets adotados", f"{result.adopted_tickets:,.0f}")
    second.metric("Horas brutas liberadas", f"{result.gross_hours_released:,.1f}")
    third.metric("Horas líquidas liberadas", f"{result.net_hours_released:,.1f}")
    st.caption(
        f"Revisão: {result.review_hours_added:,.1f} h no período. "
        f"Retrabalho: {result.rework_hours_added:,.1f} h no período."
    )
    if result.net_value is not None:
        st.metric("Valor líquido estimado", f"R$ {result.net_value:,.2f}")
    st.warning(
        "TTR não é touch time. A calculadora só deve receber touch time medido ou premissa explicitamente aprovada."
    )

with limits_tab:
    st.subheader("O que este protótipo não afirma")
    st.markdown(
        """
- Não foi treinado nem validado com dados da G4.
- Não responde tickets nem executa ações externas.
- A taxonomia de TI não equivale à taxonomia de suporte ao cliente.
- Confiança do modelo não substitui avaliação de risco.
- Mascaramento parcial por padrões não reconhece nomes, endereços ou toda PII contextual.
- Um threshold validado em dados públicos não autoriza implantação em produção.
"""
    )
