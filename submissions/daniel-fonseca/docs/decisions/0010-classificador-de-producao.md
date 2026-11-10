# 0010 — Classificador de produção: RAG por similaridade como classificador único; LLM redige

- **Status:** Aceita — Daniel escolheu o RAG como classificador principal (2026-11-09); parâmetros recomendados pela IA a partir da medição
- **Data:** 2026-11-09
- **Origem:** IA (avaliação e calibração) · Daniel (decisão: RAG único, por domínio e por ser o caso prático de LLM; aceita perder alguns pontos percentuais)
- **Evidência:** `solution/analysis/03`–`08_*.py` → `output/*.json`

## O que a avaliação mostrou (holdout de 9.567 tickets do DS2)

| Método | Acurácia | Observação |
|---|---|---|
| TF-IDF + regressão logística | 86,9% | O mais preciso, mas exige um modelo treinado rodando em nó de código |
| **RAG — voto dos vizinhos (512 dims, k=50, peso sim¹⁶)** | **82,8%** | **Escolhido.** Ajuste do voto: +0,7 p.p. sobre o padrão (k=15) |
| RAG híbrido (semântico + palavras-chave, RRF) | 82,8% | Sem ganho → descartado (mais complexo, mesmo resultado) |
| RAG 1536 dims (melhor ajuste) | 83,3% | +0,5 p.p. → não compensa o índice 3× maior na instância free |
| LLM zero-shot (400 tickets) | 43,2% | Confiança declarada ≥ 0,9 acerta só 62% |
| **RAG + LLM** (LLM vê os 15 casos parecidos; 400 tickets) | 80,8% | **O RAG quase dobrou o acerto do LLM (43% → 81%)**, mas não superou o voto simples (80,8% na mesma amostra) |

## Decisão
1. **Classificação = voto ponderado dos 50 tickets mais parecidos** no pgvector (512 dims `halfvec`, HNSW). Roda numa função SQL no Supabase → o n8n só chama, sem modelo em nó de código.
2. **Confiança = fração de votos da categoria vencedora** — calibrada (≥ 0,9 → 98,7% de precisão), ao contrário da confiança declarada pelo LLM.
3. **LLM (OpenAI) entra onde agrega:** redige o rascunho de resposta do nível 2 com base nos casos parecidos e nas soluções validadas (ADR-0004), e resume o ticket no alerta do nível 3. Não decide categoria nem nível — isso não melhorou o acerto e acrescentaria custo e latência.

## Política de 3 níveis calibrada (substitui os números da ADR-0005)
Regra: **nível 3** se a categoria prevista é sensível (HR Support, Administrative rights), se ≥ 30% dos votos caem em categoria sensível, ou se a confiança é < 0,5. **Nível 1** se a confiança é ≥ 0,9. **Nível 2** no resto.

| Nível | % do DS2 | Precisão da classificação |
|---|---|---|
| 1 — Automático | 31,2% | 98,8% |
| 2 — Revisão humana | 28,4% | 81,2% |
| 3 — Só humano | 40,5% | 71,6% |

- **Custo da escolha pelo RAG único:** o nível 1 cai de 35,9% (TF-IDF + RAG) para 31,2% dos tickets, com precisão praticamente igual (98,8% × 99,2%).
- **Risco residual:** 15 tickets realmente sensíveis (0,5% do nível 1) cairiam no automático. Mitigação: auditoria amostral do nível 1 + lista de palavras de bloqueio antes do envio.
- **Ponte para o DS1 (ADR-0009):** 44,4% elegíveis × 52,4% de nível 1 entre não sensíveis ≈ **23% de automação total** → ~7.000 tickets, ~1.000 h e ~R$ 21 mil por ano só no nível 1, só em mão de obra direta.

## Possível melhoria não testada
`text-embedding-3-large` (~US$ 0,30 para recarregar o DS2) pode render alguns pontos no RAG. Fica como experimento opcional.
