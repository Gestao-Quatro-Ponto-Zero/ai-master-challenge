"""Converte a sessão do Claude Code (arquivo .jsonl) num Markdown legível.

Uso: python exportar.py CAMINHO_DO_JSONL [SAIDA.md]

O Claude Code grava cada sessão em ~/.claude/projects/<projeto>/<id>.jsonl. Este
script mantém, em ordem de horário:

- tudo o que eu escrevi (texto integral, sem correção);
- tudo o que a IA respondeu em texto;
- uma linha por ferramenta que a IA usou (qual, e em que arquivo ou comando);
- os relatórios dos subagentes, inteiros.

Fica de fora: a saída bruta das ferramentas (dezenas de MB de arquivos lidos e
logs), o raciocínio interno do modelo (vem cifrado no arquivo) e as instruções de
sistema do aplicativo. Meu e-mail e o nome do meu usuário do Windows são
trocados por marcadores.
"""
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

LOCAL = timezone(timedelta(hours=-3))  # horário de Brasília
REDACT = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[e-mail]"),
    (re.compile(r"(?i)(C:[\\/]+Users[\\/]+)[^\\/\s\"']+"), r"\1[usuario]"),
    (re.compile(r"(?i)/c/Users/[^/\s\"']+"), "/c/Users/[usuario]"),
]
REMINDER = re.compile(r"<system-reminder[^>]*>.*?</system-reminder[^>]*>", re.S)
# O GitHub esconde tags que não conhece (e o que vem dentro delas): tira o invólucro dos relatórios.
WRAPPER = re.compile(r"</?\\?agent-message[^>]*>")


def clean(text: str) -> str:
    text = WRAPPER.sub("", REMINDER.sub("", text))
    for pattern, replacement in REDACT:
        text = pattern.sub(replacement, text)
    return text.strip()


def when(stamp: str) -> str:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(LOCAL).strftime("%d/%m %H:%M")


def tool_line(block: dict) -> str:
    data = block.get("input") or {}
    name = block.get("name", "?").split("__")[-1]
    detail = (data.get("description") or data.get("file_path") or data.get("pattern") or data.get("url")
              or data.get("command") or data.get("skill") or data.get("query") or "")
    if not detail and "actions" in data:
        detail = f"{len(data['actions'])} ações no navegador"
    detail = clean(str(detail)).replace("\n", " ")
    return f"- `{name}`" + (f": {detail[:160]}" if detail else "")


def main(source: str, target: str) -> None:
    out, tools, seen, questions = [], [], set(), set()
    counts = {"eu": 0, "ia": 0, "ferramentas": 0, "subagentes": 0}

    def flush_tools():
        if tools:
            out.append("<details><summary>" + f"{len(tools)} chamada(s) de ferramenta" + "</summary>\n\n" + "\n".join(tools) + "\n\n</details>\n")
            tools.clear()

    def human(stamp, text):
        text = clean(text)
        if not text or (text[:200], stamp[:16]) in seen:
            return
        seen.add((text[:200], stamp[:16]))
        flush_tools()
        if "Subagent hand-back" in text:
            counts["subagentes"] += 1
            out.append(f"### Relatório de subagente · {when(stamp)}\n\n{text}\n")
        elif text.startswith("<task-notification") or "SYSTEM NOTIFICATION" in text[:80] or text.startswith("<side-sessions"):
            out.append(f"_Aviso automático do aplicativo ({when(stamp)}): tarefa em segundo plano terminou._\n")
        elif "This session is being continued from a previous conversation" in text[:120]:
            out.append(f"_({when(stamp)}) O aplicativo resumiu a conversa anterior por limite de contexto; o resumo automático foi omitido._\n")
        else:
            counts["eu"] += 1
            out.append(f"## Gustavo · {when(stamp)}\n\n{text}\n")

    with open(source, encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind, stamp = row.get("type"), row.get("timestamp", "")
            if row.get("isSidechain") or row.get("isMeta"):
                continue
            if kind == "queue-operation" and row.get("operation") == "enqueue" and isinstance(row.get("content"), str):
                human(stamp, row["content"])
            elif kind == "user":
                content = row.get("message", {}).get("content")
                if isinstance(content, str):
                    human(stamp, content)
                elif isinstance(content, list):
                    for block in content:
                        if block.get("type") == "text":
                            human(stamp, block.get("text", ""))
                        elif block.get("type") == "tool_result" and block.get("tool_use_id") in questions:
                            # resposta minha a uma pergunta de múltipla escolha feita pela IA
                            answer = block.get("content")
                            if isinstance(answer, list):
                                answer = " ".join(part.get("text", "") for part in answer if isinstance(part, dict))
                            human(stamp, "(resposta a uma pergunta da IA) " + str(answer))
            elif kind == "assistant":
                for block in row.get("message", {}).get("content", []):
                    if block.get("type") == "text" and block.get("text", "").strip():
                        flush_tools()
                        counts["ia"] += 1
                        out.append(f"**Claude · {when(stamp)}**\n\n{clean(block['text'])}\n")
                    elif block.get("type") == "tool_use":
                        if block.get("name") == "AskUserQuestion":
                            questions.add(block.get("id"))
                        counts["ferramentas"] += 1
                        tools.append(tool_line(block))
    flush_tools()
    header = (
        "# Conversa com o Claude Code\n\n"
        "Gerado por `exportar.py` a partir do arquivo de sessão do Claude Code. Horários de Brasília.\n\n"
        f"- Mensagens minhas: {counts['eu']}\n- Respostas da IA em texto: {counts['ia']}\n"
        f"- Chamadas de ferramenta: {counts['ferramentas']}\n- Relatórios de subagentes: {counts['subagentes']}\n\n"
        "O que ficou de fora e por quê está no cabeçalho do script.\n\n---\n\n"
    )
    Path(target).write_text(header + "\n".join(out), encoding="utf-8")
    print(counts, "->", target, f"{Path(target).stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "sessao-claude-code.md")
