---
id: V7C2
parent: 8W2N
project: LeadScorer
subject: Prototipagem estatica das telas da interface web (Fase 1 de 8W2N)
author: dcvr@
priority: medium
status: done
created: 2026-07-19
updated: 2026-07-19
---


# Descrição (o que será feito)

Produzir os protótipos autônomos em HTML e CSS das telas principais das duas aplicações web
especificadas na concepção ('docs/concepcao-inicial.md'), no padrão 'example-{topic}-{theme}.html'
do processo orientado a exemplos do design system, arquivados em '.claude/assets/examples/'. As
telas cobertas são: identificação por seleção de usuário (do agente e do gerente), tela inicial
do agente (faixa de KPIs e
top tier), lista de disponíveis (destaque do top tier, notas explicativas das dimensões, filtro
de corte, filtros e ordenação), modal de justificativa de engajamento fora do top tier, lista de
engajadas (desfechos won, lost e devolução), tela inicial do gerente (KPIs do time e engajadas do
time) e acompanhamento do time pelo gerente (filtros por agente, produto, conta e data). Os
protótipos adotam exclusivamente o tema escuro (monotema) e as fontes IBM Plex servidas localmente.


# Motivações (por que será feito)

É a Fase 1 do plano da tarefa-pai 8W2N, que exige a decomposição em sub-tarefas atômicas no início
da sua sessão. A prototipagem estática materializa a experiência de uso antes da construção do
servidor, valida a aderência ao design system pelo processo orientado a exemplos e produz artefatos
de referência duráveis para as fases de aplicação (5 e 6 de 8W2N). Esta fase é independente da
persistência (9P4D) e da parametrização, sendo por isso executável em paralelo, o que motiva a sua
separação como sub-tarefa dedicada com registro próprio.


# Recursos e dados necessários

- Especificação funcional: 'docs/concepcao-inicial.md' (estórias, tela inicial, ciclo, modelo
  relacional e aspectos de interface);
- Design system: '.claude/rules/design.md' e os tokens em '.claude/assets/tokens/';
- Referências visuais não normativas: capturas em '.claude/assets/examples/' (outra aplicação de
  mesmo tema escuro);
- Fontes IBM Plex (Sans, Serif, Mono) em 'woff2', a serem provisionadas localmente em
  '.claude/assets/fonts/' e referenciadas por '@font-face'.


# Plano de trabalho (como será feito)

1. Provisionar as fontes IBM Plex ('woff2') em '.claude/assets/fonts/' e um CSS de '@font-face';
2. Estabelecer o esqueleto visual comum (reset, aplicação dos tokens, navbar, cartão de KPI,
   tabela densa, badges de estado) validado contra o design system;
3. Produzir os protótipos, um a um, validando a aderência ao design system a cada tela:
   login, home do agente, disponiveis, justificativa (modal), engajadas, home do gerente e
   acompanhamento do gerente;
4. Validar a responsividade (iPhone 13, 390 px) e a conformidade estética (sem box-shadow, bordas
   de fio de cabelo, algarismos tabulares, sinais explicitos);
5. Verificar o HTML e o CSS pelas ferramentas pertinentes.


# Riscos e ressalvas

- O requisito de autonomia do exemplo (dependências próprias) implica repetir o bloco de estilo
  em cada arquivo; a duplicação é inerente ao processo orientado a exemplos e é aceita;
- 'wordmark-tokens.css', referenciado por 'design.md', não existe no repositório; a aplicação do
  wordmark será derivada da hierarquia tipográfica do design system e a lacuna registrada;
- Os protótipos são estáticos e ilustrativos; os dados exibidos são sintéticos e coerentes com o
  modelo, não oriundos do seed real, que depende de 9P4D.


# Dependências

- blocks:
- blocked-by: M5T2


# Definição de pronto

- Os oito protótipos existem em '.claude/assets/examples/' no padrão 'example-{topic}-dark.html',
  incluindo os logins do agente e do gerente, autônomos (estilos e dados embutidos; fontes IBM
  Plex servidas localmente) e abríveis sem rede;
- Cada protótipo adere ao design system: tema escuro Gray 100, tipografia IBM Plex, ausência de
  efeitos de profundidade, elevação por camadas e bordas de fio de cabelo, algarismos tabulares
  e sinais numéricos explicitos;
- Os protótipos cobrem os elementos especificados na concepção: faixa de seis KPIs, top tier
  destacado, notas explicativas das dimensões, filtro de corte, filtros e ordenação, modal de
  justificativa com limite de dez, desfechos do ciclo e visão de acompanhamento do gerente;
- A responsividade é validada na largura do iPhone 13 (390 px), com colapso da grade de cartões
  e da navegação;
- As verificações de HTML e CSS pertinentes passam.
