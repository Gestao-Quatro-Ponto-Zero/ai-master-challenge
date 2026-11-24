"""Exporta a conversa do Claude Code em Markdown para o process log, sem saídas de ferramentas e com dados sensíveis removidos.

Uso: python3 -I exportar_conversa.py <sessao.jsonl> <saida.md>
Confira o resultado antes de publicar: as regras são genéricas e podem deixar passar algo específico do seu ambiente.
"""
import json, os, re, sys
src, dst = sys.argv[1], sys.argv[2]
# Regras genéricas: nenhum segredo literal fica neste arquivo.
RED = [
    (re.compile(r"\b(?:KGAT|gh[opsu]|github_pat|sk(?:-ant)?|xox[abp])[-_][A-Za-z0-9_-]{8,}"), "<token-removido>"),
    (re.compile(r"(?i)\b(senha|password|passwd|pwd|PGPASSWORD|api[_-]?key|secret|token)\b(\s*[=:]\s*|\s+)['\"]?[^\s'\"`]{8,}"), r"\1=<removido>"),
    (re.compile(r"(?i)postgres(?:ql)?://[^\s'\"`]+"), "<url-de-banco-removida>"),
    (re.compile(r"[\w.+-]+@(?!anthropic\.com|example\.com)[\w-]+\.[\w.]+"), "<e-mail-removido>"),
    (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "<ip-removido>"),
    (re.compile(r"\b[\w.-]+\.(?:internal|local|lan)(?::\d+)?\b"), "<servidor-interno>"),
    (re.compile(r"/tmp/claude-\d+/[^\s)`'\"]*"), "<pasta-temporária>"),
    (re.compile(r"\bgrowth-\w+\b"), "<container-interno>"),
]
# Termos extras a remover, um por linha, num arquivo FORA do repositório: CHURN_REDACT_FILE=~/.config/churn-redact.txt
_extra = os.environ.get("CHURN_REDACT_FILE")
if _extra and os.path.exists(os.path.expanduser(_extra)):
    for termo in open(os.path.expanduser(_extra), encoding="utf-8").read().split("\n"):
        if termo.strip():
            RED.append((re.compile(re.escape(termo.strip())), "<removido>"))
def limpa(t: str) -> str:
    t = re.sub(r"<system-reminder>.*?</system-reminder>", "", t, flags=re.S)
    t = re.sub(r"<task-notification>.*?</task-notification>", "", t, flags=re.S)
    for rx, rep in RED:
        t = rx.sub(rep, t)
    return t.strip()

out = ["# Conversa com o Claude Code (export para o process log)\n",
       "Mensagens do candidato e respostas do Claude Code (modelo Claude Opus 5.5), em ordem. Cada ação executada aparece em uma",
       "linha (ferramenta + descrição); as saídas das ferramentas foram omitidas. Tokens, senhas, e-mails, IPs e endereços internos",
       "foram removidos automaticamente.\n"]
n_user = n_tools = 0
# o histórico grava cada resposta em pedaços (uma linha por bloco, mesmo message.id): junta por id, na ordem em que aparecem
eventos, vistos = [], {}
for line in open(src, encoding="utf-8"):
    try:
        ev = json.loads(line)
    except Exception:
        continue
    mid = (ev.get("message") or {}).get("id")
    if (ev.get("message") or {}).get("role") == "assistant" and mid:
        if mid in vistos:
            blocos = eventos[vistos[mid]]["message"]["content"]
            for c in ev["message"].get("content") or []:
                if c not in blocos:
                    blocos.append(c)
            continue
        vistos[mid] = len(eventos)
        ev = json.loads(line)
    eventos.append(ev)
ultimo_user = None
ja_saiu: set = set()
for ev in eventos:
    msg = ev.get("message") or {}
    role, content = msg.get("role"), msg.get("content")
    if ev.get("isMeta") or not role:
        continue
    if isinstance(content, str):
        content = [{"type": "text", "text": content}]
    if not isinstance(content, list):
        continue
    if role == "user":
        txt = "\n".join(limpa(c.get("text", "")) for c in content if c.get("type") == "text")
        imgs = sum(1 for c in content if c.get("type") == "image")
        if txt.startswith("[Image:") and not imgs:
            continue
        txt = re.sub(r"\[Image: source:[^\n]*", "", txt)
        txt = re.sub(r"\[Image #\d+\]", "", txt).strip()
        if (not txt and not imgs) or txt == ultimo_user:
            continue
        ultimo_user = txt
        n_user += 1
        out.append(f"\n---\n\n## Candidato ({n_user})\n\n{txt}" + ("\n\n_[imagem anexada]_" if imgs else ""))
    elif role == "assistant":
        for c in content:
            chave = c.get("id") or c.get("text")
            if chave in ja_saiu:  # o mesmo bloco aparece mais de uma vez no histórico
                continue
            ja_saiu.add(chave)
            if c.get("type") == "text" and limpa(c["text"]):
                out.append("\n**Claude Code:**\n\n" + limpa(c["text"]))
            elif c.get("type") == "tool_use":
                n_tools += 1
                inp = c.get("input") or {}
                desc = inp.get("description") or inp.get("file_path") or inp.get("skill") or inp.get("query") or ""
                out.append(f"- `{c['name']}` {limpa(str(desc))[:160]}")
out.append(f"\n---\n\n_{n_user} mensagens do candidato · {n_tools} ações executadas._\n")
open(dst, "w", encoding="utf-8").write("\n".join(out))
print(n_user, n_tools)
