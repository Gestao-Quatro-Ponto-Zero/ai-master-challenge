# JourneyGraph External Link Registry

## Registry

| Link ID | Purpose | Current value | Required before | Owner | Validation method | Status |
|---|---|---|---|---|---|---|
| LINK-001 | Repository | `https://github.com/acarloshenrique/ai-master-challenge.git` | Pull Request and submission | Carlos Henrique | `git remote -v`, then clean-browser repository access | VALIDATED |
| LINK-002 | Public demo | `[PUBLIC_DEMO_URL_PENDING]` | Video description, PR, and form | Carlos Henrique | Open root and all routes in clean desktop/mobile sessions | PENDING_USER_ACTION |
| LINK-003 | Video | `[VIDEO_URL_PENDING]` | PR and form | Carlos Henrique | Verify playback, visibility, audio, subtitles, and thumbnail | PENDING_USER_ACTION |
| LINK-004 | Pull Request | `[PR_URL_PENDING]` | Submission form | Carlos Henrique | Open PR, verify branch/base, diff, checklist, and public access | PENDING_USER_ACTION |
| LINK-005 | Submission form | `[SUBMISSION_FORM_CONFIRMATION_PENDING]` | Final submission record | Carlos Henrique | Review entered fields and preserve confirmation evidence | PENDING_USER_ACTION |
| LINK-006 | LinkedIn post, if applicable | `[LINKEDIN_URL_PENDING_IF_APPLICABLE]` | Optional communication | Carlos Henrique | Open post from clean session and verify wording/visibility | NOT_APPLICABLE |

## Source Verification

`git remote -v` on the Phase 10C baseline confirmed:

- `origin`: `https://github.com/acarloshenrique/ai-master-challenge.git`
- `upstream`: `https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge.git`

No remote was changed. The repository value above identifies the candidate's configured origin; the branch, Pull Request, and submission destinations still require user verification.

## Replacement Rules

1. Replace a placeholder only after the external resource exists.
2. Validate the final URL from a clean browser session.
3. Confirm permissions and visibility match the submission requirement.
4. Update every dependent draft in the same review pass.
5. Re-run `validate_final_submission.py` and expect external-link warnings to decrease.

## Publication Boundary

Only LINK-001 has a proved current value. All creation, upload, publication, and form actions remain outside this phase.
