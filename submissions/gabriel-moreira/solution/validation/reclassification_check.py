"""Sensibilidade ao expurgo de 200 dias — Requirement "Reprodução do
impacto da reclassificação de 200 dias".

Este módulo mede o que ACONTECERIA se as oportunidades abertas há 200 dias
ou mais fossem convertidas para `Lost` e entrassem na calibração. Ele nunca
aplica essa conversão: o dataset que o motor de scoring carrega tem apenas
desfechos observados, e `aplicado_em_producao` é sempre False.

Entre 2026-08-21 e 2026-08-29 o expurgo era aplicado de verdade, na carga.
Foi removido quando esta mesma medição mostrou que ele não é neutro — ele
fabrica os dois sinais que a análise passou a reportar:

- **Produto:** o nível de produto colapsa (`k = ∞`, amplitude de p̂ de
  0,00pp) sobre os desfechos observados. Com o expurgo, GTK 500 recebe 10
  perdas atribuídas sobre 25 negócios fechados e sozinho vira a variância
  em excesso do nível de negativa para positiva.
- **Vendedor:** as oportunidades paradas não se distribuem por igual entre
  vendedores. Quem tem carteira velha leva perdas atribuídas; quem não tem,
  não leva nenhuma — e a dispersão resultante é lida pelo teste de
  permutação como sinal de desempenho.

Ver docs/decisions-log.md, entrada 2026-08-29.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from scipy.stats import chi2_contingency

from permutation_tests import permutation_test
from scoring import constants
from scoring.repository import Dataset
from scoring.shrinkage import GroupCounts, level_stats, p_hat_produto, product_group_counts

# Régua de política que o expurgo usaria. Vive aqui, no artefato de
# validação, e não em `scoring.constants`: é o parâmetro de um cenário
# hipotético, não uma constante do motor.
IDADE_EXPURGO_DIAS = 200

# Abaixo deste `n` de negócios fechados, a variação de taxa do produto é
# dominada por amostra pequena — separa limpo GTK 500 do restante do
# catálogo.
AMOSTRA_PEQUENA_N_MAXIMO = 100


@dataclass(frozen=True)
class ProdutoVariacao:
    produto: str
    n_real: int
    n_hipotetico: int
    taxa_real: float
    taxa_hipotetica: float
    variacao_pp: float
    amostra_pequena: bool


@dataclass(frozen=True)
class NivelProduto:
    """Derivação de `k` do nível de produto nos dois cenários — é aqui que
    o expurgo deixa de ser uma questão de contagem e vira uma questão de
    modelo."""

    k_real: float
    k_hipotetico: float
    var_em_excesso_real: float
    var_em_excesso_hipotetica: float
    amplitude_p_hat_real_pp: float
    amplitude_p_hat_hipotetica_pp: float


@dataclass(frozen=True)
class SinalAtributo:
    atributo: str
    p_real: float
    p_hipotetico: float


@dataclass(frozen=True)
class ReclassificationReport:
    aplicado_em_producao: bool
    n_candidatos: int
    idade_minima: int
    idade_maxima: int
    funil_real: int
    funil_hipotetico: int
    base_rate_real: float
    base_rate_hipotetica: float
    produtos: list[ProdutoVariacao]
    nivel_produto: NivelProduto
    sinais: list[SinalAtributo]
    n_vendedores_sem_candidato: int
    amplitude_vendedor_real_pp: float
    amplitude_vendedor_hipotetica_pp: float
    #: Qui-quadrado de "ser candidato ao expurgo ~ vendedor" sobre a
    #: população hipotética. Mede o MECANISMO: se os candidatos caíssem
    #: por igual entre carteiras, o expurgo deslocaria todas as taxas
    #: junto e não criaria dispersão nenhuma.
    concentracao_chi2: float
    concentracao_gl: int
    concentracao_p: float
    #: Correlação entre "fração da carteira expurgada" e "taxa de vitória
    #: hipotética". O expurgo só adiciona derrota; quanto mais negativa,
    #: mais a taxa hipotética de um vendedor é função de quanto funil
    #: parado ele tinha — e não de como ele fecha.
    corr_fracao_expurgada_taxa: float


def candidatos_ao_expurgo(dataset: Dataset) -> pd.Series:
    """Máscara booleana das oportunidades que o expurgo converteria."""
    pipeline = dataset.pipeline
    idade = (dataset.as_of_default - pipeline["engage_date"]).dt.days
    return (
        (pipeline["deal_stage"] == "Engaging")
        & idade.notna()
        & (idade >= IDADE_EXPURGO_DIAS)
    )


def _amplitude_p_hat_pp(counts: dict[str, GroupCounts], prior: float, k: float) -> float:
    valores = [
        p_hat_produto(produto, counts, global_win_rate=prior, k=k)
        for produto in constants.PRECO_TABELA
    ]
    return (max(valores) - min(valores)) * 100


def build_report(dataset: Dataset) -> ReclassificationReport:
    pipeline = dataset.pipeline
    candidatos = candidatos_ao_expurgo(dataset)

    real = pipeline[pipeline["deal_stage"].isin(constants.DEAL_STAGES_FECHADOS)]
    # O cenário hipotético é construído numa cópia — `dataset.pipeline`
    # nunca é tocado.
    hipotetico = pd.concat(
        [
            real.assign(expurgado=False),
            pipeline[candidatos].assign(deal_stage="Lost", expurgado=True),
        ],
        ignore_index=True,
    )

    idade_candidatos = (dataset.as_of_default - pipeline.loc[candidatos, "engage_date"]).dt.days
    funil_real = int(pipeline["deal_stage"].isin(constants.DEAL_STAGES_ABERTOS).sum())

    base_real = float((real["deal_stage"] == "Won").mean())
    base_hip = float((hipotetico["deal_stage"] == "Won").mean())

    counts_real = product_group_counts(real)
    counts_hip = product_group_counts(hipotetico)

    produtos = []
    for produto in constants.PRECO_TABELA:
        r = counts_real.get(produto)
        h = counts_hip.get(produto)
        taxa_r = r.rate if r else 0.0
        taxa_h = h.rate if h else 0.0
        produtos.append(
            ProdutoVariacao(
                produto=produto,
                n_real=r.n if r else 0,
                n_hipotetico=h.n if h else 0,
                taxa_real=taxa_r,
                taxa_hipotetica=taxa_h,
                variacao_pp=(taxa_h - taxa_r) * 100,
                amostra_pequena=(h.n if h else 0) <= AMOSTRA_PEQUENA_N_MAXIMO,
            )
        )

    stats_real = level_stats(counts_real, base_real)
    stats_hip = level_stats(counts_hip, base_hip)
    nivel_produto = NivelProduto(
        k_real=stats_real.k,
        k_hipotetico=stats_hip.k,
        var_em_excesso_real=stats_real.var_em_excesso,
        var_em_excesso_hipotetica=stats_hip.var_em_excesso,
        amplitude_p_hat_real_pp=_amplitude_p_hat_pp(counts_real, base_real, stats_real.k),
        amplitude_p_hat_hipotetica_pp=_amplitude_p_hat_pp(counts_hip, base_hip, stats_hip.k),
    )

    sinais = [
        SinalAtributo(
            atributo=attr,
            p_real=permutation_test(real, attr).p_valor,
            p_hipotetico=permutation_test(hipotetico, attr).p_valor,
        )
        for attr in ("sales_agent", "product", "sector", "account")
    ]

    taxa_real_por_vendedor = real.groupby("sales_agent")["deal_stage"].apply(
        lambda s: (s == "Won").mean()
    )
    taxa_hip_por_vendedor = hipotetico.groupby("sales_agent")["deal_stage"].apply(
        lambda s: (s == "Won").mean()
    )
    candidatos_por_vendedor = (
        pipeline[candidatos].groupby("sales_agent").size().reindex(taxa_real_por_vendedor.index).fillna(0)
    )

    fracao_expurgada = (candidatos_por_vendedor / hipotetico.groupby("sales_agent").size()).fillna(0.0)
    tabela_concentracao = pd.crosstab(hipotetico["sales_agent"], hipotetico["expurgado"])
    chi2, p_concentracao, gl, _ = chi2_contingency(tabela_concentracao)

    return ReclassificationReport(
        aplicado_em_producao=bool(
            (pipeline.loc[candidatos, "deal_stage"] != "Engaging").any()
        ),
        n_candidatos=int(candidatos.sum()),
        idade_minima=int(idade_candidatos.min()),
        idade_maxima=int(idade_candidatos.max()),
        funil_real=funil_real,
        funil_hipotetico=funil_real - int(candidatos.sum()),
        base_rate_real=base_real,
        base_rate_hipotetica=base_hip,
        produtos=produtos,
        nivel_produto=nivel_produto,
        sinais=sinais,
        n_vendedores_sem_candidato=int((candidatos_por_vendedor == 0).sum()),
        amplitude_vendedor_real_pp=float(
            taxa_real_por_vendedor.max() - taxa_real_por_vendedor.min()
        )
        * 100,
        amplitude_vendedor_hipotetica_pp=float(
            taxa_hip_por_vendedor.max() - taxa_hip_por_vendedor.min()
        )
        * 100,
        concentracao_chi2=float(chi2),
        concentracao_gl=int(gl),
        concentracao_p=float(p_concentracao),
        corr_fracao_expurgada_taxa=float(
            fracao_expurgada.corr(taxa_hip_por_vendedor.reindex(fracao_expurgada.index))
        ),
    )
