from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_dashboard_script_covers_operational_states() -> None:
    script = _read("public/app.js")
    assert "A carregar oportunidades" in script
    assert "getDashboardKpis" in script
    assert "Nenhum resultado com estes filtros" in script
    assert "Não foi possível carregar o ranking" in script
    assert "Oportunidade não encontrada." in script
    assert "Erro ao carregar o detalhe" in script
    assert "Pedido de detalhe cancelado." in script


def test_dashboard_script_preserves_selection_and_keyboard_accessibility() -> None:
    script = _read("public/app.js")
    assert "selectedOpportunityId" in script
    assert "hasSelectedInCurrentResult" in script
    assert 'event.key === "Enter" || event.key === " "' in script
    assert 'row.classList.toggle("is-selected"' in script


def test_drawer_controls_are_explicit_in_markup() -> None:
    html = _read("public/index.html")
    assert 'id="detail-retry"' in html
    assert 'id="detail-close"' in html
    assert 'id="filters-clear"' in html
    assert 'aria-live="polite"' in html
    assert 'id="ranking-table"' in html
    assert 'id="kpi-strip"' in html


def test_mock_fixture_contract_stays_aligned_with_ui_expectations() -> None:
    list_fixture = _read("public/infrastructure/mocks/fixtures/opportunity-list.js")
    detail_fixture = _read("public/infrastructure/mocks/fixtures/opportunity-detail.js")
    assert "id:" in list_fixture
    assert "title:" in list_fixture
    assert "deal_stage:" in list_fixture
    assert "product:" in list_fixture
    assert "score:" in list_fixture
    assert "scoreExplanation" in detail_fixture
    assert "priority_band" in detail_fixture
    assert "next_action" in detail_fixture
