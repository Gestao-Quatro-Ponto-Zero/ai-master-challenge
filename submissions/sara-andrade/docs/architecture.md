# Architecture — FastAPI Triage Service

## Por que FastAPI

Streamlit é útil para dashboard, mas o problema real é integração operacional. Um roteador de suporte precisa funcionar como serviço:

```text
plataforma de tickets → API de triagem → fila/automação/agente
```

FastAPI permite:

- contrato claro de entrada e saída;
- documentação Swagger automática;
- teste manual no navegador;
- integração futura com Zendesk/Intercom/Freshdesk;
- batch test sem interface.

## Endpoints

### `GET /health`

Verifica se a API está no ar.

### `GET /model-card`

Mostra performance do modelo, thresholds e guardrails.

### `GET /examples`

Retorna payloads de exemplo.

### `POST /triage`

Recebe:

```json
{
  "text": "Hi, I cannot access the finance dashboard after my role changed.",
  "priority": "Medium",
  "channel": "Internal portal",
  "source_context": "b2e_it"
}
```

Retorna:

```json
{
  "route": "AUTO_RESOLVE",
  "domain": "B2E_IT",
  "predicted_topic": "Access",
  "topic_confidence": 0.91,
  "rationale": ["..."],
  "suggested_action": "...",
  "suggested_reply": "..."
}
```

## Próximo passo de produção

- autenticação;
- logs estruturados;
- gravação de decisões;
- feedback do agente;
- integração com base de conhecimento;
- monitoramento de drift;
- retreinamento periódico.
