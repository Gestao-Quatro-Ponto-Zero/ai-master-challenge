"""Task 2.19 — monotonicidade de risco(t); leitura em degraus das curvas."""

from scoring import constants
from scoring.curves import p_ganho, risco


def test_risco_monotonic_non_decreasing_at_calibrated_points():
    values = [risco(t) for t, _ in constants.RISCO_BREAKPOINTS]
    assert values == sorted(values)


def test_risco_step_function_reads_calibrated_points():
    assert risco(10) == 0.219
    assert risco(57) == 0.489
    assert risco(88) == 0.832


def test_risco_freezes_above_120():
    assert risco(120) == risco(130) == 1.000


def test_p_ganho_rises_with_age_not_decays():
    assert p_ganho(0) < p_ganho(57) < p_ganho(120)


def test_p_ganho_step_function_reads_calibrated_points():
    assert p_ganho(57) == 0.684
    assert p_ganho(88) == 0.704


def test_p_ganho_freezes_above_120():
    assert p_ganho(120) == p_ganho(130) == 0.751
