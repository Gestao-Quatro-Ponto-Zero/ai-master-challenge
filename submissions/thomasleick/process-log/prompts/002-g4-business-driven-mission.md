# Prompt reference 002 — G4 business-driven investigation

**Date:** 2026-10-21  
**AI tool:** Codex (OpenAI), using local shell, Python, Docker Compose and Playwright browser tooling.  
**Human authorization:** User supplied the autonomous scoped mission to research public G4 business teaching, independently challenge the existing analysis, implement a business-oriented investigation in the existing four chapters, run tests, validate Docker/browser behavior and produce a consolidated report. All source/project edits were constrained to this candidate package. No Git or publication effects were authorized.

Representative user prompt excerpt: “The goal is to extract the maximum defensible business value from the available evidence.” The mission explicitly required public G4 sources, all five tables, cohort scrutiny, hypothesis ranking, executive answers, implementation and continuous checkpoints.

## Actual iterations recorded

- Recomputed business diagnostics from the five original source files and compared labels, cohort candidates, usage intervals, support and contract-row economics.
- Integrated the independent outputs into FastAPI and the existing React narrative, preserving the four chapters and prior reports.
- Browser viewport checks found a small-screen Chapter 03 account-candidate badge extending beyond a 320px page; added a mobile-only stacked header and verified all chapters at 320×568 and 390×844.
- The final scenario was submitted in the running browser. Its assumed lift remained explicitly hypothetical; because monthly value was unset, the displayed value and net remained UNKNOWN.
- Ruff was absent from the host, so the pinned tool in the API test image was used. The first whole-analysis scan identified unused locals/import and compressed statements; these were removed/expanded, then both analysis test suites and Ruff passed.

## Errors and corrections

- A navigation click through an accessibility reference timed out after viewport resize. The UI was rechecked using the live DOM and chapter controls; the issue was with the browser locator's stability wait, not the application.
- The first viewport-width comparison used `clientWidth`, which excludes the vertical scrollbar; subsequent overflow assertions correctly compared document scroll width with `innerWidth`.
- The first final API extraction used the wrong JSON key and returned KeyError; it was changed to the response contract's `labels.any_label_disagreement_accounts` and returned 401.
- One frontend test command was first run from `solution/` rather than `solution/apps/web`; rerunning in the package's web directory passed.
- One Compose status command was first run from the candidate root, which has no Compose file; rerunning from standalone `solution/` with the correct project name confirmed both services healthy.
- The browser screenshot tool denied writes to the candidate package because its allowed roots are configured under LeickOS. No screenshot file was written outside scope. The browser tool generated its managed accessibility snapshots in its configured `.playwright-mcp` area under the current tool workspace; these are tool artifacts, not project source edits, and were preserved.

No external G4 framework or internal business decision was invented. Recommendations, labels and scenario values are the agent's evidence-based interpretation; the human provided workspace/effect boundaries and the autonomous execution authorization.
