---
id: 1J8R
parent:
project: LeadScorer
subject: Análise exploratória dos dados brutos do dataset CRM
author: dcvr@
priority: high
status: done
created: 2026-07-18
updated: 2026-07-18
---


# Descrição (o que será feito)

Realizar uma análise exploratória dos quatro arquivos CSV do dataset CRM para enriquecer a
compreensão do domínio e do problema antes da modelagem. Registrar os aprendizados e achados em
um documento de base de conhecimento sob 'docs/' e referenciá-lo no 'README.md'. A análise deve
cobrir, no mínimo: a distribuição de 'deal_stage' e as taxas de conversão; a distribuição de
'close_value'; os tempos de ciclo entre 'engage_date' e 'close_date'; o desempenho por agente,
gerente e escritório regional; padrões por setor, porte e receita das contas e por produto; e a
qualidade dos dados, incluindo nulos, faixas de valores e integridade referencial entre o
pipeline e as tabelas de contas, produtos e times.


# Motivações (por que será feito)

A modelagem de scoring e de distribuição depende de critérios ancorados na estrutura real dos
dados. Uma análise exploratória prévia reduz o risco de escolher critérios desalinhados com a
distribuição efetiva das variáveis, expõe problemas de qualidade que afetam o cálculo e
constitui a base de conhecimento comum às duas tarefas de modelagem. O desafio valoriza a
compreensão genuína do problema antes da execução.


# Recursos e dados necessários

- Os quatro CSV do dataset em 'data/', mais o 'metadata.csv' como dicionário de campos,
  disponibilizados e verificados pela tarefa 2H5K;
- Motor analítico DuckDB, que o std-sql.md reserva para pesquisa, modelagem e simulação, capaz
  de consultar os CSV diretamente sem carga nem persistência (a confirmar em execução).


# Plano de trabalho (como será feito)

- Confirmar a disponibilidade do DuckDB e a leitura direta dos CSV;
- Executar as consultas exploratórias por eixo (estágios e conversão, valor, ciclo, agentes e
  regiões, contas e produtos, qualidade), mantendo as consultas versionadas e reprodutíveis;
- Consolidar os achados e as implicações para a modelagem em um documento sob 'docs/';
- Referenciar a base de conhecimento no 'README.md'.


# Riscos e ressalvas

- Achados de qualidade de dados (nulos, inconsistências, quebras de integridade) podem exigir
  decisões de tratamento que impactam a modelagem; devem ser registrados, não silenciados;
- A adoção do DuckDB como motor analítico já está prevista no std-sql.md, mas a sua efetiva
  disponibilidade no ambiente deve ser confirmada.


# Dependências

- blocks: 4G7C
- blocked-by: 2H5K


# Definição de pronto

Um documento de base de conhecimento sob 'docs/' registra os achados da análise exploratória nos
eixos mínimos definidos, com as implicações para a modelagem de scoring e de distribuição, as
consultas ou o script da análise estão versionados e reprodutíveis, e o 'README.md' referencia
essa base de conhecimento.
