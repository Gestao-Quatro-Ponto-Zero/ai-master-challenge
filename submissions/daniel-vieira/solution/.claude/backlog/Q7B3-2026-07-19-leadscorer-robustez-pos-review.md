---
id: Q7B3
parent:
project: LeadScorer
subject: Robustez e reprodutibilidade pos-review da camada src e persistencia
author: dcvr@
priority: high
status: done
created: 2026-07-19
updated: 2026-07-19
---


# Descrição (o que será feito)

Aplicar as correções confirmadas pela auditoria de code review da camada 'src/', dos seus testes
e da camada de persistência, endereçando defeitos de correção (majoritariamente latentes),
fragilidades de fail-closed e uma não-reprodutibilidade ativa na derivação de modelagem. O
escopo é o conjunto de correções aceito na sessão, a saber:

- Guarda de entrada vazia em 'pearson' (validation.lisp), evitando divisão por zero a partir de
  'run-validation';
- Limitação de 'min-max-normalize' a [0,100] (scoring.lisp), corrigindo composto fora de faixa
  na forma multiplicativa sob min-max;
- Tolerância a 'engage_date' em branco no comparador de 'choose-open-cycle' (seed.lisp);
- Envolvimento em 'sql-value' dos valores possivelmente NIL destinados a colunas inteiras em
  'seed-engagements' e 'seed-accounts' (seed.lisp);
- Retentativa do estabelecimento da conexão de trabalho, em conexão única, em 'call-with-database'
  (db.lisp);
- Restauração fail-safe do checksum via 'unwind-protect' e skip explícito do Parachute no teste
  de integração (tests/persistence.lisp);
- Testes de cobertura para o piso geométrico, a variância zero e a união vazia de Jaccard;
- Desempate determinístico do 'last_close_value' e espelhamento do portão na assertion de
  'engaging' em 'scripts/modeling.sql'.


# Motivações (por que será feito)

A auditoria de code review em alto esforço (seis ângulos de busca, verificação adversarial com
viés de recall) confirmou seis defeitos de correção e dois plausíveis, além de lacunas de teste.
Um defeito é ativo (a não-reprodutibilidade de 'last_close_value' via 'ARG_MAX' sem desempate);
os demais são latentes mas violam o princípio fail-closed do projeto, convertendo condições de
borda em erros enganosos ou em travamento da carga. A correção consolida a robustez das camadas
entregues em 3RJ8 (scoring) e 9P4D (persistência) antes de a Fase 4 da 8W2N construir os serviços
de ciclo sobre elas.


# Recursos e dados necessários

- Relatório de code review da sessão (registrado no worklog Q7B3-2026-07-19-1);
- Código-fonte em 'src/', testes em 'tests/' e 'scripts/modeling.sql';
- Ambiente qlot local ('qlot exec sbcl'), linter 'mallet' e 'sqlfluff' (dialeto duckdb);
- Fixtures de teste versionados em 'tests/fixtures/', suficientes para a suíte sem banco. O
  PostgreSQL e os CSV normalizados estão ausentes no ambiente da sessão; o teste de integração de
  persistência permanece ignorado, e a derivação DuckDB de 'modeling.sql' não é reexecutável por
  falta do dataset bruto.


# Plano de trabalho (como será feito)

1. Ciclo TDD dos defeitos com teste unitário viável (pearson vazio, clamp de min-max,
   comparador de ciclo aberto com data em branco, piso geométrico, variância zero, Jaccard vazio):
   teste que falha, correção mínima, suíte verde;
2. Correções verificáveis pela suíte ou por inspeção assistida (sql-value no seed, retentativa da
   conexão em db.lisp, unwind-protect e skip no teste de integração);
3. Correções de 'scripts/modeling.sql' (desempate do ARG_MAX, portão da assertion), verificadas
   por 'sqlfluff'; a reexecução da derivação e a revalidação do scoring ficam diferidas por
   ausência do dataset bruto no ambiente;
4. Verificação completa da definição de pronto e auditoria independente no encerramento.


# Riscos e ressalvas

- As correções de 'modeling.sql' alteram um artefato de derivação de dados; o seu efeito só se
  materializa na próxima execução do pipeline DuckDB, que não é reexecutável nesta sessão por
  falta do dataset bruto. A verificação automática limita-se ao lint; a revalidação do scoring é
  um desenvolvimento futuro obrigatório antes de a mudança ser considerada plenamente validada;
- A limitação de 'min-max-normalize' a [0,100] é um no-op sobre a população de potenciais (onde o
  valor normalizado sempre pertence à população de referência), de modo que os números de
  sensibilidade já validados em 'docs/validacao-scoring.md' são preservados; o efeito recai
  apenas sobre a lista de iniciadas;
- A reescrita de 'call-with-database' toca o ciclo de vida da conexão e não é exercitável sem
  banco no ambiente; a sua verificação de comportamento depende de uma execução com PostgreSQL.


# Dependências

- blocks:
- blocked-by:


# Definição de pronto

- 'pearson' retorna 0.0 para entrada vazia, sem sinalizar erro, coberto por teste;
- 'min-max-normalize' nunca retorna fora de [0,100], coberto por teste com valor fora da
  população; por consequência, 'multiplicative-composite' permanece em [0,100];
- 'choose-open-cycle' seleciona um ciclo aberto sem erro quando algum ciclo aberto tem
  'engage_date' em branco, coberto por teste;
- 'seed-engagements' e 'seed-accounts' envolvem em 'sql-value' os valores possivelmente NIL
  destinados a 'engaged_at', 'sales_agent_id' e 'subsidiary_of_id';
- 'call-with-database' estabelece uma única conexão de trabalho com retentativa do estabelecimento;
- o teste de integração restaura o checksum de 'schema_migrations' via 'unwind-protect' e, sem
  banco, é marcado como ignorado pelo Parachute em vez de afirmar uma tautologia;
- há testes de cobertura para o piso geométrico, a variância zero e a união vazia de Jaccard;
- 'scripts/modeling.sql' desempata deterministicamente o 'last_close_value' e a assertion
  'engaging_within_138' espelha o portão 'BETWEEN 0 AND 138';
- a verificação aplicável passa: compilação sem avisos, suíte Parachute verde, 'mallet' sem
  achados nos arquivos Lisp tocados e 'sqlfluff' sem achados nos arquivos SQL tocados.
