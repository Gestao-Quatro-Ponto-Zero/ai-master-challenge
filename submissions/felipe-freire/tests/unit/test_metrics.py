import pytest

from social_media_intelligence.metrics import engagement_total, safe_rate


def test_engagement_total_reconciles_components() -> None:
    assert engagement_total(1_469, 284, 197) == 1_950


def test_engagement_total_rejects_negative_counts() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        engagement_total(10, -1, 2)


def test_safe_rate() -> None:
    assert safe_rate(1_950, 9_996) == pytest.approx(0.1950780312)


@pytest.mark.parametrize("denominator", [0, -1])
def test_safe_rate_rejects_non_positive_denominator(denominator: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        safe_rate(1, denominator)
