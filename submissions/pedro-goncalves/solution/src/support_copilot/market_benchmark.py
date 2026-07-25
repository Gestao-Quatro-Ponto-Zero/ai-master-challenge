from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class UsagePrice:
    vendor: str
    unit: str
    usd_per_unit: float
    source_url: str


@dataclass(frozen=True)
class MarketBenchmark:
    annual_volume: int
    technical_coverage: float
    covered_monthly: float
    covered_weekly: float
    monthly_low_usd: float
    monthly_high_usd: float
    weekly_low_usd: float
    weekly_high_usd: float

    def to_dict(self) -> dict:
        return asdict(self)


PUBLIC_USAGE_PRICES = (
    UsagePrice(
        vendor="Freshdesk Freddy AI Agent",
        unit="sessão",
        usd_per_unit=0.49,
        source_url="https://www.freshworks.com/freshdesk/pricing/",
    ),
    UsagePrice(
        vendor="Gorgias AI Agent",
        unit="interação resolvida",
        usd_per_unit=0.90,
        source_url="https://www.gorgias.com/blog/ai-agent-pricing",
    ),
    UsagePrice(
        vendor="Intercom Fin",
        unit="resultado",
        usd_per_unit=0.99,
        source_url=(
            "https://www.intercom.com/help/en/articles/"
            "8205718-fin-ai-agent-outcomes"
        ),
    ),
)

ZENDESK_SEAT_REFERENCE = {
    "suite_team_usd_per_agent_month": 55.0,
    "copilot_usd_per_agent_month": 50.0,
    "source_url": "https://www.zendesk.com/pricing/",
}


def calculate_market_benchmark(
    *,
    annual_volume: int,
    technical_coverage: float,
    prices: tuple[UsagePrice, ...] = PUBLIC_USAGE_PRICES,
) -> MarketBenchmark:
    if annual_volume < 0:
        raise ValueError("Volume anual não pode ser negativo.")
    if not 0 <= technical_coverage <= 1:
        raise ValueError("Cobertura técnica deve estar entre 0 e 1.")
    if not prices or any(price.usd_per_unit <= 0 for price in prices):
        raise ValueError("Preços públicos devem ser positivos.")

    covered_annual = annual_volume * technical_coverage
    covered_monthly = covered_annual / 12
    covered_weekly = covered_annual / 52
    unit_prices = [price.usd_per_unit for price in prices]

    return MarketBenchmark(
        annual_volume=annual_volume,
        technical_coverage=technical_coverage,
        covered_monthly=covered_monthly,
        covered_weekly=covered_weekly,
        monthly_low_usd=covered_monthly * min(unit_prices),
        monthly_high_usd=covered_monthly * max(unit_prices),
        weekly_low_usd=covered_weekly * min(unit_prices),
        weekly_high_usd=covered_weekly * max(unit_prices),
    )
