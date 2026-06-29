# Sintese dos Critiques Externos

## Fontes

- Sonnet Max: `C:\Users\kadug\Downloads\critique-spec-churn.md`
- Opus 4.6 Max: `C:\Users\kadug\Downloads\critique-spec-opus.antgvy.md`

## Veredicto Consolidado

A estrategia esta correta na base: **Analytics Core First + Presentation Adapters**. A principal correcao e trocar o dashboard Angular por Streamlit para reduzir risco de tempo e manter toda a entrega analitica em Python.

## Decisoes Aceitas

1. Manter analytics core como fonte da verdade.
2. Usar Streamlit para dashboard minimo.
3. Tratar exports como contrato auditavel.
4. Adicionar `arr_at_risk` e `segment_size` em segmentos de risco.
5. Criar `priority_accounts` com contas especificas, ARR/MRR, sinais e acao sugerida.
6. Criar `data_quality_report.md` antes dos findings.
7. Incluir nota de causalidade em cada insight.
8. Separar churn voluntario vs. involuntario quando os dados permitirem.
9. Comparar churners vs. non-churners com mediana, diferenca pratica e teste estatistico simples.
10. Usar uma pagina executiva com conclusao primeiro e metodologia depois.

## Decisoes Rejeitadas ou Rebaixadas

- Angular nao sera usado neste challenge. E bom para produto futuro, mas caro demais para o timebox.
- Web Worker saiu do escopo.
- Modelo preditivo complexo saiu do escopo inicial.
- NLP sofisticado no feedback textual sera opcional.
- PDF export sera opcional.

## Analises Obrigatorias Atualizadas

- Churn por quantidade de contas e por ARR/MRR.
- `arr_at_risk` por segmento.
- Satisfacao geral vs. satisfacao dos churners e por segmento.
- Uso agregado vs. uso por segmento e por qualidade de uso.
- Tickets por tipo, escalacao, tempo de resposta, resolucao e satisfacao.
- Downgrade antes do churn.
- Segmentacao cruzada por plano, industria, canal e tenure.
- Churn voluntario vs. involuntario quando possivel.
- Watchlist de contas em risco.

## Entregaveis Atualizados

- `data_quality_report.md`
- `account_health.csv/json`
- `risk_segments.csv/json`
- `priority_accounts.csv/json`
- `action_backlog.csv/json`
- `executive_findings.json`
- Relatorio executivo em Markdown
- Dashboard minimo em Streamlit
- Process log com iteracoes de IA e correcoes

## Nova Regra de Corte

Se o tempo apertar, cortar nesta ordem:

1. Visual polish do dashboard.
2. PDF export.
3. NLP sofisticado.
4. Survival analysis.
5. Modelo preditivo.

Nao cortar:

1. Cruzamento das 5 tabelas.
2. ARR em risco.
3. Watchlist de contas.
4. Executive summary.
5. Process log.
6. Notas de causalidade.

## Decisao Final

Seguir com:

```text
Python/Pandas ou DuckDB
  -> exports auditaveis
  -> relatorio executivo
  -> Streamlit dashboard
```

Essa arquitetura tem o melhor custo-beneficio para vencer o challenge: analise rastreavel, narrativa acionavel, dashboard suficiente e baixo risco de estourar o timebox.
