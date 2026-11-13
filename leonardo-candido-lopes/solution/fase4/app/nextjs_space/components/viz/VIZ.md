# Dashboard kit (`@/components/viz`)

The app has the house dashboard runtime (abacus-viz on Apache ECharts): the same kit DeepAgent uses for its
one-off dashboards, as a React component. Every dashboard / analytics / report page is built with it; Recharts
and Plotly are not used on those pages.

```tsx
'use client';
import { AbacusDashboard, useDashboardData } from '@/components/viz/abacus-dashboard';
import { manifest } from '@/lib/dashboard-manifest';          // a VizManifest object, see the reference below

export default function DashboardPage() {
  const { data, dataAsOf, error } = useDashboardData('/api/dashboard', 60_000);  // re-fetches every 60 s
  return <AbacusDashboard manifest={manifest} data={data} dataAsOf={dataAsOf} className="min-h-screen" />;
}
```

- `app/api/dashboard/route.ts` returns `{ data_as_of: ISO string, data: { <data key>: rows[] } }` with one
  entry per distinct `tile.data` key (aggregate with Prisma `groupBy` / raw SQL, or compute from seeded rows;
  `export const dynamic = 'force-dynamic'`). Rows are flat objects; kpi ≤ 50 rows, table ≤ 500, charts ≤ 2000.
- Each data key is shaped for its tile, at the tile's grain: a ranking (`bar`, `lollipop`) gets one row per
  category, already summed across everything the tile does not split by (a "churn by reason" lollipop has one
  row per reason, not one per reason × region); a trend (`area`) gets one row per period with a field per
  series; a `kpi` row carries its own `delta` and `spark`. Do the aggregation in the route — the kit plots rows
  as given and never merges duplicates. Rows that a manifest `filters` tab slices must carry the filter field
  (e.g. `region`) and include the "All" rows explicitly. Months are a time series, never horizontal bars.
- `<AbacusDashboard>` mounts the runtime inside the page (filters, drawers, themes included); when `data` changes
  only the tiles whose rows changed re-render, so polling is cheap. One dashboard per page.
- Theme: `manifest.theme` — `auto` follows the app's dark mode (the `dark` class on `<html>`: midnight when dark,
  editorial otherwise) and is the default choice for an app with a theme toggle; else `midnight` for a dark app,
  `journal` for a flat white one, `editorial` otherwise. The kit's tokens are scoped to its root; the app's own
  theme and shadcn tokens are untouched. The root paints its own canvas edge to edge, so give it the full content
  width (no padding or max-width wrapper around it).
- The page around it stays quiet: the app shell (sidebar, header) and nothing else — no extra cards, glass,
  gradients, particles or count-up wrappers around the dashboard; the kit owns the hierarchy. Filters are the
  manifest's tabs; if the brief needs a server-side control (date range, account picker), put it in the page
  header and pass it to the route as a query parameter.
- `components/viz/examples/saas_revenue.json` is a complete manifest at the quality bar — read it before writing
  yours. In the reference below, `data/<key>.json` means the `<key>` entry of the route's `data` object; `query`
  is optional text shown in the tile's "View query" drawer (the SQL / Prisma call behind the rows).

# dashboard.json reference
Top level: `title` (the headline insight, a full sentence with the number in it — never "Sales Dashboard"),
`eyebrow` (who/what/when, e.g. "Acme · Q3 2026 business review"), `subtitle` (one sentence on scope and how to
read it), `data_as_of` (ISO 8601), `theme` (`editorial` default — warm paper, serif titles; `journal` — flat
white, condensed grotesk; `midnight` — dark; the kit applies it, a `?theme=` URL param overrides), `sources[]` (`{id,label}`; add `database_connector_id` when the rows came from `query_connector` — the dashboard pane's Refresh re-runs that tile's `queries/<tile>.sql` through it as the viewer), `filters[]`, `colors` (optional
`{category: token}` — the same category keeps the same colour on every tile; tokens: `accent`, `accent-2`,
`accent-3`, `pos`, `neg`, `ink`), `refresh` (optional, see the data plan: `{mode, every_hours}`), `asks[]`
(the checklist, see Accuracy), `tiles[]`.

Filters (v1: `type: "tabs"` only, client-side over the snapshot): `{id, type:"tabs", label, field, options:[
"All", ...], default:"All", applies_to:[tile ids]}`. A tile is filtered on `field` only when its rows carry
that field. Pre-aggregated tiles (kpi, area, heatmap) must ship one row set per option INCLUDING an `"All"`
row set; per-entity tiles (beeswarm, bubble, dots, lollipop, table) just carry the field on each row.
A filter must read as working from the top of the page: give every kpi tile a `where` on the filter field
(the kit dims the kpis of the other options) and put only tiles that stay full under EVERY option in
`applies_to` — a bar chart that compares the options collapses to one bar, a status table to one row; leave
those out of `applies_to` or re-aggregate them per option (a per-day trend, a breakdown by another field).

Common tile fields: `id`, `type`, `span` (12-col grid: kpi 3, hero 8+4 or 7+5, pairs 6+6), `title` (what it
shows), `subtitle` (scope line: period, segment, unit), `insight` (one sentence stating the answer — required on
every non-kpi tile), `data` (data key → `data/<key>.json`), `where` (optional `{field: value}` row filter),
`source` (source id), `query` (`queries/<tile>.sql|.py` path, or the literal query), `format` (`currency_compact`
| `integer` | `percent` | `percent_delta` | `number`) or `unit` (e.g. `"$M"`, `"ms"`).

Tile types and their fields (the kit renders these; anything else falls back to a table):
- `kpi` — rows `{label, value, format, delta, delta_label, spark:[...], good_when:"up"|"down"}` (+ filter
  field). Tile `accent` (`accent`|`neg`|`pos`) colours the top rule and number. Use `where` to pick one metric
  row set per tile; a 4-kpi strip is the standard opener.
- `area` — `x` (time field, `YYYY-MM` or `YYYY-MM-DD`), `series:[{field,label}]`, `stacked`, `end_values`
  (labels at the line ends instead of a legend), `annotations:[{x,label}]`, `bands:[{from,to,label}]`.
- `bar` — `category`, `value`, `sort` (`desc`), `signed` (diverging +/−). Horizontal, values on bars.
- `lollipop` — `category`, `value`, `color` (field for semantic colour), `limit` (top-N each side). Diverging stems.
- `beeswarm` — one dot per row: `category`, `value`, `color`, `sub`, `scale:"log"|"linear"`, `label_top` (N),
  `radius`, `ticks:[...]`.
- `bubble` — `category`, `x`, `y`, `size`, `color`, `x_label/y_label/size_label`, `x_format/y_format/size_format`,
  `label_top`. Median guides drawn automatically.
- `dots` — unit chart: `category`, `group` (column field), `groups:[order]`, `color` (field), `color_order:[...]`.
- `slope` — `category`, `period`, `periods:[a,b]`, `value`. Declines drawn dashed in the negative colour.
- `heatmap` — `x`, `y`, `value`, `format`, `x_label`, `y_label`, `min`, `max`. In-cell numbers.
- `funnel` — `category` (stage name only), `value`. The kit prints the count, share of the first stage and
  step conversion on each stage — never bake numbers or percentages into the stage name.
- `table` — `columns:[{field,label,format,bar:true}]`, `sort:{field,dir}` (initial; headers are click-sortable).
  Inline bars; `format:"status"` renders a pill whose tone (green `healthy` / amber `watch` / red `at-risk`) is
  inferred from the label, or set per value with `status_map:{"at_risk":{"tone":"watch","label":"At risk"}}`.
- `small_multiples` — `facet`, `x`, `value`, `reference:{value,label}`. Linked hover.
Read the two closest manifests in `kit/examples/` before planning — they are the quality bar and show real field usage.

# Chart grammar (enforced)
Data shape → tile: time series → `area` (stacked only for part-of-whole); ranking → sorted `bar`/`lollipop`;
two-period change → `slope`; **one row per entity** (customers, stations, SKUs, reps) → show the entities with
`beeswarm` / `bubble` / `dots` / `lollipop`, never a bar of their sum; cohort / matrix → `heatmap`; staged
conversion → `funnel`; several comparable series → `small_multiples`; lists people will scan → `table`.
Hard bans: pie/donut, 3-D, dual y-axes, legends when end-labels fit, more than 8 tiles beyond the kpi strip
(unless the user listed more sections — their explicit list wins), more than one accent
per tile, raw unformatted numbers, bar axes that do not start at 0, lorem/placeholder data, "Dashboard" as a
title. Every tile answers one question, stated in its `insight`. One hero tile (`span` ≥ 7) per dashboard.
Composition: the dashboard is one argument told in 5-8 tiles — kpi strip (the headline numbers) → hero
(the trend behind the headline) → the breakdowns that explain it → the entities that drive it.
