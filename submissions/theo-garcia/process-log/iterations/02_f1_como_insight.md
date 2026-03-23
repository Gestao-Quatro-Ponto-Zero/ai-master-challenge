# Iteracao: F1 = 0.098 — Insight, Nao Falha

**Fase:** 4 — Segmentacao de Risco
**Ferramenta:** Claude Code (Opus 4.6)

---

**Eu:** "Treine um Random Forest pra prever churn usando as features da master table."

**IA:** Treinou RF com 34 features, 5-fold cross-validation. F1 Score: 0.098.
Sugeriu: "O modelo precisa de tuning. Podemos testar class_weight, SMOTE, ou XGBoost."

**Meu julgamento:** Parei. F1 = 0.098 nao é um modelo que precisa de tuning — é um modelo dizendo que as features disponiveis nao separam as classes. E isso FAZ SENTIDO com o que encontrei na Fase 3:

Na Fase 3, comparei churned vs retidos em TODAS as metricas comportamentais:
- Uso: praticamente identico
- Satisfacao: churned MAIOR que retidos (4.01 vs 3.97)
- Tickets: sem diferenca significativa
- Erros: sem diferenca significativa

Se as features sao iguais entre os dois grupos, NENHUM modelo vai separar. Nao é o algoritmo — é a natureza do problema. O churn neste dataset é driven por fatores exogenos (preco, concorrente, budget) que nao aparecem nas features de comportamento.

**O que fiz:** Mantive o RF como complementar e criei risk scoring rule-based baseado nos SEGMENTOS que comprovadamente diferenciam:
- Industria: DevTools = 31% vs Cyber = 16%
- Canal: eventos = 30% vs partners = 15%
- MRR: mid-market = 26%

Resultado: Critico = 50% churn real vs Baixo = 11%. Separacao de 4.5x.

**Licao:** Um modelo que parece bom mas nao funciona é pior que admitir que nao funciona e usar o que funciona.

**Evidencia:** `notebooks/04_risk_segmentation.py`
