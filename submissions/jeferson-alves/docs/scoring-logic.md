# Scoring Logic

## Objetivo

Gerar uma priorizacao que um vendedor consiga usar imediatamente, com transparencia suficiente para confiar no score.

## Formula

O score final e uma estimativa de win rate convertida para escala de 0 a 100.

Componentes usados:

- Stage: 26%
- Sales agent historical win rate: 18%
- Account historical win rate: 14%
- Product historical win rate: 12%
- Manager historical win rate: 10%
- Regional office historical win rate: 8%
- Freshness do deal: 7%
- Potencial financeiro: 5%

## Como cada sinal entra

### Stage

- `Engaging` recebe prior maior que `Prospecting`.
- Isso representa maturidade comercial, nao apenas historico numerico.

### Historical win rates

As taxas por vendedor, conta, produto, manager e regiao usam smoothing bayesiano. Isso evita supervalorizar grupos com poucos exemplos.

## Freshness

- Deals mais recentes recebem score melhor.
- Deals envelhecidos perdem prioridade, especialmente quando ja deveriam ter avancado.
- Quando o deal nao tem `engage_date`, a feature recebe valor neutro-baixo em vez de quebrar o score.

## Potencial financeiro

- O valor nao define a fila sozinho.
- Ele entra apenas como desempate inteligente.
- Para deal aberto sem valor negociado, uso `sales_price` como proxy.

## Decisões de modelagem

- Nao usei modelo supervisionado pesado porque o desafio pedia algo funcional e explicavel em poucas horas.
- Preferi uma abordagem robusta e auditavel, adequada para uma primeira versao de operacao.
