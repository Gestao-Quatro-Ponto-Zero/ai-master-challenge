# CRP-008 — Quality gates, segurança e dependências

## Objetivo
Implantar disciplina automatizada no repositório.

## Entregáveis
- lint/format/typecheck
- scans de dependências
- pre-commit ou equivalente
- `docs/QUALITY_GATES.md`

## Tarefas
1. Configurar lint, format e typecheck
2. Configurar hooks locais
3. Adicionar scan de vulnerabilidades
4. Gerar SBOM quando viável
5. Avaliar checagem de licenças

## Critérios de aceite
- Ferramentas estáveis
- Comandos executáveis
- Sem toolchain inflada à toa

## DoD
- quality gates documentados
- hooks locais prontos
- LOG.md atualizado
