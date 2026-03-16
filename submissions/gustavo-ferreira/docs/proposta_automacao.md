# Proposta de Automação com IA — Challenge 002

## Arquitetura de Roteamento em 4 Níveis

### 🟢 Nível 1 — Auto-resolve (~25% dos tickets)
- **Quando:** Perguntas de FAQ, consultas de status, dúvidas sobre produto
- **Como:** IA responde automaticamente via base de conhecimento
- **Tipos:** Product inquiry, Billing inquiry (consultas simples)
- **Supervisão:** Nenhuma. Resposta vai diretamente ao cliente
- **Premissa:** Confiança da classificação ≥ 90%

### 🔵 Nível 2 — Agent Assist (~35% dos tickets)
- **Quando:** Problemas técnicos, bugs, configurações, acessos
- **Como:** IA prepara contexto (histórico do cliente, tickets similares) e sugere rascunho de resposta. Agente revisa, edita e envia
- **Tipos:** Technical issue, Access/Account
- **Supervisão:** Agente N1 ou N2
- **Premissa:** IA reduz AHT em ~40% ao eliminar pesquisa manual

### 🟡 Nível 3 — Human Required (~30% dos tickets)
- **Quando:** Reembolsos, disputas financeiras, casos complexos
- **Como:** Ticket vai direto para agente sênior. IA apenas organiza o contexto
- **Tipos:** Refund request, Billing inquiry (disputas)
- **Supervisão:** Agente sênior com autonomia de decisão
- **Justificativa:** Implicações legais (CDC, Procon). Cliente já insatisfeito — IA sem empatia piora

### 🔴 Nível 4 — Escalação Imediata (~10% dos tickets)
- **Quando:** Cliente furioso, ameaça jurídica, cancelamento iminente, suspeita de fraude
- **Como:** Alerta de prioridade máxima para supervisor/retenção. SLA: 2 horas
- **Tipos:** Cancellation request + qualquer ticket com sentimento muito negativo
- **Supervisão:** Supervisor ou especialista de retenção
- **Justificativa:** Risco de churn irreversível. Oportunidade de reter com empatia e flexibilidade

---

## Fluxo Proposto

```
📩 Ticket entra (qualquer canal: email, chat, telefone, social)
     │
     ▼
🤖 IA classifica:
     ├── Categoria (5 tipos)
     ├── Sentimento (positivo / neutro / frustrado / irritado)
     └── Prioridade (baixa / média / alta / crítica)
     │
     ├── Confiança ≥ 90% + FAQ existe ──→ 🟢 Auto-resolve
     │
     ├── Problema técnico / acesso ────→ 🔵 Agent Assist
     │
     ├── Financeiro / reembolso ───────→ 🟡 Human Required
     │
     └── Furioso / cancelamento ───────→ 🔴 Escalação
```

---

## O que NÃO automatizar

| Situação | Por quê |
|----------|---------|
| Cancelamento de assinatura | Oportunidade de retenção. Requer escuta ativa e empatia |
| Reembolso/disputa financeira | Implicações legais. Precisa de verificação e autonomia |
| Cliente muito irritado | IA sem empatia inflama. Humano com gestão de crise é insubstituível |
| Casos com múltiplas interações | Contexto complexo que IA perde entre mensagens |

---

## Impacto Financeiro Projetado

| Métrica | Valor |
|---------|-------|
| Tickets automatizáveis | 2.827 (33.4%) |
| Economia anual | R$ 42.405 |
| Economia mensal | R$ 3.534 |
| AHT economizado/mês | ~78 horas |
