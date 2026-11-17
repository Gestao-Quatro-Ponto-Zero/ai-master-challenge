# RavenStack churn app

The visual and conversational interface for the G4 AI Master challenge 001 (RavenStack churn).
It reads the SQLite database built by `../sql/build_db.py` (read-only). Every number on screen
and in the analyst's answers traces to SQL you can inspect.

It started as a copy of a previous project of mine (Veta), used as reference code only;
nothing from that project's dataset stays. The contract is `ISA.md`; human decisions are in
`../../process-log/decisions.md` (D20–D46).

**Online:** https://ravenstack-churn.vercel.app. Log in as `avaliador@ravenstack.app`; the evaluator password is shared with the submission.

## What it does

- **Overview and three screens** (D27–D44): churn over time, what it is associated with (industry,
  source, country, reason, plan, billing, trial) and support and product usage. Global filters apply
  to every screen; each chart shows its SQL.
- **Drill-down** (D46.1): click a bar or slice to open that slice: its size, the accounts in it against
  the rest of the base (revenue, support, usage), its breakdown by every other attribute (click again to
  go one level deeper), a cross of two attributes and the records.
- **Analyst** (DeepSeek): a chat on every screen. Each answer cites the SQL behind it, and follow-ups keep
  the conversation's context.
- **My screens** (D46.2): create a screen, ask the analyst for an analysis in plain Portuguese, and the
  charts it makes stay on the screen with their SQL.
- **Marked charts and the presentation** (D44–D46.3): mark any chart (screens, drill-down, my screens,
  chat). The app then builds a Minto-pyramid deck (.pptx) from the marks, the audience, the brief and the
  conversations and screens you pick as context. Every number the AI writes is checked against the SQL.
  Earlier builds stay downloadable.

## Run locally

```bash
bun install
cp .env.example .env      # fill LLM_API_KEY, WAREHOUSE_PATH, AUTH_* (password ≥ 8 chars)
bun run dev -- -p 3100 -H 127.0.0.1
```

Then open http://127.0.0.1:3100 and log in as `<AUTH_USERNAME>@ravenstack.app`.

## Deploy (Vercel)

`vercel deploy --prod` from this folder. Before the first deploy, copy the RavenStack database
to `data/ravenstack.db`: it ships inside every function and is never committed.

On Vercel the app DB (logins, conversations, marks, screens, decks) is an AES-GCM-encrypted
SQLite snapshot in a private Vercel Blob (`src/engine/estado.ts`, D46.4).

The deploy needs these environment variables: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`,
`AUTH_USERNAME`, `AUTH_PASSWORD`, `AUTH_SECRET`, `STATE_KEY` and `BLOB_READ_WRITE_TOKEN`. Linking
the Blob store adds the last one.

## Checks

```bash
bun run typecheck && bun run lint
# need WAREHOUSE_PATH:
bun run visao-test && bun run tela1-test && bun run tela2-test && bun run tela3-test
bun run marcados-test && bun run deck-marcados-test && bun run recorte-test && bun run telas-test
bun run estado-test
bun run ask "..."          # one question to the analyst, from the terminal
```

Scripts run under node/tsx because `better-sqlite3` is a native addon.
