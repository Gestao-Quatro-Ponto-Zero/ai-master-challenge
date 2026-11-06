# Lead Scorer: setup

Zero dependências. Python 3.9+ e um navegador.

## Usar (vendedor)

Abra `app/index.html` com duplo clique. Pronto.

Se o navegador bloquear arquivo local:

```bash
cd app
python -m http.server 8000
# abra http://localhost:8000
```

## Regerar os scores (RevOps)

Depois de trocar os CSVs em `data/` por um export novo do CRM:

```bash
python scorer.py                    # recalcula app/data.js e ../docs/validacao.md
python scorer.py --csv pipeline.csv # também exporta CSV (; e vírgula decimal, abre no Excel pt-BR)
```

No Windows, se aparecer erro de acentuação no terminal: `set PYTHONIOENCODING=utf-8` antes.

## Testes

```bash
python -m unittest discover tests   # 17 testes, ~2s
```

Cobrem: AUC e intervalo de confiança, shrinkage, curva de sobrevivência (com o off-by-one), estados e ações, ação independente de preço, chance desconhecida sem valor esperado, gate de fatores, backtest sem vazamento e invariantes do dataset real (8.800 deals, 1.291 zumbis, ordenação).

## Estrutura

```
solution/
├── scorer.py         modelo + build (única fonte de lógica)
├── app/index.html    interface (HTML + JS puro, lê data.js)
├── app/data.js       gerado: deals pontuados + motivos
├── data/*.csv        dataset original (Kaggle, CC0)
└── tests/            unittest
```

## O que a tela mostra

- **Filtros** por região, manager e vendedor, em cascata. Ficam salvos no navegador; ação, busca e aba voltam ao padrão a cada visita.
- **KPIs clicáveis**: Contato urgente, Empurrar fechamento, Engaging dentro do ciclo, Zumbis.
- **Foco da semana**: deals ativos ordenados por score. A barra mostra Valor e Momento.
- **Zumbis**: Engaging além do maior ciclo histórico, ordenados por valor. Ação: verificar no CRM.
- **Visão do time**: por vendedor, urgentes, reta final, prospecção, % zumbi, valor esperado e deals sem conta. Clique para abrir o pipeline do vendedor.
- **Detalhe do deal**: score decomposto, motivos em português e histórico (que não pontua).
- **Exportar CSV** da visão atual (deals ou time).
