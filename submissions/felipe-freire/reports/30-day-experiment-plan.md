# Plano operacional de 30 dias

## Objetivo

Produzir evidência incremental suficiente para decidir conteúdo e patrocínio sem transformar as diferenças artificiais do dataset em regras de negócio. Nenhum investimento é escalado antes da aprovação humana de métrica primária, MDE, break-even, orçamento e guardrails.

## Preparação — dias 1 a 5

| Entrega | Owner | Critério de conclusão |
|---|---|---|
| Definir objetivo e métrica primária | Head de Marketing + Analytics | uma métrica por teste, fórmula e janela documentadas |
| Instrumentar custos e outcomes | Marketing Ops + Data | `campaign_id`, custos, reach único, cliques, conversões e margem disponíveis |
| Aprovar MDE e break-even | Finance + Analytics | limite mínimo de efeito e custo incremental aprovados |
| Congelar hipóteses e segmentos | Social Lead | hipóteses registradas antes de observar resultados |
| Validar qualidade | Data | schema, missingness, duplicidades e reconciliação aprovados |

## Experimentos — dias 6 a 23

| ID | Pergunta | Desenho mínimo | KPI primário | Guardrail | Condição de parada |
|---|---|---|---|---|---|
| EXP-01 | Patrocínio gera valor incremental? | posts/creators elegíveis randomizados entre patrocinado e controle, com mesma janela | margem incremental por exposição elegível | custo por conversão e frequência | interromper por dano no guardrail ou inviabilidade do MDE |
| EXP-02 | Qual proposta de conteúdo melhora compartilhamento? | duas propostas criativas comparadas dentro de plataforma e faixa de creator | share rate incremental | comentários negativos e unfollow rate | parar variante prejudicial; não escolher vencedor antes do `n` planejado |
| EXP-03 | Cadência adicional gera alcance incremental? | rollout escalonado por unidades comparáveis | reach único incremental por semana | saturação/frequência e produção | interromper se o ganho marginal ficar abaixo do custo aprovado |

O Statistician define tamanho amostral somente depois que o Head aprovar métrica, baseline e MDE. “Significativo” sem relevância econômica não autoriza escala.

## Rotina semanal

| Quando | Reunião/ação | Saída |
|---|---|---|
| Segunda | qualidade e exposição | populações elegíveis, desvios e exclusões justificadas |
| Quarta | monitoramento cego de guardrails | segurança operacional sem declarar vencedor antecipadamente |
| Sexta | status executivo | execução, custos, `n`, incidentes e decisões pendentes |

## Decisão — dias 24 a 30

Cada teste termina em uma das quatro decisões:

- **Escalar:** limite inferior do efeito incremental supera o break-even e guardrails passam.
- **Replicar:** sinal promissor, mas incerteza ou validade externa ainda insuficiente.
- **Iterar:** execução ou instrumentação impediu resposta confiável.
- **Parar:** efeito incompatível com o MDE, dano em guardrail ou retorno abaixo do break-even.

O relatório final deve registrar efeito, intervalo, população, custo, limitações e decisão. Rankings exploratórios e segmentos encontrados depois do resultado geram novas hipóteses; nunca justificam retrospectivamente o investimento.
