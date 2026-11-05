"""04 — Quanto custa errar, por fila, e qual política de automação minimiza o desperdício.

Cruza os dois datasets:
- Dataset 2 (previsões do teste em 03_ds2_core.py) dá a taxa REAL de acerto e de erro por fila
  em cada política de automação.
- Dataset 1 dá a escala da operação (~30 mil tickets/ano, segundo o briefing) e o peso da espera
  pelo cliente ("Pending Customer Response").

O que NÃO existe em nenhum dataset (tempo de triagem, tempo perdido por transferência) entra
como PREMISSA explícita, com faixa baixa/base/alta. Duas dessas premissas são medidas no teste
com colegas (ver experiment/PROTOCOLO.md), e o modelo é recalculado com o valor medido.

Uso: python 04_cost_of_error.py <ds2_test_predictions.csv> <customer_support_tickets.csv> <out_dir>
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

pred = pd.read_csv(sys.argv[1])
ds1 = pd.read_csv(sys.argv[2])
out = Path(sys.argv[3])
thr_q = json.load(open(out / "ds2_core_results.json"))["per_queue_threshold_95"]

# --------------------------------------------------------------------------------------
# PREMISSAS (nenhum dataset tem isso; cada uma é rotulada e tem faixa)
# --------------------------------------------------------------------------------------
PREMISSAS = {
    "tickets_ano": {"base": 30_000, "fonte": "briefing do Diretor (~30 mil/ano)"},
    "min_triagem_manual": {"baixo": 1.0, "base": 2.0, "alto": 4.0,
                           "fonte": "premissa; MEDIDO no teste com colegas (modo sem assistente)"},
    "min_triagem_com_sugestao": {"baixo": 0.3, "base": 0.5, "alto": 1.0,
                                 "fonte": "premissa; MEDIDO no teste com colegas (modo com assistente)"},
    "min_por_transferencia": {"baixo": 8.0, "base": 15.0, "alto": 30.0,
                              "fonte": "premissa: 2º atendente relê, devolve, 1º reencaminha"},
    "erro_humano_triagem": {"base": None,
                            "fonte": "DS2: tickets quase idênticos (cos>=0.9) com filas diferentes"},
}
res = json.load(open(out / "ds2_core_results.json"))
PREMISSAS["erro_humano_triagem"]["base"] = round(res["twin90_label_disagree"], 4)

SENSIVEIS = {"HR Support": "dado pessoal (RH)", "Administrative rights": "segurança (privilégio de admin)"}


def politica(nome, auto_mask, conf_humano=False):
    """auto_mask: tickets roteados sem humano. O resto passa por triagem humana.
    conf_humano=True: humano triando COM sugestão do modelo (só confirma/corrige)."""
    return {"nome": nome, "auto": auto_mask, "sugestao": conf_humano}


p = pred
all_auto = np.ones(len(p), bool)
none = np.zeros(len(p), bool)
g90 = p.conf.values >= 0.9
pq = np.array([c >= thr_q[q]["thr"] for q, c in zip(p.pred, p.conf)])
sens_pred = p.pred.isin(SENSIVEIS).values
pq_safe = pq & ~sens_pred  # filas sensíveis: nunca roteia sozinho, humano sempre confirma
# Trava extra: se a probabilidade somada das filas sensíveis passar de G, não roteia sozinho.
# G é decisão de apetite a risco (do negócio, não da IA); ver varredura abaixo.
G_SENS = 0.05
p_sens = sum(p[f"p_{q}"] for q in SENSIVEIS).values
pq_guard = pq_safe & (p_sens < G_SENS)

POLITICAS = [
    politica("P0 Hoje: 100% triagem humana", none),
    politica("P1 100% automático (sem humano)", all_auto),
    politica("P2 Automático se confiança >= 0,90", g90),
    politica("P3 Limiar por fila (meta 95%)", pq),
    politica("P4 = P3 + filas sensíveis sempre com humano + sugestão", pq_safe, conf_humano=True),
    politica(f"P5 = P4 + trava: P(sensível) >= {G_SENS} vai para humano", pq_guard, conf_humano=True),
]


def avalia(pol, cen):
    n = len(p)
    auto = pol["auto"]
    hum = ~auto
    err_auto = (~p.ok.values & auto).sum()
    # humano triando: assume taxa de erro humano do DS2 (premissa).
    # com sugestão, o humano parte do top-1 do modelo; mantemos a mesma taxa (conservador).
    err_hum = hum.sum() * PREMISSAS["erro_humano_triagem"]["base"]
    min_tri = PREMISSAS["min_triagem_com_sugestao" if pol["sugestao"] else "min_triagem_manual"][cen]
    escala = PREMISSAS["tickets_ano"]["base"] / n
    transf = (err_auto + err_hum) * escala
    h_tri = hum.sum() * escala * min_tri / 60
    h_transf = transf * PREMISSAS["min_por_transferencia"][cen] / 60
    # exposição: ticket de fila sensível que caiu em fila errada SEM humano olhar
    true_sens = p.queue.isin(SENSIVEIS).values
    expo = ((~p.ok.values) & auto & true_sens).sum() * escala
    # e ticket NÃO sensível roteado sozinho para fila sensível (vaza para RH/segurança)
    expo += ((~p.ok.values) & auto & sens_pred & ~true_sens).sum() * escala
    return {
        "politica": pol["nome"], "cenario": cen,
        "pct_automatico": round(auto.mean() * 100, 1),
        "transferencias_ano": round(transf),
        "horas_triagem_ano": round(h_tri),
        "horas_transferencia_ano": round(h_transf),
        "horas_total_ano": round(h_tri + h_transf),
        "exposicoes_sensiveis_ano": round(expo),
    }


rows = [avalia(pol, cen) for pol in POLITICAS for cen in ["baixo", "base", "alto"]]
tab = pd.DataFrame(rows)
base = tab[tab.cenario == "base"].set_index("politica")
p0 = base.loc["P0 Hoje: 100% triagem humana", "horas_total_ano"]
base["horas_poupadas_vs_hoje"] = p0 - base["horas_total_ano"]

pd.set_option("display.width", 200)
print("== Premissas")
for k, v in PREMISSAS.items():
    print(f"  {k}: {({kk: vv for kk, vv in v.items() if kk != 'fonte'})}  <- {v['fonte']}")
print("\n== Políticas, cenário BASE (30 mil tickets/ano)")
print(base.drop(columns="cenario").to_string())
print("\n== Sensibilidade: horas totais/ano por cenário (baixo / base / alto)")
print(tab.pivot(index="politica", columns="cenario", values="horas_total_ano")[["baixo", "base", "alto"]].to_string())

print("\n== Varredura da trava G (apetite a risco): quanto automatiza x quantos sensíveis escapam/ano")
sweep = []
true_sens = p.queue.isin(SENSIVEIS).values
for g in [1.0, 0.3, 0.2, 0.1, 0.05, 0.02]:
    a = pq_safe & (p_sens < g)
    sweep.append({"G": g, "pct_automatico": round(a.mean() * 100, 1),
                  "acerto_no_automatico": round(p.ok.values[a].mean() * 100, 1),
                  "sensiveis_que_escapam_ano": round(((~p.ok.values) & a & true_sens).sum() * 30_000 / len(p))})
print(pd.DataFrame(sweep).to_string(index=False))

# Amostra para REVISÃO HUMANA: os "vazamentos" são mesmo sensíveis ou é rótulo errado no dataset?
esc = p[pq_safe & ~p.ok.values & true_sens].sample(30, random_state=7)
esc[["queue", "pred", "conf", "text"]].rename(columns={"queue": "fila_rotulada", "pred": "fila_prevista"}).assign(
    e_mesmo_sensivel_sim_nao="", comentario="").to_csv(out / "revisao_humana_vazamentos.csv", index=False)
print(f"amostra de 30 'vazamentos' para revisão humana: {out / 'revisao_humana_vazamentos.csv'}")

# --------------------------------------------------------------------------------------
# Custo do erro POR FILA (política P4): onde estão os erros que sobram e quem sofre
# --------------------------------------------------------------------------------------
print("\n== Por fila (política P4): erros automáticos que sobram, por 30 mil tickets/ano")
escala = PREMISSAS["tickets_ano"]["base"] / len(p)
fila_rows = []
for q in sorted(p.queue.unique()):
    m_true = p.queue.values == q
    auto_q = pq_safe & m_true
    err = (~p.ok.values) & auto_q
    destino = p[err].pred.value_counts()
    fila_rows.append({
        "fila_real": q,
        "volume_ano": round(m_true.sum() * escala),
        "pct_auto": round(auto_q.sum() / m_true.sum() * 100, 1),
        "erros_auto_ano": round(err.sum() * escala),
        "para_onde_vai_o_erro": ", ".join(f"{k} {round(v*escala)}" for k, v in destino.head(2).items()) or "-",
        "sensivel": SENSIVEIS.get(q, ""),
        "limiar": thr_q[q]["thr"],
    })
fila = pd.DataFrame(fila_rows).sort_values("volume_ano", ascending=False)
print(fila.to_string(index=False))

# --------------------------------------------------------------------------------------
# Dataset 1: quanto do fluxo é ESPERA pelo cliente (H4) — único sinal operacional utilizável
# --------------------------------------------------------------------------------------
pend = (ds1["Ticket Status"] == "Pending Customer Response").mean()
print(f"\n== Dataset 1: {pend:.1%} dos tickets estão parados esperando o cliente "
      f"(sintético; usado só como ordem de grandeza da espera, H4)")

json.dump({
    "premissas": PREMISSAS,
    "politicas_base": base.reset_index().to_dict(orient="records"),
    "sensibilidade": tab.to_dict(orient="records"),
    "por_fila_p4": fila.to_dict(orient="records"),
    "varredura_trava_sensivel": sweep,
    "ds1_pending_customer_share": round(pend, 4),
}, open(out / "cost_of_error.json", "w"), ensure_ascii=False, indent=1)
print(f"\nSalvo em {out / 'cost_of_error.json'}")
