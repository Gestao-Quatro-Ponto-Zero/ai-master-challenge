"""Levantamento das submissões públicas do AI Master Challenge.

Gera os números citados em 00-preparacao-do-terreno.md:
quantos PRs existem, como se dividem por case, o que as entregas do case 002
têm em comum e o que o avaliador do G4 comentou nelas.

Uso (precisa do gh logado e de git):
    python3 levantamento_prs.py <pasta-de-trabalho>
"""
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = "Gestao-Quatro-Ponto-Zero/ai-master-challenge"
AVALIADORES = {"joaovitor2763", "g4os-dev"}


def gh(path):
    out = subprocess.run(["gh", "api", "--paginate", path], capture_output=True, text=True, check=True).stdout
    # --paginate concatena vários arrays JSON
    dec, i, itens = json.JSONDecoder(), 0, []
    while i < len(out):
        resto = out[i:].lstrip()
        if not resto:
            break
        obj, n = dec.raw_decode(resto)
        itens += obj
        i = len(out) - len(resto) + n
    return itens


def git(pasta, *args):
    return subprocess.run(["git", "-C", str(pasta), *args], capture_output=True, text=True).stdout


def case_do_titulo(titulo):
    m = re.search(r"00?([1-4])\b", titulo)
    return f"00{m.group(1)}" if m else "sem número"


def main(trabalho):
    trabalho.mkdir(parents=True, exist_ok=True)
    clone = trabalho / "ai-master-challenge"
    if not clone.exists():
        subprocess.run(["git", "clone", "-q", f"https://github.com/{REPO}.git", str(clone)], check=True)

    prs = gh(f"repos/{REPO}/pulls?state=all&per_page=100")
    print(f"PRs no repositório: {len(prs)}")
    print("Por estado:", dict(collections.Counter(p["state"] for p in prs)))
    print("Por case (pelo título):", dict(collections.Counter(case_do_titulo(p["title"]) for p in prs).most_common()))

    p002 = [p for p in prs if re.search(r"00?2\b|suporte|support", p["title"], re.I)]
    print(f"\nPRs do case 002: {len(p002)}")

    refs = [f"+refs/pull/{p['number']}/head:refs/remotes/pr/{p['number']}" for p in p002]
    subprocess.run(["git", "-C", str(clone), "fetch", "-q", "--filter=blob:limit=2m", "origin", *refs], check=True)

    sinais = {
        "achou o dado sintético (49,3% invertido, CSAT aleatório etc.)": r"49[,.]3|sint[eé]tic|synthetic|faker|uniforme",
        "classificador treinado no Dataset 2": r"tf-?idf|logistic|linearsvc|naive bayes|svm",
        "trava de confiança (limiar)": r"limiar|threshold|confian[çc]a m[ií]nima|gate",
        "reembolso/cancelamento sempre humano": r"(refund|reembolso).{0,80}(humano|human|pessoa)|(humano|human|pessoa).{0,80}(refund|reembolso)",
        "LLM comparado com classificador": r"(llm|gemini|gpt|claude).{0,120}(perdeu|pior|lost|39%|41[,.]0%|42)",
        "vídeo (Loom, YouTube, Drive)": r"loom\.com|youtu|drive\.google",
        "demo publicado (Vercel, Streamlit etc.)": r"vercel\.app|streamlit\.app|railway\.app|onrender\.com|replit\.app",
    }
    contagem = collections.Counter()
    for p in p002:
        n = p["number"]
        arquivos = git(clone, "diff", "--name-only", f"origin/main...pr/{n}").split()
        texto = p.get("body") or ""
        for a in arquivos:
            if a.startswith("submissions/") and a.lower().endswith((".md", ".py", ".ts", ".tsx", ".js", ".html", ".txt")):
                texto += git(clone, "show", f"pr/{n}:{a}")[:200_000]
        for nome, padrao in sinais.items():
            if re.search(padrao, texto, re.I | re.S):
                contagem[nome] += 1
    for nome in sinais:
        print(f"  {contagem[nome]:>2} de {len(p002)}  {nome}")

    # Comentários do avaliador (reviews e comentários de conversa)
    avaliacoes = []
    for p in prs:
        for r in gh(f"repos/{REPO}/pulls/{p['number']}/reviews"):
            if r["user"]["login"] in AVALIADORES and r.get("body"):
                avaliacoes.append((p["number"], r["submitted_at"], r["body"]))
    for c in gh(f"repos/{REPO}/issues/comments?per_page=100"):
        if c["user"]["login"] in AVALIADORES:
            avaliacoes.append((int(c["issue_url"].rsplit("/", 1)[1]), c["created_at"], c["body"]))
    nums002 = {p["number"] for p in p002}
    ultima = max(d for _, d, _ in avaliacoes)
    print(f"\nComentários do avaliador: {len(avaliacoes)} (último em {ultima[:10]})")
    print(f"PRs do 002 com comentário do avaliador: {len({n for n, _, _ in avaliacoes if n in nums002})}")
    sem_avaliacao = [p["number"] for p in p002 if p["created_at"] > ultima]
    print(f"PRs do 002 abertos depois do último comentário: {len(sem_avaliacao)}")

    with open(trabalho / "avaliacoes_002.md", "w") as f:
        for n, d, b in sorted(avaliacoes):
            if n in nums002:
                f.write(f"## PR {n} · {d[:10]}\n\n{b}\n\n")
    print(f"Avaliações do 002 salvas em {trabalho / 'avaliacoes_002.md'}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "levantamento"))
