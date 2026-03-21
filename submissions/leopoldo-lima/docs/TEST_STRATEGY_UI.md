# Test Strategy UI

Estratégia de testes do frontend no snapshot atual (UI shell em HTML/CSS/JS).

## Objetivo
Proteger os comportamentos que sustentam a demo e a integração com backend.

## Suítes ativas
- `tests/test_ui_smoke.py`
  - presença de arquivos e wiring principal UI/API
  - validação de rota raiz e recursos estáticos
- `tests/test_ui_front_coverage.py`
  - estados críticos do dashboard (loading, vazio, erro, not found, cancelamento)
  - persistência de seleção e acessibilidade de teclado
  - controles de drawer
  - contrato mínimo das fixtures mock

## Comandos
```powershell
python .\scripts\tasks.py ui-tests
python .\scripts\tasks.py ui-quality
python .\scripts\tasks.py ui-ci-check
```

## O que constitui regressão de UI
- remoção de estados explícitos de erro/vazio/loading
- quebra da seleção de linha ou da navegação por teclado
- vazamento de fixtures mock para camada de apresentação
- quebra de markup essencial de tabela/drawer

## Limitações conhecidas
- não há runner E2E de browser real neste snapshot
- validações de UI usam smoke + cobertura estrutural de código/markup
