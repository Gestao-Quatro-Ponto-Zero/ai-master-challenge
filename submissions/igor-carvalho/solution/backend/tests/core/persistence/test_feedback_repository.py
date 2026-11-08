import pytest
from sqlalchemy.exc import IntegrityError

from lead_core.persistence import FeedbackRepository


def add_feedback(repo, **kw):
    base = dict(opportunity_id="D1", user_key="ana-souza", action="worked", comment=None, model_version="1",
                score=80, band="focus")
    return repo.add(**{**base, **kw})


def test_feedback_roundtrip_and_ordering(database, users):
    repo = FeedbackRepository(database)
    ids = [add_feedback(repo, action=a)["id"] for a in ("worked", "ignore", "disagree")]
    assert ids == [1, 2, 3]
    assert [h["action"] for h in repo.history("D1")] == ["disagree", "ignore", "worked"]
    assert repo.history("OUTRO") == []
    assert "score_at_feedback" not in repo.history("D1")[0]


def test_feedback_keeps_snapshot_of_score_and_band(database, users):
    repo = FeedbackRepository(database)
    add_feedback(repo, score=None, band="review")
    row = repo.all()[0]
    assert row["score_at_feedback"] is None and row["band_at_feedback"] == "review" and row["model_version"] == "1"


@pytest.mark.parametrize("kw", [{"action": "talvez"}, {"comment": "x" * 281}, {"user_key": "fantasma"}, {"score": 101}])
def test_feedback_database_constraints_are_enforced(database, users, kw):
    with pytest.raises(IntegrityError):
        add_feedback(FeedbackRepository(database), **kw)


def test_feedback_comment_of_280_chars_is_accepted(database, users):
    add_feedback(FeedbackRepository(database), comment="x" * 280)
