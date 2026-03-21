# CRP-D10 — Runbook de dados e evidência para submissão

## Objetivo
Mostrar controle sobre o dataset e deixar o avaliador rodar sem tropeço.

## Tarefas
- documentar onde os CSVs ficam
- como validar
- como gerar camada core/gold
- como reproduzir score
- como interpretar warnings

## Saídas
- `docs/RUNBOOK_DATA.md`
- `artifacts/data-validation/`
- atualização de `PROCESS_LOG.md`

## Definition of Done
- avaliador consegue rodar ingestão e validação
- existe evidência material de qualidade dos dados
- limitações do dataset estão escritas com honestidade

## Prompt para o Cursor
```text
Implemente o CRP-D10: runbook operacional dos dados.

Tarefa:
1. Criar docs/RUNBOOK_DATA.md com:
   - localização esperada dos CSVs
   - comandos para ingestão
   - comandos para validação
   - geração de modelos core/gold
   - troubleshooting
2. Salvar artefatos simples de evidência em artifacts/data-validation/.
3. Atualizar PROCESS_LOG.md e LOG.md.

Critérios:
- Runbook direto e executável
- Sem suposições mágicas
- Mostrar limitações reais do dataset
```
