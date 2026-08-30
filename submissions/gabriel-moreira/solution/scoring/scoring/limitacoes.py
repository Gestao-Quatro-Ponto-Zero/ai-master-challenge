"""Limitações metodológicas que se aplicam ao score de UMA oportunidade —
e o que cada uma faz com o número dela.

Existe porque as ressalvas do modelo não são iguais para todo negócio: um
Prospecting tem URGÊNCIA fixa, um negócio de 150 dias está fora da janela
observada, um sem conta usa porte neutro. Dizer isso genericamente na
documentação não ajuda quem está olhando um SCORE específico — cada
limitação aqui nomeia o componente que ela move e o que muda no número.

Regras deste módulo:

- **Só o que se aplica.** Uma limitação que não incide sobre esta
  oportunidade não é retornada — uma lista que nunca muda vira decoração
  e o leitor para de ler.
- **Sempre com impacto concreto.** `impacto` diz o que acontece com este
  número, não o que é a limitação em abstrato.
- **Nenhum limiar redigitado.** Tudo vem de `constants.py`, como no resto
  do motor: se a calibração mudar, o texto muda junto.

A única limitação incondicional é `score_nao_e_probabilidade` — ela define
o que o número é, e é justamente a leitura errada mais provável de quem vê
"SCORE 98".
"""

from __future__ import annotations

from dataclasses import dataclass

from . import constants, model

# Chaves canônicas dos componentes exibidos — a interface casa por elas
# para marcar o número afetado, então mudá-las é mudança de contrato.
COMPONENTE_P_HAT = "p_hat"
COMPONENTE_VALOR = "valor"
COMPONENTE_URGENCIA = "urgencia"
COMPONENTE_SCORE = "score"
COMPONENTE_CONFIANCA = "confianca"


@dataclass(frozen=True)
class LimitacaoScore:
    """`rotulo_curto` é o marcador que fica colado ao componente afetado;
    `titulo` e `impacto` são a explicação completa, exibida uma vez."""

    id: str
    componentes: tuple[str, ...]
    rotulo_curto: str
    titulo: str
    impacto: str


def _fmt(valor: float, casas: int = 2) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


_LIMITACAO_SCORE = LimitacaoScore(
    id="score_nao_e_probabilidade",
    componentes=(COMPONENTE_SCORE,),
    rotulo_curto="valor em risco",
    titulo="O SCORE é valor em risco — não a chance de este negócio ser ganho",
    impacto=(
        "É a posição de PRIORIDADE (chance × valor × urgência) contra os negócios "
        "que já foram ganhos: SCORE 90 significa 'vale mais, em risco agora, do que "
        "90% deles'. Nesta base, produto, setor, conta e vendedor não separam ganho "
        "de perda (AUC ≈ 0,50) — então quem atende e o setor da conta não alteram "
        "este número, e ele não deve ser lido como probabilidade de fechamento."
    ),
)


def _limitacao_prospecting() -> LimitacaoScore:
    return LimitacaoScore(
        id="sem_idade",
        componentes=(COMPONENTE_URGENCIA, COMPONENTE_P_HAT),
        rotulo_curto="valor fixo",
        titulo="Sem data de engajamento — a idade deste negócio é desconhecida",
        impacto=(
            f"A idade não é imputada. URGÊNCIA recebe o valor fixo de "
            f"{_fmt(constants.PROSPECTING_URGENCIA)} — o mesmo para toda oportunidade "
            "em Prospecting — e a chance de fechamento fica sem ajuste de tempo. "
            "Consequência prática: entre duas oportunidades do mesmo produto e porte "
            "em Prospecting, o SCORE é idêntico; o que as separa não está no número."
        ),
    )


def _limitacao_censura(age_days: float) -> LimitacaoScore:
    return LimitacaoScore(
        id="acima_da_censura",
        componentes=(COMPONENTE_P_HAT, COMPONENTE_URGENCIA),
        rotulo_curto="fora da janela",
        titulo=(
            f"{round(age_days)} dias em aberto — acima dos {constants.CENSURA_DIAS} "
            "dias já observados"
        ),
        impacto=(
            f"Nenhum negócio fechado nos dados levou mais de {constants.CENSURA_DIAS} "
            "dias, e as curvas não são extrapoladas além do que foi observado. Então "
            f"a chance de fechamento volta à média histórica geral "
            f"({_fmt(constants.CENSURA_P_HAT, 3)}), deixando de refletir este produto, "
            f"e URGÊNCIA cai para o piso de {_fmt(constants.CENSURA_URGENCIA)}. Daqui "
            "para frente o SCORE para de reagir ao envelhecimento."
        ),
    )


def _limitacao_curva_congelada(age_days: float) -> LimitacaoScore:
    return LimitacaoScore(
        id="curva_congelada",
        componentes=(COMPONENTE_P_HAT, COMPONENTE_URGENCIA),
        rotulo_curto="curva congelada",
        titulo=(
            f"{round(age_days)} dias em aberto — acima de "
            f"{constants.CURVA_LIMITE_CONFIAVEL_DIAS} dias, onde a amostra deixa de "
            "sustentar a curva"
        ),
        impacto=(
            f"Chance e urgência param de variar com o tempo: usam os valores "
            f"calibrados em {constants.CURVA_LIMITE_CONFIAVEL_DIAS} dias. Este negócio "
            f"e um de {constants.CENSURA_DIAS} dias recebem exatamente os mesmos dois "
            "números — a diferença de idade entre eles não aparece no SCORE."
        ),
    )


def _limitacao_sem_precedente() -> LimitacaoScore:
    return LimitacaoScore(
        id="sem_precedente",
        componentes=(COMPONENTE_CONFIANCA, COMPONENTE_SCORE),
        rotulo_curto="sem precedente",
        titulo="Nenhum negócio ganho fechou nesta faixa de idade",
        impacto=(
            "O cálculo continua válido, mas sobre uma faixa de idade em que não há "
            "nada observado para se apoiar. Por isso CONFIANÇA fica limitada pelo "
            "suporte histórico e a oportunidade sai da fila ordenada para Revisão em "
            "lote — passivo de higiene de dados, não negócio perdido."
        ),
    )


def _limitacao_porte(has_account: bool) -> LimitacaoScore:
    multiplicadores = constants.MULT_PORTE.values()
    faixa = f"de {_fmt(min(multiplicadores))} a {_fmt(max(multiplicadores))}"
    origem = (
        "Sem conta vinculada"
        if not has_account
        else "A conta vinculada não informa o número de funcionários"
    )
    return LimitacaoScore(
        id="porte_desconhecido",
        componentes=(COMPONENTE_VALOR, COMPONENTE_CONFIANCA),
        rotulo_curto="porte neutro",
        titulo=f"{origem} — o porte da empresa é desconhecido",
        impacto=(
            f"VALOR usa o multiplicador neutro de {_fmt(constants.MULT_PORTE_DESCONHECIDO)} "
            f"no lugar do multiplicador do porte real (que vai {faixa}): é o preço de "
            "tabela puro, sem favorecer nem penalizar. A mesma ausência derruba a "
            "completude do cadastro — uma das duas metades da CONFIANÇA."
        ),
    )


def _limitacao_amostra_produto(product: str, n_fechados: int) -> LimitacaoScore:
    return LimitacaoScore(
        id="amostra_do_produto",
        componentes=(COMPONENTE_P_HAT, COMPONENTE_CONFIANCA),
        rotulo_curto="amostra pequena",
        titulo=(
            f"{product} tem {n_fechados} negócios fechados no histórico — abaixo dos "
            f"{constants.SUPORTE_SATURACAO_N} que sustentam uma taxa própria"
        ),
        impacto=(
            "O encolhimento hierárquico puxa a taxa deste produto com mais força para a "
            "média do catálogo: a chance exibida é menos 'deste produto' e mais 'do "
            "catálogo'. O mesmo tamanho de amostra reduz o suporte histórico que compõe "
            "a CONFIANÇA."
        ),
    )


def limitacoes_do_score(
    ctx: model.ScoringContext,
    *,
    product: str,
    stage: str,
    age_days: float | None,
    has_account: bool,
    porte: str | None,
) -> tuple[LimitacaoScore, ...]:
    """Limitações que efetivamente incidem sobre o score desta oportunidade.

    Ordem: primeiro o que o número é (`score_nao_e_probabilidade`), depois
    o que o afeta, do mais estrutural (idade fora de janela) ao mais
    circunstancial (amostra do produto) — a mesma ordem em que alguém
    perguntaria "posso confiar nisto?".
    """
    limitacoes: list[LimitacaoScore] = [_LIMITACAO_SCORE]

    if stage == "Prospecting":
        limitacoes.append(_limitacao_prospecting())
    elif age_days is not None:
        if age_days > constants.CENSURA_DIAS:
            limitacoes.append(_limitacao_censura(age_days))
        elif age_days > constants.CURVA_LIMITE_CONFIAVEL_DIAS:
            limitacoes.append(_limitacao_curva_congelada(age_days))

    # `sem_precedente` só existe com idade conhecida — em Prospecting a
    # ausência já foi nomeada por `_limitacao_prospecting`.
    if age_days is not None and ctx.s_idade(age_days) == 0.0:
        limitacoes.append(_limitacao_sem_precedente())

    if not has_account or porte is None:
        limitacoes.append(_limitacao_porte(has_account))

    if ctx.s_produto(product) < 1.0:
        limitacoes.append(
            _limitacao_amostra_produto(product, ctx.product_closed_counts.get(product, 0))
        )

    return tuple(limitacoes)
