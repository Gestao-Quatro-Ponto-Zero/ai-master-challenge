<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# RavenStack churn app — project conventions

The app for the G4 AI Master challenge 001 (RavenStack churn). `ISA.md` is the contract;
its Criteria are the tests. Human decisions live in `../../process-log/decisions.md`.

- **One engine, two faces.** Chat and the MCP server consume the same tool layer (`src/engine/tools.ts`); a new capability is a tool, added once.
- **Grounded, never guessed.** Every answer traces to SQL the user can inspect; no arithmetic in prose.
- **Database is read-only.** Built by `../sql/build_db.py`; touch it only through `src/engine/warehouse.ts`.
- **Definitions are the human's (D20–D24):** churn = `churn_events`; accounts as headline, events as volume;
  active month = a subscription in force; each number on its own identifier (account or subscription).
- **Dates are TEXT `YYYY-MM-DD HH:MM:SS`.** Never filter with a bare `<= 'YYYY-MM-DD'` upper bound.
- **Scripts run under node/tsx, NOT the bun runtime** (`better-sqlite3` is native). Use `bun run <script>`.
- **bun for tooling, never npm/npx.** Secrets only in `.env` (git-ignored).
