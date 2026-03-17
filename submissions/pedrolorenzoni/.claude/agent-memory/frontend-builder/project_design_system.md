---
name: G4 Business Design System
description: Complete design tokens from id-visual.md — colors, typography, spacing, components
type: project
---

Design system from `id-visual.md` for G4 Business (g4business.com).

## Colors
- Primary: `#af4332` (red/terracota — CTAs, errors, risk indicators)
- Primary hover: `#842E20`
- Secondary: `#0f1a45` (navy — headers, dark sections)
- Accent: `#b9915b` (gold — hover borders, decorative lines, premium badges)
- BG: `#fafbfc`
- Surface: `#ffffff`
- Text: `#001f35`
- Text muted: `#60708a`
- Border: `#e5e7eb`
- Success: `#25D366`

## Typography
- Font sans: Manrope (200-800) — all headings and body
- Font ui: Inter (400, 600) — captions and meta
- Font serif: Libre Baskerville 400 italic — quotes only
- Display/H1: Manrope 800, 42px
- H2: Manrope 700, 36px
- H5: Manrope 500, 18px
- Body: Manrope 400, 16px
- Caption/Meta: Inter 400, 13px

## Spacing
- Base unit: 8px
- Scale: 4, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64, 80, 96, 120px

## Border Radius
- sm: 5px (tags, badges)
- md: 10px (cards, inputs)
- lg: 16px (large cards, modals)
- xl: 20px (hero cards)
- full: 9999px (pills, avatars)
- Buttons: 12px

## Shadows
- sm: `0 2px 8px rgba(0,0,0,0.06)`
- md: `0 0 22px 0 rgba(0,0,0,0.14)` — standard card
- lg: `6px 6px 9px rgba(0,0,0,0.20)`
- xl: `12px 12px 50px rgba(0,0,0,0.40)`

## Components
- Button Primary: #af4332 bg, white, radius 12px, padding 12px 24px
- Button Gold: #b9915b bg, white — premium CTAs
- Card: white bg, border rgba(0,31,53,0.15), radius 16px, shadow-md; hover: border #b9915b 2px
- Input: border #e5e7eb, radius 10px, focus border #af4332 + shadow
- Navbar: fixed 70px, #0f1a45 bg, white text/icons
- Badge primary: bg rgba(175,67,50,0.12), text #af4332

## Tailwind Config
Already configured in `tailwind.config.ts` with all these tokens as custom classes.
- `bg-primary` = #af4332
- `bg-secondary` = #0f1a45
- `bg-accent` = #b9915b
- `text-text-main` = #001f35
- `text-text-muted` = #60708a
- `bg-surface` = #ffffff
- `bg-fade` = #F5F4F3
- `bg-bg` = #fafbfc
- `font-sans` = Manrope
- `font-ui` = Inter
- `font-serif` = Libre Baskerville
