# Quality Gates UI

Gates de qualidade da trilha de frontend para o snapshot atual (UI shell em JavaScript).

## Contexto
- este repositório não possui pipeline TypeScript/npm ativo neste momento
- o endurecimento equivalente é aplicado por validações de arquitetura, smoke e contrato

## Gates UI adotados
- `python .\scripts\tasks.py ui-quality`
  - executa `scripts/validate_ui_quality.py`
  - executa `pytest` de `tests/test_ui_smoke.py`
- `python .\scripts\tasks.py ui-ci-check`
  - alias operacional para gate local equivalente ao CI da UI

## O que é validado
- `index.html` carrega `app.js` como módulo
- `public/app.js` usa factory (`createOpportunityRepository`)
- `public/app.js` não usa `fetch` direto nem importa fixtures mock
- seleção de modo (`api`/`mock`) centralizada em `repository-factory.js`
- smoke de UI segue verde

## Política
- gate vermelho bloqueia promoção de CRP de UI
- exceções exigem justificativa explícita no `PROCESS_LOG.md`

## CI de frontend
- workflow dedicado: `.github/workflows/frontend-ci.yml`
- documentação operacional: `docs/CI_FRONTEND.md`
