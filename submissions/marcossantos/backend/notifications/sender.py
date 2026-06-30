"""
notifications/sender.py
-----------------------
Envio de email via SMTP Gmail com dois templates:
1. Alerta crítico — enviado imediatamente
2. Resumo diário — snapshot do pipeline
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Optional

from .config import email_config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core — envio SMTP
# ---------------------------------------------------------------------------

def _send_email(subject: str, html_body: str, recipient: Optional[str] = None) -> bool:
    if not email_config.is_configured:
        logger.warning("Email não configurado. Verifique o .env.")
        return False

    to = recipient or email_config.recipient

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = email_config.from_address
        msg["To"]      = to
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(email_config.host, email_config.port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(email_config.user, email_config.password)
            server.sendmail(email_config.user, to, msg.as_string())

        logger.info(f"Email enviado para {to}: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("Falha de autenticação SMTP. Verifique EMAIL_USER e EMAIL_PASSWORD no .env.")
        return False
    except Exception as e:
        logger.error(f"Erro ao enviar email: {e}")
        return False


# ---------------------------------------------------------------------------
# Template base
# ---------------------------------------------------------------------------

def _base_template(content: str, title: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#F4F6F9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F4F6F9;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:#0F1C2E;padding:20px 28px;">
            <table width="100%" cellpadding="0" cellspacing="0"><tr>
              <td>
                <span style="background:#1B6FDE;border-radius:6px;padding:6px 10px;margin-right:10px;vertical-align:middle;">📊</span>
                <span style="color:#fff;font-size:16px;font-weight:700;vertical-align:middle;">Lead Scorer</span>
              </td>
              <td align="right">
                <span style="color:#64748B;font-size:11px;">{datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
              </td>
            </tr></table>
          </td>
        </tr>

        <!-- Content -->
        <tr><td style="padding:28px;">{content}</td></tr>

        <!-- Footer -->
        <tr>
          <td style="background:#F8FAFC;padding:16px 28px;border-top:1px solid #E2E8F0;">
            <p style="margin:0;font-size:11px;color:#94A3B8;text-align:center;">
              Lead Scorer · Sales Intelligence · Notificação automática
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def _severity_color(severity: str) -> tuple:
    if severity == "critical": return "#DC2626", "#FEF2F2", "#FECACA"
    if severity == "warning":  return "#D97706", "#FFFBEB", "#FDE68A"
    return "#475569", "#F8FAFC", "#E2E8F0"


# ---------------------------------------------------------------------------
# Email 1 — Alerta crítico
# ---------------------------------------------------------------------------

def send_critical_alert_email(alert: dict) -> bool:
    severity = alert.get("severity", "warning")
    color, bg, border = _severity_color(severity)

    account   = alert.get("account") or "—"
    agent     = alert.get("sales_agent") or "—"
    days      = alert.get("days_in_pipeline", "—")
    value     = alert.get("close_value", 0) or 0
    value_str = f"${value:,.0f}" if value else "—"

    content = f"""
    <h2 style="margin:0 0 4px;font-size:20px;color:#0F172A;">{alert.get('title','Alerta de Deal')}</h2>
    <p style="margin:0 0 20px;font-size:13px;color:#64748B;">Ação necessária no seu pipeline</p>

    <div style="background:{bg};border:1px solid {border};border-left:4px solid {color};border-radius:8px;padding:16px;margin-bottom:20px;">
      <p style="margin:0;font-size:13px;color:{color};font-weight:600;line-height:1.6;">{alert.get('message','')}</p>
    </div>

    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
      <tr>
        <td width="50%" style="padding:0 8px 0 0;">
          <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:6px;padding:12px;">
            <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;margin-bottom:4px;">Conta</div>
            <div style="font-size:14px;font-weight:600;color:#0F172A;">{account}</div>
          </div>
        </td>
        <td width="50%" style="padding:0 0 0 8px;">
          <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:6px;padding:12px;">
            <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;margin-bottom:4px;">Vendedor</div>
            <div style="font-size:14px;font-weight:600;color:#0F172A;">{agent}</div>
          </div>
        </td>
      </tr>
      <tr><td colspan="2" style="padding:8px 0 0;"></td></tr>
      <tr>
        <td width="50%" style="padding:0 8px 0 0;">
          <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:6px;padding:12px;">
            <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;margin-bottom:4px;">Dias no Pipeline</div>
            <div style="font-size:14px;font-weight:700;color:{color};">{days}d</div>
          </div>
        </td>
        <td width="50%" style="padding:0 0 0 8px;">
          <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:6px;padding:12px;">
            <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;margin-bottom:4px;">Valor do Deal</div>
            <div style="font-size:14px;font-weight:700;color:#1B6FDE;">{value_str}</div>
          </div>
        </td>
      </tr>
    </table>

    <p style="font-size:13px;color:#475569;margin:0;">
      Acesse o <a href="http://localhost:5173" style="color:#1B6FDE;font-weight:600;">Lead Scorer Dashboard</a> para tomar ação.
    </p>
    """

    subject = f"🚨 {alert.get('title','Alerta crítico')} — Lead Scorer"
    return _send_email(subject, _base_template(content, subject))


# ---------------------------------------------------------------------------
# Email 2 — Resumo diário
# ---------------------------------------------------------------------------

def send_daily_digest(summary: dict, top_deals: list, alerts_count: int) -> bool:
    hot       = summary.get("hot", 0)
    warm      = summary.get("warm", 0)
    cold      = summary.get("cold", 0)
    total     = summary.get("total", 0)
    value     = summary.get("pipeline_value", 0)
    value_str = f"${value:,.0f}" if value else "$0"

    kpi_row = f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
      <tr>
        <td width="25%" style="padding:0 6px 0 0;">
          <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:6px;padding:12px;text-align:center;">
            <div style="font-size:10px;color:#DC2626;font-weight:600;margin-bottom:4px;">🔥 HOT</div>
            <div style="font-size:24px;font-weight:800;color:#DC2626;">{hot}</div>
          </div>
        </td>
        <td width="25%" style="padding:0 6px;">
          <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:6px;padding:12px;text-align:center;">
            <div style="font-size:10px;color:#D97706;font-weight:600;margin-bottom:4px;">🌡 WARM</div>
            <div style="font-size:24px;font-weight:800;color:#D97706;">{warm}</div>
          </div>
        </td>
        <td width="25%" style="padding:0 6px;">
          <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:6px;padding:12px;text-align:center;">
            <div style="font-size:10px;color:#64748B;font-weight:600;margin-bottom:4px;">❄ COLD</div>
            <div style="font-size:24px;font-weight:800;color:#64748B;">{cold}</div>
          </div>
        </td>
        <td width="25%" style="padding:0 0 0 6px;">
          <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:6px;padding:12px;text-align:center;">
            <div style="font-size:10px;color:#1D4ED8;font-weight:600;margin-bottom:4px;">💰 PIPELINE</div>
            <div style="font-size:18px;font-weight:800;color:#1D4ED8;">{value_str}</div>
          </div>
        </td>
      </tr>
    </table>
    """

    alerts_section = ""
    if alerts_count > 0:
        alerts_section = f"""
        <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:14px;margin-bottom:20px;">
          <p style="margin:0;font-size:13px;color:#DC2626;font-weight:600;">
            🔔 {alerts_count} alerta(s) ativo(s) — acesse o dashboard para ver os detalhes.
          </p>
        </div>
        """

    deals_rows = ""
    for deal in top_deals[:5]:
        score = deal.get("score", 0)
        score_color = "#DC2626" if score >= 70 else "#D97706" if score >= 45 else "#64748B"
        deals_rows += f"""
        <tr style="border-bottom:1px solid #F1F5F9;">
          <td style="padding:10px 12px;font-size:13px;font-weight:700;color:{score_color};">{score}</td>
          <td style="padding:10px 12px;font-size:13px;color:#0F172A;">{deal.get('account','—')}</td>
          <td style="padding:10px 12px;font-size:11px;color:#64748B;">{deal.get('deal_stage','—')}</td>
          <td style="padding:10px 12px;font-size:13px;font-weight:600;color:#1B6FDE;">${deal.get('close_value',0):,.0f}</td>
          <td style="padding:10px 12px;font-size:11px;color:#475569;">{deal.get('sales_agent','—')}</td>
        </tr>
        """

    content = f"""
    <h2 style="margin:0 0 4px;font-size:20px;color:#0F172A;">Bom dia! Seu pipeline de hoje</h2>
    <p style="margin:0 0 20px;font-size:13px;color:#64748B;">{total} deals ativos · {datetime.now().strftime('%A, %d de %B')}</p>

    {alerts_section}
    {kpi_row}

    <h3 style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 10px;">Top 5 Deals por Score</h3>
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E2E8F0;border-radius:8px;overflow:hidden;margin-bottom:20px;">
      <thead>
        <tr style="background:#F8FAFC;">
          <th style="padding:8px 12px;text-align:left;font-size:10px;color:#94A3B8;font-weight:600;text-transform:uppercase;">Score</th>
          <th style="padding:8px 12px;text-align:left;font-size:10px;color:#94A3B8;font-weight:600;text-transform:uppercase;">Conta</th>
          <th style="padding:8px 12px;text-align:left;font-size:10px;color:#94A3B8;font-weight:600;text-transform:uppercase;">Stage</th>
          <th style="padding:8px 12px;text-align:left;font-size:10px;color:#94A3B8;font-weight:600;text-transform:uppercase;">Valor</th>
          <th style="padding:8px 12px;text-align:left;font-size:10px;color:#94A3B8;font-weight:600;text-transform:uppercase;">Vendedor</th>
        </tr>
      </thead>
      <tbody>{deals_rows}</tbody>
    </table>

    <p style="font-size:13px;color:#475569;margin:0;">
      Ver pipeline completo no <a href="http://localhost:5173" style="color:#1B6FDE;font-weight:600;">Lead Scorer Dashboard</a>
    </p>
    """

    subject = f"📊 Pipeline do dia — {hot} deals quentes · Lead Scorer"
    return _send_email(subject, _base_template(content, subject))