# Relatório de consolidação técnica

**Gate:** `TECH-CONSOLIDATION`
**Status:** `PASS`
**Data:** 16 de julho de 2026

## Integração entregue

- runner `scripts/run_pipeline.ps1`: ETL → EDA → inferência → verificação, testado em execução limpa ponta a ponta (`.venv`, EXITCODE=0);
- testes unitários, dashboard, contratos e integração cross-component (17 testes no total);
- teste de reconciliação cross-component novo: `tests/integration/test_end_to_end.py` — confere hash do raw contra o contrato, contagem/chaves do processado contra o raw, e os KPIs/segmentação do dashboard contra as tabelas/evidence pack do EDA (dois componentes calculando a mesma métrica de forma independente e concordando);
- smoke test Streamlit headless real via `streamlit.testing.v1.AppTest` em `tests/dashboard/test_app_smoke.py` (carrega `dashboard/app.py` sem exceção e confere os 4 KPIs);
- workflow `.github/workflows/felipe-social-media.yml` **na raiz do repositório** (`ai-master-challenge-main/.github/workflows/`) — é o único local que o GitHub Actions lê; um `ci.yml` havia sido criado por engano em `submissions/felipe-freire/.github/workflows/` (não seria executado nessa posição) e foi removido para não confundir o Publisher (`REV-MINOR-002` resolvido);
- ambiente limpo `.venv-clean` e `requirements-lock.txt` (68 dependências resolvidas), usados pelo workflow via `pip install -r requirements-lock.txt && pip install -e . --no-deps` para instalação determinística;
- documentação de setup, dashboard, contratos, DQ, EDA, estatística e estratégia.

## Evidências

- ambiente limpo (`.venv`): pipeline completo executado via `scripts/run_pipeline.ps1`, EXITCODE=0;
- testes finais: **17 `PASS`** (5 unit, 4 dashboard incl. smoke Streamlit, 2 EDA, 2 inferência, 4 end-to-end);
- Ruff lint: `PASS`; Ruff format: `PASS`;
- dataset: 52.214×34, chaves `id`/`content_id` únicas, hash reconciliado com `docs/contracts/source-data.md`;
- dashboard: 52.214 posts, engagement médio 0,19905454, 42,7357% patrocinados — valores idênticos aos do evidence pack do EDA (testado, não apenas inspecionado).

## CI (`.github/workflows/felipe-social-media.yml`, raiz do repo)

- `quality` (sempre roda, sem dataset, `ubuntu-latest`): instala via lock (`requirements-lock.txt` + `pip install -e . --no-deps`), Ruff lint/format, `pytest tests/unit tests/dashboard` — cobre inclusive o smoke test do Streamlit, pois usa apenas fixtures sintéticas.
- `integration` (condicional, `vars.RUN_FULL_PIPELINE == 'true'` + secrets `KAGGLE_USERNAME`/`KAGGLE_KEY`, `windows-latest`): baixa o dataset via Kaggle CLI, roda o ETL PowerShell, EDA, inferência e a suíte completa (17 testes, incluindo `tests/integration/test_end_to_end.py`).
- Motivo do split: `data/raw/*.csv` e `data/processed/*.csv` são propositalmente ignorados pelo Git (regra global de não commitar dataset grande). CI não deve baixar dados implicitamente nem falhar por ausência de segredos opcionais — por isso o job pesado só roda quando o repositório habilitar a variável e os segredos do Kaggle explicitamente.
- Nota de correção (`REV-MINOR-002`, achado do Reviewer): chegou a existir um `ci.yml` duplicado em `submissions/felipe-freire/.github/workflows/`, criado concorrentemente por engano — o GitHub só lê `.github/workflows` na raiz do repositório, então esse arquivo nunca seria executado. Foi removido; o único workflow válido é o da raiz, descrito acima.

## Incidentes encontrados e corrigidos

1. `python` global apontava para gerenciador sem runtime; runtime 3.10 existente foi localizado.
2. ExecutionPolicy bloqueou `.ps1`; comandos usam bypass por processo, sem alterar política global.
3. Decimal dependia de locale `pt-BR`; serialização tornou-se invariável.
4. Teste de unicidade era lento; substituído por `HashSet`.
5. Matplotlib tentou backend Tk quebrado; EDA usa `Agg` headless.
6. Instalação clean excedeu o timeout do wrapper, mas concluiu em background; estado foi verificado antes dos testes.
7. Um teste de integração apareceu concorrentemente; foi preservado, formatado e passou.

## Handoff

O sistema está tecnicamente pronto para o Executive Writer. Nenhum valor analítico foi alterado na consolidação. Qualquer mudança posterior em dados, fórmulas, evidence records ou estratégia invalida `TECH-CONSOLIDATION` e exige novo pipeline/review.
