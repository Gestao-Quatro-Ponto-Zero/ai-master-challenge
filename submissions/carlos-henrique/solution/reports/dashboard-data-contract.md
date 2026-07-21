# Dashboard Data Contract

## Contract boundary

`solution/scripts/build_dashboard_data.py` is the only authorized producer of application data. It reads frozen Phase 3-8 artifacts, verifies 25 SHA-256 input hashes, and writes exactly 15 UTF-8 JSON files to `solution/app/public/data/`. All files use the fixed historical cutoff `2024-12-31T19:00:00`.

The builder is deterministic: stable sorting, fixed sampling, fixed labels, finite-number validation, and canonical JSON serialization produce identical bytes across repeated runs.

## Inventory and grain

| File | Grain / primary content | Size (bytes) |
|---|---|---:|
| `overview.json` | one executive snapshot | 2,420 |
| `quality.json` | one quality snapshot with population summaries | 2,152 |
| `journey_index.json` | filter values and demo-account index | 4,229 |
| `journey_samples.json` | three real anonymous account journey samples | 19,011 |
| `graph_nodes.json` | three bounded graph-mode node lists | 71,038 |
| `graph_edges.json` | three bounded graph-mode edge lists | 53,537 |
| `graph_findings.json` | governed aggregate graph findings | 2,531 |
| `watchlist_summary.json` | aggregate queue/priority snapshot | 2,354 |
| `watchlist_items_demo.json` | bounded anonymous account-rule evidence sample | 297,830 |
| `watchlist_rules.json` | 16 governed rule definitions | 6,117 |
| `experiment_registry.json` | eight experiment cards | 4,069 |
| `experiment_details.json` | eight untested experiment specifications | 74,257 |
| `governance.json` | control checklist, limitations, and prohibited claims | 2,569 |
| `demo_story.json` | eight guided-demo steps | 3,028 |
| `metadata.json` | provenance, source hashes, output contract, and cutoff | 3,894 |

Total serialized volume is 549,036 bytes.

## Shared schema rules

Every root object includes `cutoff` directly or through metadata. Counts are integers, ratios are finite numbers, dates are ISO-8601 strings, statuses use controlled uppercase vocabularies, limitations are arrays of controlled labels, and all provenance paths are repository-relative.

Forbidden fields or values include raw `account_id`, account name, email, feedback text, PII, score, probability, automatic action, causal result, revenue-at-risk/saved attribution, and non-finite numbers.

## View schemas

### Overview and quality

`overview.json` contains `headline_metrics`, `pipeline`, `outcomes`, `business_context`, `limitations`, and provenance. `quality.json` contains MAIN/STRICT coverage, warning indicators, quarantine counts/reasons, backlog guidance, and interpretation boundaries. Quarantine is always a quality population, never a behavioral signal.

### Journey demo

`journey_index.json` defines supported filters and the labels `DEMO_A`, `DEMO_B`, and `DEMO_C`. `journey_samples.json` stores one selected real anonymous account per label, its governed journeys, timeline events, promoted patterns, quality context, outcome, scope, and deterministic explanation.

The internal `account_key` is a salted deterministic analytical key (`acct_*`), not a raw source ID. It exists in local account-level JSON only to preserve evidence joins. The UI and narrative never display it. The demo is capped at three accounts.

### Graph views

Each of `graph_nodes.json` and `graph_edges.json` has a `modes` object with `event-flow`, `pattern-explorer`, and `governance-view`.

Node:
- `id`, `type`, `label`, `properties`.

Edge:
- `id`, `source`, `target`, `type`, `properties`.

Every mode is marked `truncated=true`. Hard limits are 35 nodes and 80 edges. Only promotable ROBUST/SENSITIVE patterns and transitions with `small_sample=false` and same-day dependency other than HIGH are eligible. The initial event-flow UI further limits display to 16 relationships for legibility.

### Watchlist demo

`watchlist_summary.json` contains queue counts, priority counts, unique-account count, associated-MRR context, and warnings. `watchlist_items_demo.json` contains a bounded deterministic sample with anonymous key, queue, rule, discrete P1-P4 priority, four interpretable components, historical metrics, graph evidence, quality, limitations, prohibited actions, and human-review fields. `watchlist_rules.json` contains the 16 versioned rule definitions.

Priority is not a score. Associated MRR is contextual and deduplicated; it is not risk, loss, savings, or causal impact. Quality-review rows are visually and semantically separated from behavioral investigation.

### Experiment detail

`experiment_registry.json` contains eight cards with `experiment_id`, hypothesis, intervention, eligibility, feasibility, primary metric, required sample, duration, approvals, risks, and `causal_status=UNTESTED`. `experiment_details.json` expands eligibility, baselines, MDE/power planning, metrics, SAP, guardrails, stopping rules, ethics, limitations, and provenance.

No assignment, exposure, result, effect, uplift, synthetic outcome, or execution state is present.

### Governance, demo, and metadata

`governance.json` contains privacy, temporal, causal, operational, and language controls with implementation states and limitations. `demo_story.json` contains eight ordered steps with route, title, narrative, evidence, metric, and transition. `metadata.json` records source commit, cutoff, input hashes, output inventory, privacy contract, and deterministic build properties.

## Final SHA-256 manifest

| File | SHA-256 |
|---|---|
| `demo_story.json` | `e1cc78fe616bd7503cfa63157cf86ee4548c199588e63db4a4249bd029dfb918` |
| `experiment_details.json` | `e9331c055c393579fd2c9a7399e9f145ecb7c588c53d90915d76dc58c3a96d37` |
| `experiment_registry.json` | `b7254d28be6704faff7b72c2b9324e36e9d7ffa0485f4a51e38ff265ce8d6651` |
| `governance.json` | `a7c8754c4cd1dc09e1f3fb124b3cc45b3fc9346f136d3222e7c76a182ca380ab` |
| `graph_edges.json` | `9c7152220802d543a1faa1cd6d1369db40ecc0f791de15fbd3c923cdfbf28c36` |
| `graph_findings.json` | `20fe7a21aa315bd83a0f2dde953e0529510606f709590bee9252cafd7df376e4` |
| `graph_nodes.json` | `244e9be7e1d33b623523774910ebad8a83debc24dcfdc4184d56520a926019f6` |
| `journey_index.json` | `8a37542f6885a2a0d86ea8e4499b08f14ec78a46a29bbc1679b369cacb61f76e` |
| `journey_samples.json` | `623ef496a03422fd56e114891a7a6dc9acc7fdc08758b920ff6c659792abaef7` |
| `metadata.json` | `2f6b60eefda25f10bb7eafb8c573cc1b1c200e4c2995049029a3c99b94fb06d2` |
| `overview.json` | `e1115cbfd854a2e04bc6e044bfb1a0e993a614b490ac7528e86faa1e60538e34` |
| `quality.json` | `c877f119f82575e7ba3e9ed50f7c32929ccf0e3f11dee4108b0d170fc99a9e88` |
| `watchlist_items_demo.json` | `8b1404bd48ed282706cba05d9135d9e28a70f9c9f2bf90b62324d6be05dfe370` |
| `watchlist_rules.json` | `f7cbcc79958e4e7e97a84d7b645ecc2b9b2f95bab217cf3e9b085d9fc73d56c2` |
| `watchlist_summary.json` | `898a6bfbd43ba49055b2455b3f5eaa884a9121d7be261371a4cc225afc58c7cb` |

Two consecutive final rebuilds produced zero byte differences across all 15 files.
