"""Task 3.5 — testes unitários da resolução de escopo, independentes da
camada HTTP: os três papéis, incluindo dois supervisores no mesmo
escritório e agentes de escritórios diferentes com nomes de gerente
distintos.
"""

import pytest
from auth.identity import Identity
from auth.scope import OutOfScopeError, build_scope, resolve_scoped_agents


def test_sales_agent_scope_is_just_themselves(dataset):
    identity = Identity(role="sales_agent", name="Anna Snelling")
    scope = build_scope(dataset, identity)
    assert scope.sales_agents == frozenset({"Anna Snelling"})


def test_supervisor_scope_is_direct_reports(dataset):
    identity = Identity(role="supervisor", name="Dustin Brinkmann")
    scope = build_scope(dataset, identity)
    assert scope.sales_agents == frozenset(
        {"Anna Snelling", "Cecily Lampkin", "Versie Hillebrand", "Lajuana Vencill", "Moses Frase"}
    )


def test_manager_scope_is_whole_office(dataset):
    identity = Identity(role="manager", name="Central")
    scope = build_scope(dataset, identity)
    # Central tem dois supervisores (Dustin Brinkmann + Melvin Marxen), 11 agentes.
    assert len(scope.sales_agents) == 11
    assert "Anna Snelling" in scope.sales_agents  # time de Dustin
    assert "Darcel Schlecht" in scope.sales_agents  # time de Melvin


def test_two_supervisors_same_office_have_disjoint_scopes(dataset):
    dustin = build_scope(dataset, Identity(role="supervisor", name="Dustin Brinkmann"))
    melvin = build_scope(dataset, Identity(role="supervisor", name="Melvin Marxen"))
    assert dustin.sales_agents.isdisjoint(melvin.sales_agents)
    # mesmo escritório, times diferentes.
    assert dustin.regional_offices == melvin.regional_offices == frozenset({"Central"})


def test_agents_different_offices_distinct_managers_are_isolated(dataset):
    central_agent = build_scope(dataset, Identity(role="sales_agent", name="Anna Snelling"))
    east_agent = build_scope(dataset, Identity(role="sales_agent", name="Violet Mclelland"))
    assert central_agent.managers == frozenset({"Dustin Brinkmann"})
    assert east_agent.managers == frozenset({"Cara Losch"})
    assert central_agent.sales_agents.isdisjoint(east_agent.sales_agents)


def test_filter_within_scope_narrows(dataset):
    scope = build_scope(dataset, Identity(role="supervisor", name="Dustin Brinkmann"))
    agents = resolve_scoped_agents(dataset, scope, sales_agent="Anna Snelling")
    assert agents == frozenset({"Anna Snelling"})


def test_filter_sales_agent_outside_scope_raises(dataset):
    scope = build_scope(dataset, Identity(role="sales_agent", name="Anna Snelling"))
    with pytest.raises(OutOfScopeError):
        resolve_scoped_agents(dataset, scope, sales_agent="Violet Mclelland")


def test_filter_manager_outside_scope_raises_for_other_supervisor(dataset):
    scope = build_scope(dataset, Identity(role="supervisor", name="Dustin Brinkmann"))
    with pytest.raises(OutOfScopeError):
        resolve_scoped_agents(dataset, scope, manager="Melvin Marxen")


def test_filter_regional_office_outside_scope_raises_for_manager(dataset):
    scope = build_scope(dataset, Identity(role="manager", name="Central"))
    with pytest.raises(OutOfScopeError):
        resolve_scoped_agents(dataset, scope, regional_office="East")


def test_manager_filter_by_manager_within_office_narrows(dataset):
    scope = build_scope(dataset, Identity(role="manager", name="Central"))
    agents = resolve_scoped_agents(dataset, scope, manager="Melvin Marxen")
    assert "Darcel Schlecht" in agents
    assert "Anna Snelling" not in agents
