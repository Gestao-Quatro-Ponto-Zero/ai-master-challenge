---
name: Pipeline em Foco
description: A sales action-queue app rendered as a G4-branded business broadsheet — navy structure, gold for money, ivory paper.
colors:
  paper: "#f3ede0"
  surface: "#fffdf8"
  surface-2: "#faf5ea"
  navy: "#12233c"
  navy-2: "#1b3251"
  ink: "#1d2637"
  muted: "#6a6152"
  line: "#ddd3bf"
  line-strong: "#c8bda4"
  gold: "#b8873b"
  fechar: "#8a6212"
  fechar-soft: "#efe1bf"
  decidir: "#7c332f"
  decidir-soft: "#eed9d3"
  avancar: "#4c6440"
  avancar-soft: "#dde4d1"
  prospectar: "#33517d"
  prospectar-soft: "#d9e2f0"
  warn: "#6b4a8f"
typography:
  display:
    fontFamily: "Libre Caslon Text, Georgia, serif"
    fontSize: "clamp(2rem, 1.4rem + 2.4vw, 2.9rem)"
    fontWeight: 700
    lineHeight: 1.12
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Libre Caslon Text, Georgia, serif"
    fontSize: "1.3rem"
    fontWeight: 700
    lineHeight: 1.12
  lede:
    fontFamily: "Libre Caslon Text, Georgia, serif"
    fontSize: "1.25rem"
    fontWeight: 400
    lineHeight: 1.5
  body:
    fontFamily: "Manrope, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Manrope, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    letterSpacing: "0.04em"
  meta:
    fontFamily: "Manrope, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 500
  meta-lg:
    fontFamily: "Manrope, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
  product-name:
    fontFamily: "Manrope, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 600
  chart-axis:
    fontFamily: "Manrope, sans-serif"
    fontSize: "13px"
  brand-word:
    fontFamily: "Libre Caslon Text, Georgia, serif"
    fontSize: "1.12rem"
    fontWeight: 700
  section-title:
    fontFamily: "Libre Caslon Text, Georgia, serif"
    fontSize: "1.15rem"
    fontWeight: 700
  facts-value:
    fontFamily: "Manrope, sans-serif"
    fontSize: "1.4rem"
    fontWeight: 800
  facts-value-big:
    fontFamily: "Manrope, sans-serif"
    fontSize: "2.15rem"
    fontWeight: 800
  score-lg:
    fontFamily: "Manrope, sans-serif"
    fontSize: "2.35rem"
    fontWeight: 800
  stat-value:
    fontFamily: "Manrope, sans-serif"
    fontSize: "1.6rem"
    fontWeight: 800
  brand-word-mobile:
    fontFamily: "Libre Caslon Text, Georgia, serif"
    fontSize: "1rem"
    fontWeight: 700
  lede-mobile:
    fontFamily: "Libre Caslon Text, Georgia, serif"
    fontSize: "1.1rem"
    fontWeight: 400
  topbar-badge:
    fontFamily: "Manrope, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 800
rounded:
  sm: "5px"
  md: "12px"
  lg: "16px"
  pill: "999px"
  fine: "2px"
  tag: "3px"
  chip: "4px"
  tabs: "8px"
spacing:
  sm: "0.5rem"
  md: "1rem"
  lg: "1.75rem"
  xl: "2.75rem"
components:
  button-primary:
    backgroundColor: "{colors.navy}"
    textColor: "#f6f1e6"
    rounded: "{rounded.sm}"
    padding: "0.5rem 1rem"
  button-quiet:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "0.5rem 1rem"
  tag-fechar:
    backgroundColor: "{colors.fechar-soft}"
    textColor: "{colors.fechar}"
    rounded: "999px"
    padding: "0.1rem 0.6rem"
---

# Design System: Pipeline em Foco

## Overview

**Creative North Star: "The Editorial Ledger"**

A sales pipeline rendered as a G4-branded business broadsheet, not a SaaS dashboard. A deep-navy structural field (nav rail, table headers, the deal masthead) frames a warm ivory canvas; a serif editorial voice (Libre Caslon Text) carries headlines and one-sentence ledes, while Manrope carries UI chrome and tabular data. The system's single organizing idea is that color is the action queue, not decoration: the same four heraldic hues (gold/burgundy/sage/slate-navy) recur on every score badge, tag, table row-edge, board column and forecast stack so a deal's priority is legible at a glance across every screen it appears on. Gold is spent narrowly — the "Fechar" (close) queue, the brand mark, primary CTAs — so its appearance always means money or the one action to take.

The dark theme (navy-black, following the "Lead Scorer Dashboard" mockup) is the default. The light theme (ivory paper, navy, ink) is opt-in through `data-theme="light"`. Every color role is redefined per theme, never computed ad hoc. The hex values in this file are the light theme's; the dark theme keeps the same roles with lighter tones.

**Key Characteristics:**
- Deep navy structural chrome; in the default dark theme the canvas is navy-black, in the light theme warm ivory paper.
- Four fixed heraldic queue hues (fechar=gold, decidir=burgundy, avancar=sage, prospectar=slate-navy) as the app's only categorical color system.
- Libre Caslon Text serif for all headings and editorial ledes; Manrope sans for every UI control and tabular figure.
- Flat-to-lightly-lifted surfaces: thin warm hairlines and soft ambient shadows, no hard offset shadows.
- A recurring hand-drawn age-ruler SVG as the signature data component.

## Colors

The palette pairs a warm, taupe-tinted neutral scale with a navy structural color and four fixed heraldic accents; no accent is decorative — each maps to exactly one meaning.

### Primary
- **Signature Gold** (`#b8873b`): reserved for the brand mark, the "Fechar" (close) queue, and primary CTA fills (`.btn-gold`). Its scarcity is deliberate — gold on screen means money or the one action to take.
- **Structural Navy** (`#12233c`, deeper rail tone `#1b3251`): the nav rail, table header row, deal masthead, primary button fill, and kanban "aria-current" tab. The app's one dark mass against the paper.

### Secondary
- **Ledger Burgundy** (`#7c332f`, soft tint `#eed9d3`): the "Decidir" (decide) queue — zombie deals stalled past the observed cycle. Never used outside that queue's tag, score ring, row edge and stack segment.

### Tertiary
- **Field Sage** (`#4c6440`, soft tint `#dde4d1`): the "Avançar" (advance) queue — deals still early in the cycle. Also doubles as the "won" state color (`.won`).
- **Slate-Navy** (`#33517d`, soft tint `#d9e2f0`): the "Prospectar" (prospect) queue, and reused as the link/focus-ring color (`--focus`) since it reads as informational rather than actionable.

### Neutral
- **Warm Paper** (`#f3ede0`): page background — ivory, not white or gray.
- **Warm Surface** (`#fffdf8`) / **Surface-2** (`#faf5ea`): card, table and list backgrounds; surface-2 is the hover/alternate tint.
- **Ink** (`#1d2637`): primary text, warmed off-black.
- **Taupe Muted** (`#6a6152`): secondary text, labels, captions — warm-tinted, never neutral gray.
- **Warm Hairline** (`#ddd3bf`) / **Line-Strong** (`#c8bda4`): borders and dividers, both warm-tinted off the paper hue.
- **Warn Violet** (`#6b4a8f` light, `#c3a6e6` dark): the sole non-queue semantic color, for data-hygiene flags (missing account) and the stuck-funnel alarm. It was terracotta, but in the dark theme terracotta read almost the same as the Decidir salmon, so hygiene flags looked like queue membership. Violet sits outside the four queue hues in both themes.

### Named Rules
**The Color-Is-Queue Rule.** The four heraldic hues (gold/burgundy/sage/slate-navy) are the app's only categorical color system and mean exactly one thing each — fechar/decidir/avancar/prospectar — wherever they appear (score ring, tag, table row-edge, board column border, forecast stack, ruler zone). Never introduce a fifth categorical color or reuse one of the four for an unrelated meaning.
**The Gold-Is-Money Rule.** Signature gold appears only on the brand mark, the Fechar queue, and primary-action fills. It never decorates a neutral element.

## Typography

**Display Font:** Libre Caslon Text (with Georgia, serif fallback)
**Body Font:** Manrope (with system-ui, sans-serif fallback)

**Character:** An editorial serif for narrative moments (headlines, ledes, quote-voice italics) paired with a clean geometric sans for every control, label and number — the broadsheet's masthead against its stat columns.

### Hierarchy
- **Display** (700, `clamp(2rem, 1.4rem + 2.4vw, 2.9rem)`, line-height 1.12): page `h1`, one per view.
- **Title** (700, 1.3rem, line-height 1.12): section `h2` (queue heads, board columns), colored by the active queue hue.
- **Lede** (400, 1.25rem, line-height 1.5, Caslon): the one-sentence editorial summary under every page head, max 72ch; `<strong>` inside a lede is set in the fechar hue.
- **Body** (400, 15px/1.55, Manrope, `font-variant-numeric: tabular-nums`): default running text and all monetary/numeric figures.
- **Label** (700, 0.75–0.8125rem, letter-spacing 0.03–0.06em, uppercase, Manrope): filter labels, table header cells, action-panel eyebrow captions inside `.action h2`.

### Named Rules
**The Two-Voice Rule.** Caslon is reserved for headlines, ledes and quote/italic voice; Manrope carries every other UI surface including all tabular and numeric data. No third display face, no system UI font substitution for either role.

## Layout

A fixed two-column shell: a 244px sticky navy rail (icons, section nav, operator footer) beside a fluid ivory canvas capped at `max-width: 1440px` — wide enough that stat cards, deal lists and tables use a large desktop viewport instead of stranding half the screen as empty paper. Editorial text (`.page-head`, the lede) keeps its own independent `max-width: 72ch` regardless of the canvas width, so prose never stretches uncomfortably even when the structural content around it fills the screen. A sticky, blurred filter strip (region → manager → vendor cascade) sits above the canvas content. Section rhythm steps in large increments (`2.25rem`–`2.75rem` between sections) to read as separated ledger entries rather than a dense grid. Below 860px the rail collapses to a horizontal scrolling top bar, the two-column queue pairing (`queue-pair`) stacks to one column, and the deal-row grid drops its third (fact) column.

## Elevation & Depth

Hybrid: mostly flat, warm-hairline-bordered surfaces (`border: 1px solid var(--line)`) with two soft ambient shadow steps used sparingly for lift on interactive surfaces (cards, the deal-list, the deal masthead) — never a hard offset or neobrutalist shadow.

### Shadow Vocabulary
- **Ambient small** (`--shadow-sm: 0 1px 2px rgba(18,35,60,.06), 0 2px 8px rgba(18,35,60,.05)`): resting cards, tables, deal lists.
- **Ambient medium** (`--shadow-md: 0 6px 18px rgba(18,35,60,.10), 0 1px 3px rgba(18,35,60,.07)`): hover lift on buttons and cards, and the deal masthead at rest.

### Named Rules
**The Soft-Lift Rule.** Depth is ambient and directional-light soft, never a hard offset block shadow. Hover states raise `translateY(-1px/-2px)` paired with the medium shadow step; nothing snaps to a harsh silhouette.

## Shapes

Small, consistent corner radii throughout: `5px` (buttons, inputs, tags' pill uses `999px`), `12px` (cards, lists, tables, action panels), `16px` (the deal masthead, the largest single surface). Borders are 1px warm hairlines; no heavy strokes. The recurring signature geometry is the age-ruler: a thin horizontal three-zone bar (avançar/fechar/decidir tint bands) with a navy tick marking the deal's position — it appears at three sizes (row-inline, board-card, deal-page-large) and is the one custom visual motif that repeats app-wide, alongside the brand mark: a supplied bronze armillary-sphere emblem (`src/assets/logo-mark.png`, 32px, background keyed to transparent so it sits directly on navy with no visible box).

## Components

### Buttons
- **Shape:** small radius (`5px`), inline-flex, bold label weight.
- **Primary** (`.btn`): `--btn-bg`/`--btn-ink` tokens. Navy fill with off-white text in the light theme; inverted (ivory fill, navy text) in the dark theme, where a navy fill vanished against the navy surface. `0.5rem 1rem` padding, ambient-sm shadow at rest.
- **Suggested decision** (`.btn-decidir`): filled in the Decidir hue, used on whichever of "Requalifiquei" / "Encerrar como perdido" the engine suggests; the other button is quiet.
- **Gold** (`.btn-gold`): gold fill, near-black text (`#211603`) for the close-queue and money-adjacent CTA.
- **Quiet** (`.btn-quiet`): surface fill with an inset 1px line-strong ring instead of a border — used for secondary actions ("Encerrar como perdido").
- **Link** (`.btn-link`): no background, slate-navy text, underline, used for low-emphasis actions ("Limpar filtros", "Desfazer").
- **Hover / Focus:** all buttons lift `translateY(-1px)` and step up to the medium shadow on hover; `:focus-visible` gets a 2px slate-navy outline app-wide.

### Chips (Tags)
- **Style:** pill radius (`999px`), each queue's soft tint as background with its saturated hue as text, uppercase, 700 weight, 0.75rem.
- **State:** no selected/unselected variant — a tag is a fixed queue label, not a toggle.

### Cards / Containers
- **Corner Style:** `12px` for lists/cards, `16px` for the deal masthead.
- **Background:** warm surface (`#fffdf8`) on paper.
- **Shadow Strategy:** ambient-sm at rest, ambient-md on hover (see Elevation).
- **Border:** 1px warm hairline (`var(--line)`); the kanban card additionally tints its border toward the active queue hue on hover.
- **Internal Padding:** `0.85rem–1.6rem` depending on density (compact deal-row vs. the deal masthead).

### Stat Cards (Meu dia KPI row)
Three cards in a row (`.stat-row`, stacks on mobile): uppercase label + circular gold-on-`fechar-soft` icon badge, a bold 1.6rem number, then a thin gold-on-`line` progress bar and a muted caption stating the real ratio behind it (e.g. "14% do pipeline declarado (US$ 5 mi)"). Every ratio is computed from the same scoped-open data as the rest of the app — never an invented comparison like "12% acima da meta".

### Inputs / Fields
- **Style:** warm surface background, 1px `line-strong` border, `5px` radius, custom double-chevron select arrow drawn in CSS gradients (no native OS arrow, no icon font).
- **Focus:** border shifts to slate-navy plus a 3px soft slate-navy glow ring, no default outline.

### Navigation
- **Style:** navy rail, links in translucent warm-white text stepping to full white on hover/active; the active link carries a 3px gold tick on its leading edge (rotates to a bottom tick on the mobile horizontal rail). Each link carries a one-stroke SVG icon (17px, same stroke language as the reason icons) before its label. A "Workspace" micro-label sits above the list (hidden on the mobile horizontal rail, where it has no room to mean anything). Section headings above rows are Caslon-serif and colored by their queue.
- **Operator footer:** pinned at the bottom of the rail — a gold initials avatar plus the current filter scope's name (vendor/manager/region, or "Toda a equipe"), the same source of truth as `MyDay`'s "Bom dia, {agent}", never a fabricated logged-in identity. The "Dados até…" reference-date line sits beneath it. Hidden on mobile (no room in the horizontal rail).

### Topbar (system chrome)
A persistent 60px navy bar above the sidebar and canvas (52px on mobile), carrying the account identity rather than just the product name: the compass mark + "G4" wordmark (the real, repo-confirmed brand), a divider, then "Pipeline em Foco" as the product name. A translucent-navy global search (`.topbar-search`, `color-mix(in srgb, white 10%, var(--navy))`) routes to Pipeline's own search via a `busca` query param — real filtering, not decorative chrome. A bell icon shows a live, filter-scoped count of deals in the "decidir" queue (gold pill badge, capped at "99+"). An outlined gold "Exportar" button generates a real CSV of the current filter scope (`.topbar-export`) — a tangible action a sales manager would actually use, not a decorative CTA. On mobile the search and product-name label collapse; brand, bell and export stay.

### Tables
The `.deals` table's first column (`Deal`) is `position: sticky; left: 0` with its own background — once a table grows wide enough to need horizontal scroll (Pipeline's table has 8 columns including "Próxima ação"), the one column that says *which deal this is* never scrolls out of view, the same convention any real spreadsheet or CRM grid uses. The queue-colored left accent bar and the sticky column's own edge-hairline compose into one `box-shadow` list rather than fighting each other. "Próxima ação" reuses the engine's own `action` sentence (never new copy), truncated to one line with a small arrow-link icon.

### The Age Ruler (signature component)
A thin, three-zone horizontal bar (SVG rects tinted from each queue's hue) with a navy marker tick showing where a deal sits against the observed sales-cycle distribution. Appears inline (`ruler-sm`, 9px tall) in every deal row and board card, and large (`ruler-lg`, 16px, with axis ticks) on the deal page and the win-curve chart. It is the one component every list, board and deal page shares, and is the app's most-repeated custom visual idiom.

**Exception — the "Decida o destino" queue.** Every deal in this queue is a zombie: score is always 0 and the ruler's marker always sits pinned past its right edge. Repeating a badge and a bar that never vary carries no information, so this one queue swaps them for `StalledRow`: the score circle becomes a decidir-tinted badge showing the actual day count (the number that varies and matters), and the ruler becomes the deal's declared value with a "no forecast declarado" caption — the same key `ORDER.decidir` already sorts this queue by. Pipeline's table and board still show the ordinary Score + Ruler for decidir-bucket deals, because there they sit beside every other bucket and the contrast (0 among 40–100s, pinned among varied positions) is itself the signal.

## Do's and Don'ts

### Do:
- **Do** keep gold spent only on the Fechar queue, the brand mark, and primary CTAs (The Gold-Is-Money Rule).
- **Do** pair Caslon headlines/ledes with Manrope for every control and number (The Two-Voice Rule).
- **Do** draw icons (age-ruler, sort indicators, back chevron, reason markers, nav icons) as inline SVG in one consistent stroke weight — never a unicode glyph or icon font. The brand mark is the one exception: a real supplied raster asset, not drawn — see Cards/Navigation above.
- **Do** keep depth ambient and soft (The Soft-Lift Rule); reserve shadow escalation for hover/interactive state, not resting decoration.
- **Do** carry the four heraldic queue hues identically across every surface a deal's status appears on (score, tag, row edge, board column, stack, ruler zone).

### Don't:
- **Don't** add a kicker/eyebrow label floating above a page or section heading; the built system folds context (like a dateline) into the lede's own prose sentence instead. This is a defect the finish review removed from one page, not a pattern to reintroduce.
- **Don't** introduce a fifth categorical color, or reuse a queue hue for a meaning outside its queue.
- **Don't** use hard-edged offset shadows (neobrutalist block shadows); this world's depth is ambient-soft only.
- **Don't** substitute a system display face for Libre Caslon Text in headline/lede roles, or a system sans for Manrope in UI/data roles.
