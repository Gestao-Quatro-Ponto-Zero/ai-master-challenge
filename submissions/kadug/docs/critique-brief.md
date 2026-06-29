# Brief para Critique Externo

## Contexto

Estamos trabalhando no **AI Master Challenge do G4**, challenge escolhido:

- **Challenge:** 001 - Diagnostico de Churn
- **Empresa ficticia:** RavenStack
- **Problema:** churn aumentou, mas os times internos tem leituras conflitantes:
  - CS diz que satisfacao esta ok.
  - Produto diz que uso cresceu.
  - CEO quer entender o que esta acontecendo de verdade.

O objetivo e entregar uma solucao forte dentro de um timebox estimado de **4h**, com analise profunda, narrativa executiva e evidencia clara de uso de IA.

## Regras e Criterios do Challenge

Obrigatorio:

- Entregar tudo em `submissions/kadug/`.
- Incluir `README.md` seguindo o template oficial.
- Incluir `process-log/` com evidencia de uso de IA.
- Cruzar as 5 tabelas do dataset.
- Responder:
  1. O que esta causando o churn?
  2. Quais segmentos estao mais em risco?
  3. O que a empresa deveria fazer?
- Submeter via Pull Request.
- Nao modificar arquivos fora da pasta da submissao.

Criterios de qualidade:

- Insights verificaveis, com numeros.
- Recomendacoes acionaveis, nao genericas.
- Distincao entre correlacao e causalidade.
- Comunicacao clara para CEO e stakeholders nao tecnicos.
- Evidencia de iteracao com IA, nao apenas um prompt unico.

## Dados Disponiveis

Cinco CSVs conectados por `account_id` e `subscription_id`:

- `ravenstack_accounts.csv`: contas, industria, pais, canal, plano, trial.
- `ravenstack_subscriptions.csv`: MRR, ARR, plano, billing, upgrades/downgrades.
- `ravenstack_feature_usage.csv`: uso diario por feature, duracao, erros, beta.
- `ravenstack_support_tickets.csv`: tempo de resposta, resolucao, satisfacao, escalacoes.
- `ravenstack_churn_events.csv`: eventos de churn, reason code, refund, feedback textual.

## Direcionamento de Produto

Tese central:

```text
Dados cruzados
  -> sinais relevantes
  -> narrativas de negocio
  -> decisoes priorizadas
  -> acoes operacionais
```

Principios:

- Dados devem contar narrativas.
- Narrativas devem resultar em acoes.
- Acoes devem ser simples de entender e executar.
- Cada recomendacao deve ter evidencia, dono sugerido e impacto esperado.
- Medias gerais nao podem esconder segmentos criticos.
- Correlacao nao deve ser vendida como causalidade.

Stakeholders:

- CEO: causa raiz, impacto financeiro e decisoes prioritarias.
- Customer Success: contas em risco e playbooks de intervencao.
- Produto: features com friccao, erros ou baixa retencao.
- Suporte: relacao entre SLA, escalacoes, satisfacao e churn.
- Receita: planos, billing, downgrade e ARR em risco.

## Arquitetura Definida

A arquitetura escolhida foi:

```text
Analytics Core First + Presentation Adapters
```

Fluxo:

```text
CSV Kaggle
  -> validacao de schema
  -> analytics core
  -> datasets consolidados
  -> findings e recomendacoes
  -> exports auditaveis
  -> relatorio executivo
  -> dashboard minimo
```

Racional:

- A analise e a fonte da verdade.
- O dashboard nao deve conter a logica analitica principal.
- O dataset e pequeno; performance no browser nao e o maior risco.
- O maior risco e interpretar incorretamente churn, receita, suporte, uso e feedback.
- Exports simples tornam a solucao integravel a um futuro hub de ferramentas.

## Stack Proposta

Analytics core:

- Python.
- Pandas ou DuckDB.
- Scripts ou notebook versionado.
- Exports em CSV/JSON.

Relatorio:

- Markdown como fonte principal.
- PDF opcional.
- Graficos/tabelas exportados.

Dashboard minimo:

- Streamlit.
- Plotly ou componentes nativos do Streamlit.
- Logica analitica fora do dashboard.
- Entrada por exports estaticos gerados pela analise.

## Contratos de Export Planejados

- `account_health.csv/json`: uma linha por conta com receita, uso, suporte, churn, score e bucket de risco.
- `risk_segments.csv/json`: segmentos ordenados por risco, impacto, confianca, `segment_size` e `arr_at_risk`.
- `priority_accounts.csv/json`: contas especificas em risco com ARR/MRR e acao sugerida.
- `action_backlog.csv/json`: recomendacoes priorizadas por stakeholder.
- `executive_findings.json`: narrativas finais com evidencia, interpretacao e acao.
- `data_quality_report.md`: validacao de schema, joins e limitacoes.

## Escopo do Dashboard Minimo

O dashboard minimo deve mostrar:

- Top findings executivos.
- Segmentos em risco.
- Contas prioritarias.
- Backlog de acoes por stakeholder.

Ele deve consumir os exports prontos da analise. Se faltar tempo, cortar visual polish antes de cortar conteudo analitico.

## Plano de 4h

### 0:00-0:30 - Setup e contrato dos dados

- Baixar os 5 CSVs.
- Validar colunas, tipos, nulos, cardinalidade e chaves.
- Confirmar joins por `account_id` e `subscription_id`.
- Registrar anomalias no process log.

### 0:30-1:30 - Camada analitica

- Criar agregados por conta e assinatura.
- Separar churners vs. non-churners.
- Calcular metricas de MRR/ARR, uso, erros, tickets, satisfacao, upgrades/downgrades e motivos de churn.

### 1:30-2:30 - Findings e narrativas

- Comparar churners vs. non-churners.
- Testar contradicoes do briefing:
  - satisfacao media vs. segmentos criticos;
  - uso geral crescendo vs. uso ruim ou com friccao.
- Identificar segmentos e contas em risco.

### 2:30-3:20 - Relatorio executivo

- Escrever executive summary.
- Consolidar causa raiz, segmentos em risco, recomendacoes e limitacoes.
- Exportar tabelas/graficos.

### 3:20-4:00 - Dashboard minimo e empacotamento

- Construir dashboard Streamlit simples consumindo exports.
- Atualizar process log.
- Rodar checklist de submissao.

## Estrategia de Commits

Commits nao sao obrigatorios para provar tempo, mas serao usados como evidencia de processo.

Sequencia planejada:

1. `chore: scaffold challenge 001 submission`
2. `docs: define analytics-first architecture and delivery plan`
3. `analysis: validate churn dataset schema and joins`
4. `analysis: generate churn findings and risk segments`
5. `docs: write executive diagnosis and process log`
6. `feat: add minimal streamlit churn dashboard`

Observacao: o repositorio oficial ignora `submissions/` no `.gitignore`; sera necessario usar `git add -f submissions/kadug/...`.

## Decisoes Ja Tomadas

- O dashboard minimo sera entregue em Streamlit, mas nao sera a fonte da logica de negocio.
- A arquitetura principal sera analytics-first.
- Angular foi descartado para este timebox; Streamlit tem melhor custo-beneficio.
- O process log sera mantido desde o inicio.
- O relatorio executivo e as recomendacoes sao mais importantes que visual polish.

## Riscos Conhecidos

- Dataset externo pode exigir login no Kaggle.
- O tempo pode nao comportar analise profunda, relatorio e dashboard com alto acabamento.
- Um modelo preditivo pode parecer sofisticado, mas ser pouco confiavel sem validacao adequada.
- Feedback textual pode ter vies de resposta.
- Uso crescente pode mascarar uso ruim, erros ou uso concentrado em segmentos que nao churnam.
- Satisfacao media pode esconder segmentos de alto valor insatisfeitos.

## Perguntas para Critique

Avalie criticamente esta estrategia. Pontos desejados:

1. A arquitetura **Analytics Core First + Presentation Adapters** e a melhor para este challenge?
2. O dashboard minimo em Streamlit agrega valor suficiente ou deveria ser substituido por algo ainda mais simples?
3. Os contratos de export propostos sao suficientes para relatorio, dashboard e integracao futura?
4. O timebox de 4h esta realista?
5. Quais analises estatisticas ou cortes de dados sao indispensaveis para nao cair em insight generico?
6. Quais riscos de causalidade/correlacao precisam estar explicitamente tratados?
7. O que voce cortaria se o tempo apertar?
8. O que voce adicionaria para a entrega superar uma resposta baseline de IA?
9. O que um CEO esperaria ver nos primeiros 60 segundos de leitura?
10. O que faria essa submissao parecer operacional, nao apenas academica?

## Criterio de Sucesso

A entrega sera considerada forte se:

- cruzar as 5 tabelas;
- mostrar numeros verificaveis;
- contar uma historia clara sobre churn;
- apontar segmentos e contas especificas em risco;
- priorizar acoes concretas;
- separar evidencia de hipotese;
- mostrar como a IA foi usada e corrigida;
- entregar um dashboard minimo que facilite leitura operacional dos achados.
