"""Gerador de mocks diários com a MESMA estrutura dos CSVs reais (mesmas colunas, nomes e peculiaridades,
ex.: 'GTXPro' no pipeline). Os parâmetros do 'mundo verdadeiro' são estimados dos dados reais:

- risco diário de fechar por idade do deal (Kaplan-Meier com deals abertos como censurados);
- chance de ganhar no fechamento por idade, ajustada pelo histórico do vendedor e do produto;
- volume de leads novos, mix vendedor x produto dos últimos 90 dias, taxa de conta ausente, close_value/preço.

Deals mais velhos que o maior ciclo já visto (zumbis) não têm dado real: usamos uma SUPOSIÇÃO explícita
(ZOMBIE_HAZARD, ZOMBIE_WIN), configurável. Como o 'mundo' é conhecido, dá para calcular a receita esperada
verdadeira em 30 dias de cada deal e comparar com o score — é isso que 'condizente com a realidade' mede.
"""
from __future__ import annotations

import string
from dataclasses import dataclass

import numpy as np
import pandas as pd

MAX_AGE = 1500


def _logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


@dataclass
class WorldParams:
    new_engaging_per_day: float = 20.0
    new_prospecting_per_day: float = 4.0
    prospect_to_engage_per_day: float = 0.006
    zombie_hazard: float = 0.003      # SUPOSIÇÃO: zumbi raramente fecha...
    zombie_win: float = 0.15          # ...e quando fecha, quase sempre perde
    effect_strength: float = 1.0      # força do efeito vendedor/produto (1 = o que se vê no real)


class MockWorld:
    def __init__(self, data_dir, seed: int = 7, params: WorldParams | None = None):
        self.rng = np.random.default_rng(seed)
        self.p = params or WorldParams()
        self.pipe = pd.read_csv(data_dir / "sales_pipeline.csv", dtype=str)
        self.teams = pd.read_csv(data_dir / "sales_teams.csv")
        self.prods = pd.read_csv(data_dir / "products.csv")
        self.accounts = pd.read_csv(data_dir / "accounts.csv")["account"].tolist()
        self._fit()
        self.events: list[dict] = []

    # ------------------------------------------------------------------ estimação a partir do real
    def _fit(self):
        p = self.pipe.copy()
        p["engage_date"] = pd.to_datetime(p["engage_date"])
        p["close_date"] = pd.to_datetime(p["close_date"])
        self.today = max(p["engage_date"].max(), p["close_date"].max())
        closed = p[p["deal_stage"].isin(["Won", "Lost"])]
        dur = (closed["close_date"] - closed["engage_date"]).dt.days.to_numpy()
        self.max_seen = int(dur.max())
        open_age = (self.today - p.loc[p["deal_stage"] == "Engaging", "engage_date"]).dt.days.to_numpy()
        # Kaplan-Meier discreto, suavizado em janelas de 7 dias
        ev = np.bincount(dur, minlength=MAX_AGE)[:MAX_AGE].astype(float)
        cens = np.bincount(np.clip(open_age, 0, MAX_AGE - 1), minlength=MAX_AGE).astype(float)
        at_risk = (ev + cens)[::-1].cumsum()[::-1]
        ev_s = pd.Series(ev).rolling(7, center=True, min_periods=1).mean().to_numpy()
        h = np.divide(ev_s, at_risk, out=np.zeros(MAX_AGE), where=at_risk > 0)
        h[self.max_seen + 1:] = self.p.zombie_hazard
        self.hazard = np.clip(h, 0, 0.5)
        # chance de ganhar no fechamento por idade (janela móvel) + efeitos vendedor/produto encolhidos
        won = (closed["deal_stage"] == "Won").astype(float).to_numpy()
        w = np.bincount(dur, weights=won, minlength=MAX_AGE)[:MAX_AGE]
        n = np.bincount(dur, minlength=MAX_AGE)[:MAX_AGE].astype(float)
        ws = pd.Series(w).rolling(15, center=True, min_periods=1).sum().to_numpy()
        ns = pd.Series(n).rolling(15, center=True, min_periods=1).sum().to_numpy()
        base = won.mean()
        self.win_age = np.where(ns > 0, (ws + 10 * base) / (ns + 10), base)
        self.win_age[self.max_seen + 1:] = self.p.zombie_win
        k = 30
        c = closed.assign(won=won)
        ag = c.groupby("sales_agent")["won"].agg(["sum", "count"])
        pr = c.groupby("product")["won"].agg(["sum", "count"])
        self.agent_eff = (_logit((ag["sum"] + k * base) / (ag["count"] + k)) - _logit(base)).to_dict()
        self.prod_eff = (_logit((pr["sum"] + k * base) / (pr["count"] + k)) - _logit(base)).to_dict()
        # razão close_value / preço dos ganhos, por produto (preço via nome normalizado)
        price = self.prods.set_index("product")["sales_price"].to_dict()
        wonp = closed[closed["deal_stage"] == "Won"]
        ratio = wonp["close_value"].astype(float) / wonp["product"].replace({"GTXPro": "GTX Pro"}).map(price)
        self.ratio = ratio.dropna().to_numpy()
        self.price = price
        recent = p[p["engage_date"] > self.today - pd.Timedelta(days=90)]
        self.mix = recent.groupby(["sales_agent", "product"]).size()
        self.missing_account = p.loc[p["deal_stage"].isin(["Engaging", "Prospecting"]), "account"].isna().mean()

    # ------------------------------------------------------------------ verdade (para validar o score)
    def p_win_close(self, age, agent, product):
        a = np.clip(np.asarray(age, int), 0, MAX_AGE - 1)
        eff = self.p.effect_strength * (np.array([self.agent_eff.get(x, 0) for x in agent])
                                        + np.array([self.prod_eff.get(x, 0) for x in product]))
        z = a > self.max_seen
        out = 1 / (1 + np.exp(-(_logit(self.win_age[a]) + eff)))
        out[z] = self.win_age[a[z]]
        return out

    def true_ev(self, frame: pd.DataFrame, today: pd.Timestamp, h: int = 30) -> pd.Series:
        """Receita esperada VERDADEIRA em h dias para deals Engaging (frame no formato do pipeline)."""
        e = frame[frame["deal_stage"] == "Engaging"]
        age = (today - pd.to_datetime(e["engage_date"])).dt.days.to_numpy()
        prod = e["product"].replace({"GTXPro": "GTX Pro"}).to_numpy()
        price = np.array([self.price[x] for x in prod], float)
        surv, ev = np.ones(len(e)), np.zeros(len(e))
        for t in range(1, h + 1):
            a = np.clip(age + t, 0, MAX_AGE - 1)
            hz = self.hazard[a]
            ev += surv * hz * self.p_win_close(a, e["sales_agent"].to_numpy(), prod)
            surv *= 1 - hz
        return pd.Series(ev * price * self.ratio.mean(), index=e["opportunity_id"].to_numpy())

    # ------------------------------------------------------------------ um dia de operação
    def _new_id(self, used: set) -> str:
        alphabet = np.array(list(string.ascii_uppercase + string.digits))
        while True:
            i = "".join(self.rng.choice(alphabet, 8))
            if i not in used:
                used.add(i)
                return i

    def step(self) -> pd.Timestamp:
        self.today = self.today + pd.Timedelta(days=1)
        day = self.today.strftime("%Y-%m-%d")
        p = self.pipe
        # 1) deals Engaging que fecham hoje
        eng = p.index[p["deal_stage"] == "Engaging"]
        age = (self.today - pd.to_datetime(p.loc[eng, "engage_date"])).dt.days.to_numpy()
        close = self.rng.random(len(eng)) < self.hazard[np.clip(age, 0, MAX_AGE - 1)]
        idx = eng[close]
        prod = p.loc[idx, "product"].replace({"GTXPro": "GTX Pro"}).to_numpy()
        pw = self.p_win_close(age[close], p.loc[idx, "sales_agent"].to_numpy(), prod)
        won = self.rng.random(len(idx)) < pw
        for i, w, pr in zip(idx, won, prod):
            value = int(round(self.price[pr] * self.rng.choice(self.ratio))) if w else 0
            p.loc[i, ["deal_stage", "close_date", "close_value"]] = ["Won" if w else "Lost", day, str(value)]
            if p.loc[i, "account"] != p.loc[i, "account"]:      # fechado sempre tem conta no real
                p.loc[i, "account"] = self.rng.choice(self.accounts)
            self.events.append({"date": day, "opportunity_id": p.loc[i, "opportunity_id"],
                                "event": "won" if w else "lost", "value": value})
        # 2) Prospecting que viram Engaging
        pros = p.index[p["deal_stage"] == "Prospecting"]
        move = pros[self.rng.random(len(pros)) < self.p.prospect_to_engage_per_day]
        p.loc[move, ["deal_stage", "engage_date"]] = ["Engaging", day]
        self.events += [{"date": day, "opportunity_id": p.loc[i, "opportunity_id"], "event": "engaged", "value": 0}
                        for i in move]
        # 3) leads novos (mesmo mix vendedor x produto dos últimos 90 dias)
        used = set(p["opportunity_id"])
        rows = []
        for stage, lam in (("Engaging", self.p.new_engaging_per_day), ("Prospecting", self.p.new_prospecting_per_day)):
            n = self.rng.poisson(lam)
            pick = self.rng.choice(len(self.mix), n, p=(self.mix / self.mix.sum()).to_numpy())
            for j in pick:
                agent, product = self.mix.index[j]
                acc = None if self.rng.random() < self.missing_account else self.rng.choice(self.accounts)
                oid = self._new_id(used)
                rows.append({"opportunity_id": oid, "sales_agent": agent, "product": product, "account": acc,
                             "deal_stage": stage, "engage_date": day if stage == "Engaging" else None,
                             "close_date": None, "close_value": None})
                self.events.append({"date": day, "opportunity_id": oid, "event": f"new_{stage.lower()}", "value": 0})
        self.pipe = pd.concat([p, pd.DataFrame(rows, columns=p.columns)], ignore_index=True)
        return self.today

    def write(self, data_dir) -> None:
        self.pipe.to_csv(data_dir / "sales_pipeline.csv", index=False)
