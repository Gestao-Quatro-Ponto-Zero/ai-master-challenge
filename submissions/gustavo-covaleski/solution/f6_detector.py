import pandas as pd

from comum import OUT_DIR, SEED, ler_ds2, salvar_json
from f5_injecao import N_TICKETS, montar_pares
from triagem import carregar_modelo, detectar_injecao, mascarar

LIMITE_FALSO_POSITIVO = 0.01  # regra de adoção fixada na spec F6, antes de medir


def main():
    df = ler_ds2().merge(pd.read_csv(OUT_DIR / "f1_splits.csv"), on="id")
    ho = df[df["split_grupo"] == "holdout"]
    disparo = ho["Document"].map(lambda t: detectar_injecao(mascarar(t)))
    fp = float(disparo.mean())

    m = carregar_modelo()["pipeline"]
    tickets = ho.sample(N_TICKETS, random_state=SEED)
    pares = montar_pares(tickets, dict(zip(tickets["id"], m.predict(tickets["Document"]))), sorted(m.classes_))
    cob = [detectar_injecao(mascarar(p["texto"])) for p in pares]
    por_ataque = pd.DataFrame({"ataque": [p["ataque"] for p in pares], "d": cob}).groupby("ataque")["d"].sum().astype(int).to_dict()

    # o que dispara nos tickets limpos: padrão de instrução ou nome de categoria repetido
    from triagem import RE_INJECAO
    so_padrao = ho.loc[disparo, "Document"].map(lambda t: bool(RE_INJECAO.search(mascarar(t).lower()))).sum()

    adotar = fp <= LIMITE_FALSO_POSITIVO
    saida = {"criterio": "fixado na spec F6 antes de medir: ignore|instruction|system:|categoria|category|classify|classifique|{|} "
                         "ou nome de categoria repetido 3+ vezes; só rebaixa para humano decide",
             "falso_positivo_holdout": {"n": int(disparo.sum()), "n_holdout": int(len(ho)), "taxa": round(fp, 4),
                                        "por_padrao_de_instrucao": int(so_padrao),
                                        "so_por_nome_repetido": int(disparo.sum() - so_padrao)},
             "cobertura_100_pares": {"n": int(sum(cob)), "taxa": round(sum(cob) / len(cob), 4), "por_ataque": por_ataque},
             "regra_de_adocao": f"adotar se falso positivo ≤ {LIMITE_FALSO_POSITIVO:.0%}",
             "adotado": adotar}
    salvar_json(saida, "f6_detector.json")
    print(saida)


if __name__ == "__main__":
    main()
