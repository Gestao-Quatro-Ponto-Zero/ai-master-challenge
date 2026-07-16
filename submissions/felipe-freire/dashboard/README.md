# Dashboard

O painel público oferece temas claro e escuro e interface executiva em Português,
Español e English. Os controles ficam no topo da barra lateral; nomes de campos e
valores técnicos permanecem estáveis para preservar a rastreabilidade da análise.

## Versão pública

**Acesso:** https://felipe-social-media-intelligence.streamlit.app/

A interface usa a identidade visual de referência da G4 — azul-marinho, dourado, creme e Manrope — e inclui a marca no menu lateral. A legenda deixa explícito que se trata de um projeto independente desenvolvido para o Challenge 004.

O app está preparado para o Streamlit Community Cloud. O arquivo de entrada é
`submissions/felipe-freire/dashboard/app.py`; as dependências mínimas estão em
`dashboard/requirements.txt` e a visualização usa um asset Parquet compacto, sem texto livre,
credenciais ou dados pessoais.

Além da auditoria descritiva, a camada executiva traduz a conclusão em ações e permite ao Head de Marketing informar custo, margem e público elegível para calcular o break-even e gerar um briefing de experimento. Os valores são sempre fornecidos pelo usuário; o app não inventa custos, ROI ou causalidade.

Para reconstruir o asset depois de executar o pipeline:

```powershell
.\.venv\Scripts\python.exe scripts\build_dashboard_asset.py
```

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
