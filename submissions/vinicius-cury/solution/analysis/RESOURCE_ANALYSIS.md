# Análise de Recursos Operacionais — Relatório Explicativo

> Baseado no Notebook 08: `analysis/08_resource_analysis.ipynb`
> Dataset: Customer Support Tickets — 2.769 tickets fechados com CSAT
> Data: 21 de março de 2026

---

## 1. O Que Medimos

**Métrica central:** Horas operacionais por par Canal × Assunto.

Usamos `duration_hours = abs(TTR - FRT)` como proxy de esforço operacional — quanto tempo um agente efetivamente dedicou a cada ticket, desde a primeira resposta até a resolução.

**Total:** 21.439 horas operacionais distribuídas em 64 pares Canal × Assunto.

---

## 2. Distribuição por Canal

| Canal | Horas | % | Tickets |
|-------|------:|--:|--------:|
| Email | 5.689h | 26,5% | 720 |
| Social media | 5.423h | 25,3% | 684 |
| Chat | 5.191h | 24,2% | 674 |
| Phone | 5.136h | 24,0% | 691 |

**Achado:** Distribuição quase uniforme entre canais (~25% cada). Isso é consistente com dados sintéticos — em operações reais, esperaríamos concentração em 1-2 canais.

---

## 3. Distribuição por Assunto

Top 5 assuntos por consumo de horas:

| Assunto | Horas | % |
|---------|------:|--:|
| Software bug | 1.647h | 7,7% |
| Hardware issue | 1.526h | 7,1% |
| Network problem | 1.494h | 7,0% |
| Battery life | 1.482h | 6,9% |
| Product compatibility | 1.437h | 6,7% |

**Achado:** Também distribuição quase uniforme (~6-8% por assunto). Os 16 assuntos dividem as horas de forma equilibrada.

---

## 4. O Diagnóstico de 6 Cenários

Cada par Canal × Assunto foi classificado usando a correlação de Pearson (duração × CSAT) e o gap de CSAT entre canais:

| Cenário | Critério | Ação |
|---------|----------|------|
| **Acelerar** | r < -0.3 (mais tempo = pior CSAT) | Investir em SLA agressivo, automação |
| **Desacelerar** | r > 0.3 (mais tempo = melhor CSAT) | Manter ritmo, agentes seniores |
| **Redirecionar** | Gap CSAT > 0.5 + canal viável | Mover tickets para canal com melhor CSAT |
| **Quarentena** | Gap CSAT > 0.5 mas sem alvo viável | Investigar causa raiz |
| **Manter** | CSAT ≥ 3.5, sem correlação forte | Preservar — está funcionando |
| **Liberar** | Nenhum dos anteriores | Recursos sem retorno claro |

---

## 5. Resultado: Para Onde Vão as Horas?

| Cenário | Pares | Horas | % Total | CSAT Médio |
|---------|------:|------:|--------:|-----------:|
| **Liberar** | 50 | 17.038h | **79,5%** | 3,02 |
| Redirecionar | 7 | 2.076h | 9,7% | 2,70 |
| Quarentena | 3 | 1.177h | 5,5% | 2,81 |
| Manter | 2 | 528h | 2,5% | 3,69 |
| Acelerar | 1 | 324h | 1,5% | 2,98 |
| Desacelerar | 1 | 296h | 1,4% | 2,97 |
| **TOTAL** | **64** | **21.439h** | **100%** | — |

### A Descoberta Central

**79,5% das horas operacionais (17.038h) estão em pares "liberar"** — pares onde:
- A duração do atendimento **não correlaciona** com a satisfação do cliente
- O CSAT médio está **abaixo de 3,5** (nem satisfeito nem insatisfeito)
- Não há um canal claramente melhor para redirecionar

Em outras palavras: **a operação dedica 4/5 do seu tempo a atendimentos que não melhoram nem pioram a satisfação**, independente de quanto esforço é aplicado.

---

## 6. Cenários de Realocação

Se movermos uma fração das horas "liberar" para reforçar os pares "acelerar" (onde mais tempo = pior CSAT, ou seja, precisam de resolução RÁPIDA):

| Cenário | Horas Movidas | Capacidade Acelerar | Liberar Restante |
|---------|-------------:|--------------------:|-----------------:|
| Conservador (25%) | 4.259h | 324h → 4.584h (+1.313%) | 12.778h |
| Moderado (50%) | 8.519h | 324h → 8.843h (+2.626%) | 8.519h |
| Agressivo (75%) | 12.778h | 324h → 13.103h (+3.939%) | 4.259h |

**Nota importante:** Esses números são teóricos. Na prática, realocação significa:
- Treinar agentes para priorizar tickets "acelerar"
- Implementar autoatendimento/chatbot nos pares "liberar" para liberar agentes
- Reordenar a fila de atendimento com peso por cenário

---

## 7. O Paradoxo de Simpson em Ação

Por que 79,5% é "liberar" e não "acelerar" ou "desacelerar"?

Globalmente, a correlação entre duração e CSAT é R² ≈ 0,003 (praticamente zero). Mas ao olhar **par a par**, encontramos correlações de -0,70 a +0,87. Isso é o **Paradoxo de Simpson** — o efeito desaparece quando agregamos.

O que isso significa operacionalmente:
- Na **maioria** dos 64 pares (50 deles), a correlação é fraca (-0.3 < r < 0.3)
- Em **poucos** pares, a correlação é forte: 1 par acelerar, 1 par desacelerar
- Os 7 pares "redirecionar" são identificados pelo gap de CSAT entre canais, não pela correlação

---

## 8. Recomendações Operacionais

### Ação Imediata (< 1 semana)
1. **Reordenar a fila:** Tickets do par "acelerar" vão para o topo. Tickets "liberar" podem esperar.
2. **Auto-roteamento:** Os 7 pares "redirecionar" devem ser automaticamente encaminhados ao canal com melhor CSAT.

### Curto Prazo (1-4 semanas)
3. **Chatbot para "liberar":** Implementar autoatendimento nos 50 pares onde o esforço humano não faz diferença.
4. **Roteamento especialista:** Os 3 pares "quarentena" precisam de investigação — agentes seniores dedicados.

### Médio Prazo (1-3 meses)
5. **Dashboard de monitoramento em tempo real** com classificação automática por cenário.
6. **Modelo preditivo de CSAT** para antecipar tickets que precisam de atenção antes da insatisfação.

---

## 9. Limitações

- **Dados sintéticos:** As distribuições uniformes limitam a generalização. Em dados reais, esperaríamos concentração muito maior em certos pares.
- **Proxy de esforço:** `abs(TTR - FRT)` é uma aproximação — não considera tempo de espera, pausas, ou múltiplas interações.
- **Amostra de fechados:** Só analisamos tickets "Closed" com CSAT (2.769 de 8.469). Os abertos podem ter perfil diferente.
- **Sem custo real:** Usamos horas como proxy. O custo varia por canal (telefone > chat, tipicamente).

---

## Visualizações Disponíveis

Todos os gráficos estão em `process-log/screenshots/`:
- `p6_hours_by_channel.png` — barras horizontais por canal
- `p6_hours_by_subject.png` — barras horizontais por assunto
- `p6_heatmap_hours_csat.png` — heatmap duplo (horas + CSAT por par)
- `p6_treemap_hours_csat.png` — treemap (tamanho=horas, cor=CSAT)
- `p6_scenario_scatter.png` — scatter r vs CSAT colorido por cenário
- `p6_hours_by_scenario_stacked.png` — barras empilhadas por cenário+canal
- `p6_reallocation_scenarios.png` — comparação dos 3 cenários de realocação
- `p6_sankey_resource_flow.png` — diagrama Sankey: Canal → Cenário → Ação
