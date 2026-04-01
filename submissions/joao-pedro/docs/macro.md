# 🧠 Macro

> **AI-master Challenge** — Priorização inteligente de pipeline de vendas

---

## 🎯 O Desafio

### Contexto de Negócio

| | |
|---|---|
| 👥 **Time** | 30 vendedores, 3 regiões, múltiplos managers |
| 📦 **Pipeline** | ~8.800 oportunidades |
| ⚠️ **Problema** | Priorização feita "no feeling" |

### A Pergunta-Chave

> **"O que o vendedor deve trabalhar segunda-feira de manhã?"**

- ✅ Quais deals merecem atenção **agora**?
- ✅ Quais podem esperar?
- ✅ Quais devem ser descartados ou transferidos?

### Por Que Isso Importa

- Vendedores gastam tempo em deals que não vão fechar
- Oportunidades boas "esfriam" por falta de atenção
- Pipeline travado com deals antigos sem ação
- Desbalanceamento de carga entre vendedores

---

## 📊 O Diagnóstico: Pipeline Travado

### Tese Central

> Pipeline não está parado por "deals difíceis".
> Está travado por **FALTA DE AÇÃO**.

### Evidências Quantitativas

| Métrica | Valor | Significado |
|---|---|---|
| Engaging mediana | **165 dias** | 2.9× Won (57d) |
| Engaging média | **199 dias** | 3.5× Won |
| Vendedores sem prospecting | **57%** (17/30) | Protegem deals ruins |
| Probabilidade >200d | **38%** | vs 63% global (−25 pts) |
| Desbalanceamento de carga | **2×** | Alguns 177 deals, outros 31 |

### O Insight Crítico

```
HIPÓTESE INICIAL (rejeitada)
"Deals em Engaging são intrinsecamente difíceis."

EVIDÊNCIA CONTRÁRIA
  Lost  → fecha em 14d (mediana)   ← Percebem rápido que não vai
  Won   → fecha em 57d (mediana)   ← Quando há ação, fecha
  Engaging → trava por 165d        ← Ninguém age

CONCLUSÃO
  Não é dificuldade — é FALTA DE AÇÃO.
```

### O Círculo Vicioso

```
  Vendedor sobrecarregado (>100 deals)
          ↓
  Não prospecta (0 deals novos)
          ↓
  Protege deals ruins ("preciso manter pipeline")
          ↓
  Pipeline trava (165+ dias)
          ↓
  Performance cai → Mais sobrecarga
          ↓
        ❌ Loop infinito
```

---

## 🧠 A Solução: Priorização Contextual

### Arquitetura do Modelo

**Dois componentes independentes:**

```
SCORE (0–100)          Importância OBJETIVA do deal
  ├── 50%  Urgência       tempo travado vs. benchmark
  ├── 30%  Probabilidade  chance real de fechar
  └── 20%  Valor          importância estratégica

VIABILIDADE (0–100)    Capacidade CONTEXTUAL do vendedor
  ├── Prospecting         pipeline saudável?
  ├── Carga               tem atenção disponível?
  └── Especialização      fit com produto/setor?
```

> **Score** é objetivo — o mesmo deal tem o mesmo score para qualquer vendedor.
> **Viabilidade** é contextual — personaliza a ação por quem vai executar.

### Matriz de Ação

| Score \ Viabilidade | Alta ≥ 60 | Média 40–60 | Baixa < 40 |
|---|---|---|---|
| **≥ 80** Crítico | 🔥 PUSH HARD | 🔄 RE-QUALIFY | 🔀 TRANSFER |
| **70–79** Alto | 🔥 PUSH HARD | 🔄 RE-QUALIFY | 🔀 TRANSFER · ❌ DISCARD |
| **60–69** Médio | ⚡ ACCELERATE | 🔍 INVESTIGATE | 🔀 CONSIDER TRANSFER |
| **< 60** Baixo | ⏸ MONITOR | ⏸ MONITOR | ⏸ MONITOR |

**Legenda de ações:**

| Ação | Descrição |
|---|---|
| 🔥 PUSH HARD | Foco máximo, ação imediata |
| ⚡ ACCELERATE | Priorizar, mover forward |
| 🔄 RE-QUALIFY | Validar se ainda faz sentido |
| 🔍 INVESTIGATE | Entender o bloqueio |
| 🔀 TRANSFER | Passar para vendedor com capacidade |
| ❌ DISCARD | Descartar, liberar atenção |
| ⏸ MONITOR | Manter observação passiva |

---

## 💡 Decisões de Design

### Por Que NÃO Foi Machine Learning?

**Abordagens rejeitadas:**

| Abordagem | Motivo da rejeição |
|---|---|
| ❌ Modelo preditivo (XGBoost, RF) | Ignora contexto do vendedor · black box · não diz "o que fazer" |
| ❌ Feature engineering complexo | Sem dados de engajamento · overfitting · manutenção impossível |

**Abordagem escolhida:**

> ✅ **Regras + Heurísticas + Explicabilidade**
> Vendedor entende cada componente, confia no sistema e age.

### Trade-offs Conscientes

#### 1 · Regras > Machine Learning

| ✓ Ganhos | ✗ Perdas |
|---|---|
| Explicabilidade total | Menos preciso que modelo treinado |
| Manutenção simples | Não aprende padrões automaticamente |
| Vendedor confia (entende o "porquê") | |
| Não precisa retreinar | |

> *Modelo 70% preciso que o vendedor **usa** > Modelo 95% preciso que o vendedor **ignora**.*

#### 2 · Viabilidade Separada do Score

| ✓ Ganhos | ✗ Perdas |
|---|---|
| Score é "justo" para todos | Dois números em vez de um |
| Ação personalizada por contexto | Mais complexo de explicar |
| Identifica oportunidades de transfer | |

> *Deal importante pode não ser acionável pelo vendedor atual.*

#### 3 · Value-First Design

| ✓ Ganhos | ✗ Perdas |
|---|---|
| Zero fricção inicial | Modelo menos preciso inicialmente |
| Vendedor vê valor antes de dar esforço | Falta dados de engajamento |
| Usa apenas dados existentes | |

> *Vendedores não atualizam CRM se não veem ROI. Gerar valor **primeiro**, pedir dados **depois**.*

---

## 📈 Resultados Esperados

### Distribuição Atual — 1.589 deals em Engaging

| Ação | Qtd | % | Impacto |
|---|---|---|---|
| ❌ DISCARD | 443 | 27.9% | Liberar atenção |
| 🔀 TRANSFER | 413 | 26.0% | Redistribuir capacidade |
| ⏸ MONITOR | 696 | 43.8% | Observação passiva |
| 🔥 PUSH / ACCELERATE | 18 | 1.1% | Ação imediata |
| 🔍 INVESTIGATE | 16 | 1.0% | Investigar bloqueio |
| 🔄 RE-QUALIFY | 3 | 0.2% | Validar fit |

### Se Adotado — Simulação em 30 dias

1. **443 deals descartados** → libera ~150h/semana de atenção
2. **413 deals transferidos** → redistribui carga para vendedores com capacidade
3. **18 deals críticos em foco** → alta prob × alta urgência × vendedor tem capacidade
4. **Pipeline destranca** → vendedores voltam a prospectar, círculo vicioso quebrado

### KPIs que Moveria

| KPI | Baseline | Meta 30d | Meta 90d |
|---|---|---|---|
| Tempo médio Engaging | 165d | 120d (−27%) | 90d (−45%) |
| Win rate (deals focados) | 63% | 72% (+9 pts) | 75% (+12 pts) |
| % Vendedores prospecting | 43% | 60% (+17 pts) | 80% (+37 pts) |
| Carga média | 87 deals | 65 deals (−25%) | 50 deals (−43%) |

---
