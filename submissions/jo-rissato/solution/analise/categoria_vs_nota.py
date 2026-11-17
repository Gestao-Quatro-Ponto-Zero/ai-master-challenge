"""Cruza cada categoria registrada com a nota de satisfação (1 a 5).

Pergunta do Jó (2026-11-10): existe categoria que puxa mais para determinadas notas?
Base: os 2.769 tickets fechados, que são 100% dos tickets com nota.

Para cada variável: tabela categoria × nota em %, média, % de notas 1-2 e 4-5,
qui-quadrado com V de Cramér (corrigido para 7 variáveis) e, para cada célula, o resíduo
padronizado ajustado com limite corrigido para o total de células testadas.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy import stats

ROTULOS = {"Phone": "Telefone", "Chat": "Chat", "Email": "E-mail", "Social media": "Redes sociais",
           "Low": "Baixa", "Medium": "Média", "High": "Alta", "Critical": "Crítica",
           "Refund request": "Reembolso", "Cancellation request": "Cancelamento",
           "Billing inquiry": "Cobrança", "Technical issue": "Problema técnico",
           "Product inquiry": "Dúvida de produto", "Male": "Masculino", "Female": "Feminino",
           "Other": "Outro"}
NOTA = "Customer Satisfaction Rating"
VARIAVEIS = [("Ticket Type", "Tipo de ticket"), ("Ticket Priority", "Prioridade"),
             ("Ticket Channel", "Canal"), ("Ticket Subject", "Assunto"),
             ("Product Purchased", "Produto"), ("Customer Gender", "Gênero do cliente"),
             ("faixa_idade", "Faixa de idade do cliente")]


def residuos(ct: pd.DataFrame) -> pd.DataFrame:
    obs = ct.values.astype(float)
    n = obs.sum()
    lin = obs.sum(1, keepdims=True)
    col = obs.sum(0, keepdims=True)
    esp = lin @ col / n
    adj = (obs - esp) / np.sqrt(esp * (1 - lin / n) * (1 - col / n))
    return pd.DataFrame(adj, index=ct.index, columns=ct.columns)


def main(origem: str, saida: str, csv_saida: str) -> None:
    df = pd.read_csv(origem)
    f = df[df["Ticket Status"] == "Closed"].copy()
    f[NOTA] = f[NOTA].astype(int)
    f["faixa_idade"] = pd.cut(f["Customer Age"], [17, 29, 39, 49, 59, 70],
                              labels=["18-29", "30-39", "40-49", "50-59", "60-70"]).astype(str)
    n_celulas = sum(f[v].nunique() * 5 for v, _ in VARIAVEIS)
    z_lim = stats.norm.ppf(1 - 0.025 / n_celulas)
    md = ["# Categoria × nota de satisfação", "",
          f"Base: {len(f):,} tickets fechados, 100% dos tickets com nota.".replace(",", "."),
          "Leitura: cada linha soma 100%. Na base inteira, cada nota fica perto de 20%.", "",
          "## Resumo por variável", "",
          "| Variável | Categorias | Qui-quadrado | p | p corrigido (×7) | V de Cramér | Puxa a nota? |",
          "|---|---|---|---|---|---|---|"]
    detalhes, linhas_csv, destaques = [], [], []
    for col, nome in VARIAVEIS:
        ct = pd.crosstab(f[col], f[NOTA])
        chi2, p, gl, _ = stats.chi2_contingency(ct)
        v = np.sqrt(chi2 / (ct.values.sum() * (min(ct.shape) - 1)))
        pc = min(p * len(VARIAVEIS), 1.0)
        md.append(f"| {nome} | {ct.shape[0]} | {chi2:.1f} (gl {gl}) | {p:.3f} | {pc:.3f} | {v:.3f} | "
                  f"{'sim' if pc < 0.05 else 'não'} |")
        r = residuos(ct)
        pct = ct.div(ct.sum(1), axis=0) * 100
        media = f.groupby(col)[NOTA].mean()
        detalhes += [f"## {nome}", "",
                     f"Qui-quadrado {chi2:.1f}, p = {p:.3f}, V de Cramér {v:.3f}.", "",
                     "| Categoria | Tickets | Nota 1 | Nota 2 | Nota 3 | Nota 4 | Nota 5 | Média | Notas 1-2 | Notas 4-5 |",
                     "|---|---|---|---|---|---|---|---|---|---|"]
        for cat in ct.sum(1).sort_values(ascending=False).index:
            rot = ROTULOS.get(cat, cat)
            cel = [f"{pct.loc[cat, k]:.1f}%" for k in range(1, 6)]
            baixa = pct.loc[cat, [1, 2]].sum()
            alta = pct.loc[cat, [4, 5]].sum()
            detalhes.append(f"| {rot} | {ct.loc[cat].sum()} | {' | '.join(cel)} | {media[cat]:.2f} | "
                            f"{baixa:.1f}% | {alta:.1f}% |")
            for k in range(1, 6):
                linhas_csv.append({"variavel": nome, "categoria": rot, "nota": k,
                                   "tickets": int(ct.loc[cat, k]), "pct_linha": round(pct.loc[cat, k], 2),
                                   "residuo_ajustado": round(r.loc[cat, k], 2)})
                destaques.append((abs(r.loc[cat, k]), nome, rot, k, pct.loc[cat, k],
                                  int(ct.loc[cat].sum()), r.loc[cat, k]))
        detalhes.append("")
    destaques.sort(reverse=True)
    md += ["", "## As 10 células que mais se afastam de 20%", "",
           f"Resíduo ajustado: quantos desvios a célula está longe do esperado. Com {n_celulas} células "
           f"testadas, o limite corrigido é |{z_lim:.2f}|; abaixo disso, o desvio cabe no acaso.", "",
           "| Variável | Categoria | Nota | % da categoria nessa nota | Tickets da categoria | Resíduo | Passa do limite? |",
           "|---|---|---|---|---|---|---|"]
    for a, nome, rot, k, pc_, n, rr in destaques[:10]:
        md.append(f"| {nome} | {rot} | {k} | {pc_:.1f}% | {n} | {rr:+.2f} | {'sim' if a > z_lim else 'não'} |")
    acima = sum(1 for d in destaques if d[0] > z_lim)
    md += ["", f"Células acima do limite corrigido: {acima} de {n_celulas}.", ""] + detalhes
    with open(saida, "w") as fh:
        fh.write("\n".join(md) + "\n")
    pd.DataFrame(linhas_csv).to_csv(csv_saida, index=False)
    print("\n".join(md[:30]))


if __name__ == "__main__":
    main(*sys.argv[1:4])
