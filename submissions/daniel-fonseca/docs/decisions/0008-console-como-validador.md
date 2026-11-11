# 0008 — Console operacional como validador da solução

- **Status:** Aceita
- **Data:** 2026-11-09
- **Origem:** IA (sugestão) · Daniel (enquadramento)

## Decisão
O app tem duas áreas com papéis diferentes:
- **Dashboard** — responde ao diagnóstico (questão 1).
- **Console operacional** — **valida a proposta de automação** (questões 2 e 3): recebe um ticket (digitado ou sorteado do holdout do DS2), mostra categoria, confiança, casos similares, nível decidido, resposta/rascunho/alerta, a fila de revisão humana e a caixa de mensagens (ADR-0007).

O console não é "mais um gráfico": é a prova de que o fluxo roda com dados reais, não com 3 exemplos escolhidos a dedo.
