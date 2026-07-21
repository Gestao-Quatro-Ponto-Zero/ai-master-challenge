---
id: H4C7
project: LeadScorer
subject: Configuracao de parametros de modelo e regras em forma Lisp
author: dcvr@
status: accepted
created: 2026-07-20
updated: 2026-07-20
---


# Contexto (por que a decisão é necessária)

A concepcao ('docs/concepcao-inicial.md') e a subsecao "Stack e Competencias" da CLAUDE.md do
projeto previam YAML (e JSON) como formato dos arquivos de configuracao, e a tarefa R7M4 (Fase 4
de 8W2N) precisa externalizar os parametros do modelo de scoring (pesos, forma de agregacao,
pisos, multiplos) e as regras de negocio do ciclo de engajamento (limite de engajamento, tamanho
do top tier, janela de expiracao, intervalos, ancora do relogio virtual), hoje espalhados como
'defparameter' em 'src/scoring.lisp' e ausentes do codigo.

Adotar YAML introduziria uma nova dependencia de terceiros (um leitor YAML em Common Lisp), o
que, pelas cautelas da CLAUDE.md ao recomendar ferramentas, demanda um registro de decisao
proprio e a avaliacao da maturidade da biblioteca, e amplia a superficie de analise (parser
externo) para um insumo pequeno, estatico e de baixa cardinalidade. O projeto ja tem em Common
Lisp o precedente de leitura segura de dado como valor, sem avaliacao ('parse-number-or-nil' em
'src/model.lisp',
que vincula '*read-eval*' a NIL). A decisao fixa o formato antes de a Fase 4 depender dele.


# Decisão (o que foi decidido)

Os parametros de modelo e as regras de negocio residem em um arquivo de configuracao em forma
Lisp (s-expression), 'config/model.lisp', uma unica plist de palavras-chave versionada. O
carregador ('src/config.lisp') le o arquivo como DADO, nao como codigo: vincula '*read-eval*' a
NIL e '*package*' ao pacote KEYWORD durante a leitura, le uma unica forma, recusa conteudo
residual e nao-listas, e valida cada chave contra um schema de tipos ('*config-schema*'),
recusando chave desconhecida e valor de tipo invalido (fail-closed). As chaves ausentes preservam
o default compilado; a configuracao e a fonte canonica dos valores presentes. Nenhuma dependencia
nova e introduzida.


# Alternativas consideradas (o que mais foi ponderado)

- YAML com uma biblioteca de terceiros. Rejeitada: introduz uma dependencia e a sua superficie de
  parser para um insumo pequeno e estatico, exige avaliacao de maturidade da biblioteca e nao
  oferece beneficio sobre a leitura nativa para dado estruturado simples.
- JSON com uma biblioteca de terceiros. Rejeitada pelos mesmos motivos do YAML; a configuracao e
  mais naturalmente expressa como dado Lisp, que os proprios parametros ja eram no codigo.
- Variaveis de ambiente. Rejeitada: inadequadas para parametros estruturados e tipados (pesos
  reais, palavras-chave de enum como a forma de agregacao); o ambiente ja e reservado a
  configuracao operacional e a segredos ('src/db.lisp', 'src/web/config.lisp').
- Manter apenas os 'defparameter' compilados, sem arquivo externo. Rejeitada: nao satisfaz o
  requisito de externalizar os parametros lidos pela aplicacao.


# Consequências (o que resulta da decisão)

- Nenhuma dependencia nova; a leitura usa o leitor nativo, e a configuracao passa a ser dado na
  linguagem primaria do projeto, coerente com os parametros que ja viviam como 'defparameter'.
- Seguranca por construcao: '*read-eval*' NIL desarma a avaliacao em tempo de leitura (o '#.' de
  um fixture provoca erro, coberto por teste), o pacote KEYWORD evita internar simbolos em pacote
  de producao, e a validacao por schema e fail-closed contra erro de digitacao e tipo invalido.
- Desvia da clausula descritiva da CLAUDE.md que lista YAML e JSON como formatos de configuracao;
  o desvio e tratado como dado Lisp da aplicacao, nao um arquivo de configuracao da classe
  YAML/JSON, e fica registrado por este ADR. A concepcao foi retificada para refletir o formato.
- O arquivo tem sintaxe Lisp, menos familiar a editores nao-Lisp que o YAML; em contrapartida, sua
  validade e imposta pelo carregador e por um teste de carga, dispensando um linter externo
  (nao ha equivalente a 'yamllint' para o formato).
- Estabelece a convencao de configuracao-como-dado-Lisp para parametrizacoes futuras do projeto.


# Relações

- supersedes:
- superseded-by:
- related-tasks: R7M4, 8W2N, D2K9
