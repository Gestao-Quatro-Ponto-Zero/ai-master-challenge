---
id: K6M2
project: LeadScorer
subject: Distribuição da aplicação como imagem de core do SBCL para arranque sem compilação
author: dcvr@
status: accepted
created: 2026-07-21
updated: 2026-07-21
---


# Contexto (por que a decisão é necessária)

O arranque do conteiner recompilava as dependências Lisp (serapeum, spinneret e a árvore que
delas depende) a cada container novo, atrasando a subida e poluindo o log a ponto de um avaliador
interpretar o ruído como falha. A causa raiz é um descasamento de versão: a imagem base traz o
ASDF 3.3.1, enquanto o lock do projeto fixa uiop-3.3.7. Ao carregar o sistema, o ASDF se
auto-atualiza e força uma cascata de recompilação a partir do uiop; a cascata só cessa quando os
fasls são reescritos pela ASDF já atualizada. Por isso a reutilização do cache de fasls entre o
estágio de build e o de runtime não resolvia: os fasls produzidos no build eram rejeitados no
arranque (a invalidação vem da cascata do upgrade, não da data do arquivo; verificou-se que o
fasl era mais novo que o fonte e ainda assim era recompilado). A execução confiável conforme o
setup documentado, objetivo da Fase 1 da tarefa 6X9H, requer um arranque determinístico e sem
compilação.


# Decisão (o que foi decidido)

A aplicação é distribuída como uma imagem de core do SBCL, gerada com 'sb-ext:save-lisp-and-die'
no estágio de runtime do Dockerfile, após o carregamento de ':leadscorer/web'. O
'container-entrypoint' arranca o provisionamento e o serviço a partir desse core, por caminho
absoluto ('sbcl --core /app/leadscorer.core'), de modo que nenhuma compilação, nem
auto-atualização do ASDF, ocorra no boot. Os scripts de entrada guardam a chamada de
'asdf:load-system' com uma verificação de pacote ('unless (find-package ...)'): quando o sistema
já está presente no core, o carregamento é pulado. Isto é necessário porque manter a chamada
não guardada não é seguro: o 'asdf:load-system' re-verificaria os stamps dos arquivos e, pela
mesma cascata do 'uiop', poderia recompilar as dependências de forma não determinística entre
builds, ainda que o código já esteja no core. A guarda preserva o uso em desenvolvimento (sem
core), no qual o pacote não existe e o carregamento ocorre normalmente.


# Alternativas consideradas (o que mais foi ponderado)

- Copiar o cache de fasls do estágio de build para o runtime (estado original): rejeitada. Os
  fasls produzidos no build são rejeitados no arranque pela cascata de auto-atualização do ASDF,
  de modo que a recompilação recorre a cada container novo.
- Compilar no próprio estágio de runtime e confiar no cache de fasls: rejeitada. Sofre a mesma
  cascata: os fasls assados no build ainda são invalidados a cada sessão nova de SBCL no
  conteiner.
- Alinhar as versões de ASDF e uiop (fixar um uiop compatível com o ASDF da base ou atualizar o
  ASDF na imagem base): rejeitada para o MVP. Mexe nas dependências fixadas e acopla-se à
  compatibilidade da imagem base, o que é mais frágil do que congelar o estado já carregado, sem
  atacar a raiz de forma robusta.
- Gerar um executável autônomo ('save-lisp-and-die' com ':executable t'): diferida. O core não
  executável reaproveita o binário do SBCL da imagem base e preserva os scripts de entrada e a
  configuração dirigida por ambiente, representando a menor mudança que resolve o problema.


# Consequências (o que resulta da decisão)

- Favorável: o arranque passa a ser imediato, determinístico e sem recompilação, tanto no
  primeiro arranque quanto na re-entrada, em qualquer container novo.
- Favorável: elimina a fragilidade da reutilização do cache de fasls entre os estágios de build e
  de runtime, uma classe de problema difícil de diagnosticar.
- Desfavorável: a imagem carrega um core de porte (cerca de 103 MB). Além disso, o cache de fasls
  e a árvore de fontes do qlot copiados ao runtime tornaram-se redundantes em execução, dado que
  o core é autocontido; um enxugamento futuro pode removê-los na mesma camada, sob verificação de
  que nenhum caminho de código os referencie em runtime.
- Desfavorável: o core deve ser regenerado quando o código ou as dependências mudarem, o que já
  ocorre a cada build da imagem.
- Favorável (fail-closed): o arranque acopla-se à presença de 'leadscorer.core'; a sua ausência
  quebra o arranque de imediato, em vez de recair silenciosamente para um caminho que recompila.


# Relações

- supersedes:
- superseded-by:
- related-tasks: 6X9H
