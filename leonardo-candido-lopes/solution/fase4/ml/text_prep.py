"""Pré-processamento de texto compartilhado (importável para que os .pkl possam ser carregados)."""
import re
from functools import lru_cache
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from nltk.stem import SnowballStemmer

_STEM = SnowballStemmer("english")
_STOP = frozenset(ENGLISH_STOP_WORDS)
_NONALPHA = re.compile(r"[^a-z0-9à-ÿ ]+")


def normalize(text):
    """lowercase + remoção de pontuação + espaços colapsados (sem stemming)."""
    t = str(text).lower().replace("{product_purchased}", " ")
    t = _NONALPHA.sub(" ", t)
    return " ".join(t.split())


@lru_cache(maxsize=200_000)
def _stem(w):
    return _STEM.stem(w)


def preprocess(text):
    """normalize -> remove stopwords (lista sklearn, 318 termos) -> Snowball stemming."""
    return " ".join(_stem(w) for w in normalize(text).split() if w not in _STOP and len(w) > 1)
