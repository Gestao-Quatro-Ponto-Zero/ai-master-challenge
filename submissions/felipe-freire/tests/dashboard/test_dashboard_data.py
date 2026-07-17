import pandas as pd
import pytest
from dashboard.data import apply_filters, audience_cross, kpis, performance_by


@pytest.fixture
def sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "platform": ["A", "A", "B"],
            "content_type": ["video", "image", "video"],
            "content_category": ["tech", "tech", "beauty"],
            "creator_size": ["micro", "micro", "macro"],
            "is_sponsored": [0, 1, 0],
            "audience_age_distribution": ["19-25"] * 3,
            "audience_gender_distribution": ["female", "male", "female"],
            "audience_location": ["Brazil"] * 3,
            "engagement_rate_views": [0.2, 0.1, 0.3],
            "views": [100, 200, 300],
        }
    )


def test_filters_and_kpis_reconcile(sample: pd.DataFrame) -> None:
    filtered = apply_filters(sample, {"platform": ["A"]})
    result = kpis(filtered)
    assert result["posts"] == 2
    assert result["engagement_mean"] == pytest.approx(0.15)
    assert result["sponsored_share"] == pytest.approx(0.5)


def test_performance_by_exposes_sample_size(sample: pd.DataFrame) -> None:
    result = performance_by(sample, "platform")
    assert result["n"].sum() == 3


def test_unsupported_filter_fails_closed(sample: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="unsupported"):
        apply_filters(sample, {"creator_name": ["x"]})


def test_audience_cross_answers_required_contexts(sample: pd.DataFrame) -> None:
    result = audience_cross(sample, "audience_gender_distribution", "platform")
    assert result["n"].sum() == 3
    assert {"platform", "audience_gender_distribution", "engagement_mean"}.issubset(result)


def test_audience_cross_rejects_unsupported_dimensions(sample: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="audience"):
        audience_cross(sample, "creator_name", "platform")
    with pytest.raises(ValueError, match="context"):
        audience_cross(sample, "audience_location", "language")
