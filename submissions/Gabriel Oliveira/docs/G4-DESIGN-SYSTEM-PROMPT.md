# G4 — Super Prompt do Design System

> Prompt consolidado para implementar a identidade visual do G4 Business
> no Challenge 003 (Lead Scorer). Colar no GitHub Copilot (GLM-5.2) no
> início de cada bloco de UI. Substitui a Seção 5 do `HARNESS_STEPS.md`.

**Skill oficial:** `design-system-g4`
**Agent envelope recomendado:** `[AGENT: BUILDER]`
**Origem dos tokens:** extração Playwright de g4business.com (2026-07-06)

---

## Como usar

1. Abra este arquivo na sidebar.
2. Copie o bloco completo abaixo (entre as cercas `<<<` e `>>>`).
3. Substitua os placeholders `{...}` pela tarefa concreta da iteração.
4. Cole no Copilot Chat no início do bloco de UI.
5. Ao final, rode o checklist "Definition of Done" antes de commit.

---

## Bloco do Super Prompt

<<<
[AGENT: BUILDER] [SKILL: DESIGN-SYSTEM-G4]

Você está implementando UI para o **Challenge 003 — Lead Scorer** do G4
AI Master Challenge. A ferramenta é usada por 35 vendedores e managers
regionais segunda-feira 9h. Audiência não-técnica. Textos em PT-BR.

**Persona alvo:** Head de RevOps julgando a tela.
**Vibe:** Sóbrio, espaçoso, editorial, premium. Nada de gradientes neon/pop.

### Rígido — Tokens extraídos do g4business.com

NÃO introduza valores fora destas tabelas.

**Cores**

| Token | Valor | Papel |
|-------|-------|-------|
| `--primary-hover` | `#842E20` | Texto primary (hover) |
| `--primary-color` | `#AF4332` | Texto primary |
| `--text-muted` | `#64748B` | Texto secundário |
| `color-7` | `#D1D5DB` | Surface |
| `color-1` | `#001F35` | Texto primary (navy) — base da app |
| `color-5` | `#B9915B` | Accent (gold) |
| `color-6` | `#25D366` | Accent (green báoias) |
| `color-10` | `#FFFFFF` | Border / fundo |
| `color-8` | `#EEEEEE` | Texto light |
| `color-9` | `#F5F4F3` | Texto light / cream — secondary bg |

**Mapeamento de aplicação (Lead Scorer):**
- fundo principal → `color-10` (`#FFFFFF`)
- texto/headers/nav → `color-1` (`#001F35`)
- secondary bg / hero / seções premium → `color-9` (`#F5F4F3`)
- badge score >80 → `color-6` (`#25D366`) em wash 10% opacity, texto sólido
- badge score 50-80 → `color-5` (`#B9915B`) em wash 10%
- badge score <50 → `--primary-color` (`#AF4332`) em wash 10%
- hover de CTA → `--primary-hover` (`#842E20`)
- tabela zebra → alternar `color-10` e `color-9`

**Tipografia (3 typefaces)**

Pilha: `PPMuseum, Libre Baskerville, Manrope`

| Token | Tamanho | Uso |
|-------|---------|-----|
| `text-xs` | 6px | Captions, metadata |
| `text-sm` | 12px | Labels, secundário |
| `text-base` | 14px | Body (default) |
| `text-lg` | 16px | Subheadings, ênfase |
| `text-xl` | 17px | Section headings |
| `text-2xl` | 19px | Section headings |
| `text-3xl` | 24px | Section headings |
| `text-4xl` | 26px | Section headings |
| `text-9` | 28px | Display |
| `text-10` | 30px | Display |
| `text-11` | 32px | Display |
| `text-12` | 36px | Display |
| `text-13` | 40px | Display (H2) |
| `text-14` | 56px | Display (H1) |
| `text-15` | 112px | Hero excepcional |

Weights disponíveis: `200 · 300 · 400 · 600 · 800`
Line-heights permitidos: `56 · 39 · 38.4 · 19.2 · 30.72 · 30.4 · 36 · 24 · 12 · 20.8 · 12.8 · 16 · 112 · 20.736 · 60 · 42 · 6 · 21` (px)

Aplicação:
- Display (hero, H1, H2): `PPMuseum` weight 300, H1=56px, H2=40px
- Editorial (subtítulos, citações): `Libre Baskerville`
- Body / UI / dados / CTAs: `Manrope` weight 400 default, 800 para fortes
- Sentence case NUNCA uppercase em body/parágrafo — só acrônimos

**Spacing (base 4px)**

`space-1: 2px` · `space-2: 5px` · `space-3: 8px` · `space-4: 10px`
`space-5: 11px` · `space-6: 13px` · `space-7: 16px` · `space-8: 19px`
`space-9: 20px` · `space-10: 36px` · `space-11: 64px` · `space-12: 72px`  
`space-13: 95px`

Padding generoso = vibe premium. Respira entre sections (>= `space-10`).

**Shapes (border-radius)**

`radius-sm: 3px` (CTA, badge, campo) · `radius-md: 10px` (card pequeno)  
`radius-lg: 20px` (card grande, modal) · `radius-xl: 50px` (pill excepcional)  
`radius-full: 50%` (avatar, ícone circular) · `radius-6: 999px` (pill tag)

Default: CTAs e campos usam `radius-sm` (3px) — nada de pills salientes.

**Motion**

`duration-fast: all` · `duration-fast: transform` · `duration-fast: none`  
`duration-base: 0.25s` · `duration-base: 0.3s`  
`duration-base: background 0.3s, border 0.3s, box-shadow 0.3s, transform 0.4s`  
`duration-base: opacity 0.3s`

Elevation: nenhum token detectado — não inventar sombras pesadas.
Use transitions suaves em estados interativos, não animações decorativas.

### Workflow de component authoring

Para cada componente que criar nesta iteração, entregue nesta ordem:

1. **Intent** — 1 frase: o que faz e por que existe
2. **Token map** — lista de todos os tokens usados (nome, não valor cru)
3. **Anatomy** — partes nomeadas com token assignment
4. **States** — default, hover, focus-visible, active, disabled, loading, error, empty
5. **Interactions** — keyboard (Tab/Enter/Escape/Setas), pointer, touch, edge cases (overflow, trunc, max content)
6. **A11y** — ARIA roles/labels, contraste WCAG 2.2 AA ( verificável pass/fail), focus visível a 3:1
7. **Anti-patterns** — pelo menos 1 exemplo concreto de uso errado
8. **Definition of Done checklist** — itens verificáveis mecanicamente

### Constraints rígidas

**Sempre:**
- Referencie tokens por nome, nunca por valor cru. (\`color-1\`, não \`#001F35\`.)
- Todo elemento interativo tem hover, focus-visible, disabled.
- Segue grid 4px.
- Cumpre WCAG 2.2 AA mínimo de contraste.
- Sentence case. Reserva ALL CAPS pra acrônimos.

**Nunca:**
- Cor fora da paleta extraída.
- Espaçamento arbitrário — só a escala acima.
- Border-radius fora do set (3, 10, 20, 50, 50%, 999px).
- Body ou parágrafo em uppercase.
- Elemento interativo aninhado (botão dentro de link).
- Shipar componente sem hover/focus-visible/disabled.
- Sombras pesadas / gradientes neon-pop.
- Hardcodear hex, px, ou font fora destas tabelas.

### Aplicação específica — Lead Scorer (Streamlit)

- `.streamlit/config.toml`:

```toml
[theme]
base = "light"
primaryColor = "#001F35"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F4F3"
textColor = "#001F35"
font = "sans serif"
```

- Manrope + PPMuseum + Libre Baskerville via Google Fonts no `st.markdown` head HTML custom.
- CTA: `radius-sm` (3px), weight 800, sem uppercase.
- Tabela de deals: sem bordas pesadas, zebra com `color-9`.
- Score cards: `radius-md` (10px), padding `space-10` mínimo.
- Status badge (bandas de score): fundo wash 10% opacity, texto sólido.
- Histograma/scatter Plotly: cores dos markers respeitando badge bands,
  fundo transparente, gridlines em `color-7` sutis.
- Sidebar filtros: labels `text-sm`, campos `radius-sm`, spacing `space-7`.
- KPI cards topo: 4 cards, números em `text-13` (40px), label `text-sm` `muted`.

### Tarefa desta iteração

{DESCREVER AQUI A TAREFA ATÔMICA — ex: "construir o score card expansível
mostrando breakdown dos 6 componentes com label explicativa PT-BR"}

### Saída esperada

- Código Python/Streamlit pronto pra rodar (sem placeholder).
- Documentação inline do componente seguindo o workflow de 8 passos.
- Definition of Done auto-preenchido pelo agente.
- Sem invenção de coluna do dataset — só nomes que eu passar.
- Sem paths absolutos — `pathlib.Path(__file__).parent`.

Antes de entregar, rode você mesmo o checklist de Definition of Done e
marque o que passou. Se algo falhou, corrija antes de me devolver.
>>>

---

## Notas de manutenção

- Quando extrair novamente do site (ou quando a marca mudar), **atualize
  este arquivo antes do `HARNESS_STEPS.md`** — ele é a fonte canônica de
  tokens para UI.
- Diferenças vs. Seção 5 do `HARNESS_STEPS.md`: este super prompt usa a
  paleta completa extraída (10 cores, 3 typefaces) — a versão antiga do
  harness tinha apenas 6 cores e 2 typefaces. **Este arquivo prevalece.**
- Os tokens de badge de score (verde/amarelo/vermelho) agora são
  `color-6` / `color-5` / `--primary-color` — NÃO usar mais
  `--g4-success/warning/danger` (deprecados da extração antiga).
