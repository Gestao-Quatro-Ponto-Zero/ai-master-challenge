"""Executa test_cases.json no pipeline real e grava test_results.json (sem edição manual de resultados)."""
import json, traceback
from inference import triage
cases = json.load(open("test_cases.json")); res = []
for c in cases:
    try:
        r = triage(c["input_text"]); crash = None
    except Exception as e:
        r = {}; crash = traceback.format_exc()
    pc, fails = c["pass_criteria"], []
    if crash: fails.append("exceção na execução")
    else:
        if "category" in pc and r["predicted_category"] != pc["category"]: fails.append(f"categoria {r['predicted_category']} != {pc['category']}")
        if "domain" in pc and r["predicted_domain"] not in pc["domain"]: fails.append(f"domínio {r['predicted_domain']} ∉ {pc['domain']}")
        if "decision" in pc and r["decision"] not in pc["decision"]: fails.append(f"decisão {r['decision']} ∉ {pc['decision']}")
        if "decision_not" in pc and r["decision"] in pc["decision_not"]: fails.append(f"decisão proibida {r['decision']}")
        if "priority" in pc and r["priority"] not in pc["priority"]: fails.append(f"prioridade {r['priority']} ∉ {pc['priority']}")
    res.append(dict(id=c["id"], tipo=c["tipo"], input_text=c["input_text"], expected_domain=c["expected_domain"], predicted_domain=r.get("predicted_domain"),
                    expected_category=c["expected_category"], predicted_category=r.get("predicted_category"), confidence=r.get("confidence"), top3=r.get("top3"),
                    priority=r.get("priority"), decision=r.get("decision"), rule_triggered=r.get("rule_triggered"), rule_reason=r.get("rule_reason"),
                    domain_detail=r.get("domain_detail"), pass_criteria=pc, test_pass=not fails,
                    notes="; ".join(fails) if fails else "todos os critérios definidos a priori atendidos", error=crash))
json.dump(res, open("test_results.json", "w"), indent=1, ensure_ascii=False)
for x in res:
    print(x["id"], x["test_pass"], x["predicted_domain"], x["predicted_category"], x["confidence"], x["priority"], x["decision"], x["rule_triggered"], "|", x["notes"])
print("PASS", sum(x["test_pass"] for x in res), "/", len(res))
