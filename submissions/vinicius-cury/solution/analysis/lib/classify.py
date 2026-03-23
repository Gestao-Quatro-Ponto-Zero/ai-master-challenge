"""
LLM classification helper for ticket analysis.
Supports Claude (Sonnet/Haiku) and Gemini models.
Model selection will be decided after cost analysis.
"""

from __future__ import annotations

import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env.local")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")

# Model mappings — will be updated when we decide on specific versions
MODEL_MAP = {
    "sonnet": "claude-sonnet-4-5-20250514",
    "haiku": "claude-haiku-4-5-20251001",
    "gemini": "gemini-2.0-flash",
}

CLASSIFICATION_PROMPT = """You are a support ticket classifier for a technology company.
Classify the following ticket into exactly one category.

Categories:
{taxonomy}

Respond in JSON only:
{{"category": "...", "confidence": 0.0-1.0, "reasoning": "one sentence explaining why"}}

Ticket:
{text}"""


def _classify_anthropic(text: str, taxonomy: str, model_key: str) -> dict:
    """Classify using Claude API."""
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    model_id = MODEL_MAP.get(model_key, model_key)
    prompt = CLASSIFICATION_PROMPT.format(taxonomy=taxonomy, text=text)

    start = time.time()
    response = client.messages.create(
        model=model_id,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    latency = time.time() - start

    content = response.content[0].text.strip()
    # Extract JSON from response
    try:
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {"category": "parse_error", "confidence": 0.0, "reasoning": content}

    result["model"] = model_id
    result["latency_s"] = round(latency, 2)
    result["input_tokens"] = response.usage.input_tokens
    result["output_tokens"] = response.usage.output_tokens
    return result


def _classify_gemini(text: str, taxonomy: str) -> dict:
    """Classify using Gemini API."""
    import google.generativeai as genai

    genai.configure(api_key=GOOGLE_AI_API_KEY)
    model = genai.GenerativeModel(MODEL_MAP["gemini"])
    prompt = CLASSIFICATION_PROMPT.format(taxonomy=taxonomy, text=text)

    start = time.time()
    response = model.generate_content(prompt)
    latency = time.time() - start

    content = response.text.strip()
    try:
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {"category": "parse_error", "confidence": 0.0, "reasoning": content}

    result["model"] = MODEL_MAP["gemini"]
    result["latency_s"] = round(latency, 2)
    return result


def classify_ticket(text: str, taxonomy: str, model: str = "haiku") -> dict:
    """
    Classify a single ticket.
    model: "sonnet", "haiku", "gemini", or a full model ID
    """
    if model in ("gemini",):
        return _classify_gemini(text, taxonomy)
    return _classify_anthropic(text, taxonomy, model)


def batch_classify(
    texts: list[str],
    taxonomy: str,
    model: str = "haiku",
    batch_size: int = 10,
    progress: bool = True,
) -> list[dict]:
    """Classify a batch of tickets with progress tracking."""
    from tqdm import tqdm

    results = []
    iterator = tqdm(texts, desc=f"Classifying ({model})") if progress else texts

    for i, text in enumerate(iterator):
        try:
            result = classify_ticket(text, taxonomy, model)
            result["index"] = i
            results.append(result)
        except Exception as e:
            results.append({
                "index": i,
                "category": "error",
                "confidence": 0.0,
                "reasoning": str(e),
                "model": model,
            })

        # Rate limiting: pause between batches
        if (i + 1) % batch_size == 0:
            time.sleep(1)

    return results


def benchmark(
    texts: list[str],
    true_labels: list[str],
    taxonomy: str,
    models: list[str] = None,
) -> pd.DataFrame:
    """
    Benchmark multiple models on labeled data.
    Returns comparison DataFrame with accuracy, F1, cost, latency per model.
    """
    from sklearn.metrics import accuracy_score, f1_score

    if models is None:
        models = ["sonnet", "haiku", "gemini"]

    results = []
    for model in models:
        print(f"\n--- Benchmarking {model} on {len(texts)} tickets ---")
        predictions = batch_classify(texts, taxonomy, model)
        pred_labels = [p["category"] for p in predictions]
        latencies = [p.get("latency_s", 0) for p in predictions]

        acc = accuracy_score(true_labels, pred_labels)
        f1 = f1_score(true_labels, pred_labels, average="weighted", zero_division=0)

        results.append({
            "model": model,
            "model_id": MODEL_MAP.get(model, model),
            "accuracy": round(acc, 4),
            "f1_weighted": round(f1, 4),
            "avg_latency_s": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "total_tickets": len(texts),
            "errors": sum(1 for p in predictions if p["category"] in ("error", "parse_error")),
        })

    return pd.DataFrame(results)
