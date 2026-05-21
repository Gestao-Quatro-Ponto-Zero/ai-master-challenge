# Metodologia de Scoring — v3

Score de **0 a 100** representando prioridade relativa de cada deal. Dimensões ponderadas, pesos distintos para **Engaging** (5 dimensões) e **Prospecting** (5 dimensões).

| Faixa | Range | Significado |
|-------|-------|-------------|
| HOT | 80-100 | Prioridade máxima |
| WARM | 60-79 | Atenção ativa |
| COOL | 40-59 | Monitorar e nutrir |
| COLD | 20-39 | Avaliar se vale investir tempo |
| DEAD | 0-19 | Considerar encerramento |

---

## Engaging — Fórmula

```
score = round(
  agentProductAffinity × 0.40 +
  dealValue × 0.20 +
  velocity × 0.20 +
  accountQuality × 0.15 +
  productSectorFit × 0.05
)

if (daysInPipeline > 138):
  score = round(score × max(0.5, 1 - (days-138)/500))
```

### Agent-Product Affinity (40%)

Win rate histórica do par vendedor × produto. Preditor mais forte do dataset (spread de até 73pp).

- Normalização: `((winRate - 0.35) / (0.85 - 0.35)) × 100`
- Blending: n < 5 usa taxa global; n < 10 usa blend proporcional; n >= 10 usa individual

### Deal Value (20%)

Normalização logarítmica: `((log(price) - log(55)) / (log(26768) - log(55))) × 100`

Resultados: $55→0, $550→37, $1.096→48, $3.393→67, $4.821→72, $5.482→74, $26.768→100. Fundamentado em Esperança Matemática: E(X) = P × V.

### Velocity (20%)

Curva bimodal validada em todos os produtos (ciclos homogêneos, mediana 47-69d):

| Dias | Score | Nota |
|------|-------|------|
| < 14d | 50 | Muitos descartados rápido |
| 14-30d | 100 | Sweet spot (73% WR) |
| 31-60d | 75 | Saudável |
| 61-90d | 65 | Atenção |
| 91-120d | 70 | Viés de sobrevivência |
| 121-130d | 55 | Poucos precedentes |
| > 130d | 10 | Sem precedente histórico |

### Account Quality (15%)

Win rate histórica da conta. Range 55-72%. Bônus +5 se repeat purchase do mesmo produto. Sem histórico = 50.

### Product-Sector Fit (5%)

Win rate do par produto × setor. Range 50-75%. Blend para n < 30. Peso baixo: spread de apenas 3-5pp.

### Decay Multiplier (deals >138d)

Nenhum deal histórico fechou com mais de 138 dias. Multiplicador no score final: 200d→0.88, 300d→0.68, 400d+→0.50 (cap).

---

## Prospecting — Fórmula

```
score = round(
  agentProductAffinity × 0.40 +
  dealValue × 0.20 +
  accountQuality × 0.20 +
  productSectorFit × 0.10 +
  opportunityWindow × 0.10
)
```

**Opportunity Window (10%):** Projeta se o fechamento cairia em quarter-end (mar/jun/set/dez) usando mediana de ciclo de 57 dias.

---

## Resultados v3

| Métrica | v2 | v3 |
|---------|----|----|
| Range | 23-74 | 12-81 |
| HOT | 0 | 2 |
| WARM | 56 | 175 |
| COOL | 1.660 | 1.076 |
| COLD | 373 | 816 |
| DEAD | 0 | 20 |

**Backtest** (6.711 deals históricos): COLD 43% → COOL 60% → WARM 73% → HOT 88%. Monotonicamente crescente.

**Expected Value:** `E(V) = (score / 100) × salesPrice`

---

## Limitações

1. CV alto (76-84%) no tempo de fechamento — velocity é heurística, não predição
2. Separação Won/Lost modesta (~3-4pp)
3. Affinity dominante (40%) — vendedores com poucas observações dependem de blending
4. Dataset estático (2016-2017) — padrões podem ter mudado
5. Decay conservador — cap de 0.5 pode ser generoso para deals >400d
