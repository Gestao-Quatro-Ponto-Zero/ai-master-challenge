from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.support_copilot.audit import append_record, build_record
from src.support_copilot.inference import TicketClassifier
from src.support_copilot.memory import (
    MEMORY_SCHEMA_VERSION,
    find_approved_lessons,
    list_lessons,
    record_feedback,
    set_lesson_status,
)
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
APP_VERSION = "1.3.0"
MODEL_PATH = ROOT / "artifacts/models/ticket_classifier.joblib"
LOG_PATH = ROOT / "artifacts/logs/decisions.jsonl"
MEMORY_PATH = ROOT / "artifacts/memory/learning.sqlite3"
METRICS_PATH = ROOT / "artifacts/classifier_metrics.json"
THRESHOLDS_PATH = ROOT / "artifacts/tables/classifier_coverage_accuracy.csv"
DEMO_TICKETS = {
    "Escrever minha própria solicitação": "",
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
MODE_LABELS = {
    OperatingMode.SHADOW: "Modo observação: a IA sugere e não executa",
    OperatingMode.ASSISTED: "Modo assistido: a pessoa aprova ou corrige",
    OperatingMode.SIMULATED_AUTOMATION: "Automação simulada: apenas demonstração",
}
ACTION_LABELS = {
    "SHADOW_RECOMMENDATION": "Sugestão registrada, sem encaminhar",
    "HUMAN_REVIEW": "Enviar para decisão humana",
    "ABSTAIN": "Sem confiança suficiente, pedir revisão humana",
    "HUMAN_APPROVAL": "Aguardando aprovação humana",
    "SIMULATED_ROUTE": "Encaminhamento apenas demonstrado",
}
REASON_LABELS = {
    "Categoria sensível definida como human-only.":
        "Este assunto é sensível e precisa de uma pessoa responsável.",
    "Kill switch ativo.":
        "O controle de segurança foi ativado e toda decisão deve passar por uma pessoa.",
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
st.caption("Uma ajuda para organizar solicitações e decidir quando a IA pode participar.")
st.info(
    "**Recomendação:** testar a ajuda da IA em paralelo ao atendimento, sem enviar "
    "mensagens nem alterar sistemas. Antes, precisamos corrigir os registros de data e hora."
)

with st.sidebar:
    st.header("Controle")
    mode = OperatingMode(
        st.selectbox(
            "Como a IA participa",
            list(OperatingMode),
            index=0,
            format_func=lambda item: MODE_LABELS[item],
        )
    )
    threshold = st.slider(
        "Confiança mínima para aceitar a sugestão",
        0.50,
        0.95,
        selected_threshold,
        0.05,
        help="Abaixo desse valor, a IA não arrisca uma sugestão e pede revisão humana.",
    )
    kill_switch = st.toggle("Forçar decisão humana", value=False)
    st.info(
        "O padrão é o modo observação: a IA sugere, mas o atendimento continua nas mãos da equipe."
    )

executive_tab, triage_tab, memory_tab, evidence_tab, roi_tab, limits_tab = st.tabs(
    ["Decisão", "Triagem", "Aprendizado", "Evidência", "Cenários", "Limites"]
)

with executive_tab:
    st.subheader("As três respostas para o Diretor de Operações")
    first, second, third = st.columns(3)
    with first:
        st.metric("Onde perdemos tempo?", "Não mensurável")
        st.write(
            "**Gargalo comprovado:** os registros de data e hora não permitem "
            "saber quanto tempo o atendimento realmente levou."
        )
    with second:
        st.metric("O que automatizar?", "Triagem assistida")
        st.write(
            "**Primeiro uso:** organizar solicitações por assunto e pedir ajuda "
            "humana quando a IA não tiver segurança."
        )
    with third:
        st.metric("O que já funciona?", "Testes automatizados")
        st.write(
            "**Prova técnica:** a suíte automatizada foi aprovada. A versão experimental "
            "acertou 96,6% das sugestões que decidiu fazer."
        )

    st.subheader("Plano de 30 dias")
    rollout = pd.DataFrame(
        [
            {
                "Janela": "Dias 1 a 5",
                "DRI sugerido": "Ops + Dados",
                "Entrega": "Registrar entrada, resposta e conclusão",
                "Gate": "Datas e horas confiáveis",
            },
            {
                "Janela": "Dias 6 a 15",
                "DRI sugerido": "AI Master",
                "Entrega": "Testar sugestões junto da equipe",
                "Gate": "Medir acertos e erros por assunto",
            },
            {
                "Janela": "Dias 16 a 25",
                "DRI sugerido": "Líder de Suporte",
                "Entrega": "Ajuda para uma equipe pequena",
                "Gate": "Correções e reaberturas sob controle",
            },
            {
                "Janela": "Dias 26 a 30",
                "DRI sugerido": "Diretor de Operações",
                "Entrega": "Decidir ampliar ou interromper",
                "Gate": "Qualidade e capacidade comprovadas",
            },
        ]
    )
    st.dataframe(rollout, hide_index=True, width="stretch")
    st.warning(
        "**Decisão de gestão:** não liberar respostas automáticas. Primeiro, "
        "registrar o processo e testar sugestões com uma pessoa responsável."
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
        "Mensagem ou solicitação do cliente",
        height=160,
        key="ticket_text",
        placeholder="Cole uma solicitação de teste sem dados pessoais reais.",
    )
    st.caption(
        "Os exemplos estão em inglês porque a prova técnica foi treinada no Dataset 2."
    )
    if st.button("Analisar solicitação", type="primary", disabled=not ticket_text.strip()):
        masked_text, pii_counts = mask_pii(ticket_text)
        prediction = classifier.predict(masked_text)
        memory_matches = find_approved_lessons(
            MEMORY_PATH,
            text=masked_text,
            predicted_category=prediction["category"],
        )
        decision = decide(
            category=prediction["category"],
            confidence=prediction["confidence"],
            threshold=threshold,
            mode=mode,
            kill_switch=kill_switch,
            memory_match=bool(memory_matches),
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
            memory_lesson_ids=[
                lesson["lesson_id"] for lesson in memory_matches
            ],
            memory_schema_version=MEMORY_SCHEMA_VERSION,
        )
        append_record(LOG_PATH, record)
        st.session_state.last_analysis = {
            "decision_id": record["decision_id"],
            "predicted_category": prediction["category"],
            "confidence": prediction["confidence"],
            "memory_matches": memory_matches,
        }

        left, right = st.columns([1, 1])
        with left:
            st.metric("Categoria sugerida", prediction["category"])
            st.metric("Confiança da sugestão", f"{prediction['confidence']:.1%}")
            st.metric("Próximo passo", ACTION_LABELS.get(decision.action, decision.action))
        with right:
            st.write("**Por que o sistema sugeriu isso**")
            st.write(REASON_LABELS.get(decision.reason, decision.reason))
            st.write("**Dados pessoais encontrados e ocultados**")
            st.json(pii_counts)
            if memory_matches:
                st.write("**Lições aprovadas encontradas**")
                for lesson in memory_matches:
                    st.write(
                        f"- {lesson['instruction']} "
                        f"(recomendação: {lesson['recommended_category']})"
                    )

        if decision.action in {"HUMAN_REVIEW", "ABSTAIN"}:
            st.warning("Encaminhar para decisão humana. Nenhuma ação foi executada.")
        elif decision.action == "SHADOW_RECOMMENDATION":
            st.info("Sugestão registrada apenas para comparação. A equipe continua decidindo.")
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
        with st.expander("Registro de controle"):
            st.json(record)

with memory_tab:
    st.subheader("Memória de correções")
    st.info(
        "Esta memória não retreina o modelo sozinha. Ela registra correções, "
        "consolida lições e usa somente as que uma pessoa aprovou."
    )
    st.caption(
        "O texto bruto da solicitação não é salvo. Escreva apenas regras gerais, "
        "sem nomes, endereços, credenciais ou outros dados pessoais."
    )

    last_analysis = st.session_state.get("last_analysis")
    if not last_analysis:
        st.write("Analise uma solicitação na aba Triagem para registrar uma correção.")
    else:
        first, second = st.columns(2)
        first.metric("Sugestão anterior", last_analysis["predicted_category"])
        second.metric("Confiança", f"{last_analysis['confidence']:.1%}")

        categories = [str(category) for category in classifier.classes]
        corrected_category = st.selectbox(
            "Qual era a categoria correta?",
            categories,
            index=categories.index(last_analysis["predicted_category"]),
        )
        operator_id = st.text_input(
            "Identificador de quem registrou a correção",
            value="operador-demo",
        )
        trigger_terms = st.text_input(
            "Quais termos gerais identificam casos parecidos?",
            placeholder="Ex.: administrative, access",
        )
        st.caption(
            "Se a categoria mudar, o sistema criará uma lição candidata a partir "
            "das categorias e dos termos. Outra pessoa deverá aprová-la."
        )

        feedback_already_recorded = (
            st.session_state.get("feedback_recorded_for")
            == last_analysis["decision_id"]
        )
        if feedback_already_recorded:
            st.success("Correção registrada para esta análise.")
        elif st.button("Registrar correção", type="primary"):
            try:
                result = record_feedback(
                    MEMORY_PATH,
                    decision_id=last_analysis["decision_id"],
                    predicted_category=last_analysis["predicted_category"],
                    corrected_category=corrected_category,
                    confidence=last_analysis["confidence"],
                    model_version=classifier.model_sha256,
                    policy_version=POLICY_VERSION,
                    created_by=operator_id,
                    trigger_terms=trigger_terms.split(","),
                )
            except (ValueError, PermissionError) as error:
                st.error(str(error))
            else:
                st.session_state.feedback_recorded_for = last_analysis["decision_id"]
                if result["lesson_id"]:
                    st.success(
                        "Correção registrada. A nova lição aguarda revisão de outra pessoa."
                    )
                else:
                    st.success("Correção registrada sem criar uma nova lição.")

    lessons = list_lessons(MEMORY_PATH)
    st.subheader("Tabela universal de aprendizados")
    if not lessons:
        st.caption("Nenhum aprendizado registrado ainda.")
    else:
        lesson_frame = pd.DataFrame(
            [
                {
                    "ID": lesson["lesson_id"][:8],
                    "Status": lesson["status"],
                    "A IA sugeriu": lesson["predicted_category"],
                    "Correção": lesson["recommended_category"],
                    "Gatilhos": ", ".join(lesson["trigger_terms"]),
                    "Lição": lesson["instruction"],
                    "Evidências": lesson["evidence_count"],
                    "Criado por": lesson["created_by"],
                    "Aprovado por": lesson["approved_by"] or "",
                }
                for lesson in lessons
            ]
        )
        st.dataframe(lesson_frame, hide_index=True, width="stretch")

        reviewable = [lesson for lesson in lessons if lesson["status"] != "retired"]
        if reviewable:
            selected_lesson_id = st.selectbox(
                "Aprendizado para revisar",
                [lesson["lesson_id"] for lesson in reviewable],
                format_func=lambda lesson_id: next(
                    lesson["instruction"]
                    for lesson in reviewable
                    if lesson["lesson_id"] == lesson_id
                ),
            )
            reviewer_id = st.text_input(
                "Identificador do revisor",
                value="revisor-demo",
            )
            review_reason = st.text_input(
                "Justificativa da revisão",
                value="Regra geral conferida para uso no modo de observação.",
            )
            approve_column, retire_column = st.columns(2)
            if approve_column.button("Aprovar aprendizado"):
                try:
                    set_lesson_status(
                        MEMORY_PATH,
                        lesson_id=selected_lesson_id,
                        status="approved",
                        actor_id=reviewer_id,
                        reason=review_reason,
                    )
                except (ValueError, PermissionError, KeyError) as error:
                    st.error(str(error))
                else:
                    st.success("Aprendizado aprovado para consultas futuras.")
            if retire_column.button("Desativar aprendizado"):
                try:
                    set_lesson_status(
                        MEMORY_PATH,
                        lesson_id=selected_lesson_id,
                        status="retired",
                        actor_id=reviewer_id,
                        reason=review_reason,
                    )
                except (ValueError, PermissionError, KeyError) as error:
                    st.error(str(error))
                else:
                    st.success("Aprendizado desativado. O histórico foi preservado.")
        else:
            st.caption("Todos os aprendizados registrados estão desativados.")

with evidence_tab:
    st.caption(
        "Aqui mostramos o quanto o experimento acertou nos dados públicos. "
        "Isso ainda não prova o desempenho no atendimento real da G4."
    )
    model = metrics["model_final_test"]
    baseline = metrics["baseline_final_test"]
    first, second, third, fourth = st.columns(4)
    first.metric("Acerto equilibrado", f"{model['macro_f1']:.3f}")
    second.metric("Acerto geral", f"{model['accuracy']:.3f}")
    third.metric("Regra simples", f"{baseline['accuracy']:.3f}")
    fourth.metric("Confiabilidade da confiança", f"{model['ece_10_bins']:.3f}")

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
            title="Quanto mais a IA decide, quantos acertos ela mantém",
        ),
        width="stretch",
    )
    st.caption(
        "Esta comparação ajuda a escolher quando a IA deve parar e pedir ajuda. "
        "Os números vêm de dados públicos e não representam o suporte da G4."
    )

with roi_tab:
    st.subheader("Capacidade potencial")
    st.caption(
        "Simulação de capacidade. Altere as premissas para estimar horas possíveis; "
        "isso não é economia comprovada."
    )
    reference_rows = []
    for name, reference in REFERENCE_SCENARIOS:
        reference_result = calculate_capacity(reference)
        reference_rows.append(
            {
                "Cenário": name,
                "Solicitações no período": reference.total_tickets,
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
        "Exemplo ilustrativo usando os 30 mil pedidos mencionados no enunciado. "
        "Não é resultado observado nos arquivos públicos."
    )
    left, right = st.columns(2)
    with left:
        total_tickets = st.number_input(
            "Solicitações no período", min_value=0, value=1000, step=100
        )
        eligible_share = st.slider("Parcela elegível", 0.0, 1.0, 0.25, 0.05)
        adoption = st.slider("Adoção do fluxo", 0.0, 1.0, 0.50, 0.05)
        minutes_saved = st.number_input(
            "Minutos ativos poupados por solicitação elegível",
            min_value=0.0,
            value=5.0,
            step=0.5,
        )
    with right:
        safe_success_rate = st.slider("Taxa segura de sucesso", 0.0, 1.0, 0.90, 0.05)
        review_minutes = st.number_input(
            "Minutos de revisão por solicitação encaminhada",
            min_value=0.0,
            value=1.0,
            step=0.5,
        )
        rework_minutes = st.number_input(
            "Minutos de retrabalho por solicitação adotada",
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
    first.metric("Solicitações adotadas", f"{result.adopted_tickets:,.0f}")
    second.metric("Horas brutas liberadas", f"{result.gross_hours_released:,.1f}")
    third.metric("Horas líquidas liberadas", f"{result.net_hours_released:,.1f}")
    st.caption(
        f"Revisão: {result.review_hours_added:,.1f} h no período. "
        f"Retrabalho: {result.rework_hours_added:,.1f} h no período."
    )
    if result.net_value is not None:
        st.metric("Valor líquido estimado", f"R$ {result.net_value:,.2f}")
    st.warning(
        "A simulação precisa usar minutos reais de trabalho, não apenas o tempo total "
        "que uma solicitação ficou aberta."
    )

with limits_tab:
    st.subheader("O que este protótipo não afirma")
    st.markdown(
        """
- Não foi treinado nem testado com dados da G4.
- Não responde solicitações nem executa ações externas.
- Os assuntos dos dados públicos não são necessariamente os assuntos do suporte da G4.
- Uma porcentagem de confiança não substitui avaliação de risco.
- O sistema oculta apenas alguns padrões de dados pessoais, não todos.
- Um bom resultado em dados públicos não autoriza implantação imediata.
"""
    )
