"""Two-view local Streamlit workbench; durable state belongs to SQLite."""

import json
import os
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import streamlit as st
from triage.artifacts import BUNDLE, ROOT, load_metadata
from triage.core import CLASSES
from triage.repository import Repository
from triage.runtime import TriageService


QUEUES = {"triage_review": "Revisão da triagem", "specialist_review": "Revisão especializada", "standard_review": "Confirmação padrão"}
REASONS = {"standard_confirmation": "Confirmar a sugestão", "policy_human_category": "Categoria exige especialista",
           "low_score": "Score abaixo do limiar", "anomaly_review": "Valor fora da referência",
           "insufficient_reference": "Referência insuficiente", "unsupported_context": "Contexto fora do benchmark IT",
           "invalid_input": "Texto vazio, inválido ou acima de 10.000 caracteres", "not_ready": "Modelo indisponível ou desatualizado",
           "no_known_features": "Nenhum termo reconhecido", "timeout": "Tempo de análise excedido",
           "invalid_model_output": "Saída do modelo inválida", "inference_error": "Falha na análise",
           "persistence_error": "Não foi possível salvar", "request_conflict": "Identificador já usado para outra entrada",
           "no_feasible_gate": "Critérios de sugestão padrão não atingidos"}


def show_result(result):
    if not result["persisted"]:
        st.error("Análise não salva. Corrija a falha e tente novamente explicitamente.")
    elif result["outcome"] == "failed":
        st.error("Falha registrada. Encaminhe para revisão humana.")
    else:
        st.success("Análise salva. A decisão exige confirmação humana.")
    left, right = st.columns(2)
    left.metric("Categoria sugerida", result["predicted_category"] or "Sem sugestão")
    right.metric("Destino sugerido", QUEUES[result["review_queue"]])
    st.write(" · ".join(REASONS.get(reason, reason) for reason in result["reason_codes"]))
    if result["score"] is not None:
        st.caption(f"Score: {result['score']:.3f}. Não representa probabilidade calibrada de acerto.")
    st.caption(f"Execução: {result['run_id']}")


def main():
    st.set_page_config(page_title="Triagem IT assistida", page_icon="🗂️", layout="wide")
    st.title("Triagem IT assistida")
    st.caption("Sugestões para revisão humana · benchmark retrospectivo · nenhuma ação externa")
    try:
        repository = Repository(Path(os.environ.get("TRIAGE_DB_PATH", ROOT / "data/runtime/triage.sqlite3")))
    except Exception:
        st.error("Histórico indisponível. Não é possível salvar análises neste momento.")
        return
    examples = []
    try:
        manifest, policy, _ = load_metadata()
        st.info("Modelo disponível. Toda sugestão precisa ser confirmada." if policy["mode"] == "qualified" else "Modelo disponível apenas para revisão: os critérios de sugestão padrão não foram atingidos.")
        examples = json.loads((ROOT / BUNDLE / "demo-examples.json").read_text())
    except Exception:
        st.warning("Modelo indisponível ou desatualizado. Você pode registrar o encaminhamento para revisão.")
    triage_tab, review_tab = st.tabs(["Triagem", "Revisão e anomalias"])
    with triage_tab:
        st.subheader("Nova análise")
        st.write("Informe um texto de ticket. O contexto IT é uma declaração sua; não há detecção automática de domínio.")
        if examples:
            chosen = st.selectbox("Exemplo do treino", range(len(examples)), format_func=lambda i: f"Exemplo {i + 1}")
            if st.button("Carregar exemplo"):
                st.session_state["ticket_text"] = examples[chosen]["text"]
                st.session_state["origin"] = examples[chosen]
                st.session_state["ticket_context"] = "it_service_en"
        with st.form("triage_form"):
            text = st.text_area("Texto do ticket", key="ticket_text", height=160)
            context = st.selectbox("Contexto declarado", ["unknown", "it_service_en", "customer_support"], key="ticket_context",
                                   format_func=lambda value: {"unknown": "Desconhecido", "it_service_en": "IT em inglês", "customer_support": "Atendimento ao cliente"}[value])
            submitted = st.form_submit_button("Analisar e salvar")
        if submitted:
            request_id = st.session_state.setdefault("request_id", str(uuid.uuid4()))
            origin = st.session_state.get("origin", {})
            known_origin = origin if origin.get("text") == text and context == "it_service_en" else {}
            with st.spinner("Analisando e registrando…"):
                result = TriageService(repository).submit(text, context, request_id, known_origin.get("case_id"), known_origin.get("source"))
            st.session_state["last_result"] = result
            if result["persisted"]:
                st.session_state["request_id"] = str(uuid.uuid4())
        if "last_result" in st.session_state:
            show_result(st.session_state["last_result"])
    with review_tab:
        st.subheader("Análises salvas")
        runs = repository.list_runs()
        if not runs:
            st.write("Nenhuma análise salva ainda.")
            return
        index = {run["run_id"]: run for run in runs}
        run_id = st.selectbox("Execução para revisar", list(index), format_func=lambda key: f"{index[key]['created_at'][:19]} · {index[key]['predicted_category'] or 'Sem categoria'} · {key[:8]}")
        detail = repository.get_run(run_id)
        with st.expander("Texto e resultado originais"):
            st.text(detail["original_text"] or "Texto não retido: entrada inválida ou acima do limite.")
            show_result(detail["result"])
            st.caption("As revisões abaixo não sobrescrevem este resultado.")
        target = st.selectbox("Alvo da revisão", ["case", "model_score", "text_chars"], format_func=lambda value: {"case": "Decisão da triagem", "model_score": "Avaliação do score", "text_chars": "Avaliação do tamanho"}[value])
        with st.form("review_form"):
            decisions = ["accepted", "corrected", "deferred", "pending"] if target == "case" else ["confirmed_valid", "confirmed_issue", "deferred", "pending"]
            decision = st.selectbox("Decisão da revisão", decisions, key=f"decision_{target}",
                                    format_func=lambda value: {"accepted": "Aceitar triagem/encaminhamento", "corrected": "Corrigir categoria IT", "deferred": "Adiar", "confirmed_valid": "Valor válido (métrica)", "confirmed_issue": "Problema confirmado (métrica)", "pending": "Reabrir como pendente"}[value])
            corrected = st.selectbox("Categoria corrigida (apenas para correção de triagem IT)", ["—", *CLASSES])
            reviewer = st.text_input("Seu nome ou identificação", max_chars=120)
            reviewer_type = st.selectbox("Tipo de revisor", ["operator_declared", "automated_test"],
                                          format_func=lambda value: "Operador (declarado)" if value == "operator_declared" else "Teste automatizado")
            reason = st.text_area("Motivo da revisão", max_chars=2000)
            save_review = st.form_submit_button("Registrar revisão")
        st.caption("Identificação declarada, sem autenticação de papéis. Avaliações de métricas e decisões de triagem têm estados próprios.")
        if save_review:
            try:
                repository.review(run_id, decision, reviewer, reason, None if target == "case" else target,
                                  corrected if decision == "corrected" and corrected != "—" else None, reviewer_type=reviewer_type)
                st.success("Revisão registrada como novo evento. Valores originais preservados.")
            except (ValueError, TypeError) as error:
                st.error("Confira o alvo, o estado, a identificação e o motivo. Correção exige contexto IT e uma categoria válida.")
            except Exception:
                st.error("Não foi possível salvar a revisão. Tente novamente explicitamente.")
        history = repository.get_run(run_id)["reviews"]
        if history:
            st.dataframe(history, hide_index=True)
        st.subheader("Avaliações e filtros")
        all_rows = repository.filter_metrics()
        filters = {}
        columns = st.columns(4)
        for i, (field, label) in enumerate([("status", "Situação"), ("direction", "Direção"), ("reason", "Motivo da métrica"),
                                          ("review_state", "Estado da revisão"), ("category", "Categoria"), ("metric", "Métrica"), ("model_version", "Versão do modelo")]):
            choices = sorted({row[field] for row in all_rows if row.get(field) is not None})
            filters[field] = columns[i % 4].selectbox(label, [None, *choices], key=f"filter_{field}", format_func=lambda value: "Todos" if value is None else value)
        rows = repository.filter_metrics(**filters)
        st.caption(f"{len(rows)} avaliações · {len({r['run_id'] for r in rows})} execuções · {len({r['case_id'] for r in rows})} casos. Filtros combinados com E.")
        st.dataframe(rows, hide_index=True)


if __name__ == "__main__":
    main()
