"""
Auto-assignment de tickets para agentes online.

Algoritmo: least-loaded (agente com menos tickets abertos).
Empate: primeiro agente encontrado (FIFO).
"""

import logging
from schemas import StatusAgente
from database import db

logger = logging.getLogger(__name__)


def atribuir_automaticamente(ticket_id: str) -> str | None:
    """
    Atribui o ticket ao agente online com menor carga.
    Retorna o nome do agente ou None se nenhum disponível.
    """
    db.recalcular_cargas_agentes()
    agentes_online = [
        a for a in db.agentes.values()
        if a.status == StatusAgente.ONLINE
    ]

    if not agentes_online:
        logger.warning("Nenhum agente online para auto-assignment do ticket %s", ticket_id)
        return None

    agentes_online.sort(key=lambda a: a.tickets_atribuidos)
    agente = agentes_online[0]

    ticket = db.obter_ticket(ticket_id)
    if ticket:
        ticket.agente_responsavel = agente.nome
        db.recalcular_cargas_agentes()
        carga = db.agentes[agente.nome].tickets_atribuidos
        logger.info("Ticket %s atribuído a %s (carga: %d tickets)",
                     ticket_id, agente.nome, carga)
        return agente.nome

    return None
