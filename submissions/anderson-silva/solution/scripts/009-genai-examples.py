"""Generate real examples of the prototype's generative-AI module for the documentation (challenge 002).

Draws test tickets with a fixed seed, runs the prototype triage on each and asks the configured model for the
summary and the information request, with the same prompts as the page. Saves the generated drafts; the approved
text is filled in later by a person, never by this script.

Usage:
  python 009-genai-examples.py <csv> [--count N] [--output FILE]
"""
import argparse
import importlib.util
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

SEED = 42
DEFAULT_COUNT = 3
EXCERPT_CHARS = 400
OUTPUT_FILE = "008-genai-examples.json"
# The page no longer reads the pickle (it refits from results/011-013); this script still uses the bundle of 007.
BUNDLE_PATH = Path(__file__).resolve().parents[1] / "cache" / "003-triage-model.joblib"


def load_page():
    spec = importlib.util.spec_from_file_location("triage_page", Path(__file__).with_name("008-triage-app.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--output", default=OUTPUT_FILE, help="file name inside results/")
    args = parser.parse_args()
    page = load_page()
    env = page.read_env()
    api_key = env.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY ausente no .env")
    model = env.get("OPENROUTER_MODEL", page.DEFAULT_GENAI_MODEL)
    bundle = joblib.load(BUNDLE_PATH)
    frame = pd.read_csv(args.csv)
    rows = np.random.default_rng(SEED).choice(bundle["test_rows"], size=args.count, replace=False)
    examples = []
    for row in rows:
        text = frame.at[int(row), "Document"]
        result = page.triage(text, bundle, bundle["threshold"], bundle["min_words"])
        drafts = {task: page.ask_model(api_key, model, instructions, text)
                  for task, (_, instructions) in page.GENAI_TASKS.items()}
        examples.append({"row": int(row), "label": frame.at[int(row), "Topic_group"], "excerpt": text[:EXCERPT_CHARS],
                         "words": result["words"], "decision": result["decision"], "suggested": result["category"],
                         "confidence": round(result["confidence"], 4), "model": model, "generated_at": page.now(),
                         "prompts": {task: instructions for task, (_, instructions) in page.GENAI_TASKS.items()},
                         "drafts": drafts, "approved": {task: None for task in drafts}})
        print(f"\n### Linha {row} | rótulo {examples[-1]['label']} | {result['decision']}"
              f" ({result['category']}, confiança {result['confidence']:.2f})")
        print(f"Trecho: {text[:EXCERPT_CHARS]}")
        for task, draft in drafts.items():
            print(f"\n[{task}]\n{draft}")
    output = page.ROOT / "results" / args.output
    output.write_text(json.dumps(examples, ensure_ascii=False, indent=2))
    print(f"\nRascunhos gravados em {output} (texto aprovado vazio, à espera de uma pessoa)")


if __name__ == "__main__":
    main()
