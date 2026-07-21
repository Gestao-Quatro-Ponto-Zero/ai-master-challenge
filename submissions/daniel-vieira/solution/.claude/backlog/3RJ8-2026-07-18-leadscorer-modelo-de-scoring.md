---
id: 3RJ8
parent:
project: LeadScorer
subject: Modelo de scoring de leads por indicador composto (tripla produto-empresa-agente)
author: dcvr@
priority: high
status: done
created: 2026-07-18
updated: 2026-07-19
---


# Descrição (o que será feito)

Especificar e implementar em Common Lisp, com testes, um indicador de potencial 0-100 por tripla
produto-empresa-agente, que apoie a priorização de oportunidades e seja explicável a um usuário
não técnico. O indicador é um composto de dimensões 0-100 exibíveis (potencial econômico,
afinidade/consumo, momentum e especialização do agente, além de dimensões carregadas por
completude com peso nulo), sob um portão de elegibilidade e com o momentum atuando
multiplicativamente. O sistema
produz duas listas: as oportunidades potenciais não iniciadas, visíveis a todos e personalizadas
por agente, e as oportunidades iniciadas de cada agente, decaindo até expirar.


# Motivações (por que será feito)

É o objetivo específico central do projeto e o critério de avaliação de maior peso do
desafio, que valoriza uma lógica de scoring além da ordenação simples e a transparência sobre a
complexidade. A análise exploratória (1J8R) mostrou sinal preditivo fraco nos atributos
observáveis, o que desloca o propósito para a demonstração do método e o apoio à decisão. Por
decisão registrada no ADR B7Q3, esta tarefa incorpora a capacidade demonstrada do agente, antes
objeto da 5T6Q, agora cancelada, como a dimensão de especialização, personalizando o
ranqueamento por agente.


# Recursos e dados necessários

- Fonte normalizada 'data/normalized/' (4G7C) e o motor DuckDB para a construção da base de
  modelagem e os testes exploratórios;
- Base de conhecimento 'docs/analise-exploratoria.md' e as consultas de 'scripts/eda.sql';
- Ambiente Common Lisp sob qlot, com Parachute para testes e o linter mallet;
- Handbook on Constructing Composite Indicators (OECD/JRC, 2008) para as cautelas metodológicas.


# Plano de trabalho (como será feito)

O trabalho é decomposto em seis fases, cada uma uma fronteira de commit:

- Fase 1, Especificação: ratificar a decisão apoiada, a saída dupla, a entidade pontuada, a
  explicabilidade e os critérios de aceitação. Documental;
- Fase 2, Metodologia e fundamentação: formalizar o composto, consultar a literatura para
  cautelas documentadas, definir a abordagem de validação e registrar o ADR de metodologia;
- Fase 3, Construção da base de modelagem: derivar do conjunto fechado os artefatos empíricos
  (âncoras de preço, cadência, curva de decaimento, especialização), montar a tabela de triplas e
  aplicar o portão de elegibilidade;
- Fase 4, Implementação do composto e das duas listas em Common Lisp, orientada a testes;
- Fase 5, Validação: qualidade de ranqueamento contra baselines (só-valor, só-recência,
  aleatório), sensibilidade entre métodos de normalização e validade de face, com integridade
  temporal;
- Fase 6, Refinamento e conclusão: ajuste, documentação em 'docs/', verificação dos critérios e
  preparo para a 8W2N.


# Riscos e ressalvas

- A base tem marcas de dado sintético e sinal preditivo fraco; o propósito é demonstrar o método,
  não a acurácia sobre estes dados;
- As dimensões de tempo de fechamento e de inatividade, e a sub-regra de cross/up-sell no
  momentum, são carregadas por completude com peso zero ou nulo nesta base, pois os dados não as
  sustentam; devem ser exibidas sem distorcer o ranqueamento;
- O braço descendente da curva de momentum é assumido, na ausência de contas inativas para
  ajustá-lo;
- Os derivados de modelagem dependem da fonte normalizada e devem ser regenerados quando os
  brutos forem readquiridos.


# Dependências

- blocks: 8W2N
- blocked-by: 4G7C


# Definição de pronto

- Uma fonte de modelagem derivada de 'data/normalized/' contém, por tripla elegível, as quatro
  dimensões ativas em escala 0-100 e o indicador composto 0-100;
- O portão de elegibilidade exclui triplas sem conta e, nas iniciadas, com engajamento
  superior a 138 dias;
- O momentum entra multiplicativamente, e um teste demonstra que uma tripla com fechamento
  recente recebe momentum baixo e desce no ranqueamento;
- Cada dimensão é exposta individualmente para a explicabilidade por decomposição;
- As duas listas são produzidas conforme a especificação, a de potenciais com filtro de corte;
- Os pesos são arbitrados e documentados, e a normalização é por percentil com a sensibilidade a
  min-max reportada;
- As dimensões de peso zero ou nulo são documentadas como inertes nesta base, com a justificativa
  registrada, e não distorcem o ranqueamento;
- A verificação obrigatória passa: o sistema Common Lisp compila e carrega sem avisos, os testes
  Parachute passam e o mallet não relata achados; o SQL passa no sqlfluff (dialeto duckdb) onde
  aplicável;
- A metodologia é documentada em 'docs/' e o ADR de metodologia é registrado.
