# CRP-UX-01 — Parar de demonstrar demo rows na vitrine principal

## Objetivo
Fazer a UI principal refletir o dataset real do challenge, e não linhas sintéticas ou artefatos de `demo-opportunities`.

## Problema
Hoje a vitrine principal ainda tem cheiro de demo:
- poucos registros
- IDs sintéticos
- títulos genéricos
- sem ligação convincente com `sales_pipeline.csv`

Isso enfraquece diretamente o requisito: **precisa usar os dados reais do dataset**.

## Escopo
- ranking principal
- detalhe da oportunidade
- KPIs
- filtros

## Tarefas
1. Identificar o caminho atual de alimentação do runtime principal.
2. Trocar a fonte principal para a trilha real derivada de:
   - `sales_pipeline.csv`
   - `accounts.csv`
   - `products.csv`
   - `sales_teams.csv`
3. Manter demo data apenas em testes isolados ou fallback explícito.
4. Remover ambiguidades na UI e no README sobre qual fonte está em uso.
5. Garantir que a seleção da oportunidade na UI venha do fluxo real.

## Impacto na Submissão
- Fortalece a solução funcional.
- Fecha o requisito mínimo de uso dos dados reais.
- Evita sensação de protótipo fake.

## Evidências obrigatórias
- screenshot da tela principal com dados reais
- diff da troca de fonte de dados
- evidência de execução do fluxo real
- nota humana explicando como foi confirmado que a fonte principal deixou de ser demo

## Atualizações obrigatórias de process log
Registrar:
- como a fonte demo foi identificada
- qual trilha real foi adotada
- quais arquivos foram alterados
- erro original e correção
- evidências geradas

## Atualizações obrigatórias de README/Submission
- atualizar README para explicitar que o runtime principal usa o dataset oficial
- remover qualquer mensagem que sugira que o produto principal roda em dados sintéticos

## Definition of Done
- ranking principal usando dados reais
- detalhe usando dados reais
- KPIs usando dados reais
- filtros usando dados reais
- `PROCESS_LOG.md` atualizado
- evidências salvas
- README atualizado quando aplicável
- verificação humana explícita realizada
