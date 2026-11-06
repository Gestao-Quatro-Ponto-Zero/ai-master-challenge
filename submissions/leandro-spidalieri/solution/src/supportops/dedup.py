"""Agrupamento pré-split por equivalência e quase duplicação lexical."""

import math
from collections import Counter, defaultdict


def near_groups(keys: list[str], similarity: float = 0.85) -> list[int]:
    """Componentes conexos de Jaccard de trigramas de palavras.

    Prefixos pela mesma ordem global descartam pares sem interseção suficiente.
    Textos com menos de três tokens usam apenas equivalência exata.
    """
    shingles = []
    for key in keys:
        tokens = key.split()
        shingles.append(set(zip(tokens, tokens[1:], tokens[2:])))
    rarity = Counter(shingle for signature in shingles for shingle in signature)
    parents = list(range(len(keys)))
    index = defaultdict(list)
    exact = {}

    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    def link(i, j):
        a, b = sorted((root(i), root(j)))
        parents[b] = a

    for i, signature in enumerate(shingles):
        if keys[i] in exact:
            link(i, exact[keys[i]])
            continue
        exact[keys[i]] = i
        n = len(signature)
        if not n:
            continue
        prefix = sorted(signature, key=lambda shingle: (rarity[shingle], shingle))[
            : n - math.ceil(n * similarity) + 1
        ]
        candidates = {j for shingle in prefix for j in index[shingle]}
        for j in candidates:
            m = len(shingles[j])
            if min(n, m) < similarity * max(n, m) or root(i) == root(j):
                continue
            common = len(signature & shingles[j])
            if common / (n + m - common) >= similarity:
                link(i, j)
        for shingle in prefix:
            index[shingle].append(i)
    return [root(i) for i in range(len(keys))]
