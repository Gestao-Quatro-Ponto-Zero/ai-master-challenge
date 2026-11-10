"""Gera migrations/0009_dados_iniciais.sql a partir de data/clean/sales_teams.csv.

Rodar depois de data/clean.py:  python solution/db/gerar_dados_iniciais.py
O time (escritórios, managers e vendedores) e config_usuarios saem do dataset, sem digitação manual.
Os ids de config_usuarios são fixos e determinísticos (1 sistema, 2 admin, managers e vendedores em
ordem alfabética), para o modo reserva do app usar os mesmos ids.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEAMS = HERE.parent / "data" / "clean" / "sales_teams.csv"
OUT = HERE / "migrations" / "0009_dados_iniciais.sql"
CORRELATION = "00000000-0000-4000-8000-000000000009"

PARAMETROS = [
    ("data_referencia", "2017-12-31", "Relógio do CRM em modo demonstração (P6). null = data real."),
    ("execucao_ativa", None, "Id da score_execucoes em uso. null até a primeira carga do score."),
    ("acoes_desde", None, "Data de corte para esconder ações antigas da demonstração (reset sem DELETE)."),
    ("score_pesos", {"fit": 0.70, "heat": 0.30}, "Pesos da nota (informativo; a execução grava os pesos usados)."),
    ("faixas_nota", {"alta_min": 70, "media_min": 40}, "Faixas da barra da nota."),
    ("icone_cortes", {"super_hot_dias_min": 15, "super_hot_dias_max": 106, "super_hot_preco_min": 3000,
                      "risco_dias_min": 107, "risco_dias_max": 138, "esfriou_dias_apos": 138},
     "Cortes dos ícones (ESPEC 2.4, P13), medidos nos dados."),
    ("dias_sem_contato_risco", 14, "Dias sem contato que contam como risco quando risco_por_contato_ativo = true."),
    ("risco_por_contato_ativo", False, "Liga o risco por falta de contato (depois que o CRM tiver uso)."),
    ("acoes_contato", ["liguei", "requalifiquei"], "Ações que contam como contato (P5)."),
    ("motivo_perda_obrigatorio", True, "Pede o motivo ao perder ou descartar (P14)."),
    ("limite_lote", 500, "Máximo de deals por lote."),
    ("lote_desfazer_horas", 24, "Prazo para desfazer um lote."),
    ("desfazer_segundos", 10, "Prazo do Desfazer de uma mudança no deal."),
    ("max_tags_por_deal", 10, "Tags ativas por deal."),
    ("tag_cores", ["marinho", "dourado", "dourado-medio", "dourado-claro", "bronze", "bronze-escuro"],
     "Tokens de cor aceitos nas tags (FE-03). Conferir com o tema."),
    ("prioridades_visiveis", 5, "Itens visíveis nas Prioridades do dia."),
    ("meta_prioridades_dia", 10, "Meta diária de marcações."),
    ("prioridades_fila_max", 50, "Tamanho máximo da fila do dia."),
    ("dias_pulado_alerta", 3, "Dias seguidos pulado até o alerta de requalificar."),
    ("limite_por_minuto", 60, "Pedidos de escrita por usuário por minuto."),
    ("importacao_max_linhas", 10000, "Linhas por arquivo CSV."),
    ("importacao_grafias", {"GTXPro": "GTX Pro"}, "Grafias conhecidas corrigidas na importação (igual à limpeza)."),
    ("roteamento_min_casos", 10, "Mínimo de deals do vendedor no cohort, na janela de 3 meses, para receber lead pelo FIT."),
    ("roteamento_teto_abertos", 200, "Teto de deals abertos por vendedor para receber lead novo."),
]

MOTIVOS = [
    ("preco", "Preço", False, 1, True),
    ("concorrente", "Concorrente", False, 2, True),
    ("sem_orcamento", "Sem orçamento", False, 3, True),
    ("sem_resposta", "Sem resposta", False, 4, True),
    ("outro", "Outro", True, 5, True),
    ("cadastro_desfeito", "Cadastro desfeito", False, 90, True),
    ("importacao_desfeita", "Importação desfeita", False, 91, True),
]


def q(v) -> str:
    """Literal SQL seguro (aspas simples dobradas)."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def main() -> None:
    with TEAMS.open(encoding="utf-8", newline="") as f:
        team = [{k: v.strip() for k, v in r.items()} for r in csv.DictReader(f)]
    escritorios = sorted({r["regional_office"] for r in team})
    managers = sorted({(r["manager"], r["regional_office"]) for r in team})
    vendedores = sorted((r["sales_agent"], r["manager"]) for r in team)
    assert len({m for m, _ in managers}) == len(managers), "manager em dois escritórios"

    usuarios = [(1, "sistema", "Sistema (cargas e rodadas do score)", None, None),
                (2, "admin", "Administrador", None, None)]
    uid = 3
    for m, _ in managers:
        usuarios.append((uid, "manager", m, None, m)); uid += 1
    for v, _ in vendedores:
        usuarios.append((uid, "vendedor", v, v, None)); uid += 1

    L = []
    L.append("-- 0009_dados_iniciais: parâmetros, motivos de perda, time do dataset e config_usuarios.")
    L.append("-- GERADO por db/gerar_dados_iniciais.py a partir de data/clean/sales_teams.csv. Não editar à mão.")
    L.append(f"-- {len(escritorios)} escritórios, {len(managers)} managers, {len(vendedores)} vendedores; "
             f"{len(usuarios)} usuários (1 sistema, 1 admin, {len(managers)} managers, {len(vendedores)} vendedores).")
    L.append("-- Idempotente (on conflict do nothing). Assinado pelo usuário sistema (id 1) para a auditoria.")
    L.append("-- Contas, produtos, deals e notas vêm da carga em Python (on conflict do nothing), fora das migrations.")
    L.append("")
    L.append(f"select set_config('app.usuario_id', '1', false);")
    L.append(f"select set_config('app.correlation_id', '{CORRELATION}', false);")
    L.append("select set_config('app.lote_id', '', false);")
    L.append("")
    L.append("-- usuários sem vínculo com o time primeiro (a auditoria precisa do usuário sistema)")
    L.append("insert into config_usuarios (id, papel, nome_exibicao, vendedor_nome, manager_nome) overriding system value values")
    L.append(",\n".join(f"  ({i}, {q(p)}, {q(n)}, {q(v)}, {q(m)})" for i, p, n, v, m in usuarios[:2]))
    L.append("on conflict (id) do nothing;")
    L.append("")
    L.append("insert into core_escritorios (nome) values")
    L.append(",\n".join(f"  ({q(e)})" for e in escritorios))
    L.append("on conflict (nome) do nothing;")
    L.append("")
    L.append("insert into core_managers (nome, escritorio_nome) values")
    L.append(",\n".join(f"  ({q(m)}, {q(e)})" for m, e in managers))
    L.append("on conflict (nome) do nothing;")
    L.append("")
    L.append("insert into core_vendedores (nome, manager_nome) values")
    L.append(",\n".join(f"  ({q(v)}, {q(m)})" for v, m in vendedores))
    L.append("on conflict (nome) do nothing;")
    L.append("")
    L.append("insert into config_usuarios (id, papel, nome_exibicao, vendedor_nome, manager_nome) overriding system value values")
    L.append(",\n".join(f"  ({i}, {q(p)}, {q(n)}, {q(v)}, {q(m)})" for i, p, n, v, m in usuarios[2:]))
    L.append("on conflict (id) do nothing;")
    L.append("select setval(pg_get_serial_sequence('config_usuarios', 'id'), (select max(id) from config_usuarios));")
    L.append("")
    L.append("insert into config_motivos_perda (codigo, rotulo, exige_detalhe, ordem, ativo) values")
    L.append(",\n".join(f"  ({q(c)}, {q(r)}, {q(d)}, {o}, {q(a)})" for c, r, d, o, a in MOTIVOS))
    L.append("on conflict (codigo) do nothing;")
    L.append("")
    L.append("insert into config_parametros (chave, valor, descricao, atualizado_por) values")
    L.append(",\n".join(f"  ({q(k)}, {q(json.dumps(v, ensure_ascii=False))}::jsonb, {q(d)}, 1)" for k, v, d in PARAMETROS))
    L.append("on conflict (chave) do nothing;")
    L.append("")
    L.append("select set_config('app.usuario_id', '', false);")
    L.append("select set_config('app.correlation_id', '', false);")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"{OUT.name}: {len(usuarios)} usuários, {len(PARAMETROS)} parâmetros, {len(MOTIVOS)} motivos")


if __name__ == "__main__":
    main()
