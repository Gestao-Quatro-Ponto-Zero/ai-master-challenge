"""
alerts/queue.py
---------------
Camada de persistência dos alertas em arquivo JSON.

Responsabilidades:
- Salvar novos alertas sem duplicar os já existentes
- Marcar alertas como dismissed
- Filtrar alertas por usuário (respeitando roles)
- Limpar alertas antigos (TTL de 48h)

Em produção: trocar por SQLite/PostgreSQL + SQLAlchemy.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from .models import Alert

logger = logging.getLogger(__name__)

ALERTS_FILE = Path(__file__).parent.parent / "alerts.json"
ALERT_TTL_HOURS = 48  # alertas somem após 48h se não forem dismissed


# ---------------------------------------------------------------------------
# I/O básico
# ---------------------------------------------------------------------------

def _load_raw() -> list[dict]:
    if not ALERTS_FILE.exists():
        return []
    try:
        return json.loads(ALERTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_raw(alerts: list[dict]) -> None:
    ALERTS_FILE.write_text(
        json.dumps(alerts, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Deduplicação
# ---------------------------------------------------------------------------

def _alert_key(alert: Alert) -> str:
    """
    Chave única por alerta — evita duplicar o mesmo deal/problema
    a cada rodada do scheduler.
    """
    return f"{alert.type}::{alert.opportunity_id or alert.sales_agent}"


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def save_alerts(new_alerts: list[Alert]) -> int:
    """
    Persiste novos alertas, sem duplicar os já existentes.
    Retorna quantos alertas novos foram adicionados.
    """
    raw = _load_raw()

    # Chaves já existentes (não dismissed)
    existing_keys = {
        f"{a['type']}::{a.get('opportunity_id') or a.get('sales_agent')}"
        for a in raw
        if not a.get("dismissed")
    }

    added = 0
    for alert in new_alerts:
        key = _alert_key(alert)
        if key not in existing_keys:
            raw.append(alert.model_dump())
            existing_keys.add(key)
            added += 1

    _save_raw(raw)
    logger.info(f"Alertas: {added} novos adicionados, {len(raw)} total.")
    return added


def get_alerts_for_user(user: dict, include_dismissed: bool = False) -> list[Alert]:
    """
    Retorna alertas filtrados pelo role do usuário:
    - admin   → todos os alertas
    - manager → alertas do seu time
    - agent   → alertas dos seus deals
    """
    raw = _load_raw()
    role = user["role"]

    # Filtra por role
    filtered = []
    for a in raw:
        if role == "admin":
            filtered.append(a)
        elif role == "manager":
            if a.get("manager") == user.get("manager"):
                filtered.append(a)
        elif role == "agent":
            if a.get("sales_agent") == user.get("sales_agent"):
                filtered.append(a)

    # Filtra dismissed se solicitado
    if not include_dismissed:
        filtered = [a for a in filtered if not a.get("dismissed")]

    # Remove alertas expirados (TTL)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=ALERT_TTL_HOURS)
    filtered = [
        a for a in filtered
        if datetime.fromisoformat(a["created_at"]) > cutoff
    ]

    # Ordena: critical primeiro, depois por data desc
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    filtered.sort(
        key=lambda a: (severity_order.get(a["severity"], 99), a["created_at"]),
        reverse=False,
    )
    # Reverte data (mais recente primeiro) dentro de cada severity
    filtered.sort(key=lambda a: severity_order.get(a["severity"], 99))

    return [Alert(**a) for a in filtered]


def dismiss_alert(alert_id: str, user: dict) -> bool:
    """
    Marca um alerta como dismissed pelo usuário.
    Retorna True se encontrado e atualizado.
    """
    raw = _load_raw()
    now = datetime.now(timezone.utc).isoformat()

    for a in raw:
        if a["id"] == alert_id:
            a["dismissed"]    = True
            a["dismissed_at"] = now
            a["dismissed_by"] = user.get("name", user["id"])
            _save_raw(raw)
            return True

    return False


def dismiss_all_for_user(user: dict) -> int:
    """Marca todos os alertas visíveis ao usuário como dismissed."""
    alerts = get_alerts_for_user(user, include_dismissed=False)
    count = 0
    for alert in alerts:
        if dismiss_alert(alert.id, user):
            count += 1
    return count


def purge_old_alerts() -> int:
    """Remove alertas dismissed ou expirados. Chame periodicamente."""
    raw = _load_raw()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=ALERT_TTL_HOURS)

    kept = [
        a for a in raw
        if not a.get("dismissed")
        and datetime.fromisoformat(a["created_at"]) > cutoff
    ]

    removed = len(raw) - len(kept)
    if removed > 0:
        _save_raw(kept)
        logger.info(f"Purge: {removed} alertas removidos.")
    return removed
