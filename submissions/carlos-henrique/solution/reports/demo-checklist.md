# JourneyGraph Demo Checklist

## PRE-RECORDING

- [ ] Confirm final approved commit hash and clean working tree.
- [ ] Run `npm ci`, `npm run build:data`, `npm run lint`, `npm run typecheck`, `npm run test`, and `npm run build`.
- [ ] Run Playwright and confirm 36/36 scenarios.
- [ ] Start the production application and check all seven demo routes.
- [ ] Confirm browser zoom is 100% at 1920×1080.
- [ ] Use a clean browser session with no personal tabs or notifications.
- [ ] Confirm no internal account keys, PII, private paths, or credentials are visible.
- [ ] Reconcile displayed metrics with [final-metric-snapshot.md](final-metric-snapshot.md).
- [ ] Confirm cutoff `2024-12-31T19:00:00` is visible where expected.
- [x] English script prepared.
- [x] Portuguese supporting script prepared.
- [x] Draft subtitles prepared.
- [x] Thumbnail specification prepared.
- [ ] Test microphone, room noise, and input level.
- [ ] Rehearse with a timer; target 2:45–3:15.

## RECORDING

- [ ] Start on the fully loaded Executive Overview.
- [ ] Follow the approved route order and storyboard.
- [ ] Use only planned interactions.
- [ ] Keep cursor movement deliberate and park it during explanations.
- [ ] State historical, descriptive, human-review, and experiment-status boundaries accurately.
- [ ] Confirm no console error or broken state appears.
- [ ] Hold the Governance closing frame for two seconds.
- [ ] Save the master as `journeygraph-demo-en-1080p-v1.mp4`.

## POST-RECORDING

- [ ] Verify final duration.
- [ ] Watch the entire master file.
- [ ] Trim opening and closing dead time.
- [ ] Normalize audio without clipping.
- [ ] Synchronize English subtitles to the final edit.
- [ ] Review the Portuguese subtitle option if it will be published.
- [ ] Add intro and final title only.
- [ ] Export 1920×1080 at 30 fps.
- [ ] Play the exported file from start to finish.
- [ ] Confirm metrics, cutoff, privacy, navigation, audio, and claims.
- [ ] Produce thumbnail according to the approved specification.

## PRE-UPLOAD

- [ ] Select the user-approved hosting platform.
- [ ] Confirm filename, title, description, thumbnail, and subtitle language.
- [ ] Replace description placeholders only with verified destinations.
- [ ] Confirm intended visibility and permissions.
- [ ] Obtain explicit user authorization to upload.

## POST-UPLOAD

- [ ] Open the video from a clean browser session.
- [ ] Verify playback, resolution, audio, subtitles, thumbnail, and visibility.
- [ ] Record the verified URL in `external-link-registry.md`.
- [ ] Add the URL to the Pull Request description and submission form.
- [ ] Re-run the final-submission validator after links are updated.

## Status

Preparation assets are `READY`. Recording, editing, upload, link visibility, and link verification are `PENDING_USER_ACTION`.
