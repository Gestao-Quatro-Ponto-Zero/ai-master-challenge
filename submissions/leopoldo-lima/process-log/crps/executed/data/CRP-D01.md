# CRP-D01 — Congelar o contrato raw dos CSVs

## Objetivo
Formalizar os 5 arquivos como fonte oficial do projeto e impedir interpretação criativa logo na entrada.

## Entradas
- `accounts.csv`
- `products.csv`
- `sales_teams.csv`
- `sales_pipeline.csv`
- `metadata.csv`

## Tarefas
- criar a camada `raw`
- documentar colunas, tipos inferidos, nulabilidade e cardinalidade
- registrar que os CSVs são a source of truth
- proibir renomeação de coluna na ingestão

## Saídas
- `docs/DATA_SOURCES.md`
- `docs/RAW_CONTRACT.md`
- `src/.../raw/` ou equivalente
- atualização de `LOG.md`

## Definition of Done
- os 5 arquivos são lidos por código, não por notebook solto
- existe um resumo por arquivo com nome do campo, tipo inferido, nulabilidade e observações
- existe comando de snapshot/inspect dos dados

## Prompt para o Cursor
```text
Atue como engenheiro principal seguindo o método Vibecoding Industrial.

Implemente o CRP-D01: congelar o contrato raw dos CSVs.

Contexto:
Temos 5 arquivos oficiais:
- accounts.csv
- products.csv
- sales_teams.csv
- sales_pipeline.csv
- metadata.csv

Regras:
1. Esses arquivos são a fonte oficial de verdade.
2. Não renomeie colunas na ingestão raw.
3. Crie uma camada raw explícita no código.
4. Gere documentação técnica dos arquivos em:
   - docs/DATA_SOURCES.md
   - docs/RAW_CONTRACT.md
5. Documente por arquivo:
   - colunas
   - tipo inferido
   - nulabilidade
   - cardinalidade aproximada
   - observações importantes
6. Adicione um comando/script que faça inspeção dos CSVs e gere resumo reproduzível.
7. Atualize LOG.md com o que foi implementado e os riscos identificados.

Critérios:
- Nada de notebook como artefato principal
- Basear-se apenas nos CSVs reais
- Não corrigir dados ainda; apenas congelar e documentar
```
