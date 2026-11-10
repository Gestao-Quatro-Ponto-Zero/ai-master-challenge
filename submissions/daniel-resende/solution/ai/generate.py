"""Generate the texts with the headless Claude Code CLI (subscription login, no API key).

    python generate.py --limit 5   # five items: three deals, one briefing, one manager
    python generate.py             # everything, resuming from what is stored

The CLI runs from an empty directory with a neutral name, so no project
instruction file is loaded. Each answer is rendered and checked before it is
stored; a refused text is not stored and the run says why.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check as C  # noqa: E402
import facts as F  # noqa: E402
from render import render  # noqa: E402

HERE = Path(__file__).resolve().parent
SCHEMA = HERE / "schema.json"
PROMPT = HERE / "prompt.md"
TEXTOS = HERE / "textos.json"
MODEL = "sonnet"  # short wording tasks, speed matters; the envelope reports the exact name
PER_CALL = {"deal": 12, "briefing": 8, "manager": 100}
MAX_PARALLEL = 2
RUN_LIMIT_S = 12 * 60
CALL_TIMEOUT_S = 300
COMMAND = ('claude -p --setting-sources "" --tools "" --no-session-persistence '
           f'--model {MODEL} --json-schema <schema> --output-format json')


def shell_date():
    """Today's date from the `date` command, never from the Python clock."""
    return subprocess.run(["date", "+%Y-%m-%d"], capture_output=True, text=True,
                          check=True).stdout.strip()


def call_cli(items, workdir):
    """One CLI call. Returns (structured_output, models_reported, seconds)."""
    stdin = (PROMPT.read_text(encoding="utf-8") + "\n\n# Itens\n\n"
             + json.dumps([{"id": i["id"], "kind": i["kind"], "facts": i["facts"]} for i in items],
                          ensure_ascii=False, indent=1))
    cmd = ["claude", "-p", "--setting-sources", "", "--tools", "", "--no-session-persistence",
           "--model", MODEL, "--json-schema", json.dumps(json.loads(SCHEMA.read_text())),
           "--output-format", "json"]
    # The login of the subscription is the only credential: drop any API key from the child's env.
    env = {k: v for k, v in os.environ.items()
           if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    t0 = time.monotonic()
    proc = subprocess.run(cmd, input=stdin, capture_output=True, text=True, cwd=workdir,
                          env=env, timeout=CALL_TIMEOUT_S)
    secs = time.monotonic() - t0
    if proc.returncode != 0:
        raise RuntimeError(f"claude exit {proc.returncode}: {proc.stderr.strip()[:300]}")
    env_json = json.loads(proc.stdout)
    if env_json.get("is_error") or not isinstance(env_json.get("structured_output"), dict):
        raise RuntimeError("no structured_output in the envelope")
    return env_json["structured_output"], sorted(env_json.get("modelUsage", {})), secs


def build_entry(item, parts, model, date, sha, batch):
    """Render the parts and run the contract's checks. Returns (entry, errors)."""
    out = {}
    for name, template in parts.items():
        try:
            out[name] = {"template": template, "text": render(template, item["facts"])}
        except KeyError as e:
            out[name] = {"template": template, "text": ""}
            return None, [f"{item['id']}.{name}: placeholder {e} not in facts"]
    entry = {"id": item["id"], "kind": item["kind"], "target": item["target"], "parts": out,
             "facts": item["facts"],
             "provenance": {"model": model, "model_requested": MODEL, "generated_on": date,
                            "prompt_sha256": sha, "batch": batch}}
    errs = C.check_entry(entry, TARGETS, NAMES, sha)
    return (None if errs else entry), errs


def run_batch(items, batch, date, sha, workdir):
    """Two attempts at the call; then the per-item checks."""
    last = None
    for attempt in (1, 2):
        try:
            answer, models, secs = call_cli(items, workdir)
            break
        except Exception as e:  # noqa: BLE001 - the run reports and stops, never crashes mid-write
            last = e
            print(f"batch {batch} attempt {attempt} failed: {e}", flush=True)
    else:
        return {"failed": str(last), "entries": [], "refused": [], "secs": 0, "models": []}
    model = ", ".join(models) or MODEL
    by_id = {r.get("id"): r.get("parts") for r in answer.get("items", [])}
    entries, refused = [], []
    for item in items:
        parts = by_id.get(item["id"])
        if not isinstance(parts, dict):
            refused.append((item["id"], ["missing from the answer"]))
            continue
        entry, errs = build_entry(item, parts, model, date, sha, batch)
        if entry:
            entries.append(entry)
        else:
            refused.append((item["id"], errs))
    return {"failed": None, "entries": entries, "refused": refused, "secs": secs, "models": models}


def load_stored(sha):
    if not TEXTOS.exists():
        return []
    doc = json.loads(TEXTOS.read_text(encoding="utf-8"))
    if (doc.get("meta") or {}).get("prompt_sha256") != sha:
        print("stored texts were made with another prompt: discarded")
        return []
    return doc.get("texts", [])


def save(texts, sha):
    order = {k: n for n, k in enumerate(TARGETS)}
    texts = sorted(texts, key=lambda t: order.get(t["id"], 10**6))
    meta = {"monday": "2018-01-01", "score_file": F.DEFAULT_SCORE,
            "prompt_file": "solution/ai/prompt.md", "prompt_sha256": sha, "command": COMMAND,
            "model_requested": MODEL,
            "model_note": "sonnet chosen for speed: short wording tasks; the exact model name is in each provenance"}
    TEXTOS.write_text(json.dumps({"meta": meta, "texts": texts}, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    sha = hashlib.sha256(PROMPT.read_bytes()).hexdigest()
    date = shell_date()
    stored = load_stored(sha)
    done = {t["id"] for t in stored}

    if limit:
        wanted = [t for t in F.pick_examples(TARGETS)][:limit]
        wanted = [t for t in wanted if t["id"] not in done]
    else:
        wanted = [t for t in TARGETS.values() if t["id"] not in done]
    batches = []
    for kind in ("deal", "briefing", "manager"):
        group = [t for t in wanted if t["kind"] == kind]
        for n in range(0, len(group), PER_CALL[kind]):
            batches.append(group[n:n + PER_CALL[kind]])
    first = max([t["provenance"]["batch"] for t in stored], default=0) + 1
    print(f"{len(wanted)} items to generate in {len(batches)} calls ({len(stored)} already stored)")

    workdir = tempfile.mkdtemp(prefix="neutral-")  # empty, neutral name: no instruction file is loaded
    t_start = time.monotonic()
    refused_all, failures, new, log = [], 0, [], []
    pending = list(enumerate(batches, first))
    with ThreadPoolExecutor(MAX_PARALLEL) as pool:
        while pending and failures == 0 and time.monotonic() - t_start < RUN_LIMIT_S:
            wave, pending = pending[:MAX_PARALLEL], pending[MAX_PARALLEL:]
            futures = [pool.submit(run_batch, b, n, date, sha, workdir) for n, b in wave]
            for (n, b), fut in zip(wave, futures):
                r = fut.result()
                if r["failed"]:
                    failures += 1
                    continue
                new += r["entries"]
                refused_all += r["refused"]
                log.append((n, len(b), r["secs"], r["models"]))
                print(f"batch {n}: {len(b)} items, {r['secs']:.1f} s, model {r['models']}, "
                      f"stored {len(r['entries'])}, refused {len(r['refused'])}", flush=True)
            save(stored + new, sha)  # keep what passed, after every wave
    save(stored + new, sha)
    if failures or pending:
        print(f"STOPPED: {failures} failed batch(es), {len(pending)} batch(es) not started")
    for rid, errs in refused_all:
        print("REFUSED", rid, "|", "; ".join(errs))
    print(f"stored now {len(stored) + len(new)}; refused {len(refused_all)}; "
          f"total {time.monotonic() - t_start:.1f} s")
    if limit:
        for e in new:
            print("\n" + e["id"], json.dumps(e["facts"], ensure_ascii=False))
            for name, p in e["parts"].items():
                print(f"  [{name}] template: {p['template']}\n  [{name}] text:     {p['text']}")
    return 1 if failures else 0


TARGETS = F.build_all()
NAMES = C.load_names()

if __name__ == "__main__":
    sys.exit(main())
