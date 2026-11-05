"""Estatística usada pela ferramenta, escrita à mão para não exigir dependências."""
import math
import random

Z95 = 1.959964
Z80 = 0.841621


def wilson(sucessos: int, total: int, z: float = Z95) -> tuple:
    """Intervalo de Wilson (1927) para uma proporção."""
    if total == 0:
        return (0.0, 1.0)
    p = sucessos / total
    denominador = 1 + z * z / total
    centro = (p + z * z / (2 * total)) / denominador
    margem = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominador
    return (max(0.0, centro - margem), min(1.0, centro + margem))


def diferenca_newcombe(a: int, n_a: int, b: int, n_b: int) -> tuple:
    """Diferença entre proporções (a - b) com o intervalo de Newcombe (1998), método 10."""
    if n_a == 0 or n_b == 0:
        return (0.0, -1.0, 1.0)
    p_a, p_b = a / n_a, b / n_b
    l_a, u_a = wilson(a, n_a)
    l_b, u_b = wilson(b, n_b)
    d = p_a - p_b
    baixo = d - math.sqrt((p_a - l_a) ** 2 + (u_b - p_b) ** 2)
    alto = d + math.sqrt((u_a - p_a) ** 2 + (p_b - l_b) ** 2)
    return (d, baixo, alto)


def tamanho_por_braco(base: float, efeito: float) -> int:
    """Negócios por grupo para detectar `efeito` com 95% de confiança e 80% de poder."""
    tratado = base + efeito
    termo = base * (1 - base) + tratado * (1 - tratado)
    return math.ceil((Z95 + Z80) ** 2 * termo / (efeito * efeito))


def auc(rotulos: list, notas: list) -> float:
    """AUC pela soma de postos, com empates pela média (Hanley e McNeil, 1982)."""
    pares = sorted(zip(notas, rotulos))
    positivos = sum(1 for r in rotulos if r)
    negativos = len(rotulos) - positivos
    if positivos == 0 or negativos == 0:
        return 0.5
    soma = 0.0
    i = 0
    while i < len(pares):
        j = i
        while j + 1 < len(pares) and pares[j + 1][0] == pares[i][0]:
            j += 1
        posto = (i + j) / 2 + 1
        soma += posto * sum(1 for k in range(i, j + 1) if pares[k][1])
        i = j + 1
    return (soma - positivos * (positivos + 1) / 2) / (positivos * negativos)


def estimativa_estratificada(estratos: list) -> dict:
    """Parcela do valor que segue real, estimada por estrato (Neyman, 1934).

    Cada estrato traz: valor total, tamanho N, respostas n e respostas positivas s.
    Estratos sem resposta ficam de fora e o resultado diz quanto valor cobriu.
    """
    valor_total = sum(e["valor"] for e in estratos)
    cobertos = [e for e in estratos if e["n"] > 0]
    valor_coberto = sum(e["valor"] for e in cobertos)
    if not cobertos or valor_coberto == 0:
        return {"parcela": None, "baixo": None, "alto": None, "cobertura": 0.0}
    estimado = 0.0
    variancia = 0.0
    for e in cobertos:
        # Suavização de Agresti-Coull: evita variância zero em estratos pequenos.
        n_ajustado = e["n"] + 2
        p_ajustado = (e["s"] + 1) / n_ajustado
        p = e["s"] / e["n"]
        peso = e["valor"] / valor_coberto
        correcao = max(0.0, 1 - e["n"] / e["N"]) if e["N"] else 0.0
        estimado += peso * p
        variancia += peso * peso * correcao * p_ajustado * (1 - p_ajustado) / n_ajustado
    margem = Z95 * math.sqrt(variancia)
    return {
        "parcela": estimado,
        "baixo": max(0.0, estimado - margem),
        "alto": min(1.0, estimado + margem),
        "cobertura": valor_coberto / valor_total if valor_total else 0.0,
    }


def teste_sinal(positivos: int, negativos: int) -> float:
    """Valor-p bilateral exato do teste do sinal; empates não entram."""
    n = positivos + negativos
    if n == 0:
        return 1.0
    menor = min(positivos, negativos)
    cauda = sum(math.comb(n, k) for k in range(menor + 1)) / 2 ** n
    return min(1.0, 2 * cauda)


def reamostrar(valores: list, gerador: random.Random) -> list:
    return [valores[gerador.randrange(len(valores))] for _ in valores]
