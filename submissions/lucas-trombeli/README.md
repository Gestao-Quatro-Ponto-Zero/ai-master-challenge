# Submissão — Lucas Trombeli — Challenge 003 (Lead Scorer)

## Sobre mim

- **Nome:** Lucas Trombeli
- **LinkedIn:** (https://www.linkedin.com/in/lucas-trombeli-43b183176/)
- **Challenge escolhido:** Build 003 — Lead Scorer

---

## Executive Summary

Construí o **LeadScore AI**, uma ferramenta web funcional que ranqueia os 2.089 deals ativos do pipeline CRM por **Expected Value** (probabilidade de fechar × valor do produto). O scoring usa 6 fatores ponderados com uma curva de Pipeline Velocity baseada na descoberta-chave dos dados: deals perdidos morrem em 14 dias, enquanto ganhos levam 57 dias. A ferramenta é imediatamente acionável — um vendedor abre, vê seus deals priorizados, e sabe exatamente **por que** cada deal tem aquele score.

---

## Solução

### Abordagem

**1. Entenda antes de codar.** Comecei pela análise exploratória dos 4 CSVs (8.800 oportunidades, 85 contas, 7 produtos, 35 agentes). Encontrei o insight central: a anomalia temporal entre deals ganhos vs. perdidos.

**2. Valide o plano antes de investir tempo.** Submeti meu plano de scoring para revisão crítica ("faça o papel de CTO") — isso revelou 4 buracos que teriam comprometido a qualidade final:
- Probabilidade ≠ valor esperado
- Time decay precisa ser uma curva, não um número
- 16% dos deals não têm conta vinculada (cold start)
- A UX precisa ser de trincheira (tabela cheia, não dashboard gerencial)

**3. Construa rápido, itere com dados.** Toda a implementação levou ~35min com IA como par de programação. O maior ajuste foi pós-build: a normalização linear de preço esmagava 95% dos deals. A correção para log-scale foi um insight humano baseado na distribuição dos dados.

### Resultados / Findings

#### A ferramenta

```bash
cd submissions/lucas-trombeli/solution/lead-scorer
npm install
npm run dev
```

**3 views:**

| View | O que mostra |
|------|-------------|
| **Pipeline** (default) | Tabela paginada com todos os 2.089 deals ativos, ordenável, filtrável, com botão "Why?" para breakdown do score |
| **Overview** | KPIs ($4.9M pipeline, $2.3M EV, avg score 40), distribuição de scores, stage breakdown, top 10 deals |
| **Agents** | 35 agentes com win rate histórico, deals ativos, EV do pipeline |

#### Algoritmo de scoring (2 camadas)

**Camada 1 — Win Probability (0-100):**

| Fator | Peso (com conta) | Peso (sem conta) |
|-------|-------------------|-------------------|
| Agent Win Rate | 25% | 35% |
| Deal Stage | 20% | 25% |
| Pipeline Velocity | 20% | 20% |
| Product Factor | 15% | 20% |
| Account Sector | 10% | 0% |
| Account Size | 10% | 0% |

**Camada 2 — Priority Score:**
```
Priority = Win Probability × (0.55 + 0.45 × log(product_value) / log(max_value))
```

O score final é **Expected Value**: a probabilidade ponderada pelo valor logarítmico do produto. Isso garante que um deal de $55 com 90% de chance não bata um deal de $4.800 com 40%.

#### Descobertas nos dados

| Métrica | Valor |
|---------|-------|
| Win rate global | 63.2% |
| Deals sem conta (cold start) | ~16% |
| Mediana dias — deals perdidos | 14 dias |
| Mediana dias — deals ganhos | 57 dias |
| Variação de win rate por agente | 55%–70% |
| Faixa de preço dos produtos | $55–$26.768 |

### Recomendações

1. **Implementação imediata:** Ordenar o pipeline por Priority Score em vez de ordem cronológica. Os top 10 deals sozinhos representam >$40K em EV.

2. **Alertas de stagnação:** Deals com >80 dias no pipeline devem gerar alerta automático ao manager — a curva de velocity mostra que esses deals estão "morrendo".

3. **Coaching direcionado:** Os agentes com >67% win rate (top quartil) devem ser estudados pela equipe inteira. A diferença de 15pp entre top e bottom agents é receita perdida.

4. **Data quality:** Vincular contas a 100% dos deals elimina o cold start penalty no scoring e gera melhores previsões.

### Limitações

1. **Dados estáticos** — O scoring funciona com snapshot do CSV. Em produção, precisaria de integração com CRM em tempo real.

2. **Sem feature de interação** — Não há modelo de ML que aprenda com conversões reais. O scoring é baseado em regras derivadas da análise.

3. **Tamanho da amostra por setor** — Alguns setores têm <20 deals, tornando a win rate por setor menos confiável.

4. **Sem validação A/B** — Idealmente, mediríamos se seguir o ranking melhora a taxa de conversão em 30-60 dias.

---

## Process Log — Como usei IA

> **Documentação completa em:** `process-log/README.md`

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|---------------|
| **Gemini 2.5 Pro (Antigravity IDE)** | Par de programação principal — análise, código, testes, debug |
| **Gemini (chat separado)** | Revisão crítica do plano como "CTO do G4" |
| **Python + Pandas** | Exploração de dados (script via IA) |
| **Kaggle CLI** | Download do dataset |

### Workflow

1. **Entendimento (20min):** IA leu e resumiu todo o repositório, escolhi o challenge, baixei os dados
2. **Análise exploratória (15min):** Script Python analisou as 4 tabelas, encontrou insights-chave
3. **Revisão crítica (5min):** Submeti plano para outra IA como "CTO" — recebi 4 correções fundamentais
4. **Implementação (35min):** IA gerou código, eu revisava e iterava módulo por módulo
5. **Debug + fix (10min):** Identifiquei problema de normalização, corrigi para log-scale
6. **Documentação (15min):** Process log, README, evidências

### Onde a IA errou e como corrigi

| Erro | Impacto | Minha correção |
|------|---------|----------------|
| Normalização linear de preço | 95% dos deals ficaram "Cold" | Implementei log-scale normalization |
| `python -m kaggle` falhou | Kaggle v2 não tem `__main__` | Usei `from kaggle import api` direto |
| Projeto criado no diretório errado | Estrutura de pastas incorreta | Movi manualmente para `submissions/` |
| Fragment sem key no React | Warning no console | Troquei `<>` por `<Fragment key={}>` |

### O que eu adicionei que a IA sozinha não faria

1. **Submeter o plano para revisão como "CTO"** — usar uma IA para auditar outra IA foi decisão minha
2. **Expected Value como score principal** — a IA fez probabilidade pura, eu mudei para EV
3. **Validação da curva de velocity** — confirmei que os 14d/57d fazem sentido em vendas B2B
4. **UX de trincheira** — tabela full como default, não dashboard gerencial
5. **Fix de log-scale** — identifiquei que o problema era normalização, não algoritmo

---

## Evidências

- [x] Screenshots das 3 views (em `process-log/screenshots/`)
- [x] Screen recordings do browser testing (em `process-log/screenshots/`)
- [x] Narrativa escrita detalhada (em `process-log/README.md`)
- [x] Git history mostrando evolução do código
- [x] Build passando (`npm run build` exit code 0)

---

*Submissão enviada em: 03/03/2026*
*Tempo total do challenge: ~1h30min*
