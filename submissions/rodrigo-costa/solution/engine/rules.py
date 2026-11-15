"""Definições do modelo: constantes, rótulos em português, objetos leves e regras simples.

Importe pelo engine.core, que reexporta tudo isto.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List, NamedTuple, Optional, Tuple

HORIZON_DAYS = 30
MIN_CELL = 30
AGE_LIMITS = (14, 30, 45, 60, 75, 90, 105, 120, 138)
AGE_BAND_LABELS = ("0–14", "15–30", "31–45", "46–60", "61–75", "76–90", "91–105", "106–120", "121–138", "139+")
TRAIN_FIRST = date(2017, 3, 6)
TRAIN_LAST = date(2017, 12, 25)
FIRST_DATE = date(2017, 7, 3)
LAST_DATE = date(2017, 12, 25)
DEFAULT_DATE = date(2017, 12, 4)
WINDOW_RATIO = 0.8
HOT_MIN = 80
WARM_MIN = 40

QUARTER_PHASES = ("abre", "meio", "fecha")
PHASE_TITLES = {"abre": "Começo de trimestre", "meio": "Meio de trimestre", "fecha": "É mês de fechar"}
WEAK_CLOSE_TITLE = "Fim de trimestre"
CLOSING_PEAK_MIN = 0.30  # abaixo disso, o último mês não é chamado de "mês de fechar"
CLOSING_DAYS_MIN = 14  # "ainda em <mês>" só quando faltam pelo menos estes dias para o trimestre acabar
LEVEL_LABELS = {
    "semana": "idade e semana do trimestre",
    "mes": "idade e mês do trimestre",
    "idade": "só a idade",
    "geral": "taxa geral",
}
SCORE_BAND_LABELS = {"quente": "Quente", "morno": "Morno", "frio": "Frio", "sem_desfecho": "Sem desfecho"}
REGION_LABELS = {"Central": "Central", "East": "Leste", "West": "Oeste"}
SECTOR_LABELS = {
    "finance": "Finanças", "marketing": "Marketing", "technology": "Tecnologia", "retail": "Varejo",
    "entertainment": "Entretenimento", "software": "Software", "medical": "Saúde", "services": "Serviços",
    "telecommunications": "Telecomunicações", "employment": "Recrutamento",
}
COUNTRY_LABELS = {
    "Belgium": "Bélgica", "Brazil": "Brasil", "China": "China", "Germany": "Alemanha", "Italy": "Itália",
    "Japan": "Japão", "Jordan": "Jordânia", "Kenya": "Quênia", "Korea": "Coreia do Sul", "Norway": "Noruega",
    "Panama": "Panamá", "Philippines": "Filipinas", "Poland": "Polônia", "Romania": "Romênia",
    "United States": "Estados Unidos",
}
SECTOR_FIXES = {"technolgy": "technology"}
COUNTRY_FIXES = {"Philipines": "Philippines"}
PRODUCT_FIXES = {"GTXPro": "GTX Pro"}


# ---------------------------------------------------------------- objetos

class InputError(ValueError):
    """Entrada inválida do usuário (nome, data, filtro). O servidor devolve 400 com a mensagem em português."""


class Product(NamedTuple):
    name: str
    series: str
    price: int


class Seller(NamedTuple):
    name: str
    manager: str
    region: str


class Account(NamedTuple):
    name: str
    sector: str
    sector_label: str
    year_established: int
    revenue: float  # milhões de US$
    employees: int
    office_location: str
    country_label: str
    subsidiary_of: Optional[str]


class Deal(NamedTuple):
    """Um deal como está na base. won/lost/close_* são o desfecho FINAL: numa data d, só valem se
    closed_before(d)."""
    id: str
    seller: str
    manager: str
    region: str
    product: str
    series: str
    price: int
    account: Optional[str]
    stage: str
    engage_date: Optional[date]
    close_date: Optional[date]
    close_value: Optional[int]  # None nos abertos; 0 nos perdidos
    won: bool
    lost: bool

    @property
    def cycle_days(self) -> Optional[int]:
        if self.engage_date is None or self.close_date is None:
            return None
        return (self.close_date - self.engage_date).days

    def closed_before(self, d: date) -> bool:
        return self.close_date is not None and self.close_date < d

    def is_open_at(self, d: date) -> bool:
        return self.engage_date is not None and self.engage_date < d and not self.closed_before(d)


class Cell(NamedTuple):
    chance: float
    n: int
    y: int
    level: str


class BandRow(NamedTuple):
    index: int
    label: str
    min_age: int
    max_age: Optional[int]  # None na última faixa (139+)
    chance: float
    n: int
    y: int
    level: str


class Window(NamedTuple):
    first_band: int
    last_band: int
    min_age: int
    max_age: int
    label: str  # "61 a 105 dias"
    peak_band: int
    peak_chance: float
    threshold: float


class ScoredDeal(NamedTuple):
    deal: Deal
    age_days: int
    age_band: int
    stale: bool  # sem desfecho: idade maior que o maior ciclo conhecido
    chance: float  # 0 se stale
    n: int
    y: int
    level: str
    expected_value: float  # chance x preço de tabela; 0 se stale
    score: Optional[int]  # None se stale
    score_band: str


class WinRecord(NamedTuple):
    won: int
    lost: int
    stale: int
    official_rate: Optional[float]  # ganhos / (ganhos + perdidos)
    rate_with_stale: Optional[float]  # ganhos / (ganhos + perdidos + sem desfecho)


# ---------------------------------------------------------------- regras simples

def age_band(age: int) -> int:
    """Índice da faixa de idade (0 a 9)."""
    for i, lim in enumerate(AGE_LIMITS):
        if age <= lim:
            return i
    return len(AGE_LIMITS)


def band_bounds(index: int) -> Tuple[int, Optional[int]]:
    low = 0 if index == 0 else AGE_LIMITS[index - 1] + 1
    return low, (AGE_LIMITS[index] if index < len(AGE_LIMITS) else None)


def quarter_point(d: date) -> Tuple[int, int, str]:
    """(semana do trimestre, mês do trimestre 0-2, fase 'abre'/'meio'/'fecha')."""
    start = date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)
    month = (d.month - 1) % 3
    return (d - start).days // 7, month, QUARTER_PHASES[month]


def score_band(score: Optional[int]) -> str:
    if score is None:
        return "sem_desfecho"
    if score >= HOT_MIN:
        return "quente"
    return "morno" if score >= WARM_MIN else "frio"


def priority_key(s: ScoredDeal) -> Tuple[float, int, str]:
    """Ordem de prioridade dos vivos: receita esperada desc (2 casas), mais antigo, id."""
    return (-round(s.expected_value, 2), -s.age_days, s.deal.id)


def stale_key(s: ScoredDeal) -> Tuple[int, int, str]:
    """Ordem dos sem desfecho: preço desc, idade desc, id."""
    return (-s.deal.price, -s.age_days, s.deal.id)


def mondays(first: date, last: date) -> List[date]:
    out, d = [], first
    while d <= last:
        out.append(d)
        d += timedelta(days=7)
    return out


def win_rate(won: int, lost: int, stale: int = 0) -> Optional[float]:
    total = won + lost + stale
    return won / float(total) if total else None
