## Uso dos dados reais

A solução utiliza diretamente os datasets fornecidos:

- sales_pipeline.csv → oportunidades
- accounts.csv → dados das empresas

Os dados são integrados via merge pela coluna `account`, permitindo enriquecer cada oportunidade com contexto de negócio.

---

## Lógica de scoring

A lógica foi construída a partir de proxies reais de decisão comercial:

- ICP → baseado na receita da empresa
- Dor → inferida pelo valor do deal (`close_value`)
- Timing → tempo entre `engage_date` e `close_date`
- Estágio → avanço no funil (`deal_stage`)

O objetivo não é prever fechamento com ML, mas **priorizar oportunidades acionáveis no dia a dia de vendas**.

---

## Como executar

1. Instalar dependências:
```bash
pip install pandas

## Exemplo de saída

Após executar o script, as oportunidades são priorizadas:

| opportunity_id | account | score | priority |
|----------------|--------|------|----------|
| 1023 | TechCorp | 87 | Alta |
| 2045 | RetailCo | 62 | Média |
| 3099 | SmallBiz | 34 | Baixa |
