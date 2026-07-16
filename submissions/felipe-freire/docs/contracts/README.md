# Contratos canônicos

Antes da execução, o Planner e o Data Engineer materializam aqui:

- `source-data.md`: fonte, licença, grão, schema, ranges e versão;
- `analytical-dataset.md`: população, filtros, features e invariantes;
- `metric-registry.md`: nome, fórmula, denominador, unidade, owner e casos extremos;
- `evidence-schema.md`: campos e estados dos evidence records;
- `serving-tables.md`: schemas consumidos pelo dashboard/modelo.

Contratos são versionados e aprovados antes dos consumidores. Mudança quebra o gate dos artefatos dependentes e exige reconciliação.
