---
id: W3Q6
parent:
project: LeadScorer
subject: Divida tecnica pos-review do scoring e da persistencia
author: dcvr@
priority: low
status: done
created: 2026-07-19
updated: 2026-07-20
---


# Descrição (o que será feito)

Endereçar os itens de qualidade não-corretivos identificados pela auditoria de code review da
tarefa Q7B3, agrupados por afinidade em três fases: (1) substituir as comparações de igualdade
exata sobre ponto flutuante; (2) refinar a retentativa de conexão para distinguir erros
transitórios de permanentes; (3) aplicar a limpeza de reuso e simplificação apontada. Nenhum item
é uma correção de defeito ativo; todos são melhorias de conformidade e manutenibilidade.


# Motivações (por que será feito)

A auditoria de code review da Q7B3 confirmou, além dos defeitos já corrigidos, um conjunto de
itens de menor materialidade deliberadamente diferidos para não perturbar código validado nem
expandir o escopo daquela sessão. Registrá-los no backlog assegura que não se percam, dado que o
worklog não é carregado na abertura de sessão. A prioridade é baixa porque nenhum item afeta a
correção em produção.


# Recursos e dados necessários

- Relatório de auditoria da sessão Q7B3 (worklog 'Q7B3-2026-07-19-1');
- 'src/validation.lisp', 'src/scoring.lisp', 'src/seed.lisp', 'src/db.lisp', 'src/csv.lisp';
- 'docs/validacao-scoring.md' para a revalidação do Spearman;
- Ambiente qlot local, 'mallet' e um PostgreSQL real para validar o refinamento do retry.


# Plano de trabalho (como será feito)

1. Fase 1 --- convenções de ponto flutuante: substituir as comparações '=' exatas sobre floats
   por comparação com tolerância, nos sítios apontados (o '(= minimum maximum)' de
   'min-max-normalize', o '(= (car ...) (car ...))' de 'ranks', o '(= v x)' de 'percentile-rank'),
   e revalidar os coeficientes de Spearman de 'docs/validacao-scoring.md', dado que a semântica de
   empates alimenta essas correlações;
2. Fase 2 --- refinamento do retry: em 'connect-with-retry', distinguir por SQLSTATE os erros
   transitórios de conexão (socket recusado e a fase FATAL "the database system is starting up",
   57P03) dos erros permanentes (credencial inválida, base inexistente), retentando apenas os
   primeiros, e validar o comportamento contra um PostgreSQL real;
3. Fase 3 --- limpeza não-corretiva: unificar a duplicação entre 'score-pair' e 'score-opportunity';
   remover a tabela 'seen' redundante de 'seed-regional-offices'; eliminar a sonda duplicada de
   'database-reachable-p'; avaliar o uso do escritor de 'fare-csv' no lugar do quoting manual de
   'csv.lisp'; substituir o 'pushnew' linear de 'load-model' por um conjunto de teste 'equal'.

Estado: a Fase 3 foi CONCLUIDA na sessao W3Q6-2026-07-19-1 (unificacao via 'score-triple', remocao
do 'seen', 'pushnew' substituido por conjunto hash; a sonda duplicada tornou-se obsoleta com a
Q7B3 e o escritor CSV manual foi mantido apos avaliacao). As Fases 1 e 2 foram CONCLUIDAS na
sessao W3Q6-2026-07-20-2. Na Fase 1, a revisao sitio a sitio concluiu que a igualdade exata sobre
float e correta nos tres sitios (guard de divisao por zero e deteccao de empate); a evidencia
empirica sobre o modelo real mostrou ausencia de ambiguidade de arredondamento (nenhum par de
valores a menos de 1e-9 sem ser exatamente igual), de modo que a mudanca de codigo foi descopada e
substituida por fundamento registrado inline, com os coeficientes de Spearman reproduzidos
exatamente. Na Fase 2, 'connect-with-retry' passou a retentar apenas os transitorios (socket e
57P03) por despacho de classe de condicao, validado contra o PostgreSQL real dos containers.


# Riscos e ressalvas

- A Fase 1 toca código cujos resultados estão validados em 'docs/validacao-scoring.md'; a
  revalidação do Spearman é obrigatória e a mudança não deve ser aceita sem ela;
- A Fase 2 depende de um PostgreSQL real para validar o comportamento de retentativa, não
  exercitável na suíte sem banco;
- A Fase 3 é de baixo risco, mas cada alteração deve manter a suíte Parachute verde e o 'mallet'
  limpo.


# Dependências

- blocks:
- blocked-by:


# Definição de pronto

- Nenhuma comparação de igualdade exata *indevida* sobre ponto flutuante permanece nos sítios
  apontados. A revisão sítio a sítio (autorizada) concluiu que a igualdade exata é correta nos
  três sítios (guard de divisão por zero e detecção de empate), com o fundamento registrado
  inline e apoiado por evidência empírica de ausência de ambiguidade de arredondamento sobre o
  modelo real; os coeficientes de robustez de 'docs/validacao-scoring.md' são reproduzidos
  exatamente, confirmando comportamento inalterado;
- 'connect-with-retry' retenta apenas os erros transitórios de conexão, preservando a tolerância à
  fase de inicialização, com o comportamento validado contra um PostgreSQL real;
- Os itens de limpeza são aplicados sem regressão, com a suíte Parachute verde e o 'mallet' sem
  achados;
- Cada fase pode ser entregue e comitada de forma independente, dado que não há acoplamento entre
  elas.
