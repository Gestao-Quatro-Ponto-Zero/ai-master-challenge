"""Lógica de priorização do Lead Scorer (Challenge 003).

Cada deal aberto vai para uma de quatro listas e recebe um valor esperado:

    valor esperado = preço de tabela do produto x chance de ganhar

A chance vem do histórico, olhando "o mesmo ponto dos trimestres anteriores":
de todos os deals que estavam abertos com essa mesma idade há 3, 6 e 9 meses,
que fração foi ganha depois? Esse recorte importa porque os fechamentos seguem
o calendário do trimestre (um deal fecha no trimestre em que começou ou no
seguinte, nunca depois), então idade sozinha engana.

Vendedor, setor, conta e região NÃO entram na conta: no histórico a taxa de
ganho não varia de forma significativa entre eles (ver backtest.py).
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

# O nome do produto diverge entre sales_pipeline.csv e products.csv.
PRODUCT_FIXES = {"GTXPro": "GTX Pro"}

# Estimativa da chance de ganhar.
QUARTERS_BACK = (1, 2, 3)  # olha o mesmo ponto de até 3 trimestres atrás
AGE_WINDOW = 7  # compara com deals de idade até 7 dias diferente
MIN_SAMPLE = 15  # abaixo disso não há base para estimar: chance 0
MIN_CHANCE = 0.01  # abaixo disso o deal é tratado como parado
MAX_AGE = 200

# A chance é mostrada em faixas, não em percentual: no teste ela ordena bem, mas
# o número exato erra (ver backtest.py).
BAND_HIGH = 0.40
BAND_MID = 0.20

# "Pode fechar este mês": chance de ser ganho nos próximos SOON_DAYS dias.
SOON_DAYS = 30
SOON_MIN_CHANCE = 0.10

# Regras de reativação decididas pelo Gustavo (process-log/decisoes.md, 3 e 5):
# deals parados só recebem mensagem se forem recentes; produto caro tolera mais.
REACTIVATION_MAX_AGE = 150  # 5 meses
REACTIVATION_MAX_AGE_EXPENSIVE = 180  # 6 meses
EXPENSIVE_PRICE = 3000

FOCO, REATIVAR, ABORDAR, ENCERRAR = "foco", "reativar", "abordar", "encerrar"


def load_pipeline(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Junta as 4 tabelas em uma linha por oportunidade."""
    pipeline = pd.read_csv(
        data_dir / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"]
    )
    pipeline["product"] = pipeline["product"].replace(PRODUCT_FIXES)
    products = pd.read_csv(data_dir / "products.csv")
    teams = pd.read_csv(data_dir / "sales_teams.csv")
    accounts = pd.read_csv(data_dir / "accounts.csv")
    accounts["sector"] = accounts["sector"].replace({"technolgy": "technology"})
    return (
        pipeline.merge(products, on="product", how="left", validate="m:1")
        .merge(teams, on="sales_agent", how="left", validate="m:1")
        .merge(accounts, on="account", how="left", validate="m:1")
    )


def reference_date(deals: pd.DataFrame) -> pd.Timestamp:
    """O "hoje" do CRM: a última data registrada.

    Os dados são de 2016-2017. Usar a data real de hoje faria todo deal
    parecer ter anos de idade.
    """
    return max(deals["engage_date"].max(), deals["close_date"].max())


def open_at(deals: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """Deals em negociação em `as_of` (iniciados e ainda não fechados), com idade."""
    started = deals["engage_date"].notna() & (deals["engage_date"] <= as_of)
    still_open = deals["close_date"].isna() | (deals["close_date"] > as_of)
    snapshot = deals[started & still_open].copy()
    snapshot["age"] = (as_of - snapshot["engage_date"]).dt.days
    return snapshot


def win_chance_by_age(
    deals: pd.DataFrame, as_of: pd.Timestamp, within_days: int | None = None
) -> list[float]:
    """Chance de ganhar por idade (em dias), usando só o que era sabido em `as_of`.

    Com `within_days`, conta só os ganhos que vieram até esse número de dias
    depois: é a chance de fechar logo, e não a de fechar algum dia.

    Para cada trimestre anterior, pega os deals que estavam abertos no mesmo dia
    do trimestre e conta quantos foram ganhos até `as_of`. A base não registra
    fechamentos antes de 01/03/2017, então datas anteriores a isso não servem
    de comparação (não dá para saber o que estava aberto).
    """
    records_start = deals["close_date"].min()
    ages, won = [], []
    for quarters in QUARTERS_BACK:
        analog_date = as_of - pd.DateOffset(months=3 * quarters)
        if analog_date < records_start:
            continue
        snapshot = open_at(deals, analog_date)
        deadline = as_of
        if within_days is not None:
            deadline = min(as_of, analog_date + pd.Timedelta(days=within_days))
        ages.append(snapshot["age"].to_numpy())
        won.append(
            ((snapshot["deal_stage"] == "Won") & (snapshot["close_date"] <= deadline)).to_numpy()
        )
    if not ages:
        return [0.0] * (MAX_AGE + 1)
    ages, won = np.concatenate(ages), np.concatenate(won)

    chance = []
    for age in range(MAX_AGE + 1):
        similar = np.abs(ages - age) <= AGE_WINDOW
        chance.append(float(won[similar].mean()) if similar.sum() >= MIN_SAMPLE else 0.0)
    return chance


def chance_for(chance_by_age: list[float], age: float) -> float:
    return chance_by_age[int(age)] if age <= MAX_AGE else 0.0


def band(chance: float) -> str:
    """Faixa de chance mostrada ao vendedor."""
    if chance >= BAND_HIGH:
        return "alta"
    return "media" if chance >= BAND_MID else "baixa"


def classify(stage: str, age: float, price: float, chance: float) -> str:
    """Define em qual lista o deal aberto entra."""
    if stage == "Prospecting":
        return ABORDAR  # sem data de início: não dá para medir idade
    if chance >= MIN_CHANCE:
        return FOCO
    limit = REACTIVATION_MAX_AGE_EXPENSIVE if price >= EXPENSIVE_PRICE else REACTIVATION_MAX_AGE
    return REATIVAR if age <= limit else ENCERRAR


def score_open_deals(deals: pd.DataFrame, as_of: pd.Timestamp) -> tuple[pd.DataFrame, dict]:
    """Classifica cada deal aberto e calcula chance, valor esperado e score."""
    chance_by_age = win_chance_by_age(deals, as_of)
    soon_by_age = win_chance_by_age(deals, as_of, within_days=SOON_DAYS)
    open_deals = deals[deals["deal_stage"].isin(["Engaging", "Prospecting"])].copy()
    open_deals["age"] = (as_of - open_deals["engage_date"]).dt.days

    # Prospecting não tem data de início, e a base não mostra quantos prospects
    # viram negociação. A chance deles é desconhecida: ficam sem chance e sem score.
    is_prospect = open_deals["deal_stage"] == "Prospecting"
    open_deals["chance"] = [
        0.0 if prospect else chance_for(chance_by_age, age)
        for prospect, age in zip(is_prospect, open_deals["age"])
    ]
    open_deals["chance_soon"] = [
        0.0 if prospect else chance_for(soon_by_age, age)
        for prospect, age in zip(is_prospect, open_deals["age"])
    ]
    open_deals["lista"] = [
        classify(stage, age, price, chance)
        for stage, age, price, chance in zip(
            open_deals["deal_stage"], open_deals["age"], open_deals["sales_price"], open_deals["chance"]
        )
    ]
    in_focus = open_deals["lista"] == FOCO
    open_deals.loc[~in_focus, ["chance", "chance_soon"]] = 0.0
    open_deals["valor_esperado"] = open_deals["sales_price"] * open_deals["chance"]
    open_deals["faixa"] = [band(c) if focus else None for c, focus in zip(open_deals["chance"], in_focus)]

    # Score 0-100 = posição do valor esperado entre os deals em negociação da empresa.
    open_deals["score"] = 0
    open_deals.loc[in_focus, "score"] = (
        (open_deals.loc[in_focus, "valor_esperado"].rank(pct=True) * 100).round().astype(int)
    )
    closed = deals[deals["close_date"].notna()]
    longest_cycle = int((closed["close_date"] - closed["engage_date"]).dt.days.max())
    return open_deals, {
        "chance_by_age": chance_by_age,
        "soon_by_age": soon_by_age,
        "longest_cycle": longest_cycle,
    }
