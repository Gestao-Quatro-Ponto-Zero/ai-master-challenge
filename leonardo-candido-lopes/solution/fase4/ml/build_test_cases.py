"""Gera test_cases.json (critérios de aprovação definidos ANTES da execução)."""
import json
junk = " ".join((["lorem", "ipsum", "dolor", "sit", "amet", "zxqv", "blorf", "qwerty", "asdfgh", "foo", "bar", "baz", "1234", "!!!", "xyz"] * 15)[:220])
C = [
 (1, "obrigatorio", "I cannot log into my account", "IT_INTERNAL", "Access", {"category": "Access", "domain": ["IT_INTERNAL"]}),
 (2, "obrigatorio", "My laptop screen is flickering", "IT_INTERNAL", "Hardware", {"category": "Hardware", "domain": ["IT_INTERNAL"]}),
 (3, "obrigatorio", "I need to order 5 new monitors for the team", "IT_INTERNAL", "Purchase", {"category": "Purchase", "domain": ["IT_INTERNAL"]}),
 (4, "obrigatorio", "I need access to the shared folder for project files", "IT_INTERNAL", "Storage", {"category": "Storage", "domain": ["IT_INTERNAL"]}),
 (5, "obrigatorio", "Please give me admin access to the server", "IT_INTERNAL", "Administrative rights", {"category": "Administrative rights", "decision": ["HUMAN_REQUIRED"]}),
 (6, "obrigatorio", "I want a refund for my defective product order #1234", "FINANCIAL_COMMERCIAL", None, {"domain": ["FINANCIAL_COMMERCIAL"], "decision": ["HUMAN_REQUIRED"]}),
 (7, "obrigatorio", "Something is wrong with my setup", "IT_INTERNAL", "Hardware|Miscellaneous", {"decision_not": ["AUTOMATIC"]}),
 (8, "obrigatorio", "help", "INDETERMINATE", None, {"domain": ["INDETERMINATE"], "decision": ["HUMAN_REQUIRED"]}),
 (9, "obrigatorio", "What time is the company lunch today?", "OUT_OF_SCOPE", None, {"domain": ["OUT_OF_SCOPE", "INDETERMINATE"], "decision": ["HUMAN_REQUIRED"]}),
 (10, "obrigatorio", "Our entire network is down — no one can access anything", "IT_INTERNAL", "Access|Hardware", {"priority": ["CRITICAL"], "decision_not": ["AUTOMATIC"]}),
 (11, "adicional", "My account was hacked and there were unauthorized charges", "INDETERMINATE", None, {"decision": ["ESCALATE"]}),
 (12, "adicional", "I need to request paternity leave and update my beneficiaries", "IT_INTERNAL", "HR Support", {"category": "HR Support", "domain": ["IT_INTERNAL"]}),
 (13, "adicional", "The deadline for the Q4 migration project needs to be updated", "IT_INTERNAL", "Internal Project", {"category": "Internal Project", "domain": ["IT_INTERNAL"]}),
 (14, "adicional", "Não consigo acessar minha pasta de trabalho no servidor", "IT_INTERNAL", "Storage", {"decision": ["HUMAN_REQUIRED"]}),
 (15, "adicional", junk, "OUT_OF_SCOPE", None, {"decision": ["HUMAN_REQUIRED"], "no_crash": True}),
]
out = [dict(id=i, tipo=t, input_text=x, expected_domain=d, expected_category=c, pass_criteria=p) for i, t, x, d, c, p in C]
json.dump(out, open("test_cases.json", "w"), indent=1, ensure_ascii=False)
