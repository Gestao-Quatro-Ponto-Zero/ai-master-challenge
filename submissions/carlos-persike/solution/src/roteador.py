"""Protótipo: roteador automático de tickets.

Fluxo: ticket novo -> classifica categoria -> mede confianca -> decide
"automatizar" (sugerir categoria/resposta direto) ou "escalar pra humano".

Roda sobre o holdout real do Dataset 2 (46k tickets de IT, texto real —
ver auditoria.py sobre por que o Dataset 1 nao serve pra isso), nao sobre
exemplos escolhidos a dedo. Isso é o que o brief pede: "funciona com dados
reais, nao com 3 exemplos cherry-picked".

Categorias sempre escaladas pra humano por politica de negocio, mesmo
quando o classificador acerta com confianca alta: dados sensiveis de
pessoas (HR Support) nao devem virar acao automatica so porque o texto
foi classificado corretamente — classificar certo != decisao segura de
automatizar. Ver README, secao "O que nao automatizar".
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from classificador import carregar, separar_treino_teste, treinar

RAIZ = Path(__file__).resolve().parents[4]
OUTPUTS = RAIZ / "submissions" / "carlos-persike" / "solution" / "outputs"

LIMIAR_CONFIANCA = 0.7  # margem entre 1a e 2a classe; calibrado p/ acuracia >=95% no bucket automatizado (ver process log)
CATEGORIAS_SEMPRE_HUMANO = {"HR Support"}


def confianca(margens: np.ndarray) -> np.ndarray:
    """Diferenca entre a maior e a segunda maior margem por linha.
    Proxy de confianca pra LinearSVC (nao tem predict_proba nativo)."""
    ordenado = np.sort(margens, axis=1)
    return ordenado[:, -1] - ordenado[:, -2]


def rotear() -> dict:
    df = carregar()
    X_treino, X_teste, y_treino, y_teste = separar_treino_teste(df)
    pipeline = treinar(X_treino, y_treino)

    pred = pipeline.predict(X_teste)
    margens = pipeline.decision_function(X_teste)
    conf = confianca(margens)

    decisao = np.where(
        (conf >= LIMIAR_CONFIANCA) & (~pd.Series(pred, index=X_teste.index).isin(CATEGORIAS_SEMPRE_HUMANO)),
        "AUTOMATIZAR",
        "ESCALAR_HUMANO",
    )

    resultado_df = pd.DataFrame({
        "real": y_teste.values,
        "previsto": pred,
        "confianca": conf,
        "decisao": decisao,
    }, index=X_teste.index)

    auto = resultado_df[resultado_df["decisao"] == "AUTOMATIZAR"]
    humano = resultado_df[resultado_df["decisao"] == "ESCALAR_HUMANO"]

    acc_auto = (auto["real"] == auto["previsto"]).mean() if len(auto) else float("nan")
    acc_humano = (humano["real"] == humano["previsto"]).mean() if len(humano) else float("nan")
    acc_geral = (resultado_df["real"] == resultado_df["previsto"]).mean()

    resultado = {
        "limiar_confianca": LIMIAR_CONFIANCA,
        "categorias_sempre_humano": sorted(CATEGORIAS_SEMPRE_HUMANO),
        "total_tickets_avaliados": len(resultado_df),
        "pct_automatizado": round(len(auto) / len(resultado_df) * 100, 1),
        "pct_escalado_humano": round(len(humano) / len(resultado_df) * 100, 1),
        "acuracia_no_bucket_automatizado": round(float(acc_auto), 4),
        "acuracia_no_bucket_escalado": round(float(acc_humano), 4),
        "acuracia_geral_sem_filtro": round(float(acc_geral), 4),
    }

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "roteador_resultado.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

    return resultado


def main() -> None:
    resultado = rotear()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
