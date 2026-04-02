# PROMPT DE ATUALIZAÇÃO DO MVP — Pipeline Coach AI
# Módulo: Dashboard de Resultados do Vendedor (`/rep/results`)
# Versão: 1.1 — Adição ao MVP existente
# Destinatário: agente construtor de sites (Lovable, Bolt, v0, Cursor, Replit Agent ou equivalente)

---

## CONTEXTO

O MVP do Pipeline Coach AI já foi construído com:
- `/upload` — tela de upload dos CSVs
- `/rep` — dashboard de atividades do vendedor (prioridades, contas em risco, execution score)
- `/manager` — dashboard do gestor

**O que está faltando:** o vendedor não tem nenhuma visão de seus próprios resultados. Ele consegue ver o que fazer, mas não consegue ver o que já fez e como está performando historicamente.

Esta atualização adiciona uma nova rota `/rep/results` e uma aba "Resultados" na navegação do rep dashboard.

---

## ESCOPO DESTA ATUALIZAÇÃO

### O que adicionar
1. Nova rota `/rep/results` — Dashboard de Resultados do Vendedor
2. Aba de navegação "Resultados" no header/tab bar do módulo `/rep`
3. Nenhuma alteração nas rotas existentes — apenas adição

### O que NÃO alterar
- Lógica de upload de CSV existente
- Dashboard de atividades existente (`/rep` home)
- Dashboard do gestor (`/manager`)
- Scoring engine
- Store de dados em memória

---

## DADOS DISPONÍVEIS NOS CSVs (já carregados em memória)

Todos os cálculos usam os CSVs já carregados. Não há novo upload necessário.

```
REFERENCE_DATE = new Date('2017-12-27')  ← sempre esta data para o dataset histórico

Período com dados de fechamento: 2017-03 até 2017-12 (10 meses)
Total de deals Won: 4.238
Total de receita realizada: $10.005.534
Win rate geral: 63,2% (Won / Won+Lost)
```

### Anomalias de dados a considerar nesta feature
- `close_value` é string vazia para deals abertos — usar `safeFloat()` já implementado
- `close_date` é string vazia para deals abertos — nunca fazer parse sem verificar
- `account` pode ser string vazia — exibir como "Conta não identificada"
- Produto "GTX Pro" em `products.csv` = "GTXPro" em `sales_pipeline.csv` — normalização já implementada

---

## ESTRUTURA DA TELA `/rep/results`

### Layout geral

```
┌─────────────────────────────────────────────────────┐
│  [← Atividades]  [Resultados ●]   Seletor: Rep ▼   │  ← tab bar existente + aba nova
├─────────────────────────────────────────────────────┤
│  FAIXA DE KPIs GLOBAIS (4 cards)                    │  ← sempre visível
├─────────────────────────────────────────────────────┤
│  GRÁFICO 1: Receita Mensal (barras + linha WR)      │  ← ocupa largura total
├───────────────────────┬─────────────────────────────┤
│  GRÁFICO 2:           │  GRÁFICO 3:                 │
│  Receita por Produto  │  Ciclo de Fechamento        │
│  (timeline empilhada) │  (distribuição)             │
├───────────────────────┴─────────────────────────────┤
│  GRÁFICO 4: Receita Acumulada (área)                │
├───────────────────────┬─────────────────────────────┤
│  TABELA 5:            │  GRÁFICO 6:                 │
│  Top Contas Fechadas  │  Mix de Produtos (donut)    │
└───────────────────────┴─────────────────────────────┘
```

---

## COMPONENTE 1 — FAIXA DE KPIs

Quatro cards horizontais fixos no topo. Calculados para o vendedor selecionado, com base em todos os deals `Won`.

### KPI 1 — Receita Total Realizada
```
Valor:    soma de close_value de todos os deals Won do rep
Formato:  "$1,15M" (abreviar se >= 1M) ou "$478K" (se >= 1000)
Subtítulo: "{N} deals fechados"
Cor:      verde (#00e5a0)
```

### KPI 2 — Win Rate
```
Valor:    Won / (Won + Lost) × 100
Formato:  "63,1%"
Subtítulo: "{won}W / {lost}L"
Cor:      dinâmica:
  ≥ 65% → verde
  ≥ 60% → azul
  < 60% → âmbar
```

### KPI 3 — Ticket Médio
```
Valor:    soma(close_value) / count(Won deals)
Formato:  "$3.310" (sem abreviação — valores são pequenos)
Subtítulo: "por deal fechado"
Cor:      texto padrão
```

### KPI 4 — Ciclo Médio de Fechamento
```
Valor:    AVG(close_date - engage_date) para deals Won do rep
Formato:  "49d"
Subtítulo: "Empresa: 51,8d" (benchmark fixo do dataset)
Cor:
  ciclo_rep < 51.8 → verde (abaixo da média — bom)
  ciclo_rep >= 51.8 → âmbar (acima — precisa melhorar)

ATENÇÃO: só usar deals Won que tenham AMBOS engage_date e close_date preenchidos.
```

---

## COMPONENTE 2 — RECEITA MENSAL POR DEALS FECHADOS

### Tipo de gráfico
Gráfico de barras verticais com linha sobreposta. Usar Recharts `ComposedChart`.

### Dados
```typescript
// Para cada mês de 2017-03 a 2017-12:
interface MonthlyData {
  month: string        // "Mar", "Abr", ..., "Dez"
  monthKey: string     // "2017-03", ..., "2017-12"
  revenue: number      // soma close_value dos Won do rep naquele mês
  deals: number        // contagem de Won do rep naquele mês
  lost: number         // contagem de Lost do rep naquele mês
  winRate: number      // won / (won + lost) × 100, ou 0 se sem dados
}
```

### Referência de dados (Darcel Schlecht como exemplo)
```
Mar/17: $112.255 · 44W/13L · WR=77%
Abr/17: $92.830  · 26W/30L · WR=46%
Mai/17: $95.118  · 33W/24L · WR=58%
Jun/17: $122.127 · 37W/6L  · WR=86%
Jul/17: $96.411  · 30W/29L · WR=51%
Ago/17: $140.273 · 46W/30L · WR=61%
Set/17: $136.534 · 39W/7L  · WR=85%
Out/17: $130.432 · 32W/30L · WR=52%
Nov/17: $108.018 · 30W/25L · WR=55%
Dez/17: $119.216 · 32W/10L · WR=76%
```

### Configuração visual
```
Barras:       cor #3b82f6 (azul), altura proporcional à receita
              barra mais alta do rep em destaque: cor #00e5a0
Linha:        win rate (eixo Y direito, 0–100%), cor #f59e0b, dots nos meses
Eixo Y esq:  receita em $K
Eixo Y dir:  win rate em %
Tooltip:      ao hover: mês | receita | deals won | deals lost | win rate
Grid:         linhas horizontais sutis
```

### Insight automático abaixo do gráfico
```typescript
// Detectar padrão e mostrar insight em texto
const bestMonth = months.reduce((a, b) => a.revenue > b.revenue ? a : b)
const worstMonth = months.reduce((a, b) => a.revenue < b.revenue ? a : b)
const delta = ((bestMonth.revenue - worstMonth.revenue) / worstMonth.revenue * 100).toFixed(0)

// Texto: "📈 Melhor mês: Ago/17 ($140K). Pior mês: Abr/17 ($93K). 
//         Variação de 51% entre o melhor e o pior mês."
```

**Nota sobre o padrão global dos dados:** o win rate do dataset oscila entre ~48% e ~83% mês a mês (padrão de ondas de pipeline). Isso é esperado e visível em quase todos os reps. Não é um bug.

---

## COMPONENTE 3 — RECEITA POR PRODUTO AO LONGO DO TEMPO

### Tipo de gráfico
Barras empilhadas por mês, cada cor = um produto. Recharts `BarChart` com múltiplos `Bar` empilhados.

### Dados
```typescript
// Para cada mês, quebrar receita por produto
interface ProductMonthData {
  month: string
  GTXPro: number
  'GTX Plus Pro': number
  'MG Advanced': number
  'GTX Plus Basic': number
  'GTX Basic': number
  'GTK 500': number
  'MG Special': number
}
```

### Cores dos produtos (obrigatórias — mesmas do MVP existente)
```
GTXPro:         #3b82f6  (azul)
GTX Plus Pro:   #6366f1  (índigo)
MG Advanced:    #00e5a0  (verde)
GTX Plus Basic: #8b5cf6  (violeta)
GTX Basic:      #a78bfa  (lilás)
GTK 500:        #f59e0b  (âmbar — destaque pois é o mais caro)
MG Special:     #34d399  (verde claro)
```

### Interatividade
- Clicar em um produto na legenda filtra para mostrar apenas aquele produto
- Tooltip ao hover: produto | mês | receita | qtd de deals

### Insight automático abaixo do gráfico
```typescript
// Produto dominante do rep
const topProduct = Object.entries(productTotals)
  .sort((a, b) => b[1] - a[1])[0]
const topProductShare = (topProduct[1] / totalRevenue * 100).toFixed(0)

// Texto: "💡 GTXPro representa 67% da sua receita total. 
//         Diversificar para GTX Plus Pro pode reduzir concentração de risco."
```

---

## COMPONENTE 4 — CICLO DE FECHAMENTO POR FAIXA

### Tipo de gráfico
Gráfico de barras horizontais mostrando a distribuição dos ciclos de fechamento em 4 faixas. Recharts `BarChart` horizontal.

### Faixas e referência de dados (Darcel Schlecht como exemplo)
```
< 30 dias:   159 deals (45,6%) — "Fechamento rápido"
30–60 dias:   31 deals  (8,9%) — "Ciclo normal"
60–90 dias:   88 deals (25,2%) — "Ciclo longo"
> 90 dias:    71 deals (20,3%) — "Ciclo crítico"
```

### Configuração visual
```
Barra < 30d:   cor #00e5a0 (verde) — ideal
Barra 30-60d:  cor #3b82f6 (azul) — normal
Barra 60-90d:  cor #f59e0b (âmbar) — atenção
Barra > 90d:   cor #ef4444 (vermelho) — crítico

Cada barra mostra: valor absoluto (N deals) + percentual (%)
Label inline na barra com nome da faixa
```

### Como calcular
```typescript
// Usar apenas deals Won com ambas as datas preenchidas
const wonWithDates = wonDeals.filter(d => d.engage_date && d.close_date)
const cycles = wonWithDates.map(d => {
  const days = daysBetween(d.engage_date, d.close_date)
  return {
    ...d,
    cycle_days: days,
    bucket: days < 30 ? 'lt30' : days < 60 ? 'd30_60' : days < 90 ? 'd60_90' : 'gt90'
  }
})
```

### Insight automático
```typescript
const fastRate = (cycles.filter(c => c.bucket === 'lt30').length / cycles.length * 100).toFixed(0)
// "⚡ {fastRate}% dos seus deals fecham em menos de 30 dias. 
//    {gt90Count} deals levaram mais de 90 dias — revisar abordagem nesses casos."
```

---

## COMPONENTE 5 — RECEITA ACUMULADA (CURVA DE CRESCIMENTO)

### Tipo de gráfico
Área preenchida com linha de tendência. Recharts `AreaChart`.

### Dados
```typescript
interface CumulativeData {
  month: string
  monthRevenue: number    // receita do mês
  cumulative: number      // soma acumulada até este mês
}

// Exemplo (Darcel Schlecht):
// Mar: mensal=$112.255  acum=$112.255
// Abr: mensal=$92.830   acum=$205.085
// Mai: mensal=$95.118   acum=$300.203
// Jun: mensal=$122.127  acum=$422.330
// ...
// Dez: mensal=$119.216  acum=$1.153.214 (receita total do rep)
```

### Configuração visual
```
Área:         gradiente de #00e5a0 (100%) para #00e5a0 (0%) de cima para baixo
Linha:        #00e5a0 sólido, stroke 2px
Eixo X:       meses abreviados
Eixo Y:       valores em $K ou $M
Tooltip:      mês | receita do mês | acumulado

Adicionar linha de referência horizontal pontilhada no valor total do rep
com label: "Total: $1,15M"
```

---

## COMPONENTE 6 — TOP CONTAS FECHADAS

### Tipo
Tabela simples. Não é um gráfico.

### Dados
```typescript
// Top 10 contas por receita total won (do rep selecionado)
interface TopAccount {
  account: string         // nome da conta (ou "Conta não identificada")
  deals: number           // qtd de deals Won
  revenue: number         // soma dos close_value Won
  avgTicket: number       // revenue / deals
  lastClose: string       // close_date mais recente formatada
  sector: string          // de accounts.csv, ou "—" se não disponível
}
```

### Colunas da tabela
```
Conta          | Setor         | Deals | Receita    | Ticket Médio | Último Fechamento
Kan-code       | software      | 115   | $341.455   | $2.969       | Dez/17
Konex          | technology    | 108   | $269.245   | $2.493       | Dez/17
...
```

### Join com accounts.csv
```typescript
// Enriquecer com sector, mas account vazio é válido
const accountInfo = accounts[deal.account] || { sector: '—' }
// Nunca descartar deals com account vazio
```

### Ordenação
- Default: por receita DESC
- Permitir clicar no header para ordenar por outra coluna
- Mostrar top 10; link "Ver todas ({N}) →" abre modal com lista completa

---

## COMPONENTE 7 — MIX DE PRODUTOS (DONUT)

### Tipo de gráfico
Donut chart. Recharts `PieChart` com `innerRadius`.

### Dados
```typescript
// Receita por produto do rep (apenas deals Won)
const productMix = products.map(p => ({
  name: p.product,
  revenue: wonDeals
    .filter(d => d.product === p.product)
    .reduce((sum, d) => sum + safeFloat(d.close_value), 0),
  deals: wonDeals.filter(d => d.product === p.product).length
})).filter(p => p.revenue > 0)
  .sort((a, b) => b.revenue - a.revenue)
```

### Configuração visual
```
Centro do donut: receita total do rep formatada
Cores: mesmas do Componente 3 (consistência)
Legenda: produto | % da receita | valor absoluto
Tooltip: produto | N deals | receita | % do total
Tamanho: innerRadius=60, outerRadius=100
```

---

## FILTROS DA TELA

Dois filtros no topo da tela, abaixo do seletor de vendedor:

### Filtro 1 — Período
```
[Mar/17] [Abr/17] [Mai/17] [Jun/17] [Jul/17] [Ago/17] [Set/17] [Out/17] [Nov/17] [Dez/17] [Todos ●]
```
- Toggle: clicar em um mês filtra TODOS os gráficos para aquele mês
- "Todos" é o default (selecionado ao entrar)
- Quando um mês está selecionado, os KPIs mostram dados daquele mês

### Filtro 2 — Produto
```
Dropdown: [Todos os produtos ▼] | GTXPro | GTX Plus Pro | MG Advanced | GTX Plus Basic | GTX Basic | GTK 500 | MG Special
```
- Filtra todos os gráficos e a tabela de contas simultaneamente

---

## ESTADOS ESPECIAIS

### Vendedor sem deals Won
```
// Exibir no lugar de cada gráfico:
"Sem deals fechados no período"
// KPIs mostram zeros
// Tabela de contas vazia com mensagem
```

### Vendedor inativo (Mei-Mei Johns, Elizabeth Anderson, Natalya Ivanova, Carol Thompson, Carl Lin)
```
// Esses 5 reps têm 0 deals no dataset
// Mostrar estado vazio com:
"Nenhum deal registrado para este vendedor no período analisado."
```

### Filtro de período sem dados
```
// Se o mês selecionado não tem deals Won para o rep:
"Sem fechamentos em {mês}. Selecione outro período."
```

---

## NAVEGAÇÃO E INTEGRAÇÃO

### Nova aba no módulo `/rep`

Adicionar ao tab bar existente do dashboard do rep:

```typescript
// Tab bar atual (existente):
// [🔥 Atividades]

// Tab bar após esta atualização:
// [🔥 Atividades]  [📊 Resultados]
```

- "Atividades" aponta para `/rep` (home existente) — não alterar
- "Resultados" aponta para `/rep/results` (novo)
- Aba ativa com indicador visual (underline ou fundo)
- O seletor de vendedor é compartilhado entre as duas abas (mesma seleção)

### Compartilhamento de estado
```typescript
// O rep selecionado no store deve ser lido pela nova tela
// Não criar um novo seletor — reutilizar o já existente
const { selectedRep } = useStore()
```

---

## FUNÇÃO AUXILIAR — daysBetween (se não existir)

```typescript
function daysBetween(dateStrA: string, dateStrB: string): number {
  if (!dateStrA || !dateStrB) return 0
  const a = new Date(dateStrA)
  const b = new Date(dateStrB)
  return Math.round((b.getTime() - a.getTime()) / (1000 * 60 * 60 * 24))
}
```

---

## PERFORMANCE

Os CSVs têm 8.800 linhas. Todos os cálculos da tela de resultados devem ser **memoizados** por `selectedRep` para evitar recalcular ao trocar de aba.

```typescript
// Padrão: calcular uma vez quando o rep muda, guardar em cache
const repResults = useMemo(() => {
  if (!selectedRep) return null
  return computeRepResults(allDeals, selectedRep, products, accounts)
}, [selectedRep, allDeals])
```

---

## CHECKLIST DE VALIDAÇÃO ANTES DE ENTREGAR

### Dados
- [ ] `safeFloat()` usado em todo acesso a `close_value` (string vazia para deals abertos)
- [ ] `daysBetween()` verifica strings vazias antes de criar `Date`
- [ ] Deals com `account` vazio aparecem como "Conta não identificada", não são descartados
- [ ] Normalização GTXPro/GTX Pro aplicada no join com products.csv
- [ ] `REFERENCE_DATE = 2017-12-27` usada em qualquer cálculo relativo a "hoje"
- [ ] Vendedores inativos mostram estado vazio, não erro

### UI / UX
- [ ] Seletor de rep compartilhado com `/rep` home — mesma seleção persiste ao trocar aba
- [ ] Filtros de período e produto respondem simultaneamente em todos os componentes da tela
- [ ] Cores dos produtos consistentes com o MVP existente (mesma paleta)
- [ ] Todos os tooltips mostram: valor | unidade | contexto
- [ ] Insights automáticos presentes em pelo menos Componentes 2, 3 e 4
- [ ] Tela de resultados não quebra a navegação do `/rep` existente

### Rotas
- [ ] `/rep/results` funciona independentemente de `/rep`
- [ ] Voltar de `/rep/results` para `/rep` mantém o rep selecionado
- [ ] URL `/rep/results` é bookmarkable (sem depender de estado de navegação)

---

## ORDEM DE BUILD RECOMENDADA

```
1. Criar rota /rep/results e conectar ao tab bar existente
2. Implementar funções de computação dos dados do rep (memoizadas)
3. Componente 1: KPIs (mais simples — valida que os dados estão corretos)
4. Componente 2: Receita Mensal (gráfico mais importante)
5. Componente 5: Receita Acumulada (usa mesmos dados do 2)
6. Componente 7: Donut de mix de produtos
7. Componente 3: Timeline empilhada por produto
8. Componente 4: Ciclo de fechamento (distribuição)
9. Componente 6: Tabela de contas (requer join com accounts.csv)
10. Filtros de período e produto (conectar a todos os componentes)
11. Insights automáticos (texto gerado a partir dos dados calculados)
12. Estados vazios e edge cases
```

---

## RESUMO DO QUE ESTA ATUALIZAÇÃO ENTREGA

| Componente | O que mostra | Tipo |
|---|---|---|
| KPIs | Receita total, Win Rate, Ticket médio, Ciclo médio | Cards |
| Receita Mensal | Evolução mês a mês + Win Rate sobreposta | Barras + linha |
| Timeline por Produto | Quais produtos geraram receita em cada mês | Barras empilhadas |
| Ciclo de Fechamento | Quanto tempo os deals levam para fechar | Barras horizontais |
| Receita Acumulada | Curva de crescimento total do rep no período | Área |
| Top Contas | Quais contas geraram mais receita | Tabela |
| Mix de Produtos | Participação de cada produto na receita | Donut |

---

*Fim do prompt de atualização. Não alterar nenhuma rota ou componente existente. Apenas adicionar `/rep/results` e a nova aba de navegação.*
