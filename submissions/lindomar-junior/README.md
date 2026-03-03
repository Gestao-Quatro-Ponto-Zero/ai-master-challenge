# Submissão — Lindomar Junior — Challenge 002

## Sobre mim

- **Nome:** Lindomar Junior
- **LinkedIn:** https://www.linkedin.com/in/lindomar-junior-48820b288
- **Challenge escolhido:** 002 — Redesign de Suporte

---

## Executive Summary

Diagnostiquei 8.469 tickets de suporte e encontrei que **67,3% estão sem resolução** — não um pico temporário, mas o estado normal da operação. O achado mais contraintuitivo: tempo de resolução tem correlação de **-0,001** com satisfação do cliente, o que muda completamente onde vale investir automação. Construí um protótipo funcional chamado **Support Triage AI** (React + API Anthropic) que classifica tickets em tempo real, recalibra prioridade, calcula risco financeiro e roteia entre quatro níveis — Auto-resolve, Agent assist, Human required e Supervisor escalation. A principal recomendação é automatizar Product inquiry e Billing inquiry (~38,7% do volume) e **não** automatizar Refund e Cancellation, onde o problema é mérito da resolução, não velocidade.

---

## Solução

### Abordagem

Antes de abrir qualquer ferramenta, escrevi três hipóteses sobre o dataset. A mais importante: *tempo de resolução provavelmente não explica satisfação — clientes insatisfeitos têm problema de mérito, não de velocidade*. Essa hipótese se confirmou e mudou toda a direção da proposta.

A decomposição do problema seguiu a ordem do challenge:

1. **Diagnóstico com dados** — exploração completa do Dataset 1 (métricas operacionais) com foco nos achados que vão além do óbvio
2. **Cruzamento dos datasets** — treinar classificador no Dataset 2 e aplicar ao Dataset 1 para adicionar dimensão de categoria IT
3. **Proposta de automação com critério** — definir o que automatizar *e* o que não automatizar, com justificativa nos dados
4. **Protótipo que demonstra a proposta** — não slides, mas algo que roda com tickets reais

### Resultados / Findings

#### Gargalo principal — backlog estrutural

| Status | Qtd | % |
|---|---|---|
| Closed | 2.769 | 32,7% |
| Open (aguardando agente) | 2.819 | 33,3% |
| Pending (aguardando cliente) | 2.881 | 34,0% |
| **Não resolvidos** | **5.700** | **67,3%** |

692 tickets **Critical + Open** sem nenhuma resposta registrada.

#### A priorização está invertida

Tempo mediano de resolução por prioridade — tickets fechados:

| High | Low | Critical | Medium |
|---|---|---|---|
| **7,28h ⚠** | 6,98h | 6,55h | **6,18h ✓** |

High demora mais que Critical. A distribuição de prioridades é quase uniforme (~25% em cada nível para todas as categorias) — evidência de que a prioridade foi atribuída sem critério sistemático, provavelmente pelo próprio cliente ao abrir o ticket.

#### Tempo não explica satisfação

| Variável | Correlação com CSAT | p-valor |
|---|---|---|
| Tempo de resolução | **-0,001** | 0,947 |

Clientes com nota 1 e nota 5 passaram em média 7,56h vs 7,91h em resolução — 21 minutos de diferença numa escala de 5 pontos. Resolver mais rápido não move o ponteiro.

Piores combinações identificadas:

| Canal | Tipo | Prioridade | CSAT |
|---|---|---|---|
| Phone | Refund request | High | **2,29** |
| Email | Cancellation request | High | **2,53** |
| Social media | Technical issue | High | **2,56** |

#### Classificador IT — acurácia no test set (20%)

Modelo: TF-IDF bigramas + Logistic Regression, treinado nos 47.837 tickets do Dataset 2.

| Categoria | Precisão | Recall | F1 |
|---|---|---|---|
| Purchase | 0,99 | 0,85 | **0,91** |
| Access | 0,92 | 0,87 | **0,89** |
| Storage | 0,96 | 0,80 | 0,87 |
| HR Support | 0,86 | 0,88 | 0,87 |
| Hardware | 0,79 | 0,90 | 0,84 |
| Administrative rights | 0,91 | 0,62 | 0,74 |
| **Acurácia geral** | | | **0,86** |

> **Limitação documentada:** 89,7% dos tickets do Dataset 1 foram classificados como Hardware por domain shift (tickets de TI corporativo vs. suporte B2C com textos sintéticos). A coluna `Ticket Type` nativa é mais confiável para segmentar este dataset.

#### Estimativa de economia com automação (70%)

Usando AHT de 20 min/ticket (wall-clock time de 7,75h não é labor time):

| Cenário | AHT | Tickets auto/mês | USD/mês | USD/ano |
|---|---|---|---|---|
| Conservador | 15 min | 681 | $4.258 | $51.100 |
| **Base** | **20 min** | **681** | **$5.678** | **$68.134** |
| Otimista | 30 min | 681 | $8.517 | $102.200 |

### Recomendações

> **TL;DR para o Diretor de Operações**
>
> **Três números que resumem o problema:**
> - **67,3%** dos tickets estão parados — backlog permanente, não pico temporário
> - **2,99/5** de CSAT com distribuição uniforme — o problema é qualidade de resolução, não velocidade
> - **692 tickets Critical** sem resposta — a triagem de prioridade está quebrada (High demora mais que Critical)
>
> **Três ações com maior ROI:**
> 1. Automatizar Product inquiry + Billing inquiry → USD $68K/ano estimados, 681 tickets/mês sem agente
> 2. Recalibrar prioridade por tipo de ticket → corrige a inversão High > Critical sem custo adicional
> 3. Self-service de Access → potencial de 85%+ de self-resolution
>
> **O que não fazer:** não automatizar Refund + Cancellation — 40,7% do volume, piores CSATs, envolvem decisão financeira e retenção. A IA tria, não resolve.

**1. Automatizar — Product inquiry + Billing inquiry + Access (38,7% + 6,5% do volume)**

Perguntas de produto, dúvidas de cobrança sem disputa financeira e reset de conta/senha têm padrão repetitivo e não exigem julgamento. Self-service de Access pode chegar a 85%+ de resolução autônoma. Economia estimada: USD $68K/ano no cenário base.

**2. Recalibrar prioridade por tipo de ticket — custo zero**

Corrigir a inversão High > Critical (7,28h vs 6,55h) é mudança de processo, não de tecnologia. Um roteador que reatribui prioridade com base em `Ticket Type + Canal + histórico de contato anterior` resolve sem custo adicional.

**3. Follow-up automático em Pending — recuperar 30% do backlog**

2.881 tickets aguardando cliente sem follow-up automatizado. Um trigger de 48h com mensagem contextual fecha ~864 tickets/mês sem intervenção do agente.

**4. Não automatizar Refund + Cancellation (40,7% do volume)**

Esses dois tipos concentram os piores CSATs e envolvem decisão financeira e oportunidade de retenção. A IA deve triá-los e contextualizá-los para o agente — não resolvê-los. Automatizar aqui reduz custo operacional de curto prazo e destrói confiança de longo prazo.

### Limitações

- **Textos sintéticos no Dataset 1** — `Resolution` e `Ticket Description` são frases geradas aleatoriamente. Qualquer análise de NLP sobre esses textos (clustering, similaridade semântica) não é confiável. O diagnóstico se apoia nas colunas estruturadas (tipo, canal, prioridade, status, CSAT).
- **Timestamps são snapshot** — FRT e TTR cobrem ~2 dias (2023-05-31 a 2023-06-02). Não é série temporal — impossível analisar sazonalidade, picos ou tendência. A projeção de volume usa os 30.000 tickets/ano do enunciado do challenge.
- **Domain shift no classificador** — o modelo treinado no Dataset 2 (TI corporativo) não transfere bem para o Dataset 1 (suporte B2C). Com dados reais de produção, um classificador fine-tuned no próprio dataset teria acurácia substancialmente maior.
- **ROI sem custo de implementação** — a estimativa de economia não desconta custo de desenvolvimento, manutenção do modelo e revisão humana das respostas automáticas. Em produção, o payback real seria ~6-12 meses.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Jupyter Notebook | Análise exploratória, construção de métricas e validação de hipóteses no Dataset 1 |
| Claude (claude.ai) | Interlocutor analítico durante toda a exploração — validação de interpretações, geração de hipóteses alternativas, iteração do system prompt do protótipo |
| Python + scikit-learn | Análise exploratória, treinamento do classificador TF-IDF + LR, quantificação do backlog e estimativas de ROI |
| API Anthropic (claude-sonnet-4) | Motor de triagem do protótipo — classificação, roteamento, geração de resposta sugerida em tempo real |
| React (JSX) | Interface do protótipo Support Triage AI v3 |

### Workflow

1. **Leitura do challenge antes de abrir qualquer dado** — entender o que o Diretor de Operações quer de verdade: não análise genérica, mas três coisas específicas com evidências
2. **Hipóteses escritas antes da exploração** — três hipóteses registradas antes de abrir o CSV, para evitar viés de confirmação
3. **Primeira análise no Jupyter Notebook** (`docs/metricas_operacionais.html`) — análise exploratória inicial do Dataset 1: inspeção de nulos, distribuição de status, top 5 tipos e assuntos de tickets não resolvidos, cálculo de `Resolution Duration Hours`, drill-down por Cancellation, Technical issue e Refund request com top 10 produtos e assuntos por tipo
4. **Inspeção de qualidade dos dados** — identificar que os textos são sintéticos, que FRT/TTR são timestamps absolutos (não durações), e que 67,3% dos tickets não têm resolução registrada
5. **Análise exploratória iterativa com Claude** — cada achado validado com o Claude pedindo "o que esse número pode estar escondendo?"
5. **Treinamento do classificador no Dataset 2** — TF-IDF + LR com cross-validation, aplicado ao Dataset 1, com documentação do domain shift
6. **Cruzamentos analíticos** — prioridade vs. tempo de resolução (inversão High > Critical), correlação CSAT vs. tempo (resultado: zero), piores combos canal × tipo × prioridade
7. **Proposta de automação** — definição dos critérios com base nos dados, não em intuição
8. **Protótipo em 3 iterações** — v1 dark theme 2 colunas → v2 light theme + Supervisor escalation → v3 coluna única + respostas refinadas
9. **Refinamento do system prompt** — 4 ciclos com casos de teste reais do dataset para calibrar roteamento e tom das respostas
10. **Process log e submissão** — documentação do processo com ênfase nas decisões e divergências

### Onde a IA errou e como corrigi

**Erro 1 — Cálculo de ROI inflado**

O Claude calculou a economia usando os 7,75h de wall-clock time (diferença entre FRT e TTR) como proxy de custo de labor. O resultado: USD $130K/mês — número indefensável numa apresentação. Identifiquei que esses são timestamps de snapshot de fila, não tempo ativo do agente. Corrigi usando AHT (Average Handling Time) de mercado: 15-30 min/ticket. Resultado corrigido: USD $4.258-8.517/mês — uma diferença de 15-30x.

**Erro 2 — Roteamento permissivo demais na v1**

Na primeira versão do system prompt, Billing inquiry com cobrança duplicada era roteado como Auto-resolve. Ao testar com o exemplo "fui cobrado duas vezes", percebo que há disputa financeira — não é FAQ. Adicionei distinção explícita no prompt: dúvida de cobrança sem disputa = Auto-resolve; disputa financeira = Agent assist.

**Erro 3 — Próximos passos descrevendo ações do agente, não do cliente**

O campo `next_steps` gerava coisas como "encaminhe o ticket para o time financeiro" — ação do agente. O campo deveria conter o que o *cliente* deve fazer. Reescrevi a instrução com exemplos bons ("Aguarde o e-mail de confirmação em até 2h") e ruins ("Aguarde nosso contato") diretamente no prompt.

### O que eu adicionei que a IA sozinha não faria

**1. Identificar que a correlação -0,001 muda a estratégia toda**

A IA calculou a correlação. Mas a conclusão — *"isso significa que reduzir SLA não vai mover o CSAT, portanto a automação deve focar em qualidade de resolução, não em velocidade"* — é um salto analítico que exige contexto de negócio, não só estatística.

**2. Documentar o domain shift em vez de esconder**

A resposta óbvia ao ver 89,7% de Hardware seria ignorar o resultado ou tentar um modelo diferente. Decidi documentar a limitação explicitamente, porque isso demonstra que o modelo foi avaliado criticamente — e porque o Dataset 2 ainda tem valor como base de treino para produção com dados reais.

**3. Escolher os 5 tickets de exemplo do protótipo**

Não foram escolhidos aleatoriamente. Cada um foi selecionado para cobrir um dos três caminhos de roteamento e, especificamente, para incluir o pior combo identificado na análise (Phone + Refund + High, CSAT 2,29). Isso conecta diagnóstico com protótipo de forma demonstrável.

**4. A regra "não automatizar Refund + Cancellation"**

A IA, se perguntada genericamente, diria "automatize tudo que tiver padrão repetitivo". A decisão de não automatizar esses dois tipos vem de cruzar três dados: CSAT mais baixo (2,93 e 3,03), volume de 40,7%, e o fato de que Cancellation é oportunidade de retenção que desaparece com automação.

---

## Evidências

- [x] `solution/customer_support_tickets_labeled.csv` — Dataset 1 com colunas `Predicted_Topic` e `Prediction_Confidence` adicionadas
- [x] `solution/conclusoes_diagnostico.md` — diagnóstico operacional completo com todos os números
- [x] `solution/support_triage_v3.jsx` — código-fonte do protótipo Support Triage AI v3
- [x] `docs/metricas_operacionais.html` — notebook Jupyter com análise exploratória do Dataset 1

---

_Submissão enviada em: 03/03/2026_
