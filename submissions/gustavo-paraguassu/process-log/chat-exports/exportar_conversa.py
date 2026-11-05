"""Exporta a sessão do Claude Code (JSONL local) para Markdown legível.

Inclui: minhas mensagens na íntegra (também as enviadas enquanto a IA trabalhava e as respostas
às perguntas dela), o texto das respostas da IA e uma linha por ação (ferramenta + descrição).
Omite: o raciocínio interno da IA e o conteúdo bruto dos resultados das ferramentas (os números
estão em process-log/analysis-outputs e em solution/outputs). Lembretes do sistema são removidos.

Uso: python exportar_conversa.py <sessao.jsonl> <saida.md>
"""
import json
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

SP = ZoneInfo("America/Sao_Paulo")
src, dst = sys.argv[1], sys.argv[2]
RAIZ = "/Users/gustavoparaguassu/Documents/Codes/g4-ai-master/"


def hora(ts: str) -> str:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(SP).strftime("%d/%m %H:%M")


def limpa(t: str) -> str:
    t = re.sub(r"<system-reminder>.*?</system-reminder>", "", t, flags=re.S)
    t = re.sub(r"</?pasted_content[^>]*>", "", t)
    t = re.sub(r"\[Image #\d+\]", "[imagem anexada]", t)
    t = re.sub(r"[\w.+-]+@(?!users\.noreply|anthropic\.com)[\w-]+\.[\w.-]+", "[email]", t)
    return t.replace(RAIZ, "").strip()


def acao(b: dict) -> str:
    nome, inp = b.get("name", "?"), b.get("input", {})
    if nome == "Bash":
        det = inp.get("description", "")
    elif nome in ("Read", "Write", "Edit"):
        det = inp.get("file_path", "").replace(RAIZ, "")
    elif nome == "AskUserQuestion":
        det = " | ".join(q.get("question", "") for q in inp.get("questions", []))
    elif nome in ("WebSearch", "WebFetch"):
        det = inp.get("query") or inp.get("url", "")
    elif nome == "Skill":
        det = inp.get("skill", "")
    else:
        det = ", ".join(f"{k}={str(v)[:40]}" for k, v in list(inp.items())[:2])
    return f"- `{nome}` {limpa(det)[:160]}"


saida, acoes, inicio, fim = [], [], None, None
n_user = n_ia = n_acoes = 0


def descarrega():
    if acoes:
        saida.append("<details><summary>Ações da IA (" + str(len(acoes)) + ")</summary>\n\n" + "\n".join(acoes) +
                     "\n\n</details>\n")
        acoes.clear()


for line in open(src):
    d = json.loads(line)
    if d.get("isSidechain"):
        continue
    ts = d.get("timestamp")
    tipo = d.get("type")
    if ts and tipo in ("user", "assistant", "attachment"):
        inicio = inicio or ts
        fim = ts
    if tipo == "attachment" and d.get("attachment", {}).get("type") == "queued_command":
        descarrega()
        p = d["attachment"]["prompt"]
        if isinstance(p, list):  # texto + imagem (ex.: print do bot)
            p = " ".join(x.get("text", "") if x.get("type") == "text" else "[imagem anexada]" for x in p)
        saida.append(f"### 🧑 Gustavo · {hora(ts)} *(enviada enquanto a IA trabalhava)*\n\n{limpa(p)}\n")
        n_user += 1
        continue
    if tipo == "user":
        if d.get("isMeta"):
            continue
        cont = d["message"].get("content")
        if d.get("isCompactSummary"):
            descarrega()
            saida.append(f"---\n\n**{hora(ts)}: contexto compactado.** A conversa ficou longa e a ferramenta "
                         "resumiu o início; daqui em diante a IA trabalha a partir deste resumo (escrito por ela):\n\n"
                         f"<details><summary>Resumo usado pela IA</summary>\n\n{limpa(cont if isinstance(cont, str) else '')}"
                         "\n\n</details>\n\n---\n")
            continue
        blocos = [{"type": "text", "text": cont}] if isinstance(cont, str) else cont
        for b in blocos:
            if b.get("type") == "text":
                t = limpa(b["text"])
                if not t or t.startswith(("<command-", "<local-command")) or "local-command-caveat" in t:
                    continue
                descarrega()
                saida.append(f"### 🧑 Gustavo · {hora(ts)}\n\n{t}\n")
                n_user += 1
            elif b.get("type") == "tool_result":
                txt = b.get("content")
                txt = txt if isinstance(txt, str) else " ".join(x.get("text", "") for x in txt or [] if isinstance(x, dict))
                if "answered your questions" in txt:
                    descarrega()
                    resp = re.findall(r'"([^"]+)"="([^"]+)"', txt)
                    corpo = "\n".join(f"- **{q}** → {a}" for q, a in resp) or limpa(txt)[:500]
                    saida.append(f"### 🧑 Gustavo · {hora(ts)} *(resposta às perguntas da IA)*\n\n{corpo}\n")
                    n_user += 1
    elif tipo == "assistant":
        for b in d["message"].get("content", []):
            if b.get("type") == "text" and limpa(b["text"]):
                descarrega()
                saida.append(f"### 🤖 Claude · {hora(ts)}\n\n{limpa(b['text'])}\n")
                n_ia += 1
            elif b.get("type") == "tool_use":
                acoes.append(acao(b))
                n_acoes += 1
descarrega()

cab = (f"# Conversa completa com a IA (Claude Code · Claude Opus 5.5)\n\n"
       f"- Sessão única, de {hora(inicio)} a {hora(fim)} (horário de Brasília)\n"
       f"- {n_user} mensagens minhas · {n_ia} respostas da IA · {n_acoes} ações da IA (comandos, leituras, edições)\n"
       f"- Gerado por `exportar_conversa.py` a partir do log local da sessão. Omitidos: raciocínio interno da IA e "
       f"o conteúdo bruto dos resultados das ferramentas.\n\n---\n\n")
open(dst, "w").write(cab + "\n".join(saida))
print(f"{dst}: {n_user} msgs minhas, {n_ia} da IA, {n_acoes} ações")
