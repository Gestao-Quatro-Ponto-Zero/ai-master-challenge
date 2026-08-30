"""Constantes calibradas do motor de scoring.

Todos os números aqui vêm de uma única calibração sobre os 6.711 negócios
fechados de `sales_pipeline.csv` (out/2016-dez/2017): 4.238 Won + 2.473 Lost.
Cada constante cita sua origem. Nenhuma é escolhida à mão — mesmo quando o
valor é uma aproximação retida por política (ver nota em K_FIT), a
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
# Taxa de ganho global — uma população só.
# ---------------------------------------------------------------------------
# 4.238 Won / 6.711 fechados = 0,631650... — arredondada a 3 casas. Fonte:
# sales_pipeline.csv, toda linha com deal_stage em {Won, Lost}. É a única
# população de calibração do motor: todo negócio aqui tem desfecho
# OBSERVADO, nenhum rótulo foi atribuído por nós.
#
# Houve duas taxas entre 2026-08-21 e 2026-08-29, quando 653 oportunidades
# abertas há ≥200 dias eram convertidas para `Lost` na carga e entravam na
# calibração (0,5755 sobre 7.364). O expurgo foi removido em 2026-08-29 por
# fabricar sinal onde o dado observado não tem nenhum — reproduzido a cada
# execução por `validation/reclassification_check.py` e pela seção 10 do
# backtest. Ver docs/decisions-log.md, entrada 2026-08-29.
GLOBAL_WIN_RATE = 0.632

# ---------------------------------------------------------------------------
# Encolhimento hierárquico (p̂_produto)
# ---------------------------------------------------------------------------
# k = variância_esperada_por_acaso / variância_em_excesso, DERIVADO em tempo
# de carga (`scoring/pipeline.py::build_scoring_context`, via
# `shrinkage.level_stats`) para os quatro níveis da hierarquia (conta×
# produto, produto×setor, produto, global) — nenhum nível usa uma constante
# de política congelada substituindo esse cálculo. Reprodução honesta em
# validation/shrinkage_check.py.
#
# Sobre os 6.711 negócios com desfecho observado, os TRÊS níveis abaixo do
# global têm variância em excesso ≤ 0 (os grupos são mais parecidos entre
# si do que o ruído amostral por si só explicaria) — `k` de cada um é
# infinito e todos colapsam para a taxa global. Consequência direta e
# desejada: `p̂_produto` vale GLOBAL_WIN_RATE para os sete produtos, a
# amplitude entre produtos é 0,00pp, e o motor nunca lê conta nem setor
# para calcular p̂. Isso é o mesmo achado que a análise sempre reportou
# ("produto não prevê ganho/perda", permutação p=0,373) — agora coerente
# também no código, sem uma constante que o contradiga.
#
# O nível de produto chegou a NÃO colapsar (k ≈ 0,6966, amplitude 16,66pp)
# entre 2026-08-21 e 2026-08-29. Não foi mudança de mercado: era efeito do
# expurgo de 200 dias, que jogava 10 perdas atribuídas por nós sobre os 25
# negócios fechados de GTK 500 (60,0% → 42,86%) e sozinho virava a
# variância em excesso do nível de negativa para positiva. Removido o
# expurgo, o nível volta a colapsar sem intervenção manual — que é
# exatamente o comportamento que `compute_k` promete.

# ---------------------------------------------------------------------------
# Setor NÃO entra em p̂ (mult_setor removido em 2026-08-29).
# ---------------------------------------------------------------------------
# `mult_setor` era um ajuste produto×setor aplicado sobre p̂, com
# encolhimento por K_SETOR=25 e teto de ±15%, mantido por decisão de
# produto APESAR de a validação apontar contra. As duas evidências,
# reproduzidas a cada execução do backtest, sempre foram negativas:
# o nível produto×setor tem variância em excesso ≤ 0 (k = ∞ — colapsa,
# ver acima), e a validação cruzada 5-fold mostra que condicionar por
# produto×setor prevê PIOR fora da amostra que não condicionar
# (`validation/sector_conditioning_check.py`, seção 6 do backtest).
# Manter um multiplicador sobre um nível que a própria validação rejeita
# é codificar ruído como rigor — o mesmo critério que já mantinha
# gerente, região, receita e idade da empresa fora da fórmula. Removido:
# não sobrou constante de política aqui. Setor continua sendo lido para
# a completude de CONFIANÇA, para o fit vendedor×setor (mecanismo de
# redistribuição de carga, nunca p̂/SCORE) e como filtro de UI.
# Ver docs/decisions-log.md, entrada 2026-08-29.

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
# validation/isotonic_check.py a cada execução, não hardcoded sem
# checagem). Fronteira OBSERVADA: acima dela não há desfecho para
# extrapolar, então p̂ reverte ao prior em vez de continuar a curva.
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

# Pesos do suporte: a densidade de precedente na idade específica pesa
# mais que o volume histórico do produto, porque é a evidência direta
# sobre esta oportunidade — o volume de produto é evidência de fundo. O
# termo de idade é OMITIDO (nunca zerado) quando não há idade conhecida
# (Prospecting), com os pesos restantes renormalizados
# proporcionalmente: a ausência já é cobrada uma vez em completude, não
# pode ser cobrada duas vezes.
#
# Havia um terceiro termo, s_célula (peso 0,15), medindo o tamanho
# amostral da célula produto×setor. Ele existia para medir o suporte do
# `mult_setor`; removido junto com ele em 2026-08-29 — suporte responde
# "quanto histórico sustenta os números efetivamente usados", e a célula
# produto×setor deixou de alimentar número algum do score.
SUPORTE_PESO_IDADE = 0.65
SUPORTE_PESO_PRODUTO = 0.20

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

# ---------------------------------------------------------------------------
# Carga por vendedor e ESTADO (workload-fit spec, Requirement "Detecção de
# sobrecarga"). "Estado" aqui é o ESTADO do funil (prioritize/acompanhar/
# qualificar), não geografia — revisao_lote é excluído por definição.
# ---------------------------------------------------------------------------
CARGA_RAZAO_SOBRECARGA = 1.5
# Piso absoluto normativo: sem ele, uma única oportunidade num ESTADO cuja
# média do escritório é próxima de zero apareceria como muitas vezes a
# média (design.md, D4 — Central/prioritize, média 0,10).
CARGA_PISO_SOBRECARGA = 5

# ---------------------------------------------------------------------------
# Fit vendedor x produto / vendedor x setor (workload-fit spec, Requirement
# "Fit histórico do vendedor por produto e por setor"). Encolhimento em
# dois níveis: vendedor -> escritório -> global, sobre `pipeline.fechados`.
# k_fit é constante de POLÍTICA — a derivação por variância em excesso
# (validation/) espera-se que colapse para k=∞, do mesmo modo que os
# níveis conta×produto e produto×setor de p̂_produto (design.md, D3).
# ---------------------------------------------------------------------------
K_FIT = 25.0

# Suporte mínimo (negócios fechados) para uma célula vendedor×produto ou
# vendedor×setor ser considerada com base suficiente — usado só na
# validação (task 8.5), nunca para suprimir a exibição do fit encolhido.
FIT_SUPORTE_MINIMO = 10

# ---------------------------------------------------------------------------
# Sugestão de redistribuição (workload-fit spec, Requirement "Sugestão de
# vendedor para redistribuição"). Pesos de política, não resultado
# empírico — dado que o fit é indistinguível de ruído (ver ressalva
# estatística), a folga é o que decide na prática (design.md, D5).
# ---------------------------------------------------------------------------
RANK_PESO_FOLGA = 0.5
RANK_PESO_FIT = 0.5

# Produto pesa mais que setor: célula mais densa (mediana 34 vs 20 negócios
# fechados) e 5,9% dos fechados não têm setor (design.md, D5).
FIT_PESO_PRODUTO = 0.6
FIT_PESO_SETOR = 0.4
