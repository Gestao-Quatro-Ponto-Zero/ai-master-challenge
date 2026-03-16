# Diagnóstico Operacional — Challenge 002

## Resumo Executivo

A operação de suporte processa ~8.500 tickets com **67.3% de backlog permanente**. O CSAT é dado aleatório (distribuição uniforme). A priorização não segue critério. Automatizando 33.4% dos tickets nos níveis 1 e 2, a economia projetada é de **R$ 42.405/ano**.

---

## 1. Gargalos Operacionais

### 1.1 Backlog Estrutural
- **5.700 tickets** sem resolução (67.3%)
- 2.819 Open + 2.881 Pending = 100% do backlog é ticket aberto ou esperando cliente
- **Somente 2.769 tickets (32.7%) foram fechados**

### 1.2 Priorização Quebrada
- Critical: 25.1% | High: 24.6% | Medium: 25.9% | Low: 24.4%
- Distribuição **perfeitamente uniforme** independente do tipo de ticket
- Refund request tem a mesma porporção de Critical que Product inquiry
- **Implicação:** Não existe critério de priorização — é atribuição aleatória

### 1.3 Tipos de Ticket (5, não 3)
O README do challenge diz 3 tipos. Na realidade:
- Refund request: 1.752 (20.7%)
- Technical issue: 1.747 (20.6%)
- Cancellation request: 1.695 (20.0%)
- Product inquiry: 1.641 (19.4%)
- Billing inquiry: 1.634 (19.3%)

**Refund + Cancellation = 40.7% do volume total**

---

## 2. Satisfação do Cliente (CSAT)

### 2.1 Distribuição (prova de aleatoriedade)
| Rating | Contagem |
|:------:|:--------:|
| 1 | 553 |
| 2 | 549 |
| 3 | 580 |
| 4 | 543 |
| 5 | 544 |

Média: **2.99/5** | Variação máxima: 37 respostas (580 vs 543)

### 2.2 Correlações inexistentes
- CSAT por canal: varia de 2.95 (Phone) a 3.08 (Chat) → diferença irrelevante
- CSAT por tipo: varia de 2.93 (Refund) a 3.03 (Cancellation) → diferença irrelevante
- CSAT vs tempo de resolução: Pearson r ≈ -0.001

**Conclusão:** CSAT é dado gerado aleatoriamente. Qualquer insight baseado nele é análise de ruído.

---

## 3. Desperdício Financeiro

### Premissas
- Custo/hora agente: R$ 45,00 (benchmark mercado BR)
- AHT (Average Handle Time): 20 minutos
- Fonte: Benchmarks de mercado para suporte técnico N1/N2

### Economia por Tipo de Automação

| Tipo | Volume | % Automatizável | Tickets | Economia (R$) | Como |
|------|:------:|:---------------:|:-------:|:-------------:|------|
| Product inquiry | 1.641 | 70% | 1.148 | R$ 17.228 | FAQ + base de conhecimento |
| Billing inquiry | 1.634 | 60% | 980 | R$ 14.704 | Consulta self-service |
| Technical issue | 1.747 | 30% | 524 | R$ 7.862 | Troubleshooting guiado L1 |
| Refund request | 1.752 | 10% | 175 | R$ 2.611 | Apenas verificação de elegibilidade |
| Cancellation request | 1.695 | **0%** | 0 | R$ 0 | **NUNCA — requer retenção humana** |

### Total
- **2.827 tickets automatizáveis** (33.4% do volume)
- **Economia anual: R$ 42.405**
- **Economia mensal: R$ 3.534**

---

## 4. Qualidade dos Dados

| Problema | Evidência | Impacto |
|----------|-----------|---------|
| Textos sintéticos | 100% contêm `{product_purchased}` literal | NLP/ML é inválido nestes textos |
| Resolution gibberish | "Try capital clearly never color toward story" | Impossível usar para FAQ |
| Timestamps fabricados | Compras 2020-2021 vs FRT/TTR 31/Mai-02/Jun/2023 | Análise temporal inválida |
| 49% TTR < FRT | Ticket "resolvido" antes de receber resposta | Paradoxo temporal nos dados |
| CSAT uniforme | ~550 por nota, média 2.99 | Satisfação não medida na realidade |
