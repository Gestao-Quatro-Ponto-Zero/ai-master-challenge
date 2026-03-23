# Submissão — Lucas Caldeira Liberato Souza — Challenge 001

## Sobre mim

| Campo | Informação |
|-------|------------|
| **Nome** | Lucas Caldeira Liberato Souza |
| **LinkedIn** | [linkedin.com/in/lucascliberato](https://linkedin.com/in/lucascliberato) |
| **Challenge escolhido** | 001 — Diagnóstico de Churn (RavenStack) |

---

## Executive Summary

Analisei 5 datasets da RavenStack (500 accounts, 5K subscriptions, 25K feature events, 2K tickets, 600 churns) cruzando todas as tabelas para identificar a causa raiz do churn de 22%. **Descobri que o problema não é produto, pricing ou suporte isoladamente — é a combinação de canal de aquisição (Event/Ads) com falha no onboarding.** DevTools adquiridos via Partner têm 12.5% de churn; via Event, 43.5%. Mesma indústria, 3.5x mais churn. A principal recomendação é intervir imediatamente nas 81 contas de alto risco identificadas ($121K MRR) e redirecionar a aquisição de DevTools para Partners, com potencial de preservar ~$1.45M ARR.

---

## Solução

A solução completa está na pasta `solution/` e inclui:

1. **[diagnostico_churn_ravenstack.md](solution/diagnostico_churn_ravenstack.md)** — Relatório completo respondendo as 3 perguntas do briefing
2. **[contas_alto_risco.csv](solution/contas_alto_risco.csv)** — Lista de 81 contas para ação imediata de CS
3. **[analise_exploratoria.py](solution/analise_exploratoria.py)** — Código Python reproduzível com toda a análise

**Documentação adicional** em `docs/`:

4. **[modelo_preditivo_churn.md](docs/modelo_preditivo_churn.md)** — Modelo de ML para prever churn (com análise honesta de limitações)
5. **[predicoes_churn_ml.csv](docs/predicoes_churn_ml.csv)** — Probabilidades de churn para os 390 accounts ativos

### Principais Findings

| Métrica | Valor |
|---------|-------|
| Churn rate geral | 22% (110 de 500 accounts) |
| MRR perdido | $254,952/mês |
| Segmento mais crítico | DevTools via Event/Ads (40.8% churn) |
| Contas em alto risco | 81 ativas ($120,939 MRR) |
| Impacto potencial das ações | ~$1.45M ARR |

---

## Abordagem

### 1. Inventário e mapeamento (30 min)
Comecei extraindo os dados e mapeando a estrutura de cada tabela. Identifiquei as chaves de relacionamento (account_id, subscription_id) e os campos relevantes para churn.

### 2. Análise por categoria (1h)
Calculei churn rate por cada dimensão isoladamente: indústria, canal, plano, billing frequency, país, trial status. DevTools (31%) e Event (30%) se destacaram como outliers.

### 3. Cruzamento entre tabelas (1h30)
Criei um dataset master juntando as 5 tabelas. O insight crítico veio aqui: DevTools via Partner tem 12.5% churn vs 43.5% via Event — mesma adoção de features (~25%), churn 3.5x maior. Isso mostrou que o problema não é o cliente, é o canal.

### 4. Geração e validação de hipóteses (1h)
Gerei 5 hipóteses e testei cada uma contra os dados:
- DevTools = problema de produto → **REFUTADA** (Partner funciona)
- Event = expectativa inflada → **PARCIALMENTE VALIDADA**
- Upgrade = problema → **REFUTADA** (upgrade reduz churn)
- Features = driver principal → **VALIDADA** (<20% core = 33% churn)

### 5. Priorização e recomendações (30 min)
Calculei impacto estimado de cada ação e priorizei por esforço vs retorno.

---

## Resultados / Findings

### 1. Causa Raiz do Churn

**Não é um fator isolado — é a combinação de fatores:**

| Combinação | Churn Rate |
|------------|------------|
| DevTools + Event/Ads | 40.8% |
| DevTools + Event/Ads + Low Core | 46.7% |
| DevTools + Partner | 12.5% |

**A mecânica:** Canais sem qualificação (Event/Ads) trazem clientes que não recebem onboarding adequado → não descobrem as features certas → não percebem valor → churnam citando "support" ou "features".

### 2. Segmentos em Risco

**81 contas ativas com alto risco | $120,939 MRR**

| Perfil | Contas | MRR |
|--------|--------|-----|
| DevTools | 47 | $74,892 |
| Via Event/Ads | 62 | $78,545 |
| Com escalações | 31 | $45,221 |

Top 5 contas para ação imediata:

| Account | MRR | Score | Motivos |
|---------|-----|-------|---------|
| A-51ec1b | $3,383 | 10 | DevTools + ads + low_core + escalation |
| A-ad64c6 | $5,572 | 8 | DevTools + event + low_core |
| A-9bfc9f | $2,940 | 11 | DevTools + ads + low_core + escalation + csat |
| A-ad296b | $1,862 | 9 | DevTools + event + escalation + csat |
| A-cb5333 | $1,617 | 7 | DevTools + ads + csat |

### 3. Core Features (que retêm clientes)

Zero overlap entre top 10 features de churned vs ativos:

**Ativos usam:** feature_32, feature_12, feature_6, feature_2, feature_31...  
**Churned usam:** feature_15, feature_1, feature_4, feature_20, feature_11...

Correlação forte:
- <20% core features → 33% churn
- >40% core features → 9% churn

---

## Recomendações

### Priorização por Impacto x Esforço

| # | Ação | ARR Impacto | Esforço | Prazo |
|---|------|-------------|---------|-------|
| 1 | **Intervenção nas 81 contas** | $290K | Baixo | 2 semanas |
| 2 | **GTM DevTools → Partner** | $259K | Médio | 30 dias |
| 3 | **Onboarding core features** | $775K | Médio | 45 dias |
| 4 | SLA Enterprise | $127K | Alto | 60 dias |
| | **TOTAL** | **$1.45M** | | |

### Detalhamento

**Ação 1 — Intervenção imediata (AGORA)**
- CS contactar as 81 contas em 2 semanas
- Top 20 (maior risco + MRR): contato em 48h
- Script: health check proativo, NÃO pitch de upsell

**Ação 2 — Mudar GTM DevTools (30 dias)**
- Pausar campanhas de Ads segmentadas para DevTools
- Não priorizar DevTools em eventos
- Criar programa de Partners específico para DevTools

**Ação 3 — Onboarding core features (45 dias)**
- Identificar as 5 core features no onboarding
- Alerta para CS quando account tem <20% core adoption após 30 dias
- Email sequence educativo (dias 7, 14, 30)

---

## Limitações

1. **Dados sintéticos** — Não pude validar hipóteses com stakeholders reais ou contexto de negócio
2. **Causalidade vs correlação** — As relações identificadas são correlacionais; um experimento A/B seria necessário para confirmar causalidade
3. **Temporalidade** — Não investiguei a fundo o pico de churn em Q3-Q4 2024 (+562%); pode haver fatores externos
4. **Impactos estimados** — Os valores de ARR preservado são estimativas baseadas em premissas conservadoras
5. **Features genéricas** — Os dados usam "feature_N" sem descrição; em um caso real, mapearia para features reais do produto
6. **Modelo ML limitado** — Construí um modelo preditivo (ver `docs/`), mas tem performance modesta (CV AUC ~56%) devido aos dados sintéticos. O risk score manual baseado em regras é mais útil neste caso.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|---------------|
| **Claude (Anthropic)** | Análise exploratória, cruzamento de dados, geração de hipóteses, validação estatística, formatação de outputs |
| **Python/Pandas** | Execução do código de análise (via Claude) |

### Workflow

1. **Extração e inventário** — Pedi para Claude extrair o zip e mapear a estrutura dos dados
2. **Análise por categoria** — Solicitei cálculo de churn rate por cada dimensão (indústria, canal, plano, etc.)
3. **Cruzamento de tabelas** — Instruí a criação de um dataset master juntando as 5 tabelas
4. **Geração de hipóteses** — Pedi hipóteses baseadas nos padrões encontrados
5. **Validação** — Questionei se cada hipótese poderia ser validada pelos dados (não por opinião)
6. **Priorização** — Solicitei cálculo de impacto x esforço para cada ação

### Onde a IA errou e como corrigi

1. **Hipótese de features como driver principal** — Claude inicialmente sugeriu que adoção de core features era o principal driver de churn. Quando questionei para validar nos dados, descobrimos que DevTools via Event e DevTools via Partner têm a **mesma** adoção de features (~25%), mas churn completamente diferente (43% vs 12%). Isso mostrou que features sozinhas não explicam — o canal é o fator crítico. **Correção:** Refinei a hipótese para "combinação de canal + falha no onboarding".

2. **Conflito de colunas no merge** — Houve erro técnico ao fazer merge de tabelas (churn_flag_x vs churn_flag_y). Claude identificou e corrigiu renomeando colunas antes do merge.

3. **Hipótese de upgrade como problema** — Claude inicialmente indicou que 20.5% dos churns aconteciam pós-upgrade, sugerindo que upgrade era problemático. Ao validar, descobrimos que quem faz upgrade tem **menos** churn (20.8% vs 23.8%). **Correção:** Invertemos a conclusão.

### O que eu adicionei que a IA sozinha não faria

1. **Questionamento sistemático** — Insisti em validar TODAS as hipóteses pelos dados, não aceitar correlações superficiais. Claude teria parado na primeira análise plausível; eu forcei o cruzamento completo das 5 tabelas.

2. **Foco em acionabilidade** — Direcionei para recomendações concretas com impacto estimado, não apenas insights genéricos.

3. **Priorização por esforço** — A matriz de priorização (impacto x esforço) foi minha contribuição para tornar as recomendações implementáveis.

4. **Estrutura de submissão** — A organização do deliverable no formato solicitado.

### Evidências

- **Chat export:** Disponível em `process-log/chat-exports/` (transcript completo da sessão)
- **Código Python:** Disponível em `solution/analise_exploratoria.py` (reproduzível)

---

**Submissão enviada em:** Março 2026
