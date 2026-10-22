"""Cataloga os achados das entregas públicas do case 002.

Para cada achado conhecido, procura no texto e no código de cada PR quem
menciona e quem foi o primeiro (pela data de abertura do PR).

Uso: python3 catalogar_achados.py <pasta-de-trabalho>
A pasta de trabalho é a mesma usada por 00-preparacao/levantamento_prs.py
(precisa do clone com as refs pr/<n> já baixadas).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = "Gestao-Quatro-Ponto-Zero/ai-master-challenge"

ACHADOS = {
    # Dataset 1
    "D1 tem 8.469 tickets, não 30 mil": r"8[.,]?469",
    "Tempo invertido (49,3% resolvem antes da 1ª resposta)": r"49[,.]3",
    "Todos os horários cabem em ~27 horas": r"27 ?h|27 horas|27 hours",
    "Não existe data de abertura do ticket": r"(sem|n[aã]o (h[aá]|tem|existe|registra)).{0,40}(abertura|cria[çc][aã]o)|no (creation|open(ing)?) (date|timestamp)",
    "Descrição com {product_purchased} sem preencher": r"\{product_purchased\}|placeholder",
    "Resolução é texto aleatório (Faker)": r"faker|gibberish|sem sentido|frases aleat",
    "Categorias divididas por igual (sorteio)": r"uniform|sorteio|sorteada|sorteadas",
    "Satisfação não depende de nada (CSAT aleatório)": r"csat.{0,80}(aleat|uniform|random|ru[ií]do|n[aã]o.{0,20}explic)|r ?= ?-?0[,.]00|r[²2] ?[=≈] ?0[,.]00",
    "Prioridade não muda nada": r"prioridade.{0,60}(n[aã]o (muda|altera|prioriza|funciona|influencia))|critical.{0,40}low|low.{0,40}critical",
    "67% dos tickets não estão fechados": r"67[,.]3 ?%|67 ?%",
    "Open nunca recebeu 1ª resposta (2.819)": r"2[.,]?819",
    "Texto do D1 não prevê o tipo de ticket": r"(texto|text).{0,60}(n[aã]o prev|acaso|chance).{0,40}|18[,.]9 ?%|20[,.]9 ?%",
    "Brief erra: são 5 tipos de ticket, não 3": r"5 tipos|cinco tipos|5, n[aã]o 3|5 ticket types|refund.{0,30}cancellation.{0,60}40[,.]7",
    "E-mails em domínio de exemplo (example.com)": r"example\.(com|org|net)|rfc ?2606",
    # Dataset 2
    "Classificador simples no D2 acerta ~85-87%": r"8[4-7][,.]\d+ ?%.{0,60}(acur|accur|acert|f1)|(acur|accur|acert|f1).{0,60}8[4-7][,.]\d+ ?%",
    "Trava de confiança: ~60% sozinho com ~96-97% de acerto": r"9[5-8][,.]\d ?%.{0,80}(acert|precis)|(acert|precis).{0,40}9[5-8][,.]\d ?%",
    "LLM classifica pior que o classificador simples": r"(llm|gemini|gpt|claude|zero-?shot).{0,160}(perdeu|pior|inferior|39 ?%|41[,.]0|42)",
    "Modelo do D2 aplicado no D1 joga tudo em Hardware": r"hardware.{0,80}(8[0-9] ?%|domain shift|dom[ií]nio)|(domain shift|mudan[çc]a de dom[ií]nio)",
    "D2 tem tickets rotulados na fila errada": r"(r[oó]tulo|label|fila).{0,40}(errad|incorret|wrong|ruido)",
    "D2 tem tickets quase duplicados": r"quase.?duplicad|near.?duplicat|duplicad",
    # Proposta
    "Reembolso e cancelamento sempre com pessoa": r"(refund|reembolso).{0,120}(humano|human|pessoa)|(humano|human|pessoa).{0,120}(refund|reembolso)",
    "Medir/instrumentar antes de automatizar": r"instrument",
    "Piloto em modo sombra": r"modo sombra|shadow",
    "Lembrete automático pro cliente parado (Pending)": r"(follow-?up|lembrete|cobrar).{0,60}(cliente|pending|parado)",
    "Resposta sugerida pro atendente (rascunho)": r"rascunho|resposta(s)? sugerida|suggested (reply|response)|draft",
    "Deflexão: resolver antes de abrir ticket": r"deflex|deflection|autosservi|self-?service",
}


def git(pasta, *args):
    return subprocess.run(["git", "-C", str(pasta), *args], capture_output=True, text=True).stdout


def main(trabalho):
    clone = trabalho / "ai-master-challenge"
    prs = json.loads(subprocess.run(
        ["gh", "api", "--paginate", f"repos/{REPO}/pulls?state=all&per_page=100", "--jq", "[.[] | {number, title, created_at, body}]"],
        capture_output=True, text=True, check=True).stdout.replace("]\n[", ","))
    p002 = sorted([p for p in prs if re.search(r"00?2\b|suporte|support", p["title"], re.I)], key=lambda p: p["created_at"])

    textos = {}
    for p in p002:
        n = p["number"]
        arquivos = git(clone, "diff", "--name-only", f"origin/main...pr/{n}").split()
        t = p.get("body") or ""
        for a in arquivos:
            if a.startswith("submissions/") and a.lower().endswith((".md", ".py", ".ts", ".tsx", ".js", ".html", ".txt", ".ipynb")):
                t += git(clone, "show", f"pr/{n}:{a}")[:300_000]
        textos[n] = t

    resultado = {}
    for nome, padrao in ACHADOS.items():
        quem = [p for p in p002 if re.search(padrao, textos[p["number"]], re.I | re.S)]
        resultado[nome] = {
            "prs": [p["number"] for p in quem],
            "primeiro": (quem[0]["number"], quem[0]["created_at"][:10]) if quem else None,
        }
        primeiro = f"#{quem[0]['number']} ({quem[0]['created_at'][:10]})" if quem else "ninguém"
        print(f"{len(quem):>2}/{len(p002)}  primeiro: {primeiro:<20} {nome}")
    (trabalho / "achados.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "levantamento"))
