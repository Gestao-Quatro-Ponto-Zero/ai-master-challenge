# Sales Playbook — validated against the data

Every practice below was tested against the 6,711 closed deals in the lake (snapshot 2017-12-31). Practices that *sounded* right but failed validation are listed at the bottom — knowing what to ignore is half the playbook.

## 1. Revenue comes from deal mix and volume, not close rate

Win rate is ~63% for everyone — the spread between the best and worst *revenue* quartile of agents is not how often they win, it's **what** they sell:

| Agent revenue quartile | Win rate | Avg won deal | Premium product mix* | Revenue |
|---|---|---|---|---|
| Q1 (top 8 agents) | 63% | $2,728 | **53%** | $4.27M |
| Q2 | 63% | $2,513 | 45% | $2.41M |
| Q3 | 65% | $2,262 | 38% | $1.85M |
| Q4 (bottom 8) | 63% | $1,646 | **33%** | $1.48M |

*Premium = MG Advanced, GTX Pro, GTX Plus Pro, GTK 500 (list ≥ $3,393).
**Coaching action:** push premium-series conversations. The odds of winning a $5,482 deal are the same as a $55 deal (60–65% everywhere). There is no "safer" cheap deal.

## 2. The winnable window: day 14 to day 138

Won-cycle distribution (14–138d) ≈ bell curve centered at **~80 days** (σ ≈ 30), plus a separate fast-close spike under 28 days. Within the window, win rate never drops below 65% in any age bucket — it actually *rises* to 70–80% at the long end.

- **Do not "warm-check" a mid-window deal into a kill.** Age inside the window is not a negative signal.
- **First 14 days are natural triage:** half of all losses happen there. A deal that survives has ~69% odds.
- **Hard line at 138 days:** no deal in history ever won past it. Close/recycle — signed off as a scorer rule.

## 3. Zombie hygiene is a real behavior gap

Top-revenue agents carry 78% zombie share in their open pipeline; bottom quartile carries **89%**. Weekly recycling of >138d deals frees capacity and fixes forecast inflation (81% of all open Engaging deals are past the line today).

## 4. Prospecting routing is misaligned

25% of the 500 untriaged Prospecting leads (123 deals) sit with bottom win-rate-quartile agents, while the highest-priority leads (GTX Plus Pro, ~$3.7k priority value) are spread arbitrarily. Route by `priority_value` in `data/lake/prospecting_enriched.csv`.

## 5. What makes a zombie (vintage-controlled: deals engaged before 2017-08-15)

Baseline: 22% of same-vintage deals became zombies (open past 138d). The factors:

| Factor | Zombie signal |
|---|---|
| **No account attached** | Zombies: 32% have an account. Same-vintage closed deals: **100%**. No deal in history closed without an account — attachment is a prerequisite, not hygiene. |
| **Manager/region process** | West (Celia Rouche 28%, Summer Sewald 25%) and Cara Losch 25% vs 17–18% elsewhere — a coachable process gap, not individual failure. |
| **GTK 500 flagship** | 44% zombie rate (vs ~21% all others). The $26.8k product needs its own sales process. |
| **High win-rate agents** | Worst zombie rates (29–31%) belong to top win-rate agents (Hayden Neloms, Wilburn Farren, Boris Faz) — they cherry-pick and abandon; win rate rewards it. |

Product, sector and value are otherwise flat (~21%) — zombie formation is about **workflow discipline**, not deal quality.

## Tested and rejected (do NOT put in the playbook)

| Claimed practice | What the data says |
|---|---|
| "Focus on the right sectors/segments" (firmographic ICP) | Win rate flat 61–66% across all sectors, sizes, regions |
| "Convert in 2 weeks or close it" | Inverted — survivors of 14d win at 69%, rising with age |
| "CRM hygiene drives performance" | Account fill rate anti-correlates with win rate (-0.55); it matters for visibility, not for winning |
| "Top closers should get the leads" | Win-rate spread (55–70%) is worth less than premium-mix spread; revenue-Q1 agents are the premium sellers, not the highest win rates |
| "Segment by account/agent/product win-rate history" | Looked promising in-sample (account spread 53–75%) but **failed the time-split backtest**: AUC 0.49 (coin flip), account win rates correlate **-0.17** across periods — pure noise mean-reverting. The scorer deliberately excludes it. |
| "Fresh accounts convert better (74% on first 10 deals)" | Observed in-sample, but given the above, treat as unvalidated until it survives an out-of-time test |

## Missing metrics (instrumentation gaps — needed to go further)

The CRM has **no activity, contact, objection, or stage-transition data**. To validate *why* deals stall or how objections are overcome, instrument:
1. Per-stage timestamps (Prospecting→Engaging transition date is not recorded)
2. Activity log (calls/emails/meetings per deal) — the true "buying signal" source
3. Contact roles (champion/decision-maker present?)
4. Loss reason codes
5. Quote/discount request events (price signal on lost deals is invisible today: lost `close_value` is always 0)
