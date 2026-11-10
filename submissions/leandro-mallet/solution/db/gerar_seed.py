"""Gera os dados iniciais do lote 1 a partir de data/clean/ (rodar depois de data/clean.py).

Uso:  python solution/db/gerar_seed.py

Escreve:
  migrations/0006_config_inicial.sql  usuários "sistema" (1) e "admin" (2) e os parâmetros do CRM;
  seed/seed_dataset.sql               o dataset limpo: time, produtos, contas, usuários do time e deals.

O seed roda DEPOIS das migrations 0001–0006, numa transação só, assinado pelo usuário "sistema"
(system_iniciar_contexto_sistema), e passa pela auditoria. Rodar de novo não duplica nada
(on conflict do nothing). Ids dos usuários fixos: 1 sistema, 2 admin, vendedores (A–Z) e depois managers (A–Z).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLEAN = HERE.parent / "data" / "clean"
CONFIG_SQL = HERE / "migrations" / "0006_config_inicial.sql"
SEED_SQL = HERE / "seed" / "seed_dataset.sql"
CORR_CONFIG = "00000000-0000-4000-8000-000000000006"
CORR_SEED = "00000000-0000-4000-8000-00000000d5e7"
LOTE_INSERT = 500

PARAMETROS = [
    ("modo_demonstracao", True, "Relógio do CRM: com true, 'hoje' é a data de referência (P6)."),
    ("data_referencia", "2017-12-31", "Último dia com registro no dataset; 'hoje' no modo demonstração."),
    ("fuso_horario", "America/Sao_Paulo", "Fuso do dia real (lista de prioridades e prazos)."),
    ("execucao_ativa", None, "Execução de score em uso; definida por score_ativar_execucao."),
    ("pesos_score", {"fit": 0.70, "heat": 0.30}, "SCORE = 0,70 × FIT + 0,30 × HEAT (+ bonus, lote 2); a fórmula fica no score."),
    ("cohort_dimensoes", ["produto"], "Dimensões da chave de cohort usada no roteamento; definidas pelo score."),
    ("roteamento", {"teto_abertos": 200, "minimo_casos": 10},
     "Lead novo vai ao vendedor de maior FIT no cohort, abaixo do teto de abertos e com o mínimo de casos."),
    ("faixas_nota", {"alta": 70, "media": 40}, "Cortes das faixas da nota (barra do cartão)."),
    ("icone_cortes", {"dias_min_quente": 15, "dias_max_quente": 106, "dias_max_risco": 138, "preco_min_quente": 3000},
     "Cortes dos ícones super hot, em risco e esfriou (ESPEC-TELAS 2.4)."),
    ("dias_sem_contato_risco", 14, "Dias sem contato registrado no CRM que também marcam risco."),
    ("acoes_contato", ["liguei", "requalifiquei"], "Ações que contam como contato (P5)."),
    ("usar_abertura_como_primeiro_contato", False, "P5: usar a abertura como primeiro contato dos deals em negociação."),
    ("motivo_perda_obrigatorio", False, "P14: exigir motivo ao perder ou descartar."),
    ("limite_escritas_por_minuto", 30, "Limite de escritas por usuário por minuto (BE-06)."),
    ("limite_lote", 500, "Máximo de deals por ação em lote."),
    ("limite_linhas_importacao", 10000, "Máximo de linhas por arquivo importado."),
    ("max_tags_por_deal", 10, "Máximo de tags ativas por deal."),
    ("segundos_desfazer", 60, "Prazo do 'Desfazer' no servidor (a tela mostra 10 s)."),
    ("horas_desfazer_lote", 24, "Prazo do 'Desfazer este lote'."),
    ("prioridades_visiveis", 5, "Itens visíveis no bloco Prioridades do dia."),
    ("meta_prioridades_dia", 10, "Meta diária de itens nas Prioridades do dia."),
    ("dias_pulado_alerta", 3, "Dias seguidos pulado até perguntar 'Requalificar ou encerrar?'."),
    ("janela_painel_dias", 30, "Janela dos cartões do Painel."),
    ("papeis_importacao", ["manager", "admin"], "Quem importa CSV."),
    ("papeis_criar_tag", ["manager", "admin"], "Quem cria e arquiva tags (P7)."),
    ("papeis_lote", ["vendedor", "manager", "admin"], "Quem usa ações em lote (P8)."),
    ("papeis_reabrir", ["manager", "admin"], "Quem reabre deal encerrado (P10)."),
]


def q(v) -> str:
    if v is None or v == "":
        return "null"
    return "'" + str(v).replace("'", "''") + "'"


def inteiro(v) -> str:
    return "null" if v in (None, "") else str(int(round(float(v))))


def ler(nome: str) -> list[dict]:
    with open(CLEAN / nome, newline="", encoding="utf-8") as f:
        return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def inserts(tabela: str, colunas: str, linhas: list[str], conflito: str = "on conflict do nothing") -> list[str]:
    out = []
    for i in range(0, len(linhas), LOTE_INSERT):
        parte = linhas[i:i + LOTE_INSERT]
        out.append(f"insert into {tabela} ({colunas}) values\n" + ",\n".join(parte) + f"\n{conflito};")
    return out


def gerar_config() -> None:
    L = [
        "-- 0006_config_inicial.sql  [LOTE 1]",
        "-- Usuários 'sistema' (1) e 'admin' (2) e os parâmetros do CRM. Assinado pelo usuário 'sistema' (auditado).",
        "-- GERADO por db/gerar_seed.py. Não editar à mão. Os usuários do time vêm do seed (seed/seed_dataset.sql).",
        "",
        f"select set_config('app.usuario_id', '1', false), set_config('app.correlation_id', '{CORR_CONFIG}', false),",
        "       set_config('app.lote_id', '', false);",
        "",
        "insert into config_usuarios (id, papel, nome_exibicao) values",
        "  (1, 'sistema', 'Sistema'),",
        "  (2, 'admin', 'Admin')",
        "on conflict do nothing;",
        "select setval(pg_get_serial_sequence('config_usuarios', 'id'), greatest(2, (select max(id) from config_usuarios)));",
        "",
        "insert into config_parametros (chave, valor, descricao) values",
        ",\n".join(f"  ({q(c)}, {q(json.dumps(v, ensure_ascii=False))}::jsonb, {q(d)})" for c, v, d in PARAMETROS),
        "on conflict do nothing;",
        "",
        "select set_config('app.usuario_id', '', false), set_config('app.correlation_id', '', false);",
    ]
    CONFIG_SQL.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


def gerar_seed() -> dict:
    time = ler("sales_teams.csv")
    produtos = ler("products.csv")
    contas = ler("accounts.csv")
    deals = ler("sales_pipeline.csv")

    escritorios = sorted({r["regional_office"] for r in time})
    managers = sorted({(r["manager"], r["regional_office"]) for r in time})
    vendedores = sorted((r["sales_agent"], r["manager"]) for r in time)
    nomes_contas = {c["account"] for c in contas}

    # empresa-mãe antes da filha (a FK é para a própria tabela)
    ordem, feitas = [], set()
    pendentes = sorted(contas, key=lambda c: c["account"])
    while pendentes:
        prox = [c for c in pendentes if not c["subsidiary_of"] or c["subsidiary_of"] in feitas
                or c["subsidiary_of"] not in nomes_contas]
        assert prox, "ciclo em subsidiary_of"
        ordem += prox
        feitas |= {c["account"] for c in prox}
        pendentes = [c for c in pendentes if c["account"] not in feitas]

    usuarios = [(3 + i, "vendedor", v, v, None) for i, (v, _) in enumerate(vendedores)]
    usuarios += [(3 + len(vendedores) + i, "manager", m, None, m) for i, (m, _) in enumerate(managers)]

    def nome_deal(d):
        return f"{d['account'] or 'Sem empresa'} · {d['product']}"

    def valor(d):
        if d["deal_stage"] == "Won":
            return inteiro(d["close_value"])
        if d["deal_stage"] == "Lost":
            return "0"
        return "null"

    L = [
        "-- seed_dataset.sql  [LOTE 1 — rodar DEPOIS das migrations 0001 a 0006]",
        "-- Dataset limpo (data/clean/): time, produtos, contas, usuários do time e deals.",
        "-- GERADO por db/gerar_seed.py. Não editar à mão.",
        f"-- {len(escritorios)} escritórios · {len(managers)} managers · {len(vendedores)} vendedores · {len(produtos)} produtos"
        f" · {len(contas)} contas · {len(usuarios)} usuários do time · {len(deals)} deals.",
        "-- Uma transação só, assinada pelo usuário 'sistema' (a auditoria exige usuário e correlation_id).",
        "-- Rodar de novo não duplica nem sobrescreve nada (on conflict do nothing).",
        "-- Regras da carga: nome do deal = 'Empresa · Produto' (ou 'Sem empresa · Produto'); data_abertura = engage_date;",
        "-- close_value inteiro (Lost = 0); porte = tercil de funcionários; empresa independente fica sem empresa-mãe.",
        "",
        "begin;",
        f"select system_iniciar_contexto_sistema('{CORR_SEED}'::uuid);",
        "",
    ]
    L += inserts("core_escritorios", "nome", [f"  ({q(e)})" for e in escritorios])
    L += inserts("core_managers", "nome, escritorio_nome", [f"  ({q(m)}, {q(e)})" for m, e in managers])
    L += inserts("core_vendedores", "nome, manager_nome", [f"  ({q(v)}, {q(m)})" for v, m in vendedores])
    L += inserts("core_produtos", "nome, serie, preco",
                 [f"  ({q(p['product'])}, {q(p['series'])}, {inteiro(p['sales_price'])})"
                  for p in sorted(produtos, key=lambda p: p["product"])])
    L += inserts("core_contas",
                 "nome, setor, ano_fundacao, receita_milhoes, funcionarios, porte, pais, empresa_mae_nome",
                 [f"  ({q(c['account'])}, {q(c['sector'])}, {inteiro(c['year_established'])}, "
                  f"{c['revenue'] or 'null'}, {inteiro(c['employees'])}, {q(c['employees_band'])}, "
                  f"{q(c['office_location'])}, {q(c['subsidiary_of'])})" for c in ordem])
    L += inserts("config_usuarios", "id, papel, nome_exibicao, vendedor_nome, manager_nome",
                 [f"  ({i}, {q(p)}, {q(n)}, {q(v)}, {q(m)})" for i, p, n, v, m in usuarios])
    L.append("select setval(pg_get_serial_sequence('config_usuarios', 'id'), (select max(id) from config_usuarios));")
    L += inserts("core_deals",
                 "opportunity_id, nome, vendedor_nome, produto_nome, conta_nome, estagio, data_abertura, close_date, close_value",
                 [f"  ({q(d['opportunity_id'])}, {q(nome_deal(d))}, {q(d['sales_agent'])}, {q(d['product'])}, "
                  f"{q(d['account'])}, {q(d['deal_stage'])}, {q(d['engage_date'])}, {q(d['close_date'])}, {valor(d)})"
                  for d in sorted(deals, key=lambda d: d["opportunity_id"])])
    L += ["", "commit;"]
    SEED_SQL.parent.mkdir(exist_ok=True)
    SEED_SQL.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    return {"escritorios": len(escritorios), "managers": len(managers), "vendedores": len(vendedores),
            "produtos": len(produtos), "contas": len(contas), "usuarios_time": len(usuarios), "deals": len(deals)}


if __name__ == "__main__":
    gerar_config()
    print(CONFIG_SQL.name, f"{len(PARAMETROS)} parâmetros")
    print(SEED_SQL.name, gerar_seed())
