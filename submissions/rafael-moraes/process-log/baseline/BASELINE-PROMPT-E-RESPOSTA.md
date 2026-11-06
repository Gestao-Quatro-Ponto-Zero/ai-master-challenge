# Teste de baseline — 2026-11-06 ~15:15

Chat novo do Claude, fora do projeto. Anexos: briefing-challenge-002.md + dataset1-customer_support_tickets.csv.

**Pedido exato:** "Leia o briefing e faça o diagnóstico operacional pedido no item 1, usando o CSV anexo."

**Resposta (resumo colado pelo Rafael):**
- Detectou: timestamps em janela de 27h, 49% resolução antes da 1ª resposta, CSAT uniforme, 8.469 tickets (não 30 mil).
- "Sustentado": backlog 33% sem resposta / 34% esperando cliente; prioridade sem efeito (Critical ≈ Low em tempo); satisfação sem explicação (modelo = sorteio).
- "Ruído": piores combinações 11,4h vs 4,8h, p=0,17 em permutação.
- Desperdício: ~4.470 h/ano (2,5 FTE, ~R$ 201 mil/ano), faixa 2.735–6.536 h; R$ 35–60/h e minutos por etapa = "premissas minhas".
- Código gerado: diagnostico_baseline.py
