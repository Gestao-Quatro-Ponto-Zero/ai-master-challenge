"""Roda test_cases.json pela inferência pós-ajuste. Grava em ARQUIVO NOVO (não toca no histórico test_results.json)."""
import json, traceback, sys
sys.path.insert(0, '/home/ubuntu/g4_challenge/fase4/ml')
from inference import triage

cases = json.load(open("/home/ubuntu/g4_challenge/fase4/ml/test_cases.json"))
hist = json.load(open("/home/ubuntu/g4_challenge/fase4/ml/test_results.json"))
hist_pass = {h["id"]: h["test_pass"] for h in hist}
hist_dec  = {h["id"]: h["decision"] for h in hist}
res = []
for c in cases:
    try:
        r = triage(c["input_text"]); crash = None
    except Exception:
        r = {}; crash = traceback.format_exc()
    pc, fails = c["pass_criteria"], []
    if crash: fails.append("exceção")
    else:
        if "category" in pc and r["predicted_category"] != pc["category"]: fails.append(f"cat {r['predicted_category']}!={pc['category']}")
        if "domain" in pc and r["predicted_domain"] not in pc["domain"]: fails.append(f"dom {r['predicted_domain']}∉{pc['domain']}")
        if "decision" in pc and r["decision"] not in pc["decision"]: fails.append(f"dec {r['decision']}∉{pc['decision']}")
        if "decision_not" in pc and r["decision"] in pc["decision_not"]: fails.append(f"dec proibida {r['decision']}")
        if "priority" in pc and r["priority"] not in pc["priority"]: fails.append(f"prio {r['priority']}∉{pc['priority']}")
    res.append(dict(id=c["id"], tipo=c["tipo"], input_text=c["input_text"],
                    predicted_domain=r.get("predicted_domain"), predicted_category=r.get("predicted_category"),
                    category_raw=r.get("category_raw"), category_reliable=r.get("category_reliable"),
                    confidence=r.get("confidence"), max_sim_train=(r.get("domain_detail") or {}).get("max_sim_train"),
                    priority=r.get("priority"), decision=r.get("decision"), rule_triggered=r.get("rule_triggered"),
                    pass_criteria=pc, test_pass=not fails, notes="; ".join(fails) if fails else "ok"))
json.dump(res, open("/home/ubuntu/g4_challenge/fase4/ml/test_results_pos_ajuste.json", "w"), indent=1, ensure_ascii=False)

print(f"{'id':<3}{'pass':<6}{'HIST':<6}{'dom':<15}{'decisao':<15}{'HISTdec':<15}{'regra':<24}{'sim':<7}{'cat_ok':<6}{'nota'}")
print("-"*130)
for x in res:
    hp = hist_pass.get(x["id"]); hd = hist_dec.get(x["id"])
    flagp = "" if x["test_pass"]==hp else " <-MUDOU"
    print(f"{x['id']:<3}{str(x['test_pass']):<6}{str(hp):<6}{str(x['predicted_domain']):<15}{str(x['decision']):<15}{str(hd):<15}{str(x['rule_triggered']):<24}{str(x['max_sim_train']):<7}{str(x['category_reliable']):<6}{x['notes']}{flagp}")
print("PASS pos-ajuste:", sum(x["test_pass"] for x in res), "/", len(res), "| HIST:", sum(hist_pass.values()), "/", len(hist))
print("AUTOMATIC pos-ajuste:", sum(1 for x in res if x["decision"]=="AUTOMATIC"))
