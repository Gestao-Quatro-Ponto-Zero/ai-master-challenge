---
id: F2K9
parent:
project: LeadScorer
subject: Versionar o app.css por hash para dispensar hard-refresh apos deploy
author: dcvr@
priority: low
status: done
created: 2026-07-20
updated: 2026-07-20
---


# Descrição (o que será feito)

Versionar o ativo de estilo 'app.css' no atributo 'href' do link, por hash de conteudo ou
query-string (por exemplo, '/assets/app.css?v=<hash>'), de modo que uma alteracao do CSS seja
buscada automaticamente pelo navegador apos um deploy, sem exigir hard-refresh por aba. O link e
emitido em 'src/web/render.lisp' (a forma '(:link :rel "stylesheet" :href "/assets/app.css")').


# Motivações (por que será feito)

Registrado como debito menor nao bloqueante no worklog da tarefa N7B2 (aplicacao do gerente):
como cada aplicacao web e servida em uma porta distinta (origem distinta), o navegador cacheia o
'app.css' por aba e uma mudanca de CSS exige hard-refresh manual para aparecer. O versionamento
por hash resolve o cache-busting em deploys futuros. Impacto atual baixo (o ativo muda apenas
entre versoes), dai a prioridade baixa.


# Recursos e dados necessários

- 'src/web/render.lisp' (emissao do link do estilo) e 'src/web/static/app.css' (o ativo);
- A middleware de ativos estaticos do Lack, que serve '/assets/' ignorando a query-string, de modo
  que '?v=<hash>' resolva o mesmo arquivo;
- A CSP 'style-src 'self'', com a qual a query-string e compativel (a origem nao muda).


# Plano de trabalho (como será feito)

1. Computar um identificador de versao estavel do 'app.css' (hash de conteudo lido uma vez, ou um
   carimbo de versao do sistema) e expor uma funcao auxiliar que o forneca;
2. Emitir o 'href' com o sufixo de versao em 'render.lisp';
3. Cobrir por teste que o markup renderizado inclui o sufixo de versao e que o ativo continua
   resolvendo sob a CSP; verificar a camada web (compilacao sem avisos, Parachute, 'mallet').


# Riscos e ressalvas

- Debito de baixo impacto: afeta apenas a experiencia de atualizacao de CSS entre versoes, nao a
  funcionalidade. Nao priorizar acima de itens que afetam correcao ou seguranca.


# Dependências

- blocks:
- blocked-by:


# Definição de pronto

- O 'href' do 'app.css' carrega um sufixo de versao derivado do conteudo (ou de um carimbo de
  versao), de modo que uma alteracao do CSS seja buscada sem hard-refresh;
- O comportamento esta coberto por teste e a verificacao da camada web passa.
