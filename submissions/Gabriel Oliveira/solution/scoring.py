"""
Módulo de scoring do Lead Scorer — Challenge 003.

Filosofia (ver docs/HARNESS.md, seção 5):
- Explainability-first: cada score explica-se em PT-BR para não-técnicos
- Regras + heurísticas > ML black-box (regulamento do challenge diz isso)
- Cada componente tem hipótese de negócio documentada na docstring

Autor: Gabriel Oliveira
Data: 06/07/2026
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class ScoreComponent:
    """Um componente do score final, explicável."""
    name: str
    label_ptbr: str            # texto curto para vendedor ler
    raw_value: float           # valor bruto da feature
    subscore: float            # 0-100 (normalizado)
    weight: float              # peso no score final (soma 1.0)
    contribution: float = field(default=0.0)  # subscore * weight

    def __post_init__(self) -> None:
        self.contribution = self.subscore * self.weight


@dataclass
class DealScore:
    """Resultado de score_deal: score total + breakdown."""
    opportunity_id: str
    total_score: float                        # 0-100
    components: list[ScoreComponent]
    summary_ptbr: str                         # frase em linguagem natural

    def to_dict(self) -> dict:
        return {
            "opportunity_id": self.opportunity_id,
            "total_score": round(self.total_score, 1),
            "summary": self.summary_ptbr,
            "components": [
                {
                    "name": c.name,
                    "label": c.label_ptbr,
                    "raw_value": round(c.raw_value, 3),
                    "subscore": round(c.subscore, 1),
                    "weight": c.weight,
                    "contribution": round(c.contribution, 1),
                }
                for c in self.components
            ],
        }


# --- Normalization helpers -------------------------------------------------

def _minmax(value: float, lo: float, hi: float) -> float:
    """Normaliza valor para 0-100 com clamp. Robusto a hi==lo e a NaN."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 0.0
    if hi <= lo:
        return 50.0
    clipped = max(lo, min(hi, value))
    return float((clipped - lo) / (hi - lo) * 100.0)


def _num(value: object, default: float = 0.0) -> float:
    """Coage valor para float tratando None/NaN (comum em merges com dados reais)."""
    if value is None:
        return default
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    return default if np.isnan(f) else f


# --- Configuração de pesos (decisão humana — ver HARNESS.md seção 5.3) ----

WEIGHTS = {
    "stage":        0.25,  # Engaging > Prospecting — sinaliza avanço real
    "velocity":     0.20,  # maturidade vs. esfriamento do deal no pipeline
    "account_size": 0.20,  # contas maiores = deals maiores e mais estratégicos
    "product_value":0.15,  # ticket alto = payoff maior se fechar
    "agent_record": 0.15,  # historic do vendedor importa tanto quanto product
    "deal_value":   0.05,  # valor esperado do próprio deal (5% — não é só valor)
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "pesos devem somar 1.0"


# --- Função principal de scoring ------------------------------------------

def score_deal(
    row: pd.Series,
    agent_winrate: dict[str, float],
    today: pd.Timestamp,
    velocity_optimal_days: int = 30,
    velocity_max_days: int = 120,
    account_revenue_cap: float = 5_000.0,   # revenue em milhoes de USD (~p90 real)
    account_employees_cap: float = 10_000,  # funcionarios (~p90 real)
) -> DealScore:
    """
    Calcula score 0-100 para um deal + breakdown explicável.

    Decisões e pesos documentadas em docs/HARNESS.md seção 5.3.

    Parâmetros
    ----------
    row : pd.Series
        Uma linha de sales_pipeline.csv (com cols esperadas).
    agent_winrate : dict[str, float]
        Win rate [0,1] por sales_agent, calculado do histórico.
    today : pd.Timestamp
        "Hoje" — usado para calcular idade do deal em dias.
    velocity_optimal_days : int
        Idade considerada ótima para um deal aberto (não muito novo, não muito velho).
    velocity_max_days : int
        Idade a partir da qual o deal está claramente esfriando.

    Retorna
    -------
    DealScore com componentes + summary em PT-BR.
    """
    components: list[ScoreComponent] = []

    # ---- 1) Stage advancement (25%) ----
    # Hipótese: Engaging > Prospecting porque representa contato efetivo.
    stage_scores = {"Engaging": 90.0, "Prospecting": 35.0}
    # Won/Lost não recebem score de priorização ativa (fora do pipeline aberto),
    # mas mantemos para completude: Won=100, Lost=0.
    if row["deal_stage"] == "Won":
        stage_sub = 100.0
    elif row["deal_stage"] == "Lost":
        stage_sub = 0.0
    else:
        stage_sub = stage_scores.get(row["deal_stage"], 50.0)
    components.append(ScoreComponent(
        name="stage",
        label_ptbr=f"Estágio: {row['deal_stage']}",
        raw_value=stage_sub,
        subscore=stage_sub,
        weight=WEIGHTS["stage"],
    ))

    # ---- 2) Pipeline velocity (20%) ----
    # Hipótese: deals muito novos (<optimal) ainda maturando; muito velhos (>max) esfriando.
    # Shape triangular: 0 em 0 dias, 100 no ótimo, decai para 0 em max.
    # engage_date já vem convertido para datetime pelo caller (SPEC seção 6 item 6).
    engage = row.get("engage_date")
    age_days: float = -1.0
    if engage is None or (isinstance(engage, float) and pd.isna(engage)) or pd.isna(engage):
        velocity_sub = 0.0
        velocity_label = "Idade: sem data de engajamento — priorizar definir próximo contato"
    else:
        age_days = float((today - engage).days)
        if age_days <= 0:
            velocity_sub = 20.0  # deal novo, ainda não maturou
        elif age_days <= velocity_optimal_days:
            velocity_sub = 20.0 + (age_days / velocity_optimal_days) * 80.0
        else:
            excess = age_days - velocity_optimal_days
            decay = max(0.0, 1.0 - excess / (velocity_max_days - velocity_optimal_days))
            velocity_sub = 100.0 * decay
        velocity_label = f"Idade: {int(age_days)} dias no pipeline"
    components.append(ScoreComponent(
        name="velocity",
        label_ptbr=velocity_label,
        raw_value=age_days,
        subscore=velocity_sub,
        weight=WEIGHTS["velocity"],
    ))

    # ---- 3) Account size (20%) ----
    # Hipótese: contas maiores (receita + funcionários) geram deals maiores e estratégicos.
    # Recebido via df_accounts merge antecipado em row: 'revenue', 'employees'
    # Dados reais: revenue esta em MILHOES de USD (metadata.csv); muitos deals sem
    # account associado (~16%) caem com revenue/employees = 0 (fallback abaixo).
    rev = _num(row.get("revenue"))
    emp = _num(row.get("employees"))
    rev_sub = _minmax(rev, 0, account_revenue_cap)
    emp_sub = _minmax(emp, 0, account_employees_cap)
    acct_sub = (rev_sub * 0.6 + emp_sub * 0.4)  # receita pesa mais
    if rev > 0 or emp > 0:
        acct_label = f"Conta: receita US$ {rev:,.0f}M, {emp:.0f} funcionários"
    else:
        acct_label = "Conta: sem cadastro vinculado — enriquecer dados da conta"
    components.append(ScoreComponent(
        name="account_size",
        label_ptbr=acct_label,
        raw_value=rev,
        subscore=acct_sub,
        weight=WEIGHTS["account_size"],
    ))

    # ---- 4) Product value (15%) ----
    # Hipótese: produtos de ticket maior justificam mais atenção.
    price = _num(row.get("sales_price"))
    # Calibração: cap no produto mais caro do catálogo real (GTK 500 = US$ 26.768)
    prod_sub = _minmax(price, 0, 26_768)
    components.append(ScoreComponent(
        name="product_value",
        label_ptbr=f"Produto: {row.get('product','?')} — ticket ${price:,.0f}",
        raw_value=price,
        subscore=prod_sub,
        weight=WEIGHTS["product_value"],
    ))

    # ---- 5) Agent track record (15%) ----
    # Hipótese do AI Master: quem está vendendo importa tanto quanto o que.
    # Esta feature é frequentemente ignorada por prompts genéricos de IA.
    agent = row["sales_agent"]
    if agent in agent_winrate:
        wr = agent_winrate[agent]
        agent_label = f"Vendedor: {agent} — win rate {wr*100:.0f}%"
    else:
        # SPEC edge E5: agente novo sem histórico
        wr = 0.5
        agent_label = f"Vendedor: {agent} — novo, sem histórico ainda"
    agent_sub = _minmax(wr, 0.50, 0.72)  # range real observado na EDA (0.55-0.70)
    components.append(ScoreComponent(
        name="agent_record",
        label_ptbr=agent_label,
        raw_value=wr,
        subscore=agent_sub,
        weight=WEIGHTS["agent_record"],
    ))

    # ---- 6) Deal value (5%) ----
    # Peso baixo de propósito — o challenge avisa contra "só ordenar por valor".
    close_val = _num(row.get("close_value"))
    deal_sub = _minmax(close_val, 0, 30_288)  # max close_value real do pipeline
    components.append(ScoreComponent(
        name="deal_value",
        label_ptbr=f"Valor esperado do deal: ${close_val:,.0f}",
        raw_value=close_val,
        subscore=deal_sub,
        weight=WEIGHTS["deal_value"],
    ))

    total = sum(c.contribution for c in components)

    # ---- Summary em PT-BR para o vendedor ----
    top = sorted(components, key=lambda c: c.contribution, reverse=True)[:2]
    bottom = sorted(components, key=lambda c: c.contribution)[:1]
    parts = [f"score {total:.0f}/100"]
    if top:
        parts.append("puxado por " + " + ".join(c.label_ptbr for c in top))
    if bottom:
        parts.append("atenção: " + bottom[0].label_ptbr)
    summary = " — ".join(parts)

    return DealScore(
        opportunity_id=row["opportunity_id"],
        total_score=total,
        components=components,
        summary_ptbr=summary,
    )


# --- Batch scoring sobre um DataFrame --------------------------------------

def score_pipeline(
    pipeline: pd.DataFrame,
    accounts: pd.DataFrame,
    products: pd.DataFrame,
    sales_teams: pd.DataFrame,
    today: Optional[pd.Timestamp] = None,
    only_open: bool = True,
) -> pd.DataFrame:
    """
    Aplica score_deal em todo o pipeline e devolve DataFrame com score + breakdown.

    Passos:
    1. Merge pipeline <-> accounts e products (traz revenue, employees, sales_price)
    2. Calcula agent_winrate do histórico (só Won+Lost)
    3. Filtra deals abertos (Prospecting/Engaging) por padrão
    4. Aplica score_deal linha a linha
    5. Explode componentes em formato amigável para UI
    """
    today = today or pd.Timestamp.now().normalize()

    # SPEC seção 6 item 6: caller é responsável por converter datas com formato explícito.
    # Dados reais do challenge (CRM Sales) usam ISO 8601: format='%Y-%m-%d'.
    pipeline = pipeline.copy()
    pipeline["engage_date"] = pd.to_datetime(
        pipeline["engage_date"], format="%Y-%m-%d", errors="coerce"
    )
    pipeline["close_date"] = pd.to_datetime(
        pipeline["close_date"], format="%Y-%m-%d", errors="coerce"
    )

    # Data quality real: o pipeline traz "GTXPro" onde o catálogo tem "GTX Pro"
    # (typo conhecido do dataset). Normalizamos antes do merge para não perder
    # sales_price nesses deals.
    pipeline["product"] = pipeline["product"].replace({"GTXPro": "GTX Pro"})

    df = pipeline.merge(accounts, on="account", how="left")
    df = df.merge(products, on="product", how="left")
    df = df.merge(sales_teams, on="sales_agent", how="left")

    # agent_winrate desde histórico (só deals fechados)
    # Nota: agentes só em Engaging/Prospecting (sem nenhum deal fechado)
    # não aparecem aqui — caem no fallback "agente novo" em score_deal (SPEC E5).
    closed = df[df["deal_stage"].isin(["Won", "Lost"])]
    if closed.empty:
        win_rate_by_agent = {a: 0.5 for a in df["sales_agent"].unique()}
    else:
        won_per_agent = closed[closed["deal_stage"] == "Won"].groupby("sales_agent").size()
        total_per_agent = closed.groupby("sales_agent").size()
        win_rate_by_agent = (won_per_agent / total_per_agent).to_dict()

    if only_open:
        df = df[df["deal_stage"].isin(["Prospecting", "Engaging"])].copy()

    scores = df.apply(
        lambda r: score_deal(r, win_rate_by_agent, today),
        axis=1,
    )

    df["score"] = [s.total_score for s in scores]
    df["summary"] = [s.summary_ptbr for s in scores]
    df["components_json"] = [s.to_dict()["components"] for s in scores]
    # Valor potencial do deal aberto: no dataset real, close_value só existe para
    # deals Won/Lost. Para priorização de deals abertos, o valor "em jogo" é o
    # preço de lista do produto negociado (sales_price).
    df["expected_value"] = df["sales_price"].fillna(0.0)
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    return df


if __name__ == "__main__":
    # Smoke test self-contained
    DATA = Path(__file__).resolve().parent / "data"
    pipeline = pd.read_csv(DATA / "sales_pipeline.csv")
    accounts = pd.read_csv(DATA / "accounts.csv")
    products = pd.read_csv(DATA / "products.csv")
    sales_teams = pd.read_csv(DATA / "sales_teams.csv")

    scored = score_pipeline(pipeline, accounts, products, sales_teams,
                            today=pd.Timestamp("2017-12-31"))
    print(f"Deals scored: {len(scored)}")
    print(f"Score stats: min={scored['score'].min():.1f} "
          f"mean={scored['score'].mean():.1f} max={scored['score'].max():.1f}")
    print("\nTop 5 deals:")
    print(scored[["opportunity_id", "sales_agent", "account", "deal_stage",
                  "close_value", "score", "summary"]].head().to_string())
