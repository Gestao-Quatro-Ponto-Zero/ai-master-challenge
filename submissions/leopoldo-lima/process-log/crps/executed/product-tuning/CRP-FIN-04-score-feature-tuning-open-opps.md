# CRP-FIN-04 — Recalibrar score: features úteis para open pipeline

## Objetivo
Enriquecer o score com sinais mais úteis para operação comercial, em vez de depender demais de estágio e valor.

## Fazer
- revisar e fortalecer peso de sinais como:
  - recência/idade no pipeline
  - completude do cadastro
  - porte da conta
  - série/produto
  - região/gestor, se fizer sentido
- introduzir penalidade explícita para oportunidade aberta sem sinais mínimos de ação
- documentar trade-offs

## Impacto na submissão
Aumenta a credibilidade do score e reduz o risco de parecer ranking arbitrário.

## Evidências obrigatórias
- tabela simples com features/pesos antes e depois
- exemplos de 3 oportunidades abertas explicando por que subiram ou caíram
- atualização de docs de score

## Atualizações obrigatórias de process log
Registrar:
- quais sinais foram reavaliados
- o que a IA sugeriu
- o que foi aceito, rejeitado e por quê

## Definition of Done
- score usa sinais mais úteis para pipeline aberto
- documentação foi atualizada
- há exemplos concretos de impacto
