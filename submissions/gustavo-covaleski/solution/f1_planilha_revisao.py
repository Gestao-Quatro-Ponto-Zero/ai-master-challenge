import numpy as np
import pandas as pd

from comum import OUT_DIR, REVISAO_DIR, SEED, ler_ds2, salvar_csv_excel

TOTAL, MINIMO = 60, 5


def alocar(prev: pd.Series) -> pd.Series:
    extra = TOTAL - MINIMO * len(prev)
    cota = prev * extra
    base = np.floor(cota).astype(int)
    # maiores restos; empate desfeito pela ordem alfabética da categoria (determinístico)
    resto = (cota - base).sort_index().sort_values(ascending=False, kind="stable")
    base[resto.index[: extra - base.sum()]] += 1
    return base + MINIMO


def main():
    df = ler_ds2().merge(pd.read_csv(OUT_DIR / "f1_splits.csv"), on="id")
    hold = df[df["split_grupo"] == "holdout"]
    prev = hold["Topic_group"].value_counts(normalize=True).sort_index()
    n_cat = alocar(prev)

    um_por_grupo = hold.sample(frac=1, random_state=SEED).drop_duplicates("group_id")
    amostra = pd.concat([um_por_grupo[um_por_grupo["Topic_group"] == c].sample(k, random_state=SEED)
                         for c, k in n_cat.items()])
    amostra = amostra.sample(frac=1, random_state=SEED)

    REVISAO_DIR.mkdir(parents=True, exist_ok=True)
    vazio = [""] * len(amostra)
    salvar_csv_excel(pd.DataFrame({"id": amostra["id"].values, "texto": amostra["Document"].values,
                                   "rotulo_original": vazio, "meu_rotulo": vazio, "ambiguo": vazio, "observacao": vazio}),
                     REVISAO_DIR / "revisao_rotulos.csv")
    salvar_csv_excel(amostra[["id", "Topic_group"]].rename(columns={"Topic_group": "rotulo_original"}),
                     REVISAO_DIR / "revisao_gabarito.csv")
    salvar_csv_excel(pd.DataFrame({"categoria": n_cat.index, "n_amostra": n_cat.values,
                                   "prevalencia_holdout": prev.round(6).values}), REVISAO_DIR / "revisao_pesos.csv")
    print(f"{len(amostra)} tickets; por categoria: {n_cat.to_dict()}")
    print("categorias válidas:", sorted(prev.index))


if __name__ == "__main__":
    main()
