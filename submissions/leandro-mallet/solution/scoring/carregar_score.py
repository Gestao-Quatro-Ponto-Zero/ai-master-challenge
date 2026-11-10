"""Carrega o arquivo de score no banco, numa transação, pelo papel de carga. Só inserção.

Uso (a partir da pasta solution/):
    python scoring/carregar_score.py scoring/carga/score_2017-12-31.json            # ensaio: faz tudo e desfaz (ROLLBACK)
    python scoring/carregar_score.py scoring/carga/score_2017-12-31.json --aplicar  # grava (COMMIT) se as conferências passarem

Passos: set role system_carga → system_iniciar_contexto_sistema(uuid) → INSERT em score_execucoes e nas demais
score_* → score_ativar_execucao(uuid, id) → conferências → COMMIT ou ROLLBACK.
A senha vem de DATABASE_URL (variável ou .env) e nunca é impressa.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path

import psycopg2
from psycopg2.extras import Json, execute_values

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calcular_score import url_banco  # noqa: E402


def carregar(caminho: Path, aplicar: bool) -> dict:
    bruto = caminho.read_bytes()
    sha = hashlib.sha256(bruto).hexdigest()
    c = json.loads(bruto.decode("utf-8"))
    corr = str(uuid.uuid4())
    con = psycopg2.connect(url_banco())
    con.autocommit = False
    cur = con.cursor()
    try:
        cur.execute("set role system_carga")
        cur.execute("select system_iniciar_contexto_sistema(%s::uuid)", (corr,))
        cur.execute(
            "insert into score_execucoes (reference_date, gerado_em, versao, pesos, parametros, arquivo_sha256, observacao) "
            "values (%s, now(), %s, %s, %s, %s, %s) returning id",
            (c["reference_date"], c["versao"], Json(c["pesos"]), Json(c["parametros"]), sha,
             "Carga inicial do score (decisões 28–40). Dono atual; sem redistribuição nem repasse. "
             "BONUS só pelo histórico; janela de compra vale 0."))
        ex = cur.fetchone()[0]
        execute_values(cur, "insert into score_deals (execucao_id, opportunity_id, vendedor_nome, cohort, fit, heat, bonus, score, "
                            "acao_sugerida, dias_no_pipeline, valor_esperado, marcadores) values %s",
                       [(ex, d["opportunity_id"], d["vendedor_nome"], d["cohort"], d["fit"], d["heat"], d["bonus"], d["score"],
                         d["acao_sugerida"], d["dias_no_pipeline"], d["valor_esperado"], d["marcadores"]) for d in c["deals"]],
                       page_size=1000)
        execute_values(cur, "insert into score_componentes (execucao_id, opportunity_id, grupo, componente, pontos, maximo) values %s",
                       [(ex, d["opportunity_id"], k["grupo"], k["componente"], k["pontos"], k["maximo"])
                        for d in c["deals"] for k in d["componentes"]], page_size=2000)
        execute_values(cur, "insert into score_motivos (execucao_id, opportunity_id, ordem, grupo, texto) values %s",
                       [(ex, d["opportunity_id"], m["ordem"], m["grupo"], m["texto"]) for d in c["deals"] for m in d["motivos"]],
                       page_size=2000)
        execute_values(cur, "insert into score_fit_vendedores (execucao_id, vendedor_nome, cohort, produto_nome, taxa_media_movel, "
                            "casos, fit, janela_inicio, janela_fim) values %s",
                       [(ex, f["vendedor_nome"], f["cohort"], f["produto_nome"], f["taxa_media_movel"], f["casos"], f["fit"],
                         f["janela_inicio"], f["janela_fim"]) for f in c["fit_vendedores"]])
        execute_values(cur, "insert into score_padroes_conta (execucao_id, conta_nome, compras_ganhas, receita_ganha, "
                            "intervalo_tipico_dias, mes_habitual, ultima_compra, proxima_compra_esperada, na_janela, bonus, explicacao) values %s",
                       [(ex, p["conta_nome"], p["compras_ganhas"], p["receita_ganha"], p["intervalo_tipico_dias"], p["mes_habitual"],
                         p["ultima_compra"], p["proxima_compra_esperada"], p["na_janela"], p["bonus"], p["explicacao"])
                        for p in c["padroes_conta"]])
        cur.execute("select score_ativar_execucao(%s::uuid, %s)", (corr, ex))

        # conferências antes do COMMIT
        def um(sql, *a):
            cur.execute(sql, a)
            return cur.fetchone()
        abertos = um("select count(*) from core_deals where estagio in ('Prospecting','Engaging')")[0]
        contagens = {t: um(f"select count(*) from {t} where execucao_id = %s", ex)[0]
                     for t in ["score_deals", "score_componentes", "score_motivos", "score_fit_vendedores", "score_padroes_conta"]}
        faixa = um("select min(score), max(score) from score_deals where execucao_id = %s", ex)
        sem_nota = um("select count(*) from core_deals d where d.estagio in ('Prospecting','Engaging') and not exists "
                      "(select 1 from score_deals s where s.execucao_id = %s and s.opportunity_id = d.opportunity_id)", ex)[0]
        dono_diferente = um("select count(*) from score_deals s join core_deals d using (opportunity_id) "
                            "where s.execucao_id = %s and s.vendedor_nome <> d.vendedor_nome", ex)[0]
        ativa = um("select config_texto('execucao_ativa')")[0]
        esperado = {"score_deals": len(c["deals"]), "score_componentes": sum(len(d["componentes"]) for d in c["deals"]),
                    "score_motivos": sum(len(d["motivos"]) for d in c["deals"]), "score_fit_vendedores": len(c["fit_vendedores"]),
                    "score_padroes_conta": len(c["padroes_conta"])}
        problemas = []
        if contagens["score_deals"] != abertos or sem_nota:
            problemas.append(f"deals com nota ({contagens['score_deals']}) diferente dos abertos ({abertos}); sem nota: {sem_nota}")
        if contagens != esperado:
            problemas.append(f"contagens {contagens} diferentes do arquivo {esperado}")
        if not (0 <= faixa[0] and faixa[1] <= 120):
            problemas.append(f"score fora de 0–120: {faixa}")
        if dono_diferente:
            problemas.append(f"{dono_diferente} deals com dono diferente do atual")
        if str(ativa) != str(ex):
            problemas.append(f"execução ativa {ativa} diferente de {ex}")
        resultado = {"execucao_id": ex, "correlation_id": corr, "sha256": sha, "abertos": abertos, "contagens": contagens,
                     "score_min_max": list(faixa), "dono_diferente": dono_diferente, "execucao_ativa": ativa,
                     "problemas": problemas}
        if problemas or not aplicar:
            con.rollback()
            resultado["gravado"] = False
        else:
            con.commit()
            resultado["gravado"] = True
        return resultado
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivo")
    ap.add_argument("--aplicar", action="store_true", help="gravar (sem isto, faz ROLLBACK)")
    a = ap.parse_args()
    print(json.dumps(carregar(Path(a.arquivo), a.aplicar), ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
