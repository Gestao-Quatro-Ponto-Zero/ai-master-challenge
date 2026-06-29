# Plano de Execucao - 4h

## Norte

Entregar um diagnostico de churn que um CEO consiga usar no dia seguinte. A prioridade e clareza acionavel, nao complexidade tecnica.

## Principios de Produto

- Dados devem contar narrativas.
- Narrativas devem resultar em acoes.
- Acoes devem ser simples de entender, priorizar e executar.
- Toda recomendacao deve ter evidencia, dono sugerido e impacto esperado.
- Correlacao nao deve ser vendida como causalidade.

## Timebox

### 0:00-0:20 - Setup e contrato dos dados

- Baixar os 5 CSVs do Kaggle.
- Validar nomes de colunas, tipos, nulos, cardinalidade e chaves.
- Confirmar join paths:
  - `accounts.account_id`
  - `subscriptions.subscription_id -> account_id`
  - `feature_usage.subscription_id`
  - `support_tickets.account_id`
  - `churn_events.account_id`
- Registrar anomalias no process log.
- Gerar `data_quality_report.md`.

### 0:20-1:30 - Camada analitica

- Criar tabelas agregadas por conta e por assinatura.
- Separar churners, active accounts e contas em risco.
- Calcular metricas:
  - MRR/ARR exposto a churn.
  - Uso por feature, erros e duracao.
  - Tickets, escalacoes, first response time, resolution time e satisfacao.
  - Upgrades, downgrades, plano, billing frequency e trial.
  - Reason codes e feedback textual.
- Calcular churn por ARR/MRR e `arr_at_risk`.
- Construir score de risco simples e auditavel.

### 1:30-2:30 - Findings e narrativas

- Comparar churners vs. non-churners.
- Rodar testes estatisticos simples quando aplicavel:
  - mediana por grupo;
  - p-value;
  - tamanho de efeito ou diferenca pratica.
- Buscar contradicoes do brief:
  - "Satisfacao esta ok" vs. experiencia real por segmento.
  - "Uso cresceu" vs. uso por feature, qualidade e segmento.
- Identificar segmentos de risco com contas especificas.
- Separar churn voluntario vs. involuntario se os reason codes permitirem.
- Criar watchlist de contas prioritarias.
- Priorizar narrativas por impacto financeiro e confianca.

### 2:30-3:20 - Entrega executiva

- Escrever executive summary.
- Montar secoes:
  - Causa raiz.
  - Segmentos em risco.
  - Acoes recomendadas.
  - Limitacoes.
- Exportar graficos/tabelas relevantes.

### 3:20-3:50 - Dashboard minimo Streamlit

- Construir dashboard minimo em Streamlit consumindo os exports da analise.
- Mostrar:
  - top findings executivos;
  - segmentos em risco;
  - watchlist de contas;
  - backlog de acoes por stakeholder.

### 3:50-4:00 - Empacotamento

- Atualizar process log com prompts, iteracoes e correcoes.
- Rodar checklist final de submissao.

## Criterios de Corte

Se faltar tempo, cortar nesta ordem:

1. Visual polish do dashboard.
2. Modelo preditivo sofisticado.
3. Analises secundarias sem acao clara.
4. Analise NLP sofisticada do feedback textual.
5. Export PDF.

Nao cortar:

1. Cruzamento das 5 tabelas.
2. Process log.
3. Executive summary.
4. Recomendacoes priorizadas.
5. Dashboard minimo com os principais achados.
6. ARR em risco.
7. Watchlist de contas especificas.
8. Nota de causalidade por finding.

## Definicao de Pronto

- A submissao esta em `submissions/kadug/`.
- O README segue o template oficial.
- Existe evidencia de processo em `process-log/`.
- A solucao mostra numeros verificaveis.
- Existe dashboard minimo ou justificativa explicita se ele for reduzido por tempo.
- Existe `data_quality_report.md`.
- Existem exports de `risk_segments`, `priority_accounts`, `action_backlog` e `executive_findings`.
- As recomendacoes sao acionaveis por stakeholders.
- Nenhum arquivo fora da pasta da submissao foi alterado antes do PR.
