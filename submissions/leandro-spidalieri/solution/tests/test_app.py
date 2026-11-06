from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from supportops import ingest

APP = Path(__file__).resolve().parents[1] / "app.py"


def go(app, page):
    app.sidebar.radio[0].set_value(page).run()
    assert not app.exception


def test_no_artifacts_guides_setup_and_impact_still_works(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest, "ARTIFACTS", tmp_path)
    monkeypatch.setattr(ingest, "LOCAL", tmp_path)
    app = AppTest.from_file(str(APP), default_timeout=25).run()
    assert not app.exception
    assert any("audit" in info.value for info in app.info)
    go(app, "Triagem")
    assert any("train" in info.value for info in app.warning)
    go(app, "Qualidade e evidências")
    assert len(app.warning) == 3
    go(app, "Impacto e operação")
    assert app.metric[0].value == "600,0"
    next(w for w in app.number_input if w.label == "Tickets por mês").set_value(0).run()
    assert not app.exception
    assert app.metric[0].value == "0,0"


@pytest.mark.oficial
def test_official_data_navigation_filters_model_and_scenario():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert app.metric[0].value == "8.469"
    app.multiselect[0].set_value(["Email"]).run()
    assert not app.exception
    assert app.metric[0].value == "2.143"
    app.multiselect[3].set_value(["Open"]).run()
    assert app.metric[2].value == "0,0%"
    assert app.metric[3].value == "—"

    go(app, "Triagem")
    next(w for w in app.radio if w.label == "Origem do ticket").set_value(
        "Teste reservado (local)"
    ).run()
    app.selectbox[0].set_value("Sugestão correta").run()
    app.button[0].click().run()
    assert not app.exception
    assert any(w.value == "Sugestão de roteamento" for w in app.success)
    app.selectbox[0].set_value("Encaminhado para revisão").run()
    app.button[0].click().run()
    assert not app.exception
    assert any(w.value == "Revisão humana" for w in app.warning)
    next(w for w in app.radio if w.label == "Origem do ticket").set_value("Texto livre").run()
    app.text_area[0].set_value("Please check the laptop screen and display.").run()
    app.button[0].click().run()
    assert any(w.value == "Revisão humana" for w in app.warning)

    go(app, "Qualidade e evidências")
    assert app.metric[0].label == "Macro-F1 · TF-IDF"
    go(app, "Impacto e operação")
    assert app.metric[1].value == "18,00"
    app.selectbox[0].set_value("Conservador").run()
    assert not app.exception
    assert app.metric[1].value == "3,15"
