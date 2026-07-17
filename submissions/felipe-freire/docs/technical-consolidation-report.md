# Relatório de consolidação técnica

**Gate:** `TECH-CONSOLIDATION`
**Status:** `PASS`
**Data:** 16 de julho de 2026

## Integração entregue

- runner `scripts/run_pipeline.ps1`: ETL → EDA → inferência → verificação, testado em execução limpa ponta a ponta (`.venv`, EXITCODE=0);
- testes unitários, dashboard, contratos e integração cross-component (22 testes no total após a camada executiva do dashboard);
- teste de reconciliação cross-component novo: `tests/integration/test_end_to_end.py` — confere hash do raw contra o contrato, contagem/chaves do processado contra o raw, e os KPIs/segmentação do dashboard contra as tabelas/evidence pack do EDA (dois componentes calculando a mesma métrica de forma independente e concordando);
- smoke test Streamlit headless real via `streamlit.testing.v1.AppTest` em `tests/dashboard/test_app_smoke.py` (carrega `dashboard/app.py` sem exceção e confere os 4 KPIs);
- workflow de referência validado durante a consolidação e removido do pacote publicado para cumprir a regra do repositório: a PR só pode alterar `submissions/felipe-freire/`;
- ambiente limpo `.venv-clean` e `requirements-lock.txt` (68 dependências resolvidas), usados para instalação determinística via `pip install -r requirements-lock.txt && pip install -e . --no-deps`;
- documentação de setup, dashboard, contratos, DQ, EDA, estatística e estratégia.

## Evidências

- ambiente limpo (`.venv`): pipeline completo executado via `scripts/run_pipeline.ps1`, EXITCODE=0;
- testes finais: **22 `PASS`**, incluindo unidade, dashboard/smoke Streamlit, decisão econômica, EDA, inferência e integração end-to-end;
- Ruff lint: `PASS`; Ruff format: `PASS`;
- dataset: 52.214×34, chaves `id`/`content_id` únicas, hash reconciliado com `docs/contracts/source-data.md`;
- dashboard: 52.214 posts, engagement médio 0,19905454, 42,7357% patrocinados — valores idênticos aos do evidence pack do EDA (testado, não apenas inspecionado).

## Automação validada e decisão de publicação

- O desenho validado separava um job leve (`Ruff` + testes unitários/dashboard) de uma integração condicional com download autenticado do Kaggle e pipeline completo.
- O workflow não integra a entrega final porque GitHub Actions só lê `.github/workflows/` na raiz, enquanto o `CONTRIBUTING.md` determina que candidatos alterem exclusivamente sua própria pasta.
- A capacidade reproduzível permanece nos scripts, lock e testes versionados dentro da submissão. A ausência do workflow publicado é uma decisão de aderência ao contrato do repositório, não ausência de validação.

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
