"""Batch workbench and an explicitly human, local usability comparison."""

from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3
import uuid

import pandas as pd
import streamlit as st

from batch_workflow import MAX_ROWS, WorkflowStore, parse_csv
from triage.artifacts import ROOT
from triage.core import CLASSES

MODES = {"manual":"Manual", "assisted":"Assistido"}
ACTORS = {"operator_declared":"Operador (declarado)", "automated_test":"Teste automatizado"}
STATES = {"active":"Em andamento", "completed":"Concluído", "aborted":"Interrompido"}
QUEUES = {"standard_review":"Confirmação padrão", "triage_review":"Revisão da triagem", "specialist_review":"Revisão especializada"}
REASONS = {"standard_confirmation":"Confirmar sugestão", "policy_human_category":"Categoria exige especialista",
           "low_score":"Score abaixo do limiar", "anomaly_review":"Possível anomalia", "insufficient_reference":"Referência insuficiente",
           "unsupported_context":"Contexto não suportado", "invalid_input":"Entrada inválida", "not_ready":"Modelo indisponível",
           "no_known_features":"Sem termos reconhecidos", "timeout":"Tempo de análise excedido", "invalid_model_output":"Saída inválida",
           "inference_error":"Falha na análise", "persistence_error":"Falha ao salvar sugestão", "request_conflict":"Conflito no identificador",
           "no_feasible_gate":"Revisão manual necessária"}


def store_path():
    return Path(os.environ.get("TRIAGE_WORKFLOW_DB_PATH", ROOT / "data/runtime/workflow.sqlite3"))


def render_learning():
    st.info("Aprendizado central: acurácia não é economia. O candidato questionou se a triagem individual realmente pouparia trabalho. Isso levou ao lote com revisão numa tela e ao ensaio manual versus assistido. A ferramenta está pronta para medir; ganho humano não é presumido.")


def review_batch(store, identifier):
    batch = store.batch(identifier)
    st.write(f"**{MODES[batch['mode']]}** · {len(batch['items'])} tickets · {ACTORS[batch['actor_type']]} · {STATES[batch['state']]}")
    st.caption(f"Lote: {identifier} · início: {batch['started_at']}. O tempo inclui espera, pausas, correções e preparação do arquivo; não mede esforço ativo isolado.")
    if batch["state"] == "aborted":
        st.warning("Lote encerrado sem conclusão; tentativa e motivo preservados.")
        return
    if batch["state"] == "completed":
        st.success(f"Arquivo preparado. Tempo decorrido do lote: {batch['elapsed_seconds']:.1f} s. Download/rede e entrega ao helpdesk ficam fora dessa medição.")
        st.download_button("Baixar decisões finais", batch["artifact"].encode("utf-8-sig"), f"{identifier.replace(':','-')}.csv", "text/csv", key=f"artifact_{identifier}", on_click="ignore")
        st.download_button("Baixar trilha do lote", json.dumps(store.audit(identifier),ensure_ascii=False,indent=2),
                           f"{identifier.replace(':','-')}-audit.json", "application/json", key=f"audit_{identifier}", on_click="ignore")
        return
    with st.expander("Encerrar sem concluir (preserva a tentativa)"):
        reason = st.text_input("Motivo da interrupção",key=f"abort_reason_{identifier}")
        if st.button("Registrar interrupção",key=f"abort_{identifier}"):
            try:
                store.abort(identifier,reason)
                st.rerun()
            except (ValueError,OSError) as error:
                st.error(str(error))
    if not batch["items"]:
        st.write("Envie o CSV para continuar. O cronômetro já está iniciado.")
        return
    if batch["mode"] == "assisted" and any(r["prediction"] is None for r in batch["items"]):
        if st.button("Gerar sugestões do lote", key=f"prepare_{identifier}"):
            progress = st.progress(0.0, text="Analisando o lote…")
            try:
                store.prepare(identifier, progress=lambda n,total: progress.progress(n/total, text=f"Analisados {n}/{total}"))
                st.rerun()
            except (ValueError, OSError) as error:
                st.error(str(error))
        st.caption("A preparação usa o modelo congelado; todas as linhas continuam exigindo confirmação. Falhas são visíveis e podem ser classificadas manualmente após a tentativa.")
        return
    choices = store.decisions(identifier)
    frame_rows = []
    for item in batch["items"]:
        prediction = item["prediction"] or {}
        frame_rows.append({"Revisado":False,"ID":item["ticket_id"],"Texto":item["text"],
                           "Categoria final":choices.get(item["ticket_id"],prediction.get("predicted_category") or "—"),
                           "Confirmado":item["ticket_id"] in choices,
                           **({"Sugestão":prediction.get("predicted_category") or "Sem sugestão",
                               "Fila":QUEUES.get(prediction.get("review_queue"),"Revisão da triagem"),"Motivos":", ".join(REASONS.get(code,code) for code in prediction.get("reason_codes",[])),
                               "Falha":not prediction.get("persisted",False) or prediction.get("outcome")=="failed"} if batch["mode"]=="assisted" else {})})
    st.caption(f"{len(choices)}/{len(batch['items'])} tickets confirmados. Corrija a categoria se necessário, marque as linhas que conferiu e registre-as. Nenhuma linha vem marcada como revisada.")
    with st.expander("Textos completos para conferência"):
        for item in batch["items"]:
            st.text(f"Ticket: {item['ticket_id']}")
            st.text(item["text"])
    with st.form(f"batch_decisions_{identifier}"):
        edited = st.data_editor(pd.DataFrame(frame_rows), hide_index=True, num_rows="fixed",
                                disabled=[c for c in frame_rows[0] if c not in {"Revisado","Categoria final"}],
                                column_config={"Revisado":st.column_config.CheckboxColumn("Conferi esta linha"),
                                               "Texto":st.column_config.TextColumn(width="large"),
                                               "Categoria final":st.column_config.SelectboxColumn(options=["—",*CLASSES],required=True)},
                                key=f"batch_editor_{identifier}_{batch['revision']}")
        confirmed = st.checkbox("Conferi os textos e as categorias das linhas marcadas", key=f"attest_{identifier}_{batch['revision']}")
        save = st.form_submit_button("Registrar linhas revisadas")
    if save:
        try:
            if not confirmed:
                raise ValueError("Confirme a conferência das linhas marcadas antes de registrar.")
            selected = {r["ID"]:r["Categoria final"] for r in edited.to_dict("records") if r["Revisado"]}
            event_key = f"decision_token_{identifier}"
            token = st.session_state.setdefault(event_key,str(uuid.uuid4()))
            store.save_decisions(identifier,selected,token,batch["revision"])
            st.session_state.pop(event_key,None)
            st.rerun()
        except (ValueError,OSError) as error:
            st.error(str(error))
    final_ack = False
    if len(choices)==len(batch["items"]):
        st.write("Categorias registradas que irão para o arquivo:")
        st.dataframe([{"ID":r["ticket_id"],"Categoria final registrada":choices[r["ticket_id"]]} for r in batch["items"]],hide_index=True)
        final_ack = st.checkbox("Concluir com as decisões registradas; edições não registradas ficam fora do arquivo",key=f"final_ack_{identifier}_{batch['revision']}")
    if st.button("Preparar arquivo e concluir lote", key=f"finish_{identifier}", disabled=not final_ack):
        try:
            store.finish(identifier,batch["revision"])
            st.rerun()
        except (ValueError,OSError) as error:
            st.error(str(error))


def render_batch_workspace():
    try:
        _render_batch_workspace()
    except (OSError,sqlite3.Error):
        st.error("Registro local do lote indisponível. Nenhuma conclusão foi confirmada nesta ação; confira escrita e integridade do banco antes de tentar novamente.")


def _render_batch_workspace():
    st.header("Triagem em lote")
    st.write("Importe tickets IT em inglês, confira as sugestões numa tabela e exporte as categorias finais. O lote reduz trocas de tela; a economia de tempo precisa ser observada.")
    st.caption("Este CSV alimenta a classificação do lote; não substitui os indicadores do painel, calculados sobre a base de diagnóstico.")
    st.download_button("Baixar cabeçalho CSV", "ticket_id,text\n", "tickets-template.csv", "text/csv", on_click="ignore", key="batch_template")
    with st.form("batch_start"):
        operator = st.text_input("Identificação do operador",max_chars=120,key="batch_operator")
        actor = st.selectbox("Tipo de participante",list(ACTORS),format_func=ACTORS.get,key="batch_actor")
        domain = st.checkbox("Confirmo que os tickets são IT em inglês",key="batch_domain")
        start = st.form_submit_button("Iniciar lote e cronômetro")
    if start:
        try:
            if not domain:
                raise ValueError("Confirme o domínio IT em inglês; o modelo não foi validado para o dataset de clientes.")
            token = st.session_state.setdefault("batch_start_token",str(uuid.uuid4()))
            store = WorkflowStore(store_path())
            st.session_state["selected_operation_batch"] = store.start("assisted",operator,actor,token)
            st.session_state["operation_batch_choice"] = st.session_state["selected_operation_batch"]
            st.session_state.pop("batch_start_token",None)
        except (ValueError,OSError) as error:
            st.error(str(error))
    if not store_path().exists():
        st.caption("Comece o lote antes de enviar o CSV: ticket_id,text; até 50 linhas, UTF-8. reference_category é opcional e não vira entrada do modelo.")
        return
    store = WorkflowStore(store_path())
    batches = [b for b in store.batches() if b["purpose"]=="operation"]
    if not batches:
        return
    ids = [b["id"] for b in batches]
    selected = st.session_state.get("selected_operation_batch",ids[0])
    identifier = st.selectbox("Lote para continuar ou consultar",ids,index=ids.index(selected) if selected in ids else 0,key="operation_batch_choice")
    batch = store.batch(identifier)
    if not batch["items"] and batch["state"]=="active":
        upload = st.file_uploader("CSV de tickets",type="csv",max_upload_size=2,key=f"upload_{identifier}")
        st.caption(f"Colunas: ticket_id,text; reference_category opcional. Máximo {MAX_ROWS} linhas e 10.000 caracteres por texto. Rótulos fornecidos não são mostrados na tabela nem usados na previsão.")
        if st.button("Importar CSV no lote",key=f"import_{identifier}",disabled=upload is None):
            try:
                store.attach(identifier,parse_csv(upload.getvalue()))
                st.rerun()
            except (ValueError,OSError) as error:
                store.note_import_failure(identifier,str(error))
                st.error(str(error))
    review_batch(store,identifier)


def render_experiment():
    try:
        _render_experiment()
    except (OSError,sqlite3.Error):
        st.error("Registro local do ensaio indisponível. As tentativas não foram apagadas; confira o banco antes de continuar.")


def _render_experiment():
    st.header("Experimento manual versus assistido")
    render_learning()
    st.write("Ensaio local de uso: 8 tickets por etapa, casos/grupos distintos do treino e uma tarefa de cada classe em cada etapa. A ordem é definida antes de começar; referências ficam ocultas até concluir as duas etapas.")
    st.caption("Tempo decorrido da abertura do lote atribuído até o arquivo pronto, incluindo importação interna, modelo, espera, conferência e correções. Inclui pausas. Preparação do estudo, criação externa de CSV, download e entrega ao helpdesk ficam fora. Não é medição de custo, esforço ativo ou produção.")
    st.warning("Uma pessoa deve realizar as decisões. Testes automatizados são identificados separadamente e não demonstram ganho humano. Evite consultar resultados/labels por outras telas durante o ensaio.")
    with st.form("study_start"):
        operator = st.text_input("Identificação do participante",max_chars=120,key="study_operator")
        actor = st.selectbox("Tipo do ensaio",list(ACTORS),format_func=ACTORS.get,key="study_actor")
        understood = st.checkbox("Entendi o protocolo e vou completar as duas etapas sem consultar as referências",key="study_understood")
        create = st.form_submit_button("Preparar plano do ensaio")
    if create:
        try:
            if not understood:
                raise ValueError("Leia e confirme o protocolo antes de preparar o plano.")
            token=st.session_state.setdefault("study_start_token",str(uuid.uuid4()))
            store=WorkflowStore(store_path())
            sid=store.create_study(operator,actor,token)
            st.session_state["selected_study"]=sid
            st.session_state["study_choice"]=sid
            st.session_state.pop("study_start_token",None)
        except (ValueError,OSError,StopIteration) as error:
            st.error(f"Não foi possível preparar o ensaio: {error}")
    if not store_path().exists():
        st.info("Nenhum ensaio registrado. O ganho operacional permanece por medir.")
        return
    store=WorkflowStore(store_path())
    studies=store.studies()
    if not studies:
        st.info("Nenhum ensaio registrado. O ganho operacional permanece por medir.")
        return
    results=[store.study_result(s["id"]) for s in studies]
    human=sum(r["completed"] and r["actor_type"]=="operator_declared" for r in results)
    automatic=sum(r["completed"] and r["actor_type"]=="automated_test" for r in results)
    aborted=sum("aborted" in r["states"].values() for r in results)
    st.caption(f"{len(studies)} ensaios preparados · {human} concluídos por operador declarado · {automatic} concluídos como teste automatizado · {aborted} interrompidos. Sem exclusão automática de tentativas.")
    ids=[s["id"] for s in studies]
    chosen=st.session_state.get("selected_study",ids[0])
    sid=st.selectbox("Ensaio para continuar ou consultar",ids,index=ids.index(chosen) if chosen in ids else 0,key="study_choice")
    study=next(s for s in studies if s["id"]==sid)
    result=store.study_result(sid)
    st.write("Ordem fixada: " + " → ".join(MODES[m] for m in study["order"]))
    with st.expander("Plano e limites fixados antes do início"):
        st.json({"study_id":sid,"protocol":study["protocol"],"protocol_sha256":study["protocol_sha256"],"seed":study["seed"],"order":study["order"],"sampling":study["sampling"],"case_manifest":study["case_manifest"]})
    if result["completed"]:
        if result["actor_type"]=="automated_test":
            st.warning("Resultado de teste automatizado. Não usar como prova de economia ou desempenho humano.")
        st.dataframe([{"Etapa":MODES[m],"Casos":r["cases"],"Tempo do lote (s)":r["elapsed_seconds"],
                       "Tempo médio/ticket (s)":r["seconds_per_case"],"Concordância com referência (%)":100*r["reference_concordance"],
                       "Correções da sugestão":r["suggestion_corrections"],"Falhas de sugestão":r["failed_suggestions"]} for m,r in result["arms"].items()],hide_index=True)
        delta=result["manual_minus_assisted_seconds"]
        st.write(f"Diferença observada (manual − assistido): **{delta:.1f} s por lote**. Valor negativo significa que o assistido levou mais tempo.")
        if not result["quality_not_lower_in_sample"]:
            st.warning("A etapa assistida teve menor concordância com as referências nesta amostra. Menor tempo isolado não demonstra melhora de produtividade.")
        st.caption("Comparação descritiva de um ensaio pequeno, com possíveis efeitos de dificuldade, ordem/aprendizado e textos já usados no treino. Referências são rótulos fornecidos, não adjudicação humana. Não extrapolar para economia mensal ou qualidade de produção.")
        st.download_button("Baixar resultado e protocolo",json.dumps(result,ensure_ascii=False,indent=2),f"{sid}-result.json","application/json",on_click="ignore",key=f"study_result_{sid}")
        with st.expander("Arquivos e trilhas das duas etapas"):
            for mode in study["order"]:
                review_batch(store,study["batch_ids"][mode])
        return
    if "aborted" in result["states"].values():
        st.warning("Ensaio interrompido. A tentativa permanece registrada e não produz comparação concluída.")
        return
    active=next((bid for bid in study["batch_ids"].values() if store.batch(bid)["state"]=="active"),None)
    if active:
        review_batch(store,active)
    else:
        if study["batch_ids"]:
            st.success("Primeira etapa concluída e arquivo preservado. Inicie a próxima etapa; a comparação e as referências serão apresentadas somente após as duas conclusões.")
        if st.button("Iniciar próxima etapa e cronômetro",key=f"begin_arm_{sid}"):
            try:
                store.start_arm(sid)
                st.rerun()
            except (ValueError,OSError) as error:
                st.error(str(error))
