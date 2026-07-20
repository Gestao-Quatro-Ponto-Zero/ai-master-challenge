# Data Health — Fase 3

## 1. Cobertura

Cobertura analítica: **39.14%** (13,927/35,586). Há eventos utilizáveis para 500 contas.

## 2. Validade

Eventos `VALID`: **10,703**. A população estrita cobre 30.08% dos eventos gerados.

## 3. Warnings

Eventos `VALID_WITH_WARNING`: **3,224**, equivalentes a 23.15% da população utilizável. 4,992 episódios têm warning.

## 4. Quarentena

Eventos em quarentena: **21,659** (60.86%); 500 contas são afetadas. Eles não entram em métricas de negócio.

## 5. Impacto analítico

A cobertura reduz especialmente evidência de uso e suporte. A sobreposição atinge 99.84% dos episódios e impede atribuição simples de churn ou MRR.

## 6. População estrita e ampliada

O arquivo `sensitivity_analysis.json` recalcula métricas em `VALID` e `VALID + VALID_WITH_WARNING`. Resultados `UNSTABLE` não foram promovidos.

## 7. Recomendações de governança

Corrigir cronologias na origem, versionar regras de promoção da quarentena, monitorar cobertura por evento/período/conta e validar a semântica de múltiplas assinaturas.
