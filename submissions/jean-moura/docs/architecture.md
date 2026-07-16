# Arquitetura — Lead Scorer

## Stack

- **Frontend/UI**: Streamlit 1.56
- **Processamento**: Pandas 3.0
- **Visualização**: Plotly 6.7
- **Scoring**: Heurístico puro (sem ML)

## Estrutura

```
solution/
├── src/
│   ├── app.py          # Interface Streamlit (3 abas)
│   └── scorer.py       # Motor de scoring + breakdown
├── data/               # CSVs do dataset Kaggle (não incluso)
└── requirements.txt    # Dependências
```

## Scoring (6 fatores)

| Fator | Peso | Descrição |
|-------|------|-----------|
| deal_stage | 30% | Won=100, Engaging=70, Prospecting=30, Lost=0 |
| time_in_stage | 15% | Momentum até 365d, depois decai |
| seller_win_rate | 15% | Histórico do vendedor (fallback: manager) |
| sector_win_rate | 15% | Taxa de conversão do setor |
| product_price | 10% | Normalizado pelo catálogo |
| account_revenue | 15% | Normalizado pelas contas |

Score = Σ(factor_subscore × weight), range 0–100.

## Arquivos de Design

O design completo da solução está em:
`challenges/build-003-lead-scorer/openspec/changes/build-lead-scorer/`

- [proposal.md](../openspec/changes/build-lead-scorer/proposal.md) — O quê e por quê
- [design.md](../openspec/changes/build-lead-scorer/design.md) — Decisões técnicas e riscos
