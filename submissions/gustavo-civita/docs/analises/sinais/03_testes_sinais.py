"""Testa cada sinal candidato fora da amostra no tempo.
Efeito = variacao em pontos percentuais da chance de ganho (p10->p90 da feature, ou 0->1 se binaria),
controlando data de corte x faixa de idade. Periodos A (jun-jul), B (ago-set): ganho ate o fim; C (out-nov): ganho em 30 dias."""
from bt import *
import os, subprocess, sys
if not os.path.exists("snapshots.pkl"):  # gerado pelo bt.py
    subprocess.run([sys.executable, "bt.py"], check=True, stdout=subprocess.DEVNULL)
S = pd.read_pickle("snapshots.pkl")
acc_feats = ["wr_account", "wr_sector", "wr_agent_x_account", "prior_won_agent_x_account", "prior_any_agent_x_account", "n_agent_x_account",
             "wr_account_x_product", "prior_won_account_x_product", "prior_any_account_x_product", "wr_sector_x_product",
             "wr_size_x_product", "wr_agent_x_sector", "days_since_acc_won", "acc_won_30d", "acc_won_60d", "acc_lost_30d", "acc_wr_90d",
             "acc_open_n", "acc_agent_open_n", "n_account", "is_sub", "log_rev", "log_emp", "year_established", "us_account"]
gen_feats = ["wr_agent", "wr_product", "wr_manager", "wr_office", "wr_agent_x_product", "wr_manager_x_product", "n_agent_x_product",
             "agent_open_n", "agent_open_fresh_n", "agent_stale_share", "agent_new30_n", "agent_closed30_n", "agent_wr_30d",
             "agent_cycle_med", "load_rel", "agent_volume", "log_price", "eng_weekend", "eng_dow", "eng_dom", "eng_dom_late", "has_account"]
A = S["T"].isin(pd.to_datetime(CUT_A)); B = S["T"].isin(pd.to_datetime(CUT_B)); C = S["T"].isin(pd.to_datetime(CUT_C))
rows = []
for f in gen_feats + acc_feats:
    base = S.has_account if f in acc_feats else pd.Series(True, index=S.index)
    r = {"feature": f, "subset": "com conta" if f in acc_feats else "todos"}
    for lab, m, y in [("A", A, "y_ever"), ("B", B, "y_ever"), ("C30", C, "y30"), ("AB", A | B, "y_ever")]:
        o = fwl(S, f, y, base & m)
        r[f"eff_{lab}"] = 100 * o["eff"]; r[f"p_{lab}"] = o["p"]; r[f"n_{lab}"] = o["n"]; r[f"deals_{lab}"] = o["deals"]
    # so entre os que fecharam depois: ganho vs perda, e dias ate fechar
    o = fwl(S, f, "y_ever", base & (A | B) & (S.closes_later == 1)); r["eff_AB_fechados"] = 100 * o["eff"]; r["p_AB_fechados"] = o["p"]
    o = fwl(S, f, "days_to_close", base & (A | B) & (S.closes_later == 1)); r["dias_AB"] = o["eff"]; r["p_dias"] = o["p"]
    o = fwl(S, f, "closes_later", base & (A | B)); r["eff_fecha_AB"] = 100 * o["eff"]; r["p_fecha"] = o["p"]
    rows.append(r)
R = pd.DataFrame(rows)
R["q_AB"] = bh(R.p_AB)
R["mesmo_sinal_ABC"] = (np.sign(R.eff_A) == np.sign(R.eff_B)) & (np.sign(R.eff_B) == np.sign(R.eff_C30))
R["validado"] = R.mesmo_sinal_ABC & (R.p_A < .05) & (R.p_B < .05) & (R.q_AB < .05)
R.to_csv("03_testes_sinais.csv", index=False)
cols = ["feature", "subset", "eff_A", "p_A", "eff_B", "p_B", "eff_C30", "p_C30", "eff_AB", "p_AB", "q_AB", "n_AB", "deals_AB", "validado"]
print(R[cols].round(3).to_string())
print(R[["feature", "eff_AB_fechados", "p_AB_fechados", "dias_AB", "p_dias", "eff_fecha_AB", "p_fecha"]].round(3).to_string())
print("testes:", len(R), " p_AB<0.05:", (R.p_AB < .05).sum(), " esperado por acaso:", round(.05 * len(R), 1))
