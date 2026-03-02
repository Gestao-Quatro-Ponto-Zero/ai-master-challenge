# Challenge 002 — Redesign de Suporte

## Contexto

Você é o novo AI Master da área de **Suporte ao Cliente**. A operação atende ~30.000 tickets por ano via email, chat, telefone e redes sociais. O time está sobrecarregado: o tempo médio de resolução é alto, a satisfação do cliente caiu, e o diretor de operações quer saber onde IA pode ajudar.

Ele te passou dois datasets e disse:

> "Quero que você olhe nossos dados de suporte e me diga três coisas: onde estamos perdendo tempo, o que pode ser automatizado com IA, e me mostre que funciona — não quero só um PowerPoint."

## Os dados

Dois datasets complementares:

### Dataset 1 — Métricas operacionais
| Arquivo | Descrição | Registros |
|---------|-----------|-----------|
| `customer_support_tickets.csv` | Tickets com métricas de tempo, prioridade, canal, satisfação, e texto da descrição + resolução | ~30.000 |

**Fonte:** [Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset) (Kaggle, licença CC0)

### Dataset 2 — Texto de tickets reais
| Arquivo | Descrição | Registros |
|---------|-----------|-----------|
| `it_service_tickets.csv` | Tickets de suporte com texto real do chamado e classificação | ~48.000 |

**Fonte:** [IT Service Ticket Classification Dataset](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset) (Kaggle, licença CC0)

Baixe ambos diretamente do Kaggle.

## O que entregar

### 1. Diagnóstico operacional (obrigatório)

Com base no Dataset 1:
- **Onde o fluxo trava?** Identifique gargalos por canal, prioridade, tipo de ticket.
- **O que impacta satisfação?** Quais variáveis mais influenciam o `satisfaction_score`?
- **Quanto tempo/dinheiro estamos desperdiçando?** Quantifique.

### 2. Proposta de automação com IA (obrigatório)

Com base em ambos os datasets:
- **O que automatizar?** Classificação, roteamento, respostas sugeridas, triagem — o que fizer sentido.
- **O que NÃO automatizar?** Nem tudo deve ser delegado para IA. Justifique.
- **Como funcionaria na prática?** Descreva o fluxo proposto.

### 3. Protótipo funcional (diferencial)

Construa algo que demonstre a automação proposta. Exemplos:
- Um classificador de tickets que funcione (script, notebook, app)
- Um sistema de respostas sugeridas baseado no histórico
- Um roteador automático de tickets por categoria/prioridade
- Qualquer coisa funcional que mostre que sua proposta não é teoria

### 4. Process log (obrigatório)

Como você usou IA para chegar aqui. Veja o [Guia de Submissão](../../submission-guide.md).

## Dicas

- O Dataset 1 tem métricas. O Dataset 2 tem texto. O poder está em usar os dois.
- Automatizar 100% do suporte é um red flag, não uma virtude. Saiba onde o humano é insubstituível.
- "Usar NLP para classificar tickets" é genérico. "Classificar tickets em 8 categorias com 92% de acurácia usando embeddings + zero-shot" é específico.
- Se você construir algo, mostre que funciona com dados reais — não com 3 exemplos cherry-picked.
