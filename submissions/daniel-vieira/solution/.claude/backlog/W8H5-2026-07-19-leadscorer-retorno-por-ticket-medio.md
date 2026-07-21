---
id: W8H5
parent:
project: LeadScorer
subject: Implementar a dimensao de retorno por ticket medio no codigo e na modelagem
author: dcvr@
priority: medium
status: done
created: 2026-07-19
updated: 2026-07-19
---


# Descrição (o que será feito)

Implementar, no código de modelagem e de scoring, a mudança do ancoramento da dimensão econômica
(Retorno) do preço de tabela para o ticket médio do cliente para aquele produto, com recuo por
setor e, em último caso, o preço de tabela, conforme o ADR R4T9. Abrange a modelagem SQL
('scripts/modeling.sql'), o carregamento e as estruturas ('src/model.lisp'), o cálculo da
dimensão econômica ('src/scoring.lisp'), a regeneração das fixtures derivadas e a atualização dos
testes Parachute. A estrutura do composto, os pesos e o expoente de momentum permanecem
inalterados; muda apenas o insumo da dimensão econômica. Os identificadores internos do código
permanecem ('economic' e afins), pois a renomeação foi limitada a documentação e interface.


# Motivações (por que será feito)

A decisão de ancorar o Retorno no ticket médio foi tomada durante a revisão da concepção e da
interface na sessão V7C2 (sub-tarefa de 8W2N) e registrada no ADR R4T9. A documentação e os
protótipos já a descrevem, mas a implementação no código, que é a fonte canônica do cálculo,
permanece pendente, de modo que existe uma divergência declarada entre a decisão e o código. Esta
tarefa fecha essa divergência. Pertence ao domínio do modelo de scoring (tarefa 3RJ8) e não à
prototipagem de interface, por isso é registrada separadamente.


# Recursos e dados necessários

- ADR R4T9 (a decisão e o recuo), 'docs/metodologia-scoring.md' (definição atualizada) e
  'docs/validacao-scoring.md';
- Código: 'scripts/modeling.sql' (view 'pair_won', 'sector_avg', bases 'potentials_base' e
  'initiated_base'), 'src/model.lisp' (structs 'pair' e 'opportunity' e seus loaders),
  'src/scoring.lisp' ('score-pair', 'score-opportunity', 'load-model');
- Testes e fixtures: 'tests/scoring.lisp' ('load-model-and-ordering') e
  'tests/fixtures/derived/';
- Ambiente: o dataset bruto (aquisição do Kaggle da tarefa 2H5K) para regenerar os derivados via
  DuckDB, e o 'qlot' para a verificação canônica; ambos ausentes no ambiente da sessão V7C2.


# Plano de trabalho (como será feito)

1. 'scripts/modeling.sql': na view 'pair_won', acrescentar 'AVG(close_value) AS pair_won_avg';
   emitir o insumo econômico como nova coluna (por exemplo 'economic_value') com a cadeia de recuo
   'COALESCE(pair_won_avg, sector_won_avg, sales_price)' em 'potentials_base' e 'initiated_base';
2. 'src/model.lisp': novo campo 'economic-value' nas structs 'pair' e 'opportunity' e nos
   respectivos loaders, lendo a nova coluna;
3. 'src/scoring.lisp': trocar o insumo da dimensão econômica em 'score-pair' e
   'score-opportunity' de 'list-price' para 'economic-value', e a população de referência em
   'load-model';
4. Regenerar as fixtures derivadas e atualizar os valores esperados dos testes afetados;
5. Verificar: compilar e carregar sem avisos, suíte Parachute verde e 'mallet' limpo, através do
   qlot; atualizar a validação de robustez quanto ao efeito do novo insumo econômico.


# Riscos e ressalvas

- A EDA adverte que o valor de fechamento acompanha de perto o preço de tabela, de modo que o
  ganho de sinal independente pode ser limitado (ADR R4T9);
- O arranque a frio (pares sem histórico de venda) exige o recuo por setor; a regeneração dos
  derivados depende do dataset bruto;
- A mudança altera as saídas do scoring, exigindo a atualização das expectativas de teste;
- A tarefa está gated pela disponibilidade do dataset e do qlot no ambiente de execução.


# Dependências

- blocks:
- blocked-by:


# Definição de pronto

- A dimensão econômica é computada a partir do ticket médio do par com recuo por setor e, em
  último caso, o preço de tabela, conforme o ADR R4T9;
- As estruturas, os loaders e o cálculo refletem a mudança, mantendo os identificadores internos;
- As fixtures derivadas são regeneradas e os testes Parachute passam;
- A verificação canônica passa: compilação sem avisos, Parachute verde e 'mallet' limpo, através
  do qlot;
- A metodologia e a validação são atualizadas para descrever o insumo econômico efetivamente
  implementado, removendo a marcação de implementação pendente.
