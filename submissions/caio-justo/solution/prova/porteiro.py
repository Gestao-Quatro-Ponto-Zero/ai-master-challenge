"""Porteiro de fatores: um critério só entra na nota se prever o mês seguinte.

Em cada mês, as taxas de vitória vêm só do que encerrou antes. A comparação é
feita dentro do mês, porque a taxa de vitória muda demais entre os meses (49% a
83%) e misturar meses produz um resultado falso.
"""
import random
from collections import defaultdict
from datetime import date

from .estatistica import auc

LIMIAR_PORTEIRO = 0.53
SUAVIZACAO = 20

FATORES = {
    "vendedor": lambda n: n.vendedor,
    "produto": lambda n: n.produto,
    "setor": lambda n: n.setor,
    "região": lambda n: n.regiao,
    "manager": lambda n: n.manager,
    "porte da conta": lambda n: _porte(n.receita),
    "conta": lambda n: n.conta,
}


def _porte(receita) -> str:
    if receita is None:
        return "sem dado"
    for corte, nome in ((100, "até 100M"), (1000, "até 1B"), (5000, "até 5B")):
        if receita <= corte:
            return nome
    return "acima de 5B"


def _inicio_meses():
    return [date(2017, mes, 1) for mes in range(6, 13)]


def _proximo_mes(dia: date) -> date:
    return date(dia.year + (dia.month == 12), dia.month % 12 + 1, 1)


def dobras(fechados, fator, rotulo=None) -> list:
    """Uma lista (rótulos, notas) por mês, sem olhar para o futuro."""
    ganho = rotulo or (lambda n: n.ganho)
    ordenados = sorted(fechados, key=lambda n: n.fim)
    resultado = []
    for inicio in _inicio_meses():
        fim = _proximo_mes(inicio)
        treino = [n for n in ordenados if n.fim < inicio]
        teste = [n for n in ordenados if inicio <= n.fim < fim]
        media = sum(1 for n in treino if ganho(n)) / len(treino)
        vitorias, totais = defaultdict(int), defaultdict(int)
        for negocio in treino:
            chave = fator(negocio)
            totais[chave] += 1
            vitorias[chave] += 1 if ganho(negocio) else 0
        taxa = lambda chave: (vitorias[chave] + SUAVIZACAO * media) / (totais[chave] + SUAVIZACAO)
        resultado.append(([ganho(n) for n in teste], [taxa(fator(n)) for n in teste]))
    return resultado


def auc_mes_a_mes(listas) -> float:
    soma, peso = 0.0, 0
    for rotulos, notas in listas:
        if len(set(rotulos)) < 2 or len(set(notas)) < 2:
            continue
        soma += auc(rotulos, notas) * len(rotulos)
        peso += len(rotulos)
    return soma / peso if peso else 0.5


def intervalo(listas, repeticoes: int, gerador: random.Random) -> tuple:
    estimativas = []
    for _ in range(repeticoes):
        amostra = []
        for rotulos, notas in listas:
            indices = [gerador.randrange(len(rotulos)) for _ in rotulos]
            amostra.append(([rotulos[i] for i in indices], [notas[i] for i in indices]))
        estimativas.append(auc_mes_a_mes(amostra))
    estimativas.sort()
    return (
        estimativas[int(0.025 * repeticoes)],
        estimativas[min(repeticoes - 1, int(0.975 * repeticoes))],
    )


def avaliar(fechados, fator, repeticoes: int, gerador: random.Random, rotulo=None) -> dict:
    listas = dobras(fechados, fator, rotulo)
    baixo, alto = intervalo(listas, repeticoes, gerador)
    return {
        "auc": auc_mes_a_mes(listas),
        "baixo": baixo,
        "alto": alto,
        "aberto": baixo > LIMIAR_PORTEIRO,
    }
