# ADR-002: Agno como framework do agente de diagnóstico

**Status:** Aceito
**Data:** 2026-03-11

## Contexto

O agente de diagnóstico precisa: (1) consultar dados do gold layer, (2) consultar o playbook de CS, (3) analisar padrões históricos, e (4) responder em linguagem natural via chat no dashboard. Precisamos de um framework que gerencie o loop de raciocínio e as chamadas a ferramentas de forma estruturada.

## Decisão

Usar o framework **Agno** com **Claude (claude-sonnet-4-6)** como LLM subjacente.

## Motivação

- Agno permite definir tools tipadas em Python que o agente invoca de forma controlada
- Integração nativa com a Anthropic API
- Suporte a memória de sessão (contexto da conversa no dashboard)
- Facilita o padrão RAG simples: tool de busca no playbook de CS (leitura de Markdown)

## Tools previstas para o agente

| Tool | O que faz |
|------|-----------|
| `query_risk_accounts` | Retorna contas com risk_score acima de threshold do `gold_account_risk` |
| `query_churn_drivers` | Retorna drivers de churn por segmento/período do `gold_churn_drivers` |
| `query_dashboard_fact` | Executa queries analíticas no `gold_dashboard_fact` |
| `lookup_cs_playbook` | Busca a estratégia de CS correspondente a uma categoria de problema no playbook |
| `detect_anomaly` | Compara métricas do período atual com média histórica e sinaliza desvios |

## Consequências

- O agente nunca acessa os dados silver ou bronze diretamente
- Toda sugestão de ação deve passar pela tool `lookup_cs_playbook` — sem recomendações fora do playbook
- O playbook (`docs/02-product/04-playbook-cs.md`) é lido em tempo de execução (não embedado no prompt)
