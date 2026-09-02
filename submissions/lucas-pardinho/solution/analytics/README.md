# Pipeline analitico do G4 Focus

Esta pasta transforma os cinco CSVs brutos do challenge em contratos JSON prontos
para a aplicacao. O pipeline e deterministico, usa apenas Python 3.11+ e nao altera
os arquivos de `data/raw/`.

## Executar

A partir de `solution/`:

```bash
python3 analytics/pipeline.py \
  --data-dir data/raw \
  --normalized-dir data/normalized \
  --output-dir generated
```

O comando valida schemas, chaves, datas e joins; grava a camada normalizada; treina
e avalia o estimador; e gera:

- `generated/opportunities.json`: as 2.089 oportunidades abertas com score, fila,
  explicacao e proxima acao;
- `generated/dashboard.json`: KPIs e agregacoes executivas;
- `generated/model-report.json`: target, features, metricas, regras e limitacoes;
- `generated/data-quality.json`: hashes, schemas, joins, alertas e transformacoes.

## Metodologia

O target de Engaging e `P(Won nos proximos 60 dias | ainda aberto)`. Para
reconstrui-lo, oportunidades Won/Lost viram snapshots semanais. Deals ainda
Engaging tambem entram como negativos, mas somente em datas nas quais os 60 dias
seguintes ja sao totalmente observaveis no snapshot de 2017-12-31. Isso evita
selection bias de treinar apenas com deals que encerraram. Todas as linhas de uma
oportunidade permanecem no mesmo lado do split temporal, e cada oportunidade soma
peso 1 para evitar que ciclos longos dominem o treino.

O ambiente validado nao inclui scikit-learn. Por isso, a probabilidade usa um
estimador empirico suavizado em dois niveis: faixa de idade e produto + faixa de
idade. O holdout contem apenas coortes de engajamento posteriores ao treino. O
relatorio compara o estimador com a taxa constante usando Brier, average precision
e precision@20 e so adota a segmentacao quando ela preserva calibracao e ranking.
Campos de desfecho, conta e identidade do vendedor nunca entram na probabilidade.
Acima do maior ciclo encerrado, a confianca cai e a fila muda para resgate; isso nao
e apresentado como relacao causal entre idade e vitoria eventual.

O score de prioridade de Engaging combina:

```text
65% probabilidade + 20% actionability do ciclo + 15% valor de catalogo
```

Prospecting nao recebe probabilidade. Seu score de qualificacao combina conta
identificada (60%) e valor potencial (40%).

## Testes

```bash
python3 -m unittest discover -s analytics/tests -v
```

Os testes rodam o pipeline em diretorios temporarios e cobrem reproducibilidade,
contratos, normalizacao, leakage, joins, limites de score e regras de filas.
