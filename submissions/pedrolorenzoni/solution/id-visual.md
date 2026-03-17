# Identidade Visual — G4 Business

> Análise baseada em: https://g4business.com/ · 2026-03-14

---

## Visão Geral

- **Estilo:** corporativo, premium, bold, sério, moderno
- **Tom:** Formal, autoritativo, confiante — voltado a negócios B2B e educação executiva
- **Motivos visuais:** Combinação de tipografia serif elegante com sans-serif geométrica, paleta escura com acento terracota/ferrugem, detalhes em dourado, uso de dark sections contrastando com fundos claros

---

## Paleta de Cores

| Token | Hex | Uso |
|-------|-----|-----|
| `--color-primary` | `#af4332` | CTAs, botões principais, destaques de marca |
| `--color-primary-hover` | `#842E20` | Hover nos botões primários |
| `--color-secondary` | `#0f1a45` | Seções escuras, headers, backgrounds navy |
| `--color-accent` | `#b9915b` | Linhas decorativas, highlights dourados, bordas de destaque |
| `--color-bg` | `#fafbfc` | Fundo da página |
| `--color-surface` | `#ffffff` | Cards, modais, superfícies elevadas |
| `--color-text` | `#001f35` | Texto principal (dark navy quase preto) |
| `--color-text-muted` | `#60708a` | Texto secundário, subtítulos, metadados |
| `--color-border` | `#e5e7eb` | Bordas padrão |
| `--color-border-subtle` | `rgba(0, 31, 53, 0.15)` | Bordas de card sutis (`#001F3526`) |
| `--color-success` | `#25D366` | WhatsApp green (único uso de sucesso encontrado) |
| `--color-warning` | `#b9915b` | Avisos (reutiliza o dourado) |
| `--color-error` | `#af4332` | Erros (reutiliza o primário) |
| `--color-dark` | `#000000` | Texto ou overlays full dark |
| `--color-fade` | `#F5F4F3` | Fundo alternativo levemente off-white |

### Gradientes

```css
/* Midnight — seções de destaque */
background: linear-gradient(135deg, rgb(2, 3, 129) 0%, rgb(40, 116, 252) 100%);

/* Blush Bordeaux — seções de call-to-action */
background: linear-gradient(135deg, #af4332 0%, #842E20 100%);

/* Dark Navy Overlay — sobre imagens */
background: linear-gradient(180deg, rgba(15, 26, 69, 0.0) 0%, rgba(15, 26, 69, 0.82) 100%);

/* Dourado sutil — linhas e separadores */
background: linear-gradient(90deg, transparent 0%, #b9915b 50%, transparent 100%);
```

---

## Tipografia

| Função | Família | Peso | Tamanho | Line-height | Letter-spacing |
|--------|---------|------|---------|-------------|----------------|
| Display/H1 | Manrope | 800 | 42px / 2.625rem | 1.1 | -0.02em |
| H2 | Manrope | 700 | 36px / 2.25rem | 1.2 | -0.01em |
| H3 | Manrope | 600 | 28px / 1.75rem | 1.3 | 0 |
| H4 | Manrope | 600 | 22px / 1.375rem | 1.4 | 0 |
| H5 | Manrope | 500 | 18px / 1.125rem | 1.4 | 0 |
| Body | Manrope | 400 | 16px / 1rem | 1.6 | 0 |
| Small | Manrope | 400 | 14px / 0.875rem | 1.5 | 0 |
| Caption / Meta | Inter | 400 | 13px / 0.8125rem | 1.4 | 0.01em |
| Quote / Destaque | Libre Baskerville | 200 | 20px / 1.25rem | 1.5 | 0 |

**Fonte principal:** `"Manrope"` — Google Fonts (pesos 200–800)
**Fonte de suporte:** `"Inter"` — Google Fonts (pesos 400, 600)
**Fonte decorativa:** `"Libre Baskerville"` — Google Fonts (peso 200, italic — apenas para citações)

```html
<!-- Google Fonts import -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&family=Inter:wght@400;600&family=Libre+Baskerville:ital,wght@1,400&display=swap" rel="stylesheet">
```

---

## Espaçamento & Layout

- **Unidade base:** 8px
- **Escala:** 4, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64, 80, 96, 120px
- **Max-width do container:** 1200px (wide) / 800px (content text)
- **Padding lateral:** 16px mobile / 24px tablet / 48px desktop
- **Grid:** 12 colunas, gap 24px

| Breakpoint | Valor |
|------------|-------|
| mobile | < 480px |
| mobile-lg | 480px – 767px |
| tablet | 768px – 1023px |
| desktop | ≥ 1024px |

---

## Bordas & Raios

| Token | Valor | Uso |
|-------|-------|-----|
| `--radius-sm` | `5px` | Tags, badges, inputs pequenos |
| `--radius-md` | `10px` | Cards padrão, botões |
| `--radius-lg` | `16px` | Cards grandes, modais, imagens |
| `--radius-xl` | `20px` | Hero cards, seções arredondadas |
| `--radius-full` | `9999px` | Pills, avatares, progress bar |

- **Bordas padrão:** `1px solid var(--color-border)` — `#e5e7eb`
- **Bordas de card:** `1px solid rgba(0, 31, 53, 0.15)` — sutil sobre fundo branco
- **Bordas de hover:** `2px solid var(--color-accent)` — `#b9915b` dourado

---

## Sombras

```css
--shadow-sm:  0 2px 8px rgba(0, 0, 0, 0.06);       /* Subtle — hover de links */
--shadow-md:  0 0 22px 0 rgba(0, 0, 0, 0.14);       /* Card padrão */
--shadow-lg:  6px 6px 9px rgba(0, 0, 0, 0.20);      /* Elementos elevados */
--shadow-xl:  12px 12px 50px rgba(0, 0, 0, 0.40);   /* Modal / hero destacado */
--shadow-outlined: 6px 6px 0px -3px #ffffff, 6px 6px 0px 0px #000000; /* Efeito gráfico bold */
```

---

## Animações

- **Duração padrão:** 200ms
- **Duração longa:** 300ms (modais, menus)
- **Easing:** `ease` / `cubic-bezier(0.4, 0, 0.2, 1)`

```css
transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);

/* Botões */
transition: transform 0.2s ease, filter 0.2s ease;

/* Hover de cards */
transition: box-shadow 0.2s ease, border-color 0.2s ease;
```

---

## Componentes

### Botões

| Variante | Aparência |
|----------|-----------|
| Primary | `#af4332` bg, branco, radius 12px, padding 12px 24px, fw 600, hover `#842E20` |
| Secondary | Transparente, borda `#af4332`, texto `#af4332`, hover bg `#af4332` branco |
| Ghost | Sem borda, texto `#60708a`, hover texto `#001f35` |
| Dark | `#0f1a45` bg, branco, mesmos raios e padding do primary |
| Gold | `#b9915b` bg, branco, para CTAs premium |

```css
.btn-primary {
  background: var(--color-primary);       /* #af4332 */
  color: #ffffff;
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  font-family: var(--font-sans);
  font-weight: 600;
  font-size: 15px;
  line-height: 1.4;
  cursor: pointer;
  transition: transform 0.2s ease, filter 0.2s ease, background 0.2s ease;
}
.btn-primary:hover {
  background: var(--color-primary-hover); /* #842E20 */
  transform: translateY(-1px);
}
.btn-primary:active {
  transform: translateY(0);
}

.btn-secondary {
  background: transparent;
  color: var(--color-primary);
  border: 2px solid var(--color-primary);
  border-radius: 12px;
  padding: 10px 22px;
  font-weight: 600;
  font-size: 15px;
  transition: all 0.2s ease;
}
.btn-secondary:hover {
  background: var(--color-primary);
  color: #ffffff;
}
```

### Cards

```css
.card {
  background: var(--color-surface);               /* #ffffff */
  border: 1px solid rgba(0, 31, 53, 0.15);
  border-radius: 16px;
  padding: 24px;
  box-shadow: var(--shadow-md);                   /* 0 0 22px 0 rgba(0,0,0,0.14) */
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.card:hover {
  box-shadow: var(--shadow-lg);
  border-color: var(--color-accent);              /* #b9915b */
  border-width: 2px;
}
```

### Inputs

```css
.input {
  border: 1px solid var(--color-border);          /* #e5e7eb */
  border-radius: 10px;
  padding: 12px 16px;
  font-family: var(--font-sans);
  font-size: 15px;
  color: var(--color-text);                       /* #001f35 */
  background: var(--color-surface);               /* #ffffff */
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.input::placeholder {
  color: var(--color-text-muted);                 /* #60708a */
}
.input:focus {
  border-color: var(--color-primary);             /* #af4332 */
  box-shadow: 0 0 0 3px rgba(175, 67, 50, 0.15);
}
```

### Navegação

- **Estilo:** Fixed, fundo dark navy (`#0f1a45`), sólido
- **Altura:** 70px (desktop), 65px (mobile bottom nav)
- **Background:** `#0f1a45` — sem transparência ou blur na nav principal
- **Logo:** SVG branca `logo-g4-completa-branca.svg`
- **Links:** texto branco, hover com sublinhado ou cor `#b9915b`
- **Mobile:** Bottom navigation bar fixa com ícones 24×24px

```css
.navbar {
  position: fixed;
  top: 0;
  width: 100%;
  height: 70px;
  background: #0f1a45;
  display: flex;
  align-items: center;
  padding: 0 48px;
  z-index: 1000;
}
```

### Badges / Tags

```css
.badge {
  background: rgba(175, 67, 50, 0.1);
  color: var(--color-primary);                    /* #af4332 */
  border-radius: 9999px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.badge-gold {
  background: rgba(185, 145, 91, 0.15);
  color: var(--color-accent);                     /* #b9915b */
}

.badge-dark {
  background: rgba(15, 26, 69, 0.08);
  color: var(--color-secondary);                  /* #0f1a45 */
}
```

---

## CSS Variables — Pronto para usar

```css
:root {
  /* Colors */
  --color-primary:        #af4332;
  --color-primary-hover:  #842E20;
  --color-secondary:      #0f1a45;
  --color-accent:         #b9915b;
  --color-bg:             #fafbfc;
  --color-fade:           #F5F4F3;
  --color-surface:        #ffffff;
  --color-text:           #001f35;
  --color-text-muted:     #60708a;
  --color-border:         #e5e7eb;
  --color-border-subtle:  rgba(0, 31, 53, 0.15);
  --color-success:        #25D366;
  --color-warning:        #b9915b;
  --color-error:          #af4332;

  /* Typography */
  --font-sans:    'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-ui:      'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-serif:   'Libre Baskerville', Georgia, serif;

  /* Spacing */
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
  --space-20: 80px;
  --space-24: 96px;
  --space-30: 120px;

  /* Border radius */
  --radius-sm:   5px;
  --radius-md:   10px;
  --radius-lg:   16px;
  --radius-xl:   20px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm:  0 2px 8px rgba(0, 0, 0, 0.06);
  --shadow-md:  0 0 22px 0 rgba(0, 0, 0, 0.14);
  --shadow-lg:  6px 6px 9px rgba(0, 0, 0, 0.20);
  --shadow-xl:  12px 12px 50px rgba(0, 0, 0, 0.40);

  /* Animation */
  --transition:      all 200ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: all 300ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## Tailwind Config

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#af4332',
          hover:   '#842E20',
        },
        secondary: '#0f1a45',
        accent:    '#b9915b',
        bg:        '#fafbfc',
        fade:      '#F5F4F3',
        surface:   '#ffffff',
        'text-main':  '#001f35',
        'text-muted': '#60708a',
        border:    '#e5e7eb',
      },
      fontFamily: {
        sans:    ['Manrope', 'system-ui', 'sans-serif'],
        ui:      ['Inter', 'system-ui', 'sans-serif'],
        serif:   ['Libre Baskerville', 'Georgia', 'serif'],
      },
      fontSize: {
        'display': ['42px', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        'h2':      ['36px', { lineHeight: '1.2', letterSpacing: '-0.01em' }],
        'h3':      ['28px', { lineHeight: '1.3' }],
        'h4':      ['22px', { lineHeight: '1.4' }],
        'h5':      ['18px', { lineHeight: '1.4' }],
        'body':    ['16px', { lineHeight: '1.6' }],
        'sm':      ['14px', { lineHeight: '1.5' }],
        'xs':      ['13px', { lineHeight: '1.4', letterSpacing: '0.01em' }],
      },
      borderRadius: {
        sm:   '5px',
        md:   '10px',
        lg:   '16px',
        xl:   '20px',
        full: '9999px',
      },
      boxShadow: {
        sm:   '0 2px 8px rgba(0, 0, 0, 0.06)',
        md:   '0 0 22px 0 rgba(0, 0, 0, 0.14)',
        lg:   '6px 6px 9px rgba(0, 0, 0, 0.20)',
        xl:   '12px 12px 50px rgba(0, 0, 0, 0.40)',
      },
      maxWidth: {
        content: '800px',
        wide:    '1200px',
      },
    },
  },
}
```

---

## Logo & Iconografia

- **Logo:** Wordmark horizontal completa em SVG — `logo-g4-completa-branca.svg`. Versão branca usada no header dark navy. Provavelmente existe versão colorida/dark para fundos claros.
- **Tamanho padrão:** ~200px de largura no desktop
- **Ícones:** Estilo outline/filled, tamanho padrão 24×24px. Biblioteca provável: Lucide Icons ou Font Awesome (não confirmado via DevTools — verifique na inspeção)
- **Favicon:** Baseado na marca G4, provavelmente inicial "G4" ou ícone simplificado da logo

---

## Notas de Replicação

1. **Contraste navbar:** A navbar usa fundo `#0f1a45` (navy escuro) — todos os textos e ícones devem ser brancos (`#ffffff`) ou no máximo `rgba(255,255,255,0.8)` para estados inativos.

2. **Hierarquia tipográfica:** A combinação Manrope (headings bold) + Libre Baskerville (citações em itálico leve) é o que dá o caráter "premium executivo" ao site. Não substitua por Inter puro — o serif faz diferença.

3. **O dourado (`#b9915b`) é o detalhe diferenciador:** Use-o com moderação em linhas decorativas, hover de cards e bordas de destaque. Evite usá-lo em texto longo.

4. **Dark sections:** O site alterna entre fundos `#fafbfc` (claro) e `#0f1a45` (escuro). Em seções escuras, use texto `#ffffff` e bordas `rgba(255,255,255,0.15)`.

5. **Botões:** O border-radius de `12px` nos botões é levemente maior que o `10px` dos cards — isso é intencional e cria um contraste sutil de "suavidade".

6. **Overlay em imagens:** Use `background: linear-gradient(180deg, rgba(15,26,69,0) 0%, rgba(15,26,69,0.82) 100%)` sobre fotos para garantir legibilidade de texto branco.

7. **Churn Analysis context:** Para um dashboard de análise de churn, priorize:
   - Fundo `--color-bg` (`#fafbfc`) para a área de conteúdo
   - Navbar `#0f1a45` com logo branca
   - Cards brancos com `--shadow-md` e borda sutil
   - Métricas de risco em `--color-primary` (`#af4332` — vermelho terracota, semanticamente adequado para alertas de churn)
   - KPIs positivos em dourado `#b9915b` ou verde neutro
   - Tipografia Manrope 800 para números grandes de dashboard
