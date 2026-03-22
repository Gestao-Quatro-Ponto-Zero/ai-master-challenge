"""
Testes TDD para components/filters.py — logica pura de filtros.

Testa apenas funcoes puras (sem Streamlit):
- _get_manager_options: cascade de managers por escritorio
- _get_agent_options: cascade de agentes por escritorio/manager
- apply_filters: filtros combinados com logica AND
- FilterState: dataclass de estado dos filtros
"""

import pandas as pd
import pytest

from components.filters import (
    OPTION_ALL,
    FilterState,
    _get_agent_options,
    _get_manager_options,
    apply_filters,
)


# ---------------------------------------------------------------------------
# Fixtures — DataFrames sinteticos que replicam a estrutura real
# ---------------------------------------------------------------------------


@pytest.fixture
def df_teams() -> pd.DataFrame:
    """DataFrame sintetico de sales_teams com 3 escritorios, 6 managers, 35 sellers."""
    rows = []
    # Central — Dustin Brinkmann (5 sellers)
    for name in [
        "Anna Snelling",
        "Cecily Lampkin",
        "Lajuana Vencill",
        "Moses Frase",
        "Versie Hillebrand",
    ]:
        rows.append(
            {
                "sales_agent": name,
                "manager": "Dustin Brinkmann",
                "regional_office": "Central",
            }
        )
    # Central — Melvin Marxen (6 sellers)
    for name in [
        "Darcel Schlecht",
        "Gladys Colclough",
        "Jonathan Berthelot",
        "Marty Freudenburg",
        "Mei-Mei Johns",
        "Niesha Huffines",
    ]:
        rows.append(
            {
                "sales_agent": name,
                "manager": "Melvin Marxen",
                "regional_office": "Central",
            }
        )
    # East — Cara Losch (6 sellers)
    for name in [
        "Corliss Cosme",
        "Elizabeth Anderson",
        "Garret Kinder",
        "Rosie Papadopoulos",
        "Violet Mclelland",
        "Wilburn Farren",
    ]:
        rows.append(
            {
                "sales_agent": name,
                "manager": "Cara Losch",
                "regional_office": "East",
            }
        )
    # East — Rocco Neubert (6 sellers)
    for name in [
        "Boris Faz",
        "Cassey Cress",
        "Daniell Hammack",
        "Donn Cantrell",
        "Natalya Ivanova",
        "Reed Clapper",
    ]:
        rows.append(
            {
                "sales_agent": name,
                "manager": "Rocco Neubert",
                "regional_office": "East",
            }
        )
    # West — Celia Rouche (6 sellers)
    for name in [
        "Carol Thompson",
        "Elease Gluck",
        "Hayden Neloms",
        "Markita Hansen",
        "Rosalina Dieter",
        "Vicki Laflamme",
    ]:
        rows.append(
            {
                "sales_agent": name,
                "manager": "Celia Rouche",
                "regional_office": "West",
            }
        )
    # West — Summer Sewald (6 sellers)
    for name in [
        "Carl Lin",
        "James Ascencio",
        "Kami Bicknell",
        "Kary Hendrixson",
        "Maureen Marcano",
        "Zane Levy",
    ]:
        rows.append(
            {
                "sales_agent": name,
                "manager": "Summer Sewald",
                "regional_office": "West",
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture
def df_pipeline() -> pd.DataFrame:
    """DataFrame sintetico de pipeline enriquecido com colunas necessarias para filtros."""
    rows = [
        {
            "sales_agent": "Anna Snelling",
            "manager": "Dustin Brinkmann",
            "regional_office": "Central",
            "product": "GTX Basic",
            "sector": "technology",
            "score": 85,
            "is_zombie": False,
            "deal_stage": "Engaging",
        },
        {
            "sales_agent": "Anna Snelling",
            "manager": "Dustin Brinkmann",
            "regional_office": "Central",
            "product": "GTX Pro",
            "sector": "finance",
            "score": 45,
            "is_zombie": True,
            "deal_stage": "Engaging",
        },
        {
            "sales_agent": "Darcel Schlecht",
            "manager": "Melvin Marxen",
            "regional_office": "Central",
            "product": "MG Special",
            "sector": "retail",
            "score": 60,
            "is_zombie": False,
            "deal_stage": "Prospecting",
        },
        {
            "sales_agent": "Corliss Cosme",
            "manager": "Cara Losch",
            "regional_office": "East",
            "product": "GTX Basic",
            "sector": "technology",
            "score": 72,
            "is_zombie": False,
            "deal_stage": "Engaging",
        },
        {
            "sales_agent": "Boris Faz",
            "manager": "Rocco Neubert",
            "regional_office": "East",
            "product": "GTK 500",
            "sector": "medical",
            "score": 30,
            "is_zombie": True,
            "deal_stage": "Engaging",
        },
        {
            "sales_agent": "Carol Thompson",
            "manager": "Celia Rouche",
            "regional_office": "West",
            "product": "GTX Plus Pro",
            "sector": "software",
            "score": 90,
            "is_zombie": False,
            "deal_stage": "Engaging",
        },
        {
            "sales_agent": "Carl Lin",
            "manager": "Summer Sewald",
            "regional_office": "West",
            "product": "MG Advanced",
            "sector": "marketing",
            "score": 55,
            "is_zombie": False,
            "deal_stage": "Prospecting",
        },
    ]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Cascade tests — _get_manager_options
# ---------------------------------------------------------------------------


class TestGetManagerOptions:
    """Testes do cascade de managers por escritorio."""

    def test_manager_options_filtered_by_office_central(self, df_teams):
        """Selecionar 'Central' retorna apenas Dustin Brinkmann e Melvin Marxen."""
        result = _get_manager_options(df_teams, "Central")
        assert result[0] == OPTION_ALL
        managers = result[1:]
        assert managers == ["Dustin Brinkmann", "Melvin Marxen"]

    def test_manager_options_filtered_by_office_east(self, df_teams):
        """Selecionar 'East' retorna apenas Cara Losch e Rocco Neubert."""
        result = _get_manager_options(df_teams, "East")
        assert result[0] == OPTION_ALL
        managers = result[1:]
        assert managers == ["Cara Losch", "Rocco Neubert"]

    def test_manager_options_all_when_office_todos(self, df_teams):
        """Selecionar 'Todos' retorna todos os 6 managers."""
        result = _get_manager_options(df_teams, OPTION_ALL)
        assert result[0] == OPTION_ALL
        managers = result[1:]
        assert len(managers) == 6
        assert "Dustin Brinkmann" in managers
        assert "Melvin Marxen" in managers
        assert "Cara Losch" in managers
        assert "Rocco Neubert" in managers
        assert "Celia Rouche" in managers
        assert "Summer Sewald" in managers
        # Deve estar ordenado
        assert managers == sorted(managers)


# ---------------------------------------------------------------------------
# Cascade tests — _get_agent_options
# ---------------------------------------------------------------------------


class TestGetAgentOptions:
    """Testes do cascade de agentes por escritorio e manager."""

    def test_agent_options_filtered_by_manager(self, df_teams):
        """Selecionar manager 'Cara Losch' retorna apenas seus 6 sellers."""
        result = _get_agent_options(df_teams, "East", "Cara Losch")
        assert result[0] == OPTION_ALL
        agents = result[1:]
        assert len(agents) == 6
        assert "Corliss Cosme" in agents
        assert "Elizabeth Anderson" in agents
        assert "Garret Kinder" in agents
        assert agents == sorted(agents)

    def test_agent_options_all_when_manager_todos(self, df_teams):
        """Selecionar 'Todos' com regiao 'East' retorna todos os sellers do East (12)."""
        result = _get_agent_options(df_teams, "East", OPTION_ALL)
        assert result[0] == OPTION_ALL
        agents = result[1:]
        assert len(agents) == 12
        # Inclui sellers de ambos os managers do East
        assert "Corliss Cosme" in agents
        assert "Boris Faz" in agents
        assert agents == sorted(agents)


# ---------------------------------------------------------------------------
# apply_filters tests
# ---------------------------------------------------------------------------


class TestApplyFilters:
    """Testes da funcao apply_filters com logica AND."""

    def _make_filters(self, **overrides) -> FilterState:
        """Cria FilterState com defaults que nao filtram nada."""
        defaults = {
            "office": OPTION_ALL,
            "manager": OPTION_ALL,
            "agent": OPTION_ALL,
            "products": [],
            "sectors": [],
            "score_min": 0,
            "score_max": 100,
            "zombie_mode": "Todos os deals",
        }
        defaults.update(overrides)
        return FilterState(**defaults)

    def test_apply_filters_office_filters_by_regional_office(self, df_pipeline):
        """Filtrar por escritorio 'Central' retorna apenas deals do Central."""
        filters = self._make_filters(office="Central")
        result = apply_filters(df_pipeline, filters)
        assert len(result) == 3
        assert set(result["regional_office"].unique()) == {"Central"}

    def test_apply_filters_manager_filters_by_manager(self, df_pipeline):
        """Filtrar por manager 'Cara Losch' retorna apenas deals dela."""
        filters = self._make_filters(manager="Cara Losch")
        result = apply_filters(df_pipeline, filters)
        assert len(result) == 1
        assert result.iloc[0]["sales_agent"] == "Corliss Cosme"

    def test_apply_filters_agent_filters_by_sales_agent(self, df_pipeline):
        """Filtrar por agente 'Anna Snelling' retorna apenas deals dela."""
        filters = self._make_filters(agent="Anna Snelling")
        result = apply_filters(df_pipeline, filters)
        assert len(result) == 2
        assert all(result["sales_agent"] == "Anna Snelling")

    def test_apply_filters_products_multiselect(self, df_pipeline):
        """Filtrar por produtos especificos retorna apenas esses produtos."""
        filters = self._make_filters(products=["GTX Basic", "GTX Pro"])
        result = apply_filters(df_pipeline, filters)
        assert len(result) == 3
        assert set(result["product"].unique()) == {"GTX Basic", "GTX Pro"}

    def test_apply_filters_score_range(self, df_pipeline):
        """Filtrar por range de score retorna deals dentro do range."""
        filters = self._make_filters(score_min=50, score_max=80)
        result = apply_filters(df_pipeline, filters)
        assert all(result["score"].between(50, 80))
        # Deals com score 60, 72, 55 => 3 deals
        assert len(result) == 3

    def test_apply_filters_zombie_mode_apenas_zumbis(self, df_pipeline):
        """Modo 'Apenas zumbis' retorna apenas deals com is_zombie=True."""
        filters = self._make_filters(zombie_mode="Apenas zumbis")
        result = apply_filters(df_pipeline, filters)
        assert len(result) == 2
        assert all(result["is_zombie"])

    def test_apply_filters_zombie_mode_ocultar_zumbis(self, df_pipeline):
        """Modo 'Ocultar zumbis' retorna apenas deals com is_zombie=False."""
        filters = self._make_filters(zombie_mode="Ocultar zumbis")
        result = apply_filters(df_pipeline, filters)
        assert len(result) == 5
        assert not any(result["is_zombie"])

    def test_apply_filters_combined_and_logic(self, df_pipeline):
        """Combinacao de filtros aplica logica AND."""
        filters = self._make_filters(
            office="Central",
            zombie_mode="Ocultar zumbis",
            score_min=50,
            score_max=100,
        )
        result = apply_filters(df_pipeline, filters)
        # Central + nao-zumbi + score>=50: Anna(85) e Darcel(60)
        assert len(result) == 2
        assert all(result["regional_office"] == "Central")
        assert not any(result["is_zombie"])
        assert all(result["score"] >= 50)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Testes de casos limite."""

    def _make_filters(self, **overrides) -> FilterState:
        """Cria FilterState com defaults que nao filtram nada."""
        defaults = {
            "office": OPTION_ALL,
            "manager": OPTION_ALL,
            "agent": OPTION_ALL,
            "products": [],
            "sectors": [],
            "score_min": 0,
            "score_max": 100,
            "zombie_mode": "Todos os deals",
        }
        defaults.update(overrides)
        return FilterState(**defaults)

    def test_apply_filters_empty_products_returns_all(self, df_pipeline):
        """Lista vazia de produtos retorna todos os deals (sem filtro de produto)."""
        filters = self._make_filters(products=[])
        result = apply_filters(df_pipeline, filters)
        assert len(result) == len(df_pipeline)

    def test_apply_filters_returns_empty_when_no_match(self, df_pipeline):
        """Filtro impossivel retorna DataFrame vazio."""
        filters = self._make_filters(
            office="Central",
            score_min=95,
            score_max=100,
        )
        result = apply_filters(df_pipeline, filters)
        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)

    def test_filter_state_dataclass_has_expected_fields(self):
        """FilterState contem todos os campos esperados."""
        state = FilterState(
            office="Central",
            manager="Dustin Brinkmann",
            agent="Anna Snelling",
            products=["GTX Basic"],
            sectors=["technology"],
            score_min=0,
            score_max=100,
            zombie_mode="Todos os deals",
        )
        assert state.office == "Central"
        assert state.manager == "Dustin Brinkmann"
        assert state.agent == "Anna Snelling"
        assert state.products == ["GTX Basic"]
        assert state.sectors == ["technology"]
        assert state.score_min == 0
        assert state.score_max == 100
        assert state.zombie_mode == "Todos os deals"
