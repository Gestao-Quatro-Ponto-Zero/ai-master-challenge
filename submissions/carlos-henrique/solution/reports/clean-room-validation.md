# JourneyGraph Clean-Room Validation

## Strategy

Use a detached temporary Git worktree under `C:\tmp`, apply only the selectively staged Fase 10C patch, install dependencies from the versioned requirement and lock files, and execute the documented gates without copying `.venv`, `node_modules`, `.next`, raw CSV files, or untracked analytical artifacts from the working repository.

The worktree must retain the configured remotes unchanged, perform no network publication, and be removed after evidence is captured.

## Execution

The temporary worktree started from detached `77e5108`, retained the verified `origin` and `upstream` values, and received only selectively staged or explicitly authorized patches. Initial checks confirmed no `.venv`, `node_modules`, `.next`, raw CSV, or tracked build artifact.

| Gate | Result | Evidence |
|---|---|---|
| Python installation | PASS | New Python 3.12.10 venv; `pip check` clean; scientific imports succeeded |
| npm installation | PASS | `npm ci` from the versioned lockfile; 533 packages installed |
| Canonical inputs | PASS | 25/25 builder input hashes matched after repository-scoped EOL rules |
| `build:data` | PASS | 15 outputs; fixed cutoff; all internal validations true; zero byte drift |
| Independent Python suite | PASS | compileall plus 128 tests; two source-presence tests explicitly excluded because raw CSVs are intentionally unversioned |
| Lint | PASS | ESLint returned zero |
| Typecheck | PASS | TypeScript returned zero |
| Vitest | PASS | 19/19 tests |
| Production build | PASS | Ten statically prerendered routes including not-found |
| Playwright | PASS | 36/36 desktop, tablet, and mobile checks |
| Production security | PASS | Next.js `16.2.11` and `sharp 0.35.3` resolved; `npm audit --omit=dev` found zero vulnerabilities |
| Documentation and links | PASS | Four base documents, 67 local links, 15 metrics, seven screenshots |
| Process evidence | PASS | 45/45 checks; internal links intact |
| Runtime independence | PASS | App build used versioned JSON and required no raw CSV, secret, API, database, or external runtime service |

Two tests intentionally validate the five official raw files themselves: `test_five_official_files_are_present` and `test_input_hashes_and_mandatory_figures`. They passed in the primary workspace as part of 130/130, while the clean-room product path passed 128 tests without downloading or copying raw data.

The initial clean-room attempt exposed mixed input EOL expectations and platform-dependent output serialization. The approved correction added submission-scoped EOL rules and explicit CRLF output writing. A newly published `sharp` advisory was resolved with a lockfile-controlled `0.35.3` override. A subsequent Next.js advisory affecting versions below `16.2.11` was closed with the minimum patch release; a fresh `npm ci`, production audit, data rebuild, lint, typecheck, Vitest, production build, and Playwright suite all passed after that update. No application logic changed.

## Result

**Result: PASS.** The evaluator product, deterministic snapshot build, documentation, and governed process evidence are reproducible from versioned inputs after clean installation. The temporary worktree and patch files were removed after evidence capture.

## Limitations

The clean-room does not reconstruct upstream analytics from raw CSVs because repository policy and the Fase 10C prompt prohibit versioning or downloading those sources. That separate source-data gate passed 130/130 in the authorized primary workspace.

No recording, deployment, upload, push, Pull Request, form completion, or submission was performed.
