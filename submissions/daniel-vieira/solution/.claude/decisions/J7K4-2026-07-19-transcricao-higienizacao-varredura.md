---
id: J7K4
project: LeadScorer
subject: Higienizacao e varredura fail-closed da transcricao de sessao
author: dcvr@
status: accepted
created: 2026-07-19
updated: 2026-07-19
---


# Contexto (por que a decisao e necessaria)

O protocolo de encerramento exige exportar a transcricao de cada sessao de trabalho para
'.claude/sessions/' em forma higienizada, submetida a uma varredura de segredos fail-closed
antes do commit. A transcricao bruta do Claude Code, em JSONL, concentra o risco de exposicao de
segredos e de dados sensiveis, sobretudo nas saidas de ferramenta, nos anexos e nos snapshots de
arquivo. Era necessario decidir a linguagem de implementacao, o mecanismo de varredura, o escopo
do que se preserva e a forma do gate, sob o principio de seguranca desde a concepcao, segundo o
qual um estado inseguro deve ser impossivel de alcancar, nao apenas evitavel.


# Decisao (o que foi decidido)

- A higienizacao e implementada como um filtro 'jq' ('scripts/sanitize-transcript.jq') aplicado
  linha a linha, orquestrado por um invocavel Bash fino ('scripts/export-session'). O jq detem as
  estruturas aninhadas; o Bash restringe-se a orquestracao e ao gate, de modo que a regra de
  reescrever em Common Lisp nao e disparada;
- A varredura de segredos usa um ruleset de expressoes regulares embutido no proprio script, que
  e a fonte canonica das suas regras, sem dependencia de um scanner externo. A cobertura e uma
  linha de base nao exaustiva, e a varredura e a segunda barreira, nao a primeira;
- A higienizacao adota deny-by-default no eixo de tipo de registro: cada tipo conhecido mapeia
  para uma lista explicita de campos preservados, e qualquer tipo novo ou inesperado colapsa para
  um esqueleto minimo, de modo que nenhuma superficie desconhecida passe intacta. Preserva os
  prompts, o texto do assistente, o raciocinio ('thinking') e as chamadas de ferramenta como nome
  mais argumentos de entrada, e descarta ou trunca as saidas de ferramenta ('toolUseResult' e
  blocos 'tool_result'), os anexos, os snapshots de arquivo e o conteudo das mensagens de sistema;
- O gate e fail-closed por construcao: a saida e produzida em arquivo temporario, varrida, e
  movida para o diretorio versionado apenas quando a varredura passa; diante de qualquer achado,
  o script encerra com estado nao-zero, o temporario e removido e nada e deixado no diretorio
  versionado. O reporte informa a linha e a regra, nunca o segredo;
- A transcricao bruta nao e versionada nem copiada para dentro do repositorio; e lida diretamente
  de '~/.claude/projects/'. A forma higienizada ('*.jsonl') e versionada; a bruta ('*.raw.jsonl')
  permanece ignorada pelo controle de versao.


# Alternativas consideradas (o que mais foi ponderado)

- Implementar em Common Lisp com uma biblioteca JSON fixada por qlot: alinhar-se-ia a Common Lisp
  como linguagem de proposito geral, mas introduziria uma nova dependencia versionada e mais
  codigo para uma tarefa que o jq, ja disponivel, resolve nativamente como transformacao de fluxo
  JSONL;
- Delegar a varredura a um scanner dedicado (gitleaks, trufflehog, detect-secrets): ofereceria
  recall superior, mas introduziria uma dependencia externa nao instalada, deslocaria a fonte
  canonica das regras para a configuracao do scanner e adicionaria um ponto de instalacao ao
  fluxo reproduzivel;
- Preservar apenas o nome das chamadas de ferramenta, descartando os argumentos: seria uma
  leitura mais estrita e conservadora do enunciado, mas esvaziaria o valor de rastreabilidade da
  transcricao, que depende de registrar a acao concreta de cada passo.


# Consequencias (o que resulta da decisao)

- Favoravel: zero dependencias novas; regras de higienizacao e de varredura versionadas e
  autocontidas; gate fail-closed que torna um estado inseguro inalcancavel por construcao;
  transcricao util para rastreabilidade, com prompts, decisoes e acoes preservados;
- Desfavoravel: a varredura por regex tem recall inferior ao de um scanner dedicado; mitigado
  porque a higienizacao remove antes as superficies de maior risco, deixando a varredura como
  rede sobre o texto preservado;
- O fail-closed produz recusa diante de falsos positivos, o que e a direcao segura
  (deny-by-default); a decisao sobre um falso positivo e humana, sem override automatico que
  enfraqueceria a garantia;
- O formato do arquivo higienizado e interno e sujeito a mudanca; o worklog permanece o registro
  de referencia da sessao, e a transcricao e anexo de apoio.


# Relacoes

- supersedes:
- superseded-by:
- related-tasks: H3V6
