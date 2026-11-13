"""Orquestração ponta a ponta: domínio -> classificador IT -> prioridade -> regras de segurança."""
import json, joblib, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from domain_detector import DomainDetector
from priority_estimator import estimate_priority
from security_rules import decide, load_thresholds, UNRELIABLE_CATEGORY_RULES

_CLF = joblib.load("model/classifier_pipeline.pkl")
_DET = DomainDetector.load()
TH_LOW, TH_HIGH = load_thresholds()


def triage(text):
    dom = _DET.predict(text)
    P = _CLF.predict_proba([text])[0]; i = P.argmax()
    cat, conf = str(_CLF.classes_[i]), float(P[i])
    top3 = sorted(zip(_CLF.classes_, P), key=lambda x: -x[1])[:3]
    pr = estimate_priority(text, cat)
    decision, rule, why = decide(text, dom["domain"], cat, conf, pr["priority"], TH_LOW, TH_HIGH)
    category_reliable = rule not in UNRELIABLE_CATEGORY_RULES
    reliability_reason = None if category_reliable else f"categoria sobreposta pela regra de segurança {rule}; não tratar como orientação válida"
    return dict(predicted_domain=dom["domain"], domain_detail=dom, predicted_category=cat, category_raw=cat, confidence=round(conf, 4),
                top3=[(str(c), round(float(p), 4)) for c, p in top3], priority=pr["priority"], priority_justification=pr["justification"],
                decision=decision, rule_triggered=rule, rule_reason=why,
                category_reliable=category_reliable, category_reliability_reason=reliability_reason)


if __name__ == "__main__":
    import sys
    print(json.dumps(triage(" ".join(sys.argv[1:]) or "I cannot log into my account"), indent=1, ensure_ascii=False))
