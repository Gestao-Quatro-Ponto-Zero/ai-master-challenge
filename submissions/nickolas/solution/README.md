## Uso dos dados reais

A solução utiliza diretamente os datasets fornecidos:

- `sales_pipeline.csv` → oportunidades
- `accounts.csv` → contexto das contas

Os dados são integrados via `merge` pela coluna `account`, enriquecendo cada oportunidade com contexto da conta.

---

## Lógica de scoring

A lógica foi construída a partir de proxies observáveis nos dados reais do CRM:

- **ICP** → aproximado pela receita da conta (`revenue`)
- **Impacto financeiro** → aproximado pelo valor do deal (`close_value`)
- **Estágio** → maturidade da oportunidade no pipeline (`deal_stage`)

Nesta versão, removi o proxy de timing baseado em `close_date - engage_date`, porque ele não representa urgência real do cliente. Essa diferença pode refletir apenas uma data planejada ou preenchida no CRM, sem evidência de comportamento comercial.

Também removi `Won` e `Lost` da lógica de priorização operacional. Esses estágios finais podem existir no dataset, mas não devem competir com deals ativos no ranking de próxima ação.

---

## Calibração dos critérios

Os thresholds de `revenue` e `close_value` não são fixos. Eles são calibrados a partir da distribuição real dos dados:

- faixa alta: percentil 75
- faixa intermediária: percentil 40
- faixa baixa: abaixo do percentil 40

Isso reduz arbitrariedade e torna o score mais aderente ao dataset do challenge.

---

## Como executar

1. Instalar dependências:

```bash
pip install -r requirements.txt
