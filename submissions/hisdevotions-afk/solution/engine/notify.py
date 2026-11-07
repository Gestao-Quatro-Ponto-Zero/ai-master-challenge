"""Bot de notificação: manda a fila de prioridades do dia por Slack ou email.

Lê o data.json que scoring.py já gera — mesmas filas, mesmos motivos e mesma
ação recomendada que o app mostra na tela "Meu dia". Nenhum texto novo,
nenhuma chamada a LLM: o bot só reformata o que o motor já calculou.

Uso:
  python3 notify.py --agent "Hayden Neloms"                    # imprime no terminal (sem enviar)
  python3 notify.py --agent "Hayden Neloms" --webhook $URL      # manda pro Slack (incoming webhook)
  python3 notify.py --agent "Hayden Neloms" --to vendedor@ex.com  # manda por email (precisa de SMTP_HOST no ambiente)
  python3 notify.py                                             # digest da empresa inteira, uma mensagem só

  python3 notify.py --all                                       # digest de cada um dos 35 vendedores, impresso (sem destino)
  python3 notify.py --all --targets targets.json                # ...mandado pro destino de cada um (ver targets.example.json);
                                                                  # quem não estiver no arquivo cai no modo seguro (só imprime)

Variáveis de ambiente aceitas no lugar das flags: SLACK_WEBHOOK_URL, NOTIFY_EMAIL_TO,
SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASS, SMTP_FROM.

`sales_teams.csv` não tem email nem canal de Slack de ninguém, então não dá pra
descobrir o destino de cada vendedor a partir do dataset — `targets.json` é o
diretório vendedor→destino que, na vida real, a RevOps manteria (em produção
viria do SSO/diretório da empresa, não de um arquivo à parte).
"""
from __future__ import annotations

import argparse
import json
import os
import smtplib
import urllib.request
from email.message import EmailMessage
from pathlib import Path

import scoring as s

# (bucket, título, quantos mostrar, ordenação, valor mostrado na linha)
# fechar/avancar: receita esperada (tem score). decidir: maior valor primeiro
# (o que mais infla o forecast). prospectar: sem score nem forecast (não há
# histórico de conversão) — ordena e mostra pelo valor de lista.
QUEUES = [
    ("fechar", "Feche esta semana", 6, lambda d: -d["ev_soon"], lambda d: f"{s._money(d['ev_soon'])} em 30d"),
    ("decidir", "Decida o destino", 4, lambda d: -d["price"], lambda d: f"{s._money(d['price'])} parado"),
    ("avancar", "Mantenha em movimento", 4, lambda d: -d["ev"], lambda d: f"{s._money(d['ev'])} esperado"),
    ("prospectar", "Engaje", 4, lambda d: -d["price"], lambda d: f"{s._money(d['price'])} em potencial"),
]


def _name(d: dict) -> str:
    return f"{d['account'] or 'Sem conta vinculada'} — {d['product']}"


def build_digest(data: dict, agent: str | None) -> str:
    """Mesma estrutura da tela 'Meu dia': 4 filas, cada uma com a ação de cada deal."""
    open_deals = [d for d in data["deals"] if d["stage"] in s.OPEN_STAGES and (agent is None or d["agent"] == agent)]
    lines = [f"Bom dia, {agent.split(' ')[0]}." if agent else "Semana da empresa inteira.", ""]
    for bucket, title, cap, key, fmt in QUEUES:
        queue = sorted((d for d in open_deals if d["bucket"] == bucket), key=key)
        lines.append(f"*{title}* ({len(queue)})")
        if not queue:
            lines.append("  (nenhum deal)")
        for d in queue[:cap]:
            lines.append(f"  - {_name(d)} — {fmt(d)}: {d['action']}")
        lines.append("")
    no_account = sum(1 for d in open_deals if not d["account"])
    if no_account:
        lines.append(f"{no_account} {'deal' if no_account == 1 else 'deals'} sem conta vinculada. Cadastre a empresa no CRM.")
    return "\n".join(lines).strip()


def send_slack(webhook: str, text: str) -> None:
    body = json.dumps({"text": text}).encode()
    req = urllib.request.Request(webhook, data=body, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)


def send_email(to: str, subject: str, text: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ.get("SMTP_FROM", "pipeline-em-foco@localhost")
    msg["To"] = to
    msg.set_content(text)
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "587")), timeout=10) as smtp:
        smtp.starttls()
        user = os.environ.get("SMTP_USER")
        if user:
            smtp.login(user, os.environ["SMTP_PASS"])
        smtp.send_message(msg)


# ─── time inteiro numa chamada só (--all) ───────────────────────────────────

def load_targets(path: Path | None) -> dict[str, dict[str, str]]:
    """`targets.json`: {"Nome do vendedor": {"webhook": "...", "to": "..."}}.
    Sem arquivo (ou vendedor fora dele), cai no fallback global ou no modo
    seguro — nunca falha por destino faltando."""
    return json.loads(path.read_text(encoding="utf-8")) if path else {}


def destination(agent: str, targets: dict, webhook: str | None, to: str | None) -> tuple[str | None, str | None]:
    """Destino do vendedor: o que estiver em `targets.json` vence; sem entrada
    lá, cai no --webhook/--to globais (útil pra, por exemplo, mandar o digest
    de todo mundo pro mesmo canal de QA)."""
    t = targets.get(agent, {})
    return t.get("webhook", webhook), t.get("to", to)


def run_all(data: dict, targets: dict, webhook: str | None, to: str | None,
            send_slack=send_slack, send_email=send_email) -> list[str]:
    """Um digest por vendedor do roster (`sales_teams.csv`, 35 nomes, com ou sem
    deal aberto). `send_slack`/`send_email` são injetáveis pra testar a lógica
    de destino sem rede nem SMTP de verdade."""
    out = []
    for agent in sorted(a["name"] for a in data["agents"]):
        text = build_digest(data, agent)
        wh, mail = destination(agent, targets, webhook, to)
        if not wh and not mail:
            out.append(f"=== {agent} (sem destino configurado) ===\n{text}")
            continue
        sent = []
        if wh:
            send_slack(wh, text)
            sent.append("Slack")
        if mail:
            send_email(mail, f"Pipeline em Foco — {agent}", text)
            sent.append("email")
        out.append(f"-> {agent}: {'+'.join(sent)}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--agent", help="nome exato do vendedor (sales_agent); omitido = digest da empresa inteira")
    ap.add_argument("--all", action="store_true", help="um digest por vendedor do roster, não a empresa inteira numa mensagem só")
    ap.add_argument("--targets", type=Path, help="JSON {vendedor: {webhook, to}} usado só com --all (ver targets.example.json)")
    ap.add_argument("--data", type=Path, default=s.DEFAULT_OUT, help="data.json gerado por scoring.py")
    ap.add_argument("--webhook", default=os.environ.get("SLACK_WEBHOOK_URL"), help="URL do incoming webhook do Slack")
    ap.add_argument("--to", default=os.environ.get("NOTIFY_EMAIL_TO"), help="email de destino (requer SMTP_HOST no ambiente)")
    args = ap.parse_args()
    if args.all and args.agent:
        ap.error("--all já cobre todo mundo; não use junto com --agent")

    data = json.loads(args.data.read_text(encoding="utf-8"))

    if args.all:
        for line in run_all(data, load_targets(args.targets), args.webhook, args.to):
            print(line)
        return

    text = build_digest(data, args.agent)
    if not args.webhook and not args.to:
        print(text)
        return
    if args.webhook:
        send_slack(args.webhook, text)
        print(f"-> Slack ({args.webhook[:40]}...)")
    if args.to:
        send_email(args.to, f"Pipeline em Foco — {args.agent or 'empresa'}", text)
        print(f"-> email ({args.to})")


if __name__ == "__main__":
    main()
