"""Núcleo: carga dos CSVs, modelo de chance por data e retrato (snapshot) da base numa segunda-feira.

Regra de ouro: para uma data d, só vale o que se sabia em d. Um deal com close_date >= d está
"em negociação" em d; seu estágio final e seu valor fechado não podem ser usados pelas telas de trabalho.
"""
from __future__ import annotations

import bisect
import csv
import os
import re
import threading
import unicodedata
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from engine import fmt
from engine.rules import (  # noqa: F401  (reexportados: as telas importam tudo de engine.core)
    AGE_BAND_LABELS, AGE_LIMITS, CLOSING_DAYS_MIN, CLOSING_PEAK_MIN, COUNTRY_FIXES, COUNTRY_LABELS, DEFAULT_DATE,
    FIRST_DATE, HORIZON_DAYS, HOT_MIN, LAST_DATE, LEVEL_LABELS, MIN_CELL, PHASE_TITLES, PRODUCT_FIXES,
    QUARTER_PHASES, REGION_LABELS, SCORE_BAND_LABELS, SECTOR_FIXES, SECTOR_LABELS, TRAIN_FIRST, TRAIN_LAST,
    WARM_MIN, WEAK_CLOSE_TITLE, WINDOW_RATIO, Account, BandRow, Cell, Deal, InputError, Product, ScoredDeal,
    Seller, WinRecord, Window, age_band, band_bounds, mondays, priority_key, quarter_point, score_band,
    stale_key, win_rate)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ECHO_MAX = 60  # mensagens de erro repetem no máximo isto da entrada do usuário


# ---------------------------------------------------------------- carga

def _read(data_dir: str, name: str) -> List[Dict[str, str]]:
    with open(os.path.join(data_dir, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _date(text: str) -> Optional[date]:
    text = (text or "").strip()
    return date.fromisoformat(text) if text else None


class Dataset:
    """Base carregada e indexada. Os índices de deals são tuplas na ordem do arquivo."""

    def __init__(self, products: Dict[str, Product], sellers: Dict[str, Seller],
                 accounts: Dict[str, Account], deals: Tuple[Deal, ...]) -> None:
        self.products = products
        self.sellers = sellers
        self.accounts = accounts
        self.deals = deals
        self.managers: Dict[str, Tuple[str, ...]] = _group_names(sellers.values(), "manager")
        self.regions: Dict[str, Tuple[str, ...]] = {
            r: tuple(sorted({s.manager for s in sellers.values() if s.region == r})) for r in REGION_LABELS}
        self.deals_by_seller = _index(deals, lambda x: x.seller)
        self.deals_by_account = _index(deals, lambda x: x.account)
        self.dated = tuple(x for x in deals if x.engage_date is not None)
        self.prospecting = tuple(sorted((x for x in deals if x.engage_date is None), key=lambda x: (-x.price, x.id)))
        self.closed = tuple(sorted((x for x in deals if x.close_date is not None), key=lambda x: (x.close_date, x.id)))
        self._closed_dates = [x.close_date for x in self.closed]
        running, self._max_cycle_upto = 0, []
        for x in self.closed:
            running = max(running, x.cycle_days or 0)
            self._max_cycle_upto.append(running)
        self._closed_by: Dict[Tuple[str, str], Tuple[List[date], Tuple[Deal, ...]]] = {}
        for kind, attr in (("seller", "seller"), ("account", "account")):
            groups: Dict[str, List[Deal]] = defaultdict(list)
            for x in self.closed:
                key = getattr(x, attr)
                if key is not None:
                    groups[key].append(x)
            for key, items in groups.items():
                self._closed_by[(kind, key)] = ([x.close_date for x in items], tuple(items))
        self.end_date: date = self._closed_dates[-1]
        self.training_mondays = tuple(mondays(TRAIN_FIRST, TRAIN_LAST))
        self.monday_counts = _monday_counts(self.dated, self.training_mondays)
        self._lock = threading.Lock()
        self._snapshots: Dict[date, "Snapshot"] = {}

    def max_cycle_before(self, d: date) -> int:
        """Maior ciclo (close - engage, em dias) entre os deals fechados antes de d."""
        i = bisect.bisect_left(self._closed_dates, d)
        return self._max_cycle_upto[i - 1] if i else 0

    def closed_before(self, d: date, seller: Optional[str] = None,
                      account: Optional[str] = None) -> Tuple[Deal, ...]:
        """Deals fechados (Won/Lost) com close_date < d, em ordem de fechamento; filtro opcional (um só)."""
        for kind, key in (("seller", seller), ("account", account)):
            if key is not None:
                dates, items = self._closed_by.get((kind, key), ([], ()))
                return items[:bisect.bisect_left(dates, d)]
        return self.closed[:bisect.bisect_left(self._closed_dates, d)]


def _group_names(sellers: Iterable[Seller], attr: str) -> Dict[str, Tuple[str, ...]]:
    groups: Dict[str, List[str]] = defaultdict(list)
    for s in sellers:
        groups[getattr(s, attr)].append(s.name)
    return {k: tuple(sorted(v)) for k, v in sorted(groups.items())}


def _index(deals: Iterable[Deal], keyf) -> Dict[str, Tuple[Deal, ...]]:
    groups: Dict[str, List[Deal]] = defaultdict(list)
    for x in deals:
        key = keyf(x)
        if key is not None:
            groups[key].append(x)
    return {k: tuple(v) for k, v in groups.items()}


def _monday_counts(dated: Sequence[Deal], days: Sequence[date]) -> Dict[date, List[List[int]]]:
    """Para cada segunda de treino: [y, n] por faixa de idade dos deals abertos nela.
    y = 1 se o deal foi ganho em menos de 30 dias a partir da segunda."""
    counts = {m: [[0, 0] for _ in range(len(AGE_LIMITS) + 1)] for m in days}
    for x in dated:
        for m in days:
            if x.engage_date < m and (x.close_date is None or x.close_date >= m):
                cell = counts[m][age_band((m - x.engage_date).days)]
                cell[1] += 1
                if x.won and x.close_date < m + timedelta(days=HORIZON_DAYS):
                    cell[0] += 1
    return counts


def load_dataset(data_dir: str = DATA_DIR) -> Dataset:
    """Lê e normaliza os 4 CSVs (produto GTXPro, setor e país com erro de digitação)."""
    products = {}
    for r in _read(data_dir, "products.csv"):
        products[r["product"]] = Product(r["product"], r["series"], int(float(r["sales_price"])))
    sellers = {}
    for r in _read(data_dir, "sales_teams.csv"):
        sellers[r["sales_agent"]] = Seller(r["sales_agent"], r["manager"], r["regional_office"])
    accounts = {}
    for r in _read(data_dir, "accounts.csv"):
        sector = SECTOR_FIXES.get(r["sector"], r["sector"])
        country = COUNTRY_FIXES.get(r["office_location"], r["office_location"])
        accounts[r["account"]] = Account(
            r["account"], sector, SECTOR_LABELS.get(sector, sector), int(r["year_established"]),
            float(r["revenue"]), int(r["employees"]), country, COUNTRY_LABELS.get(country, country),
            (r["subsidiary_of"] or "").strip() or None)
    deals = []
    for r in _read(data_dir, "sales_pipeline.csv"):
        prod = products[PRODUCT_FIXES.get(r["product"], r["product"])]
        seller = sellers[r["sales_agent"]]
        stage = r["deal_stage"]
        value = (r["close_value"] or "").strip()
        deals.append(Deal(
            r["opportunity_id"], seller.name, seller.manager, seller.region, prod.name, prod.series, prod.price,
            (r["account"] or "").strip() or None, stage, _date(r["engage_date"]), _date(r["close_date"]),
            int(float(value)) if value else None, stage == "Won", stage == "Lost"))
    return Dataset(products, sellers, accounts, tuple(deals))


_DATASET: Optional[Dataset] = None
_DATASET_LOCK = threading.Lock()


def get_dataset() -> Dataset:
    """Base padrão (pasta data da solução), carregada uma vez por processo."""
    global _DATASET
    with _DATASET_LOCK:
        if _DATASET is None:
            _DATASET = load_dataset(DATA_DIR)
        return _DATASET


# ---------------------------------------------------------------- datas aceitas

def available_dates(ds: Dataset) -> List[date]:
    """As 26 segundas que o app aceita (3 jul a 25 dez 2017). Fixas: não dependem do fim da base."""
    return mondays(FIRST_DATE, LAST_DATE)


def echo(text: Optional[str]) -> str:
    """Entrada do usuário para repetir numa mensagem de erro, cortada em ECHO_MAX caracteres."""
    text = (text or "").strip()
    return text if len(text) <= ECHO_MAX else text[:ECHO_MAX] + "…"


def parse_date(ds: Dataset, text: Optional[str]) -> date:
    """Texto AAAA-MM-DD para date; vazio vira DEFAULT_DATE. InputError (em português) se inválida."""
    text = (text or "").strip()
    if not text:
        return DEFAULT_DATE
    try:
        # o regex barra formatos que o Python 3.11+ passou a aceitar ("20171204", "2017-W49-1")
        if not ISO_DATE.match(text):
            raise ValueError(text)
        d = date.fromisoformat(text)
    except ValueError:
        raise InputError("Data inválida: \"%s\". Use o formato AAAA-MM-DD, por exemplo 2017-12-04." % echo(text))
    dates = available_dates(ds)
    if d not in dates:
        raise InputError("Data fora do período: escolha uma segunda-feira entre %s e %s." % (
            fmt.date_label(dates[0]), fmt.date_label(dates[-1])))
    return d


# ---------------------------------------------------------------- modelo e retrato

class ChanceModel:
    """Contagens das segundas m com m + 30 dias <= d, agregadas por faixa x (semana | mês) do trimestre."""

    def __init__(self, ds: Dataset, d: date) -> None:
        self.date = d
        self.week, self.month, _ = quarter_point(d)
        self.mondays = tuple(m for m in ds.training_mondays if m + timedelta(days=HORIZON_DAYS) <= d)
        self.week_mondays = tuple(m for m in self.mondays if quarter_point(m)[0] == self.week)
        self.month_mondays = tuple(m for m in self.mondays if quarter_point(m)[1] == self.month)
        nb = len(AGE_LIMITS) + 1
        self._week = [[0, 0] for _ in range(nb)]
        self._month = [[0, 0] for _ in range(nb)]
        self._age = [[0, 0] for _ in range(nb)]
        self._total = [0, 0]
        for m in self.mondays:
            same_week = m in self.week_mondays
            same_month = m in self.month_mondays
            for b, (y, n) in enumerate(ds.monday_counts[m]):
                for table, use in ((self._week, same_week), (self._month, same_month), (self._age, True)):
                    if use:
                        table[b][0] += y
                        table[b][1] += n
                self._total[0] += y
                self._total[1] += n

    def cell(self, band: int) -> Cell:
        """Primeira célula com n >= 30: semana, mês, idade; senão a taxa geral."""
        for level, table in (("semana", self._week), ("mes", self._month), ("idade", self._age)):
            y, n = table[band]
            if n >= MIN_CELL:
                return Cell(y / float(n), n, y, level)
        y, n = self._total
        return Cell(y / float(n) if n else 0.0, n, y, "geral")


def find_window(bands: Sequence[BandRow]) -> Optional[Window]:
    """Trecho contíguo de faixas (sem a 139+) com chance >= 80% da maior; o que contém a maior."""
    rows = [b for b in bands if b.max_age is not None]
    peak = max(rows, key=lambda b: (b.chance, -b.index))
    if peak.chance <= 0:
        return None
    threshold = WINDOW_RATIO * peak.chance
    first = last = peak.index
    while first > 0 and rows[first - 1].chance >= threshold:
        first -= 1
    while last + 1 < len(rows) and rows[last + 1].chance >= threshold:
        last += 1
    low, high = rows[first].min_age, rows[last].max_age
    return Window(first, last, low, high, "%d a %d dias" % (low, high), peak.index, peak.chance, threshold)


class Snapshot:
    """Retrato da base numa data: deals abertos pontuados, tabela de chance, janela e ciclo máximo.

    deals: todos os abertos datados, vivos em ordem de prioridade e depois os sem desfecho.
    live / stale: as duas partes. by_seller: mesma ordem, por vendedor.
    live_evs: receitas esperadas dos vivos em ordem crescente.
    """

    def __init__(self, ds: Dataset, d: date) -> None:
        self.date = d
        self.week_of_quarter, self.month_in_quarter, self.quarter_phase = quarter_point(d)
        self.max_cycle = ds.max_cycle_before(d)
        self.model = ChanceModel(ds, d)
        self.bands: Tuple[BandRow, ...] = tuple(
            BandRow(i, AGE_BAND_LABELS[i], band_bounds(i)[0], band_bounds(i)[1], *self.model.cell(i))
            for i in range(len(AGE_LIMITS) + 1))
        self.window = find_window(self.bands)
        raw = []
        for x in ds.dated:
            if x.is_open_at(d):
                age = (d - x.engage_date).days
                band = age_band(age)
                cell = self.bands[band]
                stale = age > self.max_cycle
                chance = 0.0 if stale else cell.chance
                raw.append((x, age, band, stale, chance, cell, chance * x.price))
        self.live_evs: List[float] = sorted(r[6] for r in raw if not r[3])
        total = len(self.live_evs)
        scored = []
        for x, age, band, stale, chance, cell, ev in raw:
            score = None if stale else int(round(100.0 * bisect.bisect_right(self.live_evs, ev) / total))
            scored.append(ScoredDeal(x, age, band, stale, chance, cell.n, cell.y, cell.level, ev, score,
                                     score_band(score)))
        self.live: Tuple[ScoredDeal, ...] = tuple(sorted((s for s in scored if not s.stale), key=priority_key))
        self.stale: Tuple[ScoredDeal, ...] = tuple(sorted((s for s in scored if s.stale), key=stale_key))
        self.deals: Tuple[ScoredDeal, ...] = self.live + self.stale
        groups: Dict[str, List[ScoredDeal]] = defaultdict(list)
        for s in self.deals:
            groups[s.deal.seller].append(s)
        self.by_seller: Dict[str, Tuple[ScoredDeal, ...]] = {k: tuple(v) for k, v in groups.items()}

    def for_sellers(self, names: Iterable[str]) -> Tuple[ScoredDeal, ...]:
        """Abertos dos vendedores dados, na ordem de exibição (vivos por prioridade, depois sem desfecho)."""
        wanted = set(names)
        return tuple(s for s in self.deals if s.deal.seller in wanted)

    def fraction_above(self, expected_value: float) -> float:
        """Fração dos vivos da empresa com receita esperada maior que a dada."""
        total = len(self.live_evs)
        return (total - bisect.bisect_right(self.live_evs, expected_value)) / float(total) if total else 0.0


def closing_is_strong(snap: Snapshot) -> bool:
    """Último mês do trimestre com a melhor faixa de idade fechando bem (CLOSING_PEAK_MIN ou mais)."""
    w = snap.window
    return snap.quarter_phase == "fecha" and w is not None and w.peak_chance >= CLOSING_PEAK_MIN


def phase_title(snap: Snapshot) -> str:
    """"Começo de trimestre", "Meio de trimestre", "É mês de fechar" ou, com chance baixa, "Fim de trimestre"."""
    if snap.quarter_phase == "fecha" and not closing_is_strong(snap):
        return WEAK_CLOSE_TITLE
    return PHASE_TITLES[snap.quarter_phase]


def days_to_quarter_end(d: date) -> int:
    """Dias de d até o último dia do trimestre civil (0 no próprio último dia)."""
    q = (d.month - 1) // 3
    end = date(d.year + 1, 1, 1) if q == 3 else date(d.year, 3 * q + 4, 1)
    return (end - d).days - 1


def snapshot(ds: Dataset, d: date) -> Snapshot:
    """Retrato da data d, calculado uma vez e guardado (seguro para várias threads)."""
    with ds._lock:
        snap = ds._snapshots.get(d)
        if snap is None:
            snap = ds._snapshots[d] = Snapshot(ds, d)
        return snap


def summarize(items: Iterable[ScoredDeal]) -> Dict[str, Union[int, float]]:
    """Contagens e somas de uma lista de abertos pontuados (valores crus, sem arredondar)."""
    out: Dict[str, Union[int, float]] = {
        "open": 0, "live": 0, "stale": 0, "hot": 0, "warm": 0, "cold": 0,
        "declared_value": 0, "live_value": 0, "stale_value": 0, "expected_value": 0.0}
    names = {"quente": "hot", "morno": "warm", "frio": "cold"}
    for s in items:
        out["open"] += 1
        out["declared_value"] += s.deal.price
        if s.stale:
            out["stale"] += 1
            out["stale_value"] += s.deal.price
        else:
            out["live"] += 1
            out["live_value"] += s.deal.price
            out["expected_value"] += s.expected_value
            out[names[s.score_band]] += 1
    return out


def win_record(ds: Dataset, snap: Snapshot, sellers: Union[str, Sequence[str]]) -> WinRecord:
    """Ganhos e perdidos antes da data do retrato e as duas taxas (oficial e com os sem desfecho)."""
    names = [sellers] if isinstance(sellers, str) else list(sellers)
    won = lost = stale = 0
    for name in names:
        for x in ds.closed_before(snap.date, seller=name):
            won += x.won
            lost += x.lost
        stale += sum(1 for s in snap.by_seller.get(name, ()) if s.stale)
    return WinRecord(won, lost, stale, win_rate(won, lost), win_rate(won, lost, stale))


# ---------------------------------------------------------------- nomes

def _norm(text: Optional[str]) -> str:
    text = unicodedata.normalize("NFKD", (text or "").strip()).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.casefold().split())


def _resolve(text: Optional[str], options: Iterable[str], what: str) -> str:
    key = _norm(text)
    for name in options:
        if _norm(name) == key:
            return name
    raise InputError("%s não encontrado: \"%s\"." % (what, echo(text)))


def resolve_seller(ds: Dataset, name: Optional[str]) -> str:
    """Nome canônico do vendedor (ignora maiúsculas, acentos e espaços); InputError se não existir."""
    return _resolve(name, ds.sellers, "Vendedor")


def resolve_working_seller(ds: Dataset, name: Optional[str]) -> str:
    """Como resolve_seller, mas recusa quem só está no cadastro (sem nenhum deal): telas de vendedor e time."""
    seller = resolve_seller(ds, name)
    if seller not in ds.deals_by_seller:
        raise InputError("%s só está no cadastro: não tem deals na base." % seller)
    return seller


def resolve_manager(ds: Dataset, name: Optional[str]) -> str:
    return _resolve(name, ds.managers, "Gestor")


def resolve_region(ds: Dataset, name: Optional[str]) -> str:
    """Aceita o código ("East") ou o rótulo ("Leste"); devolve o código."""
    key = _norm(name)
    for code, label in REGION_LABELS.items():
        if key in (_norm(code), _norm(label)):
            return code
    raise InputError("Regional não encontrada: \"%s\". Use Central, Leste ou Oeste." % echo(name))


def resolve_account(ds: Dataset, name: Optional[str]) -> str:
    return _resolve(name, ds.accounts, "Cliente")


def home_region(closed: Iterable[Deal]) -> Optional[str]:
    """Regional "de casa" de um cliente: a mais frequente entre os vendedores dos fechados dados;
    empate pelo código da regional. Com os fechados antes de d, pode mudar de uma data para outra."""
    counts = Counter(x.region for x in closed)
    if not counts:
        return None
    return min(counts, key=lambda r: (-counts[r], r))


def select_sellers(ds: Dataset, manager: Optional[str] = None, region: Optional[str] = None,
                   seller: Optional[str] = None) -> List[str]:
    """Vendedores (inclusive sem deals) que atendem a todos os filtros dados, em ordem alfabética."""
    names = set(ds.sellers)
    if manager is not None:
        names &= set(ds.managers[resolve_manager(ds, manager)])
    if region is not None:
        code = resolve_region(ds, region)
        names &= {s.name for s in ds.sellers.values() if s.region == code}
    if seller is not None:
        names &= {resolve_seller(ds, seller)}
    return sorted(names)
