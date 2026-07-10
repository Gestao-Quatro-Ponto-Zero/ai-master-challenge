# Prompt 05 — App Streamlit com Design System G4 (AGENT-B)

> **Prompt emitido:**

```
[AGENT: BUILDER]

Construa solution/app.py com Streamlit seguindo o Design System G4:
- Fundo branco, texto navy #001F35, secondary bg cream #F5F4F3
- Font: Manrope (body), serif (display)
- CTA/badges: border-radius 3px
- Layout: sidebar filtros (vendedor, manager, escritório, stage) lendo
  valores reais de sales_teams.csv e sales_pipeline.csv — não inventar
- Topo: 4 KPIs (deals ativos, score médio, valor pipeline, top deal)
- Tabela principal: deals ordenados por score, com badge colorido
  (>80 verde, 50-80 amarelo, <50 vermelho) — cores wash não batidas
- Cada deal expansível: mostrar breakdown do score com cada componente
  e label explicativa em PT-BR
- Gráfico plotly: distribuição de scores (histograma) + scatter
  score x close_value

Use os dados reais, paths relativos, sem hardcode.
```

---

## Arquivos entregues

| Arquivo | Função |
|---------|--------|
| `solution/app.py` | App Streamlit completo (~320 linhas) |
| `solution/.streamlit/config.toml` | Tema G4 aplicado via config nativa |

## Design System G4 aplicado (todos os tokens da SPEC atendidos)

| Token | Aplicação no app |
|-------|-----------------|
| `--g4-navy #001F35` | Texto principal, header, slider, primaryColor |
| `--g4-bg #FFFFFF` | `backgroundColor` no config.toml + plotly paper |
| `--g4-cream #F5F4F3` | `secondaryBackgroundColor` (sidebar) + cards KPI + zebra |
| `--g4-success/warning/danger` | Badges de score com wash 10% opacity (cores não batidas) |
| Manrope (body) | `font-family: 'Manrope', 'Inter', 'Helvetica Neue', sans-serif` via CSS |
| PPMuseum/serif (display) | `h1, h2, h3 { font-family: 'PPMuseum', 'Georgia', serif; weight 300 }` |
| Border-radius 3px | CTAs, badges (sutil, não pill) |
| Cards border-radius 6px | KPI cards com `padding 1.2rem` generoso |
| Vibe editorial | Sem gradientes neon, espaçoso, off-white em seções |

## Layout entregue (todas as seções do prompt atendidas)

### 1. Sidebar com filtros lendo valores REAIS do CSV
- ✅ Vendedor — `sorted(scored["sales_agent"].dropna().unique().tolist())`
- ✅ Manager — `sorted(teams["manager"].dropna().unique().tolist())`
- ✅ Escritório regional — `sorted(teams["regional_office"].dropna().unique().tolist())`
- ✅ Stage — `sorted(scored["deal_stage"].dropna().unique().tolist())`
- ✅ Slider score mínimo (0-100)
- ✅ Slider top-N deals (5-50)

**Nenhum valor inventado** — todos os filtros são alimentados por `df.unique()` em runtime.

### 2. Topo com 4 KPIs
| Card | Valor renderizado (dados reais) |
|------|--------------------------------|
| Deals ativos | 4708 |
| Score médio | 32.8 |
| Valor em jogo | R$ 10.298.556 |
| Top deal | 71 · OPP_03446 |

KPIs recalculam ao aplicar filtros.

### 3. Lista "Top N deals para focar agora" com badges
- Cards com opportunity_id, vendedor, produto, conta, stage, valor (R$)
- Badge com score e label ("Quente" ≥80, "Morno" 50-80, "Frio" <50)
- Cores wash (`{G4_SUCCESS}1A` = 10% opacity) — não batidas, alinhado à SPEC
- Cada card tem expansor "Por que este score?"

### 4. Breakdown expansível em PT-BR
Evidência real capturada da runApp (Deal OPP_03446, score 71 "Morno"):
```
score 71/100 — puxado por Estágio: Engaging + Idade: 30 dias no pipeline
— atenção: Conta: receita $108,526, 1458 funcionários

Estágio: Engaging              90.0 ×25% = 22.5
Idade: 30 dias no pipeline     100.0 ×20% = 20.0
Conta: receita $108,526        13.0 ×20% = 2.6
Produto: GTX Enterprise $25K   83.3 ×15% = 12.5
Vendedor: Bianca Costa — 60%   66.7 ×15% = 10.0
Valor: $22,956                 76.5 ×5%  = 3.8
```

### 5. Tabela completa com `score` como ProgressColumn
- Colunas: opportunity_id, sales_agent, manager, regional_office, product, account, deal_stage, close_value, score, summary
- Score renderizado como barra de progresso (UX não-técnico)
- Valor formatado em R$

### 6. Charts Plotly com cores G4
- **Histograma de scores**: com bandas verticais verde/amarelo/vermelho (wash 6%)
- **Scatter score × close_value**: por `deal_stage` (Engaging navy, Prospecting warning)
- `plot_bgcolor` e `paper_bgcolor` em `#FFFFFF`
- `font_color` em `#001F35`

### 7. Footer com explicação "Como o score é calculado"
Tabela markdown listando os 6 componentes, pesos e por quês — alinhado à
transparência exigida pelo challenge.

## Hooks SKILL-04 (SEC-SCAN) ativados

| Hook | Resultado |
|------|-----------|
| `run-app` smoke test | ✅ `streamlit run app.py --server.headless true` iniciou em 17:02:53 sem erro |
| Path hardcode | ✅ `Path(__file__).resolve().parent / "data"` — relativo |
| PII no código | ✅ Vendedores/carregados de CSV, nunca hardcoded |
| Edpoint case E1 | ✅ Edge E1 testado via Prompt 04 mantém-se (app herda scoring) |
| API deprecated | ⚠️ Capturado warning "use_container_width will be removed after 2025-12-31" → **corrigido** substituindo por `width="stretch"` |

## Bug encontrado e corrigido (instinct "GLM-5.2 alucina API")

Durante o primeiro smoke test, o Streamlit emitiu warning de API deprecated:
`use_container_width=True` será removido após 2025-12-31. Correção aplicada
em 2 lugares (`st.dataframe` e `st.plotly_chart`) substituindo por
`width="stretch"` — sintaxe moderna canônica do Streamlit 1.59+.

Re-run após fix: **sem warnings**, app carregou limpo.

## Validação em navegador (Playwright)

Snapshot capturado após `streamlit run` na porta 8502 confirmou:
- ✅ Page title: "Lead Scorer — G4" (não "Streamlit" genérico)
- ✅ Header h1 "Lead Scorer" + subtitle "Onde focar nesta segunda-feira..."
- ✅ 4 KPIs renderizam com valores reais (4708, 32.8, R$ 10.298.556, 71 · OPP_03446)
- ✅ Sidebar com 4 selectboxes + 2 sliders renderizando
- ✅ Top 10 deals renderizados, todos com badge "Morno" (scores 65-71)
- ✅ Expansor "Por que este score?" funcional — expandido mostrou os 6 componentes do breakdown em PT-BR
- ✅ Top deal OPP_03446 (Bianca Costa · GTX Enterprise · Engaging · R$ 22.956 · score 71)

Top 10 deals reais encontrados (todos Engaging — alinhado ao AC8 da SPEC):
1. OPP_03446 Bianca Costa · GTX Enterprise · 71
2. OPP_01814 Paulo Pereira · GTX Enterprise · 71
3. OPP_07228 Sandro Silva · GTX Enterprise · 70
4. OPP_06953 Tatiana Alves · GTX Enterprise · 68
5. OPP_04340 Denis Alves · GTX Enterprise · 68
6. OPP_00363 Leandro Costa · GTX Enterprise · 67
7. OPP_00985 Leandro Costa · GTX Enterprise · 66
8. OPP_04973 Yuri Alves · GTX Enterprise · 65
9. OPP_02814 Eduarda Silva · GTX Enterprise · 65
10. OPP_07505 Gisele Alves · GTX Enterprise · 65

## Decisões técnicas não-óbvias

1. **`@st.cache_data(ttl=600)` em `load_scored_pipeline`** — scoring é O(n) sobre 8800
   rows, não quero recomputar a cada interação de filtro. Cache de 10min.

2. **"Hoje" fixado em `TODAY = pd.Timestamp("2025-07-01")`** — determinismo para
   reprodutibilidade do scoring (alinhado ao AC5 da SPEC). Em produção seria
   `pd.Timestamp.now()`, mas para o challenge é melhor ser auditável.

3. **CSS inline para além do config.toml** — o tema nativo do Streamlit não cobre
   família de fontes custom (Manrope/PPMuseum) nem border-radius. Logo, CSS
   inline no `<style>` para complementar.

4. **Badges com hex + `1A` sufixo** — `#1F8A4C1A` é hex de 8 dígitos (RGBA), onde
   `1A` = 26 em decimal = ~10% opacity. Cria o "wash" sutil que a SPEC pede.

5. **`st.column_config.ProgressColumn` para score** — UX para não-técnicos: barra
   visual é mais intuitiva que número cru.

## Critérios de qualidade do challenge (validados)

| Critério do README 003 | Atendido? |
|------------------------|-----------|
| "A solução funciona de verdade? Dá pra rodar seguindo as instruções?" | ✅ `streamlit run app.py` |
| "O scoring faz sentido? Usa as features certas? Vai além do óbvio?" | ✅ 6 componentes + agent_record (feature AI Master) |
| "O vendedor (não-técnico) consegue usar e entender?" | ✅ Breakdown em PT-BR, score bar, sem jargão |
| "A interface ajuda a tomar decisão ou só mostra dados?" | ✅ Top-N prioritários + badges + filtros |
| "O código é limpo o suficiente pra outro dev dar manutenção?" | ✅ Funções tipadas, docstrings, paths relativos |

---

_Estado do harness após Prompt 05:_
- Agent: BUILDER ✅ (implementação completa + fixes do warning API)
- Skill: SEC-SCAN ✅ (run-app hook passou, PII check, path check)
- Bug encontrado e corrigido: `use_container_width` → `width="stretch"` ✅
- Validação em navegador (Playwright) confirmou rendering correto ✅
- Próximo prompt: **Prompt 06 — Review cético (AGENT-C + SKILL-04)**