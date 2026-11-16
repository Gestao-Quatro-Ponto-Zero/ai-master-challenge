# RavenStack churn app

The visual and conversational interface for the G4 AI Master challenge 001 (RavenStack churn).
It reads the SQLite database built by `../sql/build_db.py` (read-only) and shows the churn
overview plus a chat analyst whose every answer traces to SQL you can inspect.

It started as a copy of a previous project of mine (Veta), used as reference code only;
nothing from that project's dataset stays. The contract is `ISA.md`; human decisions are in
`../../process-log/decisions.md` (D20–D26).

## Run locally

```bash
bun install
cp .env.example .env      # fill LLM_API_KEY, WAREHOUSE_PATH, AUTH_* (password ≥ 8 chars)
bun run dev -- -p 3100 -H 127.0.0.1
```

Then open http://127.0.0.1:3100 and log in as `<AUTH_USERNAME>@ravenstack.app`.

## Checks

```bash
bun run typecheck
bun run dashboard-test     # needs WAREHOUSE_PATH
bun run ask "..."          # one question to the analyst, from the terminal
```

Scripts run under node/tsx because `better-sqlite3` is a native addon.

## Status

Phase 1 (data layer, analyst, overview) is done. Phase 2 (the five dashboard screens) and
phase 3 (deploy with an evaluator login) are open; see `ISA.md`.
