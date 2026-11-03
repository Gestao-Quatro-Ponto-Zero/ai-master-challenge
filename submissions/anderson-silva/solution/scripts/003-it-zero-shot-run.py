"""Collect zero-shot answers and embedding vectors for the challenge 002 IT tickets (Dataset 2) through OpenRouter.

Usage:
  python 003-it-zero-shot-run.py <csv> <env-file> <results-dir> {embeddings,jev,jev-order-check} [--limit N]
  python 003-it-zero-shot-run.py <csv> <env-file> <results-dir> embeddings-store [--cache-dir DIR] [--limit N]

Answers are appended to CSV files in <results-dir>, so an interrupted run resumes where it stopped.
embeddings-store keeps the full normalized vectors in <cache-dir> (git-ignored) with a done mask, and also resumes.
The API key is read from <env-file> and never printed.
"""
import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

# Approved by the candidate on 2026-11-02 (audit trail items 121 and 126). Frozen: never tuned on results.
CATEGORY_DESCRIPTIONS = {
    "Hardware": "Problems with, or requests about, physical IT equipment: computers, laptops, monitors, "
                "printers, phones, peripherals and their components.",
    "HR Support": "Human resources matters: employee onboarding and offboarding, personal records, payroll, "
                  "leave, benefits and other HR processes.",
    "Access": "Getting or restoring access to systems, applications, accounts or shared resources: logins, "
              "passwords, account unlocks and user permissions.",
    "Administrative rights": "Requests for elevated or administrator privileges on a computer or system, "
                             "for example to install or configure software.",
    "Storage": "Data storage: disk space, shared drives and folders, storage quotas, backups and file recovery.",
    "Purchase": "Buying or ordering IT equipment, software, licenses or services, including quotes, "
                "approvals and order status.",
    "Internal Project": "Work related to internal company projects: project setup, tasks, timelines, resources "
                        "and coordination between project members.",
    "Miscellaneous": "IT requests that do not fit any of the other categories.",
}
CATEGORIES = list(CATEGORY_DESCRIPTIONS)
JEV_INSTRUCTIONS = "Which IT service desk category does this support ticket belong to?"
EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"
DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
EMBEDDING_MODEL = "openai/text-embedding-3-large"
JEV_MODEL = "typesafe/jev-1.14"
RESULT_FILES = {
    "embeddings": "001-it-embeddings-large-similarities.csv",
    "jev": "002-it-jev-probabilities.csv",
    "jev-order-check": "003-it-jev-order-check.csv",
}
STORE_MODE = "embeddings-store"
STORE_FILES = ("001-it-embeddings-large.npy", "001-it-embeddings-large-done.npy")
EMBEDDING_DIMENSIONS = 3072
SEED = 42
EMBEDDING_BATCH = 128
WORKERS = {"embeddings": 4, "jev": 8, "jev-order-check": 8, STORE_MODE: 4}
ORDER_CHECK_SAMPLE = 2000
# Hard caps per mode, about twice the estimates in audit trail items 111 and 119 (store: twice item 130).
BUDGET_USD = {"embeddings": 0.60, "jev": 2.00, "jev-order-check": 0.20, STORE_MODE: 0.60}
MAX_RETRIES = 6
RETRY_STATUS = {408, 429, 500, 502, 503, 504, 529}
TIMEOUT_SECONDS = 60
MAX_FAILURES = 20


def read_api_key(env_path):
    for line in Path(env_path).read_text().splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() == "OPENROUTER_API_KEY" and value.strip():
            return value.strip()
    raise SystemExit("OPENROUTER_API_KEY is missing in the env file")


def post_json(url, payload, api_key):
    body = json.dumps(payload).encode()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for attempt in range(MAX_RETRIES):
        is_last = attempt == MAX_RETRIES - 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers),
                                        timeout=TIMEOUT_SECONDS) as response:
                result = json.load(response)
            if "error" not in result:
                return result
            if is_last:
                raise RuntimeError(f"API error from {url}: {str(result['error'])[:300]}")
        except urllib.error.HTTPError as error:
            if error.code not in RETRY_STATUS or is_last:
                detail = error.read().decode(errors="replace")[:300]
                raise RuntimeError(f"HTTP {error.code} from {url}: {detail}") from None
        except (urllib.error.URLError, TimeoutError):
            if is_last:
                raise
        time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def embed(texts, api_key):
    result = post_json(EMBEDDINGS_URL, {"model": EMBEDDING_MODEL, "input": texts, "encoding_format": "float"}, api_key)
    ordered = sorted(result["data"], key=lambda item: item["index"])
    vectors = np.array([item["embedding"] for item in ordered], dtype=np.float32)
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors, float(result.get("usage", {}).get("cost") or 0.0), result.get("model", "")


def option_order(row, reverse):
    # Seeded per ticket, so the order does not depend on which tickets run first.
    order = np.random.default_rng([SEED, int(row)]).permutation(len(CATEGORIES))
    return [CATEGORIES[index] for index in (order[::-1] if reverse else order)]


def ask_jev(document, order, api_key):
    payload = {
        "model": JEV_MODEL,
        "state": {"ticket": document},
        "questions": {"category": {
            "type": "choice",
            "instructions": JEV_INSTRUCTIONS,
            "criteria": {name: CATEGORY_DESCRIPTIONS[name] for name in order},
        }},
    }
    started = time.monotonic()
    result = post_json(DECISIONS_URL, payload, api_key)
    latency = time.monotonic() - started
    answer = result["answers"]["category"]
    probabilities = [float(answer["probabilities"].get(name, 0.0)) for name in CATEGORIES]
    cost = float(result.get("usage", {}).get("cost") or 0.0)
    return probabilities, answer.get("choice"), answer.get("confidence"), result.get("model", ""), cost, latency


def select_rows(frame, mode):
    if mode != "jev-order-check":
        return list(frame.index)
    from sklearn.model_selection import train_test_split

    sample, _ = train_test_split(frame.index, train_size=ORDER_CHECK_SAMPLE, stratify=frame["Topic_group"],
                                 random_state=SEED)
    return sorted(sample)


def header_for(mode):
    if mode == "embeddings":
        return ["row"] + CATEGORIES + ["model", "cost_usd"]
    return ["row"] + CATEGORIES + ["choice", "jev_confidence", "first_option", "model", "cost_usd", "latency_s"]


def submit_all(mode, frame, pending, api_key, pool):
    if mode == "embeddings":
        category_texts = [f"{name}: {text}" for name, text in CATEGORY_DESCRIPTIONS.items()]
        category_vectors, category_cost, _ = embed(category_texts, api_key)
        batches = [pending[start:start + EMBEDDING_BATCH] for start in range(0, len(pending), EMBEDDING_BATCH)]
        futures = {pool.submit(embed, frame.loc[batch, "Document"].tolist(), api_key): batch for batch in batches}
        return futures, category_vectors, category_cost
    reverse = mode == "jev-order-check"
    futures = {}
    for row in pending:
        order = option_order(row, reverse)
        futures[pool.submit(ask_jev, frame.at[row, "Document"], order, api_key)] = (row, order[0])
    return futures, None, 0.0


def rows_from_result(mode, result, key, category_vectors):
    if mode == "embeddings":
        vectors, cost, model = result
        similarities = np.round(vectors @ category_vectors.T, 6)
        share = cost / len(key)
        return [[row, *values, model, share] for row, values in zip(key, similarities)], cost
    probabilities, choice, confidence, model, cost, latency = result
    row, first_option = key
    return [[row, *probabilities, choice, confidence, first_option, model, cost, round(latency, 3)]], cost


def run(mode, frame, pending, api_key, writer, handle):
    written, failures, stopped = 0, 0, False
    with ThreadPoolExecutor(WORKERS[mode]) as pool:
        futures, category_vectors, spent = submit_all(mode, frame, pending, api_key, pool)
        for future in as_completed(futures):
            if future.cancelled():
                continue
            try:
                rows, cost = rows_from_result(mode, future.result(), futures[future], category_vectors)
            except Exception as error:  # keep going; failed rows stay pending for the next run
                failures += 1
                print(f"  falha: {str(error)[:200]}")
                stopped = stopped or failures >= MAX_FAILURES
                rows, cost = [], 0.0
            writer.writerows(rows)
            handle.flush()
            spent, written = spent + cost, written + len(rows)
            if not stopped and spent > BUDGET_USD[mode]:
                print(f"  limite de US$ {BUDGET_USD[mode]:.2f} atingido; parando")
                stopped = True
            if stopped:
                for pending_future in futures:
                    pending_future.cancel()
    return spent, written, failures


def store_embeddings(frame, api_key, cache_dir, limit):
    cache_dir.mkdir(exist_ok=True)
    vectors_path, done_path = (cache_dir / name for name in STORE_FILES)
    vectors = np.lib.format.open_memmap(vectors_path, mode="r+" if vectors_path.exists() else "w+",
                                        dtype=np.float32, shape=(len(frame), EMBEDDING_DIMENSIONS))
    done = np.load(done_path) if done_path.exists() else np.zeros(len(frame), dtype=bool)
    pending = [row for row in frame.index if not done[row]][:limit]
    print(f"{STORE_MODE}: {int(done.sum())} já guardados, {len(pending)} nesta execução -> {vectors_path}")
    batches = [pending[start:start + EMBEDDING_BATCH] for start in range(0, len(pending), EMBEDDING_BATCH)]
    spent, failures, stopped = 0.0, 0, False
    with ThreadPoolExecutor(WORKERS[STORE_MODE]) as pool:
        futures = {pool.submit(embed, frame.loc[batch, "Document"].tolist(), api_key): batch for batch in batches}
        for future in as_completed(futures):
            if future.cancelled():
                continue
            try:
                batch_vectors, cost, _ = future.result()
            except Exception as error:  # failed batches stay pending for the next run
                failures += 1
                print(f"  falha: {str(error)[:200]}")
                stopped = stopped or failures >= MAX_FAILURES
                continue
            vectors[futures[future]] = batch_vectors
            done[futures[future]] = True
            np.save(done_path, done)
            spent += cost
            if not stopped and spent > BUDGET_USD[STORE_MODE]:
                print(f"  limite de US$ {BUDGET_USD[STORE_MODE]:.2f} atingido; parando")
                stopped = True
            if stopped:
                for pending_future in futures:
                    pending_future.cancel()
    vectors.flush()
    return spent, int(done.sum()), failures


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv")
    parser.add_argument("env_file")
    parser.add_argument("results_dir")
    parser.add_argument("mode", choices=list(RESULT_FILES) + [STORE_MODE])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--cache-dir", default="cache")
    args = parser.parse_args()
    frame = pd.read_csv(args.csv)
    api_key = read_api_key(args.env_file)
    if args.mode == STORE_MODE:
        started = time.monotonic()
        spent, stored, failures = store_embeddings(frame, api_key, Path(args.cache_dir), args.limit)
        print(f"Guardados no total: {stored} de {len(frame)} | falhas: {failures} | custo informado: US$ {spent:.4f}"
              f" | tempo: {time.monotonic() - started:.1f} s")
        return
    results_dir = Path(args.results_dir)
    results_dir.mkdir(exist_ok=True)
    path = results_dir / RESULT_FILES[args.mode]
    has_content = path.exists() and path.stat().st_size > 0
    done = set(pd.read_csv(path, usecols=["row"])["row"]) if has_content else set()
    pending = [row for row in select_rows(frame, args.mode) if row not in done][:args.limit]
    print(f"{args.mode}: {len(done)} já respondidos, {len(pending)} nesta execução -> {path}")
    started = time.monotonic()
    with open(path, "a", newline="") as handle:
        writer = csv.writer(handle)
        if not has_content:
            writer.writerow(header_for(args.mode))
        spent, written, failures = run(args.mode, frame, pending, api_key, writer, handle)
    print(f"Gravados: {written} | falhas: {failures} | custo informado: US$ {spent:.4f}"
          f" | tempo: {time.monotonic() - started:.1f} s")


if __name__ == "__main__":
    main()
