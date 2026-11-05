"""Turn the Claude Code session log into a readable conversation, without rewriting it.

Keeps every message from the user and every text from the assistant, in order.
Removes only what the tool injects by itself (system reminders, IDE notices,
local command records and harness notices), full tool outputs, and the user's
email address. Tool calls appear as one line each. No message is reworded.

Usage: python export_chat.py <session.jsonl> <output.md>
"""
import json
import re
import sys
from pathlib import Path

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ALLOWED_EMAILS = {"noreply@anthropic.com"}
AUTOMATIC_BLOCKS = re.compile(
    r"<(system-reminder|ide_opened_file|ide_selection|local-command-caveat|command-name|command-message|command-args|local-command-stdout)>.*?</\1>",
    re.DOTALL,
)
PASTED_TAG = re.compile(r"</?pasted_content[^>]*>")
# Notices the harness writes in the user role without the user typing them.
HARNESS_NOTICES = (
    "Your response above was stopped by a safety classifier",
    "This is how Claude Code surfaces messages",
)
ANSWER_PREFIXES = ("Your questions have been answered", "The user answered")


def clean(text: str) -> str:
    text = PASTED_TAG.sub("", AUTOMATIC_BLOCKS.sub("", text))
    text = EMAIL.sub(lambda m: m.group(0) if m.group(0) in ALLOWED_EMAILS else "[e-mail removido]", text).strip()
    if any(notice in text for notice in HARNESS_NOTICES):
        return ""
    return text


def tool_line(block: dict) -> str:
    name, data = block["name"], block.get("input", {})
    detail = data.get("description") or data.get("skill") or Path(str(data.get("file_path", ""))).name
    if name == "AskUserQuestion":
        questions = "\n".join(f"> {q['question']}" for q in data.get("questions", []))
        return f"*Pergunta ao usuário:*\n\n{clean(questions)}"
    return f"`{name}`: {clean(str(detail))}" if detail else f"`{name}`"


def entries(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        if item.get("isSidechain") or item.get("isMeta"):
            continue
        attachment = item.get("attachment") or {}
        if item.get("type") == "attachment" and attachment.get("type") == "queued_command":
            for part in attachment.get("prompt", []):
                if part.get("type") == "text":
                    yield "user", clean(part["text"])
        elif item.get("type") == "user":
            content = item["message"]["content"]
            if isinstance(content, str):
                yield "user", clean(content)
                continue
            for part in content:
                if part.get("type") == "text":
                    yield "user", clean(part["text"])
                elif part.get("type") == "tool_result":
                    result = part.get("content")
                    if isinstance(result, list):
                        result = " ".join(p.get("text", "") for p in result if isinstance(p, dict))
                    if isinstance(result, str) and result.startswith(ANSWER_PREFIXES):
                        yield "user", "*Resposta às perguntas:* " + clean(result)
        elif item.get("type") == "assistant":
            for part in item["message"]["content"]:
                if part.get("type") == "text":
                    yield "assistant", clean(part["text"])
                elif part.get("type") == "tool_use":
                    yield "tool", tool_line(part)


def main() -> None:
    source, target = Path(sys.argv[1]), Path(sys.argv[2])
    out = [
        "# Exportação da conversa com o Claude Code",
        "",
        "Gerada por `export_chat.py` a partir do registro da sessão. As mensagens não foram reescritas. "
        "Só foram removidos o contexto automático da ferramenta (lembretes de sistema, registros de comandos locais e avisos do próprio Claude Code), "
        "as saídas completas das ferramentas e o e-mail do usuário.",
        "",
    ]
    last_role = None
    messages = {"user": 0, "assistant": 0, "tool": 0}
    for role, text in entries(source):
        if not text:
            continue
        messages[role] += 1
        if role == "user":
            out += ["---", "", "## Vinicius", "", text, ""]
        elif role == "assistant":
            if last_role != "assistant" and last_role != "tool":
                out += ["## Claude Code", ""]
            out += [text, ""]
        else:
            if last_role == "user":
                out += ["## Claude Code", ""]
            out += [f"- {text}", ""]
        last_role = role
    target.write_text("\n".join(out), encoding="utf-8")
    print(messages)


if __name__ == "__main__":
    main()
