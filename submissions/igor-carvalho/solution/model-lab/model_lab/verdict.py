"""Critérios de aceite (o que 'condizente com a realidade' significa, em números). Ajuste aqui."""
from __future__ import annotations

import numpy as np

CRITERIA = {
    "spearman_min": 0.30,         # score deve acompanhar a receita esperada verdadeira em 30 dias
    "stale_in_top_max": 0.10,     # no máx. 10% dos deals com score >= 80 podem estar parados (> p90 do ciclo)
    "psi_max": 0.25,              # score não pode mudar de distribuição de um dia para o outro sem motivo
    "challenger_gain_min": 0.10,  # desafiante precisa capturar >= 10% a mais de receita (relativo) no backtest
}


def verdict(report: dict) -> dict:
    sim = report["simulacao"]
    rho_now = float(np.nanmean([d["spearman_atual_vs_verdade"] for d in sim]))
    rho_new = float(np.nanmean([d["spearman_novo_vs_verdade"] for d in sim]))
    hi = sum(d["score>=80_total"] for d in sim)
    stale = sum(d["score>=80_parados(>p90)"] for d in sim) / max(hi, 1)
    psis = [d["psi_score_vs_ontem"] for d in sim if d["psi_score_vs_ontem"] is not None and d["psi_score_vs_ontem"] == d["psi_score_vs_ontem"]]
    rules = all(d["regra_zumbi_sem_score"] and d["regra_score_0_100"] and d["regra_prospecting_sem_score"] for d in sim)
    out = {
        "spearman_medio_atual": round(rho_now, 3), "spearman_medio_novo": round(rho_new, 3),
        "parados_entre_score_80+": round(stale, 3), "psi_max": round(max(psis), 3) if psis else None,
        "regras_de_negocio_ok": rules, "retreinos_promovidos": sum(d["status"] == "active" for d in sim),
        "criterios": CRITERIA,
    }
    out["score_atual_condizente"] = bool(rho_now >= CRITERIA["spearman_min"] and stale <= CRITERIA["stale_in_top_max"]
                                         and (not psis or max(psis) <= CRITERIA["psi_max"]) and rules)
    bt = report.get("backtest")
    if bt:
        now, new = bt["atual_score_lista"]["rev_capture_top20"], bt["novo_receita_30d"]["rev_capture_top20"]
        out["ganho_receita_top20_backtest"] = round(new / now - 1, 3)
        out["desafiante_muito_melhor"] = bool(new / now - 1 >= CRITERIA["challenger_gain_min"] and rho_new > rho_now)
    return out
