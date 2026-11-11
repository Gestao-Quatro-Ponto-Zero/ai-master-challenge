"""Relatório produto × segmento do Dataset 1 (customer_support_tickets.csv).

Segmentos: os 5 tipos de ticket (Ticket Type) e os assuntos "Delivery problem" e "Payment issue"
(Ticket Subject). Para cada segmento, quantos tickets cada produto tem e qual a fatia (%) do
segmento. Compara com a fatia do produto no total para mostrar se algum produto concentra o problema.

Uso: python3 produto_por_segmento.py <caminho do csv> <saida.md> <saida.csv>
"""
from __future__ import annotations

import csv
import sys
from collections import Counter

SOFTWARE = {"Microsoft Office", "Adobe Photoshop", "Autodesk AutoCAD"}
SEGMENTOS = [
    ("Reembolso", "Ticket Type", "Refund request"),
    ("Cancelamento", "Ticket Type", "Cancellation request"),
    ("Cobrança", "Ticket Type", "Billing inquiry"),
    ("Problema técnico", "Ticket Type", "Technical issue"),
    ("Dúvida de produto", "Ticket Type", "Product inquiry"),
    ("Entrega (assunto)", "Ticket Subject", "Delivery problem"),
    ("Pagamento (assunto)", "Ticket Subject", "Payment issue"),
]


def main(origem: str, saida_md: str, saida_csv: str) -> None:
    with open(origem, newline="", encoding="utf-8") as h:
        linhas = list(csv.DictReader(h))
    total = Counter(r["Product Purchased"] for r in linhas)
    n_total = len(linhas)
    contagens = {}
    for nome, coluna, valor in SEGMENTOS:
        sel = [r for r in linhas if r[coluna] == valor]
        contagens[nome] = (len(sel), Counter(r["Product Purchased"] for r in sel))

    produtos = sorted(total, key=lambda p: (-total[p], p))
    with open(saida_csv, "w", newline="", encoding="utf-8") as h:
        w = csv.writer(h)
        w.writerow(["produto", "categoria", "tickets_total", "pct_total"]
                   + [f"{n}_{s}" for n, *_ in SEGMENTOS for s in ("tickets", "pct")])
        for p in produtos:
            linha = [p, "software" if p in SOFTWARE else "hardware", total[p],
                     round(100 * total[p] / n_total, 2)]
            for nome, *_ in SEGMENTOS:
                n_seg, c = contagens[nome]
                linha += [c[p], round(100 * c[p] / n_seg, 2)]
            w.writerow(linha)

    md = ["# Produto × segmento de ticket (Dataset 1)", "",
          f"Base: {n_total} tickets, 42 produtos. Cada célula = % do segmento (tickets entre parênteses).",
          "Coluna \"Total\" = fatia do produto em todos os tickets. Se algum produto concentrasse um "
          "problema, sua % no segmento ficaria muito acima da % no total.", "",
          "## Tamanho dos segmentos", "", "| Segmento | Tickets | % da base |", "|---|---|---|"]
    for nome, *_ in SEGMENTOS:
        n_seg = contagens[nome][0]
        md.append(f"| {nome} | {n_seg} | {100 * n_seg / n_total:.1f}% |")
    md += ["", "## Todos os produtos", "",
           "| Produto | Tipo | Total | " + " | ".join(n for n, *_ in SEGMENTOS) + " |",
           "|---|---|---|" + "---|" * len(SEGMENTOS)]
    for p in produtos:
        cel = [f"{100 * contagens[n][1][p] / contagens[n][0]:.1f}% ({contagens[n][1][p]})"
               for n, *_ in SEGMENTOS]
        md.append(f"| {p} | {'software' if p in SOFTWARE else 'hardware'} | "
                  f"{100 * total[p] / n_total:.1f}% ({total[p]}) | " + " | ".join(cel) + " |")

    md += ["", "## Software × hardware", "", "| Segmento | Software | Hardware |", "|---|---|---|"]
    soft_total = sum(total[p] for p in SOFTWARE)
    md.append(f"| Total | {100 * soft_total / n_total:.1f}% ({soft_total}) | "
              f"{100 * (n_total - soft_total) / n_total:.1f}% ({n_total - soft_total}) |")
    for nome, *_ in SEGMENTOS:
        n_seg, c = contagens[nome]
        s = sum(c[p] for p in SOFTWARE)
        md.append(f"| {nome} | {100 * s / n_seg:.1f}% ({s}) | {100 * (n_seg - s) / n_seg:.1f}% ({n_seg - s}) |")

    md += ["", "## Quanto cada segmento se afasta do total", "",
           "Maior diferença, em pontos percentuais, entre a fatia de um produto no segmento e a fatia dele no total.",
           "", "| Segmento | Produto com maior desvio | No segmento | No total | Diferença |", "|---|---|---|---|---|"]
    for nome, *_ in SEGMENTOS:
        n_seg, c = contagens[nome]
        p = max(produtos, key=lambda x: abs(c[x] / n_seg - total[x] / n_total))
        a, b = 100 * c[p] / n_seg, 100 * total[p] / n_total
        md.append(f"| {nome} | {p} | {a:.1f}% | {b:.1f}% | {a - b:+.1f} p.p. |")
    with open(saida_md, "w", encoding="utf-8") as h:
        h.write("\n".join(md) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:4])
