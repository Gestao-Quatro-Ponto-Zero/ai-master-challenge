from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import plotly.express as px
import streamlit as st

from src.support_copilot.audit import append_record, build_record
from src.support_copilot.batch import CUSTOMER_SUPPORT, IT_SUPPORT, analyze_queue
from src.support_copilot.customer_care import assess_customer_care
from src.support_copilot.demo_matrix import CASE_MATRIX, evaluate_matrix, matrix_frame
from src.support_copilot.inference import TicketClassifier
from src.support_copilot.memory import (
    MEMORY_SCHEMA_VERSION,
    find_approved_lessons,
    list_lessons,
    list_operational_lessons,
    record_feedback,
    seed_case_memory,
    set_lesson_status,
)
from src.support_copilot.operational_metrics import (
    EfficiencyScenario,
    calculate_efficiency,
)
from src.support_copilot.policy import (
    POLICY_VERSION,
    TAXONOMY_VERSION,
    Decision,
    OperatingMode,
    decide,
)
from src.support_copilot.privacy import mask_pii
from src.support_copilot.universal_analysis import (
    VALID_ROLES,
    apply_schema,
    category_distribution,
    compare_summaries,
    profile_dataframe,
    read_spreadsheet,
    summarize_table,
)


ROOT = Path(__file__).resolve().parent
SUBMISSION_ROOT = ROOT if (ROOT / "docs").exists() else ROOT.parent
APP_VERSION = "2.8.0"
MODEL_PATH = ROOT / "artifacts/models/ticket_classifier.joblib"
LOG_PATH = ROOT / "artifacts/logs/decisions.jsonl"
MEMORY_PATH = ROOT / "artifacts/memory/learning.sqlite3"
METRICS_PATH = ROOT / "artifacts/classifier_metrics.json"
AUDIT_PATH = ROOT / "artifacts/data_audit.json"
MATRIX_PATH = ROOT / "artifacts/demo/case_test_matrix.csv"
CASE_SUPPORT_SAMPLE_PATH = ROOT / "artifacts/demo/customer_support_case_sample.csv"
CASE_IT_SAMPLE_PATH = ROOT / "artifacts/demo/it_service_case_sample.csv"
SUPPORT_TYPES_PATH = ROOT / "artifacts/tables/support_ticket_type_distribution.csv"
IT_TYPES_PATH = ROOT / "artifacts/tables/it_topic_distribution.csv"

PAGES = [
    "Visão geral",
    "Demonstração",
    "Analisar planilhas",
    "Aprendizado",
    "Entregáveis",
    "Ajuda",
]
ACTION_LABELS = {
    "SHADOW_RECOMMENDATION": "Sugestão em observação",
    "HUMAN_REVIEW": "Decisão humana",
    "ABSTAIN": "Pedir esclarecimento",
    "HUMAN_APPROVAL": "Aguardar aprovação",
    "SIMULATED_ROUTE": "Encaminhamento simulado",
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
        "O assunto é sensível e precisa de uma pessoa responsável."
    ),
    "Kill switch ativo.": (
        "O controle máximo está ativo. Toda solicitação fica com uma pessoa."
    ),
    "A mensagem contém um sinal de cuidado prioritário com o cliente.": (
        "A mensagem indica possível dano, insatisfação ou risco para o cliente."
    ),
    "A memória aprovada encontrou um erro anterior parecido.": (
        "Um erro semelhante já foi corrigido e aprovado. A equipe deve revisar."
    ),
    "Shadow mode registra a recomendação sem executar ações.": (
        "A sugestão será comparada com a decisão da equipe, sem executar ações."
    ),
}
DEMO_CASES = {
    case["scenario"]: case
    for case in CASE_MATRIX
    if case["case_id"] in {
        "CLI-01",
        "CLI-02",
        "CLI-04",
        "ITI-01",
        "ITI-02",
        "ITI-04",
        "ITI-08",
    }
}
DELIVERABLES = (
    {
        "title": "Parecer 80/20 da operação",
        "question": "O que deve ser feito primeiro e por quê?",
        "summary": (
            "Consolida os quatro indicadores principais, prova cada cálculo "
            "e prioriza as duas ações de maior efeito operacional."
        ),
        "path": SUBMISSION_ROOT / "docs/gate-3/parecer-80-20.md",
    },
    {
        "title": "Por que escolhi este case",
        "question": "Que experiência pessoal sustenta esta escolha?",
        "summary": (
            "Conecto minha vivência no suporte da Cheers com processos, "
            "Power BI, decisão gerencial e critério de automação."
        ),
        "path": SUBMISSION_ROOT / "docs/gate-3/por-que-escolhi.md",
    },
    {
        "title": "Auditoria dos dados",
        "question": "Posso confiar nos arquivos fornecidos?",
        "summary": (
            "Confere volume, campos ausentes, pares temporais incoerentes, repetições, "
            "qualidade dos textos e limites de uso."
        ),
        "path": SUBMISSION_ROOT / "docs/gate-1/data-audit.md",
    },
    {
        "title": "Diagnóstico operacional",
        "question": "Onde a operação realmente perde tempo?",
        "summary": (
            "Transforma os dados válidos em um problema priorizado e separa "
            "evidência de hipótese."
        ),
        "path": SUBMISSION_ROOT / "docs/gate-1/diagnostico-operacional.md",
    },
    {
        "title": "Foco no cliente",
        "question": "Como a voz do cliente muda a decisão?",
        "summary": (
            "Mostra por que reincidência, dano, cancelamento e insatisfação "
            "precisam superar classificações automáticas."
        ),
        "path": SUBMISSION_ROOT / "docs/gate-3/foco-no-cliente.md",
    },
    {
        "title": "Onde colocar IA",
        "question": "Onde usamos IA, onde não usamos e por quê?",
        "summary": (
            "Explica cada decisão do fluxo: código determinístico, IA "
            "preditiva, memória aprovada ou decisão humana."
        ),
        "path": SUBMISSION_ROOT / "docs/gate-1/automacao-sob-controle.md",
    },
    {
        "title": "Análise universal",
        "question": "Como aplicar o processo em outra empresa?",
        "summary": (
            "Explica o fluxo de duas planilhas, validação de colunas, papéis "
            "humanos, painel gerencial e limites de generalização."
        ),
        "path": SUBMISSION_ROOT / "docs/gate-2/analise-universal.md",
    },
    {
        "title": "Claims e limitações",
        "question": "O que foi provado e o que ainda é hipótese?",
        "summary": (
            "Rastreia cada afirmação, sua fonte, população, método e limite."
        ),
        "path": SUBMISSION_ROOT / "docs/gate-2/claim-ledger.md",
    },
    {
        "title": "Memória sob controle",
        "question": "Por que não usamos retropropagação ou RAG agora?",
        "summary": (
            "Compara as alternativas e mostra como correções aprovadas viram "
            "memória auditável sem alterar o modelo silenciosamente."
        ),
        "path": SUBMISSION_ROOT / "docs/gate-3/memoria-de-aprendizado.md",
    },
    {
        "title": "Processo de construção",
        "question": "Como a IA foi usada e corrigida?",
        "summary": (
            "Registra decisões, erros, revisões adversariais e correções humanas."
        ),
        "path": SUBMISSION_ROOT / "process-log/README.md",
    },
    {
        "title": "Protocolo de aprovação",
        "question": "Como validar a entrega antes de enviá-la?",
        "summary": (
            "Guia duas rodadas humanas independentes e define o que bloqueia "
            "ou libera a submissão."
        ),
        "path": SUBMISSION_ROOT / "docs/gate-3/protocolo-aprovacao.md",
    },
)


st.set_page_config(
    page_title="Operação Sob Controle",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource
def load_classifier() -> TicketClassifier:
    return TicketClassifier(MODEL_PATH)


@st.cache_data
def load_selected_threshold() -> float:
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    return float(metrics["threshold_selection"]["selected_threshold"])


@st.cache_data
def load_case_evidence() -> dict:
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    return {
        "customer_rows": audit["dataset_1"]["rows"],
        "it_rows": audit["dataset_2"]["rows"],
        "repeat_unresolved": audit["dataset_1"]["repeated_unresolved_rows"],
        "macro_f1": metrics["model_final_test"]["macro_f1"],
    }


classifier = load_classifier()
selected_threshold = load_selected_threshold()
evidence = load_case_evidence()
seed_case_memory(
    MEMORY_PATH,
    model_version=classifier.model_sha256,
    policy_version=POLICY_VERSION,
)


def navigate(page: str) -> None:
    st.session_state.os_page = page
    st.query_params.clear()


def render_top_navigation(page: str) -> None:
    visible_labels = {
        "Demonstração": "Triagem diária",
        "Analisar planilhas": "Análise da operação",
    }
    links = []
    for destination in PAGES:
        active = " is-active" if destination == page else ""
        current = ' aria-current="page"' if destination == page else ""
        links.append(
            f'<a class="os-nav-link{active}" '
            f'href="?page={quote(destination, safe="")}"{current}>'
            f"{visible_labels.get(destination, destination)}</a>"
        )
    st.markdown(
        f"""
        <nav class="os-nav" aria-label="Navegação principal">
          <a class="os-brand" href="?page={quote("Visão geral", safe="")}">
            <strong>G4</strong>
            <span>OPERAÇÃO SOB CONTROLE</span>
          </a>
          <div class="os-nav-links">
            {''.join(links)}
          </div>
          <span class="os-nav-status">HUMANO NO CONTROLE</span>
        </nav>
        """,
        unsafe_allow_html=True,
    )


def go_to_case_analysis() -> None:
    activate_case_data()
    navigate("Analisar planilhas")


def load_demo_case() -> None:
    case = DEMO_CASES[st.session_state.demo_case]
    st.session_state.request_text = case["message"]
    st.session_state.service_context = case["context"]


def label_reason(reason: str) -> str:
    if reason.startswith("Confiança"):
        return reason.replace("threshold", "limite mínimo")
    return REASON_LABELS.get(reason, reason)


def log_decision(
    *,
    pii_counts: dict,
    prediction: dict,
    decision: dict,
    kill_switch: bool,
    memory_lesson_ids: list[str] | None = None,
    customer_care: dict | None = None,
) -> dict:
    record = build_record(
        pii_counts=pii_counts,
        prediction=prediction,
        decision=decision,
        mode=OperatingMode.SHADOW.value,
        threshold=selected_threshold,
        kill_switch=kill_switch,
        model_sha256=classifier.model_sha256,
        policy_version=POLICY_VERSION,
        taxonomy_version=TAXONOMY_VERSION,
        app_version=APP_VERSION,
        memory_lesson_ids=memory_lesson_ids or [],
        memory_schema_version=MEMORY_SCHEMA_VERSION,
        customer_care=customer_care,
    )
    append_record(LOG_PATH, record)
    return record


def analyze_single(request_text: str, context: str, kill_switch: bool) -> None:
    masked_text, pii_counts = mask_pii(request_text)
    customer_care = assess_customer_care(masked_text)
    is_customer = context == CUSTOMER_SUPPORT

    if is_customer:
        prediction = {
            "category": None,
            "confidence": None,
            "source": "customer-care-gate",
        }
        memory_matches = []
        if kill_switch or customer_care.requires_human:
            decision = decide(
                category="Customer support",
                confidence=0.0,
                threshold=selected_threshold,
                mode=OperatingMode.SHADOW,
                kill_switch=kill_switch,
                customer_care_required=customer_care.requires_human,
            )
        else:
            decision = Decision(
                action="HUMAN_REVIEW",
                reason=(
                    "A base de clientes não sustenta classificação automática "
                    "confiável. A equipe mantém a decisão."
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
            kill_switch=kill_switch,
            memory_match=bool(memory_matches),
            customer_care_required=customer_care.requires_human,
        )

    care_record = customer_care.to_dict()
    care_record["signal_codes"] = list(customer_care.signal_codes)
    care_record.pop("reasons")
    record = log_decision(
        pii_counts=pii_counts,
        prediction=prediction,
        decision=decision.to_dict(),
        kill_switch=kill_switch,
        memory_lesson_ids=[
            lesson["lesson_id"] for lesson in memory_matches
        ],
        customer_care=care_record,
    )

    if is_customer:
        st.session_state.pop("last_analysis", None)
    else:
        st.session_state.last_analysis = {
            "decision_id": record["decision_id"],
            "predicted_category": prediction["category"],
            "confidence": prediction["confidence"],
            "memory_matches": memory_matches,
        }

    if customer_care.requires_human:
        st.error("Cuidado prioritário: esta solicitação precisa de uma pessoa.")
        for reason in customer_care.reasons:
            st.write(f"- {reason}")

    first, second, third = st.columns(3)
    if is_customer:
        first.metric("Fila", "Cliente")
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
    third.metric("Próximo passo", ACTION_LABELS.get(decision.action, decision.action))

    st.markdown("**Por que seguir esse caminho**")
    st.write(label_reason(decision.reason))
    if decision.action in {"HUMAN_REVIEW", "ABSTAIN"}:
        st.warning("Nenhuma ação foi executada. A decisão ficou com a equipe.")
    else:
        st.info("A sugestão foi registrada para comparação, sem execução externa.")

    if any(pii_counts.values()):
        st.warning("Alguns padrões de dados pessoais foram ocultados.")
    if memory_matches:
        st.markdown("**Aprendizado anterior acionado**")
        for lesson in memory_matches:
            st.write(f"- {lesson['instruction']}")

    if not is_customer:
        with st.expander("Outras possibilidades consideradas"):
            alternatives = pd.DataFrame(prediction["top_predictions"]).rename(
                columns={
                    "category": "Assunto",
                    "probability": "Probabilidade",
                }
            )
            alternatives["Assunto"] = alternatives["Assunto"].map(
                lambda category: CATEGORY_LABELS.get(category, category)
            )
            alternatives["Probabilidade"] = alternatives["Probabilidade"].map(
                lambda value: f"{value:.1%}"
            )
            st.dataframe(alternatives, hide_index=True, width="stretch")


def render_matrix(kill_switch: bool, *, key_prefix: str) -> None:
    st.markdown(
        """
        <div class="section-kicker">MATRIZ DE TESTES</div>
        <h2>Casos do case para provar comportamento e limites</h2>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "Os cenários foram derivados dos dois datasets e dos riscos encontrados. "
        "Não contêm dados pessoais reais."
    )
    preview = matrix_frame()
    st.dataframe(
        preview[["ID", "Fila", "Cenário", "Comportamento esperado", "Origem"]],
        hide_index=True,
        width="stretch",
    )
    left, right = st.columns([1, 1])
    left.download_button(
        "Baixar matriz em CSV",
        preview.to_csv(index=False).encode("utf-8"),
        file_name="matriz-testes-case.csv",
        mime="text/csv",
        key=f"{key_prefix}_download_matrix",
    )
    run_matrix = right.button(
        "Executar testes do case",
        type="primary",
        key=f"{key_prefix}_run_matrix",
    )
    if run_matrix:
        st.session_state.matrix_results = evaluate_matrix(
            classifier=classifier,
            threshold=selected_threshold,
            memory_path=MEMORY_PATH,
            kill_switch=kill_switch,
        )

    results = st.session_state.get("matrix_results")
    if results is not None:
        passed = int(results["Resultado"].eq("PASS").sum())
        if passed == len(results):
            st.success(f"{passed}/{len(results)} casos aprovados.")
        else:
            st.error(f"{passed}/{len(results)} casos aprovados. Revise os FAIL.")
        st.dataframe(results, hide_index=True, width="stretch")
        st.download_button(
            "Baixar evidência da execução",
            results.to_csv(index=False).encode("utf-8"),
            file_name="resultado-matriz-testes.csv",
            mime="text/csv",
            key=f"{key_prefix}_download_results",
        )


def management_bar(
    frame: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
):
    figure = px.bar(
        frame,
        x=x,
        y=y,
        title=title,
        color_discrete_sequence=["#101B2F"],
    )
    figure.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font={"family": "Inter, system-ui, sans-serif", "color": "#111827"},
        title={"font": {"size": 17}},
        margin={"l": 10, "r": 10, "t": 52, "b": 10},
        showlegend=False,
    )
    return figure


@st.dialog("Painel gerencial do case", width="large")
def show_case_dashboard() -> None:
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    d1 = audit["dataset_1"]
    selective = metrics["threshold_selection"]["final_test"]
    final_rows = metrics["data"]["final_test_rows"]
    correct_covered = (
        selective["covered_tickets"] - selective["errors_when_covered"]
    )

    st.markdown(
        """
        <div class="section-kicker">PARECER 80/20</div>
        <h2>Quatro sinais para decidir o próximo ciclo</h2>
        <p class="lead">
          Primeiro, fatos medidos. Depois, uma simulação editável de eficiência.
          Nenhuma economia é apresentada como resultado observado.
        </p>
        """,
        unsafe_allow_html=True,
    )
    first, second, third, fourth = st.columns(4)
    first.metric(
        "Cliente reincidente",
        d1["repeated_unresolved_rows"],
        help="Contagem medida no Dataset 1.",
    )
    second.metric(
        "Horários inválidos",
        f"{d1['negative_response_to_resolution_rate']:.1%}",
        help="Cálculo sobre pares de horários preenchidos no Dataset 1.",
    )
    third.metric(
        "Cobertura segura",
        f"{selective['coverage']:.1%}",
        help="Cálculo no teste final independente do Dataset 2.",
    )
    fourth.metric(
        "Acerto nos cobertos",
        f"{selective['accuracy_when_covered']:.1%}",
        help="Cálculo apenas entre previsões cobertas no Dataset 2.",
    )

    with st.expander("Provar cada número: fonte, fórmula e limite"):
        st.markdown(
            f"""
1. **Cliente reincidente. Medido:** busca literal nas `{d1["rows"]}` descrições =
   `{d1["repeated_unresolved_rows"]}` casos, ou
   `{d1["repeated_unresolved_rows"] / d1["rows"]:.2%}` da base. Desses,
   `{d1["repeated_unresolved_by_status"]["Closed"]}` estão encerrados.
2. **Horários inválidos. Calculado:** `{d1["negative_response_to_resolution_rows"]} ÷
   {d1["paired_timestamp_rows"]} =
   {d1["negative_response_to_resolution_rate"]:.1%}` dos pares têm resolução
   anterior à primeira resposta.
3. **Cobertura segura. Calculado:** `{selective["covered_tickets"]} ÷ {final_rows} =
   {selective["coverage"]:.1%}` das mensagens do teste final superam o limite
   de confiança de `{selective["threshold"]:.0%}`.
4. **Acerto nos cobertos. Calculado:** `{correct_covered} ÷
   {selective["covered_tickets"]} =
   {selective["accuracy_when_covered"]:.1%}` no teste final independente.
"""
        )
        st.caption(
            "Os indicadores 3 e 4 pertencem à fila interna de TI. Não foram "
            "transferidos para a fila de clientes."
        )

    st.markdown("### Pareto: as duas primeiras ações")
    pareto_left, pareto_right = st.columns(2)
    with pareto_left:
        st.markdown(
            f"""
**1. Revisar reincidências**

Começar pelos `{d1["repeated_unresolved_by_status"]["Closed"]}` casos encerrados
que ainda relatam contatos repetidos sem solução.
"""
        )
    with pareto_right:
        st.markdown(
            f"""
**2. Corrigir a base temporal**

Resolver os `{d1["negative_response_to_resolution_rows"]}` pares incoerentes
antes de publicar FRT, TTR, produtividade ou ROI observado.
"""
        )

    st.markdown("### Simular produtividade do piloto")
    st.caption(
        "Hipótese editável, não resultado observado. O volume vem da base; "
        "as demais premissas precisam ser substituídas por medições do piloto."
    )
    volume_col, eligible_col, adoption_col = st.columns(3)
    volume = volume_col.number_input(
        "Solicitações no período",
        min_value=1,
        value=int(d1["rows"]),
        step=100,
    )
    eligible_share = eligible_col.slider(
        "Hipótese: elegíveis para assistência",
        min_value=0,
        max_value=100,
        value=25,
        format="%d%%",
    )
    adoption = adoption_col.slider(
        "Hipótese: adoção pela equipe",
        min_value=0,
        max_value=100,
        value=50,
        format="%d%%",
    )
    manual_col, assisted_col, success_col = st.columns(3)
    manual_minutes = manual_col.number_input(
        "Hipótese: minutos no processo manual",
        min_value=0.5,
        value=8.0,
        step=0.5,
    )
    assisted_minutes = assisted_col.number_input(
        "Hipótese: minutos com assistência",
        min_value=0.0,
        value=3.0,
        step=0.5,
    )
    safe_success = success_col.slider(
        "Hipótese: sucesso seguro no piloto",
        min_value=0,
        max_value=100,
        value=90,
        format="%d%%",
    )
    scenario = EfficiencyScenario(
        volume=int(volume),
        eligible_share=eligible_share / 100,
        adoption=adoption / 100,
        manual_minutes=float(manual_minutes),
        assisted_minutes=float(assisted_minutes),
        safe_success_rate=safe_success / 100,
    )
    efficiency = calculate_efficiency(scenario)
    outcome, reduction, scope = st.columns(3)
    outcome.metric(
        "Cenário: capacidade líquida",
        f"{efficiency.net_hours_released:,.1f} h".replace(",", "."),
    )
    reduction.metric(
        "Cenário: redução no escopo",
        f"{efficiency.time_reduction_rate:.1%}",
    )
    scope.metric(
        "Cenário: casos adotados",
        f"{efficiency.adopted_cases:,.0f}".replace(",", "."),
    )
    with st.expander("Ver fórmula da simulação"):
        st.code(
            (
                f"Casos adotados = {int(volume)} × {eligible_share}% × "
                f"{adoption}% = {efficiency.adopted_cases:,.1f}\n"
                f"Horas manuais = {efficiency.adopted_cases:,.1f} × "
                f"{manual_minutes:.1f} min ÷ 60 = {efficiency.manual_hours:,.1f} h\n"
                f"Horas assistidas = {efficiency.adopted_cases:,.1f} × "
                f"{assisted_minutes:.1f} min ÷ 60 = "
                f"{efficiency.assisted_hours:,.1f} h\n"
                f"Retrabalho = {efficiency.adopted_cases:,.1f} × "
                f"{100-safe_success}% × {manual_minutes:.1f} min ÷ 60 = "
                f"{efficiency.rework_hours:,.1f} h\n"
                f"Capacidade líquida = {efficiency.manual_hours:,.1f} - "
                f"{efficiency.assisted_hours:,.1f} - "
                f"{efficiency.rework_hours:,.1f} = "
                f"{efficiency.net_hours_released:,.1f} h"
            ).replace(",", "."),
            language="text",
        )

    st.markdown("### Recomendação operacional")
    st.markdown(
        """
1. Revisar primeiro os **460 relatos de reincidência**, começando pelos 152 encerrados.
2. Corrigir os campos de tempo antes de cobrar FRT, TTR ou ROI observado.
3. Rodar o classificador de TI em observação, medindo tempo manual e assistido.
4. Só promover automação após validar qualidade e ganho em um piloto real.
"""
    )

    with st.expander("Ver distribuições dos dois datasets"):
        support_types = pd.read_csv(SUPPORT_TYPES_PATH)
        it_types = pd.read_csv(IT_TYPES_PATH).head(8)
        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                management_bar(
                    support_types,
                    x="ticket_type",
                    y="tickets",
                    title="Atendimento ao cliente por tipo",
                ),
                width="stretch",
                config={"displayModeBar": False},
            )
        with right:
            st.plotly_chart(
                management_bar(
                    it_types,
                    x="topic_group",
                    y="tickets",
                    title="Suporte interno de TI por assunto",
                ),
                width="stretch",
                config={"displayModeBar": False},
            )


def render_schema_editor(
    frame: pd.DataFrame,
    *,
    title: str,
    key: str,
    default_context: str = "Análise gerencial",
) -> tuple[pd.DataFrame, str]:
    st.markdown(f"#### {title}")
    st.caption(
        f"{len(frame):,} linhas e {len(frame.columns)} colunas. "
        "Nada é removido da fonte original."
    )
    profile = profile_dataframe(frame)
    editor = st.data_editor(
        profile,
        hide_index=True,
        width="stretch",
        key=f"{key}_schema",
        disabled=[
            "Coluna",
            "Papel sugerido",
            "Tipo",
            "Preenchimento",
            "Valores distintos",
        ],
        column_config={
            "Usar": st.column_config.CheckboxColumn(
                "Usar",
                help="Desmarque apenas se a coluna não participa desta análise.",
            ),
            "Ordem": st.column_config.NumberColumn(
                "Ordem",
                min_value=1,
                step=1,
            ),
            "Papel validado": st.column_config.SelectboxColumn(
                "Papel validado",
                options=list(VALID_ROLES),
                required=True,
            ),
            "Preenchimento": st.column_config.ProgressColumn(
                "Preenchimento",
                min_value=0,
                max_value=1,
                format="percent",
            ),
        },
    )
    context_options = ["Análise gerencial", CUSTOMER_SUPPORT, IT_SUPPORT]
    context = st.selectbox(
        "Como esta planilha será usada?",
        context_options,
        index=context_options.index(default_context),
        key=f"{key}_context",
    )
    return editor, context


def analyze_validated_queue(
    frame: pd.DataFrame,
    schema: pd.DataFrame,
    *,
    context: str,
    kill_switch: bool,
    limit: int,
) -> dict:
    if context == "Análise gerencial":
        return {"status": "Somente indicadores", "rows_analyzed": 0}

    validated = schema[schema["Usar"].astype(bool)]
    text_columns = validated.loc[
        validated["Papel validado"].eq("Texto"), "Coluna"
    ].tolist()
    id_columns = validated.loc[
        validated["Papel validado"].eq("Identificador"), "Coluna"
    ].tolist()
    if not text_columns:
        return {
            "status": "Bloqueado: valide uma coluna como Texto",
            "rows_analyzed": 0,
        }

    results = analyze_queue(
        frame.head(limit),
        text_column=text_columns[0],
        id_column=id_columns[0] if id_columns else None,
        context=context,
        classifier=classifier,
        threshold=selected_threshold,
        kill_switch=kill_switch,
        limit=limit,
    )
    actions = pd.Series(
        [result["decision"]["action"] for result in results]
    ).value_counts()
    care = sum(
        result["customer_care"]["requires_human"] for result in results
    )
    priority_rows = []
    for result in results:
        action = result["decision"]["action"]
        requires_care = result["customer_care"]["requires_human"]
        if action not in {"HUMAN_REVIEW", "ABSTAIN"} and not requires_care:
            continue
        prediction = result["prediction"]
        priority_rows.append(
            {
                "Linha": result["row_id"],
                "Prioridade": "Cuidado com cliente" if requires_care else "Revisar",
                "Assunto sugerido": CATEGORY_LABELS.get(
                    prediction.get("category"),
                    prediction.get("category") or "Não classificado",
                ),
                "Confiança": prediction.get("confidence"),
                "Próxima ação": ACTION_LABELS.get(action, action),
            }
        )
    priority_rows.sort(
        key=lambda row: 0 if row["Prioridade"] == "Cuidado com cliente" else 1
    )
    return {
        "status": "Analisado em observação",
        "rows_analyzed": len(results),
        "human_review": int(
            actions.get("HUMAN_REVIEW", 0) + actions.get("ABSTAIN", 0)
        ),
        "shadow_suggestions": int(actions.get("SHADOW_RECOMMENDATION", 0)),
        "customer_care": int(care),
        "priority_rows": priority_rows,
    }


def set_session_flag(key: str, value: bool = True) -> None:
    st.session_state[key] = value


def build_technical_management_opinion(report: dict) -> dict:
    total_rows = 0
    total_human_review = 0
    total_customer_care = 0
    total_shadow_suggestions = 0
    priority_rows = []

    for item in report["tables"]:
        queue = item["queue_analysis"]
        total_rows += queue.get("rows_analyzed", 0)
        total_human_review += queue.get("human_review", 0)
        total_customer_care += queue.get("customer_care", 0)
        total_shadow_suggestions += queue.get("shadow_suggestions", 0)
        for row in queue.get("priority_rows", []):
            priority_rows.append({"Base": item["name"], **row})

    review_rate = total_human_review / total_rows if total_rows else 0.0
    care_rate = total_customer_care / total_rows if total_rows else 0.0
    shadow_rate = total_shadow_suggestions / total_rows if total_rows else 0.0

    if total_customer_care:
        priority = "Imediata"
        next_action = (
            f"Agora: abrir a fila e direcionar os {total_customer_care} caso(s) "
            "com sinal de cuidado a uma pessoa experiente antes das demais demandas."
        )
    elif total_human_review:
        priority = "Alta"
        next_action = (
            f"Revisar os {total_human_review} caso(s) incertos antes de qualquer "
            "ação ou automação."
        )
    else:
        priority = "Controlada"
        next_action = (
            "Comparar as sugestões do piloto com a decisão da equipe e medir "
            "tempo manual antes de ampliar o uso."
        )

    verdict = (
        "Operação apta para piloto assistido. Não apta para automação autônoma: "
        "casos sensíveis, incertos e qualquer ação externa continuam com uma pessoa."
    )
    risk_summary = (
        report["alerts"][0]
        if report.get("alerts")
        else "Nenhum alerta estrutural adicional foi identificado nesta execução."
    )
    roi_limit = (
        "ROI não foi observado. Os dados atuais não medem tempo de trabalho "
        "manual, custo da equipe, custo de implantação ou retrabalho do piloto. "
        "Qualquer retorno financeiro permanece hipótese."
    )
    evidence = (
        f"Foram analisadas {total_rows:,} linhas nesta execução. "
        f"{total_human_review:,} ({review_rate:.1%}) exigem revisão humana; "
        f"{total_customer_care:,} ({care_rate:.1%}) têm sinal de cuidado com cliente; "
        f"{total_shadow_suggestions:,} ({shadow_rate:.1%}) receberam somente "
        "sugestão em observação."
    ).replace(",", ".")
    markdown = f"""# Parecer técnico-gerencial

## Veredito
{verdict}

## Prioridade
**{priority}.** {next_action}

## Evidências
{evidence}

## Riscos
{risk_summary}

## Limitação do ROI
{roi_limit}

## Próxima ação recomendada
{next_action}
"""
    return {
        "verdict": verdict,
        "priority": priority,
        "evidence": evidence,
        "risk": risk_summary,
        "roi_limit": roi_limit,
        "next_action": next_action,
        "priority_rows": priority_rows,
        "total_human_review": total_human_review,
        "total_customer_care": total_customer_care,
        "total_shadow_suggestions": total_shadow_suggestions,
        "markdown": markdown,
    }


@st.dialog("Parecer técnico-gerencial", width="large")
def show_universal_dashboard() -> None:
    report = st.session_state.get("universal_report")
    if not report:
        st.warning("Confirme a estrutura das duas planilhas primeiro.")
        return

    opinion = build_technical_management_opinion(report)
    st.caption("Gerado após aprovação humana. As fontes originais permanecem intactas.")
    with st.container(border=True):
        st.markdown("#### Veredito")
        st.write(opinion["verdict"])
        st.markdown(f"**Prioridade: {opinion['priority']}**")
        st.write(opinion["evidence"])
        st.markdown("**Risco principal**")
        st.write(opinion["risk"])
        st.markdown("**Limitação do ROI**")
        st.write(opinion["roi_limit"])
        st.markdown("**Próxima ação recomendada**")
        st.info(opinion["next_action"])

    queue_action, evidence_action, download_action = st.columns(3)
    queue_action.button(
        "Abrir fila prioritária",
        use_container_width=True,
        type="primary",
        on_click=set_session_flag,
        args=("universal_show_queue",),
    )
    evidence_action.button(
        "Ver evidências",
        use_container_width=True,
        on_click=set_session_flag,
        args=("universal_show_evidence",),
    )
    download_action.download_button(
        "Baixar parecer",
        data=opinion["markdown"],
        file_name="parecer-tecnico-gerencial.md",
        mime="text/markdown",
        use_container_width=True,
    )

    if st.session_state.get("universal_show_queue"):
        st.markdown("### Fila prioritária")
        if not opinion["priority_rows"]:
            st.success("Nenhum caso exige revisão prioritária nesta execução.")
        else:
            priority_frame = pd.DataFrame(opinion["priority_rows"])
            priority_frame["Confiança"] = priority_frame["Confiança"].map(
                lambda value: (
                    "Não aplicável" if value is None else f"{value:.1%}"
                )
            )
            st.dataframe(
                priority_frame.head(20),
                hide_index=True,
                width="stretch",
            )
            st.caption(
                "A fila mostra no máximo 20 casos e não inclui o texto original."
            )

    if st.session_state.get("universal_show_evidence"):
        st.markdown("### Evidências da análise")
        comparison = report["comparison"]
        st.dataframe(
            comparison.style.format(
                {"Preenchimento": "{:.1%}", "Qualidade": "{:.1f}"}
            ),
            hide_index=True,
            width="stretch",
        )

        for item in report["tables"]:
            st.markdown(f"#### {item['name']}")
            summary = item["summary"]
            first, second, third, fourth = st.columns(4)
            first.metric("Linhas", summary.rows)
            second.metric("Colunas usadas", summary.columns)
            third.metric("Preenchimento", f"{summary.completeness:.1%}")
            fourth.metric(
                "Qualidade estrutural",
                f"{summary.quality_score:.0f}/100",
            )
            distribution = item.get("distribution")
            if distribution is not None:
                st.plotly_chart(
                    management_bar(
                        distribution,
                        x="Categoria",
                        y="Registros",
                        title=f"Principais categorias: {item['name']}",
                    ),
                    width="stretch",
                    config={"displayModeBar": False},
                )
            st.caption(
                f"Uso da IA: {item['queue_analysis']['status']}. "
                f"Linhas analisadas: {item['queue_analysis']['rows_analyzed']}."
            )

        st.markdown("#### Alertas para decisão")
        for alert in report["alerts"]:
            st.write(f"- {alert}")
        st.caption(
            "O painel não calcula NPS, FRT, TTR ou ROI sem os campos e a "
            "instrumentação necessários."
        )

    st.button(
        "Fechar parecer",
        on_click=set_session_flag,
        args=("universal_opinion_open", False),
    )


def activate_case_data() -> None:
    st.session_state.use_case_data = True


def render_universal_decision_entry() -> None:
    st.success(
        "Decisão pronta. Abra o parecer e comece pelos casos que exigem "
        "cuidado ou revisão humana."
    )
    st.button(
        "Ver decisão e fila prioritária",
        type="primary",
        key="open_universal_opinion",
        on_click=set_session_flag,
        args=("universal_opinion_open",),
    )
    if st.session_state.get("universal_opinion_open"):
        show_universal_dashboard()


def render_universal_analysis(kill_switch: bool) -> None:
    st.markdown("## Análise da operação")
    st.caption(
        "Simule um dia comum do líder: carregue as bases, valide a estrutura, "
        "acompanhe a análise e receba uma decisão operacional."
    )

    st.button(
        "Iniciar dia com dados do case",
        type="primary",
        use_container_width=True,
        key="load_case_data_button",
        on_click=activate_case_data,
    )

    st.caption(
        "Atalho de avaliação: duas amostras sistemáticas de até 5.000 linhas, "
        "sem colunas diretas de identificador, nome, e-mail, idade ou gênero. O texto recebe "
        "mascaramento parcial por padrões. A análise integral está nos entregáveis."
    )

    with st.expander("Ou enviar outras planilhas"):
        first_upload, second_upload = st.columns(2)
        with first_upload:
            file_one = st.file_uploader(
                "Planilha 1",
                type=["csv", "xlsx", "xlsm"],
                key="universal_file_one",
            )
        with second_upload:
            file_two = st.file_uploader(
                "Planilha 2",
                type=["csv", "xlsx", "xlsm"],
                key="universal_file_two",
            )

    uploaded_pair = file_one is not None and file_two is not None
    partial_upload = (file_one is None) != (file_two is None)
    if uploaded_pair:
        st.session_state.use_case_data = False
        source_one, source_two = file_one, file_two
        name_one, name_two = file_one.name, file_two.name
    elif st.session_state.get("use_case_data"):
        source_one, source_two = CASE_SUPPORT_SAMPLE_PATH, CASE_IT_SAMPLE_PATH
        name_one = "Dataset 1: amostra do atendimento"
        name_two = "Dataset 2: amostra de suporte de TI"
        st.success("Dados do case carregados. Agora valide a estrutura.")
    else:
        if partial_upload:
            st.info("Envie as duas planilhas ou use os dados do case.")
        else:
            st.info("Use os dados do case para começar sem upload.")
        return

    try:
        frame_one = read_spreadsheet(source_one, filename=f"{name_one}.csv")
        frame_two = read_spreadsheet(source_two, filename=f"{name_two}.csv")
    except Exception as error:
        st.error(f"Não foi possível ler as planilhas: {error}")
        return
    if frame_one.empty or frame_two.empty:
        st.error("As duas planilhas precisam conter pelo menos uma linha.")
        return

    left, right = st.columns(2)
    using_case_data = bool(st.session_state.get("use_case_data"))
    with left:
        schema_one, context_one = render_schema_editor(
            frame_one,
            title=name_one,
            key="universal_one",
            default_context=(
                CUSTOMER_SUPPORT if using_case_data else "Análise gerencial"
            ),
        )
    with right:
        schema_two, context_two = render_schema_editor(
            frame_two,
            title=name_two,
            key="universal_two",
            default_context=IT_SUPPORT if using_case_data else "Análise gerencial",
        )

    common_columns = sorted(set(frame_one.columns).intersection(frame_two.columns))
    relationship = st.selectbox(
        "Relação validada entre as planilhas",
        ["Não relacionar automaticamente", *common_columns],
        help=(
            "Ter o mesmo nome não prova que duas colunas possuem a mesma "
            "semântica. Selecione apenas uma chave conferida."
        ),
    )
    limit = st.number_input(
        "Máximo de linhas por base nesta análise",
        min_value=1,
        max_value=min(5000, max(len(frame_one), len(frame_two))),
        value=min(1000, max(len(frame_one), len(frame_two))),
        step=100,
        help=(
            "O limite vale separadamente para cada base. Exemplo: 4.000 por "
            "base em duas bases permite analisar até 8.000 linhas no total."
        ),
    )

    selected_one = schema_one[schema_one["Usar"].astype(bool)]["Coluna"].tolist()
    selected_two = schema_two[schema_two["Usar"].astype(bool)]["Coluna"].tolist()
    total_rows = len(frame_one) + len(frame_two)
    rows_to_analyze = min(int(limit), len(frame_one)) + min(
        int(limit), len(frame_two)
    )
    rows_outside_limit = total_rows - rows_to_analyze
    total_selected = len(selected_one) + len(selected_two)
    st.markdown("### Aprovação humana")
    st.caption(
        "Confira o recibo abaixo. A análise só começa depois da sua aprovação."
    )
    approval_a, approval_b, approval_c, approval_d = st.columns(4)
    approval_a.metric("Bases carregadas", "2")
    approval_b.metric("Linhas disponíveis", f"{total_rows:,}".replace(",", "."))
    approval_c.metric(
        "Linhas a analisar",
        f"{rows_to_analyze:,}".replace(",", "."),
    )
    approval_d.metric("Colunas aceitas", total_selected)
    limit_message = (
        f"Limite aplicado: até {int(limit):,} linha(s) por base. "
        f"Com 2 bases, esta execução analisará {rows_to_analyze:,} de "
        f"{total_rows:,} linhas disponíveis. "
        f"{rows_outside_limit:,} linha(s) ficarão fora desta execução."
    ).replace(",", ".")
    st.info(limit_message)
    st.success("Fontes alteradas: 0. A análise trabalha sobre uma cópia.")

    duplicate_rows = int(frame_one.duplicated().sum() + frame_two.duplicated().sum())
    missing_cells = int(frame_one.isna().sum().sum() + frame_two.isna().sum().sum())
    if duplicate_rows or missing_cells:
        st.warning(
            f"Problemas encontrados: {duplicate_rows} linha(s) duplicada(s) e "
            f"{missing_cells} célula(s) vazia(s). Campos incompletos bloqueiam "
            "somente os indicadores que dependem deles."
        )
    else:
        st.success("Nenhuma duplicata exata ou célula vazia foi encontrada.")

    with st.expander("Ver colunas aceitas e proteção aplicada"):
        accepted = pd.DataFrame(
            [
                *[
                    {"Base": name_one, "Coluna aceita": column}
                    for column in selected_one
                ],
                *[
                    {"Base": name_two, "Coluna aceita": column}
                    for column in selected_two
                ],
            ]
        )
        st.dataframe(accepted, hide_index=True, width="stretch")
        if st.session_state.get("use_case_data"):
            st.caption(
                "Amostras do case: identificadores diretos foram removidos e "
                "o texto recebeu mascaramento parcial por padrões."
            )
        else:
            st.caption(
                "Arquivos enviados: o mascaramento parcial por padrões ocorre "
                "apenas antes da etapa de IA."
            )

    st.info(
        "Decisão do líder agora: confirme o contexto e as colunas de texto. "
        "Se estiverem errados, ajuste acima. Se estiverem corretos, aprove para "
        "separar cuidado com cliente, baixa confiança e demais solicitações."
    )

    approval_requested = st.button(
        "Aprovar estrutura e analisar",
        type="primary",
    )
    if not approval_requested:
        if st.session_state.get("universal_report"):
            render_universal_decision_entry()
        return

    with st.status("Analisando a operação", expanded=True) as analysis_status:
        st.write("1. Estrutura aprovada por uma pessoa.")
        try:
            summary_one = summarize_table(frame_one, schema_one, name=name_one)
            summary_two = summarize_table(frame_two, schema_two, name=name_two)
            prepared_one = apply_schema(frame_one, schema_one)
            prepared_two = apply_schema(frame_two, schema_two)
        except ValueError as error:
            analysis_status.update(label="Análise interrompida", state="error")
            st.error(str(error))
            return

        st.write("2. Fontes preservadas e cópias de trabalho preparadas.")
        table_reports = []
        for frame, schema, summary, context in [
            (prepared_one, schema_one, summary_one, context_one),
            (prepared_two, schema_two, summary_two, context_two),
        ]:
            distribution = None
            if summary.category_columns:
                distribution = category_distribution(
                    frame,
                    summary.category_columns[0],
                )
            table_reports.append(
                {
                    "name": summary.name,
                    "summary": summary,
                    "distribution": distribution,
                    "queue_analysis": analyze_validated_queue(
                        frame,
                        schema,
                        context=context,
                        kill_switch=kill_switch,
                        limit=min(int(limit), len(frame)),
                    ),
                }
            )
        st.write("3. Casos sensíveis e de baixa confiança separados para revisão.")
        st.write("4. Fila prioritária e próximos passos preparados para o líder.")
        analysis_status.update(label="Análise concluída", state="complete")

    alerts = []
    for summary in (summary_one, summary_two):
        if summary.completeness < 0.95:
            alerts.append(
                f"{summary.name}: há campos ausentes; valide elegibilidade por indicador."
            )
        if summary.exact_duplicate_rows:
            alerts.append(
                f"{summary.name}: {summary.exact_duplicate_rows} linhas exatamente repetidas exigem auditoria."
            )
        if not summary.text_columns:
            alerts.append(
                f"{summary.name}: nenhuma coluna foi validada como Texto; não aplicar NLP."
            )
    if relationship == "Não relacionar automaticamente":
        alerts.append(
            "As planilhas permanecem separadas porque nenhuma chave comum foi validada."
        )
    else:
        alerts.append(
            f"A coluna {relationship} foi indicada como relação, mas o painel não faz join destrutivo."
        )

    st.session_state.universal_report = {
        "comparison": compare_summaries(summary_one, summary_two),
        "tables": table_reports,
        "alerts": alerts,
        "relationship": relationship,
    }
    render_universal_decision_entry()


def render_home(kill_switch: bool) -> None:
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    d1 = audit["dataset_1"]
    total_records = d1["rows"] + metrics["data"]["rows"]

    st.markdown(
        f"""
        <div class="section-kicker">CHALLENGE 002 · REDESIGN DE SUPORTE</div>
        <h2>{total_records:,} registros. Uma decisão: onde a IA realmente ajuda?</h2>
        <p class="lead">
          O case combina {d1["rows"]:,} solicitações de clientes com
          {metrics["data"]["rows"]:,} textos classificados de suporte de TI.
          O problema não é apenas processar volume. É priorizar o que exige
          ação agora sem automatizar risco.
        </p>
        """.replace(",", "."),
        unsafe_allow_html=True,
    )

    problem, evaluation = st.columns(2)
    with problem:
        with st.container(border=True):
            st.markdown("**O problema de negócio**")
            st.write(
                "O líder recebe filas grandes, registros incompletos e clientes "
                "que podem voltar sem solução. Tratar tudo igual desperdiça "
                "tempo; automatizar tudo aumenta o risco."
            )
    with evaluation:
        with st.container(border=True):
            st.markdown("**O que esta avaliação verifica**")
            st.write(
                "Se o protótipo usa os dois datasets, produz uma fila acionável, "
                "explica cada número e preserva uma pessoa nas decisões "
                "sensíveis ou incertas."
            )

    st.markdown(
        """
        <div class="section-kicker">SIMULAÇÃO OPERACIONAL</div>
        <h2>Opere como um líder de suporte</h2>
        <p class="lead">
          O sistema carrega as bases do case, pede sua aprovação e só então
          revela a fila prioritária, os limites e a próxima ação.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.button(
        "Iniciar dia com dados do case",
        key="evaluator_case_data",
        on_click=go_to_case_analysis,
        type="primary",
        use_container_width=True,
    )
    evaluator_left, evaluator_right = st.columns(2)
    evaluator_left.button(
        "Testar uma solicitação",
        key="evaluator_demo",
        on_click=navigate,
        args=("Demonstração",),
        use_container_width=True,
    )
    evaluator_right.button(
        "Examinar entregáveis",
        key="evaluator_deliverables",
        on_click=navigate,
        args=("Entregáveis",),
        use_container_width=True,
    )

def render_queue_upload(kill_switch: bool) -> None:
    st.markdown("### Enviar outro CSV")
    st.caption(
        "Use uma coluna com mensagens. A saída não copia o texto original."
    )
    uploaded_file = st.file_uploader("Arquivo CSV", type=["csv"])
    if uploaded_file is None:
        return
    try:
        queue = pd.read_csv(uploaded_file)
    except Exception as error:
        st.error(f"Não foi possível ler o arquivo: {error}")
        return
    if queue.empty:
        st.error("O arquivo está vazio.")
        return

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
    id_column = st.selectbox(
        "Identificador",
        ["Usar número da linha", *id_candidates],
    )
    limit = st.number_input(
        "Máximo de linhas",
        min_value=1,
        max_value=5000,
        value=min(500, len(queue)),
        step=100,
    )
    if not st.button("Analisar CSV", type="primary"):
        return

    selected = queue.head(int(limit)).copy()
    queue_results = analyze_queue(
        selected,
        text_column=text_column,
        id_column=None if id_column == "Usar número da linha" else id_column,
        context=st.session_state.service_context,
        classifier=classifier,
        threshold=selected_threshold,
        kill_switch=kill_switch,
        limit=int(limit),
    )
    rows = []
    for position, result in enumerate(queue_results):
        prediction = result["prediction"]
        assessment = result["customer_care"]
        decision = result["decision"]
        if st.session_state.service_context == CUSTOMER_SUPPORT:
            category = (
                selected.iloc[position]["Ticket Type"]
                if "Ticket Type" in selected.columns
                else "Classificação humana"
            )
            confidence = "Não aplicável"
        else:
            category = CATEGORY_LABELS.get(
                prediction["category"],
                prediction["category"],
            )
            confidence = f"{prediction['confidence']:.1%}"
        rows.append(
            {
                "ID": result["row_id"],
                "Assunto": category,
                "Confiança": confidence,
                "Cuidado prioritário": (
                    "Sim" if assessment["requires_human"] else "Não"
                ),
                "Próximo passo": ACTION_LABELS.get(
                    decision["action"],
                    decision["action"],
                ),
            }
        )
        care_record = dict(assessment)
        care_record.pop("reasons")
        log_decision(
            pii_counts=result["pii_counts"],
            prediction=prediction,
            decision=decision,
            kill_switch=kill_switch,
            customer_care=care_record,
        )

    output = pd.DataFrame(rows)
    st.success(f"{len(output)} solicitações analisadas sem ação externa.")
    st.dataframe(output, hide_index=True, width="stretch")
    st.download_button(
        "Baixar resultado",
        output.to_csv(index=False).encode("utf-8"),
        file_name="triagem.csv",
        mime="text/csv",
    )


def render_triage(kill_switch: bool) -> None:
    st.markdown(
        """
        <div class="section-kicker">DEMONSTRAÇÃO</div>
        <h2>Execute os casos do case</h2>
        """,
        unsafe_allow_html=True,
    )

    # Three-sentence framing before any table
    framing_a, framing_b, framing_c = st.columns(3)
    framing_a.caption("**Entrada:** mensagem anonimizada e fila identificada.")
    framing_b.caption("**Decisão:** categoria, confiança e próximo passo sugeridos.")
    framing_c.caption("**Saída:** resultado gravado no audit log sem ação externa.")

    # Primary action: run the case matrix
    run_matrix = st.button(
        "Executar testes do case",
        type="primary",
        use_container_width=True,
        key="triage_run_matrix",
    )
    if run_matrix:
        st.session_state.matrix_results = evaluate_matrix(
            classifier=classifier,
            threshold=selected_threshold,
            memory_path=MEMORY_PATH,
            kill_switch=kill_switch,
        )

    results = st.session_state.get("matrix_results")
    if results is not None:
        passed = int(results["Resultado"].eq("PASS").sum())
        if passed == len(results):
            st.success(f"{passed}/{len(results)} casos aprovados.")
        else:
            st.error(f"{passed}/{len(results)} casos aprovados. Revise os FAIL.")
        # Essential columns only
        essential_cols = [c for c in ["ID", "Fila", "Cenário", "Resultado", "Decisão"] if c in results.columns]
        st.dataframe(results[essential_cols], hide_index=True, width="stretch")
        with st.expander("Detalhes e download"):
            st.dataframe(results, hide_index=True, width="stretch")
            left, right = st.columns(2)
            left.download_button(
                "Baixar evidência da execução",
                results.to_csv(index=False).encode("utf-8"),
                file_name="resultado-matriz-testes.csv",
                mime="text/csv",
                key="triage_download_results",
            )
            right.download_button(
                "Baixar matriz em CSV",
                matrix_frame().to_csv(index=False).encode("utf-8"),
                file_name="matriz-testes-case.csv",
                mime="text/csv",
                key="triage_download_matrix",
            )

    # Painel gerencial acessível, mas secundário.
    st.divider()
    if st.button("Abrir painel gerencial do case", type="secondary"):
        show_case_dashboard()

    # Secondary: single-message test
    with st.expander("Testar uma mensagem"):
        if "demo_case" not in st.session_state:
            st.session_state.demo_case = "Reincidência com dano financeiro"
        if "service_context" not in st.session_state:
            st.session_state.service_context = CUSTOMER_SUPPORT
        if "request_text" not in st.session_state:
            st.session_state.request_text = DEMO_CASES[
                st.session_state.demo_case
            ]["message"]
        st.radio(
            "Contexto da fila",
            [CUSTOMER_SUPPORT, IT_SUPPORT],
            horizontal=True,
            key="service_context",
        )
        st.selectbox(
            "Caso de demonstração",
            list(DEMO_CASES),
            key="demo_case",
            on_change=load_demo_case,
        )
        request_text = st.text_area(
            "Mensagem",
            height=120,
            key="request_text",
            placeholder="Cole uma mensagem de teste sem dados pessoais reais.",
        )
        if st.button(
            "Analisar solicitação",
            type="primary",
            disabled=not request_text.strip(),
        ):
            analyze_single(
                request_text,
                st.session_state.service_context,
                kill_switch,
            )

    # Secondary: CSV upload
    with st.expander("Enviar CSV para triagem em massa"):
        render_queue_upload(kill_switch)


def render_learning() -> None:
    st.markdown(
        """
        <div class="section-kicker">APRENDIZADO SOB CONTROLE</div>
        <h2>Aprender sem transformar erro em verdade</h2>
        <p class="lead">
          A memória registra evidências e recupera somente lições aprovadas por
          outra pessoa. Ela não modifica o modelo sozinha.
        </p>
        """,
        unsafe_allow_html=True,
    )

    first, second, third = st.columns(3)
    with first:
        with st.container(border=True):
            st.markdown("**Por que não retropropagação agora?**")
            st.write(
                "Ainda não há volume confiável de correções, conjunto final "
                "congelado nem autorização para retreino contínuo."
            )
    with second:
        with st.container(border=True):
            st.markdown("**Por que não RAG agora?**")
            st.write(
                "As lições são poucas, estruturadas e críticas. Regras aprovadas "
                "são mais previsíveis que busca vetorial e geração."
            )
    with third:
        with st.container(border=True):
            st.markdown("**Quando evoluir?**")
            st.write(
                "Somente após acumular exemplos aprovados e provar, em teste "
                "separado, menos erros sem aumentar risco."
            )

    st.markdown("### O que o case já ensinou")
    operational = pd.DataFrame(list_operational_lessons(MEMORY_PATH))
    operational = operational.rename(
        columns={
            "scope": "Escopo",
            "statement": "Aprendizado",
            "evidence": "Evidência",
            "control": "Controle aplicado",
            "applied_in": "Aplicado em",
        }
    )
    st.dataframe(
        operational[
            ["Escopo", "Aprendizado", "Evidência", "Controle aplicado", "Aplicado em"]
        ],
        hide_index=True,
        width="stretch",
    )

    st.markdown("### Correções do classificador")
    st.caption(
        "O texto original não é salvo. Termos gerais não podem conter dados "
        "pessoais ou credenciais."
    )
    last_analysis = st.session_state.get("last_analysis")
    if not last_analysis:
        st.info(
            "Analise um caso da fila de TI para registrar uma nova correção. "
            "A lição de compra abaixo já demonstra o ciclo completo."
        )
    else:
        first, second = st.columns(2)
        first.metric(
            "Sugestão anterior",
            CATEGORY_LABELS.get(
                last_analysis["predicted_category"],
                last_analysis["predicted_category"],
            ),
        )
        second.metric("Confiança", f"{last_analysis['confidence']:.1%}")
        categories = [str(category) for category in classifier.classes]
        corrected_category = st.selectbox(
            "Qual era o assunto correto?",
            categories,
            index=categories.index(last_analysis["predicted_category"]),
            format_func=lambda category: CATEGORY_LABELS.get(category, category),
        )
        operator_id = st.text_input(
            "Identificador de quem registrou",
            value="operador-demo",
        )
        trigger_terms = st.text_input(
            "Termos gerais para casos parecidos",
            placeholder="Ex.: order, monitor",
        )
        recorded = (
            st.session_state.get("feedback_recorded_for")
            == last_analysis["decision_id"]
        )
        if recorded:
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
                    st.success("Lição candidata criada. Outra pessoa deve revisar.")
                else:
                    st.success("Feedback registrado sem criar nova lição.")

    lessons = list_lessons(MEMORY_PATH)
    status_labels = {
        "candidate": "Aguardando revisão",
        "approved": "Aprovado",
        "retired": "Desativado",
    }
    lesson_frame = pd.DataFrame(
        [
            {
                "Status": status_labels.get(lesson["status"], lesson["status"]),
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

    reviewable = [lesson for lesson in lessons if lesson["status"] == "candidate"]
    if reviewable:
        st.markdown("### Revisão independente")
        selected_lesson_id = st.selectbox(
            "Lição para revisar",
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
            "Justificativa",
            value="Regra conferida para uso no piloto.",
        )
        approve, retire = st.columns(2)
        if approve.button("Aprovar aprendizado"):
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
        if retire.button("Desativar aprendizado"):
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


DELIVERABLE_STEPS = [
    {
        "step_num": 1,
        "step_name": "Decisão",
        "description": "Justificativa executiva, Pareto da operação e razões estratégicas por trás da escolha do case.",
        "nota_pedro": "Minha nota: comece aqui pelo parecer 80/20 para entender as prioridades.",
        "items": [
            DELIVERABLES[0],
            DELIVERABLES[1],
            DELIVERABLES[4],
        ],
    },
    {
        "step_num": 2,
        "step_name": "Evidência",
        "description": "Dados brutos auditados, auditoria de integridade e diagnóstico operacional provado.",
        "nota_pedro": "Minha nota: confira a prova dos dados e dos pares temporais na auditoria.",
        "items": [
            DELIVERABLES[2],
            DELIVERABLES[3],
        ],
    },
    {
        "step_num": 3,
        "step_name": "Limites",
        "description": "Fronteira humano-IA, política de abstenção, controle de memória e limitações declaradas.",
        "nota_pedro": "Minha nota: aqui eu decidi não automatizar sem validação e prova de acerto.",
        "items": [
            DELIVERABLES[5],
            DELIVERABLES[7],
            DELIVERABLES[8],
        ],
    },
    {
        "step_num": 4,
        "step_name": "Execução",
        "description": "Engenharia da solução, protocolo de aprovação, generalização universal e histórico de construção.",
        "nota_pedro": None,
        "items": [
            DELIVERABLES[6],
            DELIVERABLES[9],
            DELIVERABLES[10],
        ],
    },
]


@st.dialog("Leitura do entregável", width="large")
def show_deliverable(deliverable: dict) -> None:
    st.markdown(f"## {deliverable['title']}")
    st.caption(deliverable["question"])
    st.write(deliverable["summary"])
    st.divider()
    if not deliverable["path"].exists():
        st.error("Arquivo indisponível.")
        return
    st.markdown(deliverable["path"].read_text(encoding="utf-8"))


def render_deliverables() -> None:
    st.markdown(
        """
        <div class="section-kicker">ENTREGÁVEIS DO CASE</div>
        <h2>Documentação em 4 etapas</h2>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.caption("**Números do Dataset 1**")
        st.write("460 mensagens reincidentes e 49,3% dos pares temporais incoerentes.")
    with c2:
        st.caption("**Uso material dos dois datasets**")
        st.write("Dataset 1 auditado e Dataset 2 classificado.")
    with c3:
        st.caption("**Protótipo funcional**")
        st.write("Casos do case validados com controle humano.")
    with c4:
        st.caption("**Process log**")
        st.write("Histórico completo de decisões e correções registradas.")

    with st.expander("Mapa rápido: onde entra IA e onde ela para"):
        st.caption(
            "Código calcula fatos. IA reconhece padrões textuais. "
            "Pessoas decidem quando há risco ou ação externa."
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Ponto do fluxo": "Qualidade das planilhas",
                        "Responsável": "Código",
                        "Decisão": "Conta nulos, duplicatas e tipos com fórmula reproduzível.",
                    },
                    {
                        "Ponto do fluxo": "Colunas e contexto",
                        "Responsável": "Humano",
                        "Decisão": "Valida o significado antes de qualquer análise.",
                    },
                    {
                        "Ponto do fluxo": "Cliente em risco",
                        "Responsável": "Regras + humano",
                        "Decisão": "Sinais explícitos priorizam; uma pessoa decide a ação.",
                    },
                    {
                        "Ponto do fluxo": "Assunto de suporte de TI",
                        "Responsável": "IA sugere",
                        "Decisão": "Classifica somente no domínio em que foi testada.",
                    },
                    {
                        "Ponto do fluxo": "Baixa confiança",
                        "Responsável": "IA para",
                        "Decisão": "Abaixo de 75%, pede revisão em vez de adivinhar.",
                    },
                    {
                        "Ponto do fluxo": "Prioridade da fila",
                        "Responsável": "Código + humano",
                        "Decisão": "Ordena o volume; o líder confirma a próxima ação.",
                    },
                    {
                        "Ponto do fluxo": "Aprendizado com erros",
                        "Responsável": "Humano aprova",
                        "Decisão": "SQLite guarda lições revisadas; não altera o modelo sozinho.",
                    },
                    {
                        "Ponto do fluxo": "Enviar, cobrar ou liberar acesso",
                        "Responsável": "Humano",
                        "Decisão": "Ações sensíveis e externas permanecem bloqueadas.",
                    },
                ]
            ),
            hide_index=True,
            width="stretch",
        )

    st.markdown("")

    item_counter = 1
    for step in DELIVERABLE_STEPS:
        is_open = step["step_num"] == 1
        with st.expander(
            f"{step['step_num']}. {step['step_name']}", expanded=is_open
        ):
            st.caption(step["description"])
            if step["nota_pedro"]:
                st.markdown(
                    f'<div class="nota-pedro">↳ {step["nota_pedro"]}</div>',
                    unsafe_allow_html=True,
                )

            for deliverable in step["items"]:
                with st.container(border=True):
                    left, right = st.columns([4, 1])
                    with left:
                        st.markdown(
                            f"**{item_counter:02d}. {deliverable['title']}**"
                        )
                        st.caption(deliverable["question"])
                        st.write(deliverable["summary"])
                    with right:
                        if deliverable["path"].exists():
                            st.button(
                                "Ler agora",
                                key=f"deliverable_{item_counter}",
                                on_click=show_deliverable,
                                args=(deliverable,),
                                use_container_width=True,
                            )
                        else:
                            st.error("Arquivo indisponível")
                item_counter += 1

    with st.expander("Arquivos de submissão", expanded=False):
        with st.container(border=True):
            st.markdown("**Matriz de testes**")
            st.write(
                "A planilha cobre os casos principais, os limites do modelo, a memória "
                "aprovada e a regra de não eliminar reincidências."
            )
            matrix = matrix_frame()
            st.download_button(
                "Baixar matriz de testes",
                matrix.to_csv(index=False).encode("utf-8"),
                file_name=MATRIX_PATH.name,
                mime="text/csv",
                key="deliverable_matrix",
            )
        bundle = ROOT / "submission-pedro-goncalves-final.bundle"
        if bundle.exists():
            with st.container(border=True):
                st.markdown("**Pacote final**")
                st.download_button(
                    "Baixar bundle da submissão",
                    bundle.read_bytes(),
                    file_name=bundle.name,
                    mime="application/octet-stream",
                    key="deliverable_bundle",
                )


def render_help() -> None:
    st.markdown(
        """
        <div class="section-kicker">AJUDA</div>
        <h2>Como avaliar o OSS</h2>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
1. Em **Visão geral**, escolha um dos três passos de avaliação.
2. Em **Triagem diária**, teste uma solicitação e veja quando a IA pede ajuda.
3. Em **Análise da operação**, use os dados do case e aprove a estrutura.
4. Confira a fila prioritária e a próxima ação antes das demais métricas.
5. Em **Entregáveis**, leia decisão, evidência, limites e execução sem baixar arquivos.
6. Em **Aprendizado**, confira como correções humanas são registradas e aprovadas.
"""
    )
    st.markdown("### Glossário simples")
    glossary = pd.DataFrame(
        [
            {
                "Termo": "Solicitação",
                "Significado": "Pedido, dúvida ou problema enviado ao atendimento.",
            },
            {
                "Termo": "Modo de observação",
                "Significado": "A IA sugere, mas não responde nem altera sistemas.",
            },
            {
                "Termo": "Confiança",
                "Significado": "Quanto o modelo favorece uma categoria, não uma garantia.",
            },
            {
                "Termo": "Abstenção",
                "Significado": "A IA reconhece que não tem segurança para sugerir.",
            },
            {
                "Termo": "Memória aprovada",
                "Significado": "Lição revisada por outra pessoa antes de ser usada.",
            },
        ]
    )
    st.dataframe(glossary, hide_index=True, width="stretch")
    st.markdown("### O que o piloto não faz")
    st.markdown(
        """
- não responde ao cliente;
- não altera sistemas externos;
- não retreina o modelo sozinho;
- não usa RAG ou busca vetorial sem necessidade comprovada;
- não mistura a fila de clientes com a taxonomia de TI;
- não transforma confiança em autorização.
"""
    )


st.markdown(
    """
    <style>
    :root {
        --hero-bg: #101B2F;
        --hero-bg-2: #0C1626;
        --glass-fill: rgba(255, 255, 255, 0.10);
        --glass-border: rgba(255, 255, 255, 0.28);
        --page-bg: #FFFFFF;
        --card-bg: #FFFFFF;
        --card-border: #EDEEF0;
        --ink: #051D29;
        --text-on-navy: #FFFFFF;
        --text-muted: #6B7280;
        --text-body: #111827;
        --surface-soft: #F8F9FB;
        --radius-card: 16px;
        --radius-small: 8px;
    }

    html, body, [class*="css"] {
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    [data-testid="stSidebar"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    #MainMenu,
    footer {
        display: none !important;
    }

    .stApp {
        background: var(--page-bg);
        color: var(--text-body);
    }

    .block-container {
        max-width: 1160px;
        padding: 1.5rem 2.5rem 5rem;
    }

    .os-nav {
        align-items: center;
        background: #052B3A;
        border: 1px solid #123F50;
        border-radius: var(--radius-small);
        display: grid;
        gap: 1.1rem;
        grid-template-columns: auto minmax(0, 1fr) auto;
        margin-bottom: 1rem;
        min-height: 4.4rem;
        padding: 0.65rem 0.85rem;
    }

    .os-brand {
        align-items: center;
        color: #FFFFFF !important;
        display: flex;
        gap: 0.65rem;
        text-decoration: none !important;
        white-space: nowrap;
    }

    .os-brand strong {
        color: #C79A55;
        font-size: 1.55rem;
        letter-spacing: 0;
    }

    .os-brand span,
    .os-nav-status {
        color: rgba(255, 255, 255, 0.72);
        font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 0.05em;
    }

    .os-nav-links {
        align-items: center;
        display: flex;
        gap: 0.15rem;
        justify-content: center;
        min-width: 0;
    }

    .os-nav-link {
        border: 1px solid transparent;
        border-radius: 6px;
        color: rgba(255, 255, 255, 0.72) !important;
        font-size: 0.78rem;
        font-weight: 650;
        padding: 0.55rem 0.62rem;
        text-decoration: none !important;
        white-space: nowrap;
    }

    .os-nav-link:hover,
    .os-nav-link:focus-visible {
        background: rgba(255, 255, 255, 0.10);
        color: #FFFFFF !important;
        outline: none;
    }

    .os-nav-link.is-active {
        background: #FFFFFF;
        border-color: #FFFFFF;
        color: #052B3A !important;
    }

    .os-nav-status {
        border: 1px solid rgba(255, 255, 255, 0.34);
        border-radius: 999px;
        color: #FFFFFF;
        padding: 0.48rem 0.65rem;
        white-space: nowrap;
    }

    .os-masthead {
        color: var(--text-on-navy);
        background: linear-gradient(160deg, var(--hero-bg-2), var(--hero-bg));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: var(--radius-card);
        padding: 1.35rem 1.6rem;
        margin-bottom: 1rem;
    }

    .os-meta {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        color: rgba(255, 255, 255, 0.68);
        font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .os-masthead h1 {
        color: var(--text-on-navy);
        font-size: 2.35rem;
        line-height: 1.1;
        font-weight: 800;
        margin: 0.6rem 0 0.3rem;
        letter-spacing: 0;
    }

    .os-masthead p {
        color: rgba(255, 255, 255, 0.72);
        font-size: 1rem;
        margin: 0;
        max-width: 760px;
    }

    .os-reference-links {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.8rem;
    }

    .os-reference-links a {
        background: var(--glass-fill);
        border: 1px solid var(--glass-border);
        border-radius: 999px;
        color: var(--text-on-navy);
        font-size: 0.78rem;
        font-weight: 700;
        padding: 0.45rem 0.75rem;
        text-decoration: none;
    }

    .os-reference-links a:hover {
        background: rgba(255, 255, 255, 0.14);
        color: #FFFFFF;
    }

    .section-kicker {
        color: var(--text-muted);
        font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        margin-top: 1.25rem;
        text-transform: uppercase;
    }

    h2 {
        color: var(--ink) !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        letter-spacing: 0 !important;
        margin: 0.35rem 0 0.45rem !important;
    }

    h3 {
        color: var(--ink) !important;
        font-size: 1.15rem !important;
        font-weight: 750 !important;
        letter-spacing: 0 !important;
    }

    .lead {
        color: var(--text-muted);
        font-size: 1rem;
        line-height: 1.65;
        max-width: 820px;
        margin-bottom: 1.5rem;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--card-bg);
        border-color: #D5DADE !important;
        border-radius: var(--radius-card) !important;
        box-shadow: 0 4px 18px rgba(5, 29, 41, 0.06) !important;
        padding: 0.35rem !important;
        transition: border-color 160ms ease, transform 160ms ease;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #D8DDE2 !important;
        transform: translateY(-1px);
    }

    .signal-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1rem;
        margin: 1.25rem 0 1rem;
    }

    .signal-card {
        background: var(--card-bg);
        border: 1px solid #CCD4D9;
        border-top: 4px solid #1E536C;
        border-radius: var(--radius-card);
        padding: 1.15rem;
        box-shadow: 0 4px 18px rgba(5, 29, 41, 0.06);
    }

    .signal-card.signal-critical {
        border-top-color: #9C3D32;
    }

    .signal-card.signal-warning {
        border-top-color: #B9915B;
    }

    .signal-card span {
        color: var(--text-muted);
        font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.66rem;
        font-weight: 700;
        letter-spacing: 0.06em;
    }

    .signal-card strong {
        display: block;
        color: var(--ink);
        font-size: 2.15rem;
        font-weight: 800;
        line-height: 1;
        margin: 1rem 0 0.75rem;
    }

    .signal-card h3 {
        font-size: 0.98rem !important;
        line-height: 1.35 !important;
        margin: 0 0 0.45rem !important;
    }

    .signal-card p {
        color: var(--text-muted);
        font-size: 0.83rem;
        line-height: 1.45;
        margin: 0;
    }

    /* area-grid/area-card CSS removed: home cards replaced by metrics + CTA */

    .nota-pedro {
        background: #FFFDF5;
        border: 1px solid #E6DFCD;
        border-left: 4px solid #B9915B;
        border-radius: 6px;
        color: #1E536C;
        font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.84rem;
        font-weight: 600;
        padding: 0.55rem 0.85rem;
        margin: 0.25rem 0 1rem 0;
        display: inline-block;
        box-shadow: 0 1px 3px rgba(5, 29, 41, 0.05);
    }

    [data-testid="stMetric"] {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: var(--radius-card);
        padding: 0.9rem 1rem;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-muted);
    }

    [data-testid="stMetricValue"] {
        color: var(--ink);
        font-weight: 800;
    }

    label, [data-testid="stCaptionContainer"] {
        color: var(--text-body);
    }

    .stButton > button,
    .stDownloadButton > button {
        background: var(--ink);
        border: 1px solid var(--ink);
        border-radius: var(--radius-small);
        color: #FFFFFF;
        font-weight: 650;
        min-height: 2.6rem;
        transition: background 140ms ease, border-color 140ms ease;
    }

    .stButton > button[kind="primary"] {
        background: var(--ink);
        border-color: var(--ink);
        color: #ffffff;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: var(--hero-bg);
        border-color: var(--hero-bg);
        color: #FFFFFF;
    }

    .stButton > button p,
    .stDownloadButton > button p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    [data-baseweb="segmented-control"] {
        background: var(--surface-soft);
        border: 1px solid var(--card-border);
        border-radius: var(--radius-small);
        padding: 0.2rem;
    }

    [data-baseweb="tab-highlight"] {
        background: var(--ink) !important;
    }

    [data-testid="stDataFrame"] {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: var(--radius-small);
        overflow: hidden;
    }

    [data-testid="stAlert"] {
        border-radius: var(--radius-small);
    }

    hr {
        border-color: var(--card-border) !important;
    }

    @media (max-width: 760px) {
        .block-container {
            padding: 1rem 1rem 3rem;
        }

        .os-masthead {
            padding: 1.5rem;
        }

        .os-masthead h1 {
            font-size: 1.8rem;
        }

        .os-meta {
            align-items: flex-start;
            flex-direction: column;
            gap: 0.35rem;
        }

        .os-nav {
            grid-template-columns: 1fr auto;
        }

        .os-nav-links {
            grid-column: 1 / -1;
            justify-content: flex-start;
            order: 3;
            overflow-x: auto;
            padding-bottom: 0.15rem;
        }

        .os-brand span {
            display: none;
        }

        .signal-grid,
        .area-grid {
            grid-template-columns: 1fr;
        }

        .area-card,
        .area-card:nth-child(n+4) {
            grid-column: span 1;
        }

        .area-card img {
            height: 180px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "os_page" not in st.session_state:
    st.session_state.os_page = "Visão geral"

requested_page = st.query_params.get("page")
if requested_page in PAGES:
    st.session_state.os_page = requested_page

page = st.session_state.os_page

render_top_navigation(page)

st.markdown(
    """
    <div class="os-masthead">
      <div class="os-meta">
        <span>CHALLENGE 002 · REDESIGN DE SUPORTE</span>
      </div>
      <h1>OSS</h1>
      <p>Operating System for Support</p>
      <div class="os-reference-links">
        <a href="https://github.com/pedrotgon/ai-master-challenge/tree/main/challenges/process-002-support"
           target="_blank" rel="noopener noreferrer">Ver case no GitHub</a>
        <a href="https://ats.g4business.com/careers/g4-ai-master-r6gpj1?utm_id=97757_v0_s00_e0_tv0"
           target="_blank" rel="noopener noreferrer">Contexto do G4 AI Master</a>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

_, guard = st.columns([4.8, 1.2], vertical_alignment="center")
with guard:
    send_everything_to_human = st.toggle(
        "Controle máximo",
        value=False,
        help="Quando ativo, toda solicitação fica com uma pessoa.",
    )

st.caption(
    f"Limite mínimo: {selected_threshold:.0%}. Nenhuma ação externa é executada."
)

if page == "Visão geral":
    render_home(send_everything_to_human)
elif page == "Demonstração":
    render_triage(send_everything_to_human)
elif page == "Analisar planilhas":
    render_universal_analysis(send_everything_to_human)
elif page == "Aprendizado":
    render_learning()
elif page == "Entregáveis":
    render_deliverables()
else:
    render_help()
