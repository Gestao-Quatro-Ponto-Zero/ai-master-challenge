"""Gera a tabela de contraste (WCAG AA) a partir de app/style.css e a grava em docs/DESIGN.md.

Uso (cwd = solution/):
    python tools/contrast_table.py            # imprime a tabela
    python tools/contrast_table.py --write    # substitui o bloco entre os marcadores em docs/DESIGN.md
Os pares e os mínimos estão em check_app.contrast_pairs(); o check_app reprova o build se algum cair abaixo.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from check_app import contrast_rows

sys.stdout.reconfigure(encoding="utf-8")
SOL = Path(__file__).resolve().parent.parent
CSS = SOL / "app" / "style.css"
DESIGN = SOL.parent / "docs" / "DESIGN.md"
START, END = "<!-- CONTRASTE:inicio -->", "<!-- CONTRASTE:fim -->"


def table() -> str:
    rows = contrast_rows(CSS.read_text(encoding="utf-8"))
    out = ["| Texto ou elemento | Sobre | Uso | Mínimo | Claro | Escuro | Resultado |", "| :--- | :--- | :--- | ---: | ---: | ---: | :--- |"]
    fmt = lambda r: f"{r:.2f}".replace(".", ",") + ":1"  # noqa: E731
    for a, b, where, need, rl, rd, bad in rows:
        out.append(f"| `{a}` | `{b}` | {where} | {fmt(need)} | {fmt(rl)} | {fmt(rd)} | {'FALHA' if bad else 'passa'} |")
    worst_l = min(r[4] / r[3] for r in rows)
    worst_d = min(r[5] / r[3] for r in rows)
    out.append("")
    out.append(f"{len(rows)} pares, nos dois temas. Menor razão entre o medido e o mínimo exigido: claro {worst_l:.2f}x, escuro {worst_d:.2f}x (acima de 1,00x passa).".replace("x,", "x,").replace(f"{worst_l:.2f}", f"{worst_l:.2f}".replace(".", ",")).replace(f"{worst_d:.2f}", f"{worst_d:.2f}".replace(".", ",")))
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    t = table()
    if not ap.parse_args().write:
        print(t)
        sys.exit(0)
    text = DESIGN.read_text(encoding="utf-8")
    block = f"{START}\n{t}\n{END}"
    if START in text:
        head, rest = text.split(START, 1)
        text = head + block + rest.split(END, 1)[1]
    else:
        text = text.replace("<!-- CONTRASTE -->", block)
    DESIGN.write_text(text, encoding="utf-8", newline="\n")
    print(f"tabela gravada em {DESIGN}")
