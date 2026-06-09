# Proposta de automação — RotaDesk

Challenge 002 · Jean Felipe · Base: `solution/diagnostico/` + `solution/automacao/`

**Stack do protótipo:** Next.js + Supabase (persistência, filas, eventos).

**Princípio de produto:** priorizar **ack automático**, **follow-up de Pending** e **triagem na entrada**. **Não** adotar tempo de ciclo como KPI principal — no DS1 a correlação entre tempo de ciclo e satisfação é **−0,001**.

---

## Contexto (síntese dos relatórios)

| Fonte | Achado relevante |
|-------|------------------|
| **DS1** | 8.469 tickets; **67,3%** sem resolução (2.819 Open + 2.881 Pending); satisfação média **2,99** nos Closed |
| **DS1** | **2.819** tickets sem primeira resposta (Open); **2.881** em Pending Customer Response |
| **DS1** | Refund request: pior satisfação (**2,93**); Cancellation e Refund entre os tipos mais lentos (~**8 h** de ciclo médio nos Closed) |
| **DS2** | Classificador baseline (TF-IDF + regressão logística): macro-F1 **0,8568** (holdout); CV **0,8594 ± 0,0028** |
| **DS2** | Classe fraca: **Administrative rights** (F1 **0,762**) |
| **DS1 × DS2** | **Sem join técnico** — taxonomias diferentes; cruzamento apenas **estratégico** (DS1 = dor operacional; DS2 = mecanismo de triagem por texto) |

---

## Gap DS2 × suporte real — erro esperado em produção

O classificador foi treinado e medido **apenas no DS2** (tickets de TI interna: Hardware, HR Support, Access…). A operação alvo vem do **DS1** (suporte ao cliente: Refund, Cancellation, Billing…). **Não há rótulo DS2 nos tickets DS1**, então a acurácia real em produção **não é observável** neste recorte — só dá para estimar com proxy e bounds.

### O que medimos (in-domain, holdout DS2)

| Métrica | Valor | Implicação |
|---------|-------|------------|
| Macro-F1 holdout | **85,7%** | ~**14,3%** de erro se o domínio fosse idêntico |
| Auto-roteados com conf ≥ **0,85** | ver `ds2_metrics.json` | Subconjunto de maior confiança |
| Erro no subconjunto auto (conf ≥ **0,8**, referência) | **1,57%** (acurácia 98,43%) | **Piso otimista** — assume zero domain shift |
| Classe fraca | Administrative rights, F1 **0,76** | Mitigada por revisão obrigatória |

### Proxy de domain shift (DS2 → texto DS1)

Com ambos os datasets locais, `analise_dataset2.py` (seção 5) roda o modelo treinado no DS2 sobre as **8.469 descrições do DS1** e grava em `ds2_metrics.json` → `domain_gap`:

1. **Confiança média/mediana** no DS1 vs holdout DS2 — queda indica texto fora do domínio de treino.
2. **% auto-roteável** no DS1 vs in-domain no mesmo threshold (85%) — gap em pontos percentuais mostra quanto a fila de revisão humana cresce em produção.
3. **Distribuição de classes preditas** no DS1 vs taxonomia real do DS1 (Refund, Technical issue…) — evidencia desalinhamento estrutural (DS2 não tem reembolso/cancelamento).

> Reexecute `python analise_dataset2.py` após baixar os dois CSVs para atualizar os números do proxy.

### Bounds de erro em produção (subconjunto auto-roteado)

Sem ground truth, usamos o erro medido no holdout in-domain do subconjunto auto e aplicamos penalidade explícita:

| Cenário | Taxa de erro no auto-subset | Lógica |
|---------|----------------------------|--------|
| **Otimista** | **~1,6%** | Mesmo erro do holdout DS2 em conf ≥ 0,8 (domínio idêntico) |
| **Conservador** | **~3,1%** | **2×** o erro in-domain no auto-subset |
| **Pessimista** | **~11,6%** | Erro in-domain no auto-subset **+ 10 pp** absolutos |

**Volume ilustrativo (DS1, 8.469 tickets/ano, ~40% auto no threshold 85% — premissa do ROI):**

```
Tickets auto-roteados ≈ 3.388/ano
Misroutes estimados   ≈ 53 (otimista) | ~105 (conservador) | ~390 (pessimista)
```

Isso são **roteamentos errados sem revisão humana** — tickets que iriam para fila errada. Não incluem Refund/Cancel/Critical (humano obrigatório por regra DS1) nem conf &lt; 85% (revisão de triagem).

### Mitigações já na proposta

| Mitigação | Efeito no erro |
|-----------|----------------|
| Threshold **85%** | Reduz auto-roteamento vs 70–80%; aumenta acurácia no subconjunto |
| Humano em Refund / Cancel / Critical | ~**41%** do DS1 nunca depende só do classificador |
| Administrative rights → revisão | Classe com F1 0,76 fora do auto cego |
| Conf &lt; 85% → fila de revisão | Erros de baixa confiança viram correção humana, não misroute silencioso |
| Queda de confiança OOD (proxy DS1) | Menos auto, mais revisão — troca custo de triagem por risco |

### O que validar no piloto

1. **Taxa de correção** na fila de revisão humana (erro real observável).
2. **% auto** em conf ≥ 85% vs bounds acima.
3. **Tempo de triagem** — domain shift pode inflar revisão e reduzir ROI da alavanca 3 (`roi.md`).

---

## O que terá de automação

### 1. Auto-confirmação (ack) na entrada

**Problema (DS1):** 2.819 tickets (**33,3%** do volume) em **Open** sem `First Response Time`.

**Automação:**
- Ao criar ticket (email, chat, formulário), enviar **ack imediato** com número do ticket, SLA esperado e próximos passos.
- Registrar `first_response_at` no Supabase e mover status para fluxo ativo (ex.: *Triagem* ou *Pending triage*).

**KPI do protótipo:** % de tickets com ack em **&lt; 5 min** (não tempo de resolução).

---

### 2. Follow-up em Pending Customer Response

**Problema (DS1):** 2.881 tickets (**34,0%**) em **Pending Customer Response** — agente já respondeu, cliente não retornou; fila parada sem fechamento.

**Automação:**
- Lembrete programado ao cliente (1º e 2º follow-up).
- Após N dias sem resposta: status *Pending auto-close candidate* + notificação ao agente.
- Dashboard de Pending envelhecido por canal/tipo.

**KPI do protótipo:** redução de volume Pending &gt; X dias; não CSAT por velocidade de ciclo.

---

### 3. Triagem e roteamento na entrada (classificador DS2)

**Base técnica (DS2):** macro-F1 **~86%**; viável para roteamento com **humano no loop**.

**Automação:**
- Pipeline: texto do ticket → classificador (8 `Topic_group` do DS2) → score de confiança.
- **Threshold de produto: 85%** (`confidence ≥ 0,85`) para auto-roteamento.
- Referência holdout DS2: em **≥ 0,8**, **45,4%** dos tickets seriam auto-roteados com **98,43%** de acurácia no subconjunto; em **≥ 0,85** a fração auto-roteada será **menor ou igual** (premissa conservadora no ROI).
- Mapeamento **estratégico** DS2 → filas RotaDesk (tabela configurável no Supabase, sem join de datasets).

**KPI do protótipo:** % auto-roteados vs fila de revisão; acurácia em tickets revisados por humano (amostra).

---

### 4. Regras de escalonamento humano obrigatório

Independente da confiança do classificador, **sempre fila humana** quando o ticket (metadados DS1 ou detecção no texto):

| Regra | Origem |
|-------|--------|
| `Ticket Type` = **Refund request** | DS1: pior satisfação (2,93) |
| `Ticket Type` = **Cancellation request** | DS1: alto tempo de ciclo e alto % sem resolução |
| `Ticket Priority` = **Critical** | DS1: prioridade sensível; regra de produto |

Adicionalmente:
- Classe **Administrative rights** (F1 **0,762** no DS2): **nunca** auto-roteamento cego — revisão humana ou fila dedicada.
- Confiança **&lt; 85%**: fila *Revisão de triagem* (humano confirma ou corrige categoria).

---

### 5. O que o protótipo Next.js + Supabase entrega

| Módulo | Função |
|--------|--------|
| **Ingestão** | API/formulário cria ticket + dispara ack |
| **Classificador** | Endpoint ou Edge Function chama modelo treinado (artefato do `analise_dataset2.py`) |
| **Router** | Aplica regras (Refund/Cancel/Critical/Admin rights/confiança) |
| **Filas** | Tabelas Supabase por fila + status |
| **Pending jobs** | Cron/queue para follow-ups |
| **Painel** | Volume Open/Pending, auto vs revisão, ack SLA |

---

## O que não terá de automação

| Fora de escopo | Motivo (relatório) |
|----------------|-------------------|
| **Resolução automática do problema** | DS1: satisfação não correlaciona com tempo (−0,001); qualidade importa mais que velocidade |
| **Meta de “reduzir ciclo médio” como KPI norte** | Mesmo motivo; ciclo mediano 6,7 h é proxy ruidoso (49,3% timestamps invertidos no DS1) |
| **Roteamento 100% sem humano** | DS2: macro-F1 86%, não 100%; Administrative rights F1 0,76 |
| **LLM como classificador primário** | Baseline linear já viável; LLM reservado para baixa confiança / segunda opinião (fase posterior) |
| **Join DS1 + DS2 em uma única tabela de treino** | Taxonomias incompatíveis; cruzamento só na camada de regras de produto |
| **Promessa de impacto em CSAT** | Análise DS1 não sustenta ganho de satisfação só por acelerar ciclo |
| **Fechamento automático sem política** | Pending exige regras de negócio e, em Refund/Cancel, humano |

---

## KPIs do protótipo (prioridade)

1. **Ack SLA** — % tickets com primeira resposta automática em &lt; 5 min.
2. **Open backlog** — redução dos 2.819 sem FRT (baseline DS1).
3. **Pending aging** — tickets Pending &gt; 7 / 14 dias.
4. **Triagem** — % auto-roteados (conf ≥ 85%) vs revisão humana.
5. **Precisão na revisão** — amostra de tickets corrigidos pelo agente.

**Não** é KPI principal: tempo médio de ciclo (`|TTR − FRT|`).

---

## Mapeamento estratégico DS2 → filas (configurável)

Sem join de dados; tabela de referência no Supabase:

| Topic_group (DS2) | Fila sugerida | Observação |
|-------------------|---------------|------------|
| Hardware | Infra / Dispositivos | Alto volume (28,47%) |
| HR Support | RH | 22,82% |
| Access | Acessos e senhas | |
| Miscellaneous | Geral | Revisão se conf &lt; 85% |
| Storage | Armazenamento | |
| Purchase | Compras | F1 alto (0,914) |
| Internal Project | Projetos internos | |
| Administrative rights | **Revisão obrigatória** | F1 0,762 |

Tickets com tipo DS1 Refund/Cancel ou prioridade Critical **sobrescrevem** qualquer roteamento automático.

---

## Próximo passo

Implementação em `solution/rotadesk/` (Next.js + Supabase) conforme `fluxo.md` e premissas de `roi.md`.
