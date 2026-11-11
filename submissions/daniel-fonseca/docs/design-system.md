# Design system — base G4 "Órbita"

> Fonte: [joaovitor2763/Core-Slides-G4](https://github.com/joaovitor2763/Core-Slides-G4) (licença MIT, © 2026 G4 Educação), `templates-short-deck/style.css` e `AGENTS.md`.
> O repositório é feito para slides 16:9 em HTML; aqui adaptamos **tokens e regras** para uma interface web (dashboard/console), não os layouts.

## Tokens de cor

| Token | Light | Dark | Uso |
|---|---|---|---|
| `--bg` | `#F5F4F3` (paper) | `#001525` (navy-700) | fundo da página |
| `--surface` | `#FFFFFF` | `rgba(255,255,255,.045)` | cards |
| `--surface-2` | `#EFEDE9` | `rgba(255,255,255,.08)` | áreas secundárias |
| `--text-1` | `#001F35` | `#F2F6F9` | texto principal |
| `--text-2` | `#1D3A4D` | `#C3D3DD` | texto secundário |
| `--text-3` | `#5A7184` | `#7E99AB` | metadados, eixos |
| `--border` | `rgba(0,31,53,.09)` | `rgba(255,255,255,.09)` | divisores |
| `--gold` | `#B9915B` | `#C9A05C` | **acento único** |
| `--green` | `#12693B` | `#4ADE80` | positivo / ok |
| `--red` | `#842E20` | `#F87171` | negativo / alerta |

Escala navy: `50 #E6EEF3 · 100 #B3CCD9 · 200 #80AABF · 500 #001F35 · 600 #001A2D · 700 #001525 · 800 #00101D · 900 #000B15`.
Escala gold: `300 #D4B189 · 500 #B9915B · 700 #8E6F44`.

## Tipografia
- **Libre Baskerville** — títulos de destaque e frases editoriais (`--serif`).
- **Manrope** 400–700 — corpo, UI e números hero (`--sans`, `--num`).
- **IBM Plex Mono** — IDs, eixos, código (`--tech`).

## Forma
Raios `10 / 16 / 22 / 30 / pill`; sombras suaves tingidas de navy; espaçamento generoso.

## Regras herdadas que valem para o dashboard
- **Um único protagonista dourado por tela** — o dourado marca o número/insight principal; o resto usa neutros e hierarquia tipográfica.
- "Pills" só para estado, seleção ou duração (ex.: nível de automação, status do ticket) — não decorar listas com cápsulas.
- Labels nunca dependem só de cor (acessibilidade).

## Adaptação para dados
Para os gráficos, a paleta categórica precisa ser derivada (navy/gold sozinhos não bastam para 8 categorias do DS2) — a definir na fase do dashboard, validando contraste em light e dark.

## Ressalva
O app é um protótipo de candidato que usa a linguagem visual do G4 por afinidade com a vaga; não se apresenta como produto oficial do G4.
