# Lógica de Scoring

## Critérios de scoring usados e por quê

### 1) Score da oportunidade (lead/deal)

Objetivo: priorizar deals que combinam maior chance de avanço com maior impacto financeiro.

Critérios:

- Estágio do funil (`Prospecting` ou `Engaging`)
- Valor potencial do deal (`close_value`, ou `sales_price` quando ainda não fechou)
- Histórico da conta (`account_score`)
- Urgência por tempo em pipeline (`days_in_pipeline`)
- Penalidades por dados faltantes (conta/produto)

Racional:

- Deals em `Engaging` recebem mais peso por estarem mais próximos de fechar.
- Deals com maior valor potencial sobem no ranking.
- Conta com bom histórico aumenta a prioridade do deal atual.
- Deal parado há muito tempo recebe urgência para evitar esfriar.
- Falta de dados reduz prioridade por risco operacional.

### 2) Score da conta

Objetivo: capturar a qualidade histórica da conta para apoiar a priorização de novos deals dessa conta.

Critérios:

- `Win rate` histórico (Won / (Won + Lost))
- Ticket médio dos deals ganhos (`avg_won_value`)
- Volume de histórico (`closed_deals`)

Racional:

- Conta que fecha com frequência (win rate alto) merece atenção.
- Contas com ticket médio maior tendem a gerar mais receita.
- Histórico mais robusto aumenta confiança no score da conta.

---

## Copie e cole: scoring da conta

Fonte: endpoint `GET /account-scores` em `g4sales/api.py`.

```sql
ROUND(
	MIN(
		100,
		MAX(
			0,
			45 * COALESCE((won_deals * 1.0) / NULLIF(closed_deals, 0), 0)
			+ MIN(COALESCE(avg_won_value, 0) / 150, 35)
			+ MIN(COALESCE(closed_deals, 0) * 1.0, 20)
		)
	),
	2
) AS account_score
```

Interpretação:

- Até `45` pontos por win rate
- Até `35` pontos por ticket médio
- Até `20` pontos por volume de histórico
- Resultado final limitado entre `0` e `100`

---

## Copie e cole: scoring do lead/oportunidade

Fonte: `frontend/app.py` (`get_score_components` + `calc_priority_score`).

```python
def get_score_components(row: pd.Series) -> dict[str, float]:
	stage_weight = {
		"Prospecting": 35,
		"Engaging": 55,
		"Won": 0,
		"Lost": 0,
	}
	stage_points = float(stage_weight.get(row.get("deal_stage"), 0))

	deal_value = float(row.get("deal_value") or 0)
	value_points = min(deal_value / 200, 25)

	account_score = float(row.get("account_score") or 35)
	account_points = (account_score / 100) * 20

	days_in_pipeline = int(row.get("days_in_pipeline") or 999)
	urgency_points = 0.0
	if days_in_pipeline > 30:
		urgency_points = 15.0
	elif days_in_pipeline > 14:
		urgency_points = 8.0

	account_penalty = 0.0
	if not row.get("account"):
		account_penalty = -10.0

	product_penalty = 0.0
	if not row.get("product"):
		product_penalty = -8.0

	return {
		"stage_points": stage_points,
		"value_points": value_points,
		"account_history_points": account_points,
		"urgency_points": urgency_points,
		"account_penalty": account_penalty,
		"product_penalty": product_penalty,
	}


def calc_priority_score(row: pd.Series) -> float:
	components = get_score_components(row)
	total = sum(components.values())
	return round(max(0, min(total, 100)), 2)
```

Interpretação:

- Peso base por estágio (`35` ou `55`)
- Até `25` pontos por valor potencial
- Até `20` pontos pelo histórico da conta
- Até `15` pontos por urgência de tempo
- Penalidades por ausência de dados
- Score final limitado entre `0` e `100`
