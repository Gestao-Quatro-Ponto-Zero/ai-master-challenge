"""Task 2.10 — atribuição de CONFIANÇA nos quatro ramos."""

from scoring.confianca import confianca


def test_confianca_a_account_and_engaging_within_window():
    assert confianca("Engaging", has_account=True, age_days=90) == "A"


def test_confianca_b_account_but_prospecting():
    assert confianca("Prospecting", has_account=True, age_days=None) == "B"


def test_confianca_b_engaging_without_account():
    assert confianca("Engaging", has_account=False, age_days=30) == "B"


def test_confianca_c_no_account_prospecting():
    assert confianca("Prospecting", has_account=False, age_days=None) == "C"


def test_confianca_d_censorship_dominates_other_criteria():
    assert confianca("Engaging", has_account=True, age_days=200) == "D"


def test_confianca_d_only_when_age_known():
    # Prospecting não tem idade conhecida — censura nunca se aplica a ela.
    assert confianca("Prospecting", has_account=False, age_days=None) != "D"
