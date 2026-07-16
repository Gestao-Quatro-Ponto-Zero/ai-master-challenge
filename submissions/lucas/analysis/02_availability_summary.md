# Passo 2 — Normalizacao de produto + Disponibilidade de features (deals abertos)

## 1. Normalizacao do mismatch de produto
- Mismatches ANTES da normalizacao: ['GTXPro']
- Mapeamento aplicado: {'GTXPro': 'GTX Pro'}
- Mismatches DEPOIS da normalizacao: []
- Join por produto: 8800/8800 registros casam com products.csv (100.00%)
- **Validado: 100% dos registros de sales_pipeline casam com products.csv apos a normalizacao.**

- CSV original (`../data/sales_pipeline.csv`) NAO foi alterado.
- Versao normalizada salva em `./pipeline_clean.csv` (mesmas colunas, so `product` corrigido) para uso nos proximos passos.

## 2. Disponibilidade de features — deals ABERTOS (Prospecting + Engaging)
- Total de deals abertos: 2089 (Prospecting=500, Engaging=1589)

### Disponibilidade geral (Prospecting + Engaging juntos)
| Feature | Disponivel | % |
|---|---|---|
| sales_agent (pipeline) | 2089/2089 | 100.0% |
| product (pipeline, normalizado) | 2089/2089 | 100.0% |
| account (pipeline, chave) | 664/2089 | 31.8% |
| engage_date (pipeline) | 1589/2089 | 76.1% |
| sector (via account) | 664/2089 | 31.8% |
| revenue (via account) | 664/2089 | 31.8% |
| employees (via account) | 664/2089 | 31.8% |
| office_location (via account) | 664/2089 | 31.8% |
| year_established (via account) | 664/2089 | 31.8% |
| subsidiary_of (via account) | 132/2089 | 6.3% |

### Disponibilidade por estagio (Prospecting vs Engaging)
| Feature | Prospecting % | Engaging % |
|---|---|---|
| sales_agent (pipeline) | 100.0% | 100.0% |
| product (pipeline, normalizado) | 100.0% | 100.0% |
| account (pipeline, chave) | 32.6% | 31.5% |
| engage_date (pipeline) | 0.0% | 100.0% |
| sector (via account) | 32.6% | 31.5% |
| revenue (via account) | 32.6% | 31.5% |
| employees (via account) | 32.6% | 31.5% |
| office_location (via account) | 32.6% | 31.5% |
| year_established (via account) | 32.6% | 31.5% |
| subsidiary_of (via account) | 6.4% | 6.3% |

### Checagem: account presente implica sempre dados de conta completos?
- account presente: 664 | sector presente: 664 | iguais: True

## Conclusao — o que da pra usar de verdade num deal aberto
- **Sempre disponivel (100%)**: sales_agent, product (normalizado), deal_stage.
- **account e features derivadas de conta (sector/revenue/employees/...)**: disponivel em 31.8% dos deals abertos — precisa de fallback nos 1425 deals sem conta.
- **engage_date**: disponivel em 76.1% dos deals abertos — falta em 100% dos Prospecting (por definicao, ainda nao engajou) e presente em 100% dos Engaging.
- Nao propus pesos ainda — so mapeamento do que existe pra decidir depois com que fallback tratar cada gap (account ausente, engage_date ausente em Prospecting).