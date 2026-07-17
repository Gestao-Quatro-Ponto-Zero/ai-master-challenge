# Relatório da fundação técnica

**Gate:** `TECH-FOUNDATION`
**Status:** `PASS`
**Data:** 16 de julho de 2026

## Entregue

- `pyproject.toml` com package, dependências analíticas/dashboard e ferramentas de teste/qualidade;
- ambiente virtual local em `.venv` (ignorado pelo Git);
- pacote `social_media_intelligence` com interface inicial de métricas;
- testes unitários e testes de contrato do dataset;
- `ruff`, `pytest`, coverage config e `.editorconfig`;
- comandos canônicos e troubleshooting em `docs/technical-setup.md`;
- `scripts/check_environment.py` e runner `scripts/verify.ps1`;
- contratos de fonte, dataset analítico e métricas já produzidos no DQ.

## Ambiente validado

- Python 3.10.9;
- pandas 2.3.3; NumPy 2.2.6; SciPy 1.15.3;
- statsmodels 0.14.6; scikit-learn 1.7.2;
- matplotlib 3.10.9; seaborn 0.13.2; Plotly 6.7.0;
- Streamlit 1.56.0; pytest 9.0.3; Ruff 0.15.22.

## Evidência de execução

- environment check: `PASS`;
- testes Python: `5 passed`;
- lint Ruff: `PASS`;
- format check Ruff: `PASS`;
- teste do dataset: `PASS`, 52.214 linhas × 34 colunas.

## Limitações e decisões técnicas

- O comando `python` global apontava inicialmente para um gerenciador sem runtime; foi encontrado Python 3.10.9 fora do PATH e usado apenas para criar `.venv`.
- O ambiente virtual usa `--system-site-packages` para reutilizar bibliotecas locais; consolidação deve gerar um lock limpo antes do CI.
- Scripts PowerShell exigem `-ExecutionPolicy Bypass` por processo devido à política local; a política global não foi alterada.
- CI será criado somente em `TECH-CONSOLIDATION`, após congelamento dos componentes.
- A fundação não define métodos estatísticos, KPIs ou conclusões.
