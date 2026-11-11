"""Avisa quando o que o motor aprendeu muda: janela, regra do trimestre, destino por faixa e carga."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from motor.aprender import carga_referencia, tabela_destino
from motor.carregar import carregar, recortar
from motor.janela import aprender_janela

RAIZ = Path(__file__).parent


def aprendido(pasta_dados, config: dict, hoje: pd.Timestamp) -> dict:
    d = carregar(pasta_dados)
    r = recortar(d, hoje)
    j = aprender_janela(r, config)
    t = tabela_destino(r, j, config, hoje)
    c = carga_referencia(r, hoje)
    return {
        "hoje": hoje.date().isoformat(),
        "ciclo_max": j.ciclo_max,
        "usa_prazo_trimestre": j.usa_prazo_trimestre,
        "p_decide": {faixa: round(float(p), 3) for faixa, p in t.p_decide.items()},
        "carga_referencia": {vendedor: round(float(x), 1) for vendedor, x in c.items()},
    }


def _mensagem(item: str, guardado, novo) -> str:
    if item == "ciclo_max":
        return (f"o ciclo máximo passou de {guardado} para {novo} dias: "
                "a janela de validade mudou e a fila de encerrar muda com ela.")
    if item == "usa_prazo_trimestre":
        if novo:
            return ("a regra do fim do trimestre voltou a valer: deals que chegam ao fim do trimestre "
                    "seguinte saem da lista de vivos e entram em encerrar.")
        return ("a regra do fim do trimestre desligou: deals que venceram pelo fim do trimestre "
                "voltam a aparecer como vivos e podem subir de fila.")
    if item.startswith("p_decide"):
        if guardado is None:
            return "apareceu uma faixa de idade nova, com chance de decidir em 28 dias de " + f"{novo:.3f}."
        if novo is None:
            return "uma faixa de idade sumiu: a janela aprendida agora tem outros limites."
        return f"a chance de decidir em 28 dias da faixa mudou de {guardado:.3f} para {novo:.3f}."
    return f"a carga de referência mudou de {guardado} para {novo} deals."


def _item(nome: str, guardado, novo) -> dict:
    mudou = guardado != novo
    return {
        "item": nome,
        "guardado": guardado,
        "novo": novo,
        "mudou": bool(mudou),
        "mensagem": _mensagem(nome.split("[")[0], guardado, novo) if mudou else None,
    }


def conferir(pasta_dados, guardado: dict, config: dict) -> dict:
    novo = aprendido(pasta_dados, config, pd.Timestamp(guardado["hoje"]))
    itens = [
        _item("ciclo_max", guardado["ciclo_max"], novo["ciclo_max"]),
        _item("usa_prazo_trimestre", guardado["usa_prazo_trimestre"], novo["usa_prazo_trimestre"]),
    ]
    for faixa in sorted(set(guardado["p_decide"]) | set(novo["p_decide"])):
        itens.append(_item(f"p_decide[{faixa}]", guardado["p_decide"].get(faixa), novo["p_decide"].get(faixa)))
    for vendedor in sorted(set(guardado["carga_referencia"]) | set(novo["carga_referencia"])):
        itens.append(_item(f"carga[{vendedor}]", guardado["carga_referencia"].get(vendedor),
                           novo["carga_referencia"].get(vendedor)))
    return {"itens": itens, "mudou": any(i["mudou"] for i in itens)}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Confere se a janela aprendida ainda vale.")
    p.add_argument("--dados", default=RAIZ / "data")
    p.add_argument("--janela", default=RAIZ / "janela.json")
    p.add_argument("--config", default=RAIZ / "config.json")
    a = p.parse_args(argv)
    guardado = json.loads(Path(a.janela).read_text(encoding="utf-8"))
    config = json.loads(Path(a.config).read_text(encoding="utf-8"))
    r = conferir(a.dados, guardado, config)
    if not r["mudou"]:
        print("nada mudou desde o último build")
        return 0
    for i in r["itens"]:
        if i["mudou"]:
            print(f"{i['item']}: {i['mensagem']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
