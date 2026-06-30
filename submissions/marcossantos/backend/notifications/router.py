"""
notifications/router.py
-----------------------
  GET  /api/notifications/status      → status da configuração de email
  POST /api/notifications/test-alert  → envia email de teste de alerta
  POST /api/notifications/test-digest → envia digest imediato de teste
"""

from fastapi import APIRouter, Depends

from .config import email_config
from .sender import send_critical_alert_email
from .digest import digest_scheduler
from auth.dependencies import require_role

router = APIRouter(prefix="/api/notifications", tags=["Notificações"])


@router.get("/status")
def notification_status(current_user: dict = Depends(require_role("admin"))):
    return {
        "email_enabled":  email_config.enabled,
        "is_configured":  email_config.is_configured,
        "smtp_host":      email_config.host,
        "smtp_port":      email_config.port,
        "from":           email_config.from_address if email_config.user else "não configurado",
        "recipient":      email_config.recipient or "não configurado",
        "digest_enabled": email_config.digest_enabled,
        "digest_time":    email_config.digest_time,
    }


@router.post("/test-alert")
def test_alert_email(current_user: dict = Depends(require_role("admin"))):
    if not email_config.is_configured:
        return {"success": False, "message": "Email não configurado. Preencha o .env."}

    test_alert = {
        "title":            "🧪 Teste de alerta — Lead Scorer",
        "message":          "Este é um email de teste. Se você recebeu, a configuração está correta!",
        "severity":         "critical",
        "account":          "Conta Teste",
        "sales_agent":      current_user.get("name", "Admin"),
        "days_in_pipeline": 15,
        "close_value":      50000,
    }

    success = send_critical_alert_email(test_alert)
    return {
        "success": success,
        "message": f"Email {'enviado' if success else 'falhou'} para {email_config.recipient}.",
    }


@router.post("/test-digest")
async def test_digest_email(current_user: dict = Depends(require_role("admin"))):
    if not email_config.is_configured:
        return {"success": False, "message": "Email não configurado. Preencha o .env."}

    success = await digest_scheduler.send_now()
    return {
        "success": success,
        "message": f"Digest {'enviado' if success else 'falhou'} para {email_config.recipient}.",
    }