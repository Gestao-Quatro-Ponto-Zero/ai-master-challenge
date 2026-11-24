# Dashboard — Diagnóstico de churn RavenStack

**Publicado:** https://ravenstack-churn.apsolutions-technology-services.workers.dev

Três abas: **Diagnóstico** (achados e previsão), **Sugestões** (o que fazer) e **Dados** (auditoria, mapa e as 500 contas).
Texto em linguagem simples; os números estatísticos ficam em "Detalhe técnico".

O jeito mais simples de regenerar tudo é a skill: `../../skill/diagnostico-churn/scripts/rodar.sh` (veja o SKILL.md).

Site em React + Vite + Recharts com os achados da análise. Os dados vêm de `src/data.json`,
gerado pelos scripts Python (nada é digitado à mão no front).

## Rodar

```bash
# 1. (opcional) regenerar os dados a partir do Kaggle
../scripts/00_download.sh
cd ../..   # pasta da submissão
uv run --with pandas python -I solution/scripts/01_build_dataset.py data/raw solution/outputs docs
uv run --with pandas,scipy,matplotlib python -I solution/scripts/02_correlacoes.py solution/outputs docs
uv run --with pandas,scipy python -I solution/scripts/03_correlacoes_assinatura.py solution/outputs docs
uv run --with pandas,scipy python -I solution/scripts/04_export_dashboard.py data/raw solution/outputs solution/dashboard/src/data.json

# 2. subir o site
cd solution/dashboard
npm install
npm run dev        # http://localhost:5180
```

## Seções

| Seção | Pergunta | Fonte |
|---|---|---|
| Churn subiu? | volume × taxa sobre a base ativa (assinaturas e MRR) | subscriptions, churn_events |
| Uso cresceu? | uso total × uso por assinatura ativa | feature_usage, subscriptions |
| Satisfação ok? | distribuição das notas, incluindo “sem nota” | support_tickets |
| Quem saiu? | as três definições de churn e motivo × comentário | accounts, churn_events |
| Correlações | força de cada variável por categoria, com correção BH | account_360, subscription_360 |
| Segmentos | taxa de churn com IC 95% por indústria, canal, plano, país | account_360 |
| Mapa | Spearman entre todas as variáveis das 5 tabelas | account_360 |
| Auditoria | coerência de chaves e datas entre tabelas | as 5 tabelas |
| Contas | base ligada, com busca, filtro e ordenação | account_360 |
