"""Invariants of the routing policy and its guards. Fast: no training, synthetic probabilities."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from router import NEVER_AUTO, SEGMENT_SENSITIVE, SEGMENT_WORDS, SENSITIVE_MASS, Policy, psi, segment_windows  # noqa: E402

CLASSES = np.array(["Access", "Administrative rights", "HR Support", "Hardware"])
POLICY = Policy(t_auto=0.79, t_assist=0.44, t_ood=0.24, c_min=0.55, t_coherence=0.09, classes=CLASSES)


def decide(proba, sim=0.9, cov=0.9, seg=0.0, coh=0.5):
    tiers, reasons = POLICY.decide(np.array([proba]), np.array([sim]), np.array([cov]), np.array([seg]), np.array([coh]))
    return tiers[0], reasons[0]


def test_high_confidence_goes_auto():
    assert decide([0.0, 0.0, 0.0, 1.0]) == ("auto", "confianca_alta")


def test_unknown_vocabulary_wins_over_confidence():
    assert decide([0.0, 0.0, 0.0, 1.0], cov=0.2) == ("human", "vocabulario_desconhecido")


def test_no_similar_history_goes_to_human():
    assert decide([0.0, 0.0, 0.0, 1.0], sim=0.1) == ("human", "sem_historico_parecido")


def test_privileged_queue_is_never_auto():
    assert "Administrative rights" in NEVER_AUTO
    assert decide([0.0, 0.99, 0.0, 0.01]) == ("assist", "fila_privilegiada")


def test_sensitive_mass_blocks_auto_elsewhere():
    p = [0.0, 0.0, SENSITIVE_MASS + 0.01, 1 - SENSITIVE_MASS - 0.01]
    assert decide(p) == ("assist", "possivel_conteudo_sensivel")


def test_low_confidence_goes_to_human():
    assert decide([0.3, 0.1, 0.25, 0.35]) == ("human", "confianca_baixa")


def test_psi_is_zero_for_identical_distributions_and_grows_with_shift():
    expected = np.array([0.25, 0.25, 0.25, 0.25])
    same = psi(expected, np.array([50, 50, 50, 50]))
    shifted = psi(expected, np.array([170, 10, 10, 10]))
    assert same < 0.01
    assert shifted > 0.25


def test_psi_does_not_explode_on_an_empty_category():
    expected = np.array([0.04, 0.32, 0.32, 0.32])
    assert psi(expected, np.array([0, 66, 67, 67])) < 0.25


def test_sensitive_segment_blocks_auto_even_when_the_whole_ticket_looks_safe():
    # Padding attack: the whole ticket reads as Hardware, but one window reads as HR.
    assert decide([0.0, 0.0, 0.0, 1.0], seg=SEGMENT_SENSITIVE) == ("assist", "trecho_sensivel")
    assert decide([0.0, 0.0, 0.0, 1.0], seg=SEGMENT_SENSITIVE - 0.01) == ("auto", "confianca_alta")


def test_segment_windows_overlap_and_cover_the_tail():
    words = [f"w{i}" for i in range(SEGMENT_WORDS + 3)]
    windows = segment_windows(" ".join(words))
    assert windows[0].split() == words[:SEGMENT_WORDS]
    assert windows[-1].split()[-1] == words[-1]
    assert segment_windows("short ticket") == ["short ticket"]


def test_scrambled_word_order_goes_to_human_before_any_confidence_rule():
    # Interleaving padding between every word defeats the windows; it also leaves no known word pair.
    assert decide([0.0, 0.0, 0.0, 1.0], coh=0.0) == ("human", "sequencia_incomum")
    assert decide([0.0, 0.0, 0.0, 1.0], coh=0.09) == ("auto", "confianca_alta")
