# Entry 000 — Correções pré-EDA: erros da geração inicial por IA

**Data:** 2026-03-20
**Fase:** Pré-execução (antes de qualquer dado real)
**Tipo:** Correção crítica
**Arquivos corrigidos:** 02_cross_table_agent.py, 03_hypothesis_agent.py, 04_predictive_agent.py

---

## Contexto

Após a leitura do schema oficial (`data/README.md`) e geração do `docs/data_dictionary.md`,
foram identificados 5 erros estruturais nos agents gerados pela IA na sessão anterior.
Nenhum dos erros é sutil — todos causariam falha silenciosa ou resultado incorreto se
o pipeline tivesse sido executado com dados reais.

Esta entry documenta: o erro, o impacto analítico, a correção e a decisão humana por trás dela.

---

## Erro 1 — `usage_duration_min` (coluna inexistente)

**Arquivo:** `02_cross_table_agent.py`, linhas 35–36

**Código errado:**
```sql
AVG(f.usage_duration_min)  AS avg_session_min,
SUM(f.usage_duration_min)  AS total_usage_min
```

**Código corrigido:**
```sql
AVG(f.usage_duration_secs / 60.0)  AS avg_session_min,
SUM(f.usage_duration_secs / 60.0)  AS total_usage_min
```

**Por que a IA errou:** A coluna foi nomeada com "min" na descrição narrativa do schema
("time spent"), e a IA inferiu que a unidade era minutos. O README especifica claramente
`usage_duration_secs` (segundos).

**Impacto se não corrigido:**
- A query falharia com `Column "usage_duration_min" not found` em runtime
- Se silenciosamente passasse (ex: DuckDB retornando NULL), as métricas de duração de sessão
  seriam todas zero → modelo treinado com feature de uso zerada para todos → feature inutilizável

**Decisão humana:** Manter a conversão `/60.0` para preservar a semântica "minutos" que é
mais legível nos relatórios e no SHAP. Float explícito (`60.0`, não `60`) garante divisão
decimal correta em SQL.

---

## Erro 2 — JOIN direto em `churn_events` sem deduplicação

**Arquivo:** `02_cross_table_agent.py`, linhas 51–54 e 78

**Código errado:**
```sql
churn AS (
    SELECT account_id, 1 AS churned, churn_date, churn_reason
    FROM read_csv_auto('ravenstack_churn_events.csv')
)
...
LEFT JOIN churn c ON a.account_id = c.account_id
```

**Código corrigido:**
```sql
churn_deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY churn_date DESC
        ) AS rn
    FROM read_csv_auto('ravenstack_churn_events.csv')
),
latest_churn AS (
    SELECT account_id, 1 AS churned, ... FROM churn_deduped WHERE rn = 1
)
...
LEFT JOIN latest_churn c ON a.account_id = c.account_id
```

**Por que a IA errou:** A IA assumiu relação 1:1 entre accounts e churn_events.
O README informa que `is_reactivation = True` em 10% dos registros, o que significa
que clientes que reativaram e voltaram a churnar aparecem múltiplas vezes.

**Impacto se não corrigido:**
- O `LEFT JOIN` sem `ROW_NUMBER()` produziria múltiplas linhas por conta para os 10% reativados
- O master DataFrame teria ~10% mais linhas que o esperado (500+ contas → 550+ linhas)
- Churn rate calculado estaria inflado artificialmente
- Modelo treinado com linhas duplicadas → data leakage por repetição de exemplos positivos

**Decisão humana:** Usar `ORDER BY churn_date DESC` para ficar com o churn mais recente.
Isso preserva a informação de que a conta churnou (status atual), e o campo `is_reactivation`
ainda é retornado para uso analítico no Agent 03.

---

## Erro 3 — Colunas `company_size` e `contract_value` inexistentes

**Arquivos:** `02_cross_table_agent.py` (linhas 58, 60), `03_hypothesis_agent.py`
(H3, H4, `__main__`), `04_predictive_agent.py` (FEATURE_COLS, `__main__`)

**Código errado:**
```sql
-- 02:
a.company_size,
a.contract_value,
-- 03 H3:
"metric": "company_size"
-- 03 H4:
"metric": "contract_value"
-- 04:
FEATURE_COLS = [..., "contract_value", "company_size", ...]
```

**Código corrigido:**
```python
# 02: substituídos por colunas reais
a.seats,                    # proxy de tamanho de empresa
sa.avg_mrr, sa.total_mrr,  # revenue real, de subscriptions

# 03 H3:
"metric": "seats"           # proxy numérico de tamanho
# 03 H4:
"metric": "avg_mrr"

# 04:
FEATURE_COLS = [..., "avg_mrr", "total_mrr", "seats", ...]
```

**Por que a IA errou:** A IA usou nomes de colunas convencionais de datasets de churn
(como Kaggle Telco Churn) onde `company_size` e `contract_value` são comuns.
O dataset RavenStack não tem essas colunas — tem `seats` (proxy de tamanho) e
`mrr_amount`/`arr_amount` (proxy de valor do contrato) em `subscriptions`.

**Impacto se não corrigido:**
- Query SQL falharia: `Column "company_size" not found in accounts`
- Modelo não treinaria: `KeyError: 'contract_value'` ao indexar o DataFrame
- H3 e H4 nunca rodariam, eliminando duas hipóteses críticas da análise

**Decisão humana:**
- `seats` é proxy razoável para tamanho: mais seats = empresa maior. Limitação: um cliente
  Enterprise com poucas licenças ainda aparece como "pequeno" nessa proxy.
- `avg_mrr` é preferível a `total_mrr` para H4 porque conta com múltiplas subscrições
  teria total_mrr artificialmente alto mesmo sendo SMB.
- Para o modelo, inclui-se ambos (`avg_mrr` e `total_mrr`) pois capturam aspectos distintos.

---

## Erro 4 — `priority = 'high'` ignorando o nível `urgent`

**Arquivo:** `02_cross_table_agent.py`, linha 46

**Código errado:**
```sql
SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) AS n_high_priority
```

**Código corrigido:**
```sql
SUM(CASE WHEN priority IN ('high', 'urgent') THEN 1 ELSE 0 END) AS n_high_priority,
SUM(CASE WHEN priority = 'urgent' THEN 1 ELSE 0 END)            AS n_urgent
```

**Por que a IA errou:** A IA assumiu 3 níveis de prioridade (low/medium/high), padrão
comum em sistemas de tickets. O dataset RavenStack tem 4 níveis: low, medium, high, **urgent**.
"Urgent" é semanticamente o mais grave — exatamente o que mais importa para churn.

**Impacto se não corrigido:**
- Tickets urgentes seriam classificados como "não alta prioridade"
- A feature `n_high_priority_tickets` subestimaria a gravidade real do suporte
- Contas com tickets urgentes (provavelmente as mais próximas do churn) teriam
  contagem de alta prioridade zerada ou subcontada
- O modelo teria um blind spot no nível mais crítico de escalada

**Decisão humana:** Criar duas features separadas:
- `n_high_priority_tickets`: high + urgent (para volume geral de problemas sérios)
- `n_urgent_tickets`: apenas urgent (para capturar a cauda mais extrema, potencialmente
  mais preditiva de churn imediato)

---

## Erro 5 — `satisfaction_score` NULL tratado como dado ausente

**Arquivo:** `02_cross_table_agent.py` (ausência de tratamento), `04_predictive_agent.py`
(sem feature derivada)

**Código errado (implícito):**
```python
# 04 — avg_satisfaction seria usado diretamente, com NaN para contas sem tickets
# ou com imputação de média — ambos incorretos
```

**Código corrigido:**
```sql
-- 02 ticket_agg:
AVG(CASE WHEN satisfaction_score IS NOT NULL
    THEN satisfaction_score END)                              AS avg_satisfaction,
SUM(CASE WHEN satisfaction_score IS NULL THEN 1 ELSE 0 END) AS n_no_satisfaction_response,
CAST(SUM(CASE WHEN satisfaction_score IS NULL THEN 1 ELSE 0 END) AS DOUBLE)
    / NULLIF(COUNT(ticket_id), 0)                           AS satisfaction_no_response_rate
```

```python
# 04 FEATURE_COLS — usa satisfaction_no_response_rate, não avg_satisfaction
# avg_satisfaction é excluída do modelo (conta sem tickets teria NULL e exigiria imputação)
```

**Por que a IA errou:** A IA gerou código que simplesmente ignorou o `satisfaction_score`
ou o teria tratado como missing data convencional. O README indica explicitamente:
`satisfaction_score: 1–5 (null = no response)`.

**Impacto se não corrigido:**
- Imputar NULL de satisfaction com média mascararia o sinal mais importante:
  clientes que não respondem pesquisas estão desengajados
- Contas sem nenhum ticket aberto e contas com tickets não respondidos seriam tratadas
  igualmente (ambas teriam NULL), perdendo a distinção crítica
- O modelo perderia uma das features com maior potencial preditivo

**Decisão humana:**
- `avg_satisfaction`: calculado apenas sobre tickets que têm resposta (para quem responde,
  qual a qualidade percebida)
- `satisfaction_no_response_rate`: proporção de tickets sem resposta por conta (sinal de
  desengajamento)
- `avg_satisfaction` foi **excluída do modelo** porque contas sem nenhum ticket teriam NULL,
  exigindo imputação que distorceria o sinal. `satisfaction_no_response_rate = 0` para essas
  contas é matematicamente correto e semanticamente defensável.

---

## Erros adicionais corrigidos oportunisticamente

| Erro | Arquivo | Correção |
|------|---------|---------|
| `status = 'active'` (coluna inexistente) | 02 | `end_date IS NULL` para subs ativas |
| `plan_name` (coluna inexistente) | 02 | `plan_tier` |
| `churn_reason` (coluna inexistente) | 02 | `reason_code` |
| H6/H7 ausentes | 03 | Adicionadas: auto_renew e preceding_downgrade |
| Sem `validate_binary_hypothesis` | 03 | Adicionada função para flags booleanas |

---

## Resumo: o que a IA errou e o que o julgamento humano corrigiu

| Dimensão | IA (geração inicial) | Humano (correção) |
|----------|---------------------|-------------------|
| Nomes de colunas | Assumiu convenções de outros datasets | Verificou schema oficial |
| Cardinalidade de joins | Assumiu 1:1 para todos os joins | Leu nota de reativações, deduplicou |
| Semântica de NULL | Tratou NULL como missing data | Reconheceu NULL como sinal de comportamento |
| Completude de categorias | Assumiu 3 níveis de prioridade | Leu os 4 níveis, separou "urgent" |
| Feature engineering | Usou colunas de conveniência | Derivou features do schema real |
| Hipóteses | Usou proxies inexistentes | Substituiu por colunas análogas reais |

**Conclusão:** A leitura cuidadosa do schema antes da execução evitou 5 falhas
que teriam invalidado a análise inteira. O pipeline só é confiável porque passou
por revisão humana antes de rodar com dados reais.
