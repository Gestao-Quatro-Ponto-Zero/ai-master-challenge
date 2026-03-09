# Submissão — Challenge 003: Lead Scorer

**Nome:** Vinicius Vaccari
**LinkedIn:** https://www.linkedin.com/in/vinicius-vaccari-746b30376/
**Challenge:** Build-003 — Lead Scorer (Vendas / RevOps)

---

## Resumo Executivo

Construí uma ferramenta web funcional de priorização de pipeline que pontua ~2.089 deals ativos usando 7 fatores ponderados calibrados com dados históricos de ~6.711 deals fechados (Won/Lost). O scoring é baseado em heurísticas com explainability em dois níveis — o vendedor vê não só o score, mas exatamente por que cada deal recebeu aquela pontuação. A principal descoberta dos dados é que 68,2% dos deals ativos no pipeline não têm conta associada (problema de qualidade de dados do CRM), e que todos os deals ativos estão significativamente além do ciclo típico de fechamento (mediana 57 dias para Won vs 165 dias para ativos) — sinalizando um pipeline que precisa urgentemente de limpeza e foco.

---

## Abordagem

### Tecnologia

Aplicação web pura — HTML + CSS + JavaScript, sem dependências de servidor ou instalação. Funciona com `python -m http.server 8000`. PapaParse via CDN para leitura dos CSVs.

### Lógica de Scoring

Score final de 0–100 composto por **7 fatores ponderados**, todos calibrados com dados históricos de deals Won/Lost:

| Fator | Peso | O que avalia |
|---|---|---|
| Account Fit | 20% | Média ponderada de win rates por setor (50%), faixa de receita (30%) e porte (20%) vs. média histórica |
| Product Performance | 15% | Win rate do produto (60%) + ticket médio histórico (40%) |
| Deal Stage Strength | 20% | Engaging (75pts) vs Prospecting (40pts) — calibrado por conversão histórica |
| Stage Aging Health | 20% | Idade do deal vs. ciclo mediano de deals Won (57 dias) — não-monotônico: janela ideal ≠ mais novo |
| Agent Win Rate | 10% | Taxa de ganho do vendedor centrada simetricamente na média do time |
| Account History | 5% | Deals Won anteriores na mesma conta |
| Expected Value | 10% | Taxa do vendedor × ticket médio do produto (sem dupla-contagem com Fator 2) |

### Priority Buckets

| Score | Bucket |
|---|---|
| 85+ | Foco Imediato |
| 70–84 | Alta Prioridade |
| 50–69 | Trabalhar Esta Semana |
| 30–49 | Monitorar |
| < 30 | Baixa Prioridade |

---

## Resultados

### Dataset (dados reais Kaggle CC0)

| Métrica | Valor |
|---|---|
| Total de deals | 8.800 |
| Deals fechados (Won + Lost) | 6.711 |
| Win rate global | 63,2% |
| Deals ativos pontuados | 2.089 |
| Deals sem conta (dado faltante) | 1.425 (68,2% dos ativos) |

### Descobertas do scoring

- **Win rates são uniformes** entre produtos (60–65%) e setores (61–65%) — o real diferenciador de valor é o ticket do produto (MG Special $55 vs GTK 500 $26.707)
- **Todos os deals ativos são tecnicamente "velhos"** — mediana Engaging ativa = 165 dias vs ciclo mediano de Won = 57 dias. O pipeline tem urgência real de ação
- **Variação relevante de agentes**: range de 55% (Lajuana Vencill) a 70,4% (Hayden Neloms) — o fator de maior discriminação por win rate no dataset

### Interface

- **Top 5 Deals to Act Now** — spotlight clicável dos deals mais urgentes
- **Deals at Risk** — deals com aging crítico que ainda têm score razoável
- **Distribuição por bucket** — visão executiva do pipeline
- **Filtros** por região, manager, vendedor, stage e bucket
- **Busca** por conta, agente, produto ou ID
- **Modal detalhado** — breakdown completo com barra visual por fator e explicação em linguagem natural
- **Export CSV** — lista filtrada exportável
- **Toggle light/dark mode**

---

## Recomendações

1. **Limpeza do pipeline** — 1.425 deals sem conta e ciclos 3–7x acima do normal sugerem que o pipeline ativo acumula deals que nunca foram encerrados. Purgar ou requalificar deals com mais de 300 dias
2. **Obrigar campo de conta no CRM** — 68,2% dos deals ativos sem conta impossibilita avaliação de Account Fit e Account History
3. **Conectar a CRM real** — HubSpot, Salesforce ou Pipedrive via API para dados em tempo real
4. **Treinar modelo supervisionado** — com ~6.700 deals fechados, há dados suficientes para XGBoost/LightGBM com features de interação
5. **Feedback loop** — vendedor confirma se priorização ajudou → melhora calibração dos pesos
6. **Notificações** — alertas por email/Slack para deals que entram no bucket "crítico" (aging > 3× mediana)

---

## Limitações

- **Dataset estático** — CSVs do Kaggle, não conecta a CRM real
- **Data de referência fixa** — usa 2017-12-31 (último close_date de Won) como "hoje"
- **Sem valor real do deal ativo** — close_value só existe para deals fechados; Expected Value usa ticket médio histórico do produto como proxy
- **Win rates uniformes** — variação de apenas 3–5pp entre setores e produtos; scoring baseado em win rate diferencia pouco neste dataset específico
- **Sem persistência** — filtros e configurações resetam ao recarregar
- **Sem ML supervisionado** — scoring por heurísticas calibradas, não modelo treinado

---

## Setup

```bash
# Pré-requisito: Python instalado
cd submissions/vinicius-vaccari/solution
python -m http.server 8000
# Abrir: http://localhost:8000
```

Sem instalação de dependências. PapaParse carregado via CDN.

---

## Estrutura

```
submissions/vinicius-vaccari/
├── README.md                  # Este arquivo
├── solution/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   └── data/
│       ├── accounts.csv
│       ├── products.csv
│       ├── sales_teams.csv
│       └── sales_pipeline.csv
└── process-log/
    └── process-log.md
```
