# Dashboard

Execute a partir da raiz da submissão:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

O painel responde explicitamente às perguntas obrigatórias do desafio: engagement, patrocínio, audiência, o que não funciona, concentração de esforço, frequência/threshold, quick wins e decisão de ML. Também oferece cruzamentos de audiência por plataforma, tipo de conteúdo e categoria, além de filtros, KPIs reconciliados, tamanho amostral e limitações. Ele não substitui o relatório estatístico.

Testes:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\dashboard
```

## Screenshots

- `outputs/figures/dashboard/dashboard-01-visao-geral.png`;
- `outputs/figures/dashboard/dashboard-02-audiencia.png`;
- `outputs/figures/dashboard/dashboard-03-exploracao.png`.

As imagens são capturadas do dashboard real com Edge headless por `scripts/capture_dashboard.py`.
