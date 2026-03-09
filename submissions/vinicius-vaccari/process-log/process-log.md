# Process Log — Challenge 003: Lead Scorer

**Autor:** Vinicius Vaccari
**Ferramentas:** ChatGPT o4 thinking · Gemini 3.1 Pro (High) · Claude Code (claude-sonnet-4-6)
**Duração estimada:** 4–5 horas

---

## Ferramentas utilizadas

| Ferramenta | Modelo | Propósito |
|---|---|---|
| ChatGPT | o4 thinking | Análise inicial do desafio; planejamento da solução; criação do design system da aplicação |
| Gemini | 3.1 Pro (High) | Leitura do repositório do challenge; plano de implementação; design system da UI |
| Claude Code | claude-sonnet-4-6 | Análise crítica do scoring, identificação de bugs, correções no app.js, auditoria dos dados com Python, geração de documentação |
| Python (via Claude Code) | — | Análise exploratória dos CSVs — distribuições, win rates, aging, validação de campos |
| PapaParse (CDN) | 5.4.1 | Parsing de CSV no browser |
| HTML + CSS + JS | — | Stack da solução (sem framework) |

---

## Workflow passo a passo

### Etapa 1 — Leitura e compreensão da aplicação

O Claude Code leu todos os arquivos da aplicação:
- `README.md` — entendeu a lógica de scoring documentada
- `app.js` — leu todas as 948 linhas do motor de scoring
- `index.html` — mapeou a estrutura da interface
- `data/*.csv` — verificou headers e primeiras linhas

Leu também o repositório do challenge para entender critérios de avaliação.

**Contribuição humana:** direcionamento inicial — pedir que entendesse o desafio e acessasse o repositório antes de qualquer análise.

---

### Etapa 2 — Análise crítica do scoring

Com base na leitura do código, o Claude identificou 4 problemas no motor de scoring:

**Problema 1 — Account Fit: fórmula inconsistente**
O setor usava multiplicação (`score = 50 * sectorFactor`) enquanto receita e porte usavam adição (`score += delta * 100`). Escalas diferentes faziam o setor ter peso implícito muito maior que os outros dois fatores.

**Problema 2 — Dupla-contagem Product Performance + Expected Value**
`perf.winRate` e `perf.avgCloseValue` apareciam no Fator 2 (15%) e novamente no Fator 7 (10%), via `estimatedWR = perf.winRate * 0.6 + agentWR * 0.4`. Peso efetivo de product performance era ~19%, não 15%.

**Problema 3 — Stage Aging: benchmark incorreto**
`stageAges.Engaging` e `stageAges.Prospecting` eram populados com os **mesmos dados** (ciclo total de deals Won). O benchmark de Prospecting era apenas o de Engaging × 1.3 — sem fundamento nos dados reais.

**Problema 4 — Agent Win Rate: centro de gravidade errado**
Fórmula `ratio * 60` colocava o ponto neutro em 60 (vendedor médio = 60/100), inflando levemente vendedores abaixo da média.

**Contribuição humana:** confirmação de que a análise fazia sentido antes de prosseguir com os fixes.

---

### Etapa 3 — Correções aplicadas (rodada 1)

O Claude aplicou 5 edits simultâneos ao `app.js`:

1. **Account Fit** → `compositeWR = sectorWR * 0.5 + revWR * 0.3 + empWR * 0.2`, normalizado por `avgWinRate * 50`
2. **Expected Value** → removeu `perf.winRate` da fórmula; passou a usar apenas `agentWR × avgCloseValue`
3. **Stage Aging benchmark** → calculou `medianTotal` dos ciclos de Won deals; setou `Prospecting = medianTotal`, `Engaging = medianTotal * 0.60`
4. **Agent Win Rate** → mudou de `ratio * 60` para `50 + (ratio - 1) * 60` (simétrico em torno de 50)
5. **refExpectedValue** → adicionou `avgDealValue * avgWinRate * 2` como âncora de normalização do Fator 7

---

### Etapa 4 — Auditoria de dados com Python

Após as correções, o Claude rodou análises Python nos CSVs para verificar se o scoring fazia sentido com os dados reais.

**Descobertas relevantes:**

| Descoberta | Impacto |
|---|---|
| Win rates por produto: 60–65% (range de 4,8pp) | Fator de win rate do produto quase não discrimina; ticket é o diferenciador real |
| Win rates por setor: 61–65% (range de 3,6pp) | Account Fit via win rate também pouco discriminante neste dataset |
| 1.425 deals ativos sem conta (68,2% dos ativos) | Nenhum deal Won/Lost tem conta faltando — problema de qualidade de dados do CRM |
| Mediana ciclo Won: 57 dias | Ponto de referência para Stage Aging |
| Mediana idade Engaging ativo: 165 dias | Todos os deals ativos estão muito além do ciclo típico de Won |

---

### Etapa 5 — Bug crítico identificado e corrigido (rodada 2)

> **Este é o exemplo mais importante de correção humana sobre erro da IA.**

A correção do Stage Aging na Etapa 3 introduziu um **novo bug**:

- Benchmark Engaging = `medianTotal * 0.60` = 57 × 0.60 = **34 dias**
- Os deals Engaging ativos têm idades entre **9 e 423 dias** (p25 = 148 dias)
- Com benchmark de 34 dias: qualquer deal com mais de 61 dias (34 × 1.8) recebia score 15
- **Resultado: 93% de todos os deals Engaging ativos recebiam o mesmo score 15** — nenhuma diferenciação

O raciocínio original da IA estava errado: "Engaging já usou 40% do ciclo, portanto deve fechar nos 60% restantes" ignora que deals que chegam a Engaging são mais complexos e têm ciclos mais longos, não mais curtos.

**Correção aplicada:**

```javascript
// ERRADO (introduzido pela IA na rodada 1)
Engaging: medianTotal * 0.60   // 34 dias — benchmark irrealisticamente curto

// CORRETO (corrigido após auditoria de dados)
Engaging: medianTotal * 1.5    // 86 dias — deals engajados têm ciclos mais longos
```

Além disso, foi adicionado um novo bucket de scoring para criar discriminação na faixa onde os deals ativos se concentram:

```javascript
// Antes: apenas 5 buckets, todos ativos caíam no último (score 15)
} else {
  score = 15;  // ratio > 1.8 → todos recebiam isso

// Depois: 6 buckets com granularidade na faixa crítica
} else if (ratio <= 3.0) {
  score = 25;  // significativamente atrasado — 42% dos deals ativos
} else {
  score = 10;  // crítico — 27% dos deals ativos
}
```

**Resultado após correção:**

| Score | Deals Engaging ativos | % |
|---|---|---|
| 90/70/65 (saudável) | 144 | 9% |
| 45 (envelhecendo) | 349 | 22% |
| 25 (atrasado) | 667 | 42% |
| 10 (crítico) | 429 | 27% |

**Contribuição humana crítica:** a IA não teria detectado este bug sem o passo de auditoria de dados que mostrou a distribuição real de idades dos deals ativos. A decisão de rodar a análise exploratória em Python foi fundamental para pegar o erro.

---

### Etapa 6 — Verificação final cruzada

Cross-check completo entre código e dados:

| Verificação | Resultado |
|---|---|
| Campos no app.js vs headers reais dos CSVs | Todos batem ✅ |
| `normalizeProduct("GTXPro" → "GTX Pro")` | "GTXPro" existe no pipeline, "GTX Pro" no products.csv ✅ |
| Deals sem conta: Won/Lost afetados? | 0 — apenas deals ativos têm conta faltando ✅ |
| `refExpectedValue` matemática | avgDealValue=$2.361, avgWinRate=63.2%, ref=$2.985 → deal médio = score 50 ✅ |
| Stage Aging Prospecting | 500/500 deals sem engage_date → default 90 dias → ratio=1.58 → score 45 (aging) ✅ |

---

## Erros da IA e correções

| # | Erro da IA | Como foi detectado | Correção |
|---|---|---|---|
| 1 | Stage Aging: benchmark Engaging = `medianTotal * 0.60` criou benchmark de 34 dias, colapsando 93% dos deals para score 15 | Auditoria Python: distribuição de idades dos deals ativos mostrou que p25 = 148 dias >> 34 dias | Benchmark Engaging = `medianTotal * 1.5` (86 dias) + novo bucket de scoring |
| 2 | Raciocínio incorreto: "Engaging deve fechar em 60% do ciclo porque já percorreu 40%" — ignora que deals mais qualificados têm ciclos mais longos | Análise dos dados reais e lógica de negócio revisada | Inverted: Engaging = 1.5× benchmark, não 0.6× |

---

## Contribuições humanas (além do output da IA)

1. **Direcionamento estratégico** — decidir qual análise fazer, em que ordem, e quando parar
2. **Validação dos fixes** — aprovar cada correção antes de aplicar ao código
3. **Decisão de rodar auditoria de dados** — pedir análise Python nos CSVs após as correções foi o passo que revelou o bug crítico no Stage Aging
4. **Julgamento sobre o benchmark Engaging** — a IA apresentou dois raciocínios contraditórios; a escolha do correto (1.5×) foi validada com base nos dados reais
5. **Coleta de evidências** — screenshots da aplicação rodando, prints desta sessão

---

## Evidências

### Conversas exportadas (ChatGPT)

1. **Análise do desafio proposto** — leitura do repositório, entendimento do challenge, planejamento inicial
   - [Conversa completa no ChatGPT](https://chatgpt.com/share/69af0456-a198-8007-aff7-5dcaa454c2f2)

2. **Criação do design system** — definição da interface, componentes e layout da aplicação
   - [Conversa completa no ChatGPT](https://chatgpt.com/share/69af05dd-e200-8007-a736-5ddc38713e9e)

### Screenshots das sessões de desenvolvimento

Screenshots das conversas com Claude Code e Gemini 3.1 Pro (High) estão na pasta [`process-log/screenshots/`](./screenshots/):

**Gemini 3.1 Pro (High):**
- [x] Leitura do repositório e análise inicial (`screenshots/01-gemini-repo.jpeg`)
- [x] Revisão do plano com mudanças propostas (`screenshots/02-gemini-plano_mudança.jpeg`)
- [x] Criação do design system da aplicação (`screenshots/03-gemini-design_system.jpeg`)

**Claude Code:**
- [x] Análise do que faz sentido ou não no scoring (`screenshots/01-claude-oque_faz_sentido_ou_não.jpeg`)
- [x] Identificação dos problemas no lead scoring (`screenshots/02-claude-problemas_lead.jpeg`)
- [x] Auditoria completa do lead scoring (`screenshots/03-claude-auditoria_lead_scoring.jpeg`)
- [x] Verificação se a lógica fazia sentido após correções (`screenshots/04-claude-se_a_logica_fazia_sentido.jpeg`)

### Vídeo da aplicação rodando

- [x] Screen recording da aplicação funcional — navegação pelo dashboard, filtros, modal de deal, export
  - [Vídeo no YouTube](https://www.youtube.com/watch?v=uKWrbkqsDhw)
 