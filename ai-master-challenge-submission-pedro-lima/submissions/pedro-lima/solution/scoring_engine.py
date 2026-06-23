#!/usr/bin/env python3
"""
Lead Scoring Engine v5 — Motor de priorização de deals
Cascata hierárquica de confiança com 5 sinais de qualidade,
urgência calibrada por dados reais, e scoring 3-componentes.

Dados: Kaggle API (kagglehub) com fallback para CSVs locais.
Gera: data/scored_deals.json (consumido pelo dashboard)
"""

import json
import math
from datetime import datetime
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# ── Bayesian smoothing ──────────────────────────────────────────────
PRIOR_STRENGTH = 10  # m parameter

def bayesian_rate(wins, total, base_rate):
    """Smoothed win rate: (wins + m*base_rate) / (total + m)"""
    return (wins + PRIOR_STRENGTH * base_rate) / (total + PRIOR_STRENGTH)


# ── Confidence-weighted blending ────────────────────────────────────
def confidence_blend(n_deals, threshold, signal_specific, signal_fallback):
    """
    Blend between specific and fallback signal based on sample size.
    confidence = min(1, n_deals / threshold)
    blended = confidence * specific + (1 - confidence) * fallback
    """
    confidence = min(1.0, n_deals / threshold)
    return confidence * signal_specific + (1.0 - confidence) * signal_fallback, confidence


# ── Load data via Kaggle API (with local CSV fallback) ──────────────
def load_data():
    import pandas as pd

    pipeline_df = None
    accounts_df = None
    products_df = None
    teams_df = None

    # Try Kaggle API first
    try:
        import kagglehub
        from kagglehub import KaggleDatasetAdapter
        dataset = "agungpambudi/crm-sales-predictive-analytics"
        print("  Carregando dados via Kaggle API...")
        pipeline_df = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS, dataset, "sales_pipeline.csv")
        accounts_df = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS, dataset, "accounts.csv")
        products_df = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS, dataset, "products.csv")
        teams_df = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS, dataset, "sales_teams.csv")
        print("  ✓ Dados carregados via Kaggle API")
    except Exception as e:
        print(f"  ⚠ Kaggle API indisponível ({e}), usando CSVs locais...")
        pipeline_df = pd.read_csv(DATA_DIR / "sales_pipeline.csv")
        accounts_df = pd.read_csv(DATA_DIR / "accounts.csv")
        products_df = pd.read_csv(DATA_DIR / "products.csv")
        teams_df = pd.read_csv(DATA_DIR / "sales_teams.csv")
        print("  ✓ Dados carregados via CSVs locais")

    # Build lookup dicts
    products = {}
    for _, r in products_df.iterrows():
        products[r["product"]] = {
            "series": r["series"],
            "price": int(r["sales_price"])
        }

    accounts = {}
    for _, r in accounts_df.iterrows():
        rev = float(r["revenue"]) if pd.notna(r["revenue"]) else 0
        if rev >= 800: tier = "Enterprise"
        elif rev >= 400: tier = "Mid-Market"
        else: tier = "SMB"
        accounts[r["account"]] = {
            "sector": r["sector"],
            "revenue": rev,
            "employees": int(r["employees"]) if pd.notna(r["employees"]) else 0,
            "tier": tier,
            "office_location": r.get("office_location", ""),
            "subsidiary_of": r.get("subsidiary_of", "")
        }

    teams = {}
    for _, r in teams_df.iterrows():
        teams[r["sales_agent"]] = {
            "manager": r["manager"],
            "regional_office": r["regional_office"]
        }

    # Build deals list
    product_norm = {"GTXPro": "GTX Pro"}
    deals = []
    for _, r in pipeline_df.iterrows():
        product = product_norm.get(r["product"], r["product"])
        acct = accounts.get(r.get("account", ""), {})
        team = teams.get(r["sales_agent"], {})
        prod = products.get(product, {"series": "?", "price": 0})

        raw_account = str(r.get("account", "")).strip() if pd.notna(r.get("account")) else ""
        account_missing = not raw_account
        account_name = raw_account if raw_account else f"Sem conta · {r['opportunity_id']}"

        engage_date = str(r["engage_date"]) if pd.notna(r.get("engage_date")) and str(r.get("engage_date", "")).strip() else None
        close_date = str(r["close_date"]) if pd.notna(r.get("close_date")) and str(r.get("close_date", "")).strip() else None
        close_value = int(r["close_value"]) if pd.notna(r.get("close_value")) and r["close_value"] else 0

        deals.append({
            "id": str(r["opportunity_id"]),
            "agent": r["sales_agent"],
            "product": product,
            "account": account_name,
            "account_missing": account_missing,
            "stage": r["deal_stage"],
            "engage_date": engage_date,
            "close_date": close_date,
            "close_value": close_value,
            "price": prod["price"],
            "series": prod["series"],
            "sector": acct.get("sector", "—"),
            "tier": acct.get("tier", "—"),
            "revenue": acct.get("revenue", 0),
            "employees": acct.get("employees", 0),
            "manager": team.get("manager", "—"),
            "office": team.get("regional_office", "—"),
        })

    return deals


# ── Compute all reference rates (from closed deals only) ───────────
def compute_reference_rates(deals):
    closed = [d for d in deals if d["stage"] in ("Won", "Lost")]
    total_won = sum(1 for d in closed if d["stage"] == "Won")
    total_closed = len(closed)
    global_wr = total_won / total_closed if total_closed > 0 else 0.5

    def compute_rates(key_fn):
        buckets = defaultdict(lambda: {"won": 0, "total": 0})
        for d in closed:
            k = key_fn(d)
            if k is None:
                continue
            buckets[k]["total"] += 1
            if d["stage"] == "Won":
                buckets[k]["won"] += 1
        rates = {}
        for k, v in buckets.items():
            rates[k] = {
                "raw": v["won"] / v["total"] if v["total"] > 0 else global_wr,
                "smoothed": bayesian_rate(v["won"], v["total"], global_wr),
                "won": v["won"],
                "total": v["total"],
                "n": v["total"]
            }
        return rates

    refs = {
        "global_wr": global_wr,
        "global_closed": total_closed,
        "agent": compute_rates(lambda d: d["agent"]),
        "product": compute_rates(lambda d: d["product"]),
        "sector": compute_rates(lambda d: d["sector"]),
        "tier": compute_rates(lambda d: d["tier"]),
        "agent_product": compute_rates(lambda d: (d["agent"], d["product"])),
        "agent_account": compute_rates(lambda d: (d["agent"], d["account"])),
        "agent_sector": compute_rates(lambda d: (d["agent"], d["sector"])),
        "manager_account": compute_rates(lambda d: (d["manager"], d["account"])),
        "month": compute_rates(lambda d: int(d["engage_date"].split("-")[1]) if d["engage_date"] else None),
    }
    return refs


# ── Compute pipeline signals (concurrent deals, momentum, workload) ─
def compute_pipeline_signals(deals):
    for d in deals:
        d["_engage_dt"] = datetime.strptime(d["engage_date"], "%Y-%m-%d") if d["engage_date"] else None
        d["_close_dt"] = datetime.strptime(d["close_date"], "%Y-%m-%d") if d["close_date"] else None

    by_agent = defaultdict(list)
    for d in deals:
        by_agent[d["agent"]].append(d)

    for agent, agent_deals in by_agent.items():
        sorted_deals = sorted(agent_deals, key=lambda x: x["_engage_dt"] or datetime.min)
        for i, d in enumerate(sorted_deals):
            d["_sequence"] = i + 1

    # Concurrent deals at engage_date
    for agent, agent_deals in by_agent.items():
        for d in agent_deals:
            if d["_engage_dt"] is None:
                d["_concurrent"] = 0
                continue
            ref_date = d["_engage_dt"]
            concurrent = 0
            for other in agent_deals:
                if other["id"] == d["id"] or other["_engage_dt"] is None:
                    continue
                o_start = other["_engage_dt"]
                o_end = other["_close_dt"] or datetime(2099, 1, 1)
                if o_start <= ref_date <= o_end:
                    concurrent += 1
            d["_concurrent"] = concurrent

    # Agent momentum: win rate of last 10 closed deals
    for agent, agent_deals in by_agent.items():
        closed_sorted = sorted(
            [d for d in agent_deals if d["stage"] in ("Won", "Lost") and d["_close_dt"]],
            key=lambda x: x["_close_dt"]
        )
        for d in agent_deals:
            ref_date = d["_engage_dt"] or datetime.min
            recent = [c for c in closed_sorted if c["_close_dt"] and c["_close_dt"] < ref_date]
            last_n = recent[-10:]
            if len(last_n) >= 3:
                d["_momentum"] = sum(1 for c in last_n if c["stage"] == "Won") / len(last_n)
            else:
                d["_momentum"] = None

    # Current active deals per agent
    active_count = defaultdict(int)
    for d in deals:
        if d["stage"] in ("Engaging", "Prospecting"):
            active_count[d["agent"]] += 1
    for d in deals:
        d["_active_workload"] = active_count[d["agent"]]


# ── Relationship cascade (proxy hierarchy) ──────────────────────────
def get_relationship_signal(deal, refs):
    """
    Cascade: Agent-Account → Manager-Account → Agent-Sector → Global
    Uses RAW rates (not smoothed) — confidence_blend handles the smoothing.
    Returns (score, confidence, source_label)
    """
    gwr = refs["global_wr"]

    # Level 1: Agent-Account (strongest — direct history with this client)
    key = (deal["agent"], deal["account"])
    if key in refs["agent_account"] and refs["agent_account"][key]["n"] >= 3:
        r = refs["agent_account"][key]
        score, conf = confidence_blend(r["n"], 15, r["raw"], gwr)
        return score, conf, "Vendedor-Conta"

    # Level 2: Manager-Account (team history with this client)
    key = (deal["manager"], deal["account"])
    if key in refs["manager_account"] and refs["manager_account"][key]["n"] >= 3:
        r = refs["manager_account"][key]
        score, conf = confidence_blend(r["n"], 15, r["raw"], gwr)
        return score, conf * 0.8, "Gestor-Conta"

    # Level 3: Agent-Sector (agent's track record in this industry)
    key = (deal["agent"], deal["sector"])
    if deal["sector"] != "—" and key in refs["agent_sector"] and refs["agent_sector"][key]["n"] >= 5:
        r = refs["agent_sector"][key]
        score, conf = confidence_blend(r["n"], 20, r["raw"], gwr)
        return score, conf * 0.5, "Vendedor-Setor"

    # Fallback: neutral
    return gwr, 0.0, "Global"


# ── Quality score with hierarchical confidence cascade ──────────────
def score_quality(deal, refs):
    """
    5 quality signals with confidence-weighted blending.
    Uses RAW rates in confidence_blend to avoid double-smoothing
    (bayesian_rate already smooths, so blending smoothed rates = over-dampening).

    1. Vendedor × Produto (25%) — cascade to vendedor + produto global
    2. Taxa do vendedor (30%) — cascade to global
    3. Taxa do produto (10%) — stable (all products have >500 deals)
    4. Sazonalidade (10%) — cascade to global when month <100 deals
    5. Relacionamento/Conta (25%) — proxy cascade: Agent-Account → Manager-Account → Agent-Sector → Global
    """
    gwr = refs["global_wr"]
    explanations = []
    signal_details = {}

    # ── Signal 1: Vendedor × Produto (25%) ──────────────────────
    ap_key = (deal["agent"], deal["product"])
    # Use RAW rates for agent and product (confidence_blend handles smoothing)
    agent_raw = refs["agent"].get(deal["agent"], {}).get("raw", gwr)
    agent_n = refs["agent"].get(deal["agent"], {}).get("n", 0)
    product_raw = refs["product"].get(deal["product"], {}).get("raw", gwr)
    fallback_ap = 0.5 * agent_raw + 0.5 * product_raw

    if ap_key in refs["agent_product"]:
        ap = refs["agent_product"][ap_key]
        sig_ap, conf_ap = confidence_blend(ap["n"], 10, ap["raw"], fallback_ap)
        ap_n = ap["n"]
    else:
        sig_ap = fallback_ap
        conf_ap = 0.0
        ap_n = 0

    signal_details["agent_product"] = {"value": sig_ap, "confidence": conf_ap, "n": ap_n}

    delta = sig_ap - gwr
    if abs(delta) > 0.03:
        direction = "acima" if delta > 0 else "abaixo"
        explanations.append(
            f"Vendedor × Produto: {sig_ap:.0%} ({direction} da média de {gwr:.0%})"
        )

    # ── Signal 2: Taxa do vendedor (30%) ────────────────────────
    if deal["agent"] in refs["agent"]:
        ag = refs["agent"][deal["agent"]]
        sig_agent, conf_agent = confidence_blend(ag["n"], 20, ag["raw"], gwr)
        ag_n = ag["n"]
    else:
        sig_agent = gwr
        conf_agent = 0.0
        ag_n = 0

    signal_details["agent"] = {"value": sig_agent, "confidence": conf_agent, "n": ag_n}

    delta = sig_agent - gwr
    if abs(delta) > 0.03:
        direction = "acima" if delta > 0 else "abaixo"
        explanations.append(
            f"Taxa do vendedor: {sig_agent:.0%} ({direction} da média)"
        )

    # ── Signal 3: Taxa do produto (10%) ─────────────────────────
    sig_product = product_raw
    prod_n = refs["product"].get(deal["product"], {}).get("n", 0)
    signal_details["product"] = {"value": sig_product, "n": prod_n}

    # ── Signal 4: Sazonalidade (10%) ────────────────────────────
    if deal["engage_date"]:
        month = int(deal["engage_date"].split("-")[1])
        if month in refs["month"]:
            m = refs["month"][month]
            sig_season, conf_season = confidence_blend(m["n"], 100, m["raw"], gwr)
        else:
            sig_season = gwr
            conf_season = 0.0
    else:
        sig_season = gwr
        conf_season = 0.0

    signal_details["seasonality"] = {"value": sig_season}

    delta = sig_season - gwr
    if abs(delta) > 0.03:
        month_names = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
                       7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
        m_name = month_names.get(month, str(month)) if deal["engage_date"] else "?"
        direction = "favorável" if delta > 0 else "desfavorável"
        explanations.append(f"Sazonalidade ({m_name}): {sig_season:.0%} — mês {direction}")

    # ── Signal 5: Relacionamento/Conta (25%) — proxy cascade ────
    rel_score, rel_conf, rel_source = get_relationship_signal(deal, refs)
    signal_details["relationship"] = {"value": rel_score, "confidence": rel_conf, "source": rel_source}

    if rel_source != "Global":
        delta = rel_score - gwr
        if abs(delta) > 0.03:
            direction = "acima" if delta > 0 else "abaixo"
            explanations.append(f"Histórico ({rel_source}): {rel_score:.0%} ({direction} da média)")

    # ── Combine weighted signals ────────────────────────────────
    quality_base = (
        sig_ap * 0.25 +
        sig_agent * 0.30 +
        sig_product * 0.10 +
        sig_season * 0.10 +
        rel_score * 0.25
    )

    # ── Multiplicative modifiers ────────────────────────────────
    modifiers = 1.0

    # Concurrent deals modifier
    conc = deal.get("_concurrent", 0)
    if conc <= 2:
        conc_mod = 0.93
    elif conc <= 6:
        conc_mod = 1.07
    elif conc <= 10:
        conc_mod = 0.93
    else:
        conc_mod = 0.82
        explanations.append(f"Vendedor sobrecarregado ({conc} deals simultâneos)")
    modifiers *= conc_mod
    signal_details["concurrent"] = {"value": conc, "modifier": conc_mod}

    # Workload modifier
    workload = deal.get("_active_workload", 0)
    if workload > 12:
        wl_mod = 0.90
        explanations.append(f"Carga alta ({workload} deals ativos)")
    elif workload > 8:
        wl_mod = 0.95
    else:
        wl_mod = 1.0
    modifiers *= wl_mod
    signal_details["workload"] = {"value": workload, "modifier": wl_mod}

    # Momentum modifier
    momentum = deal.get("_momentum")
    if momentum is not None:
        momentum_delta = momentum - sig_agent
        if momentum_delta > 0.10:
            mom_mod = 1.08
            explanations.append(f"Vendedor em alta (últimos deals: {momentum:.0%})")
        elif momentum_delta < -0.10:
            mom_mod = 0.92
            explanations.append(f"Vendedor em baixa (últimos deals: {momentum:.0%})")
        else:
            mom_mod = 1.0
    else:
        mom_mod = 1.0
    modifiers *= mom_mod
    signal_details["momentum"] = {"value": momentum, "modifier": mom_mod}

    quality = quality_base * modifiers
    quality = max(0.05, min(0.95, quality))

    return quality, signal_details, explanations


# ── Urgency — calibrated from real data ─────────────────────────────
# Historical: Median Won = 57 days, 77% Won close by 90d, 97% by 120d
def compute_urgency(deal, ref_date=None):
    """
    Urgency based on deal age calibrated from actual Won distribution.
    Prospecting without engage_date → 0.4 (limited visibility).
    """
    if ref_date is None:
        ref_date = datetime(2017, 5, 1)  # approximate "today" for dataset

    if deal["_engage_dt"]:
        age_days = (ref_date - deal["_engage_dt"]).days
    else:
        # Prospecting without engage_date — limited visibility
        return 0.4, 0, "Sem data de engajamento"

    # Calibrated bins from real Win distribution
    if age_days <= 30:
        urgency = 0.3
        label = "Normal"
    elif age_days <= 60:
        urgency = 0.5
        label = "Aproximando mediana"
    elif age_days <= 90:
        urgency = 0.7
        label = "Atenção"
    elif age_days <= 120:
        urgency = 0.9
        label = "Urgente"
    else:
        urgency = 1.0
        label = "Resgate"

    return urgency, age_days, label


# ── Impact — normalized product value ───────────────────────────────
def compute_impact(deal, max_price):
    """Impact from product price, log-normalized to [0.1, 1.0]."""
    price = deal["price"]
    if price <= 0:
        return 0.1
    impact = math.log(price + 1) / math.log(max_price + 1)
    return max(0.1, min(1.0, impact))


# ── Action buckets ──────────────────────────────────────────────────
def assign_action(quality, urgency, age_days):
    """
    Assign action bucket from quality and urgency signals.
    Independent of composite priority — based on raw components.
    """
    if quality >= 0.60 and urgency >= 0.5:
        return "Atacar Agora"
    if quality >= 0.45 and age_days > 90:
        return "Resgatar Hoje"
    if quality >= 0.55 and urgency < 0.5:
        return "Avançar Qualificação"
    if quality >= 0.45:
        return "Trabalhar Esta Semana"
    if quality < 0.45 and age_days > 90:
        return "Limpar Pipeline"
    return "Nutrir"


# ── Human-readable quality explanation ──────────────────────────────
def human_quality(quality, gwr):
    """Generate a simple Portuguese explanation of the quality score."""
    diff = quality - gwr
    pct = quality * 100
    if diff > 0.15:
        return f"Chance muito acima da média ({pct:.0f}% vs {gwr*100:.0f}% média)"
    elif diff > 0.05:
        return f"Chance acima da média ({pct:.0f}% vs {gwr*100:.0f}% média)"
    elif diff > -0.05:
        return f"Chance na média ({pct:.0f}%)"
    elif diff > -0.15:
        return f"Chance abaixo da média ({pct:.0f}% vs {gwr*100:.0f}% média)"
    else:
        return f"Chance muito abaixo da média ({pct:.0f}% vs {gwr*100:.0f}% média)"


# ── Main pipeline ──────────────────────────────────────────────────
def run():
    print("═══ Lead Scoring Engine v5 ═══")
    print("\nCarregando dados...")
    deals = load_data()
    print(f"  {len(deals)} deals carregados")

    print("Calculando sinais de pipeline...")
    compute_pipeline_signals(deals)

    print("Calculando taxas de referência...")
    refs = compute_reference_rates(deals)
    gwr = refs["global_wr"]
    print(f"  Taxa global de fechamento: {gwr:.1%}")
    print(f"  Combos vendedor×produto: {len(refs['agent_product'])}")
    print(f"  Vendedores: {len(refs['agent'])}")

    max_price = max(d["price"] for d in deals)

    # Score all deals
    print("\nScorando deals...")
    active = [d for d in deals if d["stage"] in ("Engaging", "Prospecting")]
    closed = [d for d in deals if d["stage"] in ("Won", "Lost")]
    print(f"  Ativos: {len(active)}, Fechados: {len(closed)}")

    def score_and_build(deal_list):
        results = []
        for d in deal_list:
            quality, signals, explanations = score_quality(d, refs)
            urgency, age_days, urg_label = compute_urgency(d)
            impact = compute_impact(d, max_price)

            priority = quality * 0.55 + urgency * 0.25 + impact * 0.20
            action = assign_action(quality, urgency, age_days)
            quality_summary = human_quality(quality, gwr)

            results.append({
                "id": d["id"],
                "agent": d["agent"],
                "product": d["product"],
                "account": d["account"],
                "account_missing": d.get("account_missing", False),
                "stage": d["stage"],
                "engage_date": d["engage_date"],
                "close_date": d["close_date"],
                "close_value": d["close_value"],
                "price": d["price"],
                "series": d["series"],
                "sector": d["sector"],
                "tier": d["tier"],
                "revenue": d["revenue"],
                "manager": d["manager"],
                "office": d["office"],
                # Scoring components
                "quality": round(quality, 4),
                "urgency": round(urgency, 4),
                "urgency_label": urg_label if isinstance(urg_label, str) else "",
                "impact": round(impact, 4),
                "priority": round(priority, 4),
                "action": action,
                "quality_summary": quality_summary,
                "explanations": list(dict.fromkeys(explanations)),  # deduplicate
                # Metadata
                "concurrent_deals": d.get("_concurrent", 0),
                "active_workload": d.get("_active_workload", 0),
                "agent_sequence": d.get("_sequence", 0),
                "age_days": age_days,
            })
        return results

    scored_active = score_and_build(active)
    scored_closed = score_and_build(closed)

    # ── Backtest ────────────────────────────────────────────────
    print("\n── Backtest (validação com deals fechados) ──")

    won_qualities = [d["quality"] for d in scored_closed if d["stage"] == "Won"]
    lost_qualities = [d["quality"] for d in scored_closed if d["stage"] == "Lost"]

    # AUC / Ranking accuracy
    concordant = 0
    discordant = 0
    ties = 0
    for w in won_qualities:
        for l in lost_qualities:
            if w > l:
                concordant += 1
            elif w < l:
                discordant += 1
            else:
                ties += 1
    total_pairs = concordant + discordant + ties
    ranking_accuracy = (concordant + 0.5 * ties) / total_pairs if total_pairs > 0 else 0.5
    print(f"  Precisão do ranking: {ranking_accuracy:.1%}")
    print(f"  Score médio Won: {sum(won_qualities)/len(won_qualities):.3f}")
    print(f"  Score médio Lost: {sum(lost_qualities)/len(lost_qualities):.3f}")

    # Decile analysis
    sorted_closed = sorted(scored_closed, key=lambda x: x["quality"], reverse=True)
    n = len(sorted_closed)
    decile_size = n // 10
    deciles = []
    print(f"\n  Análise por decis (n={n}):")
    for dec in range(10):
        start = dec * decile_size
        end = start + decile_size if dec < 9 else n
        chunk = sorted_closed[start:end]
        won = sum(1 for d in chunk if d["stage"] == "Won")
        wr = won / len(chunk) * 100 if chunk else 0
        avg_q = sum(d["quality"] for d in chunk) / len(chunk) if chunk else 0
        print(f"    D{dec+1}: WR={wr:.1f}% (n={len(chunk)}, avg_q={avg_q:.3f})")
        deciles.append({"decile": dec + 1, "wr": round(wr, 1), "n": len(chunk), "avg_quality": round(avg_q, 3)})

    # Agent stats
    agent_stats = {}
    for d in deals:
        a = d["agent"]
        if a not in agent_stats:
            agent_stats[a] = {"won": 0, "lost": 0, "revenue": 0, "manager": d["manager"], "office": d["office"]}
        if d["stage"] == "Won":
            agent_stats[a]["won"] += 1
            agent_stats[a]["revenue"] += d["close_value"]
        elif d["stage"] == "Lost":
            agent_stats[a]["lost"] += 1

    # Action distribution
    action_dist = defaultdict(int)
    for d in scored_active:
        action_dist[d["action"]] += 1
    print(f"\n── Distribuição de ações (deals ativos) ──")
    for action, count in sorted(action_dist.items(), key=lambda x: -x[1]):
        print(f"    {action}: {count}")

    # Sort active by priority
    scored_active.sort(key=lambda x: x["priority"], reverse=True)

    # Build output JSON
    output = {
        "generated_at": datetime.now().isoformat(),
        "engine_version": "v5",
        "ranking_accuracy": round(ranking_accuracy, 3),
        "global_wr": round(gwr, 4),
        "total_deals": len(deals),
        "active_deals": scored_active,
        "closed_deals": scored_closed,
        "deciles": deciles,
        "agent_stats": {
            agent: {
                "won": s["won"],
                "lost": s["lost"],
                "total": s["won"] + s["lost"],
                "wr": round(s["won"] / (s["won"] + s["lost"]) * 100, 1) if (s["won"] + s["lost"]) > 0 else 0,
                "revenue": s["revenue"],
                "manager": s["manager"],
                "office": s["office"],
                "active": sum(1 for d in scored_active if d["agent"] == agent)
            }
            for agent, s in agent_stats.items()
        },
        "refs": {
            "sector": {k: {"smoothed": round(v["smoothed"], 4), "n": v["n"]} for k, v in refs["sector"].items()},
            "product": {k: {"smoothed": round(v["smoothed"], 4), "n": v["n"]} for k, v in refs["product"].items()},
            "tier": {k: {"smoothed": round(v["smoothed"], 4), "n": v["n"]} for k, v in refs["tier"].items()},
            "month": {str(k): {"smoothed": round(v["smoothed"], 4), "n": v["n"]} for k, v in refs["month"].items()},
        }
    }

    out_path = DATA_DIR / "scored_deals.json"
    with open(out_path, "w") as f:
        json.dump(output, f, ensure_ascii=False)
    print(f"\n✓ Salvo em {out_path} ({out_path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    run()
