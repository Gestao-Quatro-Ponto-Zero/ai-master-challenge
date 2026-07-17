# 📊 RavenStack — Diagnóstico de Churn & Plano de Ação de Emergência

Autor: Paulo Sérgio Oliveira da Silva Júnior
Área: Dados / Analytics & Business Strategy
Para: CEO, RavenStack

---

## 🎯 Executive Summary

O diagnóstico completo das 5 bases de dados da **RavenStack** revelou um cenário crítico de hemorragia de receita: nossa **Taxa de Churn de Receita atingiu 70,48%**. Enquanto retemos apenas **$3.347.765,00** em MRR ativo, já perdemos **$7.990.982,00** em faturamento recorrente mensal.

Conseguimos decifrar os dois paradoxos que confundiam a diretoria:

*   **O paradoxo do "Uso Saudável":** O gráfico temporal revelou que a média de uso diário (`usage_count`) de clientes ativos e churnados é virtualmente idêntica (ambas flutuando estavelmente na média de 10 interações diárias). O time de Produto foi enganado por métricas de vaidade agregadas: o cliente não reduz o uso gradativamente ao longo dos anos; ele utiliza a plataforma até o momento em que se frustra com bugs ou falta de features e cancela abruptamente.
*   **O paradoxo da "Satisfação OK":** O principal motivo declarado para o cancelamento foi **Features** (114 reclamações) e **Suporte** (104 reclamações). O CSAT médio alto divulgado pelo CS é puramente o **Viés do Sobrevivente**: apenas os clientes que decidiram ficar respondem às pesquisas. Os clientes que saíram foram ignorados pelas métricas de satisfação, apesar de apontarem gargalos claros de produto.

---

## 🔍 1. Causa Raiz do Churn (Análise dos Dados)

### A. Diagnóstico Qualitativo (Reason Codes & Feedbacks)
A análise dos motivos de cancelamento (`reason_code`) revelou que as maiores dores estão sob nosso controle direto:
1.  **Problemas de Produto (Features):** 114 cancelamentos causados por falta de funcionalidades ou frustração com a entrega de valor. Os feedbacks textuais deixam claro que *"missing features"* é uma dor constante.
2.  **Gargalos de Suporte e Custo:** 104 cancelamentos por insatisfação com suporte e outros 104 por questões orçamentárias (*"too expensive"*), indicando que o cliente não enxerga valor suficiente para justificar o preço diante dos problemas enfrentados.
3.  **Ameaça Competitiva:** 92 contas migraram diretamente para a concorrência (*"switched to competitor"*).

### B. O Erro da Média Agregada (Métricas de Uso)
Nosso gráfico de linha temporal provou que a média diária de interações não serve como indicador antecedente de Churn quando analisada de forma isolada. O comportamento de uso diário de quem cancela é indistinguível de quem permanece ativo. O churn na RavenStack é reativo e repentino, motivado por quebras de expectativa pontuais (bugs críticos acumulados ou falta de uma ferramenta essencial no dia a dia).

---

## 🚨 2. Segmentos e Contas em Risco (Ação Imediata)

Para conter novos cancelamentos, aplicamos um algoritmo de **Alerta Vermelho** mapeando contas ativas que apresentam risco iminente de Churn (baixo engajamento recente acumulado com alta taxa de erros).

Identificamos **18 contas ativas em situação de risco**. Abaixo estão as **TOP 10 contas prioritárias** ordenadas pelo volume financeiro que o time de CS deve contatar imediatamente:

| Rank | Account ID | MRR em Risco | Uso Recente (Média) | Erros Recentes (Média) | Risk Score |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **1º** | A-fd9422 | `$11.542,00` | 6.0 | 4.0 | 1 |
| **2º** | A-bb2f49 | `$9.751,00` | 11.0 | 2.0 | 1 |
| **3º** | A-068fc6 | `$6.965,00` | 17.0 | 2.0 | 1 |
| **4º** | A-9badbd | `$5.970,00` | 19.0 | 4.0 | 1 |
| **5º** | A-970c97 | `$2.786,00` | 15.0 | 2.0 | 1 |
| **6º** | A-f9cc74 | `$1.470,00` | 8.0 | 2.0 | 1 |
| **7º** | **A-88c6ca** | **`$995,00`** | **4.0** | **2.0** | **2 (Risco Máximo)** |
| **8º** | A-4e960a | `$588,00` | 16.0 | 3.0 | 1 |
| **9º** | A-139c3b | `$551,00` | 7.0 | 2.0 | 1 |
| **10º** | A-43a9e3 | `$418,00` | 12.0 | 2.0 | 1 |

> ⚠️ **Atenção Especial:** A conta **A-88c6ca** possui um **Risk Score 2**, o que significa que ela atende simultaneamente aos dois piores critérios: uso extremamente baixo (4.0) e alta taxa de erros (2.0). Mesmo não sendo o maior MRR, ela é a conta com maior probabilidade estatística de cancelar nas próximas semanas.

---

## 🚀 3. Plano de Ação Recomendado

```
🚨 SALVAR CONTAS (48h)  ➔  ⚙️ CORREÇÃO DE PROCESSO (30 dias)  ➔  📈 PREVENÇÃO (60 dias)
```

1.  **Operação Resgate (Imediato - CS/Vendas)**
    *   **O que fazer:** Ligar imediatamente para os tomadores de decisão das contas `A-fd9422`, `A-bb2f49`, `A-068fc6` e `A-88c6ca`.
    *   **Abordagem:** Oferecer um diagnóstico técnico preventivo focado em solucionar os erros que eles andam enfrentando na plataforma (antecipando-se à reclamação deles).
2.  **SLA de Bugs e Suporte Técnico (Curto Prazo - Suporte/Devs)**
    *   **O que fazer:** Estabelecer um teto rígido de resolução para contas que apresentarem média de erros diários superior a 2.0. Reduzir o tempo de resolução de bugs críticos para no máximo 12 horas úteis.
3.  **Implementar Gatilhos de Saúde de Produto (Médio Prazo - Produto/Engenharia)**
    *   **O que fazer:** Substituir a análise de médias gerais por alertas automatizados. Criar um robô que notifica o CS via Slack quando qualquer conta individual apresentar uma queda brusca de engajamento diário de um dia para o outro.

---

## 🛠️ 4. Log de Processo (Pipeline de Dados)

O pipeline de análise que sustenta este diagnóstico seguiu os seguintes passos rigorosos de engenharia de dados:

1.  **Mapeamento e Higienização:** Padronização dos nomes de todas as colunas para minúsculas (`lowercase`), remoção de caracteres especiais e espaços para evitar falhas de interpretação do interpretador Pandas.
2.  **Resolução de Conflitos de Chaves:** Cruzamento relacional das 5 bases utilizando o fluxo de chaves `subscription_id ➔ account_id`, garantindo que a volumetria de uso diário de features fosse correlacionada sem perdas ao MRR real de cada assinatura ativa ou cancelada.
3.  **Modelagem Heurística de Risco (Risk Score):**
    *   Desenvolvimento de um score de risco ponderado estruturado de **0 a 2**.
    *   **Critério 1 (Baixo Engajamento):** Uso diário médio nos últimos logs inferior a **5.0 interações** (indica desengajamento agudo).
    *   **Critério 2 (Frustração Técnica):** Média de erros diários reportados superior ou igual a **2.0 erros** (indica experiência técnica crítica).
    *   Contas que acendem ambos os alertas simultaneamente recebem **Risk Score 2 (Risco Crítico)**.