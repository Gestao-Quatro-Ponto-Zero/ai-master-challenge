"""Os dois sorteios da ferramenta. A semente fixa torna os dois auditáveis."""
import random
from collections import defaultdict

SEMENTE_CHECAGEM = "checagem-2017-12-31"
SEMENTE_DESTAQUE = "destaque-2017-12-31"
TAMANHO_CHECAGEM = 100
MINIMO_POR_PRODUTO = 2


def alocar_por_produto(parados, total: int = TAMANHO_CHECAGEM) -> dict:
    """Quantos negócios sortear por produto: proporcional ao valor, com um mínimo.

    O que se quer estimar é o valor real, então os produtos que concentram valor
    recebem mais amostra (alocação de Neyman, 1934). Sortear por quantidade deixava
    só 2 dos 14 GTK 500, que valem 12% do total, e a margem errava mais que o prometido.
    """
    quantidade = defaultdict(int)
    valor = defaultdict(int)
    for negocio in parados:
        quantidade[negocio.produto] += 1
        valor[negocio.produto] += negocio.preco
    if len(parados) <= total:
        return dict(quantidade)
    soma = sum(valor.values())
    ideal = {p: total * valor[p] / soma for p in valor}
    alocacao = {p: min(quantidade[p], max(MINIMO_POR_PRODUTO, int(ideal[p]))) for p in valor}
    por_resto = sorted(valor, key=lambda p: ideal[p] - int(ideal[p]), reverse=True)
    while sum(alocacao.values()) < total:
        for produto in por_resto:
            if sum(alocacao.values()) == total:
                break
            if alocacao[produto] < quantidade[produto]:
                alocacao[produto] += 1
    while sum(alocacao.values()) > total:
        maior = max(alocacao, key=lambda p: alocacao[p] if alocacao[p] > MINIMO_POR_PRODUTO else -1)
        alocacao[maior] -= 1
    return alocacao


def sortear_checagem(parados, semente: str = SEMENTE_CHECAGEM) -> set:
    """Sorteia os negócios parados que os vendedores vão confirmar."""
    gerador = random.Random(semente)
    grupos = defaultdict(list)
    for negocio in sorted(parados, key=lambda n: n.id):
        grupos[negocio.produto].append(negocio)
    escolhidos = set()
    for produto, quantidade in sorted(alocar_por_produto(parados).items()):
        escolhidos.update(n.id for n in gerador.sample(grupos[produto], quantidade))
    return escolhidos


def sortear_destaque(ativos, notas: dict, semente: str = SEMENTE_DESTAQUE) -> dict:
    """Decide, dentro de cada vendedor, quais negócios recebem destaque.

    Os negócios são pareados por nota e o sorteio escolhe um de cada par. Assim
    os dois grupos ficam parecidos em preço e idade, e cada vendedor tem os dois.
    """
    gerador = random.Random(semente)
    por_vendedor = defaultdict(list)
    for negocio in sorted(ativos, key=lambda n: n.id):
        por_vendedor[negocio.vendedor].append(negocio)
    grupos = {}
    for vendedor in sorted(por_vendedor):
        lista = sorted(por_vendedor[vendedor], key=lambda n: (-notas[n.id], n.id))
        for i in range(0, len(lista), 2):
            par = lista[i : i + 2]
            if len(par) == 1:
                grupos[par[0].id] = gerador.choice(["destaque", "controle"])
                continue
            primeiro, segundo = gerador.sample(par, 2)
            grupos[primeiro.id] = "destaque"
            grupos[segundo.id] = "controle"
    return grupos
