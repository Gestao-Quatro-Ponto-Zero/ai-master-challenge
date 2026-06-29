# G4 Visual Identity Reconstruction Spec

This spec translates the G4 website identity into a non-infringing dashboard direction for the `data-001-churn` challenge.

## Fidelity Mode

- Mode: `audit-only`
- No website clone or calibrated reconstruction is produced.
- Use the extracted tokens and component guidance to style the challenge dashboard, not to copy G4 proprietary assets.

## Product Context

The current challenge front-end is a minimal Streamlit dashboard for an executive churn diagnosis. The G4 identity should make the output feel like a serious business review for operators and founders, not like a marketing landing page.

## Art Direction

- Family: executive editorial workspace.
- Composition: dark header or executive cover, light analytic workspace, sparse gold accents.
- Density: scan-first for dashboard modules, more compact than the G4 marketing homepage.
- Color behavior: navy and warm off-white dominate; gold is reserved for hierarchy and actions; rust is only for risk/negative states.
- Material: flat premium surfaces, modest radius, subtle borders, low shadow usage.
- Shape: mostly square or low-radius rectangles, with pills only for status chips.
- Motion: mostly static; use 0.3s hover transitions if web UI supports it.

## Dashboard Mapping

1. App shell:
   - Use `#001F35` for the top header/sidebar.
   - Use `#F5F4F3` for the main content background.
   - Use `#B9915B` for primary action and active tab states.

2. Executive summary:
   - Use a dark navy hero band only at the top.
   - Keep the headline in Manrope semibold.
   - Add one gold italic or serif phrase at most if the page needs editorial emphasis.

3. KPI row:
   - Four cards echo the G4 business-line grid.
   - Recommended cards: churn rate, ARR at risk, priority accounts, top churn driver.
   - Use white cards on off-white background with thin low-contrast borders.

4. Findings:
   - Use section headers in navy, with a small gold divider or gold label.
   - Each finding should follow the project narrative contract: signal, evidence, interpretation, action.

5. Risk/account tables:
   - Use Manrope, 14px dense text.
   - Use gold for selected filters and high-priority markers.
   - Use rust only for high-risk churn state, never as general decoration.

6. Charts:
   - Avoid bright multi-color chart palettes.
   - Primary series: navy.
   - Highlight series: gold.
   - Risk/negative series: rust.
   - Neutral gridlines: `#D6D5D5`.

## Streamlit CSS Notes

Streamlit cannot fully reproduce a custom design system without custom CSS injection. Keep the MVP modest:

- Override page background, header text, buttons, metric cards, tabs, tables, and alert/risk chips.
- Avoid heavy hero sections, carousels, large mentor photography, and marketing nav patterns.
- Do not load G4 logos or photos unless usage rights are confirmed.
- If `PPMuseum` is not licensed for the deliverable, use `Libre Baskerville` only for optional italic emphasis and `Manrope` for everything else.

## Accessibility

- On navy backgrounds, use `#F5F4F3` text.
- Do not use gold body text on off-white for long copy; reserve gold for short labels and accent words.
- Add visible focus outlines using `2px solid #B9915B`.
- Respect reduced motion if any animation is added.
