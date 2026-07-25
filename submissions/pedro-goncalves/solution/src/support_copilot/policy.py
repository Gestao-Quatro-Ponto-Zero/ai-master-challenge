from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class OperatingMode(str, Enum):
    SHADOW = "Shadow mode"
    ASSISTED = "Assistido"
    SIMULATED_AUTOMATION = "Automação simulada"


HUMAN_ONLY_CATEGORIES = {
    "Access",
    "Administrative rights",
    "HR Support",
}
POLICY_VERSION = "1.2.0"
TAXONOMY_VERSION = "it-service-ticket-v1"


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    requires_human: bool
    simulated: bool

    def to_dict(self) -> dict:
        return asdict(self)


def decide(
    *,
    category: str,
    confidence: float,
    threshold: float,
    mode: OperatingMode,
    kill_switch: bool,
    memory_match: bool = False,
    customer_care_required: bool = False,
) -> Decision:
    if kill_switch:
        return Decision(
            action="HUMAN_REVIEW",
            reason="Kill switch ativo.",
            requires_human=True,
            simulated=False,
        )

    if customer_care_required:
        return Decision(
            action="HUMAN_REVIEW",
            reason="A mensagem contém um sinal de cuidado prioritário com o cliente.",
            requires_human=True,
            simulated=False,
        )

    if category in HUMAN_ONLY_CATEGORIES:
        return Decision(
            action="HUMAN_REVIEW",
            reason="Categoria sensível definida como human-only.",
            requires_human=True,
            simulated=False,
        )

    if memory_match:
        return Decision(
            action="HUMAN_REVIEW",
            reason="A memória aprovada encontrou um erro anterior parecido.",
            requires_human=True,
            simulated=False,
        )

    if confidence < threshold:
        return Decision(
            action="ABSTAIN",
            reason=f"Confiança {confidence:.1%} abaixo do threshold {threshold:.0%}.",
            requires_human=True,
            simulated=False,
        )

    if mode == OperatingMode.SHADOW:
        return Decision(
            action="SHADOW_RECOMMENDATION",
            reason="Shadow mode registra a recomendação sem executar ações.",
            requires_human=True,
            simulated=False,
        )

    if mode == OperatingMode.ASSISTED:
        return Decision(
            action="HUMAN_APPROVAL",
            reason="Recomendação pronta; humano aprova ou corrige.",
            requires_human=True,
            simulated=False,
        )

    return Decision(
        action="SIMULATED_ROUTE",
        reason="Critérios técnicos atendidos, mas nenhuma ação externa é executada.",
        requires_human=False,
        simulated=True,
    )
