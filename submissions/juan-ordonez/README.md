# Submissão — Juan Ordonez — Challenge 003 Lead Scorer

## Sobre mim

- **Nome:** Juan Ordonez
- **LinkedIn:** _(preencher antes do PR)_
- **Challenge escolhido:** `build-003-lead-scorer`

---

## Executive Summary

_(A preencher na fase final: 3-5 frases sobre o que foi construído, o que foi descoberto nos dados, e qual é a recomendação principal.)_

---

## Solução

### Abordagem

_(A preencher: como ataquei o problema, por onde comecei, como decompus, o que priorizei.)_

### Resultados / Findings

_(A preencher: achados da exploração, decisões-chave, exemplos de deals scorados.)_

### Recomendações

_(A preencher: o que o time de vendas deveria fazer com a ferramenta.)_

---

## Limitações

### Calibração sem split temporal

O tier do vendedor e a calibração dos buckets são calculados sobre **todo o histórico fechado** do dataset, sem split temporal. Em produção, usaríamos uma **janela móvel** (ex: últimos 90 dias) para evitar que vitórias ou derrotas antigas dominem a avaliação atual do vendedor. Um vendedor que teve um quarter ruim há 18 meses e melhorou não deveria ser penalizado hoje.

A decisão de usar todo o histórico foi consciente: para um exercício offline de 4-6h com ~6.700 deals fechados, split temporal reduziria a amostra por bucket e aumentaria o ruído. O trade-off está documentado aqui para transparência.

### SNAPSHOT_DATE fixa em 2018-01-01

O dataset é estático e cobre 2016-2017. A ferramenta trata `2018-01-01` como "hoje" — é `max(close_date) + 1 dia` do dataset. Em produção, `SNAPSHOT_DATE` seria `datetime.now()` e os cálculos de `days_open` seriam dinâmicos.

### Ausência de sinal de atividade recente

O dataset não contém "última interação", "último update no CRM", ou equivalente. Um deal parado há 60 dias sem update é empiricamente diferente de um deal parado há 60 dias com update recente — mas não temos como distinguir. A ferramenta reconhece apenas `engage_date` e `close_date`, o que limita a precisão de detecção de deals "apodrecendo". Em produção, incluiríamos `last_activity_date`.

### Definição de "combo novo"

`is_new_combo` considera que um combo `(vendedor, conta, produto)` é "novo" se nunca apareceu antes no histórico ordenado por `engage_date`. Inclui deals abertos no passado como histórico (não só fechados), para ser consistente entre o tempo de calibração e o tempo de scoring. Um viés possível: o primeiro deal registrado no dataset pode não ser o primeiro real — pode ser apenas o primeiro no recorte temporal. Sem dados pré-2016, não dá para validar.

---

## Process Log — Como usei IA

> Este bloco é obrigatório. Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| **Claude Code** (Opus 4.6, 1M context) | Exploração dos dados, análise estatística, decisões de arquitetura, refatoração, geração do motor de score, geração do data.js, construção do front. Todo o trabalho técnico foi feito em conversa direta com o modelo. |
| **pandas / numpy** | Análise tabular, joins, agregações, feature engineering. |

### Workflow

_(A preencher com a narrativa completa ao final das etapas. Referência: `process-log/decisoes.md`.)_

### Onde a IA errou e como corrigi

_(A preencher com 2-3 casos concretos: ex. cálculo inicial do `is_new_combo` tinha viés porque considerava só deals fechados; refinamentos no template de `explanation`; etc.)_

### O que eu adicionei que a IA sozinha não faria

_(A preencher: o julgamento de escolher caminho B sobre A e C; a decisão de HTML estático sobre Streamlit; a rejeição de variáveis "óbvias" como setor e região por spread <5pp; a exigência de explicação em linguagem de vendas; etc.)_

---

## Evidências

- [ ] Decisões e achados: `process-log/decisoes.md`
- [ ] Golden file (20 deals de referência): `process-log/golden_deals.md`
- [ ] Evidências do processo (PDF consolidado): `process-log/evidencias-processo.pdf`
- [ ] Código-fonte versionado: `score/`, `web/`

---

## Como rodar

```bash
# Gerar/regerar o data.js a partir dos CSVs
cd submission/score
python score.py           # self-test do motor (valida delta <1pp por bucket)
python build_data.py      # gera ../web/data.js

# Abrir a ferramenta (não precisa de servidor)
open ../web/index.html    # duplo clique também funciona
```

Sem build, sem servidor, sem dependências externas em tempo de execução. Apenas `pandas` e `numpy` em tempo de geração do `data.js`.

**Dataset:** [CRM Sales Predictive Analytics](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics) (licença CC0), incluído completo em `data/` (5 arquivos: `accounts.csv`, `products.csv`, `sales_teams.csv`, `sales_pipeline.csv`, `metadata.csv`).

---

_Submissão enviada em: [data]_
