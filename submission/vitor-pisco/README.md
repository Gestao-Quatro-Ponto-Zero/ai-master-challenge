# Submissão — Vitor Pisco — Challenge build-003-lead-scorer

## Sobre mim

- **Nome:** Vitor Elisio Viana Pisco
- **LinkedIn:** [linkedin.com/in/vitorpisco](https://www.linkedin.com/in/vitorpisco/)
- **Challenge escolhido:** build-003-lead-scorer

---

## Executive Summary

Times de vendas perdem negócios não por falta de oportunidades, mas por falta de priorização. A solução entregue é o **Pipeline Coach AI**: uma aplicação web funcional que recebe os CSVs exportados do CRM e devolve, para cada vendedor, os 5 deals mais urgentes do dia — ordenados por um scoring engine de 5 dimensões, com o motivo explícito de cada recomendação. O produto foi construído em camadas: análise exploratória Python sobre 8.800 oportunidades → especificação técnica de produto com PRD e 8 arquivos de contexto para agentes de IA → prompts executáveis para construtores de site → aplicação funcional em produção. A principal recomendação para a equipe comercial é implementar a tabela de interações em produção — o maior ganho de precisão do scoring virá quando D1 (tempo sem contato) parar de usar `engage_date` como proxy e passar a usar a data real da última interação registrada.

---

## Solução

### Abordagem

O problema da Head de RevOps foi decomposto em três camadas antes de qualquer linha de código:

1. **Dados disponíveis** — entender o que o dataset CRM realmente contém e quais anomalias existem
2. **Insights acionáveis** — transformar padrões nos dados em critérios de priorização defensáveis
3. **Ferramenta usável** — entregar uma interface que um vendedor real abra na segunda de manhã e use sem treinamento

O desenvolvimento seguiu essa ordem estritamente. Nenhuma decisão de produto foi tomada antes de entender os dados. Nenhum prompt para construtor de site foi escrito antes de ter o PRD completo. Cada camada alimentou a seguinte.

### Resultados / Findings

**Aplicação ao vivo:** [pipelinecoachai.lovable.app](https://pipelinecoachai.lovable.app/)

Para usar: acesse a URL → faça upload dos 5 CSVs → selecione "Vendedor" ou "Gestor" → escolha um rep no dropdown.

#### O que a aplicação entrega

**Dashboard de Atividades (`/rep`)** — 4 blocos acima do fold, ordem fixa:
- 🔥 **Prioridades do dia** — Top 5 deals com score 0–100, badge colorido (Crítico/Alto/Médio/Baixo), razão explícita da recomendação e 3 ações: Executado / Reagendar / Ignorar
- ⚠️ **Contas em risco** — Deals com aging > 1,2× a média do escritório, Top 3 com link "Ver todas"
- 📵 **Ranking sem contato** — Deals ordenados por dias desde o engajamento
- 📊 **Execution Score** — % de ações executadas na sessão com meta e mensagem contextual

**Dashboard de Resultados (`/rep/results`)** — 7 visualizações baseadas em dados históricos reais:
- Receita mensal por deals fechados (barras + linha de win rate sobreposta)
- Timeline de receita por produto (barras empilhadas por mês)
- Distribuição de ciclo de fechamento em 4 faixas (`<30d / 30–60d / 60–90d / >90d`)
- Curva de receita acumulada (área + linha de tendência)
- Top 10 contas por receita (tabela com setor, ticket médio, último fechamento)
- Mix de produtos (donut com % de participação na receita)
- KPIs fixos: receita total, win rate, ticket médio, ciclo médio vs benchmark

**Dashboard do Gestor (`/manager`)** — 5 blocos:
- Ranking de Execution Score da equipe
- Aging médio por vendedor (pior primeiro, outliers destacados)
- Ranking sem contato por rep
- Pipeline coverage por vendedor
- Conversão por produto × rep (matriz com escala de cor)

#### Findings dos dados (8.800 oportunidades, 2016–2017)

| Métrica | Valor |
|---------|-------|
| Win rate geral | 63,2% (Won / Won+Lost) |
| Receita realizada | $10.005.534 |
| Ciclo médio de fechamento | 51,8 dias |
| Pipeline aberto estimado | $4.966.215 |
| Reps ativos (com deals) | 30 de 35 |

**Principais padrões identificados:**
- **Concentração de receita:** Darcel Schlecht representa $1,15M — mais que o dobro do 2º colocado ($478K). Risco de saída alto.
- **Win rate oscilante:** padrão de ondas mensais (Mar=82%, Abr=48%, Jun=82%, Jul=49%). Não é ruído — é pipeline que abre num mês e fecha dois meses depois em bloco.
- **GTK 500 subutilizado:** preço de lista $26.768 (10× o GTX Basic). Apenas 15 deals fechados no período. Elease Gluck e Rosalina Dieter têm os melhores resultados nesse produto — candidatos a especialização enterprise.
- **MG Special sem ROI de esforço:** 793 deals fechados, apenas $43.768 em receita. Ticket médio de $55 — consumo de pipeline sem retorno real.
- **5 vendedores sem nenhum deal** no CRM (Mei-Mei Johns, Elizabeth Anderson, Natalya Ivanova, Carol Thompson, Carl Lin).

### Recomendações

**Para a equipe comercial — implementar imediatamente:**

1. **Criar a tabela de interações no CRM** — é o P0 técnico mais impactante. O scoring usa `engage_date` como proxy de "último contato". Com a tabela real, D1 (25 pts) passa a refletir comportamento verdadeiro do rep, não o tempo decorrido desde o engajamento.

2. **Especializar Elease Gluck e Rosalina Dieter em GTK 500** — são os únicos com histórico relevante no produto de maior ticket. Um rep especializado em enterprise com playbook dedicado pode mudar o resultado dos 15 deals abertos em GTK 500 ($401K de pipeline estimado).

3. **Revisar estratégia do MG Special** — 793 deals fechados para $43K de receita não justifica esforço de pipeline. Avaliar se o produto deve sair do CRM ou receber pricing revision.

4. **Plano de sucessão para Darcel Schlecht** — 11,5% da receita total em um único rep é risco de concentração crítico. Documentar o playbook dele e replicar para os 3 reps mais próximos.

5. **Coaching focado em Lajuana Vencill** — win rate de 55% (8pp abaixo da média) + ciclo de 62,9 dias. Tem 80 deals abertos com $116K de pipeline estimado. Prioridade alta para 1:1 antes do próximo ciclo.

**Para o produto — próximas features P0:**

- Persistência de dados entre sessões (banco de dados)
- Autenticação com roles (rep vs manager vs revops)
- Email automático às 08:00 com as prioridades do dia
- Sync via API com CRM (Salesforce/HubSpot/Pipedrive) para eliminar upload manual

### Limitações

**Limitações técnicas do MVP:**

| O que não faz | O que seria necessário |
|---|---|
| Sem persistência entre sessões | PostgreSQL + Redis |
| Sem autenticação real | JWT com roles por `regional_office` |
| Sem email automático | Cron 07:00 + SendGrid/Resend |
| Sem sync com CRM | Webhook ou API do CRM |
| Execution Score zera ao recarregar | Tabela `daily_priorities` persistida |
| Sem metas/quotas configuráveis | Tabela `quotas` por rep/período |

**Limitações dos dados:**

- **D1 usa proxy, não dado real:** o dataset não tem tabela de interações. `engage_date` é usado como substituto — D1 nunca zera quando o rep faz contato real, apenas cresce com o tempo.
- **Win rate por vendedor fora do scoring:** o histórico individual de WR (disponível nos dados) não alimenta o score de prioridade. Em produção, um rep com 70% de WR em GTX Plus Pro receberia boost nesse produto.
- **Dataset histórico fixo (2016–2017):** os deals "abertos" já têm resultado em produção. Data de referência fixada em `2017-12-27` para todos os cálculos de aging.
- **16,2% das linhas sem conta identificada:** 1.425 oportunidades sem `account` associado. O score não é afetado, mas o enriquecimento com setor/porte fica comprometido para essas linhas.

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| ChatGPT (GPT-4) | Prompt inicial de decomposição do problema — entender o que a Head de RevOps realmente precisava antes de começar qualquer desenvolvimento |
| Claude (Anthropic) | Desenvolvimento principal: análise exploratória Python nos CSVs, geração dos 8 arquivos `.md` de contexto para agentes, criação dos dashboards HTML, especificação do scoring engine, escrita dos dois prompts para construtores de site, documentação técnica completa |
| Lovable | Agente construtor de sites — recebeu `MVP_BUILDER_PROMPT.md` e depois `MVP_UPDATE_RESULTS_PROMPT.md` sequencialmente e construiu a aplicação React funcional |
| Antigravity | Segundo agente construtor — usado para validação cruzada dos prompts, confirmando que a especificação era autossuficiente e independente de plataforma |

### Workflow

1. **[ChatGPT] Decomposição do problema** — Prompt inicial pediu ao modelo estruturar o que a Head de RevOps realmente precisava. Resultado: três camadas (dados disponíveis → insights acionáveis → ferramenta usável). Essa estrutura guiou todo o restante.

2. **[Decisão humana] Migrar para Claude** — Reconhecimento de que o trabalho de desenvolvimento denso — análise de dados, geração de múltiplos arquivos interdependentes, código TypeScript — precisava de uma ferramenta com capacidade de contexto persistente e estruturado. Claude foi escolhido para todas as fases seguintes.

3. **[Claude] Análise exploratória dos dados** — 4 rodadas de scripts Python sobre os CSVs: distribuição de stages, win rate por vendedor, ciclo médio, padrão de oscilação mensal, ticket médio por produto, top contas, distribuição de ciclos por faixa. Os números reais informaram cada decisão de scoring.

4. **[Claude] Dashboard de análise (`sales_dashboard.html`)** — Antes de especificar o produto, construção de um dashboard interativo HTML/JS com os dados reais para tornar padrões visíveis. 5 visões: funil, top vendedores, produtos, agente individual, gargalos.

5. **[Claude] Especificação completa do produto** — PRD com 7 features, 3 perfis de usuário e 5 KPIs. Documentação visual navegável (`pipeline_coach_docs.html`). 8 arquivos `.md` otimizados para agentes: `AGENT_INSTRUCTIONS.md`, `PRODUCT_SPEC.md`, `SCORING_ENGINE.md`, `DASHBOARD_SPEC.md`, `UX_RISKS.md`, `USER_JOURNEYS.md`, `DATA_SCHEMA.md`, `DIAGRAMS.md`.

6. **[Claude] Criação do Prompt 1** — `MVP_BUILDER_PROMPT.md` (574 linhas): schema TypeScript do scoring, regras de normalização de dados, stack técnica, design system com cores obrigatórias, copy rules, checklist de validação, ordem de build.

7. **[Lovable] Build do MVP** — `MVP_BUILDER_PROMPT.md` executado no Lovable. Aplicação funcional na primeira execução: upload de CSVs, scoring engine, dashboard de atividades com 4 blocos, dashboard do gestor.

8. **[Decisão humana] Gap identificado em uso real** — Após testar o MVP, percepção de que o vendedor sabia o que fazer (atividades) mas não via o que já tinha feito (resultados). Lacuna não estava no briefing original.

9. **[Claude] Nova análise + Prompt 2** — Análise específica para o dashboard de resultados: receita por mês, por produto por mês, distribuição de ciclos, top contas. `MVP_UPDATE_RESULTS_PROMPT.md` criado com 7 visualizações especificadas com dados reais de referência.

10. **[Lovable + Antigravity] Build do update** — Segundo prompt executado em ambas as plataformas. Rota `/rep/results` adicionada com as 7 visualizações. Funcionou nas duas plataformas sem ajuste, confirmando que a spec era precisa o suficiente.

11. **[Claude] Documentação técnica** — `technical_documentation.html`: setup completo, lógica de scoring com justificativa de cada peso, limitações com roadmap de escala, e este process log.

### Onde a IA errou e como corrigi

**1. Scoring com data incorreta** *(Claude)*
A primeira versão do scoring usava `new Date()` para calcular "dias em aberto". O dataset é de 2017 — todos os deals ficavam com centenas de dias de aging, produzindo scores sem sentido. Corrigi adicionando `REFERENCE_DATE = new Date('2017-12-27')` e atualizei toda a documentação para proibir o uso de `new Date()` em análise de dados históricos.

**2. Join de produtos quebrando silenciosamente** *(Claude)*
O código fazia join direto de `pipeline.product` com `products.product` sem normalizar. `"GTX Pro"` vs `"GTXPro"` — o join retornava nulo para 729 deals (16,6% do total Won), zerando o valor estimado desses deals silenciosamente. Corrigi com função `normalizeProduct()` e cataloguei como "Known Data Issue" em `DATA_SCHEMA.md` e como erro proibido em `AGENT_INSTRUCTIONS.md`.

**3. `parseFloat()` quebrando em deals abertos** *(Claude)*
Tentativa de `parseFloat(r['close_value'])` direto em todos os deals. Para os 2.089 deals abertos, `close_value` é string vazia `""` — não null, não zero. Resultado: `NaN` propagado por todos os cálculos de valor. Corrigi com função `safeFloat()` com verificação de string vazia antes do parse.

**4. Dashboard de resultados ausente** *(lacuna identificada pelo humano)*
O MVP entregue pelo Prompt 1 tinha apenas visão de atividades. O vendedor não conseguia ver o que já tinha realizado — receita, evolução, produtos. Isso não estava no briefing original. Criei análise adicional e escrevi o `MVP_UPDATE_RESULTS_PROMPT.md` como segunda iteração.

**5. Padrão de ondas do win rate** *(documentação preventiva)*
O dataset tem win rate oscilando entre 48% e 83% mês a mês. Sem documentação, um agente construtor poderia tratar como bug ou gerar alertas de anomalia desnecessários. Adicionei explicação explícita no Prompt 2: "é um padrão de pipeline onde deals abertos num mês fecham dois meses depois em bloco."

### O que eu adicionei que a IA sozinha não faria

**Estratégia de ferramentas:** A decisão de usar ChatGPT apenas para decomposição inicial e migrar para Claude para o desenvolvimento principal não é óbvia. Exige reconhecer os trade-offs de cada modelo e saber quando trocar. A IA não decide isso por si mesma.

**Decomposição em três camadas antes de agir:** Estruturar o problema como "dados → insights → ferramenta" antes de qualquer análise foi a decisão que impediu o projeto de ir na direção errada. A IA executa dentro de uma direção — o humano escolhe qual direção.

**Identificação do gap de resultados em uso real:** Após testar o MVP no Lovable e no Antigravity, percebi que o vendedor sabia o que fazer mas não via o que já tinha feito. Essa lacuna não estava no briefing original nem nos documentos .docx do produto. Foi identificada usando a aplicação como um usuário real faria.

**Seleção das métricas relevantes para análise:** Claude executa scripts Python, mas quem decide "quero ver win rate por mês, distribuição de ciclos por faixa e top contas" sou eu — o julgamento de relevância para o problema de negócio específico.

**Interpretação do padrão de ondas mensais:** Claude identificou os números (82%, 48%, 82%, 49%...). Interpretar que é um padrão de waves de pipeline — não ruído nem bug — e documentar preventivamente para que agentes futuros não tentem "corrigir" os dados foi julgamento aplicado a contexto de negócio.

**Calibração dos pesos como decisão de produto:** D1+D2 somam 50% porque "deals bons esfriando" é o problema central do desafio — não porque é matematicamente ótimo. Essa tese de priorização é escolha humana, não algoritmo.

**Validação cruzada em duas plataformas:** A decisão de rodar os prompts no Lovable E no Antigravity para verificar que o resultado independia da plataforma foi metodológica — garante que a especificação funciona, não que uma plataforma específica a interpreta bem.

**Copy rules como governança:** Definir que o dashboard do gestor nunca pode usar a palavra "monitoramento" e que comparações de benchmark sempre devem vir acompanhadas de sugestão de ação são restrições baseadas em risco político real de produtos SaaS comerciais. A IA não tem esse contexto — foi adicionado intencionalmente.

---

## Evidências

### Solução auditável e reproduzível

**Aplicação ao vivo:** [pipelinecoachai.lovable.app](https://pipelinecoachai.lovable.app/)

**Scoring engine executável** — o coração da solução pode ser rodado independentemente:

```bash
# Pré-requisito: Python 3.8+, sem dependências externas
# CSVs na mesma pasta que scoring_engine.py

python scoring_engine.py --rep "Darcel Schlecht"
# → Top 5 prioridades com score breakdown D1–D5

python scoring_engine.py --validate
# → Verifica: win rate 63,2% ✅, normalização GTXPro ✅, account vazio 16,2% ✅

python scoring_engine.py --all-reps
# → Top-1 prioridade de todos os 27 reps ativos

python scoring_engine.py --rep "Lajuana Vencill" --top 10
# → Rep com WR crítico (55%) — 80 deals abertos
```

### Artefatos do processo

| Arquivo | O que evidencia | Verificável como |
|---------|----------------|-----------------|
| `scoring_engine.py` | Implementação completa do scoring — auditável linha a linha | `python scoring_engine.py --validate` |
| `PROCESS_LOG.md` | Prompts reais, saídas reais, erros com código antes/depois | Leitura + execução dos comandos |
| `sales_dashboard.html` | Análise exploratória feita *antes* do PRD | Ordem de criação dos arquivos |
| `agent-context/SCORING_ENGINE.md` | Spec escrita *antes* do código | Compare com `scoring_engine.py` |
| `agent-context/MVP_BUILDER_PROMPT.md` | Prompt que gerou a aplicação — 574 linhas | Cole no Lovable e execute |
| `agent-context/MVP_UPDATE_RESULTS_PROMPT.md` | Prompt 2 — após gap identificado em uso real | Cole no Lovable após Prompt 1 |
| `agent-context/AGENT_INSTRUCTIONS.md` | Erros proibidos — todos baseados em falhas reais da IA | Seção 7: "Things agents must not do" |
| `technical_documentation.html` | Setup, scoring, limitações e roadmap | Abrir no browser |

### Como reproduzir a aplicação do zero

1. Abra [Lovable](https://lovable.dev), [Bolt](https://bolt.new) ou [Antigravity](https://antigravity.dev)
2. Cole o conteúdo completo de `agent-context/MVP_BUILDER_PROMPT.md` como primeiro prompt
3. Aguarde o build — a aplicação é gerada sem interação intermediária
4. Cole o conteúdo de `agent-context/MVP_UPDATE_RESULTS_PROMPT.md` como segundo prompt
5. Faça upload dos 5 CSVs na tela `/upload` da aplicação gerada

### Como verificar que o scoring da aplicação é idêntico ao `scoring_engine.py`

1. Execute `python scoring_engine.py --rep "Darcel Schlecht"`
2. Anote o score e o breakdown do deal #1 (ex: Score=100, D1=25+D2=25+D3=20+D4=20+D5=10)
3. Acesse [pipelinecoachai.lovable.app](https://pipelinecoachai.lovable.app/)
4. Faça upload dos CSVs → selecione Darcel Schlecht
5. O deal #1 na tela deve ter o mesmo score e a mesma razão

Os dois implementam a mesma fórmula com a mesma `REFERENCE_DATE = 2017-12-27`.

---

_Submissão enviada em: 31 de março de 2026_  
_Atualizada em: 31 de março de 2026 — adicionados `scoring_engine.py` e `PROCESS_LOG.md` em resposta ao feedback do PR_
