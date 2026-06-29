# Dashboard Streamlit

Este dashboard é uma camada de apresentação dos achados principais. Ele não contém a lógica analítica principal, não acessa CSV bruto e não recalcula score de risco.

## Como executar

Execute a partir da raiz do workspace que contém `data/raw/ravenstack` e `ai-master-challenge/`:

```powershell
python -m streamlit run ai-master-challenge/submissions/kadug/solution/dashboard/streamlit_app.py
```

Se os exports ainda não existirem, gere primeiro:

```powershell
python ai-master-challenge/submissions/kadug/solution/analysis/build_exports.py
```

## Entradas

O app lê apenas arquivos em `solution/exports/`:

- `executive_findings.csv`
- `risk_segments.csv`
- `priority_accounts.csv`
- `action_backlog.csv`
- `account_health.csv`
- `usage_growth_tests.csv` opcional, para mostrar crescimento bruto vs. uso em janela válida por segmento
- `root_cause_candidates.csv` opcional, para o gráfico de causa raiz e impacto financeiro
- `churner_comparison.csv` opcional, mantido como evidência auxiliar dos labels de churn

Ele não acessa os CSVs brutos e não recalcula joins, score de risco ou regras de negócio.

## Escopo de UX

- Visual executivo adaptado: navy/off-white/gold, Manrope, cards de baixo raio, botões dourados e espaçamento operacional.
- Faixa de status operacional deixa claro fonte, contrato somente leitura e fila ativa para facilitar integração.
- Visão CEO na primeira dobra: MRR/ARR total exposto, separação entre urgência Crítico/Alto e maior bolso financeiro, gap de label de churn e Top 10 contas por valor.
- Títulos "so what" que contam a conclusão antes da tabela.
- Botões de ação têm microcopy curta, estados visuais de hover/foco/pressão e feedback imediato por toast.
- Gráficos interativos de causa raiz, segmentos, Top contas e backlog por dono/prioridade.
- Botões acionáveis para focar a Mesa CS em retenção imediata, suporte, pricing ou treinamento.
- Segmentos em risco com evidência de uso em janela válida.
- Mesa CS com filtros avançados recolhidos, resumo da fila atual e busca por conta/account_id.
- Em mobile, as abas principais se comportam como navegação inferior para manter Segmentos, Mesa CS, Backlog e Confiança ao alcance do polegar.
- Watchlist de contas com `Next Best Action` operacional.
- Download da watchlist filtrada em CSV para operação do time de CS.
- Drill-down por conta com timeline de signup, subscription, suporte, uso e sinal de churn.
- Backlog de ações por dono, prioridade, impacto esperado e status.
- Tabelas técnicas recolhidas em expanders para não quebrar a narrativa visual.
- Downloads dos CSVs carregados pelo dashboard na aba Confiança.
- Notas de data quality visíveis, com caminho para `solution/analysis/data_quality_report.md`.

## Limitação operacional

O dashboard é um presentation adapter. Se Streamlit não estiver disponível, a solução principal continua verificável via README, exports e `solution/analysis/findings_summary.md`.
