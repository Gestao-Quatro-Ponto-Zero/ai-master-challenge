import sys; sys.path.insert(0, '.')
from inference import triage

cases = [
    ("login (IT legitimo)", "I cannot log into my account, my password is not being accepted"),
    ("shared folder (IT legitimo)", "I need access to the shared network folder for the finance team reports"),
    ("monitor flicker (IT legitimo)", "My monitor keeps flickering and sometimes goes black during meetings"),
    ("paternity leave (IT? HR)", "How do I request paternity leave through the internal portal?"),
    ("order monitors (compra)", "We need to order 15 new monitors for the new hires starting next month"),
    ("book lunch (FORA DE ESCOPO)", "Can you help me book a table for the team lunch at the restaurant downtown?"),
    ("setup ambiguo", "I need help with the setup, something is not working and I don't know what"),
    ("company lunch q (FORA/ambiguo)", "What time does the company cafeteria serve lunch on Fridays?"),
    ("admin rights", "Please grant me administrator rights on my workstation to install software"),
    ("refund (financeiro)", "I want a refund for the duplicate charge on my invoice last month"),
    ("account compromise", "My account was hacked, there are unauthorized login attempts from another country"),
]

print(f"{'CASO':<32} {'DOM':<16} {'DECISAO':<15} {'REGRA':<24} {'sim':<7} {'cat_ok':<6} {'categoria_crua'}")
print("-"*140)
for name, text in cases:
    r = triage(text)
    sim = r['domain_detail'].get('max_sim_train')
    print(f"{name:<32} {r['predicted_domain']:<16} {r['decision']:<15} {r['rule_triggered']:<24} {str(sim):<7} {str(r['category_reliable']):<6} {r['category_raw']}")
