# Diagnóstico descritivo de receita

## Definição

MRR é relatado como valor associado. No grão conta, `total_mrr_current` soma episódios ativos no cutoff governado; no grão episódio, MRR permanece independente.

## Totais

- MRR de episódios: 11338747.00;
- MRR em episódios abertos: 10159608.00;
- MRR em episódios encerrados: 1179139.00;
- MRR no cutoff de contas com churn observado: 3295497.00;
- MRR no cutoff de contas reativadas: 197250.00.

## Faixas e estados

Faixas usam quartis de MRR ativo no cutoff, com desempate estável. Valores detalhados por estado e faixa estão em `revenue_diagnostics.json`.

## Limitações

Sobreposição torna MRR de episódios não aditivo como exposição de conta. Os valores não comprovam perda, recuperação ou reconhecimento financeiro.
