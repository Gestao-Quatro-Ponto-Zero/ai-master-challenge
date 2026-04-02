# Challenge 003 — Lead Scorer

**Área:** Vendas / RevOps
**Tipo:** Build (construir solução funcional)
**Time budget:** 4-6 horas

---

## Contexto

Você é o novo AI Master da área de **Vendas**. O time comercial tem 35 vendedores distribuídos em escritórios regionais, gerenciados por managers, trabalhando um pipeline de ~8.800 oportunidades. Hoje, a priorização é feita "no feeling" — cada vendedor decide quais deals focar com base na própria experiência e intuição.

A Head de Revenue Operations te chamou e disse:

> *"Nossos vendedores gastam tempo demais em deals que não vão fechar e deixam oportunidades boas esfriar. Preciso de algo funcional — não um modelo no Jupyter Notebook que ninguém vai usar. Quero uma ferramenta que o vendedor abra, veja o pipeline, e saiba onde focar. Pode ser simples, mas precisa funcionar."*

Este é o challenge mais "mão na massa". O deliverable principal é **software funcionando** — não um documento.

---

## Dados disponíveis

Quatro tabelas de um CRM, todas interconectadas:

**Dataset:** [CRM Sales Predictive Analytics](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics) (licença CC0)

| Arquivo | O que contém | Registros | Campos-chave |
|---------|-------------|-----------|-------------|
| `accounts.csv` | Contas clientes — setor, receita, número de funcionários, localização, empresa-mãe | ~85 | `account` |
| `products.csv` | Catálogo de produtos com série e preço | 7 | `product` |
| `sales_teams.csv` | Vendedores com seu manager e escritório regional | 35 | `sales_agent` |
| `sales_pipeline.csv` | Pipeline completo — cada oportunidade com stage, datas, vendedor, produto, conta e valor de fechamento | ~8.800 | `opportunity_id` → liga tudo |

### Estrutura dos dados

```
accounts ←── sales_pipeline ──→ products
                   ↓
              sales_teams
```

O `sales_pipeline.csv` é a tabela central. Cada registro é uma oportunidade com:
- `deal_stage`: Prospecting, Engaging, Won, Lost
- `engage_date` / `close_date`: timeline do deal
- `close_value`: valor real de fechamento (0 se Lost)

---

## O que entregar

### 1. Solução funcional (obrigatório)

Construa algo que um vendedor possa usar. Não importa a tecnologia — importa que funcione.

**Exemplos de soluções válidas:**
- Aplicação web (Streamlit, React, HTML+JS, qualquer coisa)
- Dashboard interativo (Plotly Dash, Retool, Metabase)
- CLI tool ou script que gera relatório priorizados
- API que recebe dados de um deal e retorna score + explicação
- Planilha inteligente com fórmulas de scoring
- Bot que envia prioridades por Slack/email

**Requisitos mínimos:**
- Precisa **rodar** (não é mockup, wireframe ou PowerPoint)
- Precisa usar os **dados reais** do dataset
- Precisa ter **lógica de scoring/priorização** (não é só ordenar por valor)
- O vendedor precisa entender **por que** um deal tem score alto ou baixo

### 2. Documentação mínima (obrigatório)

- **Setup:** Como rodar a solução (dependências, comandos, URL)
- **Lógica:** Que critérios de scoring você usou e por quê
- **Limitações:** O que a solução não faz e o que precisaria pra escalar

### 3. Process log (obrigatório)

Evidências de como você usou IA para construir. Leia o [Guia de Submissão](../../submission-guide.md).

Este challenge é especialmente interessante para quem usa "vibe coding" — Cursor, Claude Code, Replit Agent, v0, etc. **Mostre o processo.**

---

## Critérios de qualidade

- A solução **funciona de verdade**? Dá pra rodar seguindo as instruções?
- O scoring faz sentido? Usa as features certas? Vai além do óbvio?
- O vendedor (não-técnico) consegue usar e entender?
- A interface ajuda a tomar decisão ou só mostra dados?
- O código é limpo o suficiente pra outro dev dar manutenção?

---

## Dicas

- A Head de RevOps não pediu ML perfeito. Pediu algo **útil**. Comece simples, itere.
- Deal stage, tempo no pipeline, tamanho da conta, produto e vendedor são features óbvias. O que mais importa? Olhe os dados.
- Um scoring baseado em regras + heurísticas, bem apresentado, vale mais que um XGBoost sem interface.
- **Explainability ganha.** Se o vendedor entender POR QUE o deal tem score 85, a ferramenta é 10x mais útil que um número sem contexto.
- Pense no uso real: o vendedor abre isso na segunda-feira de manhã. O que ele precisa ver?
- Bonus: se a solução tiver filtro por vendedor/manager/região, fica imediatamente mais útil.
