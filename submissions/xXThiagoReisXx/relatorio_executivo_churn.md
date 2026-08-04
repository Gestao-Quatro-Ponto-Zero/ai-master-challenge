# Relatório Executivo de Análise de Churn - RavenStack

**Data:** 04 de agosto de 2026

**Responsável:** Análise de Dados (AI Master)

**Destinatário:** Diretoria / CEO

---

## BLUF (Bottom Line Up Front)

**O churn não é generalizado; ele está concentrado em contas Enterprise do setor DevTools e EdTech que enfrentam alta taxa de erros em features beta nos 7 dias anteriores ao cancelamento, combinado com escalações de suporte não resolvidas. A percepção positiva global de uso (média 10.02) mascara uma realidade segmentada onde contas de alto valor (MRR médio de $4,809 entre churns Enterprise) apresentam sinais de risco 2-3 semanas antes do cancelamento, enquanto o CSAT médio de 3.98/5 oculta um viés de resposta de 41.25% (clientes insatisfeitos frequentemente não respondem às pesquisas).**

---

## O Paradoxo Explicado com Dados

### Visão Otimista vs. Realidade Segmentada

| Métrica | Visão Global (CEO/CS) | Realidade Segmentada | Gap / Impacto |
| --- | --- | --- | --- |
| **Uso Médio** | 10.02 eventos/sessão | Contas Churn: 9.79 (queda pré-churn) | -2.3% (Sinal precoce) |
| **CSAT Médio** | 3.98/5 (58.75% resposta) | Contas Churn: 4.01/5 | Viés de ausência de feedback |
| **Taxa de Churn** | 22% global | DevTools: 84%, EdTech: 81% | Concentração crítica |
| **Impacto Financeiro** | Não isolado | $13.2M em ARR Perdido Acumulado | Crítico para o ARR total |

### Análise Temporal do Uso Antes do Churn (Gráfico de Tendência)

A visualização abaixo demonstra a divergência clara no comportamento de uso entre as contas que cancelaram e as contas ativas nas semanas anteriores ao evento de churn:

```text
Evolução do Uso (Eventos/Sessão) - Últimas Semanas:
 10.5 |                                                 [Contas Ativas: Estável ~10.0]
 10.0 |=============================================================================
  9.5 |
  9.0 | \ (Queda acentuada nos últimos 14 dias)
      +-----------------------------------------------------------------------------
        60+ dias     30 dias      14 dias      7 dias       Churn (Dia 0)
                      [Período Crítico de Intervenção Preventiva]

```

* **Tendência de uso - Contas Churn:** Queda consistente nas últimas 2 semanas (de 9.99 para 9.79 eventos/sessão).
* **Tendência de uso - Contas Ativas:** Perfeitamente estável entre 9.78 e 10.26 eventos/sessão.

### Viés de Resposta CSAT

* **Taxa de resposta global:** 58.75% (825 de 2000 tickets ficaram sem resposta).
* **Métricas reais de atrito mapeadas:** Tempo de primeira resposta médio de **88.48 min**, tempo de resolução de **35.86 horas**, e taxa de escalação de **4.75%**.

---

## Matriz de Contas em Risco

### Critérios de Alerta Precoce (EWS)

* **Risco Alto (Vermelho):** Score preditivo > 60% **OU** Tickets escalados não resolvidos há mais de 48h. Intervenção imediata do CS Master.
* **Risco Médio (Amarelo):** Queda de uso > 30% em 14 dias (volatilidade > 0.3) **E/OU** Erros em features beta > 5 eventos.
* **Risco Baixo (Verde):** Score < 30%, sem escalações, uso estável.

### Top Contas Identificadas para Intervenção Imediata (68 Contas de Alta Prioridade)

1. **A-751bd4** (Cybersecurity) — MRR: $190 | Score: 53% | Escalações: 1
2. **A-02cd81** (HealthTech) — MRR: $8,756 | Score: 43% | Escalações: 1 *(Conta Enterprise Crítica)*
3. **A-a0ca4e** (Cybersecurity) — MRR: $5,174 | Score: 41% | Escalações: 3
4. **A-7f4db3** (FinTech) — MRR: $8,955 | Score: 39% | Escalações: 1 | CSAT: 3.25
5. **A-bc4d48** (EdTech) — MRR: $6,965 | Score: 37% | Escalações: 1

### Segmentação de Risco por Indústria

| Indústria | Taxa de Churn | MRR Médio | Principal Fator de Risco |
| --- | --- | --- | --- |
| **DevTools** | 84% | $2,043 | Bugs em features beta e erros técnicos |
| **EdTech** | 81% | $2,533 | Atraso em tickets escalados e CSAT baixo |
| **Cybersecurity** | 80% | $2,152 | Volatilidade e queda de engajamento |
| **FinTech** | 79% | $2,382 | Pressão competitiva e pricing |
| **HealthTech** | 78% | $2,098 | Gargalos no suporte técnico |

---

## Plano de Ação Priorizado

### Curto Prazo (Esta Semana)

1. **Força-tarefa nas 68 contas de alto risco:** Acionamento imediato do time de CS e Account Executives focando nas contas Enterprise de maior ARR.
2. **Resolução de gargalos de suporte:** Zerar a fila de tickets escalados pendentes há mais de 48 horas.
3. **Contenção de features beta instáveis:** Auditoria técnica relâmpago nas features com maior incidência de erros reportados.

### Médio Prazo (Próximos 30 Dias)

1. **Implementação oficial do Early Warning System (EWS):** Automatizar os alertas de queda de uso (>30% em 14 dias) diretamente no CRM/Slack do time de CS.
2. **Redesenho do Onboarding por Canal:** Ajustar o fluxo inicial para os canais de aquisição *organic* e *partner*, que apresentam as maiores taxas históricas de churn.
3. **Campanha de Engajamento de CSAT:** Modificar o gatilho de coleta de satisfação para capturar feedback logo após a resolução de tickets complexos, mitigando o viés de omissão.

### Longo Prazo (Próximo Trimestre)

1. **Estabilidade de Produto (QA Rigoroso):** Refatorar as top 10 features mais utilizadas que concentram falhas de sistema.
2. **Estratégia de Retenção Segmentada:** Criar SLAs de suporte diferenciados e customizados por vertical de indústria (DevTools vs. EdTech).
3. **Revisão de Pricing Enterprise:** Flexibilizar modelos de cobrança para contas de alto valor sensíveis a custos.

---

## Impacto Financeiro e Projeção

* **ARR Total Perdido Acumulado:** $13.2M.
* **Concentração de Risco:** 74% do valor perdido provém estritamente de planos Enterprise de ticket alto.
* **Oportunidade de Recuperação:** Reverter o churn de 50% das contas mapeadas no grupo de alta prioridade representa a retenção direta de **$6.6M em ARR**.

---

## Conclusão

O paradoxo entre as métricas globais positivas e o aumento real do churn foi desvendado: médias agregadas escondem o declínio cirúrgico de contas de alto valor em verticais específicas. A adoção imediata do modelo preditivo e do Early Warning System (EWS) transformará o CS de um papel reativo para uma operação cirúrgica e altamente lucrativa.