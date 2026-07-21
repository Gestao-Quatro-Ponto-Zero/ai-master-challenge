---
id: 9P4D
parent:
project: LeadScorer
subject: Persistência - schema PostgreSQL e carga do dataset (Fase B)
author: dcvr@
priority: medium
status: done
created: 2026-07-18
updated: 2026-07-19
---


# Descrição (o que será feito)

Materializar em PostgreSQL o modelo de dados especificado na concepção
('docs/concepcao-inicial.md', seção "Modelo relacional"), a saber, o grupo de referência
(accounts, products, regional_offices, sales_managers, sales_agents, engagement_justifications)
e o grupo do ciclo de engajamento (opportunities, opportunity_scores, engagements). Implementar
as migrações SQL numeradas e idempotentes, o script de carga (seed) a partir dos CSV
normalizados e a verificação de integridade referencial e de contagem. Pertence à fase de
aplicação, na qual o PostgreSQL é introduzido conforme o ADR D2K9.


# Motivações (por que será feito)

A aplicação web serve a classificação e o ciclo de engajamento a partir de dados persistidos. A
fase de modelagem opera sobre CSV e não depende desta tarefa; a persistência em banco é
necessária quando a interface e a operação da aplicação a exigirem. O modelo foi consolidado e
aprovado na tarefa M5T2, que é a especificação de origem desta tarefa.


# Recursos e dados necessários

- Especificação do modelo: 'docs/concepcao-inicial.md', seção "Modelo relacional";
- Fonte de dados: 'data/normalized/*.csv' (accounts, products, sales_teams, sales_pipeline);
- Padrão de SQL: '.claude/rules/std-sql.md' (dialeto postgres, verificado com sqlfluff);
- Stack de persistência: PostgreSQL com versão fixada e Postmodern, conforme o ADR D2K9;
- Valores canônicos de verificação: accounts 85, products 7, sales_teams 35 agentes, 6 gerentes,
  3 escritórios, sales_pipeline 8.800, conforme a tarefa 2H5K e a análise exploratória.


# Plano de trabalho (como será feito)

1. Migrações de referência: criar as seis tabelas do grupo de referência, com chaves
   substitutas, restrições de unicidade e chaves estrangeiras (subsidiary_of em accounts,
   regional_office em sales_managers, sales_manager em sales_agents), conforme a concepção e o
   'std-sql.md';
2. Migrações operacionais: criar opportunities, opportunity_scores e engagements, com as chaves
   estrangeiras, as restrições de unicidade (par conta-produto; par oportunidade-agente) e as
   restrições de domínio de status e outcome;
3. Script de seed das referências: carregar accounts e products dos CSV; derivar
   regional_offices, sales_managers e sales_agents de sales_teams.csv, com os usernames
   derivados do nome; semear engagement_justifications com os três valores;
4. Script de seed do ciclo: materializar opportunities como os pares distintos conta-produto e
   engagements como as linhas de sales_pipeline (Won, Lost, Engaging), convertendo datas para
   UNIX em milissegundos e valores monetários para inteiro na menor unidade com código ISO 4217;
5. Derivação do estado ativo: definir o status de cada oportunidade a partir do seu ciclo
   corrente, a saber, 'engaging' quando há um ciclo aberto e 'prospecting' caso contrário;
6. Verificação: conferir a integridade referencial e as contagens contra os valores canônicos,
   cobrir a carga por testes e aplicar as migrações de forma idempotente a partir de um banco
   vazio.


# Riscos e ressalvas

- O mapeamento de sales_pipeline para opportunities agrupa múltiplos ciclos históricos por par
  conta-produto; a regra de derivação do estado ativo deve tratar pares com vários ciclos e
  pares com ciclo aberto de forma inequívoca;
- A moeda do dataset é indeterminada; adota-se USD como convenção documentada, e os valores são
  convertidos para a menor unidade sem uso de ponto flutuante;
- A camada de migração não dispõe de biblioteca canônica madura (ADR D2K9); a aplicação
  idempotente das migrações numeradas é responsabilidade de um script próprio;
- A conversão de datas do CSV para UNIX em milissegundos, em UTC, deve preservar a semântica de
  ciclo aberto (close_date ausente) das linhas Engaging.


# Dependências

- blocks: 8W2N
- blocked-by: 7K2M, 2H5K, M5T2


# Definição de pronto

- As migrações numeradas criam o schema completo a partir de um banco vazio, sem erro e de forma
  idempotente;
- O seed carrega as tabelas de referência e materializa opportunities e engagements, e as
  contagens conferem com os valores canônicos;
- A integridade referencial é verificada e o estado ativo das oportunidades é derivado
  corretamente das linhas do pipeline;
- A carga é coberta por testes e o 'sqlfluff' no dialeto postgres não relata achados.
