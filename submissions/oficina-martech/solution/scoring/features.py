"""Features — funções PURAS (sem I/O), fáceis de testar.

Cada função calcula um sinal do score a partir de valores simples.
"""
from .config import (
    GLOBAL_WIN_RATE, SMOOTHING_K, URGENCY_RAMP_END, URGENCY_PEAK_END,
    URGENCY_FLOOR, WON_MAX_DAYS,
)


def smoothed_winrate(wins: int, closed: int,
                     k: float = SMOOTHING_K, p0: float = GLOBAL_WIN_RATE) -> float:
    """Win-rate do vendedor suavizado por Bayes: (wins + k·p0) / (closed + k).

    Célula pequena (closed baixo) é puxada para a base global p0; célula grande
    converge para o win-rate real. Resolve ruído de vendedores com poucos deals.

    Clampada em [0,1]: com wins>closed (dado inconsistente) a fórmula crua
    excederia 1 e distorceria expected_value e o "% fecha" do breakdown.
    """
    closed = max(int(closed or 0), 0)
    wins = max(int(wins or 0), 0)
    p = (wins + k * p0) / (closed + k)
    return min(max(p, 0.0), 1.0)


def aging_subscore(days_open, stage: str):
    """Urgência por idade — curva SINO ancorada no ciclo dos deals Won.

    Comercialmente correto: a chance de fechar SOBE até a janela produtiva
    (mediana→p75 dos Won, ~57–88d, onde a maioria fecha) e CAI depois, porque
    deals muito velhos provavelmente morreram — nenhum Won passou de 138d.
    Logo NÃO é monotônica: um deal de 300d tem urgência BAIXA (piso), não máxima.

    Formato (piecewise):
      0 → ramp_end(57):  sobe 0→100          (esquentando)
      ramp_end → peak(88): platô em 100        (janela ideal)
      peak → won_max(138): decai 100→floor     (janela fechando)
      > won_max:        piso (floor)           (além do ciclo histórico)

    Retorna (subscore 0-100, rótulo, severidade) ou None se não aplicável
    (Prospecting / sem engage_date).
    """
    if stage == "Prospecting" or days_open is None:
        return None
    d = float(days_open)
    ramp = max(float(URGENCY_RAMP_END), 1.0)   # 57 — largura da rampa de aquecimento
    peak = max(float(URGENCY_PEAK_END), ramp)  # 88 — fim do platô
    dead = float(WON_MAX_DAYS)                 # 138 — além = provavelmente morto

    if d <= ramp:
        f = d / ramp
        return round(100.0 * f, 1), f"esquentando ({int(d)}d)", "ok"
    if d <= peak:
        return 100.0, f"janela ideal ({int(d)}d)", "ok"
    if d <= dead:
        f = (d - peak) / (dead - peak) if dead > peak else 1.0
        sub = round(100.0 - (100.0 - URGENCY_FLOOR) * f, 1)
        return sub, f"janela fechando ({int(d)}d)", "alerta"
    return URGENCY_FLOOR, f"além do ciclo histórico ({int(d)}d)", "critico"


def percentile_rank(series):
    """Rank percentil 0-100 (robusto a outliers). series: pandas Series numérica."""
    return series.rank(pct=True) * 100.0
