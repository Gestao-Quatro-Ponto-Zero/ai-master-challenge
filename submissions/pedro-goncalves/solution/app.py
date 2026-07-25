from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.support_copilot.audit import append_record, build_record
from src.support_copilot.batch import (
    CUSTOMER_SUPPORT,
    IT_SUPPORT,
    analyze_queue,
)
from src.support_copilot.customer_care import assess_customer_care
from src.support_copilot.inference import TicketClassifier
from src.support_copilot.memory import (
    MEMORY_SCHEMA_VERSION,
    find_approved_lessons,
    list_lessons,
    record_feedback,
    set_lesson_status,
)
from src.support_copilot.policy import (
    Decision,
    POLICY_VERSION,
    TAXONOMY_VERSION,
    OperatingMode,
    decide,
)
from src.support_copilot.privacy import mask_pii


ROOT = Path(__file__).resolve().parent
APP_VERSION = "1.5.0"
MODEL_PATH = ROOT / "artifacts/models/ticket_classifier.joblib"
LOG_PATH = ROOT / "artifacts/logs/decisions.jsonl"
MEMORY_PATH = ROOT / "artifacts/memory/learning.sqlite3"
METRICS_PATH = ROOT / "artifacts/classifier_metrics.json"
DEMO_REQUESTS = {
    "Reclamação do cliente": (
        "Estou há dias sem solução, já entrei em contato várias vezes e ninguém "
        "responde. Também fui cobrado duas vezes. Isso é um absurdo."
    ),
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
    "Escrever minha própria solicitação": "",
}
DEMO_CONTEXTS = {
    "Reclamação do cliente": "Atendimento ao cliente",
    "Falha de equipamento": "Suporte interno de TI",
    "Acesso sensível": "Suporte interno de TI",
    "Solicitação pouco específica": "Suporte interno de TI",
    "Escrever minha própria solicitação": "Atendimento ao cliente",
}
ACTION_LABELS = {
    "SHADOW_RECOMMENDATION": "Sugestão registrada para comparação",
    "HUMAN_REVIEW": "Encaminhar para uma pessoa",
    "ABSTAIN": "Pedir revisão humana",
    "HUMAN_APPROVAL": "Aguardar aprovação humana",
    "SIMULATED_ROUTE": "Encaminhamento apenas demonstrado",
}
CATEGORY_LABELS = {
    "Access": "Acesso",
    "Administrative rights": "Permissões administrativas",
    "HR Support": "Atendimento de pessoas",
    "Hardware": "Equipamento",
    "Internal Project": "Projeto interno",
    "Miscellaneous": "Outros assuntos",
    "Purchase": "Compra",
    "Storage": "Armazenamento",
}
REASON_LABELS = {
    "Categoria sensível definida como human-only.": (
        "Este assunto é sensível e precisa de uma pessoa responsável."
    ),
    "Kill switch ativo.": (
        "O controle de segurança foi ativado e toda solicitação deve passar por uma pessoa."
    ),
    "A mensagem contém um sinal de cuidado prioritário com o cliente.": (
        "A mensagem demonstra possível dano, insatisfação ou risco na relação com o cliente."
    ),
}


st.set_page_config(
    page_title="Assistente de Triagem",
    page_icon="🧭",
    layout="wide",
)


@st.cache_resource
def load_classifier() -> TicketClassifier:
    return TicketClassifier(MODEL_PATH)


@st.cache_data
def load_selected_threshold() -> float:
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    return float(metrics["threshold_selection"]["selected_threshold"])


classifier = load_classifier()
selected_threshold = load_selected_threshold()


def load_demo_request() -> None:
    st.session_state.request_text = DEMO_REQUESTS[st.session_state.demo_request]
    st.session_state.service_context = DEMO_CONTEXTS[
        st.session_state.demo_request
    ]


st.title("Assistente de Triagem")
st.caption(
    "Organiza solicitações, protege situações delicadas e mantém a decisão com a equipe."
)

with st.sidebar:
    st.header("Piloto")
    st.success("Modo de observação ativo: nenhuma ação externa é executada.")
    send_everything_to_human = st.toggle(
        "Encaminhar tudo para uma pessoa",
        value=False,
    )
    st.caption(
        f"Abaixo de {selected_threshold:.0%} de confiança, o assistente pede revisão."
    )

triage_tab, learning_tab, help_tab = st.tabs(
    ["Triagem", "Aprendizado", "Ajuda"]
)

with triage_tab:
    st.subheader("Analisar uma solicitação")
    if "demo_request" not in st.session_state:
        st.session_state.demo_request = "Reclamação do cliente"
    if "service_context" not in st.session_state:
        st.session_state.service_context = "Atendimento ao cliente"
    if "request_text" not in st.session_state:
        st.session_state.request_text = DEMO_REQUESTS[
            st.session_state.demo_request
        ]

    st.radio(
        "Contexto da fila",
        [CUSTOMER_SUPPORT, IT_SUPPORT],
        horizontal=True,
        key="service_context",
    )

    with st.expander("Analisar uma fila em CSV"):
        st.caption(
            "Use um CSV com uma coluna de texto. A saída não copia as mensagens."
        )
        uploaded_file = st.file_uploader("Arquivo CSV", type=["csv"])
        if uploaded_file is not None:
            try:
                queue = pd.read_csv(uploaded_file)
            except Exception as error:
                st.error(f"Não foi possível ler o arquivo: {error}")
            else:
                text_candidates = [
                    column
                    for column in ["Ticket Description", "Document", "text", "message"]
                    if column in queue.columns
                ]
                default_text = text_candidates[0] if text_candidates else queue.columns[0]
                text_column = st.selectbox(
                    "Coluna com a mensagem",
                    list(queue.columns),
                    index=list(queue.columns).index(default_text),
                )
                id_candidates = [
                    column
                    for column in ["Ticket ID", "ticket_id", "id"]
                    if column in queue.columns
                ]
                id_options = ["Usar número da linha", *id_candidates]
                id_column = st.selectbox("Identificador", id_options)
                limit = st.number_input(
                    "Máximo de linhas nesta execução",
                    min_value=1,
                    max_value=5000,
                    value=min(500, max(1, len(queue))),
                    step=100,
                )

                if st.session_state.service_context == CUSTOMER_SUPPORT:
                    st.info(
                        "Na fila de clientes, o assistente preserva o tipo já "
                        "informado e procura sinais que exigem cuidado humano. "
                        "O nome da coluna não altera essa regra."
                    )
                else:
                    st.info(
                        "Na fila de TI, o classificador sugere uma das oito "
                        "categorias e mostra a confiança."
                    )

                if st.button("Analisar fila", type="primary"):
                    selected = queue.head(int(limit)).copy()
                    queue_results = analyze_queue(
                        selected,
                        text_column=text_column,
                        id_column=(
                            None
                            if id_column == "Usar número da linha"
                            else id_column
                        ),
                        context=st.session_state.service_context,
                        classifier=classifier,
                        threshold=selected_threshold,
                        kill_switch=send_everything_to_human,
                        limit=int(limit),
                    )
                    result_rows = []
                    for position, queue_result in enumerate(queue_results):
                        prediction = queue_result["prediction"]
                        assessment = queue_result["customer_care"]
                        decision = queue_result["decision"]
                        if (
                            st.session_state.service_context
                            == CUSTOMER_SUPPORT
                        ):
                            informed_type = (
                                selected.iloc[position]["Ticket Type"]
                                if "Ticket Type" in selected.columns
                                else "Classificação humana"
                            )
                            category_label = informed_type
                            confidence_label = "Não aplicável"
                        else:
                            category_label = CATEGORY_LABELS.get(
                                prediction["category"],
                                prediction["category"],
                            )
                            confidence_label = (
                                f"{prediction['confidence']:.1%}"
                            )
                        result_rows.append(
                            {
                                "ID": queue_result["row_id"],
                                "Tipo ou assunto": category_label,
                                "Confiança": confidence_label,
                                "Cuidado prioritário": (
                                    "Sim"
                                    if assessment["requires_human"]
                                    else "Não"
                                ),
                                "Próximo passo": ACTION_LABELS.get(
                                    decision["action"],
                                    decision["action"],
                                ),
                            }
                        )

                        care_record = dict(assessment)
                        care_record.pop("reasons")
                        append_record(
                            LOG_PATH,
                            build_record(
                                pii_counts=queue_result["pii_counts"],
                                prediction=prediction,
                                decision=decision,
                                mode=OperatingMode.SHADOW.value,
                                threshold=selected_threshold,
                                kill_switch=send_everything_to_human,
                                model_sha256=classifier.model_sha256,
                                policy_version=POLICY_VERSION,
                                taxonomy_version=TAXONOMY_VERSION,
                                app_version=APP_VERSION,
                                memory_schema_version=MEMORY_SCHEMA_VERSION,
                                customer_care=care_record,
                            ),
                        )

                    results = pd.DataFrame(result_rows)
                    st.success(
                        f"{len(results)} solicitações analisadas sem executar "
                        "nenhuma ação externa."
                    )
                    st.dataframe(
                        results,
                        hide_index=True,
                        width="stretch",
                    )
                    st.download_button(
                        "Baixar resultado",
                        results.to_csv(index=False).encode("utf-8"),
                        file_name="triagem.csv",
                        mime="text/csv",
                    )
    st.selectbox(
        "Exemplo",
        list(DEMO_REQUESTS),
        key="demo_request",
        on_change=load_demo_request,
    )
    request_text = st.text_area(
        "Mensagem do cliente",
        height=180,
        key="request_text",
        placeholder="Cole uma solicitação de teste sem dados pessoais reais.",
    )

    if st.button(
        "Analisar solicitação",
        type="primary",
        disabled=not request_text.strip(),
    ):
        masked_text, pii_counts = mask_pii(request_text)
        customer_care = assess_customer_care(masked_text)
        is_customer_support = (
            st.session_state.service_context == "Atendimento ao cliente"
        )
        if is_customer_support:
            prediction = {
                "category": None,
                "confidence": None,
                "source": "customer-care-gate",
            }
            memory_matches = []
            if send_everything_to_human or customer_care.requires_human:
                decision = decide(
                    category="Customer support",
                    confidence=0.0,
                    threshold=selected_threshold,
                    mode=OperatingMode.SHADOW,
                    kill_switch=send_everything_to_human,
                    customer_care_required=customer_care.requires_human,
                )
            else:
                decision = Decision(
                    action="HUMAN_REVIEW",
                    reason=(
                        "A base de atendimento não sustenta uma categoria "
                        "automática confiável; a equipe classifica."
                    ),
                    requires_human=True,
                    simulated=False,
                )
        else:
            prediction = classifier.predict(masked_text)
            memory_matches = find_approved_lessons(
                MEMORY_PATH,
                text=masked_text,
                predicted_category=prediction["category"],
            )
            decision = decide(
                category=prediction["category"],
                confidence=prediction["confidence"],
                threshold=selected_threshold,
                mode=OperatingMode.SHADOW,
                kill_switch=send_everything_to_human,
                memory_match=bool(memory_matches),
                customer_care_required=customer_care.requires_human,
            )
        care_record = customer_care.to_dict()
        care_record["signal_codes"] = list(customer_care.signal_codes)
        care_record.pop("reasons")
        record = build_record(
            pii_counts=pii_counts,
            prediction=prediction,
            decision=decision.to_dict(),
            mode=OperatingMode.SHADOW.value,
            threshold=selected_threshold,
            kill_switch=send_everything_to_human,
            model_sha256=classifier.model_sha256,
            policy_version=POLICY_VERSION,
            taxonomy_version=TAXONOMY_VERSION,
            app_version=APP_VERSION,
            memory_lesson_ids=[
                lesson["lesson_id"] for lesson in memory_matches
            ],
            memory_schema_version=MEMORY_SCHEMA_VERSION,
            customer_care=care_record,
        )
        append_record(LOG_PATH, record)
        if is_customer_support:
            st.session_state.pop("last_analysis", None)
        else:
            st.session_state.last_analysis = {
                "decision_id": record["decision_id"],
                "predicted_category": prediction["category"],
                "confidence": prediction["confidence"],
                "memory_matches": memory_matches,
            }

        if customer_care.requires_human:
            st.error(
                "**Cuidado prioritário com o cliente:** esta solicitação precisa "
                "ser analisada por uma pessoa."
            )
            for reason in customer_care.reasons:
                st.write(f"- {reason}")

        first, second, third = st.columns(3)
        if is_customer_support:
            first.metric("Fila", "Atendimento ao cliente")
            second.metric(
                "Cuidado prioritário",
                "Sim" if customer_care.requires_human else "Não",
            )
        else:
            first.metric(
                "Assunto sugerido",
                CATEGORY_LABELS.get(
                    prediction["category"],
                    prediction["category"],
                ),
            )
            second.metric("Confiança", f"{prediction['confidence']:.1%}")
        third.metric(
            "Próximo passo",
            ACTION_LABELS.get(decision.action, decision.action),
        )

        st.write("**Por que seguir esse caminho**")
        st.write(REASON_LABELS.get(decision.reason, decision.reason))

        if decision.action in {"HUMAN_REVIEW", "ABSTAIN"}:
            st.warning("Nenhuma ação foi executada. A decisão ficou com a equipe.")
        else:
            st.info(
                "A sugestão foi registrada apenas para comparação. "
                "A equipe continua decidindo."
            )

        if any(pii_counts.values()):
            st.warning(
                "Alguns padrões de dados pessoais foram ocultados antes da análise."
            )

        if memory_matches:
            st.write("**Aprendizados anteriores relacionados**")
            for lesson in memory_matches:
                st.write(f"- {lesson['instruction']}")

        if not is_customer_support:
            with st.expander("Outras possibilidades consideradas"):
                alternatives = pd.DataFrame(
                    prediction["top_predictions"]
                ).rename(
                    columns={
                        "category": "Assunto",
                        "probability": "Probabilidade",
                    }
                )
                alternatives["Assunto"] = alternatives["Assunto"].map(
                    lambda category: CATEGORY_LABELS.get(category, category)
                )
                alternatives["Probabilidade"] = alternatives[
                    "Probabilidade"
                ].map(lambda value: f"{value:.1%}")
                st.dataframe(
                    alternatives,
                    hide_index=True,
                    width="stretch",
                )

with learning_tab:
    st.subheader("Registrar e revisar aprendizados")
    st.info(
        "A memória não retreina o modelo sozinha. Ela registra correções e usa "
        "somente lições aprovadas por outra pessoa."
    )
    st.caption(
        "O texto da solicitação não é salvo. Use apenas termos gerais, sem nomes, "
        "endereços, credenciais ou outros dados pessoais."
    )

    last_analysis = st.session_state.get("last_analysis")
    if not last_analysis:
        st.write("Analise uma solicitação antes de registrar uma correção.")
    else:
        first, second = st.columns(2)
        first.metric("Sugestão anterior", last_analysis["predicted_category"])
        second.metric("Confiança", f"{last_analysis['confidence']:.1%}")

        categories = [str(category) for category in classifier.classes]
        corrected_category = st.selectbox(
            "Qual era o assunto correto?",
            categories,
            index=categories.index(last_analysis["predicted_category"]),
            format_func=lambda category: CATEGORY_LABELS.get(category, category),
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
            "Se o assunto mudar, o sistema criará uma lição candidata. "
            "Outra pessoa deverá aprová-la."
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
                st.session_state.feedback_recorded_for = last_analysis[
                    "decision_id"
                ]
                if result["lesson_id"]:
                    st.success(
                        "Correção registrada. A nova lição aguarda outra pessoa."
                    )
                else:
                    st.success("Correção registrada sem criar uma nova lição.")

    lessons = list_lessons(MEMORY_PATH)
    st.subheader("Aprendizados registrados")
    if not lessons:
        st.caption("Nenhum aprendizado registrado ainda.")
    else:
        status_labels = {
            "candidate": "Aguardando revisão",
            "approved": "Aprovado",
            "retired": "Desativado",
        }
        lesson_frame = pd.DataFrame(
            [
                {
                    "ID": lesson["lesson_id"][:8],
                    "Status": status_labels.get(
                        lesson["status"], lesson["status"]
                    ),
                    "Sugestão anterior": CATEGORY_LABELS.get(
                        lesson["predicted_category"],
                        lesson["predicted_category"],
                    ),
                    "Correção": CATEGORY_LABELS.get(
                        lesson["recommended_category"],
                        lesson["recommended_category"],
                    ),
                    "Termos": ", ".join(lesson["trigger_terms"]),
                    "Lição": lesson["instruction"],
                    "Evidências": lesson["evidence_count"],
                    "Criado por": lesson["created_by"],
                    "Aprovado por": lesson["approved_by"] or "",
                }
                for lesson in lessons
            ]
        )
        st.dataframe(lesson_frame, hide_index=True, width="stretch")

        reviewable = [
            lesson for lesson in lessons if lesson["status"] != "retired"
        ]
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
                value="Regra geral conferida para uso no piloto.",
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

with help_tab:
    st.subheader("Como usar")
    st.markdown(
        """
1. Escolha um exemplo ou cole uma mensagem sem dados pessoais reais.
2. Clique em **Analisar solicitação**.
3. Confira o assunto sugerido, a confiança e o próximo passo.
4. Quando houver reclamação, possível dano ou assunto sensível, deixe a decisão com uma pessoa.
5. Se a sugestão estiver errada, registre a correção na aba **Aprendizado**.
6. Para testar uma fila, abra **Analisar uma fila em CSV** e escolha a coluna da mensagem.
"""
    )

    st.subheader("Quando o cuidado com o cliente é prioritário")
    st.markdown(
        """
O assistente chama uma pessoa quando encontra sinais de:

- problema repetido ou ainda sem solução;
- cobrança, reembolso ou possível prejuízo financeiro;
- cancelamento;
- escalonamento jurídico ou público;
- segurança, privacidade, abuso ou discriminação;
- insatisfação forte.
"""
    )

    st.subheader("O que este piloto não faz")
    st.markdown(
        """
- Não responde ao cliente.
- Não altera sistemas externos.
- Não define sozinho a urgência final.
- Não substitui avaliação humana.
- Não mistura a taxonomia de atendimento ao cliente com a taxonomia de TI.
- Não reconhece todo tipo possível de dado pessoal ou reclamação.
"""
    )
