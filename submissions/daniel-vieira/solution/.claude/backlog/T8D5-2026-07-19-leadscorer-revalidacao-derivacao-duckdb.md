---
id: T8D5
parent:
project: LeadScorer
subject: Regeneracao e revalidacao da derivacao DuckDB pos-desempate do ARG_MAX
author: dcvr@
priority: medium
status: done
created: 2026-07-19
updated: 2026-07-19
---


# Descrição (o que será feito)

Reexecutar a derivação DuckDB ('duckdb < scripts/modeling.sql') sobre o dataset completo, com o
diretório 'data/normalized/' provisionado, regenerando os artefatos de 'data/derived/', e
revalidar o scoring subsequente ('run-validation' e 'aggregation-comparison'), confirmando a
estabilidade dos derivados e dos coeficientes de robustez após a correção do desempate
determinístico do 'ARG_MAX' e do espelhamento integral do portão na assertion, ambos introduzidos
pela tarefa Q7B3.


# Motivações (por que será feito)

A tarefa Q7B3 corrigiu, em 'scripts/modeling.sql', a não-reprodutibilidade do 'last_close_value'
(desempate do 'ARG_MAX') e completou o espelhamento do portão de elegibilidade na assertion
'engaging_within_138'. Essas correções são de nível de fonte e não puderam ser executadas na
sessão de origem por ausência do dataset bruto no ambiente; a verificação automática limitou-se ao
lint 'sqlfluff' e a um teste de semântica do 'ARG_MAX' no DuckDB. O efeito das correções só se
materializa na próxima execução do pipeline, e a validação de dados permanece pendente. Esta
tarefa fecha o laço de verificação de uma mudança já mesclada em 'main'.


# Recursos e dados necessários

- 'scripts/modeling.sql' com as correções da Q7B3 (já em 'main');
- O dataset bruto e o pipeline de normalização que produzem 'data/normalized/*.csv' (tarefas
  2H5K e 4G7C), ausentes no ambiente da sessão Q7B3;
- 'duckdb' na linha de comando e o ambiente qlot local para a revalidação em Common Lisp;
- Os valores canônicos de referência das assertions de 'modeling.sql' (cadência, decaimento,
  'engaging' 298, contas 85, produtos 7) e os coeficientes de robustez documentados em
  'docs/validacao-scoring.md'.


# Plano de trabalho (como será feito)

1. Provisionar 'data/normalized/' a partir do dataset bruto;
2. Executar 'mkdir -p data/derived && duckdb < scripts/modeling.sql' e confirmar que as assertions
   fail-closed retornam zero linhas (incluindo 'engaging_within_138' com o portão completo);
3. Comparar 'data/derived/potentials_base.csv' e os demais derivados com a linha de base anterior,
   confirmando que o 'last_close_value' passou a ser determinístico e que os demais campos não
   regrediram;
4. Reexecutar 'run-validation' e 'aggregation-comparison' e comparar os coeficientes de robustez
   com os registrados em 'docs/validacao-scoring.md', declarando a referência e o resultado.


# Riscos e ressalvas

- O 'last_close_value' é coluna diagnóstica, não consumida pelo composto, de modo que o impacto
  esperado sobre os coeficientes de robustez é nulo; uma divergência não trivial nesses
  coeficientes indicaria um efeito colateral inesperado e deveria ser diagnosticada antes de
  aceitar o resultado;
- A regeneração depende da disponibilidade do dataset bruto, que não é versionado.


# Dependências

- blocks:
- blocked-by:


# Definição de pronto

- A derivação DuckDB é reexecutada com sucesso e todas as assertions fail-closed retornam zero
  linhas;
- Os derivados regenerados são comparados com a linha de base e a determinismo do
  'last_close_value' é confirmado;
- 'run-validation' e 'aggregation-comparison' são reexecutados e os coeficientes de robustez são
  comparados com 'docs/validacao-scoring.md', com a referência e o resultado declarados;
- 'docs/validacao-scoring.md' é atualizado caso a revalidação altere qualquer valor registrado.
