---
id: K2R7
parent:
project: LeadScorer
subject: Allowlist revisado para a varredura de segredos da transcricao
author: dcvr@
priority: low
status: done
created: 2026-07-19
updated: 2026-07-19
---


# Descrição (o que será feito)

Adicionar ao script 'scripts/export-session' um mecanismo de allowlist revisado, que isenta da
varredura de segredos um conjunto pequeno e explicito de literais comprovadamente benignos, tais
como chaves de exemplo publicas documentadas (por exemplo, a chave de exemplo da AWS
'AKIAIOSFODNN7EXAMPLE') e as cadeias sinteticas usadas nas fixtures de teste. Uma vez disponivel,
provisionar a transcricao higienizada da sessao H3V6-1, hoje recusada por conter tais literais.


# Motivações (por que será feito)

A sessao que constroi e testa o proprio scanner contem, por necessidade, cadeias com forma de
segredo em suas fixtures de teste, que o scanner corretamente detecta, fazendo o gate fail-closed
recusar a exportacao da sua transcricao (decisao registrada no worklog de H3V6-1). Scanners de
segredo consagrados (gitleaks, detect-secrets) suportam allowlists de literais benignos
exatamente por esse motivo, sem enfraquecer a deteccao de segredos reais. A ausencia do mecanismo
deixa a transcricao de H3V6-1 sem versao; o worklog permanece o registro canonico no interim.


# Dependências

- blocks:
- blocked-by:
