"""
Diagnóstico do dataset de suporte (Dataset 1): qualidade dos dados + gargalos + satisfação.
Roda: python submissions/adson-valeriano/solution/diagnostico.py
"""
from pathlib import Path

import pandas as pd
from scipy import stats

RAIZ = Path(__file__).resolve().parents[3]
SAIDA = Path(__file__).resolve().parent / "resultados_diagnostico.md"


def pct(x):
    return f"{x:.1%}"


def main():
    d = pd.read_csv(RAIZ / "datasets" / "customer_support_tickets.csv")
    L = ["# Diagnóstico do dataset de suporte", "", f"Total de tickets: {len(d):,}".replace(",", "."), ""]

    # 1) Qualidade dos dados
    L += ["## 1. Qualidade dos dados (antes de qualquer conclusão)", ""]
    status = d["Ticket Status"].value_counts()
    L.append("Tickets por status: " + ", ".join(f"{k} {v}" for k, v in status.items()))
    for s, g in d.groupby("Ticket Status"):
        L.append(f"- {s}: tempo preenchido {pct(g['Time to Resolution'].notna().mean())}, "
                 f"satisfação preenchida {pct(g['Customer Satisfaction Rating'].notna().mean())}")

    c = d[d["Ticket Status"] == "Closed"].copy()
    frt = pd.to_datetime(c["First Response Time"])
    ttr = pd.to_datetime(c["Time to Resolution"])
    horas = (ttr - frt).dt.total_seconds() / 3600
    todas_frt = pd.to_datetime(d["First Response Time"].dropna())
    janela = (todas_frt.max() - todas_frt.min()).total_seconds() / 3600
    L += [
        f"- As colunas de 'tempo' são data/hora, não duração. Todas as primeiras respostas cabem em {janela:.0f} horas "
        f"({todas_frt.min():%d/%m/%Y} a {todas_frt.max():%d/%m/%Y}).",
        f"- Em {pct((horas < 0).mean())} dos tickets fechados, a resolução acontece ANTES da primeira resposta.",
        "- Distribuição da satisfação (1 a 5): " + ", ".join(
            f"{int(k)}: {v}" for k, v in d["Customer Satisfaction Rating"].value_counts().sort_index().items()),
        f"- Descrições com o texto-modelo '{{product_purchased}}' não preenchido: "
        f"{pct(d['Ticket Description'].str.contains('{product_purchased}', regex=False).mean())}",
        f"- Frases de abertura diferentes nas descrições: {d['Ticket Description'].str.split('.').str[0].nunique()}",
        f"- Domínios de e-mail: {', '.join(d['Customer Email'].str.split('@').str[1].value_counts().index[:3])}",
        "",
    ]

    # 2) Gargalos
    L += ["## 2. Onde o fluxo trava?", ""]
    for col in ["Ticket Channel", "Ticket Type", "Ticket Priority"]:
        tab = pd.crosstab(d[col], d["Ticket Status"], normalize="index").round(3)
        L += [f"### Status por {col}", "", tab.to_markdown(), ""]
    L.append(f"- Tickets parados aguardando o cliente: {status.get('Pending Customer Response', 0)} "
             f"({pct(status.get('Pending Customer Response', 0) / len(d))})")
    L.append("")

    # 3) Satisfação
    L += ["## 3. O que impacta a satisfação?", ""]
    for col in ["Ticket Channel", "Ticket Type", "Ticket Priority"]:
        grupos = [g["Customer Satisfaction Rating"].values for _, g in c.groupby(col)]
        p = stats.f_oneway(*grupos).pvalue
        medias = c.groupby(col)["Customer Satisfaction Rating"].mean().round(2).to_dict()
        L.append(f"- {col}: médias {medias} | ANOVA p = {p:.2f} "
                 f"({'diferença real' if p < 0.05 else 'diferença compatível com acaso'})")
    corr = pd.Series(horas.values).corr(c["Customer Satisfaction Rating"].reset_index(drop=True))
    L.append(f"- Correlação entre o 'tempo' calculado e a satisfação: {corr:.2f}")
    L += ["", "Conclusão: com estes dados não é possível afirmar onde se perde tempo nem o que move a satisfação. "
          "O achado é que a operação não mede de forma confiável o que importa."]

    SAIDA.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
