# Classificador simples x LLM (zero-shot)

- Amostra: 200 tickets do conjunto de teste (nunca vistos pelo modelo simples)
- LLM: gemini-3.5-flash-lite, sem exemplos (zero-shot), 10 tickets por chamada
- Tickets respondidos pelo LLM: 200 de 200 (falhas: 0)

| | Modelo simples | LLM |
|---|---|---|
| Acerto (mesmos tickets) | 92.5% | 48.0% |
| Tempo para classificar a amostra | 0.01 s | 183 s (inclui pausas do limite gratuito) |
| Custo estimado por 1.000 tickets | ~US$ 0 (roda local) | ~US$ 0.063 |

- Os dois concordam em 48.0% dos tickets.
- Tokens: 15.107 de entrada e 3.196 de saída.
- Preço usado: US$ 0.3 (entrada) e US$ 2.5 (saída) por 1 milhão de tokens. Confira a tabela atual do Google; no plano gratuito o custo é zero, com limite de uso.
- Acerto do modelo simples na amostra inteira: 92.5%