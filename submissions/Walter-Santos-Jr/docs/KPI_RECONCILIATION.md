# G4 Challenge 003 — Reconciliação independente de KPIs RC4 | V3

**Data:** 26/10/2026  
**Baseline:** `G4_Challenge_003_RC4_DEV_Manager_Sector_Light_Fix_Walter-Santos-Jr.zip`  
**Natureza:** auditoria técnica reproduzível, sem alteração do aplicativo homologado.

## 1. Método

Foi executado `g4_rc4_kpi_independent_probe.py` em ambiente isolado, com `G4_DB_PATH` apontando para SQLite temporário. A rotina leu `sales_pipeline_history.csv` e `historical_dimensions.csv` diretamente e apurou contagens, estágios, valores e taxas com lógica independente. Em seguida confrontou os resultados com `executive_intelligence()` e `management_intelligence()` do `app.py` RC4.

Foram testados **126 escopos**: global, regiões, gerentes, setores e combinações válidas região–gerente, região–setor e gerente–setor. Foram feitas **1.638 comparações de indicadores**, sem divergências.

## 2. Resultado quantitativo

| Métrica | Resultado | Situação |
|---|---:|---|
| Registros históricos | 8.800 | Confirmado no CSV |
| IDs distintos | 8.800 | Sem duplicação na fonte |
| Won | 4.238 | Reconciliado |
| Lost | 2.473 | Reconciliado |
| Aberto (Engaging + Prospecting) | 2.089 | Reconciliado |
| Win Rate (Won / (Won + Lost)) | 63,15% | Reconciliado |
| Soma de `close_value` dos Won | 10.005.534,00 | Reconciliado; moeda conforme convenção do dataset |
| Soma de `sales_price` dos Lost | 5.946.468,00 | Exposição de catálogo, **não** receita recuperável |
| Escopos verificados | 126 | 3 regiões, 6 gerentes, 11 setores |
| Comparações de indicadores | 1.638 | 0 divergências |

**Campos confrontados:** Head: deals, won, lost, open, won_revenue, catalog_lost_exposure e win_rate; Manager: deals, won, lost, prospecting, engaging e win_rate. Foram aplicadas as respectivas precisões de arredondamento dos painéis (Head: 2 casas; Manager: 1 casa para Win Rate).

## 3. Distinções metodológicas BIOS

- **Fonte histórica ≠ estado operacional:** o teste acima verifica a fotografia histórica do CSV em SQLite temporário sem fechamentos adicionados. A auditoria transacional V2 cobriu separadamente um fechamento Won persistido e o overlay por ID.
- **Win Rate descritivo ≠ efeito causal:** 63,15% é a proporção histórica dos negócios encerrados, não ganho atribuído ao sistema.
- **Won Value ≠ uplift:** o total histórico de valores Won não mede aumento de receita após adoção.
- **Catalog Lost Exposure ≠ oportunidade recuperável:** preços de catálogo de negócios perdidos não equivalem a receita realizável.
- **Granularidade:** a soma de filtros foi verificada para os 126 escopos selecionados, não para todas as sequências de alteração de filtros na interface nem para todas as combinações possíveis de eventos operacionais.

## 4. Gate e limitações

**PASS:** reconciliação independente de 13 indicadores por escopo nos 126 escopos definidos (1.638 comparações).  
**PASS anterior:** regressão automatizada RC4 101/101 e cenário transacional isolado Won (ver V2).  
**PENDENTE:** navegador automatizado, segurança, concorrência multiusuário, cenários de fechamento Lost em teste transacional independente, simulações combinadas de rework/ownership/closures, e mensuração de impacto em produção.

## 5. Rastreabilidade técnica

- Script reproduzível: `g4_rc4_kpi_independent_probe.py`.
- Implementação auditada: `solution/app.py`, funções `executive_intelligence`, `management_intelligence` e `reconciled_historical_rows`.
- Dados: `solution/data/sales_pipeline_history.csv`, `solution/data/historical_dimensions.csv`.
- Antecedentes: `G4_RC4_CROSS_AUDIT_V1.md`, `G4_RC4_UAT_TRANSACTION_AUDIT_V2.md`.

**Decisão:** os KPIs auditados atendem ao gate quantitativo definido para esta revisão. Preservar RC4 sem alterações funcionais e avançar para revisão documental do Submission Pack.
