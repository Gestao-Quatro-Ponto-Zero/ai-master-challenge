# CRP-UX-04 — Enriquecer a tabela de ranking com contexto de negócio

## Objetivo
Fazer o ranking responder claramente: “onde devo focar hoje?”

## Problema
A tabela atual mostra pouco contexto e pouca ação.

## Tarefas
1. Revisar colunas/células para incluir contexto útil:
   - account
   - produto
   - vendedor
   - manager
   - região
   - estágio
   - valor
   - score
   - banda
   - próxima ação resumida
2. Destacar visualmente a melhor oportunidade.
3. Tornar ordenação por score inequívoca.
4. Melhorar feedback de seleção da linha.

## Impacto na Submissão
- Reforça a natureza operacional do produto.
- Eleva utilidade percebida para o vendedor.

## Evidências obrigatórias
- screenshot do ranking enriquecido
- diff da tabela/listagem
- evidência de dados reais sendo exibidos
- nota humana explicando por que as colunas escolhidas ajudam decisão

## Atualizações obrigatórias de process log
Registrar:
- quais colunas existiam
- quais foram adicionadas/removidas
- por que cada campo ajuda decisão
- iterações de legibilidade

## Atualizações obrigatórias de README/Submission
- atualizar screenshots do ranking
- atualizar descrição dos dados exibidos

## Definition of Done
- ranking com contexto de negócio suficiente
- score e banda visíveis
- próxima ação presente no ranking
- linha prioritária destacada
- `PROCESS_LOG.md` atualizado
- evidências salvas
- README atualizado quando aplicável
- verificação humana explícita realizada
