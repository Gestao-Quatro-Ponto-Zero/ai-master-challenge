"""Gera o contrato JSON que a tela lê: deals, vendedores, time, qualidade e hash."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from motor.aprender import carga_referencia, tabela_destino
from motor.carregar import carregar, recortar
from motor.explicar import explicar, resumo_vendedor
from motor.janela import aprender_janela
from motor.pontuar import pontuar

RAIZ = Path(__file__).parent
FILAS = ("fechar", "preparar", "iniciar", "encerrar")


def _json(v):
    if v is None or v is pd.NaT or v is pd.NA:
        return None
    if isinstance(v, pd.Timestamp):
        return v.date().isoformat()
    if isinstance(v, np.generic):
        v = v.item()
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def _registro(d: dict) -> dict:
    return {k: _json(v) for k, v in d.items()}


def _agregar(s: pd.DataFrame, coluna: str) -> dict:
    out = {}
    for nome, g in s.groupby(coluna):
        out[nome] = {
            "abertos": int(len(g)),
            "valor_aberto": float(g.valor_tabela.sum()),
            "valor_vivo": float(g.valor_tabela[g.estado == "vivo"].sum()),
            "valor_vencido": float(g.valor_tabela[g.estado == "vencido"].sum()),
        }
    return out


def construir(pasta_dados, config: dict, saida, hoje=None) -> dict:
    if hoje is None:
        raise ValueError("hoje é obrigatório: o motor não inventa data")
    hoje = pd.Timestamp(hoje)
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)

    dados = carregar(pasta_dados)
    r = recortar(dados, hoje)
    janela = aprender_janela(r, config)
    tabela = tabela_destino(r, janela, config, hoje)
    carga = carga_referencia(r, hoje)
    s = pontuar(r, janela, tabela, carga, config, hoje)

    carteiras = {nome: g for nome, g in s.groupby("vendedor")}
    deals = []
    for _, linha in s.iterrows():
        ex = explicar(linha, janela, tabela, carteiras[linha.vendedor])
        d = _registro(linha.to_dict())
        d["cartoes"] = ex["cartoes"]
        d["nao_sabe"] = ex["nao_sabe"]
        deals.append(d)

    com_deal = set(r.pipeline.sales_agent)
    vendedores = []
    for _, t in dados.times.iterrows():
        nome = t.sales_agent
        sub = carteiras.get(nome, s.iloc[0:0])
        rv = resumo_vendedor(nome, sub, carga)
        vendedores.append({
            "vendedor": nome,
            "gerente": t.manager,
            "regiao": t.regional_office,
            "tem_deal": nome in com_deal,
            "vivos": rv["vivos"],
            "por_fila": {f: rv["por_fila"][f]["n"] for f in FILAS},
            "valor_por_fila": {f: rv["por_fila"][f]["valor"] for f in FILAS},
            "carga_referencia": rv["carga_referencia"],
            "frase_vazio": rv["frase_vazio"],
        })

    valor = s.valor_tabela
    total = float(valor.sum())
    venc = float(valor[s.estado == "vencido"].sum())
    time = {
        "total_abertos": int(len(s)),
        "valor_aberto": total,
        "valor_vivo": float(valor[s.estado == "vivo"].sum()),
        "valor_vencido": venc,
        "pct_vencido": venc / total,
        "ve_trimestre": float(s.ve_trimestre.sum()),
        "por_regiao": _agregar(s, "regiao"),
        "por_gerente": _agregar(s, "gerente"),
    }

    t_out = tabela.copy()
    t_out.index.name = "faixa"
    semana = int((hoje - pd.Timestamp(hoje.year, 3 * ((hoje.month - 1) // 3) + 1, 1)).days // 7 + 1)

    scored = {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "hoje": hoje.date().isoformat(),
        "semana_do_trimestre": semana,
        "config": config,
        "janela": asdict(janela),
        "tabela_destino": [_registro(x) for x in t_out.reset_index().to_dict("records")],
        "deals": deals,
        "vendedores": vendedores,
        "time": time,
    }

    sem_marca = {k: v for k, v in scored.items() if k != "gerado_em"}
    corpo = json.dumps(sem_marca, ensure_ascii=False, indent=1, sort_keys=True)
    h = hashlib.sha256(corpo.encode("utf-8")).hexdigest()

    qualidade = dict(dados.qualidade)
    qualidade["vendedores_sem_deal"] = sorted(set(dados.times.sales_agent) - com_deal)

    (saida / "scored.json").write_text(
        json.dumps(scored, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    (saida / "qualidade.json").write_text(
        json.dumps(qualidade, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    (saida / "hash.txt").write_text(h + "\n", encoding="utf-8")

    return {"hash": h, "saida": str(saida)}


def main():
    p = argparse.ArgumentParser(description="Gera app/data a partir de data/.")
    p.add_argument("--hoje", help="AAAA-MM-DD; sem ele usa config.json")
    p.add_argument("--saida", default=RAIZ / "app" / "data")
    a = p.parse_args()
    config = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))
    hoje = a.hoje or config["hoje"]
    if hoje is None:
        p.error("passe --hoje AAAA-MM-DD (config.hoje está null)")
    out = construir(RAIZ / "data", config, a.saida, hoje)
    print("hash", out["hash"], "| saida", out["saida"])


if __name__ == "__main__":
    main()
