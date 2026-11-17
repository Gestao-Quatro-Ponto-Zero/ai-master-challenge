"""Exporta uma sessão do Claude Code (.jsonl) para Markdown legível e público.

Mantém: o que o humano digitou, o texto das respostas da IA e uma linha por ferramenta chamada
(nome + descrição curta). Tira: injeções de sistema e de hooks, saídas de ferramentas, raciocínio
interno, resumos de compactação (só marcados) e dados pessoais (caminho da home, e-mail).
Uso: python3 -I exporta_chat.py <sessao.jsonl> <saida.md> "<título>"
"""
import json, re, sys

src, out, titulo = sys.argv[1], sys.argv[2], sys.argv[3]
DESDE = sys.argv[4] if len(sys.argv) > 4 else ""
HOME = re.compile(r"/private/tmp/claude-[0-9]+/[^\s`'\")]*|/(?:private/)?Users/[A-Za-z0-9._-]+")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@(?!ravenstack\.app)[A-Za-z0-9.-]+\.[a-z]{2,}")
TAGS = re.compile(r"<(system-reminder|lifeos-[a-z-]+|time-now|command-[a-z-]+|local-command-[a-z-]+|user-prompt-submit-hook|task-notification|ide_[a-z_]+)\b[^>]*>.*?</\1>", re.S)
# Termos pessoais a ocultar: lista local, fora do repositório (variável EXPORT_OCULTAR = arquivo com uma regex por linha).
import os
OCULTAR = [re.compile(l.strip(), re.I) for l in open(os.environ["EXPORT_OCULTAR"], encoding="utf-8") if l.strip()] if os.environ.get("EXPORT_OCULTAR") else []
LIXO = re.compile(r"^(🧠|⚙️|🗣️|═|━|🕐|♻️).*$", re.M)


def limpa(t: str) -> str:
    t = TAGS.sub("", t)
    t = re.sub(r"<pasted_content[^>]*>", "\n> [texto colado]\n", t)
    t = t.replace("</pasted_content>", "")
    t = LIXO.sub("", t)
    t = HOME.sub("~", t)
    t = re.sub(r"-Users-[A-Za-z0-9._]+", "-Users-USUARIO", t)
    t = EMAIL.sub("[e-mail]", t)
    for r in OCULTAR:
        t = r.sub("[removido]", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def ferramenta(b) -> str:
    i = b.get("input") or {}
    desc = i.get("description") or i.get("file_path") or i.get("pattern") or i.get("query") or i.get("skill") or i.get("url") or ""
    desc = limpa(str(desc)).replace("\n", " ")[:140]
    return f"`{b.get('name')}`" + (f" — {desc}" if desc else "")


blocos, n_h, n_ia, n_tool = [], 0, 0, 0
ferr_pend = []
dia = None


def flush_tools():
    global ferr_pend
    if ferr_pend:
        blocos.append("<details><summary>ferramentas (" + str(len(ferr_pend)) + ")</summary>\n\n" + "\n".join(f"- {x}" for x in ferr_pend) + "\n\n</details>")
        ferr_pend = []


for linha in open(src, encoding="utf-8"):
    try:
        r = json.loads(linha)
    except json.JSONDecodeError:
        continue
    tipo = r.get("type")
    if tipo not in ("user", "assistant") or r.get("isSidechain"):
        continue
    ts = (r.get("timestamp") or "")[:16].replace("T", " ")
    if DESDE and ts < DESDE:
        continue
    if ts[:10] and ts[:10] != dia:
        dia = ts[:10]
        flush_tools()
        blocos.append(f"\n---\n\n## {dia}\n")
    c = (r.get("message") or {}).get("content")
    if tipo == "user":
        if r.get("isMeta"):
            continue
        if r.get("isCompactSummary"):
            flush_tools()
            blocos.append("> _[O contexto da conversa foi compactado aqui; o resumo automático não foi reproduzido.]_")
            continue
        textos = [c] if isinstance(c, str) else [b.get("text", "") for b in (c or []) if isinstance(b, dict) and b.get("type") == "text"]
        imgs = 0 if isinstance(c, str) else sum(1 for b in (c or []) if isinstance(b, dict) and b.get("type") == "image")
        t = limpa("\n".join(textos))
        if t.startswith("[Request interrupted"):
            t = "_[interrompido pelo humano]_"
        if not t and not imgs:
            continue
        if "This session is being continued from a previous conversation" in t:
            flush_tools()
            blocos.append("> _[O contexto da conversa foi compactado aqui; o resumo automático não foi reproduzido.]_")
            continue
        flush_tools()
        n_h += 1
        blocos.append(f"### 🧑 Humano · {ts}\n\n" + (t or "") + (f"\n\n_[{imgs} imagem(ns) anexada(s)]_" if imgs else ""))
    else:
        for b in c or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text":
                t = limpa(b.get("text", ""))
                if t:
                    flush_tools()
                    n_ia += 1
                    blocos.append(f"**🤖 IA · {ts}**\n\n{t}")
            elif b.get("type") == "tool_use":
                n_tool += 1
                ferr_pend.append(ferramenta(b))
flush_tools()

cab = (f"# {titulo}\n\n"
       f"Export da sessão do Claude Code, gerado a partir do arquivo `.jsonl` da própria ferramenta. "
       f"{n_h} mensagens do humano, {n_ia} blocos de resposta da IA, {n_tool} chamadas de ferramenta.\n\n"
       "O que foi mantido: o texto que o humano digitou, o texto das respostas da IA e, em blocos recolhíveis, "
       "o nome e a descrição de cada ferramenta chamada. O que foi retirado: as saídas das ferramentas, o raciocínio "
       "interno do modelo, os resumos automáticos de compactação, as instruções de sistema e de hooks do ambiente "
       "pessoal do autor, o caminho da pasta pessoal (trocado por `~`) e endereços de e-mail.\n")
open(out, "w", encoding="utf-8").write(cab + "\n\n".join(blocos) + "\n")
print(out, n_h, n_ia, n_tool)
