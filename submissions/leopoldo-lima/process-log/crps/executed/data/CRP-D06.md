# CRP-D06 — Metadata.csv como dicionário vivo do sistema

## Objetivo
Usar `metadata.csv` para gerar contrato semântico e documentação útil.

## Tarefas
- mapear `Table`, `Field`, `Description`
- validar cobertura entre metadata e colunas reais
- acusar lacunas
- usar metadata para enriquecer docs e contratos

## Saídas
- `docs/DATA_DICTIONARY.md`
- checagem de cobertura metadata vs schema
- atualização de `LOG.md`

## Definition of Done
- o projeto consegue mostrar quais campos têm descrição oficial
- divergências entre metadata e CSV real ficam visíveis
- o dicionário de dados não é manual e frágil

## Prompt para o Cursor
```text
Implemente o CRP-D06: transformar metadata.csv em dicionário vivo.

Tarefa:
1. Ler metadata.csv e relacioná-lo com os 4 datasets de negócio.
2. Criar docs/DATA_DICTIONARY.md combinando:
   - tabela
   - campo
   - descrição
   - tipo inferido
   - nulabilidade observada
3. Validar cobertura entre metadata e colunas reais.
4. Destacar inconsistências ou lacunas.
5. Atualizar LOG.md.

Critérios:
- Não duplicar manualmente o que pode ser gerado
- A documentação deve ser reproduzível
- O metadata.csv deve virar artefato útil para o projeto
```
