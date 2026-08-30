"""Correção para múltiplas comparações sobre a suíte de permutação.

Seis testes de permutação rodam nesta suíte — quatro na seção 2
(vendedor, produto, setor, conta) e dois na seção 12 (vendedor×produto,
vendedor×setor). Reportar seis p-valores contra o corte de 0,05 sem
correção infla a chance de pelo menos um falso positivo de 5% para
1-(1-0,05)^6 ≈ 26%. Duas correções, porque respondem a perguntas
diferentes:

- **Holm** controla a taxa de erro por FAMÍLIA (FWER): a chance de
  cometer QUALQUER falso positivo entre os seis. É o corte conservador,
  apropriado quando uma única afirmação errada já compromete a
  conclusão — o caso aqui, já que a tese do produto é "não há sinal".
- **Benjamini-Hochberg** controla a proporção esperada de falsos
  positivos ENTRE OS REJEITADOS (FDR). É o corte que se usa quando se
  quer uma lista de candidatos a investigar, não uma afirmação isolada.

O que NÃO é multiplicidade: as 178 células vendedor×produto da seção 12.
A dispersão é uma estatística omnibus — um único teste que agrega todas
as células —, então não há 178 comparações a corrigir. Confundir as duas
coisas foi um erro de redação desta suíte, corrigido em 2026-08-29.

Por que 6 entradas e não 8: a seção 12 roda dois nulos por dimensão
(global e aditivo), e entra na família o p do nulo GLOBAL — o MENOR dos
dois. As duas escolhas são deliberadamente desfavoráveis à tese deste
trabalho ("não há sinal"): quanto mais testes na família, mais apertados
ficam os cortes de Holm e B-H e mais fácil fica NÃO rejeitar, e o p mais
baixo é o que teria mais chance de sobreviver ao corte. Família curta e p
mínimo é o arranjo em que a tese correria o maior risco de cair — é por
isso que é ele que roda.
"""

from __future__ import annotations

from dataclasses import dataclass

ALFA = 0.05


@dataclass(frozen=True)
class TesteCorrigido:
    nome: str
    origem: str
    p_valor: float
    limite_holm: float
    rejeita_holm: bool
    limite_bh: float
    rejeita_bh: bool


def corrigir(testes: list[tuple[str, str, float]], alfa: float = ALFA) -> list[TesteCorrigido]:
    """`testes` = [(nome, origem, p_valor)]. Devolve ordenado por p."""
    ordenados = sorted(testes, key=lambda t: t[2])
    m = len(ordenados)

    # Holm: compara p_(i) com alfa/(m-i); para na primeira falha e nada
    # depois dela é rejeitado (o passo que a aplicação ingênua esquece).
    rejeita_holm = []
    ainda_rejeitando = True
    for i, (_, _, p) in enumerate(ordenados):
        limite = alfa / (m - i)
        ainda_rejeitando = ainda_rejeitando and p <= limite
        rejeita_holm.append(ainda_rejeitando)

    # Benjamini-Hochberg: o maior i com p_(i) <= (i/m)·alfa rejeita tudo
    # até i — inclusive um p que sozinho não passaria do próprio limite.
    maior_i = 0
    for i, (_, _, p) in enumerate(ordenados, start=1):
        if p <= (i / m) * alfa:
            maior_i = i

    return [
        TesteCorrigido(
            nome=nome,
            origem=origem,
            p_valor=p,
            limite_holm=alfa / (m - i),
            rejeita_holm=rejeita_holm[i],
            limite_bh=((i + 1) / m) * alfa,
            rejeita_bh=(i + 1) <= maior_i,
        )
        for i, (nome, origem, p) in enumerate(ordenados)
    ]
