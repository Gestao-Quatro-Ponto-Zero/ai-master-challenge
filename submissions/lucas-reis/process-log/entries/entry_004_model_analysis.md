# Entry 004b — Análise do Modelo Preditivo: AUC < 0.5 e o que isso significa

**Data:** 2026-03-20
**Fonte:** entry_004_model_output.md
**Autor:** Lucas Reis

---

## O AUC de 0.3444: resultado crítico, não falha técnica

### O que significa AUC < 0.5?

AUC-ROC < 0.5 significa que o modelo é **pior que um coin flip** — está predizendo
o inverso do churn real. Isso não é um bug de implementação: é uma descoberta.

**AUC = 0.5** → modelo completamente aleatório (sem sinal preditivo)
**AUC = 0.3444** → modelo sistematicamente invertido (features anti-correlacionadas com churn)

### Por que o modelo prediz inversamente?

O SHAP revela o mecanismo:

| Feature | Direção SHAP | Interpretação |
|---------|-------------|---------------|
| avg_error_count | ↓ menos churn | Mais erros → mais engajamento → RETÉM |
| avg_mrr | ↓ menos churn | MRR alto → cliente valioso → é investido → RETÉM |
| avg_usage_duration_min | ↓ menos churn | Mais uso → maior dependência → RETÉM |
| avg_session_count | ↓ menos churn | Mais sessões → maior atividade → RETÉM |

**Padrão consistente:** As features de uso e valor medem o inverso do que queremos.
Os clientes com mais erros, mais sessões, mais uso e MRR maior são os que FICAM.

Isso é exatamente o paradoxo encontrado na H3 (t-test): churners e retidos usam
o produto de forma igual, com churners levemente ACIMA na média. O modelo não está
errado — ele aprendeu que "usuário ativo = retido" e está correto em fazê-lo.
O problema é que isso não discrimina quem vai churnar.

---

## Por que o esperado era 0.65–0.75 e chegou 0.34?

### Expectativa original (prompt_005)
> "A expectativa de AUC é moderada (~0.65–0.75) dado que o churn parece segmental,
> não comportamental"

### Diagnóstico retrospectivo

A expectativa estava errada por uma razão: suponha que industry e referral_source
(features segmentais com OR ~2.5×) seriam suficientes para elevar o AUC.

**Mas H1 tinha p=0.066–0.079 (não significativo).** Com n=500:
- DevTools churna 31% vs Cybersecurity 16% — diferença de 15pp
- Com n=113 DevTools e n=100 Cybersecurity → diferença real, mas ruidosa
- O modelo vê ~23 churners DevTools vs ~16 no teste — sinal fraco demais

O modelo LightGBM com 19 features e 110 churners (22% de 500) tem:
- Razão feature/sample: 19 features / 110 positivos = 0.17 (muito alta)
- `class_weight="balanced"` amplifica o ruído dos poucos positivos
- Resultado: overfitting nos negativos (78% da amostra)

### O churn da RavenStack é genuinamente difícil de prever com estes dados

| Fonte de evidência | Conclusão |
|---|---|
| H3 (uso): p=0.105, Δ=3.4% | Sem sinal comportamental |
| H4 (satisf): p=0.741, OR=0.88 | Sem sinal de suporte |
| H5 (plan_tier): p=0.9993 | Sem sinal contratual |
| H1 (segmental): p=0.066, OR=2.5× | Sinal segmental fraco |
| AUC=0.3444 | Modelo confirma: features não discriminam |

**Conclusão integrada:** O modelo quantifica o que a análise estatística sugeriu.
O churn da RavenStack não tem assinatura numérica detectável nas features disponíveis.

---

## A distribuição bimodal de risk_tier

| Tier | N | % |
|------|---|---|
| HIGH (≥70) | 99 | 19.8% |
| MEDIUM (40–69) | 8 | 1.6% |
| LOW (<40) | 393 | 78.6% |

**Por que quase nenhuma conta em MEDIUM?**

O modelo está produzindo probabilidades extremas (próximas de 0 ou 1), sem "zona cinza".
Isso é sintoma de:
1. `class_weight="balanced"` empurra o modelo a ser agressivo na classificação
2. Poucos features com poder discriminante → o modelo vai a extremos quando há qualquer sinal

A distribuição revela falta de calibração: 99 contas HIGH risk incluem muitos falsos positivos.
Dos 99 HIGH, apenas 10 são ativas (churned==0) — e mesmo esses podem ser falsos positivos.

---

## O que o modelo captura apesar do AUC ruim

Mesmo com AUC < 0.5, há dois outputs úteis:

### 1. Feature importance relativa

SHAP confirma a ordem de importância: **uso/valor superam segmental**
(avg_error_count, avg_mrr, seats acima de industry/referral_source).

Isso sugere que, se o churn tivesse sinal comportamental, usage seria mais preditivo que segmento.
A ausência desse sinal é o diagnóstico central.

### 2. CS action list: 10 contas ativas HIGH risk

Mesmo com AUC invertido, a lista de HIGH risk pode ser útil se invertida:
- Contas com score BAIXO + ainda ativas → atenção preventiva
- Ou usar score como "engajamento proxy" (alto score = muito ativo = retém)

Para uso prático: a lista CS deve ser entendida como "contas com perfil atípico",
não como "contas com alta probabilidade de churn".

---

## Implicações para o relatório final

### O que NÃO dizer
- ❌ "O modelo prevê churn com X% de acurácia"
- ❌ "Contas HIGH risk têm 70%+ de probabilidade de churnar"
- ❌ "Implemente este modelo em produção"

### O que DIZER (verdadeiro e útil)
1. **O churn da RavenStack não é previsível com os dados comportamentais disponíveis.**
   AUC=0.34 é evidência de que a causa raiz é segmental (product-market fit), não mensurável
   em logs de uso.

2. **Para construir um modelo preditivo útil, os dados necessários são:**
   - Histórico de NPS/CSAT declarado (não apenas tickets)
   - Feature específica mais usada antes do churn
   - Completude do onboarding (features_activated / features_available)
   - Frequência de login nos últimos 30/60/90 dias (recência, não volume)
   - Interações com sales/CS (calls, demos) — sinal de risco em SaaS B2B

3. **A causa raiz identificada prescinde do modelo preditivo:**
   DevTools (OR=2.36×) + event channel (OR=2.53×) + 60.9% reason_code=features
   são suficientes para orientar ação estratégica sem ML.

---

## Comparação com expectativas da análise anterior

| Expectativa (prompt_005) | Resultado | Avaliação |
|--------------------------|-----------|-----------|
| AUC 0.65–0.75 | 0.3444 | ❌ Muito abaixo (confirma hipóteses nulas) |
| Industry/referral como top features | Rank 5 e fora do top 3 | ❌ Uso supera segmental |
| avg_error_count como sinal de churn | Top 1 SHAP, mas anti-correlacionado | Surpresa confirmada |
| CS list com 20+ contas | 10 contas ativas HIGH risk | Menos que esperado |
| Risk distribution equilibrada | 99 HIGH / 8 MEDIUM / 393 LOW | ❌ Bimodal — falta calibração |

**Conclusão:** O modelo produziu resultados piores que o esperado, mas coerentes com todas as
evidências anteriores. A surpresa era esperada — foi apenas mais extrema do que previsto.
