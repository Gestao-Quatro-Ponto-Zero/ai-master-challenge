# CRP-REAL-04 — Enriquecer o scoring com features reais do dataset

## Objetivo
Evoluir o scoring além de regras muito básicas, usando features já disponíveis no projeto e no dataset.

## Problema que resolve
O score atual atende o mínimo, mas ainda parece simples demais frente ao potencial do dataset.

## Tarefas
1. Revisar o scoring atual e documentar suas limitações.
2. Incorporar features adicionais como:
   - `days_since_engage`
   - `stage_rank`
   - `account_revenue_band`
   - `employee_band`
   - `product_series`
   - `regional_office`
   - `manager_name`
   - qualidade/completude dos dados
3. Manter explainability explícita.
4. Externalizar pesos/configuração quando fizer sentido.
5. Atualizar a documentação do score e suas limitações.

## Entregáveis
- motor de score enriquecido
- `docs/SCORING_V2.md`
- atualização de `LOG.md`
- atualização de `PROCESS_LOG.md`

## Impacto na Submissão
- melhora a substância analítica da solução
- mostra uso estratégico do dataset, não apenas ordenação superficial

## Evidências obrigatórias
- diff dos pesos/regras
- tabela antes/depois de top prioridades
- exemplo de oportunidade com explicação enriquecida
- testes cobrindo novas features

## Atualizações obrigatórias de process log
- registrar hipótese de novas features
- erros de modelagem sugeridos pela IA
- decisões humanas sobre o que entrou e o que ficou fora

## Atualizações obrigatórias de README/Submission
- atualizar seção de lógica/priorização
- descrever de forma honesta o racional do score

## Definition of Done
- score usa múltiplos sinais do dataset real
- explainability continua legível
- testes passam
- README, LOG e PROCESS_LOG atualizados
