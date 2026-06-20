# Foco — Identidade de Marca

> Produto: **Foco** · Tagline: **"O que fechar primeiro."**
> Um lead scorer que não mostra dados — diz onde agir.

## 1. Posicionamento

| | |
|---|---|
| **O que é** | Ferramenta de priorização de pipeline para times de vendas |
| **Para quem** | Vendedor (uso diário) · Manager (visão do time) · RevOps (saúde) |
| **Promessa** | "Abra na segunda de manhã e saiba exatamente onde focar." |
| **Personalidade** | Direto, confiável, sem jargão. Um copiloto, não um relatório. |
| **Anti-marca** | Não é dashboard de BI, não é planilha, não é "mais um número". |

O nome **Foco** carrega a função: reduzir 2.089 deals abertos a uma lista curta e priorizada. Tudo na marca reforça *clareza e decisão*.

## 2. Logo

Wordmark simples com um **ponto de mira** substituindo o "o" central — alvo = foco/priorização.

```
    F O C O          →  F ⊙ C O      (o 1º "O" vira um alvo ◎)
   ───────────
   O que fechar primeiro.
```

- **Símbolo isolado** (favicon/app icon): o alvo `◎` no indigo da marca sobre fundo claro.
- Construção implementável sem designer: emoji `🎯`/`◎` + wordmark em Inter Bold. SVG opcional em `assets/`.
- Área de proteção: margem = altura do "F" em volta do lockup. Nunca distorcer, rotacionar ou aplicar sombra.

## 3. Paleta de cores

Base sóbria (confiança/RevOps) + **sistema semântico de prioridade** (o coração da UI: cor = decisão).

### Marca
| Token | Hex | Uso |
|-------|-----|-----|
| `ink` | `#0F172A` | Texto principal, títulos |
| `slate` | `#64748B` | Texto secundário, labels |
| `surface` | `#FFFFFF` | Fundo de cards |
| `canvas` | `#F8FAFC` | Fundo da página |
| `border` | `#E2E8F0` | Divisórias |
| **`brand`** | **`#4F46E5`** | Cor primária (ações, links, logo) — indigo |
| `brand-700` | `#4338CA` | Hover/ativo |
| `accent` | `#06B6D4` | Destaques pontuais (ciano) |

### Sistema de prioridade (semântico — sempre cor + ícone + texto, nunca só cor)
| Tier | Cor | Fundo do badge | Ícone | Significado |
|------|-----|----------------|-------|-------------|
| **Foco Agora** | `#EF4444` | `#FEF2F2` | 🔥 | Alta prioridade — agir hoje |
| **Trabalhar** | `#F59E0B` | `#FFFBEB` | ⭐ | Nutrir — manter no radar |
| **Baixa Prioridade** | `#64748B` | `#F1F5F9` | ⏳ | Esperar / desqualificar |

### Sinais de fator (no breakdown do score)
| Token | Hex | Uso |
|-------|-----|-----|
| `positive` | `#10B981` | Fator que ajuda (win-rate alto, valor) |
| `warning` | `#F59E0B` | Deal passando do ciclo (>57d) |
| `danger` | `#EF4444` | Crítico (>88d) |

> **Acessibilidade:** todos os pares texto/fundo passam contraste **WCAG AA** (≥4.5:1). A cor **nunca** é o único sinal — sempre acompanha ícone + rótulo (daltônicos e leitura rápida).

## 4. Tipografia

| Papel | Fonte | Notas |
|-------|-------|-------|
| UI / texto | **Inter** | limpa, neutra, ótima em telas; fallback `system-ui` |
| Números/score | **Inter Tabular** (`font-variant-numeric: tabular-nums`) | colunas de score alinham |
| Logo | Inter Bold / ExtraBold | wordmark |

Escala: Título 24/28 · Seção 18/20 · Corpo 14/16 · Label 12 uppercase tracking. Score em destaque: 32-40 bold.

## 5. Voz e microcopy

Direto, em linguagem de vendedor. Verbo no imperativo na ação. Nunca jargão técnico ("modelo", "feature", "threshold") na tela.

| Em vez de… | Escreva… |
|------------|----------|
| "Score: 84 (alta confiança)" | "**84 · Foco Agora** 🔥" |
| "Probabilidade de conversão: 0.70" | "Você fecha **70%** com esse perfil" |
| "Deal aging acima do threshold" | "Aberto há **64 dias** — passando do ciclo" |
| "Sem dados de engajamento" | "Ainda não engajado" |
| Empty state vazio | "Nenhum deal em Foco Agora agora. Bom trabalho. 👏" |

## 6. Aplicação no Streamlit (implementável já)

`.streamlit/config.toml`:
```toml
[theme]
base = "light"
primaryColor = "#4F46E5"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F8FAFC"
textColor = "#0F172A"
font = "sans serif"
```
Badges de tier e cores de fator via CSS injetado (`st.markdown(unsafe_allow_html=True)`) usando os hex acima — tokens centralizados em `app/theme.py` (espelha esta paleta, fonte única de verdade).

## 7. Do / Don't

✅ Cor com propósito (prioridade) · espaço em branco · 1 ação clara por card · números grandes e escaneáveis.
❌ Arco-íris de cores decorativas · gráficos de pizza · tabela densa como tela inicial · jargão · mais de 3 tiers.
