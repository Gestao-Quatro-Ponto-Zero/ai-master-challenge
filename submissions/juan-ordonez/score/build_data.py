"""
Pipeline — gera o data.js consumido pelo front.

Fluxo:
  1. Carrega CSVs via score.load_and_enrich
  2. Computa features (is_new_combo, agent_tier, agent_wr, days_open)
  3. Calibra buckets empíricos
  4. Aplica score_deal em todos os deals abertos (Engaging + Prospecting)
  5. Aplica o ranking "Foco da semana" por vendedor (top N por EV)
  6. Escreve web/data.js com window.DATA = {metadata, deals}
  7. Valida distribuição e exemplos; gera golden file

Rodar:
    python build_data.py

Saída:
    ../web/data.js           — consumido pelo HTML
    ../process-log/golden_deals.md — 20 deals de referência pro process log
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

# Import relativo do motor
sys.path.insert(0, str(Path(__file__).resolve().parent))
from score import (  # noqa: E402
    BASELINE_WR,
    FOCUS_MAX,
    FOCUS_MIN,
    FOCUS_PCT,
    SNAPSHOT_DATE,
    compute_buckets,
    compute_features,
    load_and_enrich,
    score_deal,
)


# ============================================================================
# TAXONOMIA DE PRIORIDADE
# ============================================================================

# Mapeamento action → priority. "Atribuir conta" fica fora da escala P
# (None) porque é bloqueio estrutural, não prioridade.
_ACTION_PRIORITY = {
    "Foco da semana":  "P1",
    "Foco secundário": "P2",
    "Ganho rápido":    "P3",
    "Repensar":        "P4",
    "Atribuir conta":  None,
}


def action_priority(action: str) -> str | None:
    """Retorna 'P1'-'P4' ou None para 'Atribuir conta'."""
    return _ACTION_PRIORITY.get(action)


# ============================================================================
# RANKING "Foco da semana" por vendedor
# ============================================================================

def assign_weekly_focus(scored_deals: list[dict]) -> None:
    """
    Para cada vendedor, ordena seus deals rankeáveis por expected_value
    decrescente e marca os top N como "Foco da semana" — sobrescrevendo a
    action inicial.

    N = min(FOCUS_MAX, max(FOCUS_MIN, round(FOCUS_PCT * rankable_count)))

    Deals sem account ("Atribuir conta") são excluídos do ranking: não
    dá pra priorizar um deal sem saber de qual conta ele é.

    Muta a lista in-place.
    """
    by_agent: dict[str, list[dict]] = defaultdict(list)
    for d in scored_deals:
        by_agent[d["agent"]].append(d)

    for agent, deals in by_agent.items():
        rankable = [d for d in deals if d["is_new_combo"] is not None]
        if not rankable:
            continue

        rankable.sort(key=lambda d: d["ev"], reverse=True)
        n = min(FOCUS_MAX, max(FOCUS_MIN, round(FOCUS_PCT * len(rankable))))
        n = min(n, len(rankable))

        for d in rankable[:n]:
            d["action"] = "Foco da semana"


# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    web_dir = project_root / "web"
    process_log_dir = project_root / "process-log"

    print(f"[build] lendo dados de {data_dir}")
    df = load_and_enrich(data_dir)
    df = compute_features(df)
    buckets = compute_buckets(df)

    open_deals = df[df["deal_stage"].isin(["Engaging", "Prospecting"])].copy()
    print(f"[build] {len(open_deals)} deals abertos para scorar")

    scored = [score_deal(row, buckets) for _, row in open_deals.iterrows()]

    # Ranking "Foco da semana" por vendedor — sobrescreve action nos top N
    assign_weekly_focus(scored)

    # Atribui priority (P1-P4 ou None) baseado na action FINAL
    for d in scored:
        d["priority"] = action_priority(d["action"])

    # ========================================================================
    # VALIDAÇÕES
    # ========================================================================

    # Contagem total
    assert len(scored) == len(open_deals), (
        f"esperava {len(open_deals)} deals scorados, obtive {len(scored)}"
    )
    assert len(scored) == 2089, f"esperava 2089 abertos, obtive {len(scored)}"

    # Nenhum NaN em campos críticos
    for d in scored:
        assert d["prob"] is not None, f"prob None em {d['id']}"
        assert d["ev"] is not None, f"ev None em {d['id']}"
        assert d["action"] is not None, f"action None em {d['id']}"
        assert d["explanation"], f"explanation vazia em {d['id']}"

    # Distribuição de ações e prioridades
    action_counts = Counter(d["action"] for d in scored)
    priority_counts = Counter(d["priority"] or "—" for d in scored)

    print(f"\n[build] distribuição das 5 categorias nos {len(scored)} deals abertos:")
    # Ordenação hierárquica: P1, P2, P3, P4, depois fora-da-escala
    order = ["Foco da semana", "Foco secundário", "Ganho rápido", "Repensar", "Atribuir conta"]
    for action in order:
        n = action_counts.get(action, 0)
        if n == 0:
            continue
        priority = action_priority(action) or "—"
        pct = n / len(scored) * 100
        print(f"  {priority:>2}  {action:<18} {n:>5}  ({pct:.1f}%)")

    # Cada categoria precisa ter pelo menos 1% (sanity)
    for action, n in action_counts.items():
        pct = n / len(scored) * 100
        if pct < 1.0:
            print(f"  [AVISO] categoria '{action}' com apenas {pct:.1f}%")

    # Agents únicos com pipeline aberto
    agents_with_pipeline = sorted({d["agent"] for d in scored})
    print(f"\n[build] {len(agents_with_pipeline)} vendedores com pipeline aberto")

    # Bloco organizacional: lista de vendedores com manager, regional_office,
    # e contagem de deals abertos. Consumido pelo front para o dropdown
    # agrupado e para cruzamento com os blocos agregados abaixo.
    # Ordenado por (manager, nome).
    agent_deal_count: dict[str, int] = Counter(d["agent"] for d in scored)
    agents_meta = []
    for agent_name in agents_with_pipeline:
        row = df[df["sales_agent"] == agent_name].iloc[0]
        agents_meta.append({
            "name": agent_name,
            "manager": row["manager"],
            "regional_office": row["regional_office"],
            "open_deals_count": int(agent_deal_count[agent_name]),
        })
    agents_meta.sort(key=lambda a: (a["manager"], a["name"]))

    # Blocos agregados — managers e regional_offices.
    # Suportam a "visão agregada" pedida como bonus do brief
    # ("filtro por manager/região"). Estratégia escolhida: a visão
    # agregada é UNIÃO DOS P1 INDIVIDUAIS dos vendedores do grupo,
    # não recálculo de top N sobre o pipeline unificado — decisão
    # consciente pra refletir "como o time está alocando tempo",
    # não "lista artificial de top deals do time".
    # Por isso, os action_counts aqui são a soma direta dos counts
    # individuais: a união é natural.
    agent_to_manager = {a["name"]: a["manager"] for a in agents_meta}
    agent_to_region = {a["name"]: a["regional_office"] for a in agents_meta}

    managers_dict: dict[str, dict] = {}
    regions_dict: dict[str, dict] = {}

    for a in agents_meta:
        m = a["manager"]
        r = a["regional_office"]

        if m not in managers_dict:
            managers_dict[m] = {
                "name": m,
                "agents": [],
                "regional_offices": set(),
                "open_deals_count": 0,
                "action_counts": Counter(),
            }
        managers_dict[m]["agents"].append(a["name"])
        managers_dict[m]["regional_offices"].add(r)
        managers_dict[m]["open_deals_count"] += a["open_deals_count"]

        if r not in regions_dict:
            regions_dict[r] = {
                "name": r,
                "agents": [],
                "managers": set(),
                "open_deals_count": 0,
                "action_counts": Counter(),
            }
        regions_dict[r]["agents"].append(a["name"])
        regions_dict[r]["managers"].add(m)
        regions_dict[r]["open_deals_count"] += a["open_deals_count"]

    # Passada única pelos deals pra agregar action_counts por manager e região
    for d in scored:
        m = agent_to_manager.get(d["agent"])
        r = agent_to_region.get(d["agent"])
        if m:
            managers_dict[m]["action_counts"][d["action"]] += 1
        if r:
            regions_dict[r]["action_counts"][d["action"]] += 1

    # Serializar sets → listas, Counters → dicts
    managers_meta = []
    for m_name in sorted(managers_dict.keys()):
        d = managers_dict[m_name]
        managers_meta.append({
            "name": d["name"],
            "agents": sorted(d["agents"]),
            "agent_count": len(d["agents"]),
            "regional_offices": sorted(d["regional_offices"]),
            "open_deals_count": d["open_deals_count"],
            "action_counts": dict(d["action_counts"]),
        })

    regions_meta = []
    for r_name in sorted(regions_dict.keys()):
        d = regions_dict[r_name]
        regions_meta.append({
            "name": d["name"],
            "managers": sorted(d["managers"]),
            "manager_count": len(d["managers"]),
            "agents": sorted(d["agents"]),
            "agent_count": len(d["agents"]),
            "open_deals_count": d["open_deals_count"],
            "action_counts": dict(d["action_counts"]),
        })

    # Distribuição de Foco por vendedor
    focus_per_agent = Counter(
        d["agent"] for d in scored if d["action"] == "Foco da semana"
    )
    print(f"\n[build] Foco da semana: {sum(focus_per_agent.values())} deals total")
    print(f"         média por vendedor: {sum(focus_per_agent.values()) / len(focus_per_agent):.1f}")
    print(f"         min: {min(focus_per_agent.values())}, max: {max(focus_per_agent.values())}")

    # ========================================================================
    # EXEMPLOS DE REFERÊNCIA — sanity contra o que validamos antes
    # ========================================================================
    print("\n[build] exemplos de referência:")
    for (agent, account, product) in [
        ("Maureen Marcano", "Ganjaflex", "MG Advanced"),
        ("Daniell Hammack", "Zathunicon", "GTX Plus Basic"),
    ]:
        matches = [
            d for d in scored
            if d["agent"] == agent and d["account"] == account and d["product"] == product
        ]
        if not matches:
            print(f"  [WARN] não achei {agent} / {account} / {product}")
            continue
        d = matches[0]
        print(f"  {agent} / {account} / {product}")
        print(f"    prob={d['prob']}  ev={d['ev']}  action={d['action']}")
        print(f"    {d['explanation']}")

    # Um deal sem conta do Darcel
    darcel_no_account = [
        d for d in scored
        if d["agent"] == "Darcel Schlecht" and d["account"] is None
    ]
    if darcel_no_account:
        d = darcel_no_account[0]
        print(f"\n  Darcel / SEM CONTA / {d['product']}")
        print(f"    prob={d['prob']}  action={d['action']}")
        print(f"    {d['explanation']}")

    # ========================================================================
    # PAYLOAD E ESCRITA DO data.js
    # ========================================================================
    payload = {
        "metadata": {
            "snapshot_date": SNAPSHOT_DATE.strftime("%Y-%m-%d"),
            "global_win_rate": BASELINE_WR,
            "total_open_deals": len(scored),
            "total_agents_with_pipeline": len(agents_with_pipeline),
            "action_counts": dict(action_counts),
            "priority_counts": dict(priority_counts),
            "agents": agents_meta,
            "managers": managers_meta,
            "regional_offices": regions_meta,
            "focus_rule": {
                "pct": FOCUS_PCT,
                "min": FOCUS_MIN,
                "max": FOCUS_MAX,
                "description": (
                    f"Top {int(FOCUS_PCT*100)}% do pipeline rankeável de cada "
                    f"vendedor, entre {FOCUS_MIN} e {FOCUS_MAX} deals."
                ),
            },
            "buckets": [
                {
                    "tier": idx[0],
                    "is_new_combo": bool(idx[1]),
                    "n": int(row["n"]),
                    "win_rate": round(float(row["wr"]), 4),
                    "smoothed_win_rate": round(float(row["smoothed_wr"]), 4),
                }
                for idx, row in buckets.iterrows()
            ],
        },
        "deals": scored,
    }

    web_dir.mkdir(exist_ok=True)
    data_js_path = web_dir / "data.js"
    with data_js_path.open("w", encoding="utf-8") as f:
        f.write("window.DATA = ")
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        f.write(";\n")

    print(f"\n[build] ✅ escrito: {data_js_path}")
    print(f"         tamanho: {data_js_path.stat().st_size / 1024:.1f} KB")

    # ========================================================================
    # GOLDEN FILE (20 deals de referência pro process log)
    # ========================================================================
    golden_path = process_log_dir / "golden_deals.md"
    write_golden_file(scored, golden_path)
    print(f"[build] ✅ escrito: {golden_path}")


# ============================================================================
# GOLDEN FILE
# ============================================================================

def write_golden_file(scored: list[dict], path: Path) -> None:
    """
    Seleciona 20 deals de referência e escreve em markdown.
    Serve como teste de regressão mental: se refatorar o score e os números
    mudarem, a diferença fica visível aqui. Também vai no process log como
    evidência de que olhei casos concretos.
    """
    # Seleção: 5 do Darcel (o que tem mais pipeline), 1 de cada outra
    # combinação relevante.
    darcel = [d for d in scored if d["agent"] == "Darcel Schlecht"][:5]

    # Top deal em Foco da semana (por EV)
    focus_deals = sorted(
        [d for d in scored if d["action"] == "Foco da semana"],
        key=lambda d: d["ev"],
        reverse=True,
    )[:3]

    # Um de cada outra action
    others = {}
    for d in scored:
        if d["action"] not in others and d["action"] != "Foco da semana":
            others[d["action"]] = d
        if len(others) >= 4:
            break

    # GTK 500 (o produto mais caro, $26.768) — se existir no pipeline aberto
    gtk = [d for d in scored if d["product"] == "GTK 500"][:2]

    # Um deal da Maureen (top tier)
    maureen = [d for d in scored if d["agent"] == "Maureen Marcano"][:2]

    # Um deal do Lajuana (único vendedor em tier low)
    lajuana = [d for d in scored if d["agent"] == "Lajuana Vencill"][:2]

    selected = []
    seen_ids = set()
    for group in (darcel, focus_deals, list(others.values()), gtk, maureen, lajuana):
        for d in group:
            if d["id"] not in seen_ids:
                selected.append(d)
                seen_ids.add(d["id"])

    with path.open("w", encoding="utf-8") as f:
        f.write("# Golden deals — 20 casos de referência\n\n")
        f.write(
            "Snapshot dos números gerados pelo motor para deals específicos.\n"
            "Se o score for refatorado e os números mudarem, a diferença fica "
            "visível aqui e vira smoke test.\n\n"
        )
        f.write(f"Total selecionado: **{len(selected)}** deals.\n\n")
        f.write("---\n\n")

        for i, d in enumerate(selected, 1):
            account = d["account"] or "—"
            days = d["days_open"] if d["days_open"] is not None else "—"
            combo = (
                "novo" if d["is_new_combo"] is True
                else "recorrente" if d["is_new_combo"] is False
                else "sem conta"
            )
            f.write(f"## {i}. {d['agent']} — {d['product']} — {account}\n\n")
            f.write(f"- **id:** `{d['id']}`\n")
            f.write(f"- **valor:** ${d['value']:,.0f}\n")
            f.write(f"- **dias aberto:** {days}\n")
            f.write(f"- **combo:** {combo}\n")
            f.write(f"- **prob:** {d['prob']} ({d['confidence']})\n")
            f.write(f"- **expected value:** ${d['ev']:,.0f}\n")
            f.write(f"- **ação:** **{d['action']}**\n")
            f.write(f"- **texto:** _{d['explanation']}_\n\n")


if __name__ == "__main__":
    main()
