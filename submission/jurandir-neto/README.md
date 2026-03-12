# Submissão — Jurandir Neto — Challenge data-001-churn

## Sobre mim

| Campo | |
|---|---|
| **Nome** | Jurandir Neto |
| **LinkedIn** | https://linkedin.com/in/jurandirneto |
| **Challenge escolhido** | data-001-churn — Diagnóstico de Churn (RavenStack) |

---

## Executive Summary

Construí um sistema completo de inteligência de churn para a RavenStack: um pipeline de dados em três camadas (Bronze → Silver → Gold), um dashboard interativo e um agente de IA conversacional capaz de responder perguntas estratégicas de negócio sobre churn. O principal achado é que o spike de $1,07M em MRR perdido em dezembro/2024 não foi um evento isolado — foi o colapso de uma degradação silenciosa de 4 meses, com causa raiz no suporte (não produto ou preço), concentrada em contas Enterprise adquiridas via canal Orgânico. A recomendação central é acionar o playbook de EBR Acelerado nas contas Company_188 e Company_227 esta semana e implementar coleta obrigatória de reason_code no fluxo de cancelamento — hoje, 4 de 5 indústrias têm UNKNOWN como motivo de churn, tornando qualquer diagnóstico futuro parcialmente cego.

---

## Solução

### Abordagem

O problema foi atacado em quatro fases sequenciais. A ordem importa: nenhuma linha de código foi escrita antes das fases 1 e 2 estarem concluídas.

**Fase 1 — Decomposição do problema antes de qualquer código**

Antes de abrir o editor, li o challenge inteiro e mapeei manualmente:
- As 3 perguntas diagnósticas centrais (causa raiz / segmentos em risco / ações)
- Os 5 datasets disponíveis e as relações entre eles (accounts → subscriptions → feature_usage; accounts → support_tickets; accounts → churn_events)
- O que precisaria existir em cada camada para responder cada pergunta

Esse mapeamento virou o esqueleto das specs que guiaram toda a implementação.

**Fase 2 — SDD: specs em 3 camadas antes do código**

Adotei Spec-Driven Development (SDD) — uma metodologia onde a especificação completa do sistema é escrita em 3 camadas antes de qualquer implementação:

| Camada | Diretório | O que especifica |
|--------|-----------|-----------------|
| Business | `docs/01-business/` | Definições de churn, KPIs, personas, jornada do cliente, playbook de CS |
| Product | `docs/02-product/` | Dados disponíveis, perguntas da análise, deliverables, playbook de CS detalhado |
| Engineering | `docs/03-engineering/` | Stack técnico, arquitetura medallion, modelo de dados (star schema), ADRs |

Por que SDD em vez de sair codificando? Porque IA (Claude Code incluído) é excelente para implementar o que está bem especificado — e péssima para decidir o que deve ser implementado. Sem specs, o Claude tende a gerar código funcionalmente correto mas estrategicamente errado: implementa o que parece óbvio, não o que o negócio precisa. As specs em `docs/` são o contrato que separou as decisões humanas das decisões técnicas delegáveis à IA.

Dois Architecture Decision Records documentam as decisões mais críticas:
- **ADR-001**: Por que Medallion + DuckDB + Parquet (não pandas + SQLite)
- **ADR-002**: Por que Agno (não LangChain/LlamaIndex/OpenAI direto)

**Fase 3 — Pipeline Medallion**

Com as specs em mãos, o pipeline foi implementado em 3 camadas:

```
data/raw/*.csv  →  Bronze (Parquet)  →  Silver (Star Schema)  →  Gold (Métricas prontas)
```

- **Bronze** (`pipeline/bronze/ingest.py`): ingestão direta, preserva schema original, sem transformação. Rastreabilidade total — sempre é possível reprocessar.
- **Silver** (`pipeline/silver/transform.py`): limpeza, tipagem, deduplicação, modelagem dimensional. O star schema (fct_subscription, fct_feature_usage, fct_support_ticket, fct_churn_event + dimensões) separa fatos de contexto e habilita joins eficientes.
- **Gold** (`pipeline/gold/aggregate.py`): métricas agregadas, cálculo de risk_score, tabelas otimizadas para consumo direto pelo dashboard e agente.

**Fase 4 — Agente + Dashboard**

O agente (Agno + Claude Sonnet) recebe perguntas em linguagem natural e responde com dados reais via 5 tools tipadas:

| Tool | O que faz |
|------|-----------|
| `query_risk_accounts` | Contas com risk_score acima de threshold |
| `query_churn_drivers` | Drivers de churn por segmento/período |
| `query_dashboard_fact` | Queries analíticas no gold layer |
| `lookup_cs_playbook` | Busca estratégia correspondente no playbook de CS |
| `detect_anomaly` | Compara métricas do período atual com média histórica |

O dashboard Streamlit consome diretamente as gold tables — sem joins em tempo de renderização.

---

### Resultados / Findings

O agente respondeu as 3 perguntas diagnósticas com os dados reais do pipeline. Abaixo os outputs literais.

---

#### P1 — O que está causando o churn?

> **Dezembro/2024 não é um pico de churn — é o colapso de uma degradação silenciosa que se acelerou por 4 meses consecutivos, concentrada em contas Enterprise adquiridas via canal Orgânico e correlacionada primariamente com falha de suporte, não com produto ou preço.**

**Evidência 1 — O spike de dez/24 é uma anomalia estatística severa**

| Período | MRR Perdido | Churns | CSAT |
|---------|-------------|--------|------|
| Jun/24  | $73,9K      | 41     | 3,97 |
| Jul/24  | $40,2K      | 38     | 4,07 |
| Ago/24  | $60,8K      | 36     | 4,40 |
| Set/24  | $177,7K     | 59     | 4,41 |
| Out/24  | $232,8K     | 115    | 3,90 |
| Nov/24  | $273,5K     | 136    | 3,67 |
| Dez/24  | **$1,075M** | **465**| 4,07 |

O detector de anomalias confirma: +651% acima da média histórica dos 6 meses anteriores. O sinal de alerta começou em setembro — a empresa teve 3 meses de aviso e não reagiu.

**Evidência 2 — A causa raiz está no suporte, não em produto ou preço**

- SUPPORT é o reason_code com maior MRR perdido por conta: $413K em apenas 168 churns (~$2.459/conta) vs. FEATURES com $384K em 192 churns.
- Clientes reclamando de "preço" (PRICING) têm avg_error_rate de 8,3% — o mais alto de todos os reason_codes. Preço é o pretexto; instabilidade técnica é o motivo.

**Evidência 3 — O vetor de destruição é Enterprise + Organic**

- Enterprise/Organic: $524K destruído, 108 churns.
- Canal Orgânico tem churn_rate de 23,6% — quase o dobro do canal PARTNER (13,5%).

**Evidência 4 — Features que separam quem fica de quem sai**

- `feature_31` tem retention lift de 1,73x — contas retidas usam 73% mais essa feature.
- `feature_26`, `feature_32`, `feature_19` têm retention_lift < 0,84 e taxa de erro 2-4x maior: bug de produto disfarçado de churn.

---

#### P2 — Quais segmentos estão mais em risco?

> **O trio EDTECH + UK + ENTERPRISE concentra o maior MRR em risco imediato ($13,5K+ em contas high-risk ativas), enquanto FINTECH e DEVTOOLS lideram o churn histórico acumulado com mais de $490K cada em MRR destruído.**

**Por Indústria**

| Indústria | Churn Rate | MRR Perdido | Reason Code |
|-----------|------------|-------------|-------------|
| FINTECH | 20,3% | $431K | UNKNOWN |
| EDTECH | 19,6% | $389K | UNKNOWN |
| DEVTOOLS | 19,5% | $491K | SUPPORT |
| CYBERSECURITY | 18,9% | $460K | UNKNOWN |
| HEALTHTECH | 17,0% | $393K | UNKNOWN |

4 de 5 indústrias com reason_code = UNKNOWN — lacuna crítica no processo de coleta.

**Por País**

- UK: 25,6% de churn — $312K perdidos (maior taxa isolada)
- FR: 17,6% com reason_code = SUPPORT (único país com sinal claro)
- US: volume absoluto dominante — 635 churns, $1,4M perdido

**Contas específicas em risco agora**

| Conta | Indústria | País | MRR | Sinais |
|-------|-----------|------|-----|--------|
| Company_188 | DEVTOOLS | FR | $1.568 | Erros altos + Downgrade (446 dias sem uso) |
| Company_227 | CYBERSECURITY | UK | $1.026 | Baixo uso + Downgrade (485 dias sem uso) |
| Company_30 | CYBERSECURITY | CA | $398 | Erros + Suporte ruim (ticket aberto) |
| Company_454 | FINTECH | US | $0 MRR | Baixo uso + Suporte ruim (já sem receita) |
| Company_482 | DEVTOOLS | US | $0 MRR | Baixo uso + Downgrade |

**Company_188 e Company_227** têm 2+ sinais simultâneos com MRR > $1K — classificação `alto_risco_combinado`.

---

### Recomendações

As 3 ações abaixo são derivadas diretamente dos dados e mapeadas para as categorias do playbook de CS em `docs/02-product/04-playbook-cs.md`.

**Ação 1 — EBR Acelerado: Company_188 e Company_227 esta semana**
- Playbook: Categoria 5 (Alto Risco Combinado) + Categoria 3 (Experiência Negativa de Suporte)
- Público-alvo: CS Manager Sênior assume pessoalmente — não delegar para CS júnior
- Pauta da reunião: "Vimos que sua experiência de suporte não foi a prometida — quero entender e resolver antes de continuar cobrando"
- Impacto potencial: $2.594/mês preservado (Company_188 + Company_227)
- Escala do impacto estrutural: se Enterprise/Organic reduzir churn_rate de 17% para 13,5% (média do canal PARTNER), $150-200K/mês preservado nos próximos 6 meses

**Ação 2 — Resolver o UNKNOWN em reason_code**
- Problema: 4 de 5 indústrias sem causa identificada de churn — diagnóstico parcialmente cego
- Ação: implementar coleta obrigatória de motivo no fluxo de cancelamento (campo required, não optional)
- Playbook: Categoria 6 (Entrevista de Saída)
- Impacto: sem isso, qualquer diagnóstico futuro permanece comprometido — não é melhoria opcional, é prerequisito de inteligência

**Ação 3 — Monitorar feature_31 no onboarding revisado**
- `feature_31` tem retention lift 1,73x — contas que a adotam retêm 73% mais
- `feature_26` e `feature_32` têm taxa de erro 2-4x acima da média — priorizar no roadmap de estabilidade
- Ação: incluir `feature_31` no checklist de ativação do onboarding; monitorar error_count diário em `feature_26`/`feature_32` com alerta automático (threshold: +50% acima da média)

---

### Limitações

| Limitação | Impacto |
|-----------|---------|
| ~30% de `reason_code = UNKNOWN` nos churn_events | Diagnóstico de causa raiz parcialmente cego — correlações são indicativas, não causais |
| Dados até dez/2024 | Sem visibilidade do que aconteceu depois do spike — não sabemos se a tendência reverteu |
| Sem dados de CRM/Intercom | Impossível correlacionar qualidade das conversas de vendas/CS com churn — o CSAT de ticket é proxy, não medida direta |
| risk_score heurístico (4 sinais × 0,25) | Pesos iguais não foram validados estatisticamente — um modelo de regressão logística com dados históricos refinaria significativamente o score |
| Sem dados de cohort pós-onboarding | Não é possível distinguir churn por problema de fit (cliente errado) de churn por problema de entrega (produto falhou) |

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| **Claude Code** | Design da arquitetura (ADRs), escrita das specs SDD (docs/), implementação do pipeline medallion, construção do agente Agno, dashboard Streamlit, Dockerfile/docker-compose, README |
| **Agente construído** (Agno + Claude Sonnet via API) | Responder as 3 perguntas diagnósticas com os dados reais após o pipeline rodar |

Nenhuma outra ferramenta de IA foi usada. A razão é metodológica: queria que todo o contexto do projeto residisse em um único ambiente (o repositório + CLAUDE.md), não fragmentado entre ChatGPT, Cursor e Claude.

---

### Workflow

**Passo 1 — Decomposição manual do problema (sem IA)**

Antes de qualquer prompt, li o challenge inteiro e fiz no papel:
- Mapeamento dos 5 datasets e suas relações
- Rascunho das 3 perguntas diagnósticas que o sistema precisaria responder
- Identificação do que precisaria existir em cada camada (bronze/silver/gold) para cada pergunta ser respondível

Esse trabalho prévio é o que separou esta submissão de "peça para o Claude analisar o CSV". Sem esse mapeamento, o Claude teria implementado algo funcionalmente correto mas estrategicamente superficial.

**Passo 2 — CLAUDE.md como memória persistente do agente**

Antes de escrever qualquer spec ou código, criei o `CLAUDE.md` — um documento que o Claude Code lê no início de cada sessão. Ele contém:
- Visão geral do projeto e stack
- Schema exato dos 5 CSVs
- Regras de código (DuckDB, Streamlit, Agno)
- As 3 perguntas diagnósticas obrigatórias
- Restrições operacionais (nunca modificar raw/, nunca hardcodar credenciais)

O CLAUDE.md não é documentação — é o contexto que permite ao Claude Code trabalhar de forma coerente entre sessões. Sem ele, cada sessão começa do zero.

**Passo 3 — Specs SDD antes de qualquer código**

Com o CLAUDE.md em vigor, trabalhei com o Claude Code para escrever as specs em `docs/`:
- `docs/01-business/`: visão estratégica, personas, KPIs, jornada do cliente
- `docs/02-product/`: dados disponíveis, perguntas da análise, deliverables, playbook de CS
- `docs/03-engineering/`: stack técnico, arquitetura medallion, modelo de dados (star schema completo), ADR-001 e ADR-002

O star schema do Silver foi especificado antes de qualquer transformação: `fct_subscription`, `fct_feature_usage`, `fct_support_ticket`, `fct_churn_event` + `dim_account`, `dim_plan`, `dim_feature`, `dim_date`. A razão: o modelo dimensional no Silver é o que habilita queries eficientes no Gold sem joins explosivos — e essa decisão precisa ser tomada antes de implementar qualquer transformação.

**Passo 4 — Implementação do pipeline com Claude Code**

Com as specs prontas, o Claude Code implementou:
1. `pipeline/bronze/ingest.py` — leitura dos CSVs, escrita em Parquet, sem transformação
2. `pipeline/silver/transform.py` — limpeza, tipagem, modelagem dimensional em SQL via DuckDB
3. `pipeline/gold/aggregate.py` — métricas agregadas, cálculo do risk_score por 4 sinais binários, tabelas gold_dashboard_fact, gold_account_risk, gold_churn_drivers, gold_feature_retention, gold_support_health

**Passo 5 — Agente Agno + 5 tools**

O agente foi construído com Agno porque permite definir tools tipadas em Python que o modelo invoca de forma controlada — com integração nativa com a Anthropic API. LangChain foi descartado (complexidade excessiva para o caso de uso), LlamaIndex foi descartado (voltado para RAG sobre documentos, não análise de dados), OpenAI diretamente foi descartado (sem suporte nativo para o padrão de tools tipadas que queria).

As 5 tools do agente foram definidas iterativamente — `detect_anomaly` foi adicionada depois da rodada inicial mostrar que o agente precisava de um comparativo histórico para contextualizar o spike de dez/24.

**Passo 6 — Execução do pipeline e diagnóstico**

Com o pipeline rodando e o agente construído, rodei `/diagnose` para as 3 perguntas. Os outputs literais estão na seção Resultados.

---

### Onde a IA errou e como corrigi

**Erro 1 — SQL no Silver sem preservação de tipos DATE**

Na primeira versão do `transform.py`, o Claude gerou SQL que tratava datas como VARCHAR no Silver. O problema só apareceu no Gold quando queries com filtros de período quebravam silenciosamente (retornavam resultados errados sem erro). Correção manual: adicionei casts explícitos (`CAST(... AS DATE)`) em todos os campos de data no Silver, mais um teste de sanidade que verifica os tipos dos Parquets após cada camada.

**Erro 2 — Agente recomendava ações sem consultar o playbook**

Na versão inicial do agente, ele respondia perguntas de "o que fazer" baseando-se apenas no raciocínio do modelo — sem chamar `lookup_cs_playbook`. O resultado eram recomendações genéricas que poderiam ser sobre qualquer SaaS. Correção: instrução explícita no system prompt — *"ALWAYS call lookup_cs_playbook before making any retention recommendation"* — e reestruturação do fluxo da tool para que `query_risk_accounts` retorne a categoria de problema junto com o account_id, tornando natural a sequência `query` → `lookup_cs_playbook` → resposta.

**Erro 3 — Gold sem detecção de anomalias**

O pipeline gold inicial calculava métricas corretas mas sem baseline histórico — impossível saber se um valor era normal ou excepcional. A tool `detect_anomaly` não estava no plano original. Foi adicionada depois de rodar o diagnóstico inicial e perceber que o agente não conseguia contextualizar o spike de dez/24 sem comparar com a média histórica. A ferramenta calcula média e desvio padrão dos últimos N meses e sinaliza desvios acima de 2σ.

---

### O que eu adicionei que a IA sozinha não faria

**1. A decisão de usar SDD como metodologia**

O Claude Code é otimizado para implementar. Sem direcionamento explícito, ele tende a começar pelo código. A decisão de escrever specs em 3 camadas (business/product/engineering) antes de qualquer linha de pipeline foi minha — e foi o que garantiu que o sistema final respondesse as perguntas certas com o modelo de dados certo.

**2. A escolha do Agno sobre LangChain/LlamaIndex/OpenAI**

O Claude não escolheria espontaneamente o Agno — é um framework menos conhecido. A escolha foi baseada em três critérios que eu defini: (1) tools tipadas em Python sem boilerplate excessivo, (2) integração nativa com Anthropic API, (3) suporte a memória de sessão para o contexto do dashboard. O ADR-002 em `docs/03-engineering/` documenta essa decisão formalmente.

**3. A estrutura do CLAUDE.md como memória persistente**

Organizar o repositório com um `CLAUDE.md` detalhado — incluindo schema dos CSVs, regras de código, as 3 perguntas diagnósticas e restrições operacionais — foi um design deliberado para potencializar o Claude Code entre sessões. O Claude não teria criado esse contexto por iniciativa própria; eu projetei o repositório para maximizar a coerência da ferramenta.

**4. A definição dos 4 sinais binários do risk_score**

O risk_score em `gold_account_risk` é calculado como soma de 4 sinais (`signal_low_usage`, `signal_high_errors`, `signal_bad_support`, `signal_downgrade`), cada um com peso 0,25. Os limiares de cada sinal — qual percentual da média do segmento define "baixo uso", qual multiplicador define "erros altos" — foram calibrados por mim com base na lógica do playbook de CS, não gerados automaticamente.

**5. A constraint de governança: sem recomendação sem playbook**

A regra de que o agente nunca pode recomendar uma ação de retenção sem antes chamar `lookup_cs_playbook` é uma constraint de governança — não técnica. Garante que as recomendações sejam consistentes com a estratégia documentada de CS, não com o que o LLM acha razoável em geral. O Claude não adicionaria essa constraint por conta própria.

---

### Evidências

- **Git history**: todos os artefatos do projeto estão commitados no repositório com histórico de desenvolvimento
- **CLAUDE.md**: documento de contexto persistente que demonstra a metodologia de organização do repositório
- **`docs/`**: specs completas escritas antes do código — consultar timestamps dos commits para verificar a ordem
- **ADR-001 e ADR-002**: decisões arquiteturais documentadas formalmente em `docs/03-engineering/`
- **Pipeline executável**: `python pipeline/bronze/ingest.py && python pipeline/silver/transform.py && python pipeline/gold/aggregate.py` roda o pipeline completo; outputs dos agente nas seções de Resultados acima são os outputs reais após execução

---

Submissão enviada em: 11/03/2026
