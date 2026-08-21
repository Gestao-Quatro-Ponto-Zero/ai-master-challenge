"""Constantes calibradas do motor de scoring.

Todos os números aqui vêm de uma única calibração sobre os 6.711 negócios
fechados de `sales_pipeline.csv` (out/2016-dez/2017): 4.238 Won + 2.473 Lost.
Cada constante cita sua origem. Nenhuma é escolhida à mão — mesmo quando o
valor é uma aproximação retida por política (ver nota em K_PRODUTO), a
reprodução do cálculo vive em `validation/shrinkage_check.py` e
`validation/isotonic_check.py`, não aqui.

Recalibração: trimestral (ver Requirement "Recalibração declarada" em
specs/lead-scoring/spec.md). Gatilhos de emergência:
- taxa de ganho global fora de 0,60-0,66
- mediana do ciclo de fechamento variando >20%
- mudança na tabela de preços
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Taxa de ganho global
# ---------------------------------------------------------------------------
# 4.238 Won / 6.711 fechados = 0,631650... — arredondada a 3 casas.
# Fonte: sales_pipeline.csv, todas as linhas com deal_stage em {Won, Lost}.
GLOBAL_WIN_RATE = 0.632

# ---------------------------------------------------------------------------
# Encolhimento hierárquico (p̂_produto)
# ---------------------------------------------------------------------------
# k = variância_esperada_por_acaso / variância_em_excesso, nível "produto"
# (7 produtos, n de 25 a 1.436 negócios fechados por produto).
# Reprodução honesta em validation/shrinkage_check.py: a variância em excesso
# do nível de produto é NEGATIVA (-0,001199) — os sete produtos são mais
# parecidos entre si do que o ruído amostral por si só explicaria — logo o
# `k` recalculado é infinito, exatamente como nos níveis conta×produto e
# produto×setor. K_PRODUTO = 4,0 é uma aproximação retida por política, não
# o resultado do cálculo: com `k` infinito, p̂_produto colapsaria para 0,632
# em todos os produtos, e a constante congelada preserva uma diferenciação
# (0,6034 a 0,6484) cujo efeito é desprezível — p̂ responde por 0,1% da
# variância de log(PRIORIDADE) no funil aberto (ver docs/decisions-log.md,
# entrada 2026-08-20, e o relatório de validação para a reprodução).
K_PRODUTO = 4.0

# Os níveis conta×produto e produto×setor têm variância em excesso ≤ 0 nos
# dados calibrados (k = ∞) e colapsam para o nível de produto — por isso não
# aparecem como uma constante de peso aqui: contribuem zero, por definição,
# e o motor de scoring nunca lê conta ou setor para calcular p̂_produto.
# A verificação do colapso está em validation/shrinkage_check.py.

# ---------------------------------------------------------------------------
# Curva p_ganho(t) — probabilidade de ganho condicionada a "ainda aberto na
# idade t", lida em degraus (maior ponto calibrado ≤ t).
# Fonte: negócios Won/Lost fechados, agrupados por idade em Engaging no
# momento do desfecho, suavizados por regressão isotônica.
# ---------------------------------------------------------------------------
P_GANHO_BREAKPOINTS: list[tuple[int, float]] = [
    (0, 0.632),
    (14, 0.686),
    (57, 0.684),
    (88, 0.704),
    (120, 0.751),
]

# ---------------------------------------------------------------------------
# Curva risco(t) — P(resolve nos próximos 30 dias | ainda aberto na idade t),
# suavizada por regressão isotônica (garante monotonicidade não-decrescente).
# ---------------------------------------------------------------------------
RISCO_BREAKPOINTS: list[tuple[int, float]] = [
    (0, 0.219),  # patamar válido para 0-30 dias
    (45, 0.322),
    (57, 0.489),
    (88, 0.832),
    (110, 1.000),
]

# ---------------------------------------------------------------------------
# Fronteiras de idade
# ---------------------------------------------------------------------------
# Nenhum dos 6.711 negócios fechados levou mais de 138 dias (verificado em
# validation/isotonic_check.py a cada execução, não hardcoded sem checagem).
CENSURA_DIAS = 138
# Última idade com amostra confiável (n >= 200 negócios ainda abertos) nas
# curvas calibradas — acima disso, congela em p_ganho(120)/risco(120) até
# o limite de censura de 138 dias.
CURVA_LIMITE_CONFIAVEL_DIAS = 120

# Reversão ao prior acima de 138 dias (censura, não extrapolação).
CENSURA_P_HAT = GLOBAL_WIN_RATE
CENSURA_URGENCIA = 0.15

# ---------------------------------------------------------------------------
# Prospecting — sem engage_date, sem idade a imputar.
# ---------------------------------------------------------------------------
# Risco médio observado na entrada do funil (t=0), sem suavização isotônica.
PROSPECTING_URGENCIA = 0.47

# ---------------------------------------------------------------------------
# Preços de tabela — products.csv, catálogo de 7 produtos.
# ---------------------------------------------------------------------------
PRECO_TABELA: dict[str, float] = {
    "GTX Basic": 550.0,
    "GTX Pro": 4821.0,
    "MG Special": 55.0,
    "MG Advanced": 3393.0,
    "GTX Plus Pro": 5482.0,
    "GTX Plus Basic": 1096.0,
    "GTK 500": 26768.0,
}

# ---------------------------------------------------------------------------
# Multiplicador de porte — razão entre ticket médio do porte e o ticket médio
# global, calculada sobre os negócios fechados (decisions-log.md, entrada
# 2026-08-19: produto+porte explica 98,70% da variância do valor fechado
# contra 98,30% só com produto).
# ---------------------------------------------------------------------------
MULT_PORTE: dict[str, float] = {
    "SMB": 0.95,
    "Mid": 0.91,
    "Upper": 1.07,
    "Enterprise": 1.06,
}
# Prior neutro quando a conta é desconhecida — nunca impede o score.
MULT_PORTE_DESCONHECIDO = 1.00

# Faixas de porte por número de funcionários (accounts.csv).
PORTE_SMB_MAX = 1_000  # < 1.000
PORTE_MID_MAX = 3_000  # 1.000-2.999
PORTE_UPPER_MAX = 8_000  # 3.000-7.999
# >= 8.000 -> Enterprise


def classificar_porte(employees: float | None) -> str | None:
    """Classifica o porte de uma conta pelo número de funcionários.

    Retorna None quando o número de funcionários é desconhecido (conta
    ausente) — o chamador deve tratar isso como MULT_PORTE_DESCONHECIDO.

    `employees != employees` cobre NaN (idioma IEEE754) além de `None`: o
    merge de `accounts.csv` preenche `employees` com NaN, não None, quando
    não há conta vinculada — sem essa checagem, `NaN < limiar` é sempre
    False e a conta caía silenciosamente em "Enterprise" em vez do prior
    neutro que este requisito promete.
    """
    if employees is None or employees != employees:
        return None
    if employees < PORTE_SMB_MAX:
        return "SMB"
    if employees < PORTE_MID_MAX:
        return "Mid"
    if employees < PORTE_UPPER_MAX:
        return "Upper"
    return "Enterprise"


# ---------------------------------------------------------------------------
# Correções de qualidade de dados na origem (proposal.md / architecture.md).
# ---------------------------------------------------------------------------
SECTOR_CORRECTIONS: dict[str, str] = {
    "technolgy": "technology",
}
PRODUCT_CORRECTIONS: dict[str, str] = {
    "GTXPro": "GTX Pro",
    "GTX-Pro": "GTX Pro",
}

# ---------------------------------------------------------------------------
# CONFIANÇA — completude x suporte, ambas 0-100 (Requirement "Atribuição de
# confiança"). Nenhuma das duas usa idade como regra de censura própria:
# idade só entra através da densidade de precedente em SUPORTE_JANELA_IDADE_DIAS.
# ---------------------------------------------------------------------------
# Janela de idade (dias, +/-) usada para contar negócios ganhos "próximos"
# da idade da oportunidade — a evidência direta de precedente para aquela
# idade específica. Sensibilidade (docs/decisions-log.md, entrada
# 2026-08-20): mais estreita perderia amostra em faixas já finas; mais larga
# confundiria idades com dinâmicas de janela diferentes (ver curves.py).
SUPORTE_JANELA_IDADE_DIAS = 15

# Saturação de cada termo de suporte: min(1, n / SUPORTE_SATURACAO_N).
# n/50 foi escolhido sobre n/200 porque n/200 deixava 76% do funil aberto em
# suporte zero (inutilizável para ordenar) — ver docs/decisions-log.md,
# entrada 2026-08-20, para a comparação entre variantes testadas.
SUPORTE_SATURACAO_N = 50

# Pesos do suporte quando a idade é conhecida: a densidade de precedente na
# idade específica pesa mais que o volume histórico do produto, porque é a
# evidência direta sobre esta oportunidade — o volume de produto é evidência
# de fundo. Quando a idade é desconhecida (Prospecting), o termo de idade é
# OMITIDO (nunca zerado) e o suporte usa só o termo de produto — a ausência
# de engage_date já é cobrada em completude, não pode ser cobrada duas vezes.
SUPORTE_PESO_IDADE = 0.75
SUPORTE_PESO_PRODUTO = 0.25

# ---------------------------------------------------------------------------
# Cortes da árvore de decisão de ESTADO (Requirement "Atribuição de estado").
# ---------------------------------------------------------------------------
# SCORE >= 95: percentil 95 da própria distribuição de referência — "vale
# mais, em risco agora, do que 95% dos negócios que historicamente
# converteram em receita". Acompanha a recalibração trimestral da
# distribuição de referência, sem constante própria a recalibrar.
SCORE_CORTE_PRIORITIZE = 95.0

# CONFIANÇA < 50: "menos da metade do que este score afirma está apoiada em
# dado observado e precedente". CONFIANÇA se aglomera nesta base — 50 contra
# 60 move só 8 das 2.089 oportunidades (docs/decisions-log.md, 2026-08-20).
CONFIANCA_CORTE_QUALIFICAR = 50.0

DEAL_STAGES_ABERTOS = ("Prospecting", "Engaging")
DEAL_STAGES_FECHADOS = ("Won", "Lost")

ESTADOS = ("prioritize", "acompanhar", "qualificar", "revisao_lote")

ESTADO_LABELS: dict[str, str] = {
    "prioritize": "Priorizar",
    "acompanhar": "Acompanhar",
    "qualificar": "Qualificar",
    "revisao_lote": "Revisão em lote",
}
