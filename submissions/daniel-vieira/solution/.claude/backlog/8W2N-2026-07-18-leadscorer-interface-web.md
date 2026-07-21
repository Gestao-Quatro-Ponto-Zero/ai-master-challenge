---
id: 8W2N
parent:
project: LeadScorer
subject: Interface web de visualização e priorização de leads
author: dcvr@
priority: medium
status: done
created: 2026-07-18
updated: 2026-07-20
---


# Descrição (o que será feito)

Construir as duas aplicações web server-side em Common Lisp com HTMX especificadas na concepção
('docs/concepcao-inicial.md'), a saber, a aplicação do agente e a aplicação do gerente,
segregadas e sem gestão de papéis, que apresentam a classificação de leads e operam o ciclo de
engajamento (ranqueamento, seleção, decaimento, fechamento e expiração) de forma
autoexplicativa e em conformidade com o design system do projeto.


# Motivações (por que será feito)

É o terceiro objetivo específico do projeto e o ponto de contato do usuário final com a solução.
O desafio avalia usabilidade, suporte à decisão e explicabilidade para usuários não técnicos, e
oferece bônus pela filtragem por indivíduo, gerente ou região. A concepção foi consolidada na
tarefa M5T2, que é a especificação de origem desta tarefa.


# Recursos e dados necessários

- Especificação funcional: 'docs/concepcao-inicial.md' (estórias, tela inicial, ciclo de
  computação, modelo relacional);
- Motor de scoring existente: 'src/scoring.lisp' e 'src/model.lisp' (dimensões, momentum,
  composto e listas);
- Persistência: o schema e o seed da tarefa 9P4D;
- Design system: '.claude/rules/design.md' e '.claude/assets/tokens/'; exemplos ilustrativos em
  '.claude/assets/examples/';
- Stack de aplicação conforme o ADR D2K9 (Clack, Hunchentoot, Ningle, Spinneret, Postmodern,
  HTMX 2.0.x);
- Parâmetros de modelo e regras de negócio em um arquivo de configuração em forma Lisp
  (s-expression), lido pela aplicação com '*read-eval*' em falso.


# Plano de trabalho (como será feito)

A tarefa é ampla e deve ser decomposta em sub-tarefas atômicas no início da sua sessão, na
divisão indicada pelas fases abaixo, a saber, a fundação (fases 1 a 4), a aplicação do agente
(fase 5) e a aplicação do gerente (fase 6).

1. Prototipagem estática: produzir os protótipos autônomos em HTML e CSS das telas principais
   (tela inicial com cartões de indicadores e top tier, lista de disponíveis, lista de
   engajadas, visão do gerente, modal de justificativa) no padrão
   'example-{topic}-{theme}.html', conforme o processo orientado a exemplos do design system;
2. Esqueleto da aplicação: montar Clack sobre Hunchentoot, roteamento com Ningle e renderização
   com Spinneret, servir o HTMX como ativo estático sob CSP estrita com htmx.config.allowEval em
   falso, e estabelecer o layout base a partir dos tokens;
3. Identificação e sessão: login por seleção do usuário semeado, sem senha, com sessão de
   servidor e segregação das duas aplicações por papel;
4. Serviços de ciclo: implementar os laços de ranqueamento, decaimento e expiração, persistindo
   opportunity_scores a partir do motor de 'src/scoring.lisp' e observando o ciclo acelerado da
   concepção (ranqueamento e decaimento a cada minuto, expiração em vinte minutos);
5. Aplicação do agente: tela inicial (cartões de indicadores e top tier); lista de disponíveis
   com filtros, ordenação, nota explicativa das dimensões, filtro de corte e destaque do top
   tier; engajamento com o limite de dez e o modal de justificativa fora do top tier; lista de
   engajadas com os desfechos won, lost e devolução;
6. Aplicação do gerente: tela inicial (cartões do time e engajadas do time); visão de
   acompanhamento das engajadas do time com filtros por agente, produto, conta e data, e
   ordenação;
7. Responsividade (validação no iPhone 13), conformidade com o design system e verificação
   completa.


# Riscos e ressalvas

- O escopo é composto e material; a ausência de decomposição em sub-tarefas atômicas
  comprometeria o controle da execução. A decomposição precede a execução;
- O padrão de integração HTMX com Common Lisp não é coberto por documentação oficial e é
  implementado manualmente por inspeção do cabeçalho HX-Request (ADR D2K9);
- O ranqueamento personalizado por agente recomputa uma pontuação por par disponível e agente a
  cada minuto; a implicação de escala é aceitável para o MVP e está declarada na concepção;
- A lista de destaque do gerente na tela inicial (oportunidades engajadas do time) é a proposta
  registrada na concepção e deve ser confirmada na prototipagem.


# Dependências

- blocks: 6X9H
- blocked-by: 3RJ8, 9P4D, M5T2


# Definição de pronto

- As duas aplicações, do agente e do gerente, operam server-side com HTMX, em conformidade com o
  design system e responsivas no iPhone 13;
- O ciclo de engajamento completo funciona, a saber, ranqueamento, seleção com limite e
  justificativa, decaimento, fechamento e expiração, com os serviços automáticos ativos;
- A tela inicial apresenta os cartões de indicadores e a lista de destaque de cada papel, e as
  listas oferecem os filtros, a ordenação, a nota explicativa e o filtro de corte especificados;
- A verificação de software aplicável passa (compilação sem avisos, testes Parachute, linter
  mallet, e as verificações de HTML, CSS e YAML pertinentes).
