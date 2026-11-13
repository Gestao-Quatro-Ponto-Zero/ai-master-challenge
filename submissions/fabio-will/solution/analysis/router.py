"""Ticket router building blocks shared by the lab, the stress tests and the app export."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from common import SEED, load_it_tickets

AUTO_PRECISION = 0.95       # auto-route only where validation precision is at least this
ASSIST_TOP2_ACCURACY = 0.90  # suggest top-2 to the agent where the right queue is in it this often
OOD_PERCENTILE = 2.0         # novelty guard: reject below this percentile of in-domain similarity
COHERENCE_PERCENTILE = 2.0   # word-order guard: reject below this percentile of known word pairs (catches interleaved padding)
VOCAB_FLOOR = 0.55           # vocabulary guard: Portuguese probes peak at 0.50; 90% of 5%-typo text stays above 0.63
SENSITIVE_MASS = 0.05        # probability mass on sensitive queues that blocks auto-routing elsewhere (see E3 trade-off)
PSI_ALARM = 0.25             # population stability index that pauses auto-routing (common rule of thumb)
SEGMENT_WORDS = 8            # segment guard: window size in words, stride half a window (see 05_adversarial.py)
SEGMENT_SENSITIVE = 0.70     # a window this confident in a sensitive queue blocks auto-routing elsewhere (chosen on validation)
NEVER_AUTO = ("Administrative rights",)   # privileged access: a human always confirms the queue
SENSITIVE = ("Administrative rights", "HR Support")


@dataclass
class Split:
    X_train: np.ndarray
    X_val: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_val: np.ndarray
    y_test: np.ndarray


def make_split() -> Split:
    df = load_it_tickets()
    X, y = df["Document"].values, df["Topic_group"].values
    X_train, X_tmp, y_train, y_tmp = train_test_split(X, y, test_size=0.30, stratify=y, random_state=SEED)
    X_val, X_test, y_val, y_test = train_test_split(X_tmp, y_tmp, test_size=0.50, stratify=y_tmp, random_state=SEED)
    return Split(X_train, X_val, X_test, y_train, y_val, y_test)


def word_tfidf(max_features: int | None = 10000) -> TfidfVectorizer:
    return TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=max_features, sublinear_tf=True)


def build_router(max_features: int = 10000) -> Pipeline:
    """Logistic regression on word 1-2 grams: best calibration and portable to the browser."""
    return Pipeline([("tfidf", word_tfidf(max_features)), ("clf", LogisticRegression(C=8, max_iter=2000))])


def expected_calibration_error(conf: np.ndarray, correct: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            ece += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(ece)


def gate_curve(conf: np.ndarray, correct: np.ndarray) -> list[dict]:
    rows = []
    for t in np.round(np.arange(0.30, 0.995, 0.01), 2):
        m = conf >= t
        rows.append({"t": float(t), "coverage": float(m.mean()), "precision": float(correct[m].mean()) if m.any() else 1.0})
    return rows


def pick_threshold(curve: list[dict], target: float) -> float:
    for row in curve:
        if row["precision"] >= target:
            return row["t"]
    return 0.99


def top2_hit(proba: np.ndarray, classes: np.ndarray, y: np.ndarray) -> np.ndarray:
    top2 = np.argsort(-proba, axis=1)[:, :2]
    return (classes[top2] == y[:, None]).any(axis=1)


def pick_assist_floor(conf: np.ndarray, hit2: np.ndarray, t_auto: float) -> float:
    """Lowest threshold t such that tickets in [t, t_auto) have the right queue in the top-2 often enough."""
    best = t_auto
    for t in np.round(np.arange(t_auto - 0.01, 0.0, -0.01), 2):
        band = (conf >= t) & (conf < t_auto)
        if band.any() and hit2[band].mean() >= ASSIST_TOP2_ACCURACY:
            best = float(t)
        else:
            break
    return best


def max_similarity(pipe: Pipeline, train_matrix: sparse.csr_matrix, texts, chunk: int = 2000) -> np.ndarray:
    """Cosine similarity to the closest training ticket (TF-IDF rows are L2-normalised)."""
    out = []
    for i in range(0, len(texts), chunk):
        q = pipe.named_steps["tfidf"].transform(texts[i:i + chunk])
        sims = q @ train_matrix.T
        out.append(np.asarray(sims.max(axis=1).todense()).ravel())
    return np.concatenate(out)


def vocabulary_coverage(pipe: Pipeline, texts) -> np.ndarray:
    """Share of a ticket's tokens that the router has seen in training (catches other languages)."""
    vec = pipe.named_steps["tfidf"]
    analyzer = vec.build_tokenizer()
    vocab = vec.vocabulary_
    out = []
    for t in texts:
        toks = analyzer(t.lower())
        out.append(sum(tok in vocab for tok in toks) / len(toks) if toks else 0.0)
    return np.array(out)


@dataclass
class Policy:
    t_auto: float
    t_assist: float
    t_ood: float
    c_min: float
    t_coherence: float
    classes: np.ndarray

    def decide(
        self, proba: np.ndarray, sim: np.ndarray, coverage: np.ndarray, segment: np.ndarray, coherence: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Returns (tier, reason) per ticket. Order matters: the first rule that fires wins.

        segment is segment_sensitivity(): the strongest sensitive-queue probability over any short window of the
        ticket. Padding a ticket with off-topic words dilutes the whole-ticket probabilities, not the windows.
        coherence is word_pair_coherence(): interleaving padding between every word defeats the windows, but it
        also destroys the word pairs the router knows, which real tickets keep.
        """
        conf = proba.max(1)
        pred = self.classes[proba.argmax(1)]
        sens_idx = [i for i, c in enumerate(self.classes) if c in SENSITIVE]
        sens_mass = proba[:, sens_idx].sum(1)
        tier = np.full(len(conf), "human", dtype=object)
        reason = np.full(len(conf), "confianca_baixa", dtype=object)
        rules = [
            (coverage < self.c_min, "human", "vocabulario_desconhecido"),
            (sim < self.t_ood, "human", "sem_historico_parecido"),
            (coherence < self.t_coherence, "human", "sequencia_incomum"),
            (np.isin(pred, NEVER_AUTO) & (conf >= self.t_assist), "assist", "fila_privilegiada"),
            (~np.isin(pred, SENSITIVE) & (sens_mass >= SENSITIVE_MASS) & (conf >= self.t_assist), "assist", "possivel_conteudo_sensivel"),
            (~np.isin(pred, SENSITIVE) & (segment >= SEGMENT_SENSITIVE) & (conf >= self.t_assist), "assist", "trecho_sensivel"),
            (conf >= self.t_auto, "auto", "confianca_alta"),
            (conf >= self.t_assist, "assist", "confianca_media"),
        ]
        decided = np.zeros(len(conf), dtype=bool)
        for mask, t, r in rules:
            m = mask & ~decided
            tier[m] = t
            reason[m] = r
            decided |= m
        return tier.astype(str), reason.astype(str)


def word_pair_coherence(pipe: Pipeline, texts) -> np.ndarray:
    """Share of a ticket's adjacent token pairs that are bigrams in the router vocabulary. One token or none: 1.0."""
    vec = pipe.named_steps["tfidf"]
    analyzer = vec.build_tokenizer()
    vocab = vec.vocabulary_
    out = []
    for t in texts:
        toks = analyzer(str(t).lower())
        pairs = [f"{a} {b}" for a, b in zip(toks, toks[1:])]
        out.append(sum(p in vocab for p in pairs) / len(pairs) if pairs else 1.0)
    return np.array(out)


def segment_windows(text: str, words: int = SEGMENT_WORDS) -> list[str]:
    """Overlapping word windows (stride half a window). Short tickets are a single window. Mirrored in app/src/lib/router.ts."""
    tokens = text.split()
    if len(tokens) <= words:
        return [text]
    step = max(1, words // 2)
    return [" ".join(tokens[i : i + words]) for i in range(0, len(tokens) - words + step, step)]


def segment_sensitivity(pipe: Pipeline, texts, words: int = SEGMENT_WORDS) -> np.ndarray:
    """Per ticket, the highest probability any single window gives to a single sensitive queue."""
    windows, owner = [], []
    for i, text in enumerate(texts):
        for w in segment_windows(str(text), words):
            windows.append(w)
            owner.append(i)
    classes = pipe.classes_
    proba = pipe.predict_proba(windows)[:, np.isin(classes, SENSITIVE)].max(1)
    out = np.zeros(len(texts))
    np.maximum.at(out, np.asarray(owner), proba)
    return out


def psi(expected: np.ndarray, observed_counts: np.ndarray) -> float:
    """Population stability index of observed category counts against expected shares.
    Add-one smoothing keeps an empty category in a small window from firing a false alarm."""
    o = (observed_counts + 1) / (observed_counts.sum() + len(observed_counts))
    e = np.clip(expected, 1e-6, None)
    return float(np.sum((o - e) * np.log(o / e)))


def fit_router_and_policy(sp: Split) -> tuple[Pipeline, Policy, sparse.csr_matrix]:
    """Trains the router on the train split and picks every threshold on validation only."""
    pipe = build_router().fit(sp.X_train, sp.y_train)
    classes = pipe.classes_
    train_matrix = pipe.named_steps["tfidf"].transform(sp.X_train)
    val_proba = pipe.predict_proba(sp.X_val)
    val_conf = val_proba.max(1)
    val_correct = classes[val_proba.argmax(1)] == sp.y_val
    t_auto = pick_threshold(gate_curve(val_conf, val_correct), AUTO_PRECISION)
    t_assist = pick_assist_floor(val_conf, top2_hit(val_proba, classes, sp.y_val), t_auto)
    t_ood = float(np.percentile(max_similarity(pipe, train_matrix, sp.X_val), OOD_PERCENTILE))
    t_coherence = float(np.percentile(word_pair_coherence(pipe, sp.X_val), COHERENCE_PERCENTILE))
    policy = Policy(t_auto=t_auto, t_assist=t_assist, t_ood=t_ood, c_min=VOCAB_FLOOR, t_coherence=t_coherence, classes=classes)
    return pipe, policy, train_matrix
