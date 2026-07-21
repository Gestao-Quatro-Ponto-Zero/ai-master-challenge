---
id: H3V6
parent:
project: LeadScorer
subject: Infraestrutura de higienização e varredura da transcrição de sessão
author: dcvr@
priority: medium
status: done
created: 2026-07-19
updated: 2026-07-19
---


# Descrição (o que será feito)

Implementar o script versionado que exporta a transcrição de cada sessão de trabalho para
'.claude/sessions/' na forma higienizada, preservando os prompts, as decisões e os nomes das
chamadas de ferramenta e descartando ou truncando as saídas de ferramenta, e que submete a
transcrição higienizada a uma varredura de segredos fail-closed antes do commit, abortando a
inclusão quando a varredura acusar achados. O script é a fonte canônica das suas próprias regras.


# Motivações (por que será feito)

O protocolo de encerramento exige a exportação da transcrição higienizada, com varredura de
segredos fail-closed, antes do commit; contudo a infraestrutura não existe, e as sessões vêm
sendo encerradas sem ela, inclusive a sessão 3RJ8-1. A ausência do mecanismo fail-closed é uma
lacuna de segurança, pois a transcrição bruta concentra o risco de exposição de segredos e de
dados sensíveis, e uma lacuna de rastreabilidade da sessão.


# Recursos e dados necessários

- Transcricoes brutas do Claude Code, em JSONL, sob
  '~/.claude/projects/-Users-dradicchi-projects-mvp-leadscorer/*.jsonl'. Cada registro possui um
  campo 'type' entre 'user', 'assistant', 'attachment', 'file-history-snapshot', 'system',
  'mode', 'ai-title' e 'last-prompt';
- Ferramental: 'jq' para a transformacao de fluxo JSONL, 'shellcheck' para a verificacao do Bash
  e 'bats-core' para os testes;
- Convencao ja antecipada no '.gitignore': transcricao bruta como '*.raw.jsonl' (ignorada) e
  higienizada como '*.jsonl' (versionada) em '.claude/sessions/'.


# Plano de trabalho (como será feito)

1. Escrever 'scripts/sanitize-transcript.jq' com as regras de higienizacao chaveadas por 'type':
   preservar prompts, texto, 'thinking' e as chamadas de ferramenta como nome mais argumentos;
   descartar ou truncar as saidas de ferramenta ('toolUseResult' e blocos 'tool_result'), os
   anexos, os snapshots de arquivo e o conteudo das mensagens de sistema;
2. Escrever 'scripts/export-session' em Bash, que resolve a transcricao bruta a partir de um
   identificador de cc-session ou caminho, higieniza via jq, valida o JSONL, varre segredos com
   um ruleset regex embutido e move a saida para '.claude/sessions/' apenas quando a varredura
   passa, abortando fail-closed em caso de achado;
3. Cobrir o comportamento com 'tests/export-session.bats' e uma fixture com segredos plantados em
   uma saida (removida) e em um prompt (dispara a varredura);
4. Verificar com shellcheck e bats, e exercitar o script sobre as transcricoes reais;
5. Registrar o ADR das decisoes consequentes.


# Riscos e ressalvas

- A varredura por regex embutido tem recall inferior ao de um scanner dedicado; o risco e
  mitigado por a higienizacao remover previamente as superficies de maior risco, deixando a
  varredura como rede fail-closed sobre o texto preservado;
- Uma cc-session pode cobrir mais de um worklog, rompendo a correspondencia unívoca pressuposta
  pela convencao de nomenclatura; a resolucao e tratada no provisionamento.


# Dependências

- blocks:
- blocked-by:


# Definição de pronto

- 'scripts/sanitize-transcript.jq' e 'scripts/export-session' existem e sao versionados, e o
  segundo e executavel;
- A higienizacao preserva prompts, texto de assistente, 'thinking' e as chamadas de ferramenta
  como nome mais argumentos, e remove ou trunca saidas de ferramenta, anexos, snapshots e
  conteudo de mensagens de sistema, produzindo JSONL valido ('jq empty' sem erro);
- A varredura de segredos e fail-closed: diante de qualquer achado, o script encerra com estado
  nao-zero e nao deixa arquivo no diretorio versionado, reportando a linha e a regra sem expor o
  segredo;
- 'shellcheck scripts/export-session' nao relata avisos;
- 'tests/export-session.bats' passa, cobrindo a higienizacao, a validade do JSONL, o caminho
  feliz e o caso fail-closed;
- O script foi exercitado sobre ao menos uma transcricao real, com saida higienizada verificada.
