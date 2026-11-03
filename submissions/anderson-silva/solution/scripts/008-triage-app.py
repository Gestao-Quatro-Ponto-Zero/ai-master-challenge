"""Streamlit prototype of the triage stage in docs/004 (challenge 002).

A ticket goes through the rules (standardized message, insufficient content), the classifier with a confidence
threshold (routed alone above it, human queue with suggestions below it), similar tickets from the history and a
decision record in the docs/003 format. The optional generative-AI module (summary and information request) runs
only with an OpenRouter key in .env, and every draft needs a person's approval.

The page needs no dataset: on opening it refits the model from results/011 to 013 (exported by script 010 from
the model of script 007) in a few seconds, with the same predictions as the evaluated model. Run it with:
  pip install -r requirements.txt
  streamlit run scripts/008-triage-app.py --server.address 127.0.0.1

Bind to 127.0.0.1: the page reads the OpenRouter key from .env and can spend its balance.
"""
import importlib.util
import json
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
EVALUATION_PATH = RESULTS_DIR / "006-triage-test-evaluation.json"
ENV_PATH = ROOT / ".env"
DECISIONS_LOG = ROOT / "cache" / "004-triage-decisions.jsonl"
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
# Pinned version, chosen by the candidate for cost (audit item 181); override with OPENROUTER_MODEL in .env.
DEFAULT_GENAI_MODEL = "z-ai/glm-5.3-flash"
GENAI_MAX_TOKENS = 2000
GENAI_TIMEOUT_SECONDS = 90
SEED = 42
TOP_SUGGESTIONS = 3
SIMILAR_TICKETS = 3
SNIPPET_CHARS = 160
DEFAULT_TRIAGE_MINUTES = 3.0
CHANNELS = ["Email", "Chat", "Phone", "Social media"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
MODEL_NAME = "TF-IDF + regressão logística, treinado com 80% do Dataset 2"
# Version 2 of the prompts (audit item 185). Version 1 is kept in results/009-genai-prompts-v1.json.
GENAI_TASKS = {
    "summary": ("Gerar resumo para o atendente",
                "Você ajuda um atendente de suporte de TI. Resuma o ticket em português, em até 3 frases: o que a "
                "pessoa pede, o que ela já tentou e o que ainda falta saber. Regras: use só o que está escrito no "
                "texto; não acrescente datas, nomes, números, sistemas ou fatos que não apareçam nele; não complete "
                "datas parciais (se o texto diz só 'sexta-feira', escreva só 'sexta-feira'). O texto pode vir sem "
                "pontuação e sem palavras como 'not'; quando uma frase puder ser lida de dois jeitos, diga que ela "
                "está ambígua em vez de escolher uma leitura."),
    "info_request": ("Gerar pedido de informação ao solicitante",
                     "You help an IT support agent. Write a short, polite message to the requester in the same "
                     "language as the ticket text (if the ticket is in English, write in English). Before writing, "
                     "check which of these the ticket already states: the system or equipment, what happened, the "
                     "exact error message, and since when. Ask only for the items that are missing; never ask for "
                     "something the ticket already states, and briefly restate what you understood. If nothing "
                     "essential is missing, say what you understood and that the team will follow up. Do not promise "
                     "deadlines or solutions, and do not invent names, dates or facts."),
}


def load_rules():
    # Reuse the decision names and the opening rule of the model script, so page and evaluation agree.
    spec = importlib.util.spec_from_file_location("triage_model", Path(__file__).with_name("007-triage-model.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RULES = load_rules()


def number(value, digits=2):
    return f"{value:.{digits}f}".replace(".", ",")


def percent(value):
    return f"{value * 100:.1f}%".replace(".", ",")


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@st.cache_resource(show_spinner="Treinando o modelo com os tickets de treino...")
def load_bundle():
    return RULES.load_page_bundle(RESULTS_DIR)


def read_env():
    if not ENV_PATH.exists():
        return {}
    values = {}
    for line in ENV_PATH.read_text().splitlines():
        name, separator, value = line.partition("=")
        if separator and not name.strip().startswith("#") and value.strip():
            values[name.strip()] = value.strip()
    return values


def append_log(event, record):
    DECISIONS_LOG.parent.mkdir(exist_ok=True)
    with DECISIONS_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": event, "logged_at": now(), "record": record}, ensure_ascii=False) + "\n")


def triage(text, bundle, threshold, min_words):
    model = bundle["model"]
    probabilities = model.predict_proba([text])[0]
    order = np.argsort(-probabilities)[:TOP_SUGGESTIONS]
    suggestions = [(str(model.classes_[index]), float(probabilities[index])) for index in order]
    category, confidence = suggestions[0]
    words = len(text.split())
    is_standard = RULES.opening(text, bundle["prefix_words"]) in bundle["standard_openings"]
    is_short = words < min_words
    if is_standard:
        decision, reason = RULES.DECISION_STANDARD, "A abertura do ticket é uma das mensagens padronizadas do histórico."
    elif is_short:
        decision, reason = RULES.DECISION_INFO, f"O ticket tem {words} palavras, abaixo do mínimo de {min_words}."
    elif confidence >= threshold:
        decision, reason = RULES.DECISION_AUTO, f"Confiança {number(confidence)} acima do limiar {number(threshold)}."
    else:
        decision, reason = RULES.DECISION_HUMAN, f"Confiança {number(confidence)} abaixo do limiar {number(threshold)}."
    return {"text": text, "words": words, "is_standard": is_standard, "is_short": is_short, "category": category,
            "confidence": confidence, "suggestions": suggestions, "decision": decision, "reason": reason,
            "threshold": threshold, "min_words": min_words}


def similar_tickets(text, bundle):
    vector = bundle["model"].named_steps["tfidfvectorizer"].transform([text])
    scores = (bundle["train_matrix"] @ vector.T).toarray().ravel()  # TF-IDF rows are unit length: dot = cosine
    top = np.argsort(-scores)[:SIMILAR_TICKETS]
    return pd.DataFrame({"Semelhança": [number(scores[index]) for index in top],
                         "Categoria recebida": [bundle["train_labels"][index] for index in top],
                         "Trecho": [bundle["train_texts"][index][:SNIPPET_CHARS] for index in top]})


def new_record(result, channel, priority, bundle):
    moment = now()
    routed_alone = result["decision"] == RULES.DECISION_AUTO
    return {
        "ticket_id": uuid.uuid4().hex[:8], "opened_at": moment, "auto_ack_at": moment, "first_response_at": None,
        "channel": channel, "priority": priority, "word_count": result["words"],
        "rules": {"standardized_message": result["is_standard"], "insufficient_content": result["is_short"]},
        "suggested_category": result["category"], "confidence": round(result["confidence"], 4),
        "suggestions": [{"category": name, "probability": round(value, 4)} for name, value in result["suggestions"]],
        "threshold": round(result["threshold"], 4), "decision": result["decision"], "reason": result["reason"],
        "decided_by": "automação" if routed_alone else "pendente: pessoa",
        "assigned_at": moment if routed_alone else None, "queue": result["category"] if routed_alone else None,
        "model": MODEL_NAME, "model_built_at": bundle["built_at"],
    }


def draw_test_ticket(bundle):
    draws = st.session_state.get("draws", 0)
    row = int(np.random.default_rng(SEED + draws).choice(bundle["test_rows"]))
    ticket = bundle["test_tickets"].loc[row]
    st.session_state.update(draws=draws + 1, ticket_text=ticket["text"], drawn_text=ticket["text"],
                            drawn_label=ticket["label"], drawn_row=row)


def run_triage(bundle, threshold, min_words):
    text = st.session_state.get("ticket_text", "").strip()
    if not text:
        st.session_state["triage_warning"] = "Escreva ou sorteie um ticket antes de triar."
        return
    result = triage(text, bundle, threshold, min_words)
    record = new_record(result, st.session_state["channel"], st.session_state["priority"], bundle)
    stale = [key for key in st.session_state if key.startswith(("draft_", "genai_")) or key == "confirmed_category"]
    for key in stale:
        del st.session_state[key]
    st.session_state.update(result=result, record=record, triage_warning=None)
    append_log("triagem", record)


def confirm_category():
    record = dict(st.session_state["record"])
    chosen = st.session_state["confirmed_category"]
    record.update(confirmed_category=chosen, queue=chosen, decided_by="pessoa", assigned_at=now(),
                  corrected=chosen != record["suggested_category"])
    st.session_state["record"] = record
    append_log("confirmação", record)


def ask_model(api_key, model, instructions, text):
    payload = {"model": model, "max_tokens": GENAI_MAX_TOKENS, "reasoning": {"effort": "low"},
               "messages": [{"role": "system", "content": instructions}, {"role": "user", "content": text}]}
    request = urllib.request.Request(CHAT_URL, data=json.dumps(payload).encode(),
                                     headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=GENAI_TIMEOUT_SECONDS) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError(str(result["error"])[:300])
    return (result["choices"][0]["message"].get("content") or "").strip()


def generate_draft(task, api_key, model):
    try:
        draft = ask_model(api_key, model, GENAI_TASKS[task][1], st.session_state["result"]["text"])
    except urllib.error.HTTPError as error:
        st.session_state["genai_error"] = f"Erro {error.code} da API: {error.read().decode(errors='replace')[:200]}"
        return
    except (urllib.error.URLError, TimeoutError, RuntimeError, KeyError) as error:
        st.session_state["genai_error"] = f"Falha ao gerar o rascunho: {str(error)[:200]}"
        return
    st.session_state.update({f"draft_{task}": draft, f"genai_original_{task}": draft, "genai_error": None})


def approve_draft(task, model):
    final = st.session_state[f"draft_{task}"]
    record = dict(st.session_state["record"])
    drafts = dict(record.get("ai_drafts", {}))
    drafts[task] = {"model": model, "approved_by": "pessoa", "approved_at": now(),
                    "edited": final != st.session_state[f"genai_original_{task}"], "text": final}
    record["ai_drafts"] = drafts
    st.session_state["record"] = record
    append_log("rascunho aprovado", record)


def render_genai(api_key, model):
    st.markdown("**IA generativa, sempre com revisão humana**")
    buttons = st.columns(len(GENAI_TASKS))
    for column, (task, (label, _)) in zip(buttons, GENAI_TASKS.items()):
        column.button(label, key=f"generate_{task}", on_click=generate_draft, args=(task, api_key, model))
    if st.session_state.get("genai_error"):
        st.error(st.session_state["genai_error"])
    for task, (label, _) in GENAI_TASKS.items():
        if f"draft_{task}" not in st.session_state:
            continue
        st.text_area(f"Rascunho ({label.lower()}). Edite antes de aprovar.", key=f"draft_{task}", height=120)
        st.button("Aprovar e registrar", key=f"approve_{task}", on_click=approve_draft, args=(task, model))
        if task in st.session_state["record"].get("ai_drafts", {}):
            st.success("Rascunho aprovado e registrado.")


def render_result(bundle, genai_on, api_key, genai_model):
    result = st.session_state["result"]
    target = f" para **{result['category']}**" if result["decision"] == RULES.DECISION_AUTO else ""
    st.subheader("Decisão")
    st.markdown(f"**{result['decision']}**{target}")
    st.caption(result["reason"])
    if st.session_state.get("drawn_text") == result["text"]:
        st.info(f"Rótulo real deste ticket de teste, só para conferência: {st.session_state['drawn_label']}")
    left, right = st.columns(2)
    with left:
        st.markdown("**Regras**")
        st.dataframe(pd.DataFrame({"Regra": ["Mensagem padronizada", f"Menos de {result['min_words']} palavras"],
                                   "Resultado": ["sim" if result["is_standard"] else "não",
                                                 "sim" if result["is_short"] else "não"]}), hide_index=True)
        st.markdown("**Sugestões do classificador**")
        st.dataframe(pd.DataFrame({"Categoria": [name for name, _ in result["suggestions"]],
                                   "Probabilidade": [percent(value) for _, value in result["suggestions"]]}),
                     hide_index=True)
    with right:
        st.markdown("**Tickets parecidos do histórico**")
        st.dataframe(similar_tickets(result["text"], bundle), hide_index=True)
    categories = [str(name) for name in bundle["model"].classes_]
    st.markdown("**Decisão da pessoa: confirmar ou corrigir a categoria**")
    st.selectbox("Categoria", categories, index=categories.index(result["category"]), key="confirmed_category")
    st.button("Confirmar e encaminhar", key="confirm", on_click=confirm_category)
    if st.session_state["record"].get("decided_by") == "pessoa":
        st.success(f"Encaminhado por uma pessoa para {st.session_state['record']['queue']}.")
    if genai_on:
        render_genai(api_key, genai_model)
    st.markdown("**Registro (campos do docs/003)**")
    st.json(st.session_state["record"])


def render_ticket_tab(bundle, threshold, min_words, genai_on, api_key, genai_model):
    text_column, side_column = st.columns([3, 1])
    with side_column:
        st.selectbox("Canal", CHANNELS, key="channel")
        st.selectbox("Prioridade informada", PRIORITIES, key="priority")
        st.button("Sortear ticket do teste", key="draw", on_click=draw_test_ticket, args=(bundle,))
    with text_column:
        st.text_area("Texto do ticket", key="ticket_text", height=180)
    st.button("Triar", type="primary", key="triage", on_click=run_triage, args=(bundle, threshold, min_words))
    if st.session_state.get("triage_warning"):
        st.warning(st.session_state["triage_warning"])
    if st.session_state.get("result"):
        render_result(bundle, genai_on, api_key, genai_model)


def render_evaluation_tab():
    if not EVALUATION_PATH.exists():
        st.warning("Avaliação ainda não gerada. Rode scripts/007-triage-model.py.")
        return
    metrics = json.loads(EVALUATION_PATH.read_text())
    st.markdown(f"Avaliação em **{metrics['test_tickets']} tickets de teste** que o modelo nunca viu,"
                f" com o limiar {number(metrics['threshold'], 3)} e o mínimo de {metrics['min_words']} palavras.")
    columns = st.columns(3)
    columns[0].metric("Acerto geral do classificador", percent(metrics["accuracy_all"]))
    columns[1].metric("Encaminhados sozinhos", percent(metrics["auto_share"]))
    columns[2].metric("Acerto nos encaminhados sozinhos", percent(metrics["auto_accuracy"]))
    st.markdown("**Decisões no teste**")
    st.dataframe(pd.DataFrame({"Decisão": list(metrics["decision_shares"]),
                               "Parcela": [percent(value) for value in metrics["decision_shares"].values()]}),
                 hide_index=True)
    st.markdown("**Por categoria**")
    st.dataframe(pd.DataFrame(metrics["per_category"]).T)
    minutes = st.number_input("Minutos de triagem manual por ticket (m)", 0.5, 30.0, DEFAULT_TRIAGE_MINUTES, 0.5,
                              key="minutes")
    hours = metrics["hours_per_1000_per_minute"] * minutes
    st.markdown(f"**Horas de triagem economizadas a cada 1.000 tickets:** {number(metrics['hours_per_1000_per_minute'])}"
                f" × m = **{number(hours, 1)} horas**. A taxa vem do Dataset 2; na empresa, precisa ser medida de novo.")


def main():
    st.set_page_config(page_title="Triagem de tickets: protótipo", layout="wide")
    st.title("Triagem de tickets: protótipo")
    st.caption("Etapa de triagem da proposta (docs/004). O modelo vem do Dataset 2, um suporte interno de TI: o "
               "protótipo demonstra o mecanismo; na empresa, ele seria treinado de novo com o histórico dela.")
    data_files = [RULES.TRAIN_TICKETS_FILE, RULES.TEST_TICKETS_FILE, RULES.SETTINGS_FILE]
    if not all((RESULTS_DIR / name).exists() for name in data_files):
        st.error("Dados do modelo não encontrados em results/. Rode scripts/007-triage-model.py e depois "
                 "scripts/010-triage-demo-data.py.")
        st.stop()
    bundle = load_bundle()
    env = read_env()
    api_key, genai_model = env.get("OPENROUTER_API_KEY"), env.get("OPENROUTER_MODEL", DEFAULT_GENAI_MODEL)
    with st.sidebar:
        st.header("Ajustes")
        threshold = st.slider("Limiar de confiança para encaminhar sozinho", 0.30, 0.99,
                              round(float(bundle["threshold"]), 2), 0.01, key="threshold")
        st.caption(f"Padrão: {number(bundle['threshold'], 3)}, que deu 95% de acerto no treino.")
        min_words = int(st.number_input("Conteúdo mínimo (palavras)", 1, 30, int(bundle["min_words"]), key="min_words"))
        st.caption("Padrão definido pela medição no treino (docs/006).")
        genai_on = st.toggle("IA generativa (resumo e pedido de informação)", value=bool(api_key),
                             disabled=not api_key, key="use_genai")
        st.caption(f"Modelo: {genai_model}" if api_key else "Sem chave no .env: módulo desligado.")
    ticket_tab, evaluation_tab = st.tabs(["Novo ticket", "Avaliação no teste"])
    with ticket_tab:
        render_ticket_tab(bundle, threshold, min_words, genai_on, api_key, genai_model)
    with evaluation_tab:
        render_evaluation_tab()


# Streamlit runs the page as __main__; other scripts (for example 009) import it to reuse the prompts.
if __name__ == "__main__":
    main()
