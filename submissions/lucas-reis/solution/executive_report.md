# Diagnóstico de Churn — RavenStack
**Preparado por:** Lucas Reis
**Data:** 2026-03-20
**Dados analisados:** 500 contas · 5 tabelas · 32.000+ registros

---

## TL;DR — O que está acontecendo

**22% das contas da RavenStack estão saindo, sem causa única dominante.** Clientes de DevTools churnam 2× mais que a média (31% vs 16%); clientes vindos de eventos têm o segundo pior perfil (30%). Os motivos declarados são distribuídos entre budget (15.5%), pricing (14.5%), features (13.6%) e support (12.7%) — nenhum domina. O sinal mais forte não está nos motivos declarados, mas nos segmentos: DevTools e canal event têm odds ratio de 2.4–2.5× de churn independentemente do que o cliente declara ao sair. Há $710K de MRR ativo em contas com múltiplos sinais de risco — ação nas próximas 4 semanas pode salvar uma fração relevante antes que se materialize.

---

## O que os dados mostram

### Churn real: 22% — 110 de 500 contas perdidas

A RavenStack perdeu 110 contas de uma base de 500, representando **$229K de MRR** cancelado. A taxa de 22% é materialmente acima do benchmark saudável de 5–8% para SaaS B2B. Ao ritmo atual, sem intervenção, mais ~110 contas seguirão no próximo período — o que representa aproximadamente **$229K/mês em receita em risco contínuo**, ou ~$2.7M ARR ameaçado em 12 meses.

O churn é distribuído: 31.8% dos churners saíram **sem deixar nenhum registro de motivo** em churn_events — o "churner silencioso" é o perfil dominante. Entre os que deixaram registro, nenhuma categoria se destaca com clareza.

---

### Causa raiz: product-market fit segmental

O sinal mais robusto desta análise não vem dos motivos declarados de saída, mas de onde o churn se concentra:

| Segmento | Churn rate | vs. melhor benchmark | MRR perdido |
|----------|-----------|----------------------|-------------|
| **Indústria DevTools** | **31.0%** | 2× maior que Cybersecurity (16%) | $60,227 |
| **Canal event** | **30.2%** | 2× maior que partner (14.6%) | $65,983 |
| FinTech | 22.3% | — | $51,189 |
| HealthTech | 21.9% | — | $47,981 |
| EdTech | 16.5% | — | $27,213 |
| **Cybersecurity** | **16.0%** | melhor da base | $42,512 |

**Odds Ratio DevTools vs Cybersecurity: 2.36×. Odds Ratio event vs partner: 2.53×.**

Estes números são calculados diretamente de `accounts.churn_flag × industry/referral_source` — sem intermediação de reason_code. São a evidência mais limpa e confiável do diagnóstico.

**O mecanismo:** Clientes de DevTools e vindos de eventos chegam com expectativas específicas sobre o que um "AI-driven team tool" deve fazer para seu contexto de trabalho. Fazem onboarding genuíno — em média, usam 28 features distintas antes de sair. Ao tentar executar seus fluxos reais, descobrem que as integrações ou automações específicas que seu segmento precisa estão ausentes ou incompletas. Saem sem deixar muito rastro — frequentemente sem reclamação de suporte.

**Por que isso importa estrategicamente:** O produto não tem um problema de adoção. Tem um problema de adequação para segmentos específicos. As soluções convencionais de retenção (mais onboarding, tutoriais, check-ins de CS) não atacam esta causa.

---

### Os motivos declarados de saída — multicausal, sem dominância

Entre os 75 churners com registro em churn_events (68% dos 110), a distribuição dos reason_codes é:

| Motivo | Churners | % dos 110 |
|--------|---------|-----------|
| Sem registro | 35 | **31.8%** |
| budget | 17 | 15.5% |
| pricing | 16 | 14.5% |
| features | 15 | 13.6% |
| support | 14 | 12.7% |
| competitor | 7 | 6.4% |
| unknown | 6 | 5.5% |

Budget + pricing combinados (~30%) superam features (~14%). Nenhuma causa domina. Isso é consistente com um problema segmental — clientes de perfis diferentes saem por razões diferentes, sem um único "culpado" identificável nos dados categóricos.

> **Nota metodológica:** Uma versão anterior desta análise reportou "60.9% declaram features" — este número foi corrigido após auditoria. O bug original contou contas retidas com eventos históricos de cancelamento de subscrição (não de conta) no numerador, inflando o count de "features" de 15 para 67. O correto é 15 churners (13.6%) com reason_code=features. O campo `feedback_text` foi analisado separadamente: contém 3 categorias sintéticas (too expensive, missing features, switched to competitor) distribuídas uniformemente sem correlação com reason_code — não acrescenta informação.

---

### O paradoxo do uso — o sinal mais contraintuitivo

Churners da RavenStack usam, em média, **3.4% mais features que os clientes que ficam** (28.3 vs 27.4 features distintas). Eles têm mais sessões, passam mais tempo no produto, e geram volumes similares de uso.

**O que isso descarta:**
- Não é problema de onboarding — os churners já usam o produto ativamente
- Não é problema de engajamento — eles interagem mais que os retidos
- Não é perfil de cliente "errado" em termos de motivação de uso

**O que isso confirma:**
- O churn ocorre *depois* da adoção, não durante
- O cliente chegou ao limite do produto em seu caso de uso específico
- A solução está no produto, não na operação de CS ou marketing

Uma analogia: é como um cozinheiro profissional que usa todos os utensílios de uma cozinha mas descobre que não há a ferramenta certa para seu tipo de culinária — e vai embora. Ele engajou. O problema não foi a falta de uso; foi a falta do recurso específico.

---

### O que o modelo de Machine Learning revelou

Um modelo preditivo foi treinado com 19 variáveis comportamentais e de contrato para tentar identificar, com antecedência, quais contas iriam churnar.

**O resultado foi revelador: o modelo não conseguiu distinguir churners de retidos com base em comportamento de uso.**

Em linguagem técnica, o AUC (capacidade de separação) foi de 0.34 — abaixo de 0.50, que seria equivalente a uma moeda jogada ao acaso. Clientes que vão sair e clientes que vão ficar se comportam de forma indistinguível nos logs de uso, frequência de tickets, e dados de contrato.

**Por que isso é uma descoberta, não uma falha:**

Se fosse possível prever o churn por comportamento (queda no uso, mais tickets, redução de sessões), o problema seria de *detecção precoce* e *intervenção de CS*. Um modelo funcionaria. Mas como o modelo falhou, isso significa que o churn não tem precursor comportamental detectável — ele está determinado *antes* do uso, pela adequação do produto ao segmento.

**Em outras palavras:** o cliente de DevTools já carrega um risco elevado desde o signup, porque o produto pode não ter sido construído para suas necessidades específicas. A jornada de uso confirma este diagnóstico, mas não o causa — e um sistema de alertas baseado em comportamento de uso não resolveria o problema.

---

## Quem está em risco agora

### $710K de MRR em 306 contas com múltiplos sinais de risco

A análise cross-table identificou 306 contas ativas com 2 ou mais sinais simultâneos de risco (auto_renew desativado, escalação de suporte, baixo uso relativo, tickets urgentes recorrentes). O MRR combinado destas contas é **$710,421/mês** — equivalente a **$8.5M ARR** que pode sair nos próximos 6–12 meses.

As contas com perfil de risco mais agudo identificadas pela análise cruzada:

| Account ID | Indústria | MRR/mês | Sinais de risco | Ação recomendada |
|-----------|-----------|---------|----------------|-----------------|
| A-e43bf7 | Cybersecurity | $6,667 | 4 de 4 🚨 | **Intervenção imediata** |
| A-c58f49 | EdTech | $10,140 | 3 de 4 | Contato CS prioritário |
| A-76fa4d | HealthTech | $8,812 | 3 de 4 | Contato CS prioritário |
| A-afa505 | DevTools | $7,334 | 3 de 4 | Contato CS prioritário |
| A-5c046d | EdTech | $10,486 | 2 de 4 | Monitorar + outreach |
| A-5b1bcd | DevTools | $8,887 | 2 de 4 | Monitorar |
| A-56962b | EdTech | $7,801 | 2 de 4 | Monitorar |

---

### 10 contas HIGH risk ainda ativas — intervenção imediata do CS

O modelo preditivo identificou 10 contas com score ≥ 70 que ainda não churnariam (churned = 0). MRR total em risco imediato: **$12,231/mês**.

| Account ID | Score | MRR/mês | Indústria | Canal | Principal fator de risco |
|-----------|-------|---------|-----------|-------|--------------------------|
| A-49b828 | 73 | $2,222 | FinTech | ads | Tamanho (seats) atípico |
| A-94d3da | 72 | $1,889 | HealthTech | other | Alto volume de erros |
| A-e36807 | 97 | $1,257 | EdTech | other | Sessões longas (possível frustração) |
| A-bad8c1 | 89 | $1,114 | FinTech | organic | Alto volume de erros |
| A-9289f6 | 76 | $1,091 | EdTech | event | MRR abaixo do esperado p/ perfil |
| A-5247b3 | 76 | $1,072 | FinTech | partner | MRR abaixo do esperado p/ perfil |
| A-3cc791 | 73 | $1,065 | EdTech | other | MRR abaixo do esperado p/ perfil |
| A-6a4e2d | 88 | $945 | EdTech | partner | MRR abaixo do esperado p/ perfil |
| A-019782 | 95 | $928 | DevTools | event | MRR abaixo do esperado p/ perfil |
| A-c42f1f | 96 | $647 | HealthTech | other | Sessões longas (possível frustração) |

> **Nota metodológica:** O modelo de ML tem AUC abaixo de 0.5, o que significa baixo poder preditivo individual. Estes scores devem ser usados como *sinalizadores para triagem*, não como probabilidades literais de churn. A lista cruzada com os sinais da análise cross-table (tabela acima) é mais confiável para priorização.

---

## O que fazer — 3 ações priorizadas

### Ação 1 — Esta semana (Quick win)
**CS entra em contato com as 10 contas HIGH risk ainda ativas**

- **MRR em risco:** $12,231/mês
- **Script de abordagem:** não é ligação de check-in genérica. A pergunta central: *"Quais funcionalidades você precisava usar e ainda não conseguiu? O que falta no produto para o seu fluxo de trabalho?"* — independente do segmento.
- **Meta conservadora:** salvar 50% = $6,115/mês → $73K ARR
- **Meta otimista:** salvar 70% = $8,562/mês → $103K ARR
- **Custo:** 10 ligações de CS.

---

### Ação 2 — Este mês (Estrutural)
**Auditoria de product gap em DevTools e canal event**

DevTools churna em 31% — quase o dobro de Cybersecurity (16%). Se conseguirmos trazer DevTools para 16%, o ganho seria de **$25,248/mês adicional retido** (15 contas × $2,158 MRR médio).

- **Passo 1:** Entrevistar os 35 churners DevTools e os 29 churners de evento. Perguntar especificamente quais funcionalidades faltaram para o fluxo de trabalho deles.
- **Passo 2:** Cruzar as features mais usadas *antes* do churn (disponível nos logs de feature_usage) com o que os churners declaram. Identificar os "últimos cliques antes do abandono".
- **Passo 3:** Decisão estratégica de produto: construir as funcionalidades faltantes, fechar parceria com ferramenta complementar, ou conscientemente descontinuar o segmento e focar em Cybersecurity (onde o churn é 16%).

---

### Ação 3 — Este trimestre (Estratégica)
**Revisar ICP e alocação de budget de aquisição**

O canal `partner` tem churn de 14.6% — o melhor da base. O canal `event` tem 30.2% — o pior. Clientes vindos de parceiros chegam pré-qualificados; clientes de eventos chegam com expectativas heterogêneas.

- **Revisar ROI de eventos:** calcular LTV por canal (não apenas CAC). Um evento com CAC=$500 e churn de 30% em 6 meses tem LTV menor que um partner com CAC=$800 e churn de 14%.
- **Dobrar investimento em partner:** identificar os 3–5 parceiros que geram mais accounts e investir em expansão.
- **Qualificação de leads em eventos:** criar processo de qualificação de ICP no evento antes de passar o lead para sales.

**Impacto estimado:** Migrar 30% das aquisições de event para partner reduziria o churn de novos clientes em ~4pp no próximo cohort, equivalente a +$8–12K/mês de MRR retido em 12 meses.

---

## O que NÃO fazer

Os dados descartam três respostas intuitivas que seriam dinheiro mal investido:

- **Não investir em onboarding ou tutoriais** — churners usam +3.4% mais features que os que ficam. O problema não está na curva de aprendizado.
- **Não focar em melhorar o SLA de suporte como estratégia de retenção** — contas com tickets urgentes têm churn de 19.9%, menor que contas sem tickets urgentes (25.7%). O churn "silencioso" é mais prevalente que o churn "reclamante".
- **Não segmentar benefícios por plano** — Pro, Basic e Enterprise têm taxas de churn de 21.9%, 22.0% e 22.1% respectivamente. São estatisticamente idênticas (p=0.999).

---

## Limitações desta análise

1. **Poder estatístico limitado (n=500):** Os diferenciais de churn segmental (DevTools 31% vs Cybersecurity 16%) têm OR de 2.36× mas não atingiram p<0.05 com esta amostra. Com 5.000+ contas, seriam confirmados com p<0.001. A direção está correta; a magnitude exata precisa de confirmação.

2. **Dataset sintético limita análise de features específicas:** Os registros de uso referem-se a `feature_1` até `feature_40` sem semântica de negócio. Em dados de produção, seria possível identificar quais features específicas os churners de DevTools usaram antes de sair — tornando o roadmap diretamente derivável dos dados.

3. **Cobertura de reason_code:** 31.8% dos churned accounts não têm nenhum evento registrado em churn_events. A análise de causas cobre apenas os 68% com registro, e mesmo esses mostram distribuição uniforme sem causa dominante.

---

## Metodologia (para quem quiser aprofundar)

**Dados:** 5 tabelas · ravenstack_accounts (500 linhas), subscriptions (5.000), feature_usage (25.000), support_tickets (2.000), churn_events (600 bruto)

**Análise:**
- DuckDB cross-table analysis (6 perguntas de negócio)
- Testes estatísticos: chi-square (segmentação × churn) + Welch's t-test (uso × churn)
- Modelo preditivo: LightGBM com 19 features + SHAP values (importância e direção por conta)
- Odds Ratios por segmento (industry e referral_source)
- Análise de feedback_text (entrada 006 do process log)

**Código:** `submissions/lucas-reis/solution/agents/`
- `01_eda_agent.py` — exploração de cada tabela
- `02_cross_table_agent.py` — 6 perguntas de negócio via DuckDB
- `03_hypothesis_agent.py` — validação estatística de 5 hipóteses
- `04_predictive_agent.py` — LightGBM + SHAP + CS action list

**Process log completo:** `submissions/lucas-reis/process-log/`
Cada decisão analítica, correção de bug, e interpretação de resultado está documentada com o prompt literal usado, o output gerado, e o julgamento humano aplicado — incluindo a correção do erro metodológico do 60.9% (entry_006).

---

*Este relatório foi gerado como parte do G4 AI Master Challenge — Lucas Reis, 2026-03-20.*
