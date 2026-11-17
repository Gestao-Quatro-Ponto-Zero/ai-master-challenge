"""Roda o roteador sobre todos os tickets reais do teste (20% do Dataset 2, nunca vistos no treino).

Responde ao critério do brief "funciona com dados reais, não com 3 exemplos cherry-picked".
Uso: python lote.py  (gera saida/lote-teste.csv e imprime o resumo)
"""
from __future__ import annotations

import pandas as pd

from config import LIMITE_CONFIANCA, LOTE
from modelo import carregar, separar
from roteador import FILA, ROTULOS, acao_sensivel, decidir_lote


def rodar() -> pd.DataFrame:
    modelo = carregar()
    _, xte, _, yte = separar()
    p = modelo.predict_proba(xte)
    df = pd.DataFrame({"texto": xte.values, "categoria_real": yte.values,
                       "categoria_prevista": modelo.classes_[p.argmax(1)], "confianca": p.max(1).round(4)})
    df["destino"] = df["confianca"].map(decidir_lote)
    df["acao_sensivel"] = df["texto"].map(acao_sensivel)
    df["acertou"] = df["categoria_real"] == df["categoria_prevista"]
    LOTE.parent.mkdir(exist_ok=True)
    df.to_csv(LOTE, index=False)
    return df


def resumo(df: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for cat, g in df.groupby("categoria_real"):
        auto = g[g.destino == FILA]
        linhas.append({"categoria": ROTULOS[cat], "tickets": len(g),
                       "roteados_pela_ia": round(len(auto) / len(g) * 100, 1),
                       "acerto_quando_roteia": round(auto.acertou.mean() * 100, 1) if len(auto) else None,
                       "para_triagem_humana": round((1 - len(auto) / len(g)) * 100, 1)})
    return pd.DataFrame(linhas).sort_values("tickets", ascending=False)


if __name__ == "__main__":
    df = rodar()
    auto = df[df.destino == FILA]
    print(f"{len(df)} tickets reais do teste, limite {LIMITE_CONFIANCA}")
    print(f"roteados pela IA: {len(auto)} ({len(auto) / len(df) * 100:.1f}%), "
          f"acerto {auto.acertou.mean() * 100:.1f}%")
    print(f"triagem humana: {len(df) - len(auto)} ({(1 - len(auto) / len(df)) * 100:.1f}%)")
    print(f"com sinal de ação sensível: {df.acao_sensivel.notna().sum()}")
    print(df.acao_sensivel.value_counts().to_string())
    print(resumo(df).to_string(index=False))
