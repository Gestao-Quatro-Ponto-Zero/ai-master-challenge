"""Adversarial (evasion) test of the routing policy.

Threat: someone dresses up a privileged-access or HR ticket so it skips the human check and lands,
unreviewed, in a queue with less scrutiny. Attack: append words that pull the model toward another queue.

- White-box (worst case): the attacker knows the model and appends the terms that most separate the
  target queue from the victim queue (coef[target] - coef[victim]).
- Black-box: the attacker appends everyday hardware words without seeing the model.

Victims: test tickets labelled Administrative rights and HR Support. "Escaped" means the full policy
(all seven guards) sends the ticket to auto into a queue other than its true one.
Outputs: outputs/adversarial.json
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from common import write_json
from router import NEVER_AUTO, SEGMENT_SENSITIVE, SEGMENT_WORDS, SENSITIVE, fit_router_and_policy, make_split, max_similarity, segment_sensitivity, vocabulary_coverage, word_pair_coherence

WORD_COUNTS = [0, 1, 2, 3, 5, 8, 12]
VICTIMS = ["Administrative rights", "HR Support"]
TARGETS = ["Hardware", "Miscellaneous"]
BLACK_BOX_WORDS = ["laptop", "screen", "printer", "keyboard", "monitor", "mouse", "cable", "battery", "dock", "headset", "charger", "replacement"]


def main() -> None:
    sp = make_split()
    pipe, policy, train_matrix = fit_router_and_policy(sp)
    vec, clf = pipe.named_steps["tfidf"], pipe.named_steps["clf"]
    classes = list(clf.classes_)
    terms = vec.get_feature_names_out()
    is_word = np.array([" " not in t for t in terms])
    X, y = np.asarray(sp.X_test), np.asarray(sp.y_test)

    def route(texts: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Tiers with the shipped policy, tiers without the segment guard, and the predicted queue."""
        proba = pipe.predict_proba(texts)
        sim, cov = max_similarity(pipe, train_matrix, texts), vocabulary_coverage(pipe, texts)
        with_guard, _ = policy.decide(proba, sim, cov, segment_sensitivity(pipe, texts), word_pair_coherence(pipe, texts))
        # The policy before the pentest: no segment guard, no word-order guard.
        without, _ = policy.decide(proba, sim, cov, np.zeros(len(texts)), np.ones(len(texts)))
        return with_guard, without, np.asarray(classes)[proba.argmax(1)]

    def attack(victim: str, words: list[str], interleave: bool = False) -> list[dict]:
        base = [str(t) for t in X[y == victim]]
        rows = []
        for k in [1] if interleave else WORD_COUNTS:
            if interleave:  # one padding word after every original word: breaks windows, and the text with them
                texts = [" ".join(w for pair in zip(t.split(), (words * 50)[: len(t.split())]) for w in pair) for t in base]
            else:
                texts = [f"{t} {' '.join(words[:k])}".strip() for t in base]
            tiers, tiers_without, pred = route(texts)
            rows.append({
                "words": k,
                "escaped_auto_pct": round(100 * float(((tiers == "auto") & (pred != victim)).mean()), 1),
                "escaped_before_pentest_pct": round(100 * float(((tiers_without == "auto") & (pred != victim)).mean()), 1),
                "assist_pct": round(100 * float((tiers == "assist").mean()), 1),
                "human_pct": round(100 * float((tiers == "human").mean()), 1),
            })
        return rows

    result: dict = {
        "victims": {},
        "black_box_words": BLACK_BOX_WORDS,
        "never_auto": list(NEVER_AUTO),
        "sensitive": list(SENSITIVE),
        "segment_guard": {"words": SEGMENT_WORDS, "threshold": SEGMENT_SENSITIVE},
        "coherence_floor": round(policy.t_coherence, 4),
    }
    for victim in VICTIMS:
        v = classes.index(victim)
        entry = {
            "tickets": int((y == victim).sum()),
            "white_box": {},
            "black_box": attack(victim, BLACK_BOX_WORDS),
            "interleaved_black_box": attack(victim, BLACK_BOX_WORDS, interleave=True)[-1],
        }
        for target in TARGETS:
            gap = clf.coef_[classes.index(target)] - clf.coef_[v]
            order = [i for i in np.argsort(-gap) if is_word[i]]
            words = [str(terms[i]) for i in order[: max(WORD_COUNTS)]]
            entry["white_box"][target] = {"words_used": words, "curve": attack(victim, words)}
        result["victims"][victim] = entry

    path = write_json("adversarial.json", result)
    for victim, e in result["victims"].items():
        print(f"{victim} ({e['tickets']} test tickets)")
        print("  black-box  escaped% before pentest guards:", [r["escaped_before_pentest_pct"] for r in e["black_box"]], "for words", WORD_COUNTS)
        print("  black-box  escaped% with both guards:      ", [r["escaped_auto_pct"] for r in e["black_box"]])
        print("  interleaved black-box:", e["interleaved_black_box"])
        for target, wb in e["white_box"].items():
            print(f"  white-box → {target:13s} escaped%:", [r["escaped_auto_pct"] for r in wb["curve"]], "words:", wb["words_used"][:5])
    print("→", path.relative_to(Path(__file__).resolve().parent))


if __name__ == "__main__":
    main()
