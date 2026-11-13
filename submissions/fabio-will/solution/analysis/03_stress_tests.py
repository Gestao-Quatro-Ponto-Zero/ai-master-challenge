"""Stress tests for the router, by severity. Every scenario is measured, not argued.

Severity scale (impact if the guardrail fails, not likelihood):
- extreme: a wrong automatic action reaches a customer or a security/HR queue
- critical: the automation keeps running but quietly gets worse
- medium: some tickets degrade, a human catches them in the normal flow
- light: known weakness with contained impact
Outputs: outputs/stress.json
"""
from __future__ import annotations

import random

import numpy as np

from common import SEED, load_tickets, write_json
from router import (
    AUTO_PRECISION,
    OOD_PERCENTILE,
    PSI_ALARM,
    SENSITIVE,
    NEVER_AUTO,
    build_router,
    fit_router_and_policy,
    psi,
    segment_sensitivity,
    word_pair_coherence,
    SEGMENT_SENSITIVE,
    SENSITIVE_MASS,
    vocabulary_coverage,
    expected_calibration_error,
    gate_curve,
    make_split,
    max_similarity,
    pick_threshold,
    top2_hit,
)

# Synthetic probes (written for this test, labelled as such): a Brazilian operation will receive
# Portuguese tickets, and the router was trained on English only.
PT_PROBES = [
    ("não consigo acessar minha conta, a senha expirou e o reset não chega", "Access"),
    ("perdi o acesso ao sistema de ponto depois da troca de senha", "Access"),
    ("preciso liberar o acesso da nova analista ao drive do time", "Access"),
    ("notebook não liga depois da atualização de ontem", "Hardware"),
    ("monitor piscando e teclado parou de funcionar", "Hardware"),
    ("impressora do terceiro andar travando todos os documentos", "Hardware"),
    ("preciso de permissão de administrador para instalar o software de análise", "Administrative rights"),
    ("solicito acesso de admin na máquina para configurar a vpn", "Administrative rights"),
    ("pedido de direitos de administrador local para o time de dados", "Administrative rights"),
    ("dúvida sobre minhas férias e o saldo do banco de horas", "HR Support"),
    ("como atualizo meus dados bancários para o pagamento do salário", "HR Support"),
    ("quero informar uma licença médica a partir de segunda", "HR Support"),
    ("solicito a compra de dois monitores para o time de produto", "Purchase"),
    ("orçamento para renovar as licenças do software de design", "Purchase"),
    ("aprovar a compra de headsets para o suporte", "Purchase"),
    ("pasta compartilhada sem espaço, a cota está cheia", "Storage"),
    ("preciso aumentar o armazenamento da caixa de e-mail", "Storage"),
    ("backup do servidor de arquivos falhou de novo", "Storage"),
    ("projeto interno de migração precisa de um ambiente de testes", "Internal Project"),
    ("criar repositório para o projeto de dados do trimestre", "Internal Project"),
    ("cronograma do projeto interno de automação atrasou", "Internal Project"),
    ("reunião marcada sem link, quem pode ajustar", "Miscellaneous"),
    ("dúvida geral sobre o uso da sala de reuniões", "Miscellaneous"),
    ("onde encontro o manual do novo processo", "Miscellaneous"),
]


def add_typos(text: str, rate: float, rng: random.Random) -> str:
    letters = "abcdefghijklmnopqrstuvwxyz"
    out = []
    for ch in text:
        if ch.isalpha() and rng.random() < rate:
            op = rng.random()
            if op < 0.4:
                out.append(rng.choice(letters))        # substitution
            elif op < 0.7:
                continue                               # deletion
            else:
                out.append(ch + rng.choice(letters))   # insertion
        else:
            out.append(ch)
    return "".join(out)


def breaker_simulation(in_pred: np.ndarray, ood_pred: np.ndarray, classes: np.ndarray, y_train: np.ndarray, window: int = 200) -> dict:
    """Stream normal tickets, then a 50/50 mix with out-of-domain ones; count tickets until PSI alarm."""
    rng = np.random.default_rng(SEED)
    baseline = np.array([(y_train == c).mean() for c in classes])
    normal = rng.choice(in_pred, size=1000, replace=False)
    mixed = np.where(rng.random(1000) < 0.5, rng.choice(ood_pred, 1000), rng.choice(in_pred, 1000))
    stream = np.concatenate([normal, mixed])
    false_alarm_at, alarm_at = None, None
    for i in range(window, len(stream) + 1):
        w = stream[i - window:i]
        obs = np.array([(w == c).sum() for c in classes])
        if psi(baseline, obs) > PSI_ALARM:
            if i <= 1000:
                false_alarm_at = false_alarm_at or i
            else:
                alarm_at = i - 1000
                break
    psi_normal = psi(baseline, np.array([(normal == c).sum() for c in classes]))
    return {"window": window, "psi_threshold": PSI_ALARM, "psi_on_normal_traffic": round(psi_normal, 4), "false_alarm_on_normal_traffic": false_alarm_at, "tickets_after_flood_start_until_pause": alarm_at}


def sensitive_tradeoff(proba: np.ndarray, classes: np.ndarray, y: np.ndarray, t_auto: float, segment: np.ndarray) -> list[dict]:
    """How much automation each sensitivity setting costs, and how many sensitive tickets still leak.
    Mass-only rows show the whole-ticket guard alone; the last row adds the segment guard (the shipped policy)."""
    conf = proba.max(1)
    pred = classes[proba.argmax(1)]
    mass = proba[:, [i for i, c in enumerate(classes) if c in SENSITIVE]].sum(1)
    rows = []
    settings = [(th, False) for th in [0.05, 0.10, 0.15, 0.20, 1.01]] + [(SENSITIVE_MASS, True)]
    for th, use_segment in settings:
        blocked = (~np.isin(pred, SENSITIVE)) & ((mass >= th) | (use_segment & (segment >= SEGMENT_SENSITIVE)))
        auto = (conf >= t_auto) & ~blocked & ~np.isin(pred, NEVER_AUTO)
        leak = auto & np.isin(y, SENSITIVE) & (pred != y)
        rows.append({
            "sensitive_mass": th if th <= 1 else None,
            "segment": use_segment,
            "auto_share": round(float(auto.mean()), 4),
            "sensitive_tickets_auto_routed_elsewhere": int(leak.sum()),
        })
    return rows


def tier_summary(tiers: np.ndarray, correct: np.ndarray) -> dict:
    res = {}
    for t in ["auto", "assist", "human"]:
        m = tiers == t
        res[t] = {"share": round(float(m.mean()), 4), "precision": round(float(correct[m].mean()), 4) if m.any() else None}
    return res


def main() -> None:
    sp = make_split()
    pipe, policy, train_matrix = fit_router_and_policy(sp)
    classes = pipe.classes_
    t_auto, t_assist, t_ood, c_min = policy.t_auto, policy.t_assist, policy.t_ood, policy.c_min

    def evaluate(texts, y=None) -> dict:
        proba = pipe.predict_proba(texts)
        conf = proba.max(1)
        pred = classes[proba.argmax(1)]
        sim = max_similarity(pipe, train_matrix, texts)
        cov = vocabulary_coverage(pipe, texts)
        seg = segment_sensitivity(pipe, texts)
        coh = word_pair_coherence(pipe, texts)
        tiers, reasons = policy.decide(proba, sim, cov, seg, coh)
        no_guard = np.where(conf >= t_auto, "auto", np.where(conf >= t_assist, "assist", "human"))
        out = {"proba": proba, "conf": conf, "pred": pred, "sim": sim, "cov": cov, "seg": seg, "coh": coh, "tiers": tiers, "reasons": reasons, "no_guard": no_guard}
        if y is not None:
            out["correct"] = pred == y
            out["hit2"] = top2_hit(proba, classes, y)
        return out

    base = evaluate(sp.X_test, sp.y_test)
    baseline = {
        "accuracy": round(float(base["correct"].mean()), 4),
        "ece": round(expected_calibration_error(base["conf"], base["correct"]), 4),
        "thresholds": {"t_auto": t_auto, "t_assist": t_assist, "t_ood_similarity": round(t_ood, 4), "c_min_coverage": round(c_min, 4)},
        "confidence_only_tiers": tier_summary(base["no_guard"], base["correct"]),
        "reasons": {k: int(v) for k, v in zip(*np.unique(base["reasons"], return_counts=True))},
        "tiers": tier_summary(base["tiers"], base["correct"]),
        "assist_top2_accuracy": round(float(base["hit2"][base["tiers"] == "assist"].mean()), 4),
        "guard_false_rejection": round(float(((base["sim"] < t_ood) | (base["cov"] < c_min) | (base["coh"] < policy.t_coherence)).mean()), 4),
    }
    print("baseline", baseline)

    scenarios = []

    # EXTREME 1: out-of-domain flood (Dataset 1: customer product tickets the router never saw).
    d1 = load_tickets()
    d1_text = (d1["Ticket Subject"].fillna("") + " " + d1["Ticket Description"].fillna("")).str.replace("{product_purchased}", "product", regex=False).str.lower().values
    ood = evaluate(d1_text)
    scenarios.append({
        "id": "E1", "severity": "extreme", "name": "Enxurrada de tickets de outro domínio",
        "evidence": f"{len(d1_text):,} tickets em formato de cliente (Dataset 1) passados por um roteador treinado em tickets de TI".replace(",", "."),
        "without_guard": {"auto_share": round(float((ood["no_guard"] == "auto").mean()), 4), "median_confidence": round(float(np.median(ood["conf"])), 3), "top_prediction_share": round(float(max(np.unique(ood["pred"], return_counts=True)[1]) / len(d1_text)), 4)},
        "with_guard": {"auto_share": round(float((ood["tiers"] == "auto").mean()), 4), "human_share": round(float((ood["tiers"] == "human").mean()), 4)},
        "cost_in_domain": {"false_rejection": baseline["guard_false_rejection"]},
        "stream_breaker": breaker_simulation(base["pred"], ood["pred"], classes, sp.y_train),
        "guardrail": "Duas travas: por ticket, se o texto não se parece com nada do histórico vai para humano; por população, o disjuntor compara a distribuição das últimas 200 previsões com a do histórico (PSI) e pausa a auto-rota quando passa de 0,25",
    })

    # EXTREME 2: a new category appears (taxonomy change). Retrain without "Purchase".
    held = "Purchase"
    keep = sp.y_train != held
    pipe_wo = build_router().fit(sp.X_train[keep], sp.y_train[keep])
    tm_wo = pipe_wo.named_steps["tfidf"].transform(sp.X_train[keep])
    vp = pipe_wo.predict_proba(sp.X_val[sp.y_val != held])
    vc = vp.max(1)
    vcor = pipe_wo.classes_[vp.argmax(1)] == sp.y_val[sp.y_val != held]
    ta2 = pick_threshold(gate_curve(vc, vcor), AUTO_PRECISION)
    tsim2 = float(np.percentile(max_similarity(pipe_wo, tm_wo, sp.X_val[sp.y_val != held]), OOD_PERCENTILE))
    new_texts = sp.X_test[sp.y_test == held]
    np_proba = pipe_wo.predict_proba(new_texts)
    np_conf = np_proba.max(1)
    np_sim = max_similarity(pipe_wo, tm_wo, new_texts)
    scenarios.append({
        "id": "E2", "severity": "extreme", "name": "Surge uma fila que o modelo não conhece",
        "evidence": f"Retreinei sem a fila Compras (Purchase) e mandei os {len(new_texts)} tickets de Compras do teste",
        "without_guard": {"auto_share": round(float((np_conf >= ta2).mean()), 4)},
        "with_guard": {"auto_share": round(float(((np_conf >= ta2) & (np_sim >= tsim2)).mean()), 4)},
        "destinations": {k: int(v) for k, v in zip(*np.unique(pipe_wo.classes_[np_proba.argmax(1)], return_counts=True))},
        "guardrail": "Toda auto-rota errada vira sinal: taxa de override por fila no painel; categoria nova exige retreino com rótulos, e até lá a fila entra como regra fixa por palavra-chave revisada por humano",
    })

    # EXTREME 3: sensitive queues. Routing is allowed, acting is not.
    auto = base["tiers"] == "auto"
    sens = {}
    for c in SENSITIVE:
        into = auto & (base["pred"] == c)
        out_of = auto & (sp.y_test == c)
        sens[c] = {
            "auto_routed_into": int(into.sum()),
            "wrong_auto_routed_into": int((into & ~base["correct"]).sum()),
            "auto_routed_out_of_true": int(out_of.sum()),
            "wrong_auto_routed_out_of_true": int((out_of & ~base["correct"]).sum()),
            "true_total": int((sp.y_test == c).sum()),
            "confidence_only_wrong_auto_out_of_true": int(((base["no_guard"] == "auto") & (sp.y_test == c) & ~base["correct"]).sum()),
        }
    scenarios.append({
        "id": "E3", "severity": "extreme", "name": "Ticket de acesso privilegiado ou de RH na fila errada",
        "evidence": "Tickets de Direitos de administrador e de RH no conjunto de teste, olhando só o que seria roteado sem humano",
        "measured": sens,
        "privacy_tradeoff": sensitive_tradeoff(base["proba"], classes, sp.y_test, t_auto, base["seg"]),
        "guardrail": "Política: a IA só escolhe a fila. Conceder permissão, mexer em folha ou responder RH é sempre humano, com dupla checagem para direito de administrador",
    })

    # CRITICAL 1: mix shift (an incident multiplies one category). Resample test priors.
    rng = np.random.default_rng(SEED)
    shifts = {}
    for c, factor in [("Access", 3), ("Hardware", 2), ("HR Support", 3)]:
        idx_c = np.where(sp.y_test == c)[0]
        extra = rng.choice(idx_c, size=len(idx_c) * (factor - 1), replace=True)
        idx = np.concatenate([np.arange(len(sp.y_test)), extra])
        t = base["tiers"][idx]
        corr = base["correct"][idx]
        shifts[f"{c} x{factor}"] = tier_summary(t, corr)
    scenarios.append({
        "id": "C1", "severity": "critical", "name": "Incidente multiplica uma categoria",
        "evidence": "Reamostrei o teste triplicando Acesso e RH e dobrando Hardware",
        "measured": shifts,
        "guardrail": "Precisão da auto-rota monitorada por fila e por dia; alarme se cair abaixo de 92% em amostra auditada",
    })

    # CRITICAL 2: typing noise (mobile, hurried users).
    noise = {}
    r = random.Random(SEED)
    for rate in [0.05, 0.10, 0.20]:
        noisy = np.array([add_typos(t, rate, r) for t in sp.X_test])
        ev = evaluate(noisy, sp.y_test)
        noisy_val = np.array([add_typos(t, rate, r) for t in sp.X_val])
        nvp = pipe.predict_proba(noisy_val)
        t_fix = pick_threshold(gate_curve(nvp.max(1), classes[nvp.argmax(1)] == sp.y_val), AUTO_PRECISION)
        fixed = ev["conf"] >= t_fix
        noise[f"{int(rate * 100)}%"] = {
            "accuracy": round(float(ev["correct"].mean()), 4), **tier_summary(ev["tiers"], ev["correct"]),
            "recalibrated_t_auto": t_fix,
            "recalibrated_auto": {"share": round(float(fixed.mean()), 4), "precision": round(float(ev["correct"][fixed].mean()), 4)},
        }
    scenarios.append({
        "id": "C2", "severity": "critical", "name": "Texto com erro de digitação",
        "evidence": "5%, 10% e 20% das letras trocadas, apagadas ou duplicadas no conjunto de teste",
        "measured": noise,
        "guardrail": "O gate perde precisão com ruído; a correção é recalibrar o limiar com amostra auditada semanal (a coluna de limiar recalibrado mostra o efeito)",
    })

    # MEDIUM 1: short or vague tickets.
    lengths = np.array([len(t.split()) for t in sp.X_test])
    buckets = {}
    for name, lo, hi in [("1 a 5 palavras", 1, 5), ("6 a 15", 6, 15), ("16 a 40", 16, 40), ("mais de 40", 41, 10_000)]:
        m = (lengths >= lo) & (lengths <= hi)
        buckets[name] = {"tickets": int(m.sum()), "accuracy": round(float(base["correct"][m].mean()), 4), **tier_summary(base["tiers"][m], base["correct"][m])}
    scenarios.append({
        "id": "M1", "severity": "medium", "name": "Ticket curto ou vago",
        "evidence": "Conjunto de teste separado por tamanho do texto",
        "measured": buckets,
        "guardrail": "Ticket curto cai para assistido ou humano; o formulário pede um detalhe a mais quando o texto tem menos de 6 palavras",
    })

    # MEDIUM 2: Portuguese tickets (synthetic probes).
    pt_texts = np.array([t for t, _ in PT_PROBES])
    pt_y = np.array([c for _, c in PT_PROBES])
    pt = evaluate(pt_texts, pt_y)
    scenarios.append({
        "id": "M2", "severity": "medium", "name": "Ticket em português num modelo treinado em inglês",
        "evidence": f"{len(PT_PROBES)} sondas sintéticas escritas para este teste, 3 por categoria",
        "measured": {"accuracy": round(float(pt["correct"].mean()), 4), **tier_summary(pt["tiers"], pt["correct"]), "without_guard_auto_share": round(float((pt["no_guard"] == "auto").mean()), 4)},
        "guardrail": "Guarda de novidade manda para humano; em produção, treinar com o histórico real da operação no idioma dela",
    })

    # MEDIUM 3: neighbour queues the model confuses.
    pairs = {}
    wrong = ~base["correct"]
    for a, b in zip(sp.y_test[wrong], base["pred"][wrong]):
        key = f"{a} → {b}"
        pairs[key] = pairs.get(key, 0) + 1
    top_pairs = dict(sorted(pairs.items(), key=lambda kv: -kv[1])[:6])
    scenarios.append({
        "id": "M3", "severity": "medium", "name": "Filas vizinhas que se confundem",
        "evidence": f"{int(wrong.sum()):,} erros no teste, agrupados por par real e previsto".replace(",", "."),
        "measured": top_pairs,
        "guardrail": "No assistido, o agente vê as duas filas mais prováveis e confirma com um clique",
    })

    # LIGHT 1: small classes and per-class calibration.
    per_class = {}
    for c in classes:
        m = sp.y_test == c
        per_class[c] = {"support": int(m.sum()), "accuracy": round(float(base["correct"][m].mean()), 4), "auto_share": round(float((base["tiers"][m] == "auto").mean()), 4), "ece": round(expected_calibration_error(base["conf"][m], base["correct"][m]), 4)}
    scenarios.append({
        "id": "L1", "severity": "light", "name": "Categorias pequenas e calibração por fila",
        "evidence": "Acurácia, parcela automática e erro de calibração por categoria no teste",
        "measured": per_class,
        "guardrail": "Limiar por fila quando houver volume para estimar; até lá, limiar global",
    })

    for s in scenarios:
        print(s["id"], s["name"], {k: v for k, v in s.items() if k in ("without_guard", "with_guard")} or "")

    write_json("stress.json", {"baseline": baseline, "scenarios": scenarios})


if __name__ == "__main__":
    main()
