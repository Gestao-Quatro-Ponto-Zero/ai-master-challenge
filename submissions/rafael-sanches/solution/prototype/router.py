"""
NUCLEO de classificacao e roteamento — SEM dependencia de UI.
A mesma funcao `classify()` que alimenta a demo Streamlit e a que iria atras
de um endpoint FastAPI em producao. Separar isto da UI e' o que torna o
"caminho para producao" concreto, nao promessa.
"""
from pathlib import Path
import joblib

BASE = Path(__file__).parent
MODEL_PATH = BASE / "model" / "ticket_classifier.joblib"
SAMPLE_PATH = BASE / "sample_tickets.csv"

# Limiar de confianca escolhido empiricamente: ~95% de precisao nos auto-roteados
# (ver curva precisao x cobertura em solution-draft/figures/06_gate_confianca.png).
# Em producao isto e' um valor de CONFIG que o time de ops define, nao um slider.
DEFAULT_THRESHOLD = 0.69

# Cada categoria -> fila/time responsavel. Este mapa e' o "roteamento".
QUEUES = {
    "Hardware": "Equipe de Hardware / Field Support",
    "HR Support": "RH / People Ops",
    "Access": "IAM / Gestão de Acessos",
    "Administrative rights": "Suporte Desktop (admin local)",
    "Storage": "Infra / Armazenamento",
    "Purchase": "Compras / Procurement",
    "Internal Project": "Engenharia / Projetos Internos",
    "Miscellaneous": "Triagem Geral",
}

_model = None


def get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def _top_terms(text, category, n=6):
    """Termos presentes no ticket que mais empurraram para a categoria prevista."""
    model = get_model()
    tfidf = model.named_steps["tfidf"]
    clf = model.named_steps["clf"]
    feats = tfidf.get_feature_names_out()
    ci = list(clf.classes_).index(category)
    coef = clf.coef_[ci]
    row = tfidf.transform([text]).tocoo()
    contribs = [(feats[i], v * coef[i]) for i, v in zip(row.col, row.data) if v * coef[i] > 0]
    contribs.sort(key=lambda t: t[1], reverse=True)
    return [t for t, _ in contribs[:n]]


def classify(text, threshold=DEFAULT_THRESHOLD, with_terms=True):
    """Classifica um ticket e decide o roteamento. Retorna dict pronto pra UI ou API."""
    model = get_model()
    proba = model.predict_proba([text])[0]
    classes = model.classes_
    order = proba.argsort()[::-1]
    category = str(classes[order[0]])
    confidence = float(proba[order[0]])
    auto = confidence >= threshold
    return {
        "category": category,
        "confidence": confidence,
        "runner_up": str(classes[order[1]]),
        "runner_up_confidence": float(proba[order[1]]),
        "auto_route": auto,
        "destination": QUEUES.get(category, "Triagem Geral") if auto else "Fila humana (baixa confiança)",
        "top_terms": _top_terms(text, category) if with_terms else [],
    }


def load_samples():
    import pandas as pd
    return pd.read_csv(SAMPLE_PATH)
