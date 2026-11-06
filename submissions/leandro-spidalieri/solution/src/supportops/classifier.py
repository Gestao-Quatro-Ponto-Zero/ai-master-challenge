"""Treino, seleção de política e inferência do classificador de TI."""

import hashlib
import math
import platform
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from .dedup import near_groups
from .ingest import IT, ROOT, digest, read_json
from .policy import (
    DOMAIN_IT,
    MAX_CHARS,
    MIN_TOKENS,
    WORDS,
    decide,
    input_reasons,
    model_reasons,
)
from .quality import strip_identifiers, text_profile

SEED = 241
MIN_ACCEPTED = 100
MIN_WILSON = 0.90
GRID = tuple(i / 20 for i in range(21))
TOKEN = re.compile(r"\w+", re.UNICODE)
HEADER = re.compile(r"(?im)(?:^|[\n;])\s*(?:category|topic.group|assignment group|assigned to)\s*:")
ENGLISH_MARKERS = re.compile(r"\b(?:the|and|please|with|this|need|my|for|can|have|not)\b", re.I)
PORTUGUESE_MARKERS = re.compile(r"\b(?:com|para|obrigado|senha|não|estou|preciso)\b", re.I)
MODEL_FILES = ("classifier.py", "dedup.py", "policy.py", "quality.py")


def normalize(text: str) -> str:
    return " ".join(
        TOKEN.findall(unicodedata.normalize("NFKC", strip_identifiers(text)).casefold())
    )


def prepare(raw: pd.DataFrame, source_sha: str):
    rows = raw[["Document", "Topic_group"]].fillna("").copy()
    rows["Document"] = rows["Document"].str.strip()
    rows["Topic_group"] = rows["Topic_group"].str.strip()
    rows["id"] = [
        digest(f"{source_sha}:{ordinal}".encode())[:20] for ordinal in range(1, len(rows) + 1)
    ]
    rows["key"] = rows["Document"].map(normalize)
    invalid = {
        "texto_insuficiente_ou_vazio": rows["Document"].map(
            lambda s: len(WORDS.findall(s)) < MIN_TOKENS
        ),
        "texto_longo": rows["Document"].str.len().gt(MAX_CHARS),
        "rotulo_ausente": rows["Topic_group"].eq(""),
    }
    excluded = {}
    remaining = pd.Series(True, index=rows.index)
    for name, flags in invalid.items():
        excluded[name] = int((flags & remaining).sum())
        remaining &= ~flags
    clean = rows.loc[remaining].copy()
    conflict = clean.groupby("key")["Topic_group"].transform("nunique").gt(1)
    excluded["chave_exata_com_rotulo_conflitante"] = int(conflict.sum())
    clean = clean.loc[~conflict].reset_index(drop=True)
    if clean.empty:
        raise ValueError("Nenhum ticket de TI elegível após a auditoria.")
    groups = near_groups(clean["key"].tolist())
    clean["group"] = [clean.at[i, "id"] for i in groups]
    exact_excess = int(clean["key"].duplicated().sum())
    mixed_near = clean.groupby("group")["Topic_group"].nunique().gt(1)
    label_literals = sum(
        bool(re.search(r"(?<!\w)" + re.escape(label) + r"(?!\w)", text, re.I))
        for text, label in zip(rows["Document"], rows["Topic_group"], strict=True)
        if label
    )
    audit = {
        "linhas_originais": len(raw),
        "linhas_utilizaveis": len(clean),
        "exclusoes": excluded,
        "classes_raw": dict(Counter(rows["Topic_group"])),
        "classes_utilizaveis": dict(Counter(clean["Topic_group"])),
        "duplicatas_de_linha_raw_excedentes": int(raw.duplicated().sum()),
        "texto": text_profile(rows["Document"]),
        "sinais_idioma": {
            "marcador_ingles": int(rows["Document"].str.contains(ENGLISH_MARKERS).sum()),
            "marcador_portugues": int(rows["Document"].str.contains(PORTUGUESE_MARKERS).sum()),
            "metodo": "Presença de termos comuns, com sobreposição. Não certifica idioma por linha.",
        },
        "grupos": int(clean["group"].nunique()),
        "maior_grupo": int(clean["group"].value_counts().max()),
        "duplicatas_normalizadas_excedentes_retidas_no_grupo": exact_excess,
        "unioes_adicionais_por_quase_duplicacao": int(
            clean["key"].nunique() - clean["group"].nunique()
        ),
        "grupos_aproximados_com_rotulos_distintos": int(mixed_near.sum()),
        "texto_com_rotulo_literal": label_literals,
        "texto_com_cabecalho_de_roteamento": int(rows["Document"].str.contains(HEADER).sum()),
    }
    return clean, audit


def split(clean: pd.DataFrame) -> pd.DataFrame:
    labels = clean["Topic_group"]
    if labels.nunique() < 2 or clean.groupby("Topic_group")["group"].nunique().min() < 7:
        raise ValueError("São necessárias duas classes e pelo menos sete grupos por classe.")
    splitter = StratifiedGroupKFold(n_splits=7, shuffle=True, random_state=SEED)
    parts = clean[["id", "group", "Topic_group"]].copy()
    parts["particao"] = "treino"
    for fold, (_, selection) in enumerate(splitter.split(clean, labels, groups=clean["group"])):
        if fold >= 2:
            break
        parts.iloc[selection, parts.columns.get_loc("particao")] = ("teste", "validacao")[fold]
    if (parts.groupby("group")["particao"].nunique() != 1).any():
        raise ValueError("Vazamento entre grupos do split.")
    if not parts.groupby("particao")["Topic_group"].nunique().eq(labels.nunique()).all():
        raise ValueError("Classe ausente em uma partição.")
    return parts


def fit(train: pd.DataFrame) -> Pipeline:
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2), min_df=2, max_features=65_000, sublinear_tf=True
                ),
            ),
            ("logit", LogisticRegression(C=4, max_iter=300, random_state=SEED)),
        ]
    )
    with threadpool_limits(limits=2):
        return pipeline.fit(train["key"], train["Topic_group"])


def wilson(successes: int, total: int):
    if not total:
        return None
    z = 1.96
    p = successes / total
    denom = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denom
    return [max(0.0, center - half), min(1.0, center + half)]


def coverage(rows: pd.DataFrame, threshold: float) -> dict:
    accepted = rows["apto"] & rows["score"].ge(threshold)
    n = int(accepted.sum())
    correct = int((accepted & rows["previsto"].eq(rows["real"])).sum())
    return {
        "n": len(rows),
        "aceitos": n,
        "acertos_aceitos": correct,
        "revisao": len(rows) - n,
        "cobertura": n / len(rows) if len(rows) else None,
        "acerto_nos_aceitos": correct / n if n else None,
        "ic95_wilson_acerto": wilson(correct, n),
    }


def select_threshold(validation: pd.DataFrame):
    curve = [{"limiar": t, **coverage(validation, t)} for t in GRID]
    viable = [
        r
        for r in curve
        if r["aceitos"] >= MIN_ACCEPTED and r["ic95_wilson_acerto"][0] >= MIN_WILSON
    ]
    if not viable:
        return 1.01, curve
    best = max(viable, key=lambda row: (row["aceitos"], row["acertos_aceitos"], -row["limiar"]))
    return best["limiar"], curve


def lexical_overlap(pipeline, key: str):
    vec = pipeline.named_steps["tfidf"]
    tokens = set(vec.build_tokenizer()(key))
    known = sum(token in vec.vocabulary_ for token in tokens)
    return known / len(tokens) if tokens else 0.0, known


def score_rows(pipeline, frame: pd.DataFrame) -> pd.DataFrame:
    probabilities = pipeline.predict_proba(frame["key"])
    winners = probabilities.argmax(axis=1)
    labels = pipeline.classes_[winners]
    reasons = []
    for text, key, label in zip(frame["Document"], frame["key"], labels, strict=True):
        overlap, known = lexical_overlap(pipeline, key)
        reasons.append(input_reasons(text, DOMAIN_IT, "") + model_reasons(label, overlap, known))
    return pd.DataFrame(
        {
            "id": frame["id"].to_numpy(),
            "group": frame["group"].to_numpy(),
            "real": frame["Topic_group"].to_numpy(),
            "previsto": labels,
            "score": probabilities.max(axis=1),
            "apto": [not row for row in reasons],
            "guardas": [" | ".join(row) for row in reasons],
        }
    )


def provenance(source_sha: str) -> dict:
    module = Path(__file__).parent
    checksum = hashlib.sha256()
    for name in MODEL_FILES:
        checksum.update(name.encode())
        checksum.update((module / name).read_bytes())
    checksum.update((ROOT / "requirements.lock").read_bytes())
    return {
        "dataset_sha256": source_sha,
        "codigo_e_lock_sha256": checksum.hexdigest(),
        "seed": SEED,
        "python": platform.python_version(),
        "sklearn": sklearn.__version__,
        "numpy": np.__version__,
    }


def classify(pipeline, meta: dict, text: str, domain: str, priority: str, row_id=None):
    start = time.perf_counter()
    reasons = input_reasons(text, domain, priority)
    category = score = None
    if not reasons:
        key = normalize(text)
        probs = pipeline.predict_proba([key])[0]
        winner = int(probs.argmax())
        category, score = str(pipeline.classes_[winner]), float(probs[winner])
        reasons += model_reasons(category, *lexical_overlap(pipeline, key))
    decision, reasons = decide(reasons, score, meta["limiar"])
    return {
        "id": row_id or digest((meta["modelo_versao"] + text[:MAX_CHARS]).encode())[:16],
        "dominio": domain,
        "prioridade_informada": priority,
        "categoria_prevista": category,
        "score": score,
        "tipo_score": "score do modelo não calibrado",
        "decisao": decision,
        "motivos": reasons,
        "versao_modelo": meta["modelo_versao"],
        "latencia_ms": (time.perf_counter() - start) * 1000,
    }


def load_local(folder: Path):
    """Só usado com a pasta de execução local fixa, jamais com uploads."""
    meta = read_json(folder / "model.json")
    binary = folder / "model.joblib"
    if provenance(IT.sha256) != meta["proveniencia"]:
        raise ValueError(
            "Modelo de outro snapshot, código ou ambiente. Execute o pipeline novamente."
        )
    if digest(binary.read_bytes()) != meta["binario_sha256"]:
        raise ValueError("Integridade do modelo local inválida.")
    return joblib.load(binary), meta
