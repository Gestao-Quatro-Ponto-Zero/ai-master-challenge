# RC4 DEV — Management Performance Center

Escopo: implementação tática exclusiva da persona Manager. A versão Head aprovada foi preservada.

- Navbar: escolha de região e manager; a escolha do manager ativa a identidade de demonstração no backend.
- Main: comparação regional, KPIs da equipe, ranking descritivo de Win Rate, pipeline ativo e intervenção.
- Aside: vendedores do manager; selecionar um vendedor mostra seus deals priorizados.
- Reatribuição: permanece sujeita às verificações de ownership no servidor e é auditada.

Os indicadores Won/Lost são históricos e não representam o estado atual do pipeline. O score não é probabilidade. O ranking não estabelece causalidade.

Execute `python -m unittest discover -s tests -q` e `python app.py`.
