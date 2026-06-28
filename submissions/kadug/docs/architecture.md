# Arquitetura da Solucao

## Objetivo Arquitetural

Construir uma solucao pequena, reproduzivel e facil de integrar a um hub de ferramentas. A arquitetura deve servir a decisao de negocio: transformar dados dispersos em narrativas acionaveis sobre churn.

A decisao atual e adotar uma arquitetura **Analytics Core First + Presentation Adapters**. A analise e a fonte da verdade; dashboard, relatorio e exports sao camadas de apresentacao consumindo os mesmos artefatos.

Depois dos critiques externos, a decisao foi refinada: o dashboard minimo sera feito em **Streamlit**, nao em Angular. Angular continua sendo uma opcao futura para produto, mas tem custo alto demais para o timebox do challenge.

```text
CSV Kaggle
  -> analytics core
  -> datasets consolidados
  -> findings e recomendacoes
  -> relatorio executivo
  -> dashboard minimo
```

## Stack Proposta

### Analytics Core

- Python para leitura, validacao e transformacao dos CSVs.
- Pandas ou DuckDB para agregacoes e joins.
- Jupyter ou scripts versionados para reproducibilidade.
- Exportacao de artefatos em CSV/JSON para consumo por dashboard e relatorio.
- Regras analiticas fora do front-end.

### Presentation Adapters

- Markdown/PDF para o relatorio executivo.
- CSV/JSON para integracao e auditoria.
- Dashboard minimo para leitura operacional dos principais achados.

### Dashboard minimo

- Streamlit em Python.
- Plotly ou componentes nativos do Streamlit para graficos e tabelas.
- Zero duplicacao de joins, regras de risco ou calculos principais.
- Componentes simples para:
  - Visao executiva.
  - Segmentos em risco.
  - Lista de contas prioritarias.
  - Evidencias por narrativa.
- Acoes recomendadas por stakeholder.
- Integracao futura com hub de ferramentas via arquivos JSON ou endpoint REST.

### Relatorio

- Markdown como fonte principal.
- Export opcional para PDF.
- Graficos exportados como imagens ou tabelas.

## Por que Streamlit neste Challenge

Angular e adequado para um produto operacional futuro, mas nao deve ser usado agora. O dataset e pequeno e o risco maior nao e performance no browser; e interpretar corretamente churn, receita, suporte, uso e feedback.

Streamlit mantem a stack em Python, consome Pandas diretamente, reduz setup e entrega interatividade suficiente para demonstrar os achados. O tempo economizado deve ir para profundidade analitica, narrativa executiva e process log.

## Decisao Pragmatica

O dashboard minimo passa a ser parte da entrega planejada, mas nao pode competir com a qualidade da analise. Em 4h, a ordem correta e:

1. Analise correta.
2. Narrativa executiva.
3. Process log completo.
4. Dashboard Streamlit consumindo exports prontos.

Se a camada analitica nao estiver solida, o dashboard deve ser reduzido ao essencial: resumo executivo, top segmentos, top contas e acoes.

## Fluxo de Dados

```text
Kaggle CSVs
  -> validacao de schema
  -> joins por account_id/subscription_id
  -> features analiticas por conta
  -> exports canonicos
  -> findings e segmentos
  -> relatorio executivo
  -> dashboard minimo
```

## Contrato de Dados

### Entidades

- Account: empresa cliente, plano, industria, pais, canal e trial.
- Subscription: receita, plano, billing, upgrades e downgrades.
- Feature usage: intensidade, duracao, erros e beta usage.
- Support ticket: SLA, satisfacao, escalacoes e resolucao.
- Churn event: motivo, refund e feedback textual.

### Camadas Derivadas

- `account_health`: consolidado por conta.
- `subscription_health`: consolidado por assinatura.
- `feature_quality`: uso, erros e adocao por feature.
- `support_friction`: friccao operacional por conta.
- `risk_segments`: segmentos com maior exposicao de churn.
- `action_backlog`: recomendacoes priorizadas.
- `executive_findings`: narrativas finais com evidencia, interpretacao e acao.
- `priority_accounts`: watchlist de contas em risco com ARR e acao sugerida.
- `churn_timeline`: eventos relevantes na jornada ate churn, quando houver dados temporais suficientes.
- `data_quality_report`: schema, joins, nulos, anomalias e limites do dataset.

## Contratos de Export

Os exports devem permitir auditoria e reuso:

- `account_health.csv/json`: uma linha por conta, com receita, uso, suporte, churn, risk score, bucket de risco e dias desde ultima atividade.
- `risk_segments.csv/json`: segmentos ordenados por risco, impacto e confianca, incluindo `segment_size` e `arr_at_risk`.
- `priority_accounts.csv/json`: top contas em risco, com account_id, MRR/ARR, principais sinais e acao recomendada.
- `action_backlog.csv/json`: recomendacoes priorizadas por stakeholder.
- `executive_findings.json`: narrativas prontas para relatorio e dashboard, com `confidence_level` e `evidence_strength`.
- `churn_timeline.csv/json`: timeline de eventos por conta quando houver dados temporais suficientes.
- `data_quality_report.md`: validacao de schema, joins e limitacoes.

Esses contratos deixam a ferramenta integravel sem depender da stack do hub.

## Modelo de Narrativa

Cada insight deve seguir o formato:

```text
Sinal observado:
Evidencia:
Interpretacao:
Risco de falsa causalidade:
Nota de causalidade:
Acao recomendada:
Dono sugerido:
Impacto esperado:
```

## Analises Obrigatorias

- Churn por ARR/MRR, nao apenas por quantidade de contas.
- Churn voluntario vs. involuntario, se o dataset permitir via `reason_code`; se nao permitir, registrar como limitacao.
- Churners vs. non-churners com mediana, diferenca pratica e teste estatistico simples quando aplicavel.
- Satisfacao desagregada por segmento e janela pre-churn.
- Uso agregado vs. uso por segmento, para testar a frase "uso cresceu".
- Tickets por tipo, escalacao, resolucao e satisfacao, nao apenas volume.
- Downgrade pre-churn como possivel sinal de intencao.
- Segmentacao cruzada por plano, industria, canal e tenure.
- Watchlist de contas especificas em risco com ARR e acao.

## Stakeholders

- CEO: causa raiz, impacto financeiro e decisoes prioritarias.
- Customer Success: contas em risco e playbooks de intervencao.
- Produto: features com friccao, erros e baixa retencao.
- Receita: planos, billing, downgrade e ARR em risco.
- Suporte: SLAs, escalacoes e relacao com churn.

## Riscos

- Dataset externo pode exigir login Kaggle.
- A correlacao entre uso e churn pode esconder qualidade ruim de uso.
- Feedback textual pode ser enviesado por quem decidiu responder.
- Modelo preditivo sem validacao pode parecer sofisticado e ser pouco confiavel.
- Churn involuntario pode distorcer a narrativa se nao for separado.
- Medias gerais podem esconder segmentos pequenos com alto ARR em risco.

## Guardrails

- Nao concluir causalidade sem evidencia forte.
- Nao agregar tudo sem preservar segmento e valor financeiro.
- Nao esconder contas especificas atras de medias.
- Nao entregar recomendacao generica como "melhorar suporte".
- Nao priorizar dashboard sobre executive summary, ARR em risco e watchlist.
