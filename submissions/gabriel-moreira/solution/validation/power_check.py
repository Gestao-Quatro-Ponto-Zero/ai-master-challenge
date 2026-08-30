"""Poder do teste de vendedor — o que este histórico conseguiria enxergar.

As seções 2 e 12 respondem "a dispersão observada se distingue do acaso?"
e devolvem não. Essa resposta tem uma leitura correta e uma leitura
errada, e a diferença entre as duas vale dinheiro:

  LEITURA ERRADA   "os vendedores são todos iguais".
  LEITURA CORRETA  "se existe diferença real de habilidade, ela é menor
                   do que o menor efeito que este histórico enxergaria".

Um teste que não rejeita só é informativo junto com o seu poder. Sem ele,
"p=0,371" é compatível tanto com "não há diferença nenhuma" quanto com
"há uma diferença enorme e a amostra é pequena demais" — e neste funil a
segunda hipótese seria cara: 6pp de conversão a mais sobre uma carteira de
220 negócios são dezenas de milhares de reais por vendedor por ano. Esta
seção mede onde fica a fronteira entre as duas.

Quatro números:

1. `spread_observado` vs `spread_nulo` — a amplitude entre o melhor e o
   pior vendedor comparada com a que 30 vendedores IDÊNTICOS já produzem
   com os mesmos tamanhos de carteira. É o número que impede a leitura
   ingênua: a amplitude que parece um achado é a amplitude que o acaso
   entrega de graça.

2. `curva_poder` — para uma grade de τ (desvio-padrão VERDADEIRO da taxa
   de vitória entre vendedores), com que frequência o teste omnibus da
   seção 2 rejeitaria. Daí sai o MDE: o menor τ detectável em 80% das
   amostras.

3. `tau_excesso_pp` — a estimativa PONTUAL da dispersão verdadeira, por
   variância em excesso (a mesma técnica que `scoring/fit.py` usa para
   derivar k): variância observada menos a variância binomial que os
   tamanhos de carteira já explicam. É o número que impede a leitura
   oposta, a de que "não rejeitou" significa "é zero" — o excesso é
   positivo, só é pequeno e está abaixo do que o teste enxerga.

4. `poder_vendedor_unico` — o outro extremo: um vendedor específico,
   escolhido ANTES de olhar o dado, realmente δ acima dos demais. É o
   teste mais favorável possível (uma comparação, sem multiplicidade), e
   serve de teto — o que o omnibus não vê, este veria.

Nota de método: a região de rejeição vem do nulo de permutação do próprio
teste (percentil 95 da dispersão nula), e os mundos com heterogeneidade
real são gerados por sorteio binomial, que não condiciona no total de
vitórias como a permutação condiciona. Com n=6.711 a diferença é de
segunda ordem — a dispersão nula é dominada por ruído binomial DENTRO de
cada carteira —, mas ela existe e empurra o poder marginalmente para
cima; ou seja, o MDE reportado é, se erra, otimista. Nenhuma das
conclusões abaixo depende dessa casa.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from permutation_tests import _dispersion

SEED = 20260830
N_SIMULACOES = 2000
#: Grade de τ em pontos percentuais de desvio-padrão verdadeiro entre
#: vendedores. Vai de 1pp (diferença desprezível) a 10pp (um mundo em que
#: o melhor vendedor converte ~40pp acima do pior).
TAU_GRADE_PP = (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 7.5, 10.0)
#: Grade de tamanho de carteira usada para dimensionar o experimento do
#: roadmap: quantos negócios fechados por vendedor seriam necessários para
#: que τ̂ saísse da zona cega. Aleatorizar a alocação de leads remove o
#: confundimento (taxa de vitória deixa de misturar habilidade com
#: qualidade da carteira) mas NÃO muda o poder — este é o preço em amostra.
N_GRADE_DIMENSIONAMENTO = (220, 500, 1000, 2000, 4000, 8000)
#: Efeitos individuais testados. 6,3pp é "10% a mais" em termos
#: relativos sobre um base rate de ~63%; 10pp é a leitura absoluta da
#: mesma frase.
DELTAS_PP = (5.0, 6.3, 10.0, 15.0)
PODER_ALVO = 0.80
ALFA = 0.05


@dataclass(frozen=True)
class PontoDePoder:
    tau_pp: float
    amplitude_media_pp: float
    poder: float


@dataclass(frozen=True)
class PontoDeDimensionamento:
    n_por_vendedor: int
    poder: float


@dataclass(frozen=True)
class PoderVendedorUnico:
    delta_pp: float
    poder: float


@dataclass(frozen=True)
class PowerReport:
    n_vendedores: int
    n_fechados: int
    base_rate: float
    n_mediano_carteira: int
    spread_observado_pp: float
    spread_nulo_mediano_pp: float
    spread_nulo_p2_5_pp: float
    spread_nulo_p97_5_pp: float
    dispersao_observada_pp: float
    dispersao_nula_esperada_pp: float
    tau_excesso_pp: float
    dispersao_critica_pp: float
    curva_poder: tuple[PontoDePoder, ...] = field(default_factory=tuple)
    poder_vendedor_unico: tuple[PoderVendedorUnico, ...] = field(default_factory=tuple)
    dimensionamento: tuple[PontoDeDimensionamento, ...] = field(default_factory=tuple)

    @property
    def mde_pp(self) -> float | None:
        """Menor τ detectável com 80% de poder, interpolado entre os dois
        pontos da grade que cercam o corte. Interpolar em vez de devolver o
        primeiro ponto acima de 80% evita reportar como fronteira um valor
        que é só o espaçamento da grade. None se nem o maior τ chega lá."""
        anterior = None
        for ponto in self.curva_poder:
            if ponto.poder >= PODER_ALVO:
                if anterior is None:
                    return ponto.tau_pp
                intervalo = ponto.poder - anterior.poder
                if intervalo <= 0:
                    return ponto.tau_pp
                fracao = (PODER_ALVO - anterior.poder) / intervalo
                return anterior.tau_pp + fracao * (ponto.tau_pp - anterior.tau_pp)
            anterior = ponto
        return None

    @property
    def n_para_enxergar_tau(self) -> int | None:
        """Negócios fechados por vendedor necessários para que τ̂ — a
        dispersão que hoje é invisível — fosse detectável com 80% de poder.
        É o custo em amostra do experimento do roadmap, e a razão pela qual
        aleatorizar a alocação de leads não resolve o problema sozinho:
        aleatorizar tira o confundimento, não a variância."""
        for ponto in self.dimensionamento:
            if ponto.poder >= PODER_ALVO:
                return ponto.n_por_vendedor
        return None

    @property
    def tau_abaixo_do_detectavel(self) -> bool:
        """A dispersão verdadeira estimada cai na zona cega do teste?

        Quando isto é verdade, as duas leituras extremas estão erradas ao
        mesmo tempo: não há sinal a publicar (τ̂ < MDE, o teste não o
        distingue de zero) e não há igualdade a afirmar (τ̂ > 0)."""
        mde = self.mde_pp
        return mde is not None and self.tau_excesso_pp < mde

    @property
    def amplitude_implicada_por_tau_pp(self) -> float:
        """Amplitude esperada entre o melhor e o pior de `n_vendedores`
        sorteados de uma normal com desvio-padrão τ̂ — a tradução de τ̂ para
        a unidade em que a operação pensa ("quanto o melhor converte a mais
        que o pior"). Usa a aproximação clássica de Tippett para a amplitude
        esperada da normal padrão."""
        if self.n_vendedores < 2:
            return 0.0
        n = self.n_vendedores
        z = float(np.sqrt(2.0 * np.log(n)))
        amplitude_padrao = 2.0 * (z - (np.log(np.log(n)) + np.log(4 * np.pi)) / (2 * z))
        return self.tau_excesso_pp * amplitude_padrao

    @property
    def spread_observado_dentro_do_nulo(self) -> bool:
        """A amplitude real cabe no intervalo que o acaso puro produz?"""
        return self.spread_nulo_p2_5_pp <= self.spread_observado_pp <= self.spread_nulo_p97_5_pp


def _taxas_por_vendedor(closed: pd.DataFrame) -> pd.DataFrame:
    won = (closed["deal_stage"] == "Won").astype(float)
    return (
        pd.DataFrame({"sales_agent": closed["sales_agent"].to_numpy(), "won": won.to_numpy()})
        .groupby("sales_agent")["won"]
        .agg(["size", "mean"])
    )


def build_report(
    closed: pd.DataFrame,
    n_simulacoes: int = N_SIMULACOES,
    tau_grade_pp: tuple[float, ...] = TAU_GRADE_PP,
    deltas_pp: tuple[float, ...] = DELTAS_PP,
) -> PowerReport:
    por_vendedor = _taxas_por_vendedor(closed)
    n_por_vendedor = por_vendedor["size"].to_numpy()
    taxas = por_vendedor["mean"].to_numpy()
    base_rate = float((closed["deal_stage"] == "Won").mean())

    labels = (closed["deal_stage"] == "Won").to_numpy(dtype=float)
    grupos = closed["sales_agent"].to_numpy()
    dispersao_observada = _dispersion(labels, grupos)
    spread_observado = float(taxas.max() - taxas.min())

    # Variância em excesso: quanto da dispersão observada sobra depois de
    # descontar a variância binomial que os tamanhos de carteira já
    # explicam. É a estimativa pontual de τ, e é a mesma conta que
    # `scoring/fit.py` faz para derivar k — o excesso aqui é positivo mas
    # pequeno, e o teste (MDE abaixo) não o separa de zero.
    pesos_v = n_por_vendedor / n_por_vendedor.sum()
    var_observada = float((pesos_v * (taxas - base_rate) ** 2).sum())
    var_binomial = float((pesos_v * (base_rate * (1 - base_rate) / n_por_vendedor)).sum())
    tau_excesso = float(np.sqrt(max(var_observada - var_binomial, 0.0)))

    # Nulo: a permutação da seção 2 — mesmos tamanhos de carteira, mesmo
    # total de vitórias, vínculo vendedor↔desfecho destruído.
    rng = np.random.default_rng(SEED)
    dispersoes_nulas = np.empty(n_simulacoes)
    spreads_nulos = np.empty(n_simulacoes)
    for i in range(n_simulacoes):
        embaralhado = rng.permutation(labels)
        dispersoes_nulas[i] = _dispersion(embaralhado, grupos)
        taxas_nulas = pd.DataFrame({"won": embaralhado, "g": grupos}).groupby("g")["won"].mean()
        spreads_nulos[i] = float(taxas_nulas.max() - taxas_nulas.min())
    critica = float(np.percentile(dispersoes_nulas, 100 * (1 - ALFA)))

    # Poder do omnibus: mundos em que a habilidade REALMENTE varia com
    # desvio-padrão τ, medidos contra a região de rejeição acima.
    curva = []
    for tau_pp in tau_grade_pp:
        tau = tau_pp / 100.0
        rng_tau = np.random.default_rng(SEED + int(tau_pp * 10))
        verdadeiras = np.clip(
            rng_tau.normal(base_rate, tau, size=(n_simulacoes, len(n_por_vendedor))), 0.02, 0.98
        )
        simuladas = rng_tau.binomial(n_por_vendedor, verdadeiras) / n_por_vendedor
        pesos = n_por_vendedor / n_por_vendedor.sum()
        medias = (simuladas * pesos).sum(axis=1)
        disp = np.sqrt((pesos * (simuladas - medias[:, None]) ** 2).sum(axis=1))
        curva.append(
            PontoDePoder(
                tau_pp=tau_pp,
                amplitude_media_pp=float((simuladas.max(1) - simuladas.min(1)).mean() * 100),
                poder=float((disp >= critica).mean()),
            )
        )

    # Teto: um vendedor pré-especificado, carteira mediana, contra o resto
    # do funil (z de duas proporções, variância combinada).
    n_v = int(np.median(n_por_vendedor))
    n_resto = int(n_por_vendedor.sum()) - n_v
    poder_unico = []
    for delta_pp in deltas_pp:
        delta = delta_pp / 100.0
        rng_d = np.random.default_rng(SEED + 1000 + int(delta_pp * 10))
        p_v = rng_d.binomial(n_v, min(base_rate + delta, 0.98), size=n_simulacoes) / n_v
        p_r = rng_d.binomial(n_resto, base_rate, size=n_simulacoes) / n_resto
        p_pool = (p_v * n_v + p_r * n_resto) / (n_v + n_resto)
        se = np.sqrt(p_pool * (1 - p_pool) * (1 / n_v + 1 / n_resto))
        z = (p_v - p_r) / se
        poder_unico.append(PoderVendedorUnico(delta_pp=delta_pp, poder=float((z > 1.96).mean())))

    # Dimensionamento: com carteiras de tamanho n (iguais entre vendedores),
    # com que frequência o mesmo teste pegaria uma dispersão verdadeira do
    # tamanho de τ̂? Responde "quanto histórico faltaria".
    dimensionamento = []
    for n_alvo in N_GRADE_DIMENSIONAMENTO:
        rng_n = np.random.default_rng(SEED + 2000 + n_alvo)
        ns = np.full(len(n_por_vendedor), n_alvo)
        pesos_n = ns / ns.sum()
        homogeneo = rng_n.binomial(ns, base_rate, size=(n_simulacoes, len(ns))) / ns
        medias_h = (homogeneo * pesos_n).sum(axis=1)
        disp_h = np.sqrt((pesos_n * (homogeneo - medias_h[:, None]) ** 2).sum(axis=1))
        critica_n = float(np.percentile(disp_h, 100 * (1 - ALFA)))
        verdadeiras_n = np.clip(
            rng_n.normal(base_rate, tau_excesso, size=(n_simulacoes, len(ns))), 0.02, 0.98
        )
        heterogeneo = rng_n.binomial(ns, verdadeiras_n) / ns
        medias_t = (heterogeneo * pesos_n).sum(axis=1)
        disp_t = np.sqrt((pesos_n * (heterogeneo - medias_t[:, None]) ** 2).sum(axis=1))
        dimensionamento.append(
            PontoDeDimensionamento(
                n_por_vendedor=n_alvo, poder=float((disp_t >= critica_n).mean())
            )
        )

    return PowerReport(
        n_vendedores=len(n_por_vendedor),
        n_fechados=int(len(closed)),
        base_rate=base_rate,
        n_mediano_carteira=n_v,
        spread_observado_pp=spread_observado * 100,
        spread_nulo_mediano_pp=float(np.median(spreads_nulos) * 100),
        spread_nulo_p2_5_pp=float(np.percentile(spreads_nulos, 2.5) * 100),
        spread_nulo_p97_5_pp=float(np.percentile(spreads_nulos, 97.5) * 100),
        dispersao_observada_pp=dispersao_observada * 100,
        dispersao_nula_esperada_pp=float(np.sqrt(var_binomial) * 100),
        tau_excesso_pp=tau_excesso * 100,
        dispersao_critica_pp=critica * 100,
        curva_poder=tuple(curva),
        poder_vendedor_unico=tuple(poder_unico),
        dimensionamento=tuple(dimensionamento),
    )
