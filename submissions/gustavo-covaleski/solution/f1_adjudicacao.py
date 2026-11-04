import argparse
import sys
from pathlib import Path

import pandas as pd

from comum import PROCESS_LOG_DIR, REVISAO_DIR, ler_csv_excel, salvar_csv_excel

CATEGORIAS = {"Access", "Administrative rights", "HR Support", "Hardware", "Internal Project",
              "Miscellaneous", "Purchase", "Storage"}
DESFECHOS = {"original errado", "eu errei", "ambíguo"}


def falhar(msg, linhas):
    print(msg)
    for l in linhas:
        print("  ", l)
    sys.exit(1)


def preparar(dir_rev: Path):
    rev = ler_csv_excel(dir_rev / "revisao_rotulos.csv")
    gab = ler_csv_excel(dir_rev / "revisao_gabarito.csv")
    rev["meu_rotulo"] = rev["meu_rotulo"].str.strip()
    rev["ambiguo"] = rev["ambiguo"].str.strip().str.lower()
    ruins = rev[~rev["meu_rotulo"].isin(CATEGORIAS) | ~rev["ambiguo"].isin({"s", "n"})]
    if len(ruins):
        falhar(f"{len(ruins)} linha(s) inválida(s): meu_rotulo fora das 8 categorias ou ambiguo fora de s/n.",
               [f"id={r.id} meu_rotulo={r.meu_rotulo!r} ambiguo={r.ambiguo!r}" for r in ruins.itertuples()])
    if set(rev["id"]) != set(gab["id"]):
        falhar("ids da revisão e do gabarito não coincidem.", sorted(set(rev["id"]) ^ set(gab["id"])))
    m = rev.drop(columns="rotulo_original").merge(gab, on="id")
    div = m[m["meu_rotulo"] != m["rotulo_original"]]
    salvar_csv_excel(div[["id", "texto", "meu_rotulo", "rotulo_original"]].assign(adjudicacao="", observacao_adjudicacao=""),
                     dir_rev / "adjudicacao.csv")
    print(f"{len(div)} de {len(m)} divergiram; ver {dir_rev / 'adjudicacao.csv'}")


def consolidar(dir_rev: Path, dir_saida: Path):
    rev = ler_csv_excel(dir_rev / "revisao_rotulos.csv")
    gab = ler_csv_excel(dir_rev / "revisao_gabarito.csv")
    adj = ler_csv_excel(dir_rev / "adjudicacao.csv")
    adj["adjudicacao"] = adj["adjudicacao"].str.strip()
    ruins = adj[~adj["adjudicacao"].isin(DESFECHOS)]
    if len(ruins):
        falhar(f"{len(ruins)} linha(s) com adjudicacao fora de {sorted(DESFECHOS)}.",
               [f"id={r.id} adjudicacao={r.adjudicacao!r}" for r in ruins.itertuples()])
    final = (rev.drop(columns="rotulo_original").merge(gab, on="id", how="left")
             .merge(adj[["id", "adjudicacao", "observacao_adjudicacao"]], on="id", how="left").fillna(""))
    final = final[["id", "texto", "rotulo_original", "meu_rotulo", "ambiguo", "observacao",
                   "adjudicacao", "observacao_adjudicacao"]]
    salvar_csv_excel(final, dir_saida / "revisao_rotulos_adjudicada.csv")
    desfecho = final["adjudicacao"].replace("", "sem divergência")
    print(f"{len(final)} linhas gravadas em {dir_saida / 'revisao_rotulos_adjudicada.csv'}")
    print("por desfecho:", desfecho.value_counts().to_dict())
    print(pd.crosstab(final["rotulo_original"], desfecho).to_string())


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("modo", choices=["preparar", "consolidar"])
    p.add_argument("--dir-revisao", type=Path, default=REVISAO_DIR)
    p.add_argument("--dir-saida", type=Path, default=PROCESS_LOG_DIR)
    a = p.parse_args(argv)
    if a.modo == "preparar":
        preparar(a.dir_revisao)
    else:
        consolidar(a.dir_revisao, a.dir_saida)


if __name__ == "__main__":
    main()
