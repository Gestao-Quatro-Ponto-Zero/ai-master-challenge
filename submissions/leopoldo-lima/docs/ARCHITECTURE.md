# ARCHITECTURE

## Visão geral
A arquitetura deste repositório é centrada em governança de execução por CRPs e produção de evidência para submissão.

## Camadas principais
1. **Planejamento e execução**
   - `crps/executed/` + `indexes/` (governança CRP) e, em `legacy/`, pacotes `focus-score-*` importados como referência (ver `docs/REPO_SHAPE.md`)
   - define objetivo, entregáveis, DoD e encerramento por CRP

2. **Rastreabilidade**
   - `PROCESS_LOG.md`
   - `LOG.md`
   - `artifacts/process-log/`

3. **Estratégia de submissão**
   - `docs/SUBMISSION_STRATEGY.md`
   - `docs/PROCESS_LOG_GUIDE.md`
   - `docs/CRP_GOVERNANCE.md`
   - `docs/README_SUBMISSION_SKELETON.md`

## Fluxo operacional
1. selecionar CRP
2. executar tarefas do CRP
3. gerar evidências
4. atualizar process log
5. revisar com julgamento humano
6. encerrar com commit e PR

## Princípios arquiteturais
- incrementalismo (`1 CRP = 1 PR pequeno`)
- verificabilidade (sem evidência, sem conclusão)
- rastreabilidade de IA (uso, erro, correção, iteração)
- aderência ao guia de submissão

## Restrições
- evitar suposições sobre componentes inexistentes
- manter documentação sincronizada com o estado real do disco
- priorizar clareza para avaliação externa
