# Challenge 001 — Diagnóstico de Churn

**Área:** Dados / Analytics
**Tipo:** Análise
**Time budget:** 4-6 horas

---

## Contexto

Você é o novo AI Master da **RavenStack**, uma plataforma SaaS B2B de colaboração com IA. A empresa tem ~500 contas, opera com modelo de assinatura (mensal e anual), e está preocupada com a retenção.

Nos últimos meses, o churn aumentou. O CEO quer respostas:

> *"Estamos perdendo clientes e não sei por quê. Os números mostram que o churn subiu, mas o time de CS diz que a satisfação está ok. O time de produto diz que o uso da plataforma cresceu. Algo não bate. Preciso de alguém que olhe pra isso com olhos frescos e me diga o que está acontecendo de verdade."*

---

## Dados disponíveis

Cinco datasets públicos disponíveis no Kaggle, conectados por `account_id` e `subscription_id`:

**Dataset:** [SaaS Subscription & Churn Analytics](https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset) (licença MIT)

| Arquivo | O que contém | Registros | Chave |
|---------|-------------|-----------|-------|
| `ravenstack_accounts.csv` | Contas com indústria, país, canal de aquisição, plano, flag de trial | ~500 | `account_id` |
| `ravenstack_subscriptions.csv` | Assinaturas com MRR, ARR, plano, upgrades/downgrades, billing frequency | ~5.000 | `subscription_id` → `account_id` |
| `ravenstack_feature_usage.csv` | Uso diário por feature — contagem, duração, erros, flag de beta | ~25.000 | `subscription_id` |
| `ravenstack_support_tickets.csv` | Tickets com tempo de resolução, first response time, satisfação, escalações | ~2.000 | `account_id` |
| `ravenstack_churn_events.csv` | Eventos de churn com reason code, valor de refund, feedback em texto | ~600 | `account_id` |

---

## O que entregar

### Deliverable principal

Um **relatório de diagnóstico** respondendo:

1. **O que está causando o churn?** Não a resposta óbvia — a causa raiz. Cruze os dados entre tabelas.
2. **Quais segmentos estão mais em risco?** Com dados, não feeling. Identifique contas específicas.
3. **O que a empresa deveria fazer?** Ações concretas, priorizadas, com impacto estimado.

### Formato

Livre. PDF, Markdown, Notion, notebook, dashboard — o que melhor comunicar seus findings.

### Diferencial (não obrigatório)

Nos surpreenda. Exemplos:
- Um modelo preditivo de churn que funcione
- Um dashboard ou visualização interativa
- Uma automação que o time de CS poderia usar amanhã
- Uma análise que ninguém pediu mas que muda a conversa

### Process log (obrigatório)

Envie junto evidências de como usou IA. Leia o [Guia de Submissão](../../submission-guide.md).

---

## Critérios de qualidade

- Os dados foram cruzados entre as 5 tabelas? (quem só olhou uma perdeu o ponto)
- Os insights são verificáveis? (mostre os números)
- As recomendações são acionáveis? (não queremos "melhorar a experiência do cliente")
- A análise distingue correlação de causalidade?
- O CEO (não-técnico) consegue ler e agir?

---

## Dicas

- Comece entendendo a estrutura dos dados antes de fazer qualquer análise
- Cruze feature usage com churn events — há padrões?
- Olhe os tickets de suporte dos clientes que churnearam vs. os que ficaram
- O CEO disse que "uso cresceu" — isso é verdade pra todos os segmentos?
- Nem todo churn tem o mesmo peso: perder uma conta de $50/mês ≠ perder uma de $5K/mês
- Cuidado com conclusões apressadas: nem toda correlação é insight
