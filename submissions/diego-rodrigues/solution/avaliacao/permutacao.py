"""Os atributos do deal predizem o ganho? Embaralhamento dos resultados, com e sem controle de calendário."""
from __future__ import annotations

import numpy as np
import pandas as pd

from avaliacao.backtest import NUMERO_CONTROLE, cortes_padrao, preparar_corte


def historico(dados, config: dict, cortes=None) -> pd.DataFrame:
    """Um registro por deal com conta preenchida: o primeiro corte em que ele estava vivo.

    Deals sem conta saem: o campo `account` só é preenchido depois do desfecho
    (0 de 6.711 fechados não têm conta; 1.425 abertos não têm). Contá-los
    deixa o resultado vazar para o atributo. Um deal aberto atravessa vários
    cortes; contá-lo em todos faria o teste tratar repetições como independentes.
    """
    porte = pd.qcut(dados.contas.set_index("account").employees, 4, labels=False, duplicates="drop")
    linhas = []
    for corte in cortes or cortes_padrao():
        prep = preparar_corte(dados, config, corte)
        if prep is None:
            continue
        s, _ = prep
        v = s[(s.estado == "vivo") & s.conta.notna()]
        linhas.append(pd.DataFrame({
            "opportunity_id": v.opportunity_id.values,
            "mes_do_trimestre": (corte.month - 1) % 3 + 1,
            "conta": v.conta.values,
            "vendedor": v.vendedor.values,
            "gerente": v.gerente.values,
            "regiao": v.regiao.values,
            "setor": v.setor.values,
            "porte": [porte.get(c) for c in v.conta],
            "produto": v.produto.values,
            "ganhou": v.ganhou.values,
        }))
    return (pd.concat(linhas, ignore_index=True)
            .drop_duplicates("opportunity_id", keep="first")
            .drop(columns="opportunity_id")
            .reset_index(drop=True))


def _variancia_entre_grupos(df: pd.DataFrame, chave) -> float:
    return float(df.groupby(chave)["ganhou"].mean().var())


def permutacao(historico_df: pd.DataFrame, chave, estratificar_por=None, n: int = 300,
               controle: int = NUMERO_CONTROLE) -> dict:
    """p-valor: fração de embaralhamentos com variância entre grupos igual ou maior que a observada."""
    rng = np.random.default_rng(controle)
    observada = _variancia_entre_grupos(historico_df, chave)
    perms = []
    for _ in range(n):
        df = historico_df.copy()
        if estratificar_por is None:
            df["ganhou"] = rng.permutation(df["ganhou"].values)
        else:
            df["ganhou"] = df.groupby(estratificar_por)["ganhou"].transform(
                lambda x: rng.permutation(x.values)
            )
        perms.append(_variancia_entre_grupos(df, chave))
    perms = np.array(perms)
    return {
        "observada": observada,
        "media_permutada": float(perms.mean()),
        "p": float((np.sum(perms >= observada) + 1) / (n + 1)),
    }
