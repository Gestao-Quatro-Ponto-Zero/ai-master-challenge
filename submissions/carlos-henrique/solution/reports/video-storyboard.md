# JourneyGraph Video Storyboard

## Storyboard

| Timestamp | Screen | Route | User action | Narration objective | Visual focus | Cursor movement | Transition | Risk | Fallback |
|---|---|---|---|---|---|---|---|---|---|
| 00:00–00:20 | Executive Overview | `/` | Start on loaded page; no interaction | State the fragmented-data problem and product promise | Title, governed pipeline, top metrics | Park outside content | Hard cut from title card | Page still loading | Hold on title card, then restart clip |
| 00:20–00:40 | Executive Overview | `/` | Point once to evidence pipeline | Explain why joins and terminal labels fail | Pipeline from raw data to experiment design | One slow horizontal move | In-page continuation | Cursor covers text | Keep cursor in page margin |
| 00:40–01:05 | Executive Overview | `/` | No scrolling; metrics already visible | Establish fixed snapshot and headline reconciliation | Processed, usable, quarantined, journeys | Two deliberate points, then park | Navigation click | Metric outside viewport | Use validated screenshot `01-executive-overview.png` |
| 01:05–01:25 | Data Quality | `/quality` | Open route; do not change filters | Separate MAIN, STRICT, and quarantine | Quality cards and warning boundary | One point to population split | Navigation click | Slow route load | Use screenshot `02-data-quality.png` |
| 01:25–01:50 | Journey Explorer | `/journeys` | Select the recurrent-churn demo profile only if already visible | Show recurrence, reactivation, anonymity, and ordered evidence | Profile alias and event timeline | One selection, then vertical trace | Navigation click | Selection misses or page shifts | Keep default profile and narrate scope; use screenshot `03-journey-explorer.png` |
| 01:50–02:15 | JourneyGraph | `/graph` | Keep default bounded graph; optionally select one visible node | Explain promotion gates and descriptive semantics | Bounded nodes/edges and evidence panel | One slow node selection | Navigation click | Graph animation or dense view | Do not interact; use screenshot `04-journeygraph.png` |
| 02:15–02:35 | Review Queue | `/watchlist` | Open first evidence item already in view | Show deterministic rule, evidence, and manual disposition | Queue label, rule explanation, boundary text | One click and park | Navigation click | Panel below fold | Use screenshot `05-watchlist.png` and narrate no action |
| 02:35–02:50 | Experiment Lab | `/experiments` | Select the ready-for-review design only if stable | Distinguish readiness from result | Status distribution and `UNTESTED` label | One selection | Navigation click | Wrong design selected | Keep overview distribution; use screenshot `06-experiment-lab.png` |
| 02:50–03:05 | Governance | `/governance` | No interaction | Close with privacy, causal, runtime, and human boundaries | Governance controls and cutoff | Park cursor in margin | Fade to final title | Text below fold | Use screenshot `07-governance.png` |

## Navigation Rules

- Preload the seven routes in order before recording.
- Use browser navigation or the stable application menu; do not type routes on camera.
- Keep zoom at 100% and avoid scrolling unless the verified viewport requires one controlled movement.
- The guided demo may be open in another preparation tab, but the recording must not depend on it.
- If any interaction becomes unstable, narrate over the validated screenshot rather than improvising.

## Evidence Boundary

The storyboard demonstrates decisions and validated product states. It does not instruct the recorder to execute a customer action, an experiment, a deployment, or any external publication step.
