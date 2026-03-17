---
name: CRM Dashboard Scoring System
description: Account Rating and Kill Score scoring engines implemented for G4 Business CRM Dashboard
type: project
---

Account Rating and Kill Score scoring systems have been implemented for the G4 Business CRM Dashboard.

**Why:** The dashboard needs two scoring dimensions — Account Rating (account health based on deal history, 0-100 scale) and Kill Score (identifies deals to abandon, 0-100 scale). These are distinct from the pre-existing Deal Smell and Killer Score in scores.ts.

**How to apply:**
- `lib/data.ts` contains all 8800 deals from CSV (4238 Won, 2473 Lost, 1589 Engaging, 500 Prospecting). GTXPro normalized to "GTX Pro" in deals. Uses `as any` cast to avoid TS union complexity limit.
- `lib/accountRating.ts` — 6-signal weighted rating. Reference date: 2018-01-01. Cached.
- `lib/killScore.ts` — 5-signal weighted score for active deals. Reference date: 2018-01-01. Cached.
- `lib/scores.ts` re-exports both modules. Existing Deal Smell / Killer Score functions preserved.
- PRODUCTS array still has legacy GTXPro entry for backward compat.
