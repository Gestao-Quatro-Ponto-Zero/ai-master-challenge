
"""Headless smoke test: the Streamlit app must load without raising."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[2] / "dashboard" / "app.py"


def test_app_runs_headless_without_exception() -> None:
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    assert not at.exception
    assert len(at.metric) == 4
    rendered = " ".join(item.value for item in at.subheader)
    assert "O que gera engajamento?" in rendered
    assert "Patrocínio funciona?" in rendered
    assert "Qual audiência mais engaja?" in rendered
