"""Derivação de papel a partir de `sales_teams.csv` — sem senha.

- Sales Agent: nome presente em `sales_agent`
- Supervisor: nome presente em `manager`
- Manager: um dos três `regional_office`

Ordem de resolução: escritório primeiro (conjunto fechado de 3 valores
literais), depois gerente, depois vendedor — os três universos não se
sobrepõem nos dados reais, mas a ordem deixa explícito que um escritório
nunca é confundido com um nome de pessoa.
"""

from __future__ import annotations

from dataclasses import dataclass

from scoring.repository import Dataset

ROLE_SALES_AGENT = "sales_agent"
ROLE_SUPERVISOR = "supervisor"
ROLE_MANAGER = "manager"


class UnknownIdentityError(Exception):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"identidade desconhecida: {name!r}")


@dataclass(frozen=True)
class Identity:
    role: str
    name: str


def list_available_identities(dataset: Dataset) -> dict[str, list[str]]:
    """Lista usada pelo seletor "quem é você" — sem autenticação prévia."""
    teams = dataset.sales_teams
    return {
        "sales_agents": sorted(teams["sales_agent"].dropna().unique().tolist()),
        "supervisors": sorted(teams["manager"].dropna().unique().tolist()),
        "managers": sorted(teams["regional_office"].dropna().unique().tolist()),
    }


def resolve_identity(dataset: Dataset, name: str) -> Identity:
    teams = dataset.sales_teams
    offices = set(teams["regional_office"].dropna())
    managers = set(teams["manager"].dropna())
    agents = set(teams["sales_agent"].dropna())

    if name in offices:
        return Identity(role=ROLE_MANAGER, name=name)
    if name in managers:
        return Identity(role=ROLE_SUPERVISOR, name=name)
    if name in agents:
        return Identity(role=ROLE_SALES_AGENT, name=name)
    raise UnknownIdentityError(name)
