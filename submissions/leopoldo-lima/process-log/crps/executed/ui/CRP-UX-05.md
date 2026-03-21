# CRP-UX-05 — Alinhar nomenclatura ao challenge e ao dataset real

## Objetivo
Eliminar mistura de idioma e semântica confusa.

## Problema
Quando a UI mistura:
- português e inglês sem critério
- `status` genérico com `deal_stage`
- labels técnicas com labels de negócio

a solução perde clareza e parece remendo.

## Tarefas
1. Levantar todos os labels críticos da UI.
2. Padronizar nomenclatura conforme:
   - dataset real
   - challenge
   - idioma escolhido para a submissão
3. Garantir consistência em:
   - stages
   - score band
   - filtros
   - detalhes
4. Atualizar glossário ou mapeamento de labels.

## Impacto na Submissão
- Melhora comunicação para técnico e não técnico.
- Reduz ruído na avaliação.

## Evidências obrigatórias
- tabela de antes/depois dos labels
- screenshot final da tela padronizada
- diff dos componentes/formatters
- nota humana sobre convenção adotada

## Atualizações obrigatórias de process log
Registrar:
- inconsistências encontradas
- convenção final escolhida
- pontos de conflito entre dataset e UX
- correções aplicadas

## Atualizações obrigatórias de README/Submission
- alinhar screenshots, descrições e termos do README à nomenclatura final

## Definition of Done
- labels consistentes
- stages consistentes
- nada de semântica híbrida confusa
- `PROCESS_LOG.md` atualizado
- evidências salvas
- README atualizado quando aplicável
- verificação humana explícita realizada
