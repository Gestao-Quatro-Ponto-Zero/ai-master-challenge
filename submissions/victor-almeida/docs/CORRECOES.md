# SPEC CORRECTIONS — Validado contra dados reais em 2026-03-21

**Contexto:** As specs do Lead Scorer foram validadas contra os CSVs reais. Este documento lista TODAS as correcoes necessarias antes de implementar. Cada item tem a spec afetada, o problema exato, e a acao corretiva.

---

## CRITICO-01: `created_date` NAO EXISTE no dataset

**Specs afetadas:**
- `specs/deal_zombie.md` secao 11.1 (usa `deal['created_date']`)
- `specs/scoring_engine.md` secao 5.5 (usa `created_date` em `calculate_days_in_stage`)
- `specs/pipeline_view.md` secao 11.1 (lista `created_date` como coluna esperada)
- `specs/nba.md` secoes 3.3, 8.6 (NBA-03 depende de `dias_no_stage` para Prospecting)
- `specs/deal_zombie.md` secao 8.3 funcao `classify_zombies` (lista `created_date` nos inputs)
- `specs/deal_zombie.md` secao 8.3 funcao `calculate_prospecting_reference` (usa `created_date`)

**Problema:** As colunas reais do `sales_pipeline.csv` sao APENAS: `opportunity_id, sales_agent, product, account, deal_stage, engage_date, close_date, close_value`. NAO existe `created_date`. Deals em Prospecting tem ZERO informacao temporal (engage_date, close_date e close_value sao todos NULL).

**Acao corretiva — aplicar em TODOS os modulos:**

1. **`data_loader.py`**: NAO tentar carregar ou calcular `created_date`. A coluna `days_in_stage` para Prospecting deve ser `NaN`.

2. **`scoring/velocity.py`**: Para `deal_stage == 'Prospecting'`, retornar score fixo de 50.0 (neutro), label `"sem_dados_temporais"`, metadata `{"ratio": None, "reason": "prospecting_sem_data"}`. NAO tentar calcular ratio.

3. **`scoring/deal_zombie.py`**: NAO classificar deals em Prospecting como zombie. A funcao `classify_zombies` deve ignorar Prospecting (is_zombie = False, zombie_severity = None). REMOVER a funcao `calculate_prospecting_reference` — nao ha dados para calcula-la. REMOVER `PROSPECTING_REFERENCE_DAYS` das constantes.

4. **`scoring/nba.py`**: NBA-01 (Deal Parado), NBA-02 (Deal em Risco), NBA-03 (Alto Valor Estagnado) e NBA-ZB (Zumbi) NAO se aplicam a Prospecting. Para Prospecting, apenas avaliar: NBA-04 (Seller Fit), NBA-05 (Conta Problematica), NBA-06 (Prioridade Maxima — adaptar condicao: remover check de `dias_no_stage`). Criar fallback especifico para Prospecting: "Deal em fase inicial de qualificacao. Proximo passo: validar fit e agendar primeiro contato."

5. **`components/pipeline_view.py`**: REMOVER `created_date` da lista de colunas esperadas (secao 11.1). A coluna `dias_no_stage` para Prospecting exibe "—" ou "N/D" na tabela.

---

## CRITICO-02: Nome do campo `sales_price` inconsistente entre specs

**Specs afetadas:**
- `specs/metrics.md` secao 8 usa `sale_price` (sem 's')
- `specs/pipeline_view.md` secao 11.1 usa `product_price`
- `specs/data_model.md` usa `sales_price` (correto — nome real no CSV)

**Problema:** Tres nomes diferentes para o mesmo campo. O CSV real usa `sales_price`.

**Acao corretiva:** Padronizar para `sales_price` em TODOS os modulos. Apos o LEFT JOIN do pipeline com products, a coluna se chama `sales_price`. Nunca usar `sale_price` nem `product_price`.

---

## CRITICO-03: Faixas de score inconsistentes entre Pipeline View e Metrics

**Specs afetadas:**
- `specs/metrics.md` secao 4 define: Critico 0-39, Risco 40-59, Atencao 60-79, Alta 80-100
- `specs/pipeline_view.md` secao 4.1 define: Critico 0-24, Risco 25-49, Atencao 50-74, Alta 75-100

**Problema:** Faixas completamente diferentes para a mesma informacao. O vendedor veria um deal como "Atencao" na tabela e "Alta Prioridade" no grafico.

**Acao corretiva:** Usar UMA unica definicao em `scoring/constants.py`:

```python
SCORE_RANGES = {
    "Critico":          (0, 39),
    "Risco":            (40, 59),
    "Atencao":          (60, 79),
    "Alta Prioridade":  (80, 100),
}

SCORE_COLORS = {
    "Critico":          "#e74c3c",
    "Risco":            "#e67e22",
    "Atencao":          "#f1c40f",
    "Alta Prioridade":  "#2ecc71",
}
```

Ambos `pipeline_view.py` e `metrics.py` importam de `constants.py`. As faixas 0-39/40-59/60-79/80-100 fazem mais sentido estatisticamente dado que o score medio do pipeline ficara entre 30-60.

---

## IMPORTANTE-04: Contradicao sobre correcao do typo `technolgy`

**Specs afetadas:**
- `specs/data_model.md` secao 4.3 diz: "NAO corrigir — manter como esta"
- `specs/filters.md` secao 4.7 diz: "Corrigir na carga de dados (data_loader.py)"

**Problema:** Instrucoes contraditorias.

**Acao corretiva:** O JOIN entre pipeline e accounts usa a coluna `account` (nome da empresa), NAO `sector`. Portanto, corrigir `sector` nao quebra nenhum JOIN. A correcao DEVE acontecer para que o filtro de setor na UI mostre "technology" (legivel) em vez de "technolgy" (typo).

Implementar no `data_loader.py`:
```python
accounts_df['sector'] = accounts_df['sector'].replace('technolgy', 'technology')
```

Atualizar `specs/data_model.md` secao 4.3 para refletir que `technolgy` SERA corrigido (diferente de `Philipines` que NAO sera corrigido pois nao aparece na UI de forma prominente).

---

## IMPORTANTE-05: Numero de zombies com P75 — valor exato

**Spec afetada:** `specs/deal_zombie.md` secao 5 e secao 13

**Problema:** A spec diz "aproximadamente 50%" dos deals Engaging serao zombie com threshold P75. O valor real e **46.9%** (745 de 1.589).

**Acao corretiva:** Atualizar secao 5:
- "Aproximadamente **47%** dos deals Engaging serao classificados como Zumbi com referencia P75"
- Secao 13 (validacao de sanidade): a faixa de 40-70% esta correta, manter.

---

## IMPORTANTE-06: Win Rate KPI precisa de dados historicos

**Spec afetada:** `specs/metrics.md` secao 3.4

**Problema:** O KPI de Win Rate usa "deals fechados no escopo do filtro". Mas o DataFrame principal so contem deals ativos (Prospecting/Engaging). Se o filtro esta aplicado, nao ha Won/Lost para calcular WR.

**Acao corretiva:** A funcao `render_metrics` ja recebe `df_all` (DataFrame completo). Garantir que `df_all` inclua TODOS os deals (Won + Lost + ativos). O calculo de Win Rate deve:
1. Filtrar `df_all` pelo mesmo vendedor/manager/regiao do filtro ativo
2. Calcular WR apenas sobre deals com `deal_stage` in ('Won', 'Lost')
3. Se nenhum filtro de vendedor/manager/regiao estiver ativo, usar WR geral (63.2%)

---

## MELHORIA-07: Deals ativos sem conta — oportunidade de diferenciacao

**Dados reais:** 68.5% dos deals em Engaging (1.088 de 1.589) e 67.4% dos deals em Prospecting (337 de 500) NAO tem conta associada (`account` = null).

**Problema:** Esses deals sao "cegos" — sem setor, sem historico, sem health score. Nenhuma spec trata isso como informacao acionavel para o vendedor.

**Acao corretiva — ADICIONAR aos seguintes modulos:**

1. **`scoring/nba.py`**: Criar nova regra `NBA-07: Deal Sem Conta`:
   - Condicao: `account` is null
   - Prioridade: 4 (baixa, informativa)
   - Template: "Este deal nao tem conta associada no CRM. Associar a conta desbloqueia insights de historico e setor."
   - Tipo: `orientacao`

2. **`components/pipeline_view.py`**: Na coluna "Conta" da tabela, exibir "Sem conta" em cinza italico quando `account` is null (em vez de celula vazia).

3. **`components/metrics.py`**: Adicionar metrica no resumo: "X deals sem conta associada (Y%)" — mostra pro manager o gap de dados.

4. **`components/filters.py`**: No filtro de setor, incluir opcao "Sem setor (deal sem conta)" que filtra por `account.isna()`.

---

## MELHORIA-08: NBA-06 precisa de ajuste para Prospecting

**Spec afetada:** `specs/nba.md` secao 3.6

**Problema:** NBA-06 (Prioridade Maxima) exige `deal_stage == 'Engaging'` E `dias_no_stage <= referencia_engaging`. Isso exclui todos os deals de Prospecting de alto valor, que tambem merecem destaque.

**Acao corretiva:** Criar variante para Prospecting:
```
NBA-06B: Prospecting de Alto Valor
Condicao: deal_stage == 'Prospecting' AND valor_deal >= percentil_75_valor
Template: "Oportunidade de alto valor ({produto}, {valor_formatado}) em Prospecting. Priorizar qualificacao para mover para Engaging."
Prioridade: 2 (alta)
Tipo: oportunidade
```

---

## REFERENCIA: Dados validados contra os CSVs

Para conferencia rapida durante implementacao:

| Metrica | Valor Real |
|---------|-----------|
| Total registros pipeline | 8.800 |
| Prospecting | 500 |
| Engaging | 1.589 |
| Won | 4.238 |
| Lost | 2.473 |
| Accounts | 85 |
| Products | 7 |
| Sales agents | 35 |
| Mediana Won (dias) | 57 |
| P75 Won (dias) | 88 |
| P90 Won (dias) | 106 |
| Mediana Engaging ativos (dias) | 165 |
| Engaging > 2x P75 (176 dias) | 745 (46.9%) |
| Engaging > 2x mediana (114 dias) | 1.403 (88.3%) |
| Win rate geral | 63.2% |
| Seller WR min | 55.0% (Lajuana Vencill) |
| Seller WR max | 70.4% (Hayden Neloms) |
| GTXPro deals no pipeline | 1.480 |
| Deals sem account (Engaging) | 1.088 (68.5%) |
| Deals sem account (Prospecting) | 337 (67.4%) |
| Hottechi losses | 82 |
| Kan-code losses | 72 |
| Max close_value Won | verificar no runtime |
| Max product price | 26.768 (GTK 500) |
| Min product price | 55 (MG Special) |