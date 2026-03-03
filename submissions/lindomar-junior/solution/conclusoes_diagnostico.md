# Diagnóstico Operacional — Conclusões e Recomendações
### Challenge 002 · Redesign de Suporte · Customer Support Ticket Dataset

---

## 1. O problema central: 67,3% dos tickets não foram resolvidos

Do total de **8.469 tickets** no dataset:

| Status | Qtd | % |
|---|---|---|
| Closed | 2.769 | 32,7% |
| Open (aguardando agente) | 2.819 | 33,3% |
| Pending (aguardando cliente) | 2.881 | 34,0% |
| **Não resolvidos** | **5.700** | **67,3%** |

**O que isso significa:** dois em cada três tickets estão parados. O backlog não é um pico temporário — é o estado normal da operação. Com 5.700 tickets represados, a equipe está em modo reativo permanente, respondendo ao que aparece em vez de trabalhar o que importa.

Mais grave: **692 tickets Critical + 704 tickets High estão Open** sem nenhuma resposta registrada. A operação não está priorizando urgência — está atendendo na ordem de chegada.

---

## 2. Onde o fluxo trava: a inversão de prioridade

Tempo mediano de resolução por prioridade (tickets fechados):

| Prioridade | Mediana |
|---|---|
| High | **7,28h** ← mais lento |
| Low | 6,98h |
| Critical | 6,55h |
| Medium | **6,18h** ← mais rápido |

**High demora mais que Critical.** Isso não é coincidência estatística — é evidência de que o critério de priorização está quebrado ou sendo ignorado na fila. Tickets marcados como Critical provavelmente recebem atenção especial por visibilidade, enquanto High se acumula sem tratamento diferenciado.

A distribuição de prioridades por categoria de ticket é quase perfeitamente uniforme (~25% em cada nível para todas as categorias), o que confirma que a prioridade está sendo atribuída sem critério baseado na natureza do problema — provavelmente pelo próprio cliente ao abrir o ticket.

---

## 3. O que impacta satisfação — e o que não impacta

**CSAT geral: 2,99/5**

| Nota | % dos tickets fechados |
|---|---|
| 1 (péssimo) | 20,0% |
| 2 | 19,8% |
| 3 (neutro) | 20,9% |
| 4 | 19,6% |
| 5 (ótimo) | 19,6% |

A distribuição é quase perfeitamente plana — 20% em cada nota. Isso não é aleatoriedade: é evidência de que **nenhuma variável operacional isolada explica a satisfação**.

Confirmação estatística:

| Variável | Correlação com CSAT | p-valor |
|---|---|---|
| Tempo de resolução (duration_h) | **-0,001** | 0,947 |
| Idade do cliente | -0,004 | — |

Correlação de -0,001 com p-valor de 0,95 significa: **tempo de resolução não tem relação com satisfação**. O dado mais contundente: clientes com nota 1 e nota 5 passaram em média **7,56h vs 7,91h** em resolução — diferença de 21 minutos numa escala de 5 pontos.

**Piores combinações identificadas:**

| Canal | Tipo | Prioridade | CSAT médio |
|---|---|---|---|
| Phone | Refund request | High | **2,29** |
| Email | Cancellation request | High | **2,53** |
| Social media | Technical issue | High | **2,56** |

O padrão é consistente: **tickets financeiros ou técnicos complexos via canais assíncronos com prioridade High** geram a pior experiência. O cliente que liga pedindo reembolso urgente não quer ser mais rápido atendido — quer o reembolso aprovado.

**Conclusão:** resolver mais rápido não vai mover o CSAT. A alavanca de satisfação é **qualidade da resolução**, não velocidade. Isso tem impacto direto em onde investir automação.

---

## 4. Quanto está sendo desperdiçado

### Backlog atual

| Item | Horas estimadas | Custo (USD $25/h) |
|---|---|---|
| Backlog total (5.700 tickets × 6,7h) | 38.190h | USD $954.750 |
| Critical + Open sem resposta (692 tickets) | 4.636h | USD $115.910 |

> **Nota metodológica:** os 6,7h representam o tempo decorrido entre FRT e TTR (wall-clock time de fila), não o tempo ativo do agente. O custo real de mão de obra por ticket segue o AHT (Average Handling Time) de mercado — entre 15 e 30 minutos por ticket. Os valores acima representam o **custo de oportunidade do backlog represado**, não o custo direto de labor.

### Desperdício recuperável com automação

Usando AHT realista de 20 minutos por ticket:

| Cenário | Taxa auto | Tickets/mês | Horas/mês | USD/mês | USD/ano |
|---|---|---|---|---|---|
| Conservador | 50% | 486 | 162h | $4.050 | $48.600 |
| **Base** | **70%** | **681** | **227h** | **$5.678** | **$68.134** |
| Otimista | 90% | 875 | 292h | $7.288 | $87.450 |

**Maior oportunidade identificada:** 1.071 tickets Open de Product inquiry + Billing inquiry — perguntas sobre produto e cobrança que se repetem de forma padronizada e podem ser resolvidas por FAQ automatizado ou resposta gerada por LLM.

---

## 5. O que automatizar — e o que não automatizar

### ✅ Alto potencial de automação (38,7% do volume)

**Product inquiry + Billing inquiry — 3.275 tickets**

São perguntas sobre funcionamento de produto, informações de fatura, status de pedido. O padrão de resolução é repetitivo, o texto das respostas é curto e uniforme, e não exige julgamento sobre casos individuais. Um sistema de FAQ dinâmico com recuperação semântica (RAG) ou classificação zero-shot resolve 60-70% desses tickets sem intervenção humana.

**Access (account reset, login) — 551 tickets**

Problemas de acesso são o caso clássico de self-service. Redefinição de senha, desbloqueio de conta e recuperação de credenciais têm fluxo determinístico. Automação aqui pode chegar a 85-90% de resolução sem agente, com base em benchmarks de mercado.

### 🟡 Automação parcial (20,6% do volume)

**Technical issue — 1.747 tickets**

Parte dos problemas técnicos segue padrões conhecidos (battery life, product setup, network problem) e pode ser resolvida com troubleshooting guiado ou base de conhecimento. A outra parte exige diagnóstico contextual. Recomendação: automação de **triagem e roteamento** + **resposta sugerida** para o agente, não resposta autônoma. Estimativa de 40% de resolução autônoma, 60% com assistência.

### ❌ Não automatizar (40,7% do volume)

**Refund request + Cancellation request — 3.447 tickets**

Esses dois tipos concentram os piores CSATs e envolvem julgamento, negociação e risco financeiro direto. Automatizar reembolsos sem critério expõe a empresa a fraude e abuso. Automatizar cancelamentos sem tentativa de retenção destrói receita. **Esses tickets precisam de humano** — o papel da IA aqui é triagem e priorização, não resolução.

---

## 6. Fluxo proposto com IA

```
Ticket entra
     │
     ▼
[IA] Classificação automática
  → Categoria (Product/Billing/Technical/Refund/Cancellation)
  → Prioridade recalibrada (baseada em categoria + canal, não auto-declarada)
  → Confiança da classificação
     │
     ├─── Alta confiança + categoria auto-resolvível (Product/Billing/Access)
     │         → Resposta automática gerada por LLM
     │         → Ticket fechado se cliente confirma resolução
     │         → Escalado para agente se cliente não confirma
     │
     ├─── Média confiança ou Technical issue
     │         → Resposta sugerida apresentada ao agente
     │         → Agente aprova, edita ou descarta
     │         → Tempo de resposta reduzido, qualidade mantida
     │
     └─── Baixa confiança ou Refund/Cancellation
               → Roteado diretamente para agente especializado
               → IA fornece contexto: histórico do cliente, produto, prioridade
               → Agente decide, IA não interfere na resolução
```

---

## 7. Resumo executivo para o Diretor de Operações

**Três números que resumem o problema:**
- **67,3%** dos tickets estão parados — a operação está em modo de backlog permanente
- **2,99/5** de CSAT com distribuição uniforme — o problema não é velocidade, é qualidade
- **692 tickets Critical** esperando agente — a triagem de prioridade não está funcionando

**Três ações com maior ROI:**
1. **Automação de Product inquiry + Billing inquiry:** economia estimada de USD $68K/ano no cenário base, com 681 tickets/mês resolvidos automaticamente
2. **Recalibração de prioridade por tipo de ticket:** resolver a inversão High > Critical no tempo de resolução sem custo adicional — só mudança de processo
3. **Self-service de Access (account/login):** potencial de 85%+ de self-resolution, categoria com maior confiança de classificação e menor complexidade de resolução

**O que não fazer:** automatizar Refund e Cancellation. Esses tickets têm o pior CSAT e envolvem decisões financeiras — a IA pode triá-los e contextualizá-los, mas não deve resolvê-los. Automatizar aqui reduz custo operacional de curto prazo e destrói confiança de longo prazo.
