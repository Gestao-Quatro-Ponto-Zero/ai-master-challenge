"""Atribuição de CONFIANÇA — quanto do score está apoiado em dado observado
e em precedente histórico. CONFIANÇA = min(completude, suporte): a metade
mais fraca governa, porque conhecer todos os campos de uma oportunidade sem
precedente histórico não a torna confiável (design.md, decisão "min em vez
de média").

Independente de PRIORIDADE/SCORE. Não considera idade como regra própria —
idade só entra através da densidade de precedente em `suporte`.
"""

from __future__ import annotations

from . import constants, model

_CAMPOS_COMPLETUDE = 5


def completude(
    stage: str,
    has_account: bool,
    has_employees: bool,
    has_sector: bool,
    has_team: bool,
) -> tuple[float, list[str]]:
    """Fração (0-100) dos cinco campos de cadastro observados, e a lista
    dos campos ausentes (para a razão de CONFIANÇA e o plano de ação)."""
    campos = [
        (stage == "Engaging", "engajamento"),
        (has_account, "conta"),
        (has_employees, "funcionários"),
        (has_sector, "setor"),
        (has_team, "time"),
    ]
    ausentes = [nome for presente, nome in campos if not presente]
    valor = round(100 * (_CAMPOS_COMPLETUDE - len(ausentes)) / _CAMPOS_COMPLETUDE, 1)
    return valor, ausentes


def suporte(ctx: model.ScoringContext, product: str, age_days: float | None) -> float:
    """Quanto histórico sustenta os números efetivamente usados.

    Com idade conhecida: combinação ponderada de s_idade (evidência direta
    na idade) e s_produto (evidência de fundo do produto). Sem idade
    conhecida (Prospecting), o termo de idade é OMITIDO, nunca zerado — a
    ausência de engage_date já reduz completude, e zerar aqui também
    cobraria a mesma ausência duas vezes.
    """
    s_prod = ctx.s_produto(product)
    if age_days is None:
        return round(100 * s_prod, 1)
    s_idade = ctx.s_idade(age_days)
    valor = constants.SUPORTE_PESO_IDADE * s_idade + constants.SUPORTE_PESO_PRODUTO * s_prod
    return round(100 * valor, 1)


def confianca(completude_valor: float, suporte_valor: float) -> float:
    """CONFIANÇA = min(completude, suporte) — a metade mais fraca governa."""
    return min(completude_valor, suporte_valor)


def metade_governante(completude_valor: float, suporte_valor: float) -> str:
    """Qual metade determina o mínimo — "completude", "suporte" ou "empate"."""
    if completude_valor < suporte_valor:
        return "completude"
    if suporte_valor < completude_valor:
        return "suporte"
    return "empate"


def sem_precedente(ctx: model.ScoringContext, age_days: float | None) -> bool:
    """Nenhum negócio ganho fechou dentro da janela de idade desta
    oportunidade. Só se aplica quando a idade é conhecida — Prospecting
    nunca é "sem precedente", é "idade desconhecida"."""
    if age_days is None:
        return False
    return ctx.s_idade(age_days) == 0.0


def razao_confianca(
    completude_valor: float,
    campos_ausentes: list[str],
    suporte_valor: float,
    sem_precedente_flag: bool,
) -> str:
    """Texto que nomeia qual metade governou o mínimo e o que especificamente
    falta — nunca apenas repete o número (Requirement "Explicabilidade")."""
    if sem_precedente_flag:
        return (
            "confiança limitada por ausência de precedente: nenhum negócio "
            "ganho fechou nesta faixa de idade"
        )

    metade = metade_governante(completude_valor, suporte_valor)
    if metade == "completude":
        campos = ", ".join(campos_ausentes) if campos_ausentes else "nenhum campo"
        return f"confiança limitada pela completude do cadastro: faltam {campos}"
    if metade == "suporte":
        return (
            "confiança limitada pelo suporte histórico: poucos negócios "
            "ganhos respaldam esta idade ou este produto"
        )
    return "completude e suporte equivalentes — nenhuma metade domina o mínimo"
