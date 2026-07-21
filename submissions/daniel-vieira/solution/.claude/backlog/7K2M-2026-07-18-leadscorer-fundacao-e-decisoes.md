---
id: 7K2M
parent:
project: LeadScorer
subject: Fundação do projeto e registro das decisões arquiteturais
author: dcvr@
priority: high
status: done
created: 2026-07-18
updated: 2026-07-18
---


# Descrição (o que será feito)

Estabelecer a fundação mínima, verificável e reproduzível para iniciar a fase de modelagem:
repositório Git versionado, as três decisões arquiteturais registradas como ADR, a estrutura de
código-fonte e o esqueleto do sistema ASDF sob qlot que compila e carrega sem avisos e provê a
leitura genérica de arquivos CSV coberta por testes. Esta tarefa não ergue PostgreSQL nem
contêiner, não ingere o dataset real e não implementa lógica de negócio; a persistência em
banco, o servidor web, o HTMX e a conteinerização pertencem à fase de aplicação.


# Motivações (por que será feito)

O projeto encontrava-se em gênese, sem repositório versionado nem estrutura de código. As
decisões de stack, empacotamento e estratégia de repositório foram tomadas e confirmadas pelo
usuário e são consequentes e difíceis de reverter, o que exige o seu registro formal como ADR.
O usuário definiu que a fase de modelagem operaria diretamente sobre os arquivos CSV,
postergando o PostgreSQL, o que torna a fundação enxuta e alinhada ao princípio MVP.


# Recursos e dados necessários

- SBCL, qlot e a distribuição Quicklisp para o ambiente Common Lisp;
- Biblioteca fare-csv para a leitura de CSV, Parachute para testes e o linter mallet;
- Gabaritos de ADR em '.claude/assets/templates/temp-adr.md' e índice em
  '.claude/decisions/_adr-index.md'.


# Plano de trabalho (como será feito)

Detalhado e aprovado em modo de planejamento. Em síntese: inicializar o repositório e a higiene
de versionamento; registrar os ADRs D2K9, D4M3 e D6P7 e indexá-los; criar o sistema ASDF, o
pacote, o utilitário de leitura de CSV e a suíte de testes com um fixture mínimo; fixar as
dependências com qlot; verificar carga, testes e linter.


# Riscos e ressalvas

- A pilha de aplicação (servidor web, HTMX, PostgreSQL, contêiner) introduz dependências novas
  cuja implementação e verificação ocorrem na fase de aplicação, não nesta tarefa;
- O qlot reside fora do PATH global neste ambiente, o que deverá ser tratado no Dockerfile da
  fase de aplicação.


# Dependências

- blocks: 2H5K, 9P4D
- blocked-by:


# Definição de pronto

O sistema Common Lisp compila e carrega sem avisos sob o ambiente qlot, a suíte Parachute passa
cobrindo a leitura do fixture CSV, o linter mallet não reporta achados sobre 'src/' e 'tests/',
o 'qlfile.lock' está gerado e os três registros de decisão (D2K9, D4M3, D6P7) estão criados e
indexados no '_adr-index.md'.
