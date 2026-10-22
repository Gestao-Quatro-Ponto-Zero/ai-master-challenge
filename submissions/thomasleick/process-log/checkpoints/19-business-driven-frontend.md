CHECKPOINT: 19 — Business investigation frontend
STATUS: PASS
OBJECTIVE: Integrate additional business findings into the existing four chapters without creating a disconnected page or changing the historical narrative definitions.
WORK COMPLETED: Added a direct Question 1 answer; four-label segment filter with Wilson intervals; support comparison by selectable label with account-grain means, denominators, missing satisfaction counts and ticket priority; adoption interval sensitivity, first-use proxy, alternative-label use table, signup/earliest-listed-subscription cohort diagnostics without retention rates; row-grain financial field observations; specific account reconciliation candidates; dynamic recommendations and hypothesis evidence priority. Added explicit focus styles and responsive layout styles; existing reduced-motion preference remains respected.
FILES CREATED: This checkpoint.
FILES MODIFIED: `solution/apps/web/src/App.tsx`; `src/contracts.ts`; `src/lib/api.ts`; `src/App.test.tsx`; `src/styles.css`.
COMMANDS EXECUTED: `npm test -- --run`; `npm run build` from `solution/apps/web`.
TESTS EXECUTED: Vitest UI tests and TypeScript production build.
TEST RESULTS: 6 tests passed across 2 test files. TypeScript/Vite build passed; Vite reports the existing-style bundle-size warning, with the main JS bundle at 662.02 kB minified (186.41 kB gzip). An initial assertion expected wording absent from the screen; updated the assertion to match the product copy and reran successfully.
EVIDENCE LEVEL: UNIT / SYNTHETIC UI FIXTURE, STATIC.
BUSINESS FINDINGS: Chapter 02 now allows alternative label comparisons for segments and support, shows both ticket-grain and account-cluster satisfaction, exposes uptake/censoring caveats and cohort label composition. Chapter 03 includes accounts selected for data review and clearly disclaims future risk; subscription row fields remain generic values and recurring loss remains UNKNOWN. Chapter 04 shows evidence/counterevidence and actions.
UNKNOWN: Actual responsive browser rendering and integrated API requests remain pending the project-only Docker rebuild and browser QA.
BLOCKERS: None.
RISKS: The monolithic App remains; the 662.02 kB main JS warning persists. Wide evidence tables rely on their scroll wrapper on small screens.
NEXT STEP: Run current analytics/API/frontend under standalone Compose, exercise all chapters and scenario interaction in the browser, then write the consolidated executive report.
