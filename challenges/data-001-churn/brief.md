# Challenge 001 — Diagnóstico de Churn

**Área:** Dados / Analytics
**Tipo:** Análise
**Dificuldade:** Hard
**Time budget:** 4-6 horas

---

## Contexto

Você é o novo AI Master da **RavenStack**, uma plataforma SaaS B2B de colaboração com IA. A empresa tem ~500 contas, opera com modelo de assinatura (mensal e anual), e está preocupada com a retenção.

Nos últimos meses, o churn aumentou. O CEO quer respostas:

> *"Estamos perdendo clientes e não sei por quê. Os números mostram que o churn subiu, mas o time de CS diz que a satisfação está ok. O time de produto diz que o uso da plataforma cresceu. Algo não bate. Preciso de alguém que olhe pra isso com olhos frescos e me diga o que está acontecendo de verdade."*

---

## Dados disponíveis

Cinco datasets públicos disponíveis no Kaggle:

**Dataset:** [SaaS Subscription & Churn Analytics](https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset)

Os arquivos:

| Arquivo | Descrição | Chave |
|---------|-----------|-------|
| `ravenstack_accounts.csv` | 500 contas com indústria, país, canal de aquisição, plano | `account_id` |
| `ravenstack_subscriptions.csv` | 5.000 assinaturas com MRR, plano, upgrades/downgrades | `subscription_id`, `account_id` |
| `ravenstack_feature_usage.csv` | 25.000 registros de uso diário por feature | `subscription_id` |
| `ravenstack_support_tickets.csv` | 2.000 tickets com tempo de resolução e satisfação | `account_id` |
| `ravenstack_churn_events.csv` | 600 eventos de churn com reason codes e feedback | `account_id` |

---

## O que entregar

### Deliverable principal
Um **relatório de diagnóstico** respondendo:

1. **O que está causando o churn?** Não a resposta óbvia — a causa raiz.
2. **Quais segmentos estão mais em risco?** Com dados, não feeling.
3. **O que a empresa deveria fazer?** Ações concretas, priorizadas, com impacto estimado.

### Formato
Livre. PDF, Markdown, Notion, notebook, dashboard — o que melhor comunicar seus findings.

### Critérios de qualidade
- Os dados foram cruzados entre as tabelas? (quem só olhou uma tabela perdeu o ponto)
- Os insights são verificáveis? (mostre os números)
- As recomendações são acionáveis? (não queremos "melhorar a experiência do cliente")
- A análise distingue correlação de causalidade?

---

## Dicas (não obrigatórias)

- Comece entendendo a estrutura dos dados antes de fazer qualquer análise
- Cruze feature usage com churn events — há padrões?
- Olhe os tickets de suporte dos clientes que churnearam vs. os que ficaram
- O CEO disse que "uso cresceu" — isso é verdade pra todos os segmentos?
- Cuidado com conclusões apressadas: nem toda correlação é insight

---

## Lembrete

Envie junto o **process log** mostrando como você usou IA nesta análise. Leia o [Guia de Submissão](../../submission-guide.md).
