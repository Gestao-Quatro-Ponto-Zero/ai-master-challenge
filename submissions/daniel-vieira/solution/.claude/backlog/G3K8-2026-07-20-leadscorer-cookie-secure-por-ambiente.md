---
id: G3K8
parent:
project: LeadScorer
subject: Tornar o atributo Secure do cookie de sessao dirigido por ambiente
author: dcvr@
priority: low
status: done
created: 2026-07-20
updated: 2026-07-20
---


# Descrição (o que será feito)

O cookie de sessao das aplicacoes web, definido em 'src/web/server.lisp' pelo estado de cookie do
Lack, hoje emprega 'HttpOnly' e 'SameSite=Lax', mas mantem o atributo 'Secure' em falso, adequado
ao desenvolvimento sobre HTTP. Tornar o atributo 'Secure' dirigido por ambiente, de modo que seja
habilitado sob TLS na implantacao, sem quebrar o desenvolvimento local sobre HTTP.


# Motivações (por que será feito)

Registrado como endurecimento futuro no worklog da tarefa K9X4, que ergueu a fundacao das
aplicacoes web e a sessao. Em conformidade com o principio de seguranca desde a concepcao, sob
HTTPS o cookie de sessao deve carregar 'Secure' para nao trafegar em canal em claro. Um cookie
'Secure' incondicional, porem, impediria o envio sobre HTTP no desenvolvimento, dai a
parametrizacao por ambiente.


# Dependências

- blocks:
- blocked-by:


# Definição de pronto

- O atributo 'Secure' do cookie de sessao e habilitado quando o ambiente indica implantacao sob
  TLS e permanece desabilitado no desenvolvimento sobre HTTP, por leitura de variavel de ambiente;
- A configuracao segue o padrao de leitura de ambiente ja adotado em 'src/web/config.lisp';
- A verificacao de software aplicavel passa.
