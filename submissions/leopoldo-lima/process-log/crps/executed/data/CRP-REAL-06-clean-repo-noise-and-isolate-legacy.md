# CRP-REAL-06 — Limpar ruído do repositório e isolar legado/protótipos

## Objetivo
Reduzir o ruído do repositório para que o avaliador encontre claramente a solução final.

## Problema que resolve
Artefatos residuais e protótipos paralelos confundem a leitura arquitetural e enfraquecem a submissão.

## Tarefas
1. Identificar pastas, apps e artefatos que não fazem parte da solução final.
2. Decidir entre:
   - remover
   - mover para `legacy/`
   - documentar como protótipo importado
3. Garantir que o caminho principal de solução esteja evidente na raiz.
4. Atualizar links, docs e scripts para refletir essa limpeza.

## Entregáveis
- repositório limpo ou legado isolado
- `docs/REPO_SHAPE.md`
- atualização de `LOG.md`
- atualização de `PROCESS_LOG.md`

## Impacto na Submissão
- reduz confusão do avaliador
- melhora percepção de código limpo e solução coesa

## Evidências obrigatórias
- árvore de pastas antes/depois
- lista do que foi removido ou movido
- justificativa humana para cada bloco isolado

## Atualizações obrigatórias de process log
- registrar critérios de corte
- anotar onde a IA quis apagar demais ou preservar demais
- explicar decisões humanas

## Atualizações obrigatórias de README/Submission
- refletir a nova topologia do repositório

## Definition of Done
- solução final está fácil de localizar
- ruído residual está removido ou explicitamente isolado
- docs, LOG e PROCESS_LOG atualizados
