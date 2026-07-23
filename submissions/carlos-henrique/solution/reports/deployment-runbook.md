# JourneyGraph Deployment Runbook

## Preconditions

- Final approved commit is available in the chosen remote.
- Working tree and staging are clean.
- Final-submission validation is `PASS_WITH_WARNINGS` only for expected external actions.
- Deployment owner, platform, public-access policy, rollback owner, and monitoring owner are confirmed.
- No secret or credential is required by the application.

## Generic Deployment Steps

1. **Choose platform.** Select a host with supported Next.js 16 and Node.js 20.9+ behavior.
2. **Configure root directory.** Set the project root to `submissions/carlos-henrique/solution/app`.
3. **Configure install command.** Use `npm ci`.
4. **Choose data strategy.** Prefer committed `public/data` snapshots for this fixed demo. If rebuilding, provision Python 3 and `requirements.txt`, then run `npm run build:data` before the app build.
5. **Configure build command.** Use `npm run build` for committed snapshots or `npm run build:data && npm run build` only in a shell/pipeline already validated for command chaining.
6. **Configure output/runtime.** Use the platform's supported Next.js runtime; do not assume a pure static export directory.
7. **Verify Node version.** Pin or confirm Node.js 20.9 or newer.
8. **Validate environment.** Add no secrets. If `NEXT_PUBLIC_DEMO_MODE` is configured, use only the documented non-sensitive value.
9. **Deploy.** Execute only after explicit user authorization.
10. **Smoke-test routes.** Check `/`, `/quality`, `/journeys`, `/graph`, `/watchlist`, `/experiments`, `/governance`, `/demo`, and `/methodology`.
11. **Verify data and console.** Confirm every `/data/*.json` request succeeds and the browser console has no error.
12. **Verify mobile.** Test at least 390×844 and one tablet width; confirm no horizontal overflow.
13. **Verify privacy and claims.** Check aliases, no internal keys, fixed cutoff, descriptive language, manual review, and `UNTESTED` experiments.
14. **Verify links and access.** Open the root URL in a clean browser session and confirm intended visibility.
15. **Record final URL.** Add it to `external-link-registry.md`, then update the video description, PR draft, and form draft.
16. **Revalidate.** Run the final validator after verified URLs replace placeholders.

## Vercel-Compatible Example

This is an example configuration, not evidence that Vercel has been set up:

| Setting | Example |
|---|---|
| Root Directory | `submissions/carlos-henrique/solution/app` |
| Framework Preset | Next.js |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Node.js | Supported 20.x or newer |
| Environment Variables | None required for committed snapshots |

Do not set an output directory manually unless the platform's current Next.js integration requires and documents it.

## Rollback

1. Preserve the last known-good deployment identifier and commit hash.
2. If smoke tests fail, stop link propagation and restore the last known-good deployment.
3. Remove an invalid URL from external drafts or mark it `PENDING_USER_ACTION` again.
4. Record the failure, affected route, browser evidence, and corrective owner.
5. Repeat the complete smoke and privacy review after correction.

## Status

Runbook is `READY`. Platform selection, deployment, URL capture, and external verification are `PENDING_USER_ACTION`.
