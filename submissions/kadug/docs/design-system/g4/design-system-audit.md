# Design System Extraction: G4

## Source Coverage

- Target: https://g4business.com/
- Date: 2026-06-28
- Pages/routes inspected: homepage and linked evidence from the homepage source.
- Viewports: desktop screenshot at 1440x1200; mobile screenshot at 390x844.
- Evidence files:
  - `evidence/g4-home.html`
  - `evidence/g4-home-desktop.png`
  - `evidence/g4-home-mobile.png`
  - `evidence/post-7.css`
  - `evidence/post-32690.css`
  - `evidence/post-25730.css`
  - `evidence/base-desktop.css`
  - `css-token-inventory.json`
- Limitations:
  - This is not an official G4 brand book.
  - Playwright browser launch was blocked by host permissions, so screenshots were captured through Chrome headless and styles were extracted from downloaded HTML/CSS.
  - Use of G4 logos, photos, and proprietary fonts must be confirmed before public shipping.

## Preview Fidelity

- Mode: `audit-only`
- Claim: extracted identity and implementation guidance only; no visual clone or calibrated preview.
- Calibration required: no
- Calibration file: none
- Scene graph required: no
- Scene graph file: none
- Gate result: pass
- Known gaps: no runtime computed-style JSON from Playwright; no hover-state screenshot; no official usage-rights confirmation.
- Rationale: the challenge needs a front-end visual direction, not a reconstruction of the G4 site.

## Executive Summary

The current G4 identity is an executive editorial system: deep navy, warm off-white, muted gold, restrained typography, human/business proof, and low-noise conversion controls. For the churn challenge, the strongest adaptation is not to reproduce the homepage. It is to translate the brand into a serious Streamlit executive dashboard: navy shell, off-white workspace, gold hierarchy, Manrope UI, modest cards, and data visuals with premium restraint.

## Page Map

See `page-map.json` for the structured section inventory. The source rhythm is:

1. Promotional announcement band.
2. Main navigation.
3. People-led campaign hero.
4. Four-pillar ecosystem band.
5. Practitioner/mentor proof.
6. Testimonials and video/social proof.
7. Mission and metrics.
8. Program highlights.
9. Content, FAQ, and footer.

For the challenge dashboard, only the underlying grammar should be reused: dark executive entry, light analytic workspace, restrained cards, strong CTAs, and proof-oriented content hierarchy.

## Brand DNA

- Positioning: business education and execution ecosystem for leaders, founders, and operators.
- Visual personality: premium, ambitious, practical, founder-led, disciplined.
- Density: marketing pages alternate large cinematic sections with compact proof grids; dashboard adaptation should be denser and more operational.
- Trust model: founders/mentors, mission metrics, testimonials, program proof, content authority.
- Signature patterns: navy fields, off-white bands, gold emphasis, real-person imagery, editorial italic phrases, four-column proof grids, modest rounded CTAs.
- Color temperature: cool dark navy balanced by warm gold and warm off-white.
- Section rhythm: dark campaign section, light proof band, dark authority section, proof/media sections, metric/program/content closure.
- Motion personality: simple carousel controls and hover transitions; no heavy motion is needed for the Streamlit MVP.
- Micro-detail families: thin gold divider, compass-like icon mark, round carousel arrows, gold arrows, subtle borders, dense footer link groups.

## Art Direction Model

- Family: executive editorial workspace.
- Composition: full-width dark/navy bands paired with off-white proof surfaces; people-led hero on marketing; compact analytic grid for dashboard.
- Density: breathable on marketing, scan-first in the dashboard adaptation.
- Color behavior: navy and off-white dominate; gold is a semantic accent; rust is secondary/warning.
- Material system: flat ink, modest shadows, low-contrast borders, photographic proof, editorial text emphasis.
- Depth system: mostly flat; shallow panel shadow appears in dropdown/menu-like surfaces.
- Shape language: low-radius rectangles, circular icon/arrow controls, pills only for status chips.
- Motion language: hover/focus transitions around 0.3s; carousel movement on marketing proof only.
- Micro-detail language: dividers, arrows, icon marks, highlighted phrases, compact proof tiles.
- Anti-patterns: bright SaaS blues, neon gradients, decorative blobs, oversized rounded cards, cartoon motion, generic stock illustrations, colorful dashboard palettes.
- Reconstruction constraints: use tokens and grammar; do not copy G4 logos, photos, or font files unless rights are confirmed.

## Reference Calibration

- Reference: `evidence/g4-home-desktop.png` and `evidence/g4-home-mobile.png`.
- Measured anchors: not pixel-calibrated because no preview/reconstruction was requested.
- Reconstructed primitives: tokens, component guidance, Streamlit CSS.
- Deliberate deviations: dashboard spacing is tighter than the marketing homepage; carousels and founder imagery are omitted from the MVP dashboard guidance.
- Remaining mismatch: exact responsive menu behavior and hover states were not captured.

## Visual Evidence Inventory

| Section | Visual role | Layers | Color evidence | Motion evidence | Micro-details | Confidence |
|---|---|---|---|---|---|---|
| Announcement band | Premium urgency | Gradient background, campaign mark, centered copy, CTA | `#105C88`, `#02131F`, `#B9915B`, `#F5F4F3` | None observed in screenshot | Gold italic phrase, outline CTA | observed |
| Main navigation | Conversion and IA | Logo, nav, primary CTA, secondary CTA | `#001F35`, `#B9915B`, `#F5F4F3` | Hover/focus inferred from CSS | Dropdown arrows, compact nav | observed |
| Hero campaign | Main conversion proof | Dark copy block, people image, gold CTA, carousel arrows | `#001F35`, `#B9915B`, `#842E20`, white/off-white text | Carousel controls visible | Gold divider, large image crop | observed |
| Business lines | Ecosystem proof | Off-white surface, 4 columns, icon/title/body/link | `#F5F4F3`, `#001F35`, `#B9915B` | Link hover inferred | Gold icon, arrow link | observed |
| Mentor proof | Authority statement | Dark band, centered headline, mentor modules below | `#001F35`, `#B9915B`, `#F5F4F3` | Carousel/media likely | Italic gold phrase | observed |
| Testimonials | Social proof | Media thumbnails/cards, carousel controls | rust controls and neutral surfaces | Carousel controls visible in source | Dots/arrows/media thumbnails | observed |
| Mission metrics | Impact proof | Large statements, counters, sector/program groups | navy/gold/off-white | Counter animation possible but not verified | Large numeric hierarchy | inferred |
| Program highlights | Product proof | Card grid, image crops, CTA | off-white, navy, gold | Hover inferred | Program tiles and image crops | observed |
| Content/FAQ/footer | Objection handling | Article cards, accordion, dense footer | navy, gold links, neutral borders | Accordion interaction likely | Dividers, link groups | observed |

## Foundations

### Colors

| Token | Value | Role | Usage | Source | Confidence |
|---|---:|---|---|---|---|
| `g4.navy` | `#001F35` | Primary brand field | Header, dark sections, text on light | `post-7.css` | official |
| `g4.ink` | `#031A26` | Main text | Body, table text, links | `post-7.css` | official |
| `g4.gold` | `#B9915B` | Accent/CTA | Buttons, highlights, icons, dividers | `post-7.css` | official |
| `g4.silver` | `#F5F4F3` | Warm surface | Background bands and inverse text | `post-7.css` | official |
| `g4.rust` | `#842E20` | Secondary/warning | Carousel controls; dashboard risk accent | HTML/CSS inventory | observed |
| `g4.border` | `#D6D5D5` | Divider | Tables, cards, subtle separators | CSS inventory | observed |
| `g4.muted` | `#706F6F` | Muted text | Secondary descriptions | CSS inventory | observed |

### Typography

| Style | Family | Size | Weight | Line height | Usage | Confidence |
|---|---|---:|---:|---:|---|---|
| UI body | Manrope | 14-16px | 200-400 | 1.5 inferred | Dashboard text, tables, nav | official |
| UI title | Manrope | 25-36px | 600 | 1.2 inferred | Section headings, card titles | observed |
| CTA | Manrope | 16px | 800 | normal | Buttons and commands | official |
| Editorial display | PPMuseum | variable | 200-600 | variable | Brand/editorial phrases | official but license-sensitive |
| Italic emphasis | Libre Baskerville | variable | 400-700 italic | variable | Gold phrase inside heading | observed |

### Spacing And Layout

| Token | Value | Usage | Evidence |
|---|---:|---|---|
| `space.xs` | 5px | compact icon/text gaps | CSS gap inventory |
| `space.sm` | 8px | chips and small controls | CSS gap inventory |
| `space.md` | 10px | standard component gap | CSS gap inventory |
| `space.lg` | 20px | card padding and menu panels | CSS padding/gap inventory |
| `space.xl` | 40px | section/module spacing | CSS gap inventory |
| `container.marketing` | 1140px | website max width | `post-7.css` |
| `container.dashboard` | 1200px | dashboard recommendation | inferred from challenge context |

### Shape, Border, Elevation

| Token | Value | Usage | Evidence |
|---|---:|---|---|
| `radius.none` | 0px | bands, tables | CSS inventory |
| `radius.sm` | 8px | buttons | CSS inventory |
| `radius.md` | 10px | cards/buttons | CSS inventory |
| `radius.lg` | 15px | grouped panels | CSS inventory |
| `radius.pill` | 999px | chips/status only | CSS inventory |
| `shadow.panel` | `0 0 10px rgba(0,0,0,0.2)` | elevated menu/card | CSS inventory |
| `border.default` | `1px solid #D6D5D5` | low contrast structure | inferred from CSS colors |

### Effects And Visual Atmosphere

| Token | Value | Usage | Evidence | Confidence |
|---|---:|---|---|---|
| `effect.goldDivider` | transparent to gold to transparent linear gradient | section separator | `post-32690.css` | computed |
| `effect.darkHeaderGradient` | `171deg, #105C88 0%, #02131F 35%` | top band/header atmosphere | `post-25730.css` | computed |
| `effect.photoCrop` | large real-person image crop | credibility proof | screenshots | observed |

### Motion

| Token | Value | Trigger | Usage | Evidence | Confidence |
|---|---:|---|---|---|---|
| `motion.hover` | 0.3s | hover/focus | icon/link/button feedback | CSS transitions | observed |
| `motion.carousel` | manual/loop inferred | click/autoplay unknown | homepage proof modules | screenshot/HTML controls | inferred |
| `motion.reduced` | remove non-essential motion | user preference | dashboard fallback | accessibility guidance | inferred |

## Atomic Design Inventory

### Tokens

Color, typography, spacing, radius, border, effect, motion, layout, and component tokens are normalized in `tokens.json`.

### Atoms

- Button
- Link
- Icon mark
- Divider
- Heading
- Body text
- Chip/status
- Arrow
- Counter value
- Table cell

### Molecules

- Nav item with dropdown marker
- CTA group
- Metric card
- Finding block
- Account risk chip group
- Filter row
- Article/program tile
- Accordion row

### Organisms

- Dark app header
- Executive summary band
- KPI grid
- Risk segment section
- Priority account table
- Recommendation backlog
- Evidence/finding narrative section

### Templates

- Executive dashboard page
- Detail drill-down page
- Export/report cover page
- Data quality page

### Pages

- Challenge Streamlit dashboard
- Executive report export
- Optional stakeholder view for CS/Product/Revenue/Support

## Component Architecture

### Executive Header

- Anatomy: title, subtitle, current analysis scope, primary action.
- Visual expression: navy gradient or solid navy with off-white text.
- Layering: flat background, optional gold divider.
- Micro-details: one gold accent phrase or divider.
- Variants: compact dashboard header, report cover header.
- States: no complex states.
- Motion/interactions: none required.
- Responsive behavior: stack actions below copy on mobile.
- Accessibility notes: keep off-white text on navy, avoid gold-only long text.
- Rebuild notes: use in Streamlit through markdown container plus injected CSS.

### KPI Card

- Anatomy: label, value, delta/status, short evidence note.
- Visual expression: white card on off-white background, navy text, gold accent.
- Layering: flat card with subtle border; shadow only for priority.
- Micro-details: tiny gold rule or chip.
- Variants: neutral, positive, risk.
- States: hover optional; selected state uses gold border.
- Motion/interactions: none required.
- Responsive behavior: four columns desktop, two/tablet, one/mobile.
- Accessibility notes: do not encode risk only by color.
- Rebuild notes: map to Streamlit metrics or custom HTML cards.

### Finding Block

- Anatomy: signal, evidence, interpretation, action, owner, confidence.
- Visual expression: structured editorial block, Manrope text, gold section label.
- Layering: white/elevated panel, low-contrast dividers.
- Micro-details: confidence chip, stakeholder tag.
- Variants: executive, product, support, revenue.
- States: expandable detail optional.
- Motion/interactions: accordion can use native Streamlit expander.
- Responsive behavior: full-width stacked blocks.
- Accessibility notes: labels must remain visible in text.
- Rebuild notes: follow the architecture narrative contract already defined in `docs/architecture.md`.

### Priority Account Table

- Anatomy: account, ARR/MRR, risk bucket, signals, recommended action.
- Visual expression: dense Manrope table, neutral grid, gold active filters.
- Layering: white table surface over off-white page.
- Micro-details: risk chips, owner tags, sorted column state.
- Variants: high risk, watchlist, recovered.
- States: selected row, filtered, empty, loading.
- Motion/interactions: none required.
- Responsive behavior: horizontal scroll on mobile or cardized rows.
- Accessibility notes: keyboard focus and non-color labels for risk.
- Rebuild notes: avoid marketing card density; this is operational.

## Motion And Interaction Model

| Element | Observed behavior | Trigger | Duration/easing | Loop/state count | Reduced-motion fallback | Confidence |
|---|---|---|---|---|---|---|
| Header/nav links | Color/fill transition | hover/focus | 0.3s, easing not captured | default/hover/focus | instant state change | observed |
| CTA buttons | Background and text color change | hover/focus | 0.3s inferred | default/hover/focus | instant state change | observed |
| Homepage carousel | Arrow/dot navigation | click/autoplay unknown | not captured | multiple slides | static first slide | inferred |
| FAQ accordion | Expand/collapse likely | click | not captured | closed/open | native expander without animation | inferred |
| Dashboard filters | Not from source; recommended | click | none | default/active/disabled | same | inferred |

## Layout And Spacing

- Use a single dark header, not the full marketing nav stack.
- Use an off-white page background and white elevated cards.
- Use four-column KPI grid on desktop, two-column on tablet, one-column mobile.
- Keep section gaps around 24-40px in the dashboard.
- Avoid huge landing-page vertical spacing inside analytic workflows.
- Cards should be 8-10px radius; 15px only for large grouped panels.

## Communication Model

- Voice: direct, ambitious, executive, practical.
- Headline pattern: business outcome first, proof second, action third.
- CTA pattern: concrete verbs such as "Exportar relatorio", "Ver contas prioritarias", "Abrir backlog".
- Microcopy: evidence-led, not generic. Prefer "Sinal observado", "Evidencia", "Acao recomendada".
- Vocabulary: lideres, empresas reais, metodo, disciplina, execucao, risco, ARR, conta prioritaria.
- Narrative architecture: problem signal, evidence, interpretation, stakeholder action.

## Responsive Behavior

- Source mobile shows compressed nav and stacked hero/content behavior.
- Dashboard adaptation should prioritize readability:
  - Single-column metric cards on narrow screens.
  - Tables can scroll horizontally or convert to account cards.
  - Header CTAs should stack.
  - Avoid large fixed-width typography or viewport-scaled text in dashboard controls.

## Accessibility Risks

- Contrast: gold on off-white can be weak for long text; use gold for short accents only.
- Focus: custom CSS must preserve visible focus outline.
- Motion: carousel/motion should have reduced-motion fallback if added.
- Touch targets: CTA and filter chips should stay at least 44px high where practical.
- Text overflow: long account names and recommendations need wrapping/truncation rules.
- Font licensing: PPMuseum is observed, but licensing must be confirmed; Manrope is safer for app UI.

## Fidelity Gate

- Result: pass for audit-only extraction.
- Missing evidence: runtime hover screenshots; exact computed styles through Playwright; official brand permissions.
- Missing motifs: no calibrated scene graph because no preview was created.
- Required revisions: none before using as dashboard design guidance.

## Visual Coherence Gate

- Result: pass
- Weakest section: dashboard adaptation of marketing photography. It should be omitted unless there is relevant evidence imagery.
- Removed or simplified elements: large marketing hero, carousel-heavy modules, mentor photography, and dense website footer.
- Remaining risks: overusing gold; making the Streamlit app look like a landing page instead of an analytic tool.
- Rationale: the chosen dashboard grammar preserves navy/off-white/gold, editorial hierarchy, and premium restraint while respecting the operational challenge.

## Premium Design Rubric

| Dimension | Score | Rationale | Required revision |
|---|---:|---|---|
| Brand recognizability | 4 | Core navy/gold/off-white, editorial emphasis, and proof-grid rhythm captured. | None |
| Composition | 4 | Section map and dashboard translation preserve dark entry plus light workspace. | None |
| Color fidelity | 5 | Official CSS variables and repeated observed values captured. | None |
| Typography hierarchy | 4 | Manrope, PPMuseum, and Libre Baskerville roles documented with usage limits. | None |
| Material and depth | 4 | Low-radius panels, subtle borders, and shallow shadow rules captured. | None |
| Asset fidelity | 4 | Asset families documented, with explicit no-copy constraint. | Confirm rights before shipping assets |
| Scene anatomy | 4 | Major source sections and layers mapped; no reconstruction claimed. | None |
| Motion sophistication | 3 | Hover and carousel patterns documented; no animation needed for MVP. | Add reduced-motion if animation is implemented |
| Component coherence | 4 | Components map consistently to executive dashboard needs. | None |
| Micro-detail fidelity | 4 | Dividers, arrows, icon marks, chips, and section emphasis captured. | None |
| Restraint | 5 | Guidance removes marketing excess and avoids generic SaaS decoration. | None |
| Accessibility and robustness | 4 | Contrast, focus, motion, touch, and text overflow risks documented. | Validate when UI is implemented |

Overall result: pass

## Rebuild Guidance

1. Foundations to implement first:
   - `#001F35`, `#031A26`, `#B9915B`, `#F5F4F3`, `#842E20`
   - Manrope for all dashboard UI
   - 8-10px radius cards/buttons
   - 20px card padding and 24-40px section spacing

2. Components to implement first:
   - Executive header
   - KPI card
   - Finding block
   - Priority account table
   - Risk chip
   - Stakeholder action card

3. Implementation mapping:
   - Use `tokens.json` as design-token reference.
   - Use `streamlit-theme.css` as a starting CSS injection file.
   - Keep G4 identity in colors, typography, spacing, and component hierarchy.
   - Do not copy G4 logos, photos, or custom fonts without permission.

4. Open questions:
   - Will the final dashboard be public or only submitted privately?
   - Should the app use only open-source fonts, or can it reference observed G4 font files?
   - Should the dashboard include a branded cover/export page?

## Files Produced

- `design-system-audit.md`
- `page-map.json`
- `tokens.json`
- `preview-manifest.json`
- `reconstruction-spec.md`
- `streamlit-theme.css`
- `css-token-inventory.json`
- `evidence/g4-home.html`
- `evidence/g4-home-desktop.png`
- `evidence/g4-home-mobile.png`
- `evidence/*.css`
