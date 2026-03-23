# PRD — Lead Scorer
**Challenge 003 — G4 AI Master**
**Autor:** Vinicius (Residence Imobiliária)
**Versão:** 3.0 — consolidada em sessão colaborativa

---

## 1. Contexto e Objetivo

### O que é o produto
Um dashboard de priorização de pipeline comercial chamado **Lead Scorer**. A ferramenta permite que vendedores saibam exatamente onde focar sua energia a cada dia — quais deals atacar hoje e quais tentar reativar — com base em dados reais do CRM, não no feeling de cada um.

### Para quem
Três perfis com visões distintas na mesma interface:
- **Vendedor** — vê seu próprio pipeline, scores e prioridades
- **Manager** — vê ranking dos seus vendedores, posição global e por região
- **Diretor** — vê visão global, por região, managers e pipeline completo

Troca de perfil via seletor no canto superior direito — popover com subgrupos:
- **Diretor** — perfil único, sem nome
- **Managers** — seleção por nome (6 managers)
- **Vendedores** — seleção por nome (35 vendedores)

### O problema que resolve
2.089 deals ativos, priorização feita no feeling. Deals bons esfriando por falta de atenção, tempo gasto em deals sem chance real.

### O que entrega
- Score de 0 a 100 por deal com explicação em linguagem natural
- Dois grupos operacionais: **Prospect** e **Engaging**
- Sinalização de risco por ciclo histórico de fechamento
- Visões diferenciadas por nível de usuário

---

## 2. Dados e Fontes

**Dataset:** CRM Sales Predictive Analytics (Kaggle, CC0)
**Período:** outubro/2016 a dezembro/2017
**Data de referência:** 31/dez/2017 (última data do dataset — usada como "hoje")

### accounts.csv — 85 contas
| Campo | Uso |
|---|---|
| `account` | Chave de ligação |
| `sector` | 10 setores — usado no score de Prospect |
| `revenue` | Receita anual (milhões USD) — usado no score |
| `employees` | Não usado no score |
| `office_location` | Contexto informativo |
| `subsidiary_of` | 70/85 vazios — não usado |

### products.csv — 7 produtos
| Produto | Série | Preço |
|---|---|---|
| MG Special | MG | $55 |
| GTX Basic | GTX | $550 |
| GTX Plus Basic | GTX | $1.096 |
| MG Advanced | MG | $3.393 |
| GTX Pro | GTX | $4.821 |
| GTX Plus Pro | GTX | $5.482 |
| GTK 500 | GTK | $26.768 |

> **Atenção técnica:** "GTXPro" = "GTX Pro" com typo. Normalizar para "GTX Pro" antes de qualquer cálculo.

### sales_teams.csv — 35 vendedores
| Campo | Uso |
|---|---|
| `sales_agent` | Chave de ligação |
| `manager` | Hierarquia |
| `regional_office` | East / West / Central |

**Estrutura:**
| Região | Manager | Vendedores |
|---|---|---|
| Central | Dustin Brinkmann | Anna Snelling, Cecily Lampkin, Versie Hillebrand, Lajuana Vencill, Moses Frase |
| Central | Melvin Marxen | Jonathan Berthelot, Marty Freudenburg, Gladys Colclough, Niesha Huffines, Darcel Schlecht, Mei-Mei Johns |
| East | Cara Losch | Violet Mclelland, Corliss Cosme, Rosie Papadopoulos, Garret Kinder, Wilburn Farren, Elizabeth Anderson |
| East | Rocco Neubert | Daniell Hammack, Cassey Cress, Donn Cantrell, Reed Clapper, Boris Faz, Natalya Ivanova |
| West | Celia Rouche | Vicki Laflamme, Rosalina Dieter, Hayden Neloms, Markita Hansen, Elease Gluck, Carol Thompson |
| West | Summer Sewald | James Ascencio, Kary Hendrixson, Kami Bicknell, Zane Levy, Maureen Marcano, Carl Lin |

### sales_pipeline.csv — 8.800 oportunidades
| Campo | Nulos | Uso |
|---|---|---|
| `opportunity_id` | 0 | Identificador único |
| `sales_agent` | 0 | Liga com sales_teams |
| `product` | 0 | Liga com products |
| `account` | 1.425 | 16% sem conta — fallback aplicado |
| `deal_stage` | 0 | Prospecting / Engaging / Won / Lost |
| `engage_date` | 500 | Só os 500 Prospecting sem data |
| `close_date` | 2.089 | Ativos não têm |
| `close_value` | 2.089 | Só Won tem valor |

**Distribuição:** Won 4.238 (48%) / Lost 2.473 (28%) / Engaging 1.589 (18%) / Prospecting 500 (6%)

---

## 3. Lógica de Scoring

### Pré-processamento obrigatório
- Normalizar "GTXPro" → "GTX Pro"
- Data de referência: 31/dez/2017
- Todos os fatores normalizados no range real do dataset

---

### Dois grupos baseados no stage

**Prospect** — 500 deals em Prospecting
- Nunca avançaram para negociação / Sem `engage_date` — tempo não se aplica
- Score responde: *"Qual abordar primeiro?"*

**Engaging** — 1.589 deals em Engaging
- Em negociação ativa / Têm `engage_date` — tempo se aplica
- Score responde: *"Onde focar a energia?"*
- Deals além do P75 → badge de alerta + botão "Reengajar" — não altera o score

---

### P75 por produto — base para zonas de risco e cálculo de tempo

| Produto | P75 | Zona âmbar (−20%) | Máx. histórico |
|---|---|---|---|
| GTX Pro | 84d | 67d | 138d |
| GTX Plus Pro | 85d | 68d | 138d |
| MG Advanced | 87d | 70d | 138d |
| MG Special | 88d | 70d | 138d |
| GTX Plus Basic | 90d | 72d | 138d |
| GTX Basic | 91d | 73d | 138d |
| GTK 500 | 107d | 86d | 138d |

**Zonas de risco visual:**
- **Verde:** dentro do P75
- **Âmbar:** últimos 20% antes do P75 (P75×0.8 até P75)
- **Vermelho:** além do P75 até 138 dias
- **Vermelho crítico:** além de 138 dias (máximo histórico absoluto de Won)

> **Nota GTK 500:** P75 calculado com apenas 15 deals históricos — amostra pequena. Limitação documentada.

---

### Score bruto — Engaging

| Fator | Peso | Como calcula |
|---|---|---|
| Win rate da conta | 40% | Normalizado 53%–75%. Sem histórico suficiente = 45. **Sem conta = 35** |
| Tempo no pipeline | 35% | ratio dias/P75: ≤0.25=100, ≤0.50=88, ≤0.75=72, ≤1.0=52, ≤1.5=25, ≤2.0=10, >2.0=3 |
| Preço do produto | 15% | Normalizado $55–$26.768 |
| Receita da conta | 10% | Normalizado $5M–$11.698M. **Sem conta = 35** |
| Bônus agente | ±pts | WR agente ≥65%=+8, ≥60%=+4, <57%=−4 |

**Sem conta = 35:** incerteza, não punição severa. Deals sem conta ficam no meio-baixo da lista, não no fundo absoluto. Fundamento: todos os 6.711 deals históricos fechados têm conta preenchida.

---

### Score bruto — Prospect

| Fator | Peso | Como calcula |
|---|---|---|
| Win rate da conta | 50% | Normalizado 53%–75%. Sem histórico = 45. **Sem conta = 35** |
| Receita da conta | 30% | Normalizado $5M–$11.698M. **Sem conta = 35** |
| Setor da conta | 20% | Marketing/Entertainment=100, Software=90, Tech/Services/Retail/Employment=80, Telecom/Medical=60, Finance=0. Sem setor=50 |
| Bônus agente | ±pts | Mesmo critério do Engaging |

**Win rate histórico por setor:** Marketing 65% / Entertainment 65% / Software 64% / Technology 63% / Services 63% / Retail 63% / Employment 63% / Telecom 62% / Medical 62% / Finance 61%

---

### Score exibido — normalização relativa por conjunto do usuário

O score bruto determina a **ordenação** dos deals. O score **exibido** é uma normalização min-max dentro do conjunto visível para o usuário atual:

```
score_exibido = (bruto - min_bruto) / (max_bruto - min_bruto) × 95 + 2
```

- O melhor deal do conjunto fica entre 95–98
- O pior fica entre 2–5
- Os demais distribuídos proporcionalmente

**Por que:** o dataset não possui deals perfeitos — o máximo bruto alcançado é ~75. Sem normalização relativa, o vendedor nunca vê scores acima de 75, perdendo a referência visual de urgência. Com normalização, a escala é relativa ao pipeline do usuário — sempre comunicando prioridade real dentro do contexto.

**Ordenação:** sempre por score bruto — nunca pelo score exibido.

**Diretor:** usa score bruto diretamente — não normalização relativa — para permitir comparação entre regiões.

---

### Dois scores no lead_details

**Score relativo** (principal, em destaque):
- Score normalizado dentro do pipeline do usuário
- Subtítulo: *"Sua prioridade relativa no pipeline"*
- Acompanha explicação completa dos fatores

**Score global do lead** (secundário, menor):
- Posição do lead em relação a todos os deals ativos da empresa
- Subtítulo: *"Posição global na carteira da empresa"*
- Texto fixo: *"Este score compara este lead com todos os deals ativos da empresa. Prospectar mais contas qualificadas melhora sua posição global."*
- Sem explicação de fatores — só contexto

---

### Explicação do score — templates JavaScript internos

Função JS que recebe os fatores calculados e monta explicação em português. Zero dependência externa, instantânea, funciona offline.

**Mapeamento completo:**

| Condição | Frase gerada |
|---|---|
| Win rate alto (norm > 70) | *"[Conta] tem histórico forte — fecha [X]% dos deals. Entre os melhores do seu pipeline."* |
| Win rate médio (40–70) | *"[Conta] tem histórico consistente de compra. Deal bem posicionado no seu pipeline."* |
| Sem conta identificada | *"Conta não identificada — score estimado com dados limitados. Vincular a conta pode melhorar a prioridade."* |
| Tempo fresco (ratio ≤ 0.5) | *"Deal recente no pipeline — janela de fechamento aberta. Um dos mais prioritários agora."* |
| Zona âmbar (ratio 0.75–1.0) | *"Deal se aproximando do limite histórico para este produto. Atenção recomendada."* |
| Além do P75 | *"Deal fora do ciclo histórico ([X]d vs P75 [Y]d). [Fator positivo] justifica tentativa de reativação."* |
| Além de 138 dias | *"Deal além do ciclo máximo histórico de fechamento. Avalie se ainda há interesse ativo da conta."* |
| Preço alto (GTK/GTX Pro) | *"Produto de alto valor — merece atenção prioritária pelo impacto na meta."* |
| Posição relativa (top 10%) | *"Entre os 10% com maior prioridade do seu pipeline."* |
| Posição relativa (top 25%) | *"Um dos deals mais fortes neste momento."* |

**Regra:** nunca sugerir probabilidade absoluta de fechamento. Sempre linguagem de prioridade relativa.

---

### Score de desempenho — Vendedores (para o Manager)

| Fator | Peso | Range real |
|---|---|---|
| Win rate histórico | 40% | 55%–70% |
| Valor gerado (Won) | 40% | $0–$1.153.214 |
| Pipeline ativo | 20% | 0–194 deals |

Normalizado no range do time do manager. Vendedores sem Won = score zero, no final do ranking.

**Explicação sempre exibida:**
> *"Fecha [X]% dos deals — [acima/abaixo] da média do time ([Y]%). Gerou $[Z] em deals fechados — [posição]º no time. Tem [N] deals ativos."*

---

### Ranking de Managers (para o Diretor)

Ranking simples por **valor total gerado (Won)** — sem score composto.
O range de win rate entre managers é apenas 2,3pp (62,1%–64,4%) — variação insuficiente para score confiável.

| Posição | Manager | Valor Won | WR% |
|---|---|---|---|
| 1 | Melvin Marxen | $2.251.930 | 62,2% |
| 2 | Summer Sewald | $1.964.750 | 64,3% |
| 3 | Rocco Neubert | $1.960.545 | 62,1% |
| 4 | Celia Rouche | $1.603.897 | 63,4% |
| 5 | Cara Losch | $1.130.049 | 64,4% |
| 6 | Dustin Brinkmann | $1.094.363 | 63,0% |

---

## 4. Interface e Layout

### Tecnologia
- React + HTML/JS — **single file**
- Ícones: **Lucide** — sem emojis funcionais
- Sem build, sem npm — abre direto no navegador
- **Fonte:** DM Sans

### Assistente AI — tecnologia
- **OpenAI API** — somente no assistente flutuante
- Campo de input na interface para inserção da chave API pelo usuário
- **Limitação documentada:** *"O assistente AI requer chave OpenAI própria. A explicação do score e todas as demais funcionalidades operam sem chave."*
- Explicação do score: templates JS internos — sempre funciona, sem chave

---

### Sistema de cores — light mode

| Camada | Valor |
|---|---|
| Background global | `#F7F8FA` — off-white frio |
| Sidebar | `#F0F2F5` — 2% mais escuro |
| Cards | `#FFFFFF` com borda `#E8EBF0` |
| Acento principal | `#4F46E5` — indigo-600 |
| Hover | `#4338CA` — indigo-700 |
| Body text | `#374151` |
| Subtexto | `#6B7280` |
| Semânticas | Verde / Âmbar / Vermelho / Indigo — equalizados OKLCH |

**Cards de grupo:**
- **Prospect:** fundo `#1e293b`, elementos brancos
- **Engaging:** fundo `#4F46E5`, elementos brancos

---

### Shell persistente

**Topbar fixa:**
- Logo à esquerda
- Abas de leads abertas crescem esquerda → direita (até 10, esteira)
- Seletor de usuário **fixo no canto superior direito**
- Cada aba: nome do lead + badge de grupo. "X" no hover

**Sidebar retrátil** (ícone + label / só ícone colapsada):

*Vendedor:*
- Dashboard / Prospect / Engaging / — / Configurações / Ajuda

*Manager:*
- Dashboard / Meu Time / Pipeline do Time / — / Configurações / Ajuda

*Diretor:*
- Dashboard Global / Regiões / Managers / Deals (sub: Prospect · Engaging) / — / Configurações / Ajuda

**Sidebar — item Produtos** (todos os níveis):
Badge "Em breve", desabilitado, tooltip: *"Funcionalidade em desenvolvimento"*

---

### Dashboard — Vendedor

**Linha 1 — 4 colunas:**
- **Prospect** (col 1, fundo `#1e293b`): número, score médio, valor potencial, top 5 por score bruto
- **Engaging** (col 2, fundo `#4F46E5`): número, score médio, valor potencial, top 5, badge de quantos em alerta
- **Em alerta** (col 3, borda âmbar): deals em zona âmbar/vermelho, por score bruto
- **Urgências** (col 4, menor): deals cruzando P75 nos próximos 7 dias

**Linha 2 — 2 KPIs compactos:**
- Win Rate + sparkline
- Deals Won no período + sparkline

Cada card clicável → aba correspondente. Cada item → lead_details.

---

### Dashboard — Manager

**Seção 1 — Ranking do time (principal):**
Tabela com todos os vendedores do manager:
Nome / Score de desempenho / WR% / Valor gerado / Deals ativos.
Cada linha clicável → pipeline do vendedor. Explicação do score sempre visível.

**Seção 2 — Posição global:**
Card com posição do manager no ranking global por valor gerado.

**Seção 3 — Alertas:**
Vendedores com pipeline parado / abaixo da média do time em WR.

> Manager **nunca vê deals de outros managers**. Vê apenas sua posição no ranking — não os deals dos concorrentes.

---

### Dashboard — Diretor

**Tela: Dashboard Global**
Cards por região (East / West / Central): deals ativos, WR médio, valor potencial, valor gerado.
Ranking de managers por valor gerado.

**Tela: Regiões**
Drill-down por região: KPIs, managers da região, top vendedores.

**Tela: Managers**
Tabela com os 6 managers: valor gerado, WR%, deals ativos.
Clicável → visão do time com score de cada vendedor.

**Tela: Deals**
Sub-menu: Prospect / Engaging.
Tabela densa com filtro por região/manager/vendedor — não kanban.
Score exibido = score bruto real (não normalização relativa — permite comparação entre regiões).

---

### Lead Details — página de detalhe

**Header:** nome do deal em destaque, badge de grupo, zona de risco, vendedor, produto — sempre visíveis. Breadcrumb. Menu `···`.

**Painel principal (esquerda ~65%):**

*Score relativo:*
Anel circular (donut, fill horário) + número.
Subtítulo: *"Sua prioridade relativa no pipeline"*
Explicação por template JS — 1–3 linhas, clara, acionável.

*Score global:*
Número menor, abaixo.
Subtítulo: *"Posição global na carteira da empresa"*
Texto fixo explicativo.

*Detalhes do deal:*
Grid 3 colunas: Produto / Stage (badge) / Dias no pipeline (colorido por zona)
Valor potencial / Série / Vendedor

*Ciclo do deal:*
Donut chart fill horário — dias decorridos vs P75.
Data início / P75 do produto / delta / zona de risco.
Botão "Reengajar" se além do P75.

**Painel lateral (direita ~35%):**

*Card conta (maior, com destaque no topo):*
Nome e setor em área de destaque. Receita / Localização / Win rate + barra / Histórico Won/Lost.

*Card produto:*
Preço / Win rate do produto / Ciclo médio Won / Deals ativos.

---

### Abas Prospect e Engaging

Cards de deal com altura generosa:
- **Nome** em destaque máximo
- **Score** como donut + número
- Conta, produto, dias, valor potencial, badge de zona
- Botão "Reengajar" se além do P75

Filtros: produto / série / conta / score / tempo
Ordenação: Score (padrão) / Tempo / Valor / Conta

---

### Assistente AI — botão flutuante

Botão fixo canto inferior direito (ícone `sparkles` Lucide).
Ao abrir: painel ~400px. Campo para chave OpenAI. Saudação dinâmica. Chips por nível. Chat com contexto do pipeline do usuário.

**Chips:**
*Vendedor:* "O que tenho de urgente hoje?" / "Qual deal não posso perder?" / "Algum deal fora do ciclo?" / "Onde estou perdendo mais?"
*Manager:* "Qual vendedor precisa de atenção?" / "Quem está abaixo da média?" / "Maior valor em risco?" / "Resumo do pipeline"
*Diretor:* "Qual região tem pipeline mais parado?" / "Qual manager está abaixo?" / "Onde estão os GTK 500?" / "Resumo executivo"

Prioriza Engaging com maior score. Sem duplicação. Chips contextuais após primeira resposta.

---

### Regras globais de interação

- Toasts canto inferior direito, auto-dismiss 3–5s
- Tabelas: busca + filtro + ordenação
- Ações em menu `···` por linha
- Estado vazio projetado para todas as listas
- Animações discretas: fade-in stagger, grow em gráficos
- UI 100% em português
- Todo elemento clicável: cursor pointer + hover state
- Usuário padrão ao abrir: Anna Snelling (Vendedora)

---

### Bugs conhecidos

- **Carl Lin e Carol Thompson** — não carregam. Bug de string matching no código
- **Ícones Lucide** — garantir ícones adequados para Prospect e Engaging na sidebar

---

## 5. Visões por Perfil

| | Score relativo | Score global | Leads | Ranking time | Ranking global | Pipeline global |
|---|---|---|---|---|---|---|
| Vendedor | Sim (seu pipeline) | Sim (lead_details) | Seus | Não | Não | Não |
| Manager | Sim (time) | Sim (lead_details) | Seu time | Sim (seus vendedores) | Sim (sua posição) | Não |
| Diretor | Score bruto | Score bruto | Todos (por região) | Sim (global) | Sim (global) | Sim |

---

## 6. Documentação e Limitações

### Setup
```bash
# Clonar repositório
git clone [repo]

# Abrir no navegador — sem servidor, sem build
open index.html

# Assistente AI (opcional)
# Inserir chave OpenAI no campo dentro do assistente
# Todas as demais funcionalidades operam sem chave
```

### Limitações conhecidas

**Dados:**
- 1.425 deals sem conta (68% dos ativos) — fallback aplicado, precisão reduzida
- Dataset estático 2016–2017 — data de referência fixa
- GTK 500: P75 com apenas 15 deals históricos — amostra pequena
- Win rate entre managers: range de 2,3pp — insuficiente para score composto confiável

**Produto:**
- Autenticação simulada via seletor
- Dados de CSVs estáticos — sem tempo real
- Sem persistência entre sessões
- **Assistente AI requer chave OpenAI própria** — inserida pelo usuário na interface

**Funcionalidades futuras:**
- Cross-sell por novo produto — sem dados de sequência de compra
- Integração CRM real via API
- Autenticação real

---

## 7. Process Log

**Fase 1 — Análise do problema**
Leitura do README. Decisões-chave antes de qualquer código.

**Fase 2 — Análise dos dados**
Python nos 4 CSVs. Descobertas: distribuição bimodal do ciclo, typo GTXPro, 1.425 deals sem conta, win rate 53%–75%, ausência de correlação receita×win rate, ausência de correlação preço×win rate, range de win rate entre managers insuficiente para score.

**Fase 3 — Decisões de scoring**
Iterações: Prospect/Engaging pelo stage, P75 como zona de risco (não fronteira), score bruto com 4 fatores + bônus agente, normalização relativa min-max por conjunto do usuário, dois scores no lead_details, score de desempenho de vendedores, ranking de managers por valor gerado.

**Fase 4 — Decisões de produto**
Três níveis com visões radicalmente diferentes, templates JS para explicação, OpenAI só no assistente com chave opcional, botão flutuante.

**Fase 5 — Decisões de UI/UX**
Light mode, DM Sans, `#4F46E5` como acento, donut de score, cards com zonas de risco coloridas, anti-vibe-code aplicado.

**Fase 6 — Construção**
Claude Code no Antigravity com este PRD como contexto.

---

## 8. Prompt de Execução — Claude Code / Antigravity

*"O projeto Lead Scorer já está construído no Antigravity. Aplique todas as mudanças abaixo — não reconstrua do zero. Execute na ordem de prioridade.*

---

**PRIORIDADE 1 — SCORE: refatorar completamente**

ENGAGING — score bruto:
- Win rate da conta: 40% — normalizado 53%–75%. Sem histórico=45. Sem conta=35
- Tempo: 35% — ratio dias/P75: ≤0.25=100, ≤0.50=88, ≤0.75=72, ≤1.0=52, ≤1.5=25, ≤2.0=10, >2.0=3
- Preço do produto: 15% — normalizado $55–$26.768
- Receita da conta: 10% — normalizado $5M–$11.698M. Sem conta=35
- Bônus agente: WR≥65%=+8, ≥60%=+4, <57%=−4

PROSPECT — score bruto:
- Win rate da conta: 50% — normalizado 53%–75%. Sem conta=35
- Receita: 30% — normalizado $5M–$11.698M. Sem conta=35
- Setor: 20% — Marketing/Entertainment=100, Software=90, Tech/Services/Retail/Employment=80, Telecom/Medical=60, Finance=0. Sem setor=50
- Bônus agente: mesmo critério

P75 por produto: GTX Pro=84d, GTX Plus Pro=85d, MG Advanced=87d, MG Special=88d, GTX Plus Basic=90d, GTX Basic=91d, GTK 500=107d

SCORE EXIBIDO — normalização relativa:
Após calcular score bruto de todos os deals do conjunto visível:
score_exibido = (bruto - min_bruto) / (max_bruto - min_bruto) × 95 + 2
Ordenação sempre por score bruto. Score exibido só para apresentação visual.
Diretor usa score bruto diretamente — sem normalização relativa.

DOIS SCORES no lead_details:
1. Score relativo: score_exibido do conjunto do usuário. Subtítulo: "Sua prioridade relativa no pipeline". Com explicação de fatores.
2. Score global: score_exibido calculado sobre todos os deals da empresa. Subtítulo: "Posição global na carteira da empresa". Texto: "Este score compara este lead com todos os deals ativos da empresa. Prospectar mais contas qualificadas melhora sua posição global."

GTXPro → normalizar para GTX Pro antes de qualquer cálculo.

---

**PRIORIDADE 2 — ZONAS DE RISCO**

Verde: dentro do P75. Âmbar: P75×0.8 até P75. Vermelho: além do P75 até 138d. Vermelho crítico: além de 138d.
Deals em âmbar/vermelho: badge colorido + texto "Fora do ciclo histórico (P75: Xd)" + botão "Reengajar" no card e no lead_details.

---

**PRIORIDADE 3 — EXPLICAÇÃO DO SCORE (templates JS)**

Mapear todos os fatores:
- WR alto (norm>70): "[Conta] tem histórico forte — fecha [X]% dos deals. Entre os melhores do seu pipeline."
- WR médio (40–70): "[Conta] tem histórico consistente. Deal bem posicionado."
- Sem conta: "Conta não identificada — score estimado com dados limitados."
- Tempo fresco (ratio≤0.5): "Deal recente — janela aberta. Um dos mais prioritários agora."
- Zona âmbar: "Deal se aproximando do limite histórico. Atenção recomendada."
- Além do P75: "Deal fora do ciclo histórico ([X]d vs P75 [Y]d). [Fator positivo] justifica reativação."
- Além de 138d: "Deal além do ciclo máximo histórico. Avalie se há interesse ativo."
- Preço alto: "Produto de alto valor — merece atenção pelo impacto na meta."
- Top 10%: "Entre os 10% com maior prioridade do seu pipeline."
- Top 25%: "Um dos deals mais fortes neste momento."
Nunca sugerir probabilidade absoluta.

---

**PRIORIDADE 4 — VISÃO DO MANAGER**

Sidebar: Dashboard / Meu Time / Pipeline do Time / — / Configurações / Ajuda

Dashboard Manager:
1. Ranking vendedores: tabela Nome / Score (WR40%+Valor40%+Ativos20%, normalizado no time) / WR% / Valor gerado / Deals ativos. Sem Won=zero, no final. Explicação por linha.
2. Posição global: card com posição no ranking por valor gerado.
3. Alertas: pipeline parado, WR abaixo da média.
Manager nunca vê deals de outros managers.

---

**PRIORIDADE 5 — VISÃO DO DIRETOR**

Sidebar: Dashboard Global / Regiões / Managers / Deals (sub: Prospect · Engaging) / — / Configurações / Ajuda

Dashboard Global: cards por região + ranking managers por valor gerado.
Tela Managers: tabela 6 managers, clicável → time com score de cada vendedor.
Tela Deals: tabela densa, sub-menu Prospect/Engaging, filtro por região. Score bruto (sem normalização relativa).

---

**PRIORIDADE 6 — ASSISTENTE AI**

Botão flutuante canto inferior direito. Campo para chave OpenAI. Contexto do pipeline do usuário. Chips por nível. Resposta única.

---

**PRIORIDADE 7 — BUGS E AJUSTES**

Carl Lin e Carol Thompson: corrigir string matching.
Topbar: seletor fixo à direita, abas crescem esquerda → direita.
Interface 100% em português.
Usuário padrão: Anna Snelling (Vendedora).
Todos os elementos clicáveis: cursor pointer + hover state.

Execute na ordem. Confirme remoção do scoring anterior antes de implementar o novo."*
