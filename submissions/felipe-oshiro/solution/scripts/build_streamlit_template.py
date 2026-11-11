"""PASSO 4 — Gera o template do app Streamlit a partir do dashboard_g4.html.

Lê solution/dashboard/dashboard_g4.html (fonte única do design), remove as
tags de envolvimento de documento (DOCTYPE/<html>/<body>) e insere o marcador
`<!-- classifier-slot -->` no fim da seção 2 (antes da linha de fontes),
onde o app Streamlit injeta o bloco interativo.

Saída: solution/dashboard/streamlit_template.html

Como rodar:
  solution/.venv/bin/python solution/scripts/build_streamlit_template.py

Reexecutar sempre que o dashboard_g4.html mudar — o template é gerado,
nunca editado à mão.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "dashboard" / "dashboard_g4.html"
DST = ROOT / "dashboard" / "streamlit_template.html"
SLOT = "<!-- classifier-slot -->"
ANCHOR = '<p class="src">Fontes: <code>solution/artifacts/step1_results.json</code>'

html = SRC.read_text(encoding="utf-8")

for tag in ('<!DOCTYPE html>', '<html lang="pt-BR">', '</html>',
            '<body>', '</body>'):
    html = html.replace(tag, "")

assert ANCHOR in html, "âncora da linha de fontes da seção 2 não encontrada"
assert SLOT not in html, "marcador já presente no dashboard de origem"

html = html.replace(ANCHOR, SLOT + "\n" + ANCHOR)

DST.write_text(html, encoding="utf-8")
print(f"[build_streamlit_template] template gerado: {DST} ({len(html)/1e6:.1f} MB)")
