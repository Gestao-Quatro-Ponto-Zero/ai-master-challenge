"""Grava a redistribuição de domingo no banco, pelo papel de carga, uma chamada de core_repassar_deal por troca.

Uso (a partir da pasta solution/):
    python scoring/aplicar_redistribuicao.py            # ensaio: refaz o plano com o estado de agora, aplica e desfaz (ROLLBACK)
    python scoring/aplicar_redistribuicao.py --aplicar  # grava (COMMIT) se as conferências passarem

O plano é refeito na hora (redistribuir.py). Só entram leads sem contato registrado; quem ganhou contato fica com o dono.
Nada de UPDATE direto: a troca de dono, a auditoria e a linha do tempo saem da função do banco.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calcular_score as cs  # noqa: E402
import redistribuir  # noqa: E402
import regra  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()
    d = regra.preparar(*cs.ler_banco())
    plano = redistribuir.planejar(d, cs.REFERENCIA)
    trocas = [t for t in plano["trocas"] if t["muda"]]
    corr = str(uuid.uuid4())
    con = psycopg2.connect(cs.url_banco())
    cur = con.cursor()
    try:
        cur.execute("set role system_carga")
        cur.execute("select system_iniciar_contexto_sistema(%s::uuid)", (corr,))
        cur.execute("select score_execucao_ativa()")
        execucao = cur.fetchone()[0]
        cur.execute("select count(*) from core_deals")
        total_antes = cur.fetchone()[0]
        cur.execute("select count(*) from acao_reatribuicoes where origem = 'redistribuicao'")
        reatrib_antes = cur.fetchone()[0]
        recusadas = []
        for t in trocas:
            cur.execute("savepoint s")
            try:
                cur.execute("select core_repassar_deal(%s::uuid, %s, %s, 'redistribuicao', %s, %s::smallint, %s::smallint, null, %s)",
                            (corr, t["opportunity_id"], t["para"], execucao, int(round(t["fit_dono"])), int(round(t["fit_novo"])),
                             "sem data de abertura"))
                cur.execute("release savepoint s")
            except psycopg2.Error as e:
                cur.execute("rollback to savepoint s")
                recusadas.append({"opportunity_id": t["opportunity_id"], "erro": (e.pgerror or str(e)).strip().splitlines()[0]})
        cur.execute("select count(*) from core_deals")
        total = cur.fetchone()[0]
        cur.execute("select count(*) from acao_reatribuicoes where origem = 'redistribuicao'")
        reatrib = cur.fetchone()[0] - reatrib_antes
        ok_ids = [t["opportunity_id"] for t in trocas if t["opportunity_id"] not in {r["opportunity_id"] for r in recusadas}]
        esperado = {t["opportunity_id"]: t["para"] for t in trocas}
        cur.execute("select opportunity_id, vendedor_nome from core_deals where opportunity_id = any(%s)", (ok_ids,))
        donos_errados = [o for o, v in cur.fetchall() if esperado[o] != v]
        problemas = []
        if total != total_antes:
            problemas.append(f"total de deals mudou: {total_antes} -> {total}")
        if reatrib != len(ok_ids):
            problemas.append(f"reatribuições registradas {reatrib} != trocas {len(ok_ids)}")
        if donos_errados:
            problemas.append(f"{len(donos_errados)} deals sem o dono esperado")
        res = {"correlation_id": corr, "execucao_ativa": execucao, "planejadas": len(trocas), "gravadas": len(ok_ids),
               "recusadas": recusadas, "deals_total": total, "reatribuicoes_novas": reatrib, "problemas": problemas,
               "limite": plano["limite"], "sem_contato": len(plano["trocas"])}
        if problemas or not a.aplicar:
            con.rollback()
            res["gravado"] = False
        else:
            con.commit()
            res["gravado"] = True
        print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
