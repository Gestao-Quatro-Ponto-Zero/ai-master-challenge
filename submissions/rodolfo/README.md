# Submissão — Rodolfo — Challenge 001

## Sobre mim

- **Nome:** Rodolfo
- **LinkedIn:** [rodolfosouzam](https://linkedin.com/in/rodolfosouzam)
- **Challenge escolhido:** 001 — Diagnóstico de Churn (RavenStack)

---

## Executive Summary

A RavenStack tem **22% de churn** (110/500 contas, $1.18M em MRR perdido). A análise cruzada de 5 datasets revela dois achados contraintuitivos: (1) satisfação e uso do produto são **praticamente idênticos** entre churned e retidos — o CEO estava certo nesses indicadores, (2) mas as causas **variam drasticamente por indústria**: DevTools churna por budget, HealthTech/EdTech por features, FinTech por suporte. A recomendação principal não é uma ação genérica, mas um **conjunto de intervenções segmentadas** por indústria, país e perfil de risco.

---

## Solução

### Abordagem

1. **Entendimento do problema:** Identifiquei a contradição aparente (uso cresceu + satisfação ok, mas churn subiu) como o ponto de partida — em vez de ignorá-la, decidi testá-la com dados.
2. **Exploração e merge:** Carreguei as 5 tabelas, entendi chaves de ligação (account_id, subscription_id), tratei duplicatas (cada conta tem múltiplas assinaturas) e criei visão unificada por conta.
3. **Análise segmentada:** Calculei churn rate por indústria, plano, país, canal de aquisição, tamanho. Cruzei feature usage e suporte com churn.
4. **Geração de hipóteses:** Usei IA para sugerir cruzamentos não óbvios; testei cada hipótese com dados reais.
5. **Construção do relatório:** Gerei visualizações interativas (Plotly) e documentei findings em formato acionável para o CEO.

### Resultados / Findings

O relatório completo está disponível em [`report.html`](./report.html) com visualizações interativas. Principais descobertas:

| Achado | Detalhe |
|--------|---------|
| **Churn rate** | 22% (110/500) |
| **MRR perdido** | $1,179,139 |
| **Uso do produto** | Idêntico entre churned e retidos (média 52 usos) — não é falta de engajamento |
| **Satisfação** | 4.0 para ambos os grupos — não é insatisfação generalizada |
| **Maior churn por indústria** | DevTools (31%), seguido de FinTech (22%) |
| **Maior churn por país** | Alemanha/DE (32%) |
| **Causa varia por indústria** | DevTools → budget, HealthTech/EdTech → features, FinTech → support |
| **MRR perdido por causa** | Budget ($276K), Support ($267K), Features ($228K) |
| **Escalações** | Churned têm 2x mais escalações que retidos — melhor preditor que satisfação |
| **Contas em risco** | 21 contas ativas com score ≥ 60 (de 0-100) identificadas |

### Recomendações

1. **🔥 Intervir nas 21 contas em risco imediatamente** — CS Team em 48h com plano personalizado
2. **🔥 Ações por indústria** — DevTools (revisar pricing), HealthTech/EdTech (features), FinTech (suporte)
3. **🔥 Investigar churn na Alemanha** — 32% de churn, provável problema de localização
4. **📌 Dashboards por segmento** — parar de olhar médias agregadas
5. **📌 Revisar onboarding** — churn precoce (~primeiros dias) indica falha de ativação
6. **⚡ Programa pós-downgrade** — downgrade seguido de churn é padrão recuperável
7. **⚡ Modelo preditivo** — próximo passo após validação das intervenções

### Limitações

- **Causalidade vs correlação:** Análise descritiva identifica padrões, mas não prova causalidade. Recomendações de entrevistas de churn para validação qualitativa.
- **Dados de custo:** Não havia dados de CAC ou custo de suporte por ticket, o que impediu cálculo de ROI exato das intervenções.
- **Feedback textual:** 25% dos churn events têm feedback_text vazio. Análise de NLP seria mais robusta com preenchimento completo.
- **Modelo preditivo:** Não implementado como parte desta entrega (análise descritiva já responde às perguntas do CEO; modelo viria como next step).

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code | Análise exploratória, merge de datasets, geração de hipóteses, criação de visualizações, construção do relatório HTML |
| KaggleHub API | Download do dataset SaaS Subscription & Churn Analytics |
| Python (pandas, plotly, numpy) | Processamento, análise estatística e visualizações interativas |
| Git/GitHub | Fork do repositório, versionamento, PR de submissão |

### Workflow

1. **Entendimento do problema:** Li o README do challenge e identifiquei que o CEO tem uma contradição aparente (uso cresceu + satisfação ok, mas churn subiu) — usei isso como bússola da análise.
2. **Exploração dos dados:** Carreguei as 5 tabelas, entendi estrutura, chaves de ligação e qualidade com ajuda do Claude para identificar rapidamente os schemas e possíveis joins.
3. **Merge cruzado:** IA sugeriu o merge completo, mas eu percebi que cada account_id tem múltiplas subscriptions — precisei corrigir para pegar apenas a subscription ativa no momento do churn.
4. **Análise segmentada:** Claude gerou blocos de código para análise por indústria, plano, país. Eu validei cada output contra os dados brutos.
5. **Hipóteses:** IA sugeriu cruzamentos (beta features, upgrade/downgrade, etc.). Testei cada um com dados reais.
6. **Construção do relatório:** IA gerou o HTML + CSS + Plotly. Eu editei os insights e recomendações com base no que os dados realmente diziam.

### Onde a IA errou e como corrigi

- **Merge incorreto:** Claude fez merge direto account_id sem considerar múltiplas subscriptions por conta. Corrigi usando a subscription ativa na data do churn (start_date ≤ churn_date ≤ end_date).
- **Hipótese falsa:** IA sugeriu que "clientes com baixo uso churnam mais". Testei: uso é IDÊNTICO entre grupos. Removi essa conclusão e investiguei outras causas.
- **Satisfação:** IA inicialmente concluiu "satisfação é menor entre churned". Testei: média é 4.0 para ambos. Corrigi o insight — o que difere são escalações, não satisfação.
- **Over-engineering:** Claude sugeriu modelo XGBoost como primeira abordagem. Optei por análise descritiva + heurísticas primeiro, que já geram valor imediato.

### O que eu adicionei que a IA sozinha não faria

- **Contexto de negócio:** Entendi que a fala do CEO não é erro — é o paradoxo clássico de médias agregadas que escondem segmentos. A IA tratou como "dados inconsistentes"; eu tratei como "pista de investigação".
- **Análise por indústria:** IA não segmentou por indústria até eu pedir. Quando fiz, descobri que as causas de churn são completamente diferentes entre setores — o insight mais valioso do relatório.
- **Julgamento sobre o que não automatizar:** Decidi conscientemente não construir modelo preditivo — a análise descritiva já responde às perguntas do CEO. Modelo viria em uma segunda iteração.
- **Priorização das recomendações:** Não listei 20 ações. Priorizei 7, das quais 3 são críticas e acionáveis imediatamente.
- **Tom e comunicação:** Adaptei a linguagem para CEO não-técnico — executive summary de 5 frases, recomendações com "o que fazer" em vez de "o que observar".

---

## Evidências

- [x] Código-fonte da análise: [`analysis.py`](./analysis.py)
- [x] Visualizações interativas: [`report.html`](./report.html) + 10 gráficos Plotly individuais
- [x] Dados brutos: pasta [`data/`](./data/) com os 5 CSVs
- [x] Git history: branch `submission/rodolfo` neste repositório

---

*Submissão enviada em: 16/07/2026*
