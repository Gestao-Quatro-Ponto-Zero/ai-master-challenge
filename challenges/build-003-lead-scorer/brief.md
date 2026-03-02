# Challenge 003 — Lead Scorer

## Contexto

Você é o novo AI Master da área de **Vendas**. O time comercial tem 35 vendedores que trabalham um pipeline de ~8.800 oportunidades. Hoje, a priorização é feita "no feeling" — cada vendedor decide quais deals focar com base na própria experiência.

A Head de Revenue Operations te chamou e disse:

> "Nossos vendedores gastam tempo demais em deals que não vão fechar. Preciso de algo funcional — não um modelo no Jupyter Notebook que ninguém vai usar. Quero uma ferramenta que o vendedor abra, veja o pipeline, e saiba onde focar. Pode ser simples, mas precisa funcionar."

## Os dados

4 tabelas de um CRM real:

| Arquivo | Descrição | Registros |
|---------|-----------|-----------|
| `accounts.csv` | Contas (setor, receita, tamanho, localização) | ~85 |
| `products.csv` | Produtos e preços | 7 |
| `sales_teams.csv` | Vendedores, gerentes e escritórios regionais | 35 |
| `sales_pipeline.csv` | Pipeline de oportunidades com stage, datas e valor | ~8.800 |

**Fonte:** [CRM Sales Predictive Analytics](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics) (Kaggle, licença CC0)

Baixe o dataset diretamente do Kaggle.

## O que entregar

### 1. Uma solução funcional (obrigatório)

Construa algo que um vendedor possa usar. Exemplos:
- Uma aplicação web onde o vendedor vê o pipeline rankeado por probabilidade de fechar
- Um script que gera um relatório diário "top 10 deals para focar hoje"
- Um dashboard interativo com scoring de leads
- Uma API que recebe dados de um deal e retorna a probabilidade de conversão
- Qualquer coisa que **funcione** e **resolva o problema**

**Requisitos mínimos:**
- Precisa rodar (não é mockup)
- Precisa usar os dados reais do dataset
- Precisa ter alguma lógica de scoring/priorização (não é ordenar por valor)

### 2. Documentação mínima (obrigatório)

- Como rodar a solução (setup instructions)
- Que lógica de scoring você usou e por quê
- Quais limitações a solução tem

### 3. Process log (obrigatório)

Como você usou IA para construir isso. Veja o [Guia de Submissão](../../submission-guide.md).

## Dicas

- O VP não pediu um modelo de ML perfeito. Pediu algo que funcione. Comece simples.
- Deal stage, tempo no pipeline, tamanho da conta e produto são features óbvias. O que mais importa?
- Um scoring simples mas bem apresentado vale mais que um XGBoost sem interface.
- Se usar "vibe coding" (Cursor, Claude Code, Replit, etc.), mostre o processo — é exatamente isso que queremos ver.
- Bonus: se o vendedor entender POR QUE um deal tem score alto, a ferramenta é 10x mais útil.
