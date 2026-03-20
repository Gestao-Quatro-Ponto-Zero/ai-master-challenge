# RavenStack — Churn Diagnosis
**Lucas Reis · 2026-03-20 · Para o CEO · Leitura: 2 minutos**

---

## O problema em uma frase

22% das contas saíram. Não há um motivo único dominante — mas há dois segmentos que churnam **2× mais que os outros**: DevTools (31%) e clientes de eventos (30%).

---

## 3 números que definem o problema

| # | Número | O que significa |
|---|--------|----------------|
| **22%** | Taxa de churn anual | 110 de 500 contas perdidas · $229K MRR cancelado |
| **31% vs 16%** | DevTools churna 2× mais que Cybersecurity | OR=2.36× — product-market fit insuficiente para este segmento |
| **$710K** | MRR ativo em contas com múltiplos sinais de risco | Oportunidade de intervenção nas próximas 4 semanas |

---

## O que os dados confirmaram (e o que foi corrigido)

**Confirmado:** O churn é *segmental*, não comportamental. DevTools e canal event têm OR ~2.5× de churn vs os melhores segmentos. Churners usam o produto mais ativamente do que os que ficam — não é abandono, é adequação de produto.

**Corrigido em análise:** Um número anterior ("60.9% saiu por features") estava errado por um bug de denominador no código — o correto é 13.6%. Os motivos declarados são distribuídos: budget (15.5%), pricing (14.5%), features (13.6%), support (12.7%). Nenhum domina. O sinal segmental é mais robusto.

**Descartado:** Não é problema de onboarding (churners usam +3% mais features). Não é problema de suporte (urgent tickets correlacionam com menor churn). Não é problema de plano (Enterprise, Pro e Basic têm churn idêntico de ~22%).

---

## 3 ações — esta semana, este mês, este trimestre

**Esta semana:** CS liga para as **10 contas HIGH risk ainda ativas** ($12,231 MRR em risco). Script: perguntar quais funcionalidades faltam para o fluxo de trabalho, não check-in genérico. Meta: salvar 50% = $73K ARR.

**Este mês:** **Auditoria de product gap em DevTools.** Entrevistar os 35 churners DevTools. Decisão de produto: construir as funcionalidades faltantes, parceria, ou sair do segmento. Potencial: +$25K/mês se DevTools churn cair de 31% para 16%.

**Este trimestre:** **Redirecionar budget de aquisição de evento para partner.** Canal partner: 14.6% churn. Canal event: 30.2% churn. Dobrar investimento em parceiros reduz estruturalmente o churn de novos clientes.

---

## O que NÃO fazer

- ❌ Mais onboarding — churners já usam o produto mais que os retidos
- ❌ Melhorar SLA de suporte como foco de retenção — não é o driver
- ❌ Benefícios por plano Enterprise — churn idêntico nos 3 tiers (p=0.999)

---

*Relatório completo: `solution/executive_report.md` · Código: `solution/agents/` · Auditoria: `process-log/`*
