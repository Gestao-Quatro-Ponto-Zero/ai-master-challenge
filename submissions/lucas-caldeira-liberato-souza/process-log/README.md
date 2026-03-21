# Process Log — Uso de IA no Challenge

## Ferramentas Utilizadas

| Ferramenta | Para que usei |
|------------|---------------|
| **Claude (Anthropic)** | Análise exploratória, cruzamento de dados, geração de hipóteses, validação estatística, formatação de outputs |
| **Python/Pandas** | Execução do código de análise (via Claude) |

---

## Workflow Detalhado

### Etapa 1: Extração e Inventário (30 min)

**Prompt:** "Extraia o arquivo e faça um inventário completo dos dados"

**O que a IA fez:**
- Extraiu archive.zip via bash
- Identificou 5 arquivos CSV
- Mapeou colunas de cada tabela
- Identificou chaves de relacionamento

**Output:**
```
ravenstack_accounts.csv      → 500 registros
ravenstack_subscriptions.csv → 5,000 registros
ravenstack_feature_usage.csv → 25,000 registros
ravenstack_support_tickets.csv → 2,000 registros
ravenstack_churn_events.csv  → 600 registros
```

---

### Etapa 2: Análise por Categoria (1h)

**Prompts:**
- "Calcule churn rate por indústria"
- "Analise churn por canal de aquisição"
- "Compare churn por plano"
- "Mostre evolução temporal do churn"

**O que a IA fez:**
- Calculou métricas de churn por cada dimensão
- Identificou DevTools (31%) e Event (30%) como outliers
- Mostrou aumento de +562% no churn entre 2023 e 2024

---

### Etapa 3: Cruzamento de Tabelas (1h30)

**Prompt:** "Cruze as 5 tabelas para encontrar padrões"

**O que a IA fez:**
- Criou dataset master juntando todas as tabelas
- Calculou métricas agregadas por account
- Identificou "core features" (top 10 de ativos)

**Insight crítico encontrado:**
```
DevTools + Partner: 25.0% core adoption | 12.5% churn
DevTools + Event:   25.0% core adoption | 43.5% churn
```

---

### Etapa 4: Geração de Hipóteses (30 min)

**Prompt:** "Baseado nos dados, quais hipóteses explicam o churn?"

**Hipóteses geradas:**
1. DevTools não tem product-market fit
2. Canal Event traz clientes com expectativa inflada
3. Upgrades falham por expectativa não entregue
4. Adoção de features é o driver principal

---

### Etapa 5: Validação de Hipóteses (1h)

**Prompt:** "Use os dados para validar ou refutar cada hipótese"

**Resultados:**

| Hipótese | Resultado | Evidência |
|----------|-----------|-----------|
| DevTools = problema de produto | REFUTADA | Partner funciona (12.5%) |
| Event = expectativa inflada | PARCIAL | CSAT pior, mas tickets iguais |
| Upgrade = problema | REFUTADA | Upgrade reduz churn |
| Features = driver | VALIDADA | <20% core = 33% churn |

---

### Etapa 6: Recomendações (30 min)

**Prompt:** "Calcule impacto estimado de cada ação"

**Output:**
- Intervenção 81 contas: $290K ARR
- GTM DevTools → Partner: $259K ARR
- Onboarding core features: $775K ARR
- SLA Enterprise: $127K ARR

---

## Onde a IA Errou e Como Corrigi

### Erro 1: Hipótese de Features

**O que aconteceu:** Claude sugeriu que adoção de core features era o principal driver.

**Minha correção:** Questionei se os dados validavam isso. Ao cruzar, descobrimos que DevTools via Event e via Partner têm a MESMA adoção (~25%), mas churn 3.5x diferente.

**Conclusão corrigida:** Não é features sozinho — é a combinação canal + onboarding.

### Erro 2: Conflito de Colunas

**O que aconteceu:** Erro técnico ao fazer merge (churn_flag_x vs churn_flag_y).

**Minha correção:** Pedi para renomear colunas antes do merge.

### Erro 3: Hipótese de Upgrade

**O que aconteceu:** Claude indicou que 20.5% dos churns eram pós-upgrade, sugerindo que upgrade era problema.

**Minha correção:** Pedi para validar se quem faz upgrade churna mais. Descobrimos que NÃO — upgrade reduz churn (20.8% vs 23.8%).

---

## O Que Eu Adicionei

1. **Questionamento sistemático** — Insisti em validar TODAS as hipóteses pelos dados
2. **Foco em acionabilidade** — Direcionei para recomendações concretas
3. **Priorização** — A matriz impacto x esforço foi minha contribuição
4. **Estrutura de entrega** — Organização no formato do template

---

## Evidências

- **Código Python:** Disponível em `solution/analise_exploratoria.py` (reproduzível)
- **Screenshots:** Podem ser adicionados em `screenshots/` se necessário

---

## Tempo Total

- Análise com IA: ~4 horas
- Formatação e revisão: ~30 min
- Total: ~4h30
