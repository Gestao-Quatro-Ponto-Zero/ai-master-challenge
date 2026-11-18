# Relatório Reprodutível de Auditoria Forense, Benchmark Out-of-Sample e Simulação de ROI

**Desafio:** Challenge 002 — Redesign de Suporte (Operações / CX)<br>
**Autor:** Arthur Lima<br>

---

## 1. Diagnóstico Forense do Dataset 1 (`customer_support_tickets.csv`, `N = 8.469`)

- **Backlog Aberto/Pendente:** `5700 / 8469` (**67.30%** sem fechamento: `2819` Open + `2881` Pending Customer Response).
- **Distribuição Equitativa das 4 Prioridades (`High` + `Critical`):** `4214 / 8469` (**49.76%** rotulados como `High` ou `Critical`, ~25% em cada uma das 4 faixas).
- **Placeholder Não Interpolado (`{product_purchased}`):** `8469 / 8469` (**100.00%** dos chamados).
- **Inversão Temporal nos Fechados (`Time to Resolution < First Response Time`):** `1365 / 2769` (**49.30%** com duração negativa; média `-0.06 h`, mediana `0.17 h`).
- **CSAT e Intervalo de Resolução (Sem Diferença Significativa Detectada):** CSAT médio `2.991` (DP `1.407`), correlação linear com tempo de resolução `r = 0.0199` (`p = 0.2958`).
- **Teste de Preditibilidade Linear Supervisionada no Dataset 1 (Split 80/20, `N_test = 1694`):**
  - `Ticket Type` (5 classes, baseline uniforme = 20,0%): Accuracy = **21.43%**, Macro-F1 = **0.2143**.
  - `Ticket Priority` (4 classes, baseline uniforme = 25,0%): Accuracy = **24.97%**, Macro-F1 = **0.2486**.

### Testes de Hipótese por Dimensão no Dataset 1

| Dimensão | ANOVA F (CSAT) | ANOVA p (CSAT) | Kruskal p (CSAT) | Permutação p (CSAT) | ANOVA p (Δ Horas) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `Ticket Channel` | 1.2808 | 0.2792 | 0.2785 | 0.3383 | 0.4508 |
| `Ticket Priority` | 0.5722 | 0.6333 | 0.6287 | 0.5323 | 0.5687 |
| `Ticket Type` | 0.5475 | 0.7008 | 0.6993 | 0.8159 | 0.9109 |
| `Ticket Subject` | 0.6766 | 0.8100 | 0.8066 | 0.4726 | 0.4586 |

---

## 2. Benchmark Out-of-Sample no Dataset 2 (`N_train = 38269`, `N_test = 9568`)

- **Auditoria de Duplicatas no Corpus (`test_d2` vs. `train_d2`):** `0 / 9568` (**0.00%**) das linhas da partição de teste possuem texto normalizado idêntico na partição de treino; nos `9568` textos estritamente inéditos, a acurácia global é **85.95%** e a acurácia no Tier 1 é **97.30%**.

| Modelo / Estratégia | Accuracy Global | Macro-F1 Global | Top-2 Accuracy |
| :--- | :---: | :---: | :---: |
| Motor Principal: Calibrated LinearSVC (TF-IDF 1-2g, CV=3 por fold) | 85.95% | 0.8628 | 96.30% |
| Baseline 3: Logistic Regression (TF-IDF 1-2g) | 85.61% | 0.8555 | N/A |
| Baseline 2: Complement Naive Bayes | 81.30% | 0.8030 | N/A |
| Baseline 1: Classe Majoritária (Hardware) | 28.47% | 0.0554 | N/A |

### Curva de Automação Seletiva (Confiança Bruta vs. Tier 1 Operacional Pós-Guardrail/PAM)

| Limiar de Confiança (τ) | Tickets Cobertos Bruto (n) | Cobertura Bruta (%) | Acurácia Bruta (%) | Tier 1 Operacional (n) | Cobertura Tier 1 Operacional (%) | Acurácia Tier 1 Operacional (%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `>= 0.55` | 8466 | 88.48% | **90.79%** | 8048 | **84.11%** | **90.88%** |
| `>= 0.60` | 8023 | 83.85% | **92.38%** | 7642 | **79.87%** | **92.45%** |
| `>= 0.70` | 7189 | 75.14% | **94.80%** | 6869 | **71.79%** | **94.86%** |
| `>= 0.75` | 6644 | 69.44% | **95.97%** | 6354 | **66.41%** | **96.02%** |
| `>= 0.80` | 6075 | 63.49% | **97.23%** | 5822 | **60.85%** | **97.30%** |
| `>= 0.85` | 5366 | 56.08% | **98.16%** | 5162 | **53.95%** | **98.20%** |
| `>= 0.90` | 4383 | 45.81% | **99.04%** | 4242 | **44.34%** | **99.03%** |

### Distribuição Operacional dos 3 Tiers na Partição de Teste (`N = 9.568`)

- **Tier 1 — Auto-Route (`conf >= 0.80`, sem bloqueio de guardrail/PAM):** `5822` chamados classificados/encaminhados (**60.85%** da fila) com **97.30%** de acurácia.
- **Tier 2 — Copilot Assist (`0.55 <= conf < 0.80` ou aprovação PAM):** `2504` chamados (**26.17%** da fila) com **94.97%** de cobertura nas Top-2 sugestões.
- **Tier 3 — Escalação Humana (`conf < 0.55` ou Guardrail Acionado):** `1242` chamados (**12.98%** da fila).

---

## 3. Teste de Estresse de Domain Shift (Dataset 1 Consumidor no Motor de TI Dataset 2)

- **Sem Guardrail de Domínio (Apenas `conf >= 0.80`):** `3329 / 8469` (**39.31%**) dos tickets de consumidor seriam falsamente auto-roteados para filas internas de TI.
- **Com Guardrails Determinísticos (Dataset 1 Bruto):** `0 / 8469` auto-roteados (**100.00%** de contenção humana/consumidor).
- **Com Guardrails Determinísticos (Dataset 1 Interpolando `{product_purchased}` pelo Produto Real):** **93.43%** de contenção fora do Tier 1.

---

## 4. Simulação Paramétrica de Capacidade, Retrabalho e TCO (Base 30.000 tickets/ano)

> **Nota de Transparência:** Os cenários separam explicitamente o **tempo de triagem e encaminhamento manual** (Cenário 1: `4,0 min/ticket`, escopo executado pelo protótipo) de ganhos adicionais condicionais de assistência em resolução (Cenários 2 e 3), aplicando penalidade uniforme de retrabalho de `2,0x` sobre os erros residuais do Tier 1.

| Cenário | Escopo Modelado | Cobertura Tier 1 (%) | Precisão Tier 1 (%) | Horas Base/Ano | Horas Brutas Poupadas | (-) Horas Retrabalho Erro | (=) Horas Líquidas/Ano | FTEs Liberados | Economia Líquida (R$/ano) | Payback (meses) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1. Escopo Estrito do Protótipo (Apenas Triagem & Roteamento: 4,0 min + 0,0 min resolução) | Executado pelo Protótipo (Triagem Pura) | 60.85% | 97.30% | 2000.0 | 1363.3 | 65.6 | **1297.6** | 0.74 | **R$ 30,346.13** | 13.8 |
| 2. Base Operacional (Triagem 4,0 min + Aceleração Runbook/Precedente +4,0 min) | Protótipo + Adoção do Runbook N1/N2 | 60.85% | 97.30% | 4000.0 | 3005.4 | 131.3 | **2874.1** | 1.63 | **R$ 108,818.95** | 5.0 |
| 3. Expansão Futura via API (Triagem 4,0 min + Provisionamento Automático IAM/ITSM +8,0 min) | Hipotético (Requer Integração ITSM/AD) | 60.85% | 97.30% | 6000.0 | 4582.1 | 196.9 | **4385.2** | 2.49 | **R$ 207,039.06** | 2.6 |
