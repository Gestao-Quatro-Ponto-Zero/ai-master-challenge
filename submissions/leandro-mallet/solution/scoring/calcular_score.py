"""Calcula o lead score dos deals abertos e grava o arquivo de carga.

Uso (a partir da pasta solution/):
    python scoring/calcular_score.py            # lê o banco (DATABASE_URL), só leitura
    python scoring/calcular_score.py --csv      # lê data/clean/ (dataset, sem as mudanças feitas no CRM)

Saída: scoring/carga/score_<data>.json (o sha256 desse arquivo vai para score_execucoes.arquivo_sha256).
A regra está em scoring/regra.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import pandas as pd

import regra

AQUI = Path(__file__).resolve().parent
SOLUTION = AQUI.parent
REFERENCIA = pd.Timestamp("2017-12-31")


def ler_csv() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    clean = SOLUTION / "data" / "clean"
    d = pd.read_csv(clean / "sales_pipeline.csv")
    deals = pd.DataFrame({
        "opportunity_id": d["opportunity_id"], "vendedor_nome": d["sales_agent"], "produto_nome": d["product"],
        "conta_nome": d["account"], "estagio": d["deal_stage"], "data_abertura": d["engage_date"],
        "close_date": d["close_date"], "close_value": d["close_value"], "ultimo_contato_em": None, "criado_em": None,
    })
    a = pd.read_csv(clean / "accounts.csv")
    contas = pd.DataFrame({"nome": a["account"], "setor": a["sector"], "receita_milhoes": a["revenue"],
                           "funcionarios": a["employees"], "pais": a["office_location"]})
    p = pd.read_csv(clean / "products.csv")
    produtos = pd.DataFrame({"nome": p["product"], "serie": p["series"], "preco": p["sales_price"]})
    return deals, contas, produtos


def url_banco() -> str:
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    for pasta in [SOLUTION, *SOLUTION.parents]:
        env = pasta / ".env"
        if env.exists():
            for linha in env.read_text(encoding="utf-8").splitlines():
                if linha.startswith("DATABASE_URL="):
                    return linha.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL não encontrada (variável de ambiente ou .env).")


def ler_banco() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    import psycopg2
    con = psycopg2.connect(url_banco())
    con.set_session(readonly=True)
    try:
        def q(sql):
            return pd.read_sql_query(sql, con)
        deals = q("select opportunity_id, vendedor_nome, produto_nome, conta_nome, estagio, data_abertura, "
                  "close_date, close_value, ultimo_contato_em, criado_em from core_deals")
        contas = q("select nome, setor, receita_milhoes, funcionarios, pais from core_contas")
        produtos = q("select nome, serie, preco from core_produtos")
    finally:
        con.close()
    return deals, contas, produtos


def montar_carga(res: dict, produtos: pd.DataFrame, fonte: str) -> dict:
    deals = res["deals"].sort_values("opportunity_id")
    cel, pad = res["celulas"], res["padroes"]
    ini, fim = cel.janela
    carga = {
        "versao": regra.VERSAO,
        "reference_date": str(REFERENCIA.date()),
        "fonte": fonte,
        "pesos": regra.PESOS,
        "parametros": {
            "fit": {"janela_inicio": str(ini.date()), "janela_fim": str(fim.date()), "janela_meses": regra.JANELA_MESES,
                    "encolhimento": regra.ENCOLHIMENTO, "minimo_casos": regra.MINIMO_CASOS,
                    "corte_destaque_pontos": regra.CORTE_DESTAQUE * 100, "caracteristicas": list(regra.DIMENSOES),
                    "sem_empresa": "produto e série", "recalculo": "todo domingo"},
            "heat": {"faixas": [{"ate_dias": a, "pontos": p} for a, p, _ in regra.FAIXAS_HEAT],
                     "prospecting_sem_data": regra.HEAT_SEM_DATA,
                     "fator_contato": [{"ate_dias": a, "fator": f} for a, f in regra.FATOR_CONTATO],
                     "fator_sem_historico": 1.0},
            "bonus": {"historico_tercos": list(regra.BONUS_HISTORICO),
                      "cortes_receita": [round(x, 2) for x in pad.attrs["cortes_receita"]],
                      "janela_pontos": regra.BONUS_JANELA, "janela_recorte": regra.JANELA_RECORTE,
                      "janela_teste": "permutação contra o calendário geral, Bonferroni para o número de empresas",
                      "janela_empresas_aprovadas": int(pad["na_janela"].sum())},
            "acao": {"requalificar_acima_dias": regra.RISCO_ESFRIAR[1], "desistir_acima_dias": regra.DESISTIR_ACIMA},
            "marcadores": {"risco_esfriar": list(regra.RISCO_ESFRIAR), "esfriou_acima": regra.RISCO_ESFRIAR[1],
                           "atendimento_atrasado": f"lead do CRM sem contato há mais de 1 dia com FIT >= {regra.FIT_FURAR_FILA}"},
            "cohort": "produto=<produto> (config cohort_dimensoes)",
        },
        "deals": [], "fit_vendedores": [], "padroes_conta": [],
    }
    for _, l in deals.iterrows():
        ld = l.to_dict()
        carga["deals"].append({
            "opportunity_id": l["opportunity_id"], "vendedor_nome": l["vendedor_nome"], "cohort": l["cohort"],
            "fit": int(round(l["fit"])), "heat": int(round(l["heat"])), "bonus": int(l["bonus"]),
            "score": int(round(l["nota"])), "nota_exata": round(float(l["nota"]), 4),
            "acao_sugerida": l["acao_sugerida"], "dias_no_pipeline": None if pd.isna(l["dias"]) else int(l["dias"]),
            "valor_esperado": int(l["valor_esperado"]), "marcadores": list(l["marcadores"]),
            "componentes": regra.componentes(ld),
            "motivos": [{"ordem": i + 1, "grupo": g, "texto": t} for i, (g, t) in enumerate(l["motivos"])],
        })
    for _, f in regra.fit_vendedores(cel, produtos).iterrows():
        carga["fit_vendedores"].append({**f.to_dict(), "casos": int(f["casos"]), "fit": int(f["fit"]),
                                        "janela_inicio": str(ini.date()), "janela_fim": str(fim.date())})
    for nome, p in pad.sort_index().iterrows():
        carga["padroes_conta"].append({
            "conta_nome": nome, "compras_ganhas": int(p["compras_ganhas"]), "receita_ganha": int(p["receita_ganha"]),
            "intervalo_tipico_dias": None, "mes_habitual": None, "ultima_compra": str(p["ultima_compra"].date()),
            "proxima_compra_esperada": None, "na_janela": bool(p["na_janela"]), "bonus": int(p["bonus"]),
            "explicacao": regra.explicacao_conta(p),
        })
    return carga


def resumo(res: dict) -> dict:
    d = res["deals"]
    t5 = regra.top5(d)
    return {
        "deals": len(d), "vendedores": int(d["vendedor_nome"].nunique()),
        "nota": d["nota"].describe().round(1).to_dict(), "fit": d["fit"].describe().round(1).to_dict(),
        "heat": d["heat"].value_counts().sort_index().to_dict(), "bonus": d["bonus"].value_counts().sort_index().to_dict(),
        "acao": d["acao_sugerida"].value_counts().to_dict(),
        "marcadores": pd.Series([m for ms in d["marcadores"] for m in ms]).value_counts().to_dict(),
        "fit_75_ou_mais": int((d["fit"] >= 75).sum()),
        "top5": {"deals": len(t5), "ativos_pct": round(100 * t5["ativo"].mean(), 1),
                 "com_empresa_pct": round(100 * t5["conta_nome"].notna().mean(), 1),
                 "prospecting_pct": round(100 * (t5["estagio"] == "Prospecting").mean(), 1),
                 "dias_181_ou_mais": int((t5["dias"] >= 181).sum())},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", action="store_true", help="usar data/clean em vez do banco")
    ap.add_argument("--salvar-entrada", metavar="ARQ", help="grava as linhas lidas (deals, contas, produtos) em JSON")
    ap.add_argument("--entrada", metavar="ARQ", help="lê as linhas de um JSON gravado por --salvar-entrada")
    args = ap.parse_args()
    if args.entrada:
        e = json.loads(Path(args.entrada).read_text(encoding="utf-8"))
        deals, contas, produtos = (pd.DataFrame(e[k]) for k in ("deals", "contas", "produtos"))
    else:
        deals, contas, produtos = ler_csv() if args.csv else ler_banco()
    if args.salvar_entrada:
        def linhas(df):
            out = df.copy()
            for c in out.columns:
                if pd.api.types.is_datetime64_any_dtype(out[c]):
                    out[c] = out[c].map(lambda x: None if pd.isna(x) else x.isoformat())
                elif out[c].dtype == object:
                    out[c] = out[c].map(lambda x: None if x is None or (isinstance(x, float) and pd.isna(x)) else
                                        (x.isoformat() if hasattr(x, "isoformat") else (float(x) if hasattr(x, "as_tuple") else x)))
            return json.loads(out.to_json(orient="records", force_ascii=False))
        Path(args.salvar_entrada).write_text(json.dumps({"deals": linhas(deals), "contas": linhas(contas), "produtos": linhas(produtos)},
                                                        ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    d = regra.preparar(deals, contas, produtos)
    res = regra.calcular(d, REFERENCIA)
    carga = montar_carga(res, produtos, "csv" if args.csv else "banco")
    saida = AQUI / "carga" / f"score_{REFERENCIA.date()}{'_csv' if args.csv else ''}.json"
    saida.parent.mkdir(exist_ok=True)
    texto = json.dumps(carga, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    saida.write_text(texto, encoding="utf-8", newline="\n")
    sha = hashlib.sha256(saida.read_bytes()).hexdigest()
    print(json.dumps({"arquivo": str(saida.relative_to(SOLUTION)), "sha256": sha, **resumo(res)},
                     ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
