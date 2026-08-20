"""Resolução de escopo — aplicada a todo endpoint de dados.

Um filtro do cliente só pode RESTRINGIR o escopo do token, nunca ampliá-lo:
pedir um vendedor, gerente ou escritório fora do escopo levanta
`OutOfScopeError`, que a camada HTTP traduz para 403.
"""

from __future__ import annotations

from dataclasses import dataclass

from scoring.repository import Dataset

from .identity import Identity, ROLE_MANAGER, ROLE_SALES_AGENT, ROLE_SUPERVISOR


class OutOfScopeError(Exception):
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"{field}={value!r} está fora do escopo do token")


@dataclass(frozen=True)
class Scope:
    role: str
    identity: str
    sales_agents: frozenset[str]
    managers: frozenset[str]
    regional_offices: frozenset[str]


def build_scope(dataset: Dataset, identity: Identity) -> Scope:
    teams = dataset.sales_teams

    if identity.role == ROLE_SALES_AGENT:
        sub = teams[teams["sales_agent"] == identity.name]
    elif identity.role == ROLE_SUPERVISOR:
        sub = teams[teams["manager"] == identity.name]
    elif identity.role == ROLE_MANAGER:
        sub = teams[teams["regional_office"] == identity.name]
    else:
        raise ValueError(f"papel desconhecido: {identity.role!r}")

    return Scope(
        role=identity.role,
        identity=identity.name,
        sales_agents=frozenset(sub["sales_agent"].dropna()),
        managers=frozenset(sub["manager"].dropna()),
        regional_offices=frozenset(sub["regional_office"].dropna()),
    )


def resolve_scoped_agents(
    dataset: Dataset,
    scope: Scope,
    sales_agent: str | None = None,
    manager: str | None = None,
    regional_office: str | None = None,
) -> frozenset[str]:
    """Conjunto de `sales_agent` a que a consulta deve se restringir.

    Parte sempre de `scope.sales_agents` (nunca do universo completo) e
    intersecta com cada filtro informado, validando cada um contra o
    escopo do token antes de aplicá-lo.
    """
    if sales_agent is not None and sales_agent not in scope.sales_agents:
        raise OutOfScopeError("sales_agent", sales_agent)
    if manager is not None and manager not in scope.managers:
        raise OutOfScopeError("manager", manager)
    if regional_office is not None and regional_office not in scope.regional_offices:
        raise OutOfScopeError("regional_office", regional_office)

    teams = dataset.sales_teams
    sub = teams[teams["sales_agent"].isin(scope.sales_agents)]
    if sales_agent is not None:
        sub = sub[sub["sales_agent"] == sales_agent]
    if manager is not None:
        sub = sub[sub["manager"] == manager]
    if regional_office is not None:
        sub = sub[sub["regional_office"] == regional_office]

    return frozenset(sub["sales_agent"])
