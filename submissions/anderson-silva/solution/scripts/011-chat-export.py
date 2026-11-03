"""Export the messages of a Claude Code session as Markdown, for the process log of the submission (challenge 002).

Keeps only the text written by the candidate and by the AI, with the time converted to local time. Leaves out tool
calls and their outputs, the AI's internal reasoning, system notes (command caveats, task notifications, image
notes) and the automatic context summaries, which become a one-line marker. Removes e-mail addresses, local paths
and the API key, then checks the result: no e-mail, no local path, no key, and no customer name or e-mail from
Dataset 1 (only counts are printed, never the names).

Other terms that must not appear come only from the CHAT_EXPORT_HIDDEN_TERMS environment variable (comma-separated),
set at run time, so they are never written in this file or in the project. They are replaced by "[nome removido]",
ignoring case, and the final check refuses to write the export if any is left.

Usage:
  CHAT_EXPORT_HIDDEN_TERMS="..." python 011-chat-export.py <transcript.jsonl> --output FILE \
      [--customers datasets/001-customer-support-tickets.csv]
"""
import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
LOCAL_TIME = timezone(timedelta(hours=-3))
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
# Addresses written as "name (at) domain.com", as in some Dataset 1 ticket texts quoted in the session.
OBFUSCATED_EMAIL = re.compile(r"[\w.+-]+\s*\(at\)\s*[\w-]+\.[\w.]+")
KEY_PATTERN = re.compile(r"sk-or-[\w-]+")
SYSTEM_PREFIXES = ("<local-command-caveat>", "<local-command-stdout>", "<local-command-stderr>", "<command-name>",
                   "<task-notification>", "[Image:")
INTERRUPTED_PREFIX = "[Request interrupted"
PASTE_OPEN = re.compile(r'<pasted_content id="[^"]*">\s*')
PASTE_CLOSE = re.compile(r'\s*</pasted_content id="[^"]*">|\s*</pasted_content>')
SYSTEM_REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)
HIDDEN_TERMS_VARIABLE = "CHAT_EXPORT_HIDDEN_TERMS"
HIDDEN_MARKER = "[nome removido]"
SUMMARY_MARKER ="*[Aqui o Claude Code resumiu automaticamente a conversa anterior para liberar contexto; o resumo não entra no export.]*"
INTERRUPTED_MARKER = "*[Pedido interrompido pela pessoa candidata.]*"


def read_api_key():
    if not ENV_PATH.exists():
        return None
    for line in ENV_PATH.read_text().splitlines():
        name, _, value = line.partition("=")
        if name.strip() == "OPENROUTER_API_KEY" and value.strip():
            return value.strip()
    return None


def read_hidden_terms():
    terms = [term.strip() for term in os.environ.get(HIDDEN_TERMS_VARIABLE, "").split(",") if term.strip()]
    return [re.compile(re.escape(term), re.IGNORECASE) for term in terms]


def local_time(stamp):
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(LOCAL_TIME).strftime("%Y-%m-%d %H:%M")


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n\n".join(part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text")
    return ""


def read_messages(transcript):
    """Return (time, author, text) entries; consecutive AI texts in one turn are joined."""
    entries = []
    for line in transcript.open(encoding="utf-8"):
        record = json.loads(line)
        kind = record.get("type")
        if kind not in ("user", "assistant") or record.get("isSidechain"):
            continue
        if record.get("isCompactSummary"):
            entries.append((local_time(record["timestamp"]), "marker", SUMMARY_MARKER))
            continue
        text = SYSTEM_REMINDER.sub("", text_of((record.get("message") or {}).get("content"))).strip()
        if not text or record.get("isMeta"):
            continue
        if kind == "user":
            if text.startswith(SYSTEM_PREFIXES):
                continue
            if text.startswith(INTERRUPTED_PREFIX):
                entries.append((local_time(record["timestamp"]), "marker", INTERRUPTED_MARKER))
                continue
            text = PASTE_CLOSE.sub("", PASTE_OPEN.sub("*[Texto colado]*\n\n", text))
            entries.append((local_time(record["timestamp"]), "Eu", text))
        elif entries and entries[-1][1] == "IA":
            stamp, _, previous = entries[-1]
            entries[-1] = (stamp, "IA", previous + "\n\n" + text)
        else:
            entries.append((local_time(record["timestamp"]), "IA", text))
    return entries


def sanitize(text, counts, api_key, hidden_terms):
    for pattern in hidden_terms:
        text, found = pattern.subn(HIDDEN_MARKER, text)
        counts["nomes"] += found
    project = str(ROOT)
    encoded_project = project.replace("/", "-")
    home = str(Path.home())
    replacements = [(project + "/", ""), (project, "."), (encoded_project, "<pasta-do-projeto>"), (home, "~")]
    for old, new in replacements:
        counts["caminhos locais"] += text.count(old)
        text = text.replace(old, new)
    for pattern, label, new in ((EMAIL, "e-mails", "[e-mail removido]"), (OBFUSCATED_EMAIL, "e-mails", "[e-mail removido]"),
                                (KEY_PATTERN, "chaves", "[chave removida]")):
        text, found = pattern.subn(new, text)
        counts[label] += found
    if api_key and api_key in text:
        counts["chaves"] += text.count(api_key)
        text = text.replace(api_key, "[chave removida]")
    return text


def leftovers(text, api_key, customers, hidden_terms):
    checks = {"e-mail": len(EMAIL.findall(text)), "e-mail disfarçado (at)": len(OBFUSCATED_EMAIL.findall(text)),
              "caminho /Users/ ou /Volumes/": len(re.findall(r"/Users/|/Volumes/", text)),
              "padrão de chave": len(KEY_PATTERN.findall(text)), "valor da chave": text.count(api_key) if api_key else 0,
              "termo oculto": sum(len(pattern.findall(text)) for pattern in hidden_terms)}
    if customers is not None:
        names, emails = customers
        checks["nome de cliente do Dataset 1"] = sum(1 for name in names if name in text)
        checks["e-mail de cliente do Dataset 1"] = sum(1 for email in emails if email in text)
    return checks


def load_customers(path):
    import pandas as pd

    frame = pd.read_csv(path, usecols=["Customer Name", "Customer Email"])
    return set(frame["Customer Name"].dropna()), set(frame["Customer Email"].dropna())


def render(entries, counts, generated_at):
    authors = {"Eu": "Eu (pessoa candidata)", "IA": "IA (Claude Code, Claude Opus 5.5)"}
    total = {author: sum(1 for _, who, _ in entries if who == author) for author in ("Eu", "IA")}
    summaries = sum(1 for _, who, text in entries if who == "marker" and text == SUMMARY_MARKER)
    lines = ["# Chat export da sessão principal", "",
             f"- **Período:** de {entries[0][0]} a {entries[-1][0]}, horário de Brasília (−03). Gerado em {generated_at}.",
             f"- **O que entra:** só o texto das mensagens: {total['Eu']} minhas e {total['IA']} blocos de resposta da IA."
             " Respostas seguidas da IA no mesmo turno aparecem juntas.",
             "- **O que fica de fora:** as chamadas de ferramentas e as saídas delas, o raciocínio interno da IA, os"
             f" avisos do sistema e os {summaries} resumos automáticos de contexto, marcados no ponto em que ocorreram."
             " A segunda sessão do Claude não entra; ela está descrita no process log.",
             f"- **Limpeza feita por script (`scripts/011-chat-export.py`):** {counts['caminhos locais']} caminhos locais"
             f" trocados por caminhos relativos, {counts['e-mails']} e-mails e {counts['chaves']} chaves removidos,"
             f" {counts['nomes']} {'nome trocado' if counts['nomes'] == 1 else 'nomes trocados'} por \"{HIDDEN_MARKER}\".",
             "- **Detalhe de cada passo:** está no [audit trail](../002-audit-trail.md).", ""]
    for stamp, who, text in entries:
        lines += ["---", "", text, ""] if who == "marker" else ["---", "", f"### {stamp} · {authors[who]}", "", text, ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--customers", type=Path, help="Dataset 1 CSV, to check that no customer name or e-mail leaks")
    args = parser.parse_args()
    api_key = read_api_key()
    hidden_terms = read_hidden_terms()
    counts = {"caminhos locais": 0, "e-mails": 0, "chaves": 0, "nomes": 0}
    entries = [(stamp, who, sanitize(text, counts, api_key, hidden_terms))
               for stamp, who, text in read_messages(args.transcript)]
    generated_at = datetime.now(LOCAL_TIME).strftime("%Y-%m-%d %H:%M")
    document = render(entries, counts, generated_at)
    customers = load_customers(args.customers) if args.customers else None
    checks = leftovers(document, api_key, customers, hidden_terms)
    print(f"Termos ocultos recebidos em {HIDDEN_TERMS_VARIABLE}: {len(hidden_terms)}")
    print("Trocas feitas:", counts)
    print("Conferência do export (deve ser tudo zero):", checks)
    if any(checks.values()):
        raise SystemExit("Export não gravado: sobrou dado que não pode sair.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(document, encoding="utf-8")
    print(f"{args.output}: {args.output.stat().st_size / 1e3:.0f} KB, {len(entries)} entradas")


if __name__ == "__main__":
    main()
