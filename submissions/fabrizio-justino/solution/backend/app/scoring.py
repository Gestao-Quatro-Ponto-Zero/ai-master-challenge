"""Motor de scoring: benchmarks tirados do histórico + score 0-100 de PRIORIDADE de
cada deal aberto, com cada ponto explicado em linguagem de vendedor.

O que a EDA e o backtest mostraram (ver docs/README.md, seção Lógica):
- "Este deal vai ganhar algum dia?" não é previsível neste dataset: vendedor, conta,
  produto, setor, histórico da conta e afinidade dão AUC 0,49–0,52 (cara ou coroa).
- "Este deal vai ganhar ATÉ O FIM DO TRIMESTRE?" é: a chance empírica dada a idade do
  deal e os dias que faltam tem AUC ≈ 0,75. É o único sinal real — e é exatamente a
  pergunta da segunda-feira de manhã.

Por isso o score = chance calibrada no horizonte (60) + valor (25) + engajamento e
qualidade de dado (15). A chance vem de chance_bruta (estimador com censura) e passa
pela recalibração isotônica do backtest (calibracao.py) antes de virar probabilidade."""
import math
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np
import pandas as pd

from . import config
from .dados import Dados

ORDEM_ACOES = ["Atacar agora", "Nutrir", "Primeiro contato", "Requalificar", "Encerrar", "Baixa prioridade"]
Z_95 = 1.96


def wilson(sucessos: float, n: float, z: float = Z_95) -> tuple[float, float]:
    """Intervalo de Wilson (95%) para uma proporção — estável mesmo com n pequeno."""
    if n <= 0:
        return 0.0, 1.0
    p = sucessos / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    meia = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centro - meia), min(1.0, centro + meia)


@dataclass
class Horizonte:
    """Até quando a chance é medida: o fim do trimestre atual — ou o do próximo, se
    faltam menos de HORIZONTE_MIN_DIAS (no último dia do trimestre, a pergunta útil é
    sobre o trimestre que começa amanhã)."""
    fim: pd.Timestamp
    dias: int

    @property
    def rotulo(self) -> str:
        return self.fim.strftime("%d/%m/%Y")


def horizonte(t: pd.Timestamp) -> Horizonte:
    fim = t.to_period("Q").end_time.normalize()
    if (fim - t).days < config.HORIZONTE_MIN_DIAS:
        fim = (t.to_period("Q") + 1).end_time.normalize()
    return Horizonte(fim, (fim - t.normalize()).days)


@dataclass
class Benchmarks:
    win_rate_geral: float
    zona_risco_dias: int            # mediana de duração dos deals perdidos
    pct_perdidos_na_zona: float     # % dos perdidos que morreram até zona_risco_dias
    ciclo_max_dias: int             # maior duração de um deal fechado
    ciclo_p75_produto: dict         # produto → P75 da duração dos ganhos
    ciclo_mediano_produto: dict     # produto → mediana da duração dos ganhos
    win_agente: dict                # agente → taxa suavizada (usado na redistribuição)
    win_agente_produto: dict        # (agente, produto) → taxa suavizada pra taxa do agente
    desconto_produto: dict          # produto → média de close_value/sales_price nos ganhos
    preco_min: float
    preco_max: float
    ranking_preco: dict             # produto → posição (1 = mais caro)
    win_fim_trimestre: float
    win_fora_trimestre: float
    # Insumos do estimador de chance (ver chance_bruta)
    duracoes: np.ndarray = field(repr=False, default=None)
    ganhou: np.ndarray = field(repr=False, default=None)
    idades_abertas: np.ndarray = field(repr=False, default=None)
    _cache_chance: dict = field(repr=False, default_factory=dict)

    def chance_bruta(self, idade: int, dias: int) -> float:
        """P(ganhar nos próximos `dias` | o deal já sobreviveu `idade` dias), só com o
        que se sabia na data de referência.

        Numerador: deals fechados que passaram de `idade` e GANHARAM até idade+dias.
        Denominador: todos que passaram de `idade` com desfecho conhecido na janela —
        os fechados, mais os ainda abertos que já passaram de idade+dias sem fechar
        (censura). Sem esse segundo termo o estimador ignora os deals que nunca
        fecham e fica otimista demais (achado no backtest: previa 80%, real 30%)."""
        num, den = self.chance_contagem(idade, dias)
        return float(num / den) if den else 0.0

    def chance_contagem(self, idade: int, dias: int) -> tuple[int, int]:
        """(ganhos na janela, deals com desfecho conhecido na janela) — ver chance_bruta.
        O denominador é a base do intervalo de incerteza."""
        chave = (idade, dias)
        if chave not in self._cache_chance:
            vivos = self.duracoes > idade
            num = int(((self.ganhou == 1) & vivos & (self.duracoes <= idade + dias)).sum())
            den = int(vivos.sum() + (self.idades_abertas >= idade + dias).sum())
            self._cache_chance[chave] = (num, den)
        return self._cache_chance[chave]


def _taxa(soma: float, n: float, prior: float, k: int = config.SUAVIZACAO_K) -> float:
    return (soma + k * prior) / (n + k)


def calcular_benchmarks(dados: Dados) -> Benchmarks:
    f = dados.fechados
    g = float(f.ganhou.mean())
    perdidos = f[f.ganhou == 0]
    ganhos = f[f.ganhou == 1]
    zona = int(perdidos.duracao_dias.median())

    agg_agente = f.groupby("sales_agent").ganhou.agg(["sum", "count"])
    win_agente = {a: _taxa(r["sum"], r["count"], g) for a, r in agg_agente.iterrows()}
    agp = f.groupby(["sales_agent", "product"]).ganhou.agg(["sum", "count"])
    win_agente_produto = {(a, p): _taxa(r["sum"], r["count"], win_agente[a]) for (a, p), r in agp.iterrows()}

    precos = f.drop_duplicates("product").set_index("product").sales_price
    trimestre = f.close_date.dt.month.isin([3, 6, 9, 12])
    engajados = dados.abertos.engage_date.dropna()

    return Benchmarks(
        win_rate_geral=g,
        zona_risco_dias=zona,
        pct_perdidos_na_zona=float((perdidos.duracao_dias <= zona).mean()),
        ciclo_max_dias=int(f.duracao_dias.max()),
        ciclo_p75_produto={p: int(round(v)) for p, v in ganhos.groupby("product").duracao_dias.quantile(0.75).items()},
        ciclo_mediano_produto={p: int(round(v)) for p, v in ganhos.groupby("product").duracao_dias.median().items()},
        win_agente=win_agente,
        win_agente_produto=win_agente_produto,
        desconto_produto=(ganhos.close_value / ganhos.sales_price).groupby(ganhos["product"]).mean().to_dict(),
        preco_min=float(precos.min()),
        preco_max=float(precos.max()),
        ranking_preco=precos.rank(ascending=False).astype(int).to_dict(),
        win_fim_trimestre=float(f[trimestre].ganhou.mean()),
        win_fora_trimestre=float(f[~trimestre].ganhou.mean()),
        duracoes=f.duracao_dias.to_numpy(),
        ganhou=f.ganhou.to_numpy(),
        idades_abertas=(dados.data_referencia - engajados).dt.days.to_numpy(),
    )


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def usd(x: float) -> str:
    """US$ no formato brasileiro de milhar (26.768)."""
    return "US$ " + f"{x:,.0f}".replace(",", ".")


def _motivo(pilar: str, pontos: float, texto: str, tom: str) -> dict:
    """tom: 'positivo' | 'neutro' | 'negativo' — só pra cor na interface."""
    return {"pilar": pilar, "pontos": round(pontos, 1), "maximo": config.PESOS[pilar], "texto": texto, "tom": tom}


def _contexto_ciclo(deal, idade: int, bm: Benchmarks) -> str:
    """Frase curta dizendo em que fase do ciclo o deal está."""
    teto = bm.ciclo_max_dias
    if idade > teto:
        return f"Passou {idade - teto} dias do maior ciclo que já fechou ({teto}d) — nenhum deal ganhou nessa idade."
    if idade <= bm.zona_risco_dias:
        return (f"Fase de maior risco: {_pct(bm.pct_perdidos_na_zona)} dos deals perdidos morrem até o "
                f"{bm.zona_risco_dias}º dia — um follow-up agora decide.")
    p75 = bm.ciclo_p75_produto.get(deal["product"], teto)
    if idade > p75:
        return f"Reta final: faltam {teto - idade} dias para o maior ciclo já fechado — hora de pedir a decisão."
    return "Dentro do ciclo típico do produto."


def _pilar_chance(deal, idade: Optional[int], prob: Optional[float], prob_max: float, hz: Horizonte, bm: Benchmarks) -> dict:
    w = config.PESOS["chance"]
    if prob is None:
        # Não mostrar um número que sabemos ser otimista: Prospecting não tem data de
        # engajamento no CRM, então não existe histórico comparável para estimar.
        return _motivo("chance", 0.0, "Chance n/d: o deal ainda está em Prospecting, sem data de engajamento — "
                                      "o relógio do ciclo só começa no primeiro contato.", "neutro")
    pontos = w * min(1.0, prob / prob_max) if prob_max else 0.0
    texto = (f"Chance de ganhar até {hz.rotulo}: {_pct(prob)} — o que aconteceu no histórico com deals de "
             f"{idade} dias quando faltavam {hz.dias} dias. {_contexto_ciclo(deal, idade, bm)}")
    tom = "negativo" if idade > bm.ciclo_max_dias or prob < 0.15 else "positivo" if pontos >= 0.6 * w else "neutro"
    return _motivo("chance", pontos, texto, tom)


def _pilar_valor(deal, bm: Benchmarks) -> dict:
    w = config.PESOS["valor"]
    preco = float(deal.sales_price)
    # Escala log: o catálogo vai de US$55 a US$26.768 (500×) — em escala linear, o GTK
    # 500 engoliria qualquer outro critério.
    frac = (math.log(preco) - math.log(bm.preco_min)) / (math.log(bm.preco_max) - math.log(bm.preco_min))
    pos = bm.ranking_preco.get(deal["product"])
    tom = "positivo" if frac >= 0.6 else "neutro" if frac >= 0.3 else "negativo"
    return _motivo("valor", w * frac, f"{deal['product']} — {usd(preco)}, {pos}º maior ticket do catálogo.", tom)


def _pilar_dados(deal) -> dict:
    w = config.PESOS["dados"]
    engajado = deal.deal_stage == "Engaging"
    tem_conta = isinstance(deal.account, str)
    pontos = (0.6 * w if engajado else 0.15 * w) + (0.4 * w if tem_conta else 0)
    partes = ["Cliente já engajado" if engajado else "Ainda sem engajamento",
              "conta preenchida" if tem_conta else "conta NÃO preenchida no CRM"]
    tom = "positivo" if engajado and tem_conta else "negativo" if not tem_conta else "neutro"
    return _motivo("dados", pontos, "; ".join(partes) + ".", tom)


def _acao(stage: str, idade: Optional[int], preco: float, score: int, cortes: dict, bm: Benchmarks) -> str:
    if stage == "Prospecting" or idade is None:
        # Trilha própria: sem data de engajamento não há chance honesta para mostrar
        return "Primeiro contato"
    if idade > bm.ciclo_max_dias:
        # Fora do ciclo a chance é ZERO como está, caro ou barato (0 de 13.871 no backtest).
        # "Requalificar" = perguntar ao cliente; se o projeto continua, encerrar este e abrir
        # uma oportunidade NOVA, com o relógio zerado. Barato não compensa a conversa.
        return "Requalificar" if preco >= config.REQUALIFICAR_PRECO_MIN else "Encerrar"
    if score >= cortes["atacar"]:
        return "Atacar agora"
    if score >= cortes["nutrir"]:
        return "Nutrir"
    return "Baixa prioridade"


def cortes_de_score(scores_vivos: pd.Series) -> dict:
    """Score mínimo de 'Atacar agora' e 'Nutrir' na data (percentis dos deals vivos)."""
    if scores_vivos.empty:
        return {"atacar": 101, "nutrir": 101}
    return {"atacar": int(np.ceil(scores_vivos.quantile(config.PERCENTIL_ATACAR))),
            "nutrir": int(np.ceil(scores_vivos.quantile(config.PERCENTIL_NUTRIR)))}


Calibrador = Callable[[float], float]


def _identidade(p: float) -> float:
    return p


def pontuar(dados: Dados, bm: Benchmarks, calibrar: Calibrador = _identidade) -> pd.DataFrame:
    """1 linha por deal aberto, ordenado por ação e valor esperado.

    `calibrar` transforma a chance bruta em probabilidade calibrada (vem do backtest).
    Duas probabilidades por deal:
    - `probabilidade`: até o fim do HORIZONTE (o que o score usa);
    - `prob_trimestre`: até o fim do trimestre ATUAL (o que a meta/emergência usa).
    Na maior parte do tempo são iguais; diferem só nos últimos dias do trimestre."""
    ref = dados.data_referencia
    hz = horizonte(ref)
    dias_tri = (ref.to_period("Q").end_time.normalize() - ref.normalize()).days
    abertos = dados.abertos

    def chance(idade: int, dias: int) -> float:
        return calibrar(bm.chance_bruta(idade, dias)) if dias > 0 else 0.0

    def faixa(idade: int, dias: int) -> tuple[float, float]:
        """Wilson sobre a contagem bruta daquela idade, levado pela mesma calibração
        (monotônica, então os limites continuam em ordem)."""
        if dias <= 0:
            return 0.0, 0.0
        lo, hi = wilson(*bm.chance_contagem(idade, dias))
        return calibrar(lo), calibrar(hi)

    idades = [None if pd.isna(e) else int((ref - e).days) for e in abertos.engage_date]
    # Prospecting (sem idade): chance n/d (None). Fora do ciclo: chance 0.
    probs = [None if i is None else 0.0 if i > bm.ciclo_max_dias else chance(i, hz.dias) for i in idades]
    # Referência dos pontos de chance: a maior chance possível neste horizonte
    prob_max = max([chance(i, hz.dias) for i in range(bm.ciclo_max_dias + 1)] + [1e-9])

    linhas = []
    for (_, deal), idade, prob in zip(abertos.iterrows(), idades, probs):
        motivos = [_pilar_chance(deal, idade, prob, prob_max, hz, bm), _pilar_valor(deal, bm), _pilar_dados(deal)]
        score = int(round(sum(m["pontos"] for m in motivos)))
        fora = idade is not None and idade > bm.ciclo_max_dias
        valor_liquido = float(deal.sales_price) * bm.desconto_produto.get(deal["product"], 1.0)
        vivo = idade is not None and not fora
        prob_tri = (prob if dias_tri == hz.dias else chance(idade, dias_tri)) if vivo else 0.0
        prob_min, prob_max_deal = faixa(idade, hz.dias) if vivo else (None, None)
        linhas.append({
            "opportunity_id": deal.opportunity_id,
            "agente": deal.sales_agent,
            "manager": deal.manager,
            "regiao": deal.regional_office,
            "produto": deal["product"],
            "serie": deal.series,
            "conta": deal.account if isinstance(deal.account, str) else None,
            "setor": deal.sector if isinstance(deal.sector, str) else None,
            "stage": deal.deal_stage,
            "engage_date": None if idade is None else deal.engage_date.date().isoformat(),
            "idade_dias": idade,
            "fora_do_ciclo": fora,
            "valor": float(deal.sales_price),
            # Deal aberto não tem close_value: preço de tabela × desconto histórico do produto
            "valor_liquido": round(valor_liquido),
            "probabilidade": None if prob is None else round(prob, 3),
            "prob_min": None if prob_min is None else round(prob_min, 3),
            "prob_max": None if prob_max_deal is None else round(prob_max_deal, 3),
            # Prospecting não entra no valor esperado: não há chance honesta para multiplicar
            "valor_esperado": round((prob or 0.0) * valor_liquido),
            "prob_trimestre": round(prob_tri, 3),
            "valor_esperado_trimestre": round(prob_tri * valor_liquido),
            "score": score,
            # Ordem de exibição: o que mais pesou primeiro
            "motivos": sorted(motivos, key=lambda m: m["pontos"] / m["maximo"], reverse=True),
        })

    df = pd.DataFrame(linhas)
    if df.empty:
        return df
    vivos = (df.stage == "Engaging") & ~df.fora_do_ciclo
    cortes = cortes_de_score(df.loc[vivos, "score"])
    df["acao"] = [_acao(s, None if pd.isna(i) else int(i), p, sc, cortes, bm)
                  for s, i, p, sc in zip(df.stage, df.idade_dias, df.valor, df.score)]
    df["idade_dias"] = df.idade_dias.astype("Int64")  # Prospecting não tem idade → sem virar float
    # Ordena pela AÇÃO antes do resto: um zumbi caro não pode aparecer acima de um deal
    # saudável. Dentro da ação, o que vale mais em valor esperado vem primeiro.
    df["_ordem"] = df.acao.map({a: i for i, a in enumerate(ORDEM_ACOES)})
    df = df.sort_values(["_ordem", "valor_esperado", "score"], ascending=[True, False, False])
    df = df.drop(columns="_ordem").reset_index(drop=True)
    df.attrs["cortes"] = cortes  # o motor guarda na Visao (aparece em /benchmarks)
    return df
