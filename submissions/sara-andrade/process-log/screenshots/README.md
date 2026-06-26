# Screenshots — Evidências do Protótipo e Validação

Esta pasta contém evidências visuais de que o protótipo foi executado localmente e testado em diferentes cenários de triagem.

A narrativa principal do uso de IA está em `process-log.md`. Estes prints complementam o process log mostrando o protótipo rodando, os guardrails funcionando e o teste em lote executado.

## Arquivos

| Arquivo | O que demonstra |
|---|---|
| `00_fastapi_docs_home.png` | Tela inicial do Swagger/FastAPI com os endpoints disponíveis: `/health`, `/model-card`, `/triage` e `/examples`. |
| `01_auto_resolve_password_reset.png` | Caso B2E/IT simples de reset de senha retornando `AUTO_RESOLVE`, com categoria `Access` e alta confiança. |
| `02_agent_assist_b2c_product_help.png` | Caso B2C externo sem risco alto retornando `AGENT_ASSIST`, demonstrando que o sistema não aplica o classificador de IT em domínio B2C. |
| `03_human_escalation_refund_angry.png` | Caso B2C com reembolso e linguagem emocional negativa retornando `HUMAN_ESCALATION`, validando os guardrails de risco. |
| `04_batch_test_distribution.png` | Execução de `python3 test_batch.py`, mostrando a distribuição em lote entre `AUTO_RESOLVE`, `AGENT_ASSIST` e `HUMAN_ESCALATION`. |
| `05_model_card.png` | Endpoint `/model-card`, mostrando modelo selecionado, baseline, métrica, confidence gate e guardrails. |


## Como estes prints conectam com a proposta

Os screenshots demonstram a política central da solução:

- **AUTO_RESOLVE** para tickets internos/IT, simples, com alta confiança e baixo risco.
- **AGENT_ASSIST** para tickets externos/B2C ou casos em que a IA deve apoiar o agente sem responder automaticamente.
- **HUMAN_ESCALATION** para casos críticos, financeiros, emocionais ou ambíguos.

Essa evidência evita cherry-picking porque inclui tanto testes manuais no Swagger quanto execução em lote via `test_batch.py`.