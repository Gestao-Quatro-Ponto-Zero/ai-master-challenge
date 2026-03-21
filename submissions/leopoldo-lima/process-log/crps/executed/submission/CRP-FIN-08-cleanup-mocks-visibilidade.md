# CRP-FIN-08 — Limpeza: reduzir visibilidade de mocks e legado

## Objetivo
Remover do pacote final o máximo possível de artefatos mockados, packs e legado que possam confundir o avaliador.

## Fazer
- localizar e classificar:
  - mocks ativos
  - mocks inativos
  - legado de UI anterior
  - packs auxiliares
  - artefatos de construção que não precisam entrar na submissão
- mover para área claramente isolada ou remover do pacote final

## Impacto na submissão
Reduz ruído, ambiguidade e risco de o avaliador achar que a solução principal ainda depende de demo data.

## Evidências obrigatórias
- inventário antes/depois
- lista do que foi removido/isolarado
- screenshot/árvore resumida do pacote final

## Atualizações obrigatórias de process log
Registrar:
- quais resíduos existiam
- decisão de remoção ou isolamento
- impacto no pacote final

## Definition of Done
- pacote final ficou mais limpo
- mocks não aparecem como caminho principal
- legado visível foi reduzido
