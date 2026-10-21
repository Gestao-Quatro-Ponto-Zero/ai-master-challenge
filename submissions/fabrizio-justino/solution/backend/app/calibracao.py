"""Calibração por backtest, rolling-origin — a prova de que a chance (e o score) funciona.

Para cada segunda-feira do histórico: reconstrói o pipeline como ele estava naquele
dia (dados.snapshot), calcula benchmarks SÓ com o que já se sabia, estima a chance
bruta de cada deal aberto ganhar até o fim do horizonte e guarda o que de fato
aconteceu. Agrupando por faixa de chance prevista, dá pra ver se "40%" de fato ganhou
~40% das vezes.

O estimador bruto é otimista nas faixas altas, então a taxa real de cada faixa
(forçada a ser crescente — isotônica) vira a função de calibração.

Rolling-origin: a calibração usada numa data t só enxerga observações cujo desfecho
já era conhecido em t (horizonte terminado até t). Simular 04/12/2017 não usa nada
que aconteceu depois de 04/12/2017. Sem histórico suficiente (início do dataset), a
chance bruta é usada sem calibração e a interface avisa.

Também mede a regra do teto: quantos deals que já tinham passado do maior ciclo
fechado acabaram ganhando depois (esperado: ~0)."""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .dados import Dados, snapshot
from .scoring import calcular_benchmarks, horizonte

LARGURA_FAIXA = 0.05
# Abaixo disso a curva fica instável demais — melhor assumir "sem calibração"
MIN_OBSERVACOES = 3000


@dataclass
class Calibracao:
    data_corte: str
    calibrada: bool
    curva: list             # [{de, ate, previsto, real, calibrado, n}]
    auc: float              # entre deals vivos (dentro do ciclo)
    auc_com_teto: float     # pipeline inteiro, com a regra "fora do ciclo = chance 0"
    n_observacoes: int
    datas: list
    zumbis_observados: int
    zumbis_que_ganharam: int
    _x: np.ndarray = field(repr=False, default=None)
    _y: np.ndarray = field(repr=False, default=None)

    def __call__(self, chance_bruta: float) -> float:
        """Chance bruta → probabilidade calibrada (interpolação monotônica)."""
        if not self.calibrada:
            return float(chance_bruta)
        return float(np.interp(chance_bruta, self._x, self._y))


def _isotonica(taxas: np.ndarray, pesos: np.ndarray) -> np.ndarray:
    """Pool-adjacent-violators: menor ajuste que deixa a sequência não-decrescente."""
    blocos = [[t, w, 1] for t, w in zip(taxas, pesos)]
    i = 0
    while i < len(blocos) - 1:
        if blocos[i][0] > blocos[i + 1][0]:
            t1, w1, n1 = blocos[i]
            t2, w2, n2 = blocos.pop(i + 1)
            w = w1 + w2
            blocos[i] = [(t1 * w1 + t2 * w2) / w if w else (t1 + t2) / 2, w, n1 + n2]
            i = max(i - 1, 0)
        else:
            i += 1
    return np.concatenate([[t] * n for t, _, n in blocos])


def auc(y: np.ndarray, s: np.ndarray) -> float:
    """Área sob a curva ROC via ranks (empates recebem rank médio)."""
    rank = pd.Series(s).rank(method="average").to_numpy()
    pos = y == 1
    n_pos, n_neg = pos.sum(), (~pos).sum()
    return float((rank[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)) if n_pos and n_neg else 0.5


def datas_backtest(dados: Dados) -> list:
    p = dados.pipeline
    fim = p.close_date.max()
    inicio = p.close_date.min() + pd.offsets.MonthBegin(1)
    return [t for t in pd.date_range(inicio, fim, freq="W-MON") if horizonte(t).fim <= fim]


@dataclass
class Backtest:
    """Todas as observações do backtest; `para_data` ajusta a calibração de uma data."""
    obs: pd.DataFrame       # chance, ganhou, t, fim (fim = quando o desfecho fica conhecido)
    zumbis: pd.DataFrame    # ganhou (algum dia), ganhou_no_prazo, t, fim
    _cache: dict = field(default_factory=dict, repr=False)

    def para_data(self, t: pd.Timestamp) -> Calibracao:
        chave = pd.Timestamp(t).normalize()
        if chave not in self._cache:
            self._cache[chave] = self._ajustar(chave)
        return self._cache[chave]

    def _ajustar(self, t: pd.Timestamp) -> Calibracao:
        bt = self.obs[self.obs.fim <= t]
        zb = self.zumbis[self.zumbis.fim <= t]
        datas = sorted(bt.t.unique())
        base = dict(
            data_corte=t.date().isoformat(), n_observacoes=len(bt),
            datas=[pd.Timestamp(d).date().isoformat() for d in datas],
            zumbis_observados=len(zb), zumbis_que_ganharam=int(zb.ganhou.sum()),
            auc=round(auc(bt.ganhou.to_numpy(), bt.chance.to_numpy()), 3) if len(bt) else 0.5,
            auc_com_teto=round(auc(np.concatenate([bt.ganhou.to_numpy(), zb.ganhou_no_prazo.to_numpy()]),
                                   np.concatenate([bt.chance.to_numpy(), np.zeros(len(zb))])), 3) if len(bt) else 0.5,
        )
        if len(bt) < MIN_OBSERVACOES:
            return Calibracao(calibrada=False, curva=[], **base)

        n_faixas = int(round(1 / LARGURA_FAIXA))
        faixa = np.minimum((bt.chance / LARGURA_FAIXA).astype(int), n_faixas - 1)
        agg = bt.groupby(faixa).agg(previsto=("chance", "mean"), real=("ganhou", "mean"), n=("ganhou", "size"))
        calibrado = _isotonica(agg.real.to_numpy(), agg.n.to_numpy(dtype=float))
        curva = [
            {"de": round(i * LARGURA_FAIXA, 2), "ate": round((i + 1) * LARGURA_FAIXA, 2),
             "previsto": round(float(r.previsto), 3), "real": round(float(r.real), 3),
             "calibrado": round(float(c), 3), "n": int(r.n)}
            for (i, r), c in zip(agg.iterrows(), calibrado)
        ]
        # Âncoras da interpolação: chance 0 → 0 e o centro (previsto médio) de cada faixa
        x = np.concatenate([[0.0], agg.previsto.to_numpy()])
        y = np.maximum.accumulate(np.concatenate([[0.0], calibrado]))
        return Calibracao(calibrada=True, curva=curva, _x=x, _y=y, **base)


def calibrar(dados: Dados) -> Backtest:
    real = dados.pipeline.set_index("opportunity_id")[["deal_stage", "close_date"]]
    obs, zumbis = [], []
    for t in datas_backtest(dados):
        snap = snapshot(dados, t)
        bm = calcular_benchmarks(snap)
        hz = horizonte(t)
        ab = snap.abertos[snap.abertos.engage_date.notna()]
        idades = (t - ab.engage_date).dt.days.to_numpy()
        r = real.loc[ab.opportunity_id]
        ganhou = r.deal_stage.to_numpy() == "Won"
        ganhou_no_prazo = ganhou & (r.close_date.to_numpy() <= np.datetime64(hz.fim))
        zumbi = idades > bm.ciclo_max_dias
        # Desfecho "ganhou algum dia" de um zumbi só é conhecido no fim do dataset; para a
        # contagem da regra do teto usamos o fim do horizonte, como nas outras observações.
        zumbis.append(pd.DataFrame({"ganhou": ganhou[zumbi].astype(int), "ganhou_no_prazo": ganhou_no_prazo[zumbi].astype(int),
                                    "t": t, "fim": hz.fim}))
        vivos = ~zumbi
        obs.append(pd.DataFrame({"chance": [bm.chance_bruta(int(i), hz.dias) for i in idades[vivos]],
                                 "ganhou": ganhou_no_prazo[vivos].astype(int), "t": t, "fim": hz.fim}))
    return Backtest(pd.concat(obs, ignore_index=True), pd.concat(zumbis, ignore_index=True))
