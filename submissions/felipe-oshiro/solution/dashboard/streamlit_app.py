"""Demo web interativa do classificador de tickets (Streamlit).

Replica o dashboard_g4.html (via streamlit_template.html, gerado por
build_streamlit_template.py) e injeta, no marcador `<!-- classifier-slot -->`
no fim da seção 2, um classificador em tempo real: o usuário insere o texto
livre do ticket, clica em "Classificar ticket" e recebe tópico, confiança e
decisão AUTO/HUMANO — a mesma lógica do CLI solution/scripts/route_tickets.py.

Reuso da lógica (sem duplicação):
  - load_model / predict_probs / decide  ← route_tickets.py
  - limiar 0,86                          ← artifacts/router_threshold.json
  - modelo DistilBERT                    ← artifacts/transformer/

Como rodar:
  solution/.venv/bin/pip install -r solution/requirements.txt
  solution/.venv/bin/streamlit run solution/dashboard/streamlit_app.py
"""

import html as html_mod
import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import route_tickets as rt  # noqa: E402  (módulo do CLI; main() só roda em __main__)

TEMPLATE = ROOT / "dashboard" / "streamlit_template.html"

st.set_page_config(
    page_title="Triagem inteligente de tickets — G4 Educação",
    page_icon=str(ROOT / "brand" / "icone-azul-270.png"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS: esconde o chrome do Streamlit, devolve o layout full-bleed do design e
# estiliza os widgets nativos (textarea/botão/chips) com o mesmo vocabulário
# visual do dashboard (variáveis --navy/--gold etc. vêm do template).
WIDGET_CSS = """
<style>
#MainMenu, header[data-testid="stHeader"], footer,
div[data-testid="stStatusWidget"], aside[data-testid="stSidebar"] {
  display: none !important;
}
.stApp { background: #F5F4F3; }
.block-container { padding: 0; max-width: none; margin: 0 auto; }
.stMarkdown { padding: 0; }

/* textarea do ticket */
.st-key-ticket_text textarea {
  background: #fff;
  border: 1.5px solid #184560;
  border-radius: 10px;
  color: #031A26;
  font-size: .98rem;
  line-height: 1.55;
  padding: .7rem .9rem;
  min-height: 120px;
}
.st-key-ticket_text textarea:focus {
  border-color: #B9915B;
  box-shadow: none;
  outline: none;
}

/* botão principal */
.st-key-classify button {
  background: #001F35;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-family: 'PPMuseum', -apple-system, sans-serif;
  font-weight: 700;
  font-size: .95rem;
  padding: .6rem 1.5rem;
}
.st-key-classify button:hover { background: #184560; color: #fff; }
.st-key-classify button:disabled { opacity: .4; }
.st-key-classify p { margin: 0; }

/* chips de exemplo */
.st-key-chip0 button, .st-key-chip1 button, .st-key-chip2 button {
  background: #fff;
  color: #001F35;
  border: 1.5px solid #184560;
  border-radius: 6px;
  font-family: -apple-system, 'Segoe UI', Roboto, sans-serif;
  font-size: .74rem;
  font-weight: 600;
  padding: .3rem .7rem;
  white-space: nowrap;
}
.st-key-chip0 button:hover, .st-key-chip1 button:hover, .st-key-chip2 button:hover {
  border-color: #B9915B;
  color: #001F35;
}
.st-key-chip0 p, .st-key-chip1 p, .st-key-chip2 p { margin: 0; }

/* o resultado e os chips vivem dentro do fluxo da seção 2 */
.h-block { margin: .4rem 0 1.4rem; }

/* widgets nativos alinhados ao .wrap do design (1080px - 2 × 1.25rem) */
.st-key-ticket_text, .st-key-classify,
div[data-testid="stHorizontalBlock"] {
  max-width: 1048px;
  margin-left: auto;
  margin-right: auto;
}
</style>
"""

EXAMPLES = [
    ("Exemplo — fila AUTO (conf. 0,97)",
     "I'm having an issue with the {product_purchased}. Please assist. "
     "I've checked the device settings and made sure that everything is configured correctly.",
     "chip0"),
    ("Exemplo — triagem humana (conf. 0,45)",
     "I'm having an issue with the {product_purchased}. Please assist. "
     "I need assistance as soon as possible because it's affecting my work and productivity.",
     "chip1"),
    ("Exemplo — classe sensível (conf. 0,31)",
     "I'm having an issue with the {product_purchased}. Please assist. "
     "I've tried clearing the cache and data for the {product_purchased} app, but the issue persists.",
     "chip2"),
]


@st.cache_resource(show_spinner="Carregando DistilBERT fine-tuned… (~15 s, uma única vez por sessão)")
def get_model():
    return rt.load_model()


def fmt_pct(x):
    return f"{x * 100:.1f}".replace(".", ",") + "%"


def result_html(topic, conf, probs, classes, threshold):
    decision, reason = rt.decide(topic, conf, threshold)

    if decision == "AUTO":
        banner = """
        <div class="branch auto">
          <span class="tag">SIM → AUTO</span>
          <div class="b-t">Fila automática</div>
          <p>Roteado para a equipe de <b>{topic}</b> — confiança de {conf}
          (≥ limiar {thr}) e tópico não sensível.</p>
        </div>"""
    elif reason == "low_confidence":
        banner = """
        <div class="branch human">
          <span class="tag">NÃO → HUMANO</span>
          <div class="b-t">Triagem humana</div>
          <p>Baixa confiança: {conf} &lt; limiar {thr}. Uma pessoa decide o destino do ticket.</p>
        </div>"""
    else:
        banner = """
        <div class="branch human">
          <span class="tag">NÃO → HUMANO</span>
          <div class="b-t">Triagem humana</div>
          <p>Classe sensível: <b>{topic}</b> → sempre humano, mesmo com confiança de {conf}.</p>
        </div>"""
    banner = banner.format(topic=html_mod.escape(topic), conf=fmt_pct(conf),
                           thr=f"{threshold:.2f}".replace(".", ","))

    order = probs.argsort()[::-1][:3]
    bars = []
    for rank, i in enumerate(order):
        cls = "step win" if rank == 0 else "step"
        bars.append(
            f'<div class="{cls}">'
            f'<div class="step-n">{html_mod.escape(classes[i])}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{probs[i] * 100:.1f}%"></div></div>'
            f'<div class="pct">{fmt_pct(probs[i])}</div>'
            f'</div>'
        )

    return (
        '<div class="h-block">'
        '<div class="flow" style="max-width:620px">'
        + banner +
        '<p class="step-note" style="text-align:center">Top-3 probabilidades do modelo para este texto:</p>'
        '<div style="max-width:520px;width:100%">' + "".join(bars) + '</div>'
        '<p class="step-note" style="text-align:center">'
        'Administrative rights → sempre humano · abaixo de 0,86 → triagem humana.</p>'
        '</div></div>'
    )


def main():
    # modelo eager + cache (decisão: toda classificação instantânea)
    tok, model, classes = get_model()
    threshold = json.loads(rt.THRESHOLD_JSON.read_text())["threshold"]

    template = TEMPLATE.read_text(encoding="utf-8")
    assert "<!-- classifier-slot -->" in template, "marcador ausente no template"
    part1, part2 = template.split("<!-- classifier-slot -->", 1)

    # st.html (não st.markdown): injeta HTML puro no DOM, sem passar pelo
    # parser de markdown — que quebraria o template em blocos a cada linha
    # em branco e vazaria o CSS como texto.
    st.html(part1 + WIDGET_CSS)

    # ---- bloco interativo (injetado no fim da seção 2) ----
    st.html(
        '<div style="max-width:1080px;margin:0 auto;padding:0 1.25rem">'
        '<p class="kicker" style="margin-top:1.5rem">Experimente agora</p>'
        '<h3>Classifique um ticket em tempo real</h3>'
        '<p style="max-width:760px;color:#706F6F;margin:.3rem 0 1rem">'
        'Cole o texto cru do ticket (como chega da produção, ruído e tudo — '
        'os exemplos usam os placeholders <code>{product_purchased}</code> do lote) '
        'e receba tópico, confiança e decisão de roteamento na hora.</p></div>'
    )

    cols = st.columns([1, 1, 1, 3])
    for (label, text, key), col in zip(EXAMPLES, cols):
        col.button(label, key=key, on_click=_set_text, args=(text,),
                   width="content")

    st.text_area("Texto do ticket", key="ticket_text",
                 label_visibility="collapsed",
                 placeholder='Ex.: "my laptop will not turn on"',
                 height=140)

    clicked = st.button("Classificar ticket", key="classify", width="content",
                        disabled=not st.session_state.get("ticket_text", "").strip())

    if clicked:
        text = st.session_state["ticket_text"].strip()
        probs = rt.predict_probs([text], tok, model, rt.get_device())[0]
        idx = int(probs.argmax())
        topic, conf = classes[idx], float(probs[idx])
        st.html(result_html(topic, conf, probs, classes, threshold))

    st.html(part2)


def _set_text(text):
    st.session_state["ticket_text"] = text


if __name__ == "__main__":
    main()
