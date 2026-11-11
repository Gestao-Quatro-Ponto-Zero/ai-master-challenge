"""Auditoria do Dataset 2 (tickets de TI rotulados), antes de treinar o classificador.

Verifica estrutura, vazios, duplicatas, conflito de rótulo, pré-processamento do texto,
tamanho por categoria, desequilíbrio entre categorias, textos-modelo repetidos e
palavras ambíguas entre categorias. Gera um relatório em markdown.
"""
from __future__ import annotations

import sys

import pandas as pd

ROTULOS = {"Hardware": "Hardware", "HR Support": "Suporte de RH", "Access": "Acesso",
           "Miscellaneous": "Diversos", "Storage": "Armazenamento", "Purchase": "Compra",
           "Internal Project": "Projeto interno", "Administrative rights": "Direitos de administrador"}
AMBIGUAS = {"password, login, locked, unlock": r"\b(password|login|locked|unlock)\b",
            "leave, holiday, salary, payroll, vacation": r"\b(leave|holiday|salary|payroll|vacation)\b",
            "admin rights, administrator, local admin": r"\b(admin rights|administrator|local admin)\b"}


def fmt(n: float) -> str:
    return f"{n:,.0f}".replace(",", ".")


def main(origem: str, saida: str) -> None:
    d = pd.read_csv(origem)
    t = d["Document"]
    n = len(d)
    d["palavras"] = t.str.split().str.len()
    norm = t.str.lower().str.replace(r"[^a-z ]", " ", regex=True).str.split().str.join(" ")
    conflito = int((d.assign(k=norm).groupby("k")["Topic_group"].nunique() > 1).sum())
    md = ["# Auditoria do Dataset 2", "",
          f"Arquivo: `all_tickets_processed_improved_v3.csv`. Base: {fmt(n)} textos, 2 colunas "
          "(`Document`, `Topic_group`).", "",
          "## 1. Integridade", "",
          "| Verificação | Resultado |", "|---|---|",
          f"| Valores vazios | {int(d.isna().sum().sum())} |",
          f"| Textos duplicados exatos | {int(t.duplicated().sum())} |",
          f"| Duplicados após normalizar (minúsculas, só letras) | {int(norm.duplicated().sum())} |",
          f"| Mesmo texto com rótulos diferentes | {conflito} |",
          f"| Textos com 3 palavras ou menos | {int((d.palavras <= 3).sum())} |",
          f"| Textos com mais de 200 palavras | {fmt((d.palavras > 200).sum())} |", "",
          "## 2. O texto já vem pré-processado", "",
          "| Marca | Textos |", "|---|---|",
          f"| Com letra maiúscula | {int(t.str.contains(r'[A-Z]').sum())} |",
          f"| Com dígito | {int(t.str.contains(r'[0-9]').sum())} |",
          f"| Com @ (e-mail) | {int(t.str.contains('@').sum())} |",
          f"| Com pontuação (. , ! ?) | {int(t.str.contains(r'[.,!?]').sum())} |",
          f"| Com caractere fora do ASCII | {int(t.str.contains(r'[^\x00-\x7f]').sum())} |", "",
          "O texto está em inglês, em minúsculas, sem números, sem e-mails e quase sem pontuação. "
          "Esse tratamento foi feito antes da publicação. Para o classificador, isso quer dizer "
          "que um ticket novo precisa passar pelo mesmo tratamento antes de ser classificado.", "",
          "## 3. Categorias", "",
          "| Categoria | Textos | % | Mediana de palavras |", "|---|---|---|---|"]
    vc = d["Topic_group"].value_counts()
    med = d.groupby("Topic_group")["palavras"].median()
    for cat, q in vc.items():
        md.append(f"| {ROTULOS[cat]} ({cat}) | {fmt(q)} | {q / n * 100:.1f}% | {med[cat]:.0f} |")
    md += ["", f"A maior categoria tem {vc.max() / vc.min():.1f} vezes o volume da menor. Acurácia geral "
           "esconde as categorias pequenas, então o classificador será medido por categoria.", "",
           "## 4. Textos-modelo repetidos", ""]
    p = t.str.split().str[:6].str.join(" ")
    pv = p.value_counts()
    rep = pv[pv >= 20]
    g = (d[p.isin(rep.index)].assign(p=p).groupby("p")["Topic_group"]
         .agg(textos="size", categorias="nunique", principal=lambda s: s.value_counts().index[0],
              pct=lambda s: s.value_counts(normalize=True).iloc[0] * 100)
         .sort_values("textos", ascending=False))
    compra_modelo = int(d[p.str.startswith("new purchase po")]["Topic_group"].eq("Purchase").sum())
    md += [f"{len(rep)} começos de texto (6 primeiras palavras) se repetem em 20 textos ou mais, cobrindo "
           f"{fmt(rep.sum())} textos ({rep.sum() / n * 100:.1f}%). Em {int((g.categorias == 1).sum())} deles "
           "todos os textos têm a mesma categoria.", "",
           "| Começo do texto | Textos | Categorias | Categoria principal | % na principal |",
           "|---|---|---|---|---|"]
    for k, r in g.head(8).iterrows():
        md.append(f"| {k} | {r.textos} | {r.categorias} | {ROTULOS[r.principal]} | {r.pct:.1f}% |")
    md += ["", f"Os textos que começam com \"new purchase po\" e são de Compra somam {fmt(compra_modelo)}, "
           f"{compra_modelo / vc['Purchase'] * 100:.1f}% da categoria Compra ({fmt(vc['Purchase'])}). "
           "São formulários automáticos, fáceis de acertar, e podem inflar o acerto dessa categoria. "
           "O classificador será medido também sem esses textos-modelo.", "",
           "## 5. Palavras que aparecem em várias categorias", "",
           "| Palavras | Textos | Distribuição pelas 3 categorias principais |", "|---|---|---|"]
    for nome, pat in AMBIGUAS.items():
        m = t.str.contains(pat, regex=True).fillna(False)  # noqa
        dist = (d[m]["Topic_group"].value_counts(normalize=True) * 100).head(3)
        md.append(f"| {nome} | {fmt(m.sum())} | "
                  + ", ".join(f"{ROTULOS[c]} {v:.1f}%" for c, v in dist.items()) + " |")
    md += ["", "Lendo os exemplos, a mesma palavra muda de sentido conforme o contexto: \"leave\" é férias em "
           "Suporte de RH e é o verbo \"deixar\" em Hardware; \"locked\" é conta bloqueada em Acesso e é "
           "aparelho bloqueado em Compra; \"administrator\" é a assinatura do formulário de compra (1.184 dos "
           "1.980 textos de Compra com essas palavras começam com \"new purchase po\"). Isso não prova "
           "rótulo errado. Mostra que regra por palavra-chave erra e que o classificador precisa do contexto "
           "do texto inteiro.", "",
           "## 6. O que a auditoria permite e o que não permite", "",
           "- Permite: treinar um classificador de 8 categorias sobre textos sem vazio, sem duplicata e sem "
           "conflito de rótulo.",
           "- Não permite: medir tempo, satisfação ou resolução, porque o Dataset 2 só tem texto e categoria.",
           "- Não permite: ligar o Dataset 2 ao Dataset 1 (lacuna 12). As 8 categorias de TI interna não são "
           "os 5 tipos do Dataset 1 (reembolso, cancelamento etc.).",
           "- Não permite afirmar que os rótulos estão todos certos: só a matriz de confusão do classificador "
           "vai mostrar onde as categorias se confundem.", ""]
    with open(saida, "w") as fh:
        fh.write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main(*sys.argv[1:3])
