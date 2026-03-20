# Prompt 006 — Agent Relatório Executivo

**Data:** 2026-03-20
**Agent:** gerado via Claude Code (sem 05_report_agent.py como script separado)
**Ferramenta:** Claude Code
**Executado por:** Lucas Reis

---

## Prompt enviado ao Claude Code

> Contexto: projeto G4 AI Master Challenge — Challenge 001 Diagnóstico de Churn.
> Leia o CLAUDE.md e docs/data_dictionary.md antes de começar.
>
> Você é o Agent 05 — Relatório Executivo. Sua missão é transformar todos os
> achados dos agents anteriores em um relatório que o CEO da RavenStack leia
> em 5 minutos e saiba exatamente o que fazer na segunda-feira.
>
> Leia antes de escrever:
> 1. process-log/entries/entry_001_eda_analysis.md
> 2. process-log/entries/entry_002_cross_table_analysis.md
> 3. process-log/entries/entry_003_hypothesis_analysis.md
> 4. process-log/entries/entry_004_model_analysis.md
> 5. solution/churn_scores.csv (para os números finais)
>
> Gere solution/executive_report.md com estrutura:
> TL;DR → Churn real → Causa raiz → Paradoxo do uso → ML revelou →
> Quem está em risco → 3 ações priorizadas → O que NÃO fazer → Limitações → Metodologia
>
> Gere também executive_summary_1page.md (máx 1 página para o CEO).
> Preencha prompt_006_report.md e escreva entry_005_report_review.md.

---

## Output gerado

- `solution/executive_report.md` — relatório completo (~5 min de leitura para CEO)
- `solution/executive_summary_1page.md` — resumo executivo de 1 página (~2 min)
- `process-log/entries/entry_005_report_review.md` — análise crítica do relatório

## Estrutura do relatório

1. TL;DR (3 frases com números-chave)
2. Churn real: 22% — 110 contas, $229K MRR
3. Causa raiz: product-market fit segmental (60.9% features, OR 2.5×)
4. Paradoxo do uso: churners usam +3.4% mais features (não é adoção)
5. O que o ML revelou: AUC=0.34, churn não tem precursor comportamental
6. Quem está em risco: $710K MRR + 10 contas HIGH risk ativas ($12,231)
7. 3 ações: CS quick win → product gap audit → ICP revision
8. O que NÃO fazer: onboarding, SLA suporte, segmentação por plano
9. Limitações: n=500, dataset sintético, sem NLP de feedback_text
10. Metodologia: links para código e process log

## Decisão editorial

**Prioridade ao paradoxo do uso:** Este achado é o mais contraintuitivo e o mais importante
estrategicamente. A narrativa "churners usam mais que retidos" destrói o frame padrão de
"problema de onboarding" que a maioria das empresas adotaria por default.

**O ML como ferramenta de diagnóstico, não de predição:** Em vez de esconder o AUC=0.34,
o relatório o usa como evidência central: "o modelo falhou, e isso prova que o problema
é de produto, não de comportamento". Esta inversão transforma um resultado ruim em insight.

**Números do cross-table são mais confiáveis que o modelo:** A lista de contas em risco
usa preferencialmente a análise de múltiplos sinais ($710K, A-e43bf7 com 4/4 sinais),
não apenas os scores do modelo com AUC baixo. O relatório documenta esta limitação.

## Reflexão final

**O que a IA sozinha não teria capturado:**
1. A interpretação do AUC < 0.5 como *descoberta positiva*, não falha técnica
2. A distinção entre "poder estatístico insuficiente" (H1, H2) e "hipótese genuinamente nula" (H3, H5)
3. A narrativa do "cozinheiro que usou todos os utensílios mas não tinha a faca certa"
4. A recomendação explícita de "o que NÃO fazer" (baseada em hipóteses refutadas)
5. A conexão entre canal event (OR 2.5×) e a decisão de revisar ROI de eventos vs partner
