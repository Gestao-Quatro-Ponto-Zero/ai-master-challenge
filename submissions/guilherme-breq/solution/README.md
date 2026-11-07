# Lead Scorer — onde focar esta semana

App web que o vendedor abre na segunda de manhã para saber em quais deals focar, com o porquê de cada prioridade.

## Rodar

Requisitos: Node.js 20.9+ (testado em 24.14) e npm.

```bash
cd submissions/guilherme-breq/solution
npm install
npm run build
npm start          # http://localhost:3000
```

Para desenvolvimento: `npm run dev`.

Não precisa de banco, chave de API nem `.env`. Os 4 CSVs do dataset (CC0) estão em `data/` e são lidos no servidor no build. A página sai pré-renderizada como estática.

## Verificar

```bash
npm test           # 24 testes: motor de score, filtros e integração com os CSVs reais
npm run lint
npm run build
```

O teste de integração (`src/lib/data.test.ts`) confere os números do app contra a análise em Python: 2.089 deals abertos, 298 vivos, 1.291 zumbis, 500 em prospecção, ciclo máximo de 138 dias e win rate de 63,2%. Se alguém mudar a lógica e esses números mudarem, o teste quebra.

### Reproduzir a análise

```bash
pip install pandas
cd analysis
python 04_backtest.py              # por que a "chance de ganhar" ficou fora do score
python 05_timing_and_zombies.py    # validação do momento e da regra do zumbi
```

`01` a `03` são a exploração inicial, mantida como evidência do processo.

## Estrutura

```
solution/
├── data/                  CSVs do dataset (fonte única para o app e para a análise)
├── analysis/              Python: exploração (01-03), backtest (04), validação dos sinais (05)
└── src/
    ├── lib/scoring.ts     Motor de score: puro, sem I/O, testado
    ├── lib/data.ts        Lê os CSVs, roda o modelo e cruza com time e contas ('use cache')
    ├── lib/selection.ts   Filtros e indicadores da tela (puro, testado)
    ├── components/        Dashboard, DealRow, TeamTable, HowItWorks
    └── app/page.tsx       Server component: carrega os dados e entrega ao Dashboard
```

## Lógica de scoring (resumo)

| Componente | Peso | O que é | Evidência |
|---|---|---|---|
| Valor | 0–60 | Preço do produto em escala log (US$ 55 → 0, US$ 26.768 → 60) | Ordenar por valor põe ~50% da receita ganha no top 20% |
| Momento | 0–40 | Chance de o deal se decidir nos próximos 30 dias, dada a idade dele | AUC de 0,66 a 0,87 em 3 snapshots fora da amostra |
| Zumbi | fora do ranking | Aberto há mais que o maior ciclo que já fechou (138 d) | 589 zumbis em datas passadas, 0 fecharam depois |
| Chance de ganhar | **não entra** | Vendedor, produto, setor, tamanho da conta e idade | AUC ~0,50 no backtest: é ruído |

Detalhes, decisões e limitações: [`../docs/scoring.md`](../docs/scoring.md).

Para ajustar pesos e limiares, use as constantes no topo de `src/lib/scoring.ts` (`VALUE_WEIGHT`, `MOMENTUM_WEIGHT`, `HORIZON_DAYS`, `WINDOW_ALERT_DAYS`).
