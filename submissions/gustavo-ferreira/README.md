# Submissão — Gustavo Ferreira — Challenge 002

## Sobre mim

- **Nome:** Gustavo Ferreira
- **Challenge escolhido:** 002 — Redesign de Suporte

---

## Executive Summary

Analisei o dataset de ~8.500 tickets de suporte e descobri que **67.3% estão sem resolução** (backlog permanente), a **priorização é atribuída uniformemente** (sem critério), e o **CSAT é estatisticamente aleatório** (distribuição uniforme perfeita). Fui transparente sobre as limitações dos dados sintéticos — os timestamps são fabricados, os textos de resolução são gibberish, e o README do challenge erra ao dizer que há 3 tipos de ticket (são 5, incluindo Refund e Cancellation que representam 40.7% do volume). Construí um **protótipo funcional em Streamlit** com dashboard executivo, simulador de triagem com IA em tempo real, e proposta de automação em 4 níveis que estima uma economia de **R$ 42.405/ano** automatizando 33.4% dos tickets — sendo explícito que **Cancellation e Refund NUNCA devem ser automatizados**.

---

## Solução

### Abordagem

1. **EDA profunda primeiro** — Antes de qualquer análise, explorei os dados coluna por coluna e documentei 6 achados críticos de qualidade
2. **Honestidade sobre os dados** — Em vez de fingir correlações que não existem (CSAT vs tempo = r ≈ -0.001), admiti que os dados são sintéticos e foquei no que é válido
3. **Design de processo independente dos dados** — Os 4 níveis de roteamento (Auto-resolve → Agent Assist → Human Required → Escalação) são design de processo válido independente da qualidade dos dados
4. **Protótipo funcional como herói** — Como os dados são sintéticos, o valor real está em demonstrar um sistema que funciona com tickets reais digitados pelo avaliador

### Resultados / Findings

#### Diagnóstico Operacional

| Achado | Valor | Implicação |
|--------|-------|-----------|
| Backlog | 67.3% sem resolução | 5.700 tickets parados = horas desperdiçadas |
| CSAT | Distribução uniforme (~550/nota) | Métrica quebrada — não reflete satisfação real |
| Priorização | ~25% em cada nível | Sem critério — Critical tratado igual a Low |
| Ticket Types | 5 (não 3 como README diz) | Refund + Cancellation = 40.7% do volume |
| Timestamps | Fabricados (2023 vs compras 2020-2021) | Análise temporal inválida |
| Resolution | Gibberish (palavras aleatórias) | Impossível usar para FAQ/base de conhecimento |

#### Proposta de Automação — 4 Níveis

| Nível | Quando | % Tickets | Automação |
|-------|--------|:---------:|-----------|
| 🟢 Auto-resolve | FAQ, consultas simples | ~25% | IA responde sozinha |
| 🔵 Agent Assist | Problemas técnicos, acessos | ~35% | IA prepara rascunho, humano revisa |
| 🟡 Human Required | Reembolsos, disputas financeiras | ~30% | Agente sênior obrigatório |
| 🔴 Escalação | Cliente furioso, cancelamento | ~10% | Supervisor imediato |

#### Protótipo Funcional

Webapp em Streamlit com 4 telas:
- **Dashboard do Diretor**: KPIs, gráficos de status, heatmap canal × tipo, economia projetada
- **Simulador de Triagem IA**: Classificação em tempo real com sentimento, prioridade, roteamento e rascunho de resposta
- **Proposta de Automação**: 4 níveis de roteamento, fluxo visual, o que NÃO automatizar, ROI
- **Análise Cruzada (Datasets 1 + 2)**: Distribuição do DS2, comparação textual lado a lado, viabilidade de transferência

**Para rodar:**
```bash
cd submissions/gustavo-ferreira/solution
pip install -r requirements.txt
streamlit run app.py
```

### Recomendações

1. **Imediato**: Implementar sistema de priorização baseado em regras (substituir a atribuição uniforme atual)
2. **Curto prazo (1-2 semanas)**: Deploy do classificador por regras semânticas para triagem automática Nível 1 e 2
3. **Médio prazo (2-5 semanas)**: Integração com LLM para Agent Assist (rascunhos automáticos com revisão humana)
4. **Longo prazo**: Métricas de CSAT reais (NPS pós-resolução) para medir impacto da automação

### Limitações encontradas nos dados

Durante a EDA, identifiquei **6 problemas críticos de qualidade** que impactam diretamente o que é possível extrair dos datasets:

#### Dataset 1 — Problemas que invalidam análises tradicionais

| Problema | O que encontrei | Impacto na análise |
|----------|----------------|-------------------|
| **Timestamps fabricados** | `Date of Purchase` é de 2020-2021, mas `FRT` e `TTR` são todos de 31/Mai a 02/Jun/2023 | Análise temporal (SLA, tempo médio de resolução) é inválida |
| **Paradoxo temporal** | 49% dos tickets fechados têm `TTR < FRT` (resolução antes da primeira resposta) | Impossível calcular tempo real de atendimento |
| **CSAT aleatório** | Distribuição perfeitamente uniforme (~550 respostas por nota, 1 a 5). Pearson r = -0.001 vs tempo | CSAT não reflete satisfação real. Correlações são ruído |
| **Textos sintéticos** | 100% das descrições contêm `{product_purchased}` como placeholder literal | NLP/análise de sentimento impossível nestes textos |
| **Resoluções gibberish** | Texto tipo `"Try capital clearly never color toward story"` — palavras aleatórias | Impossível construir base de FAQ ou knowledge base |
| **README erra Ticket Types** | README diz 3 tipos, mas existem 5. Refund request + Cancellation request = 40.7% do volume | Ignorar esses tipos perde quase metade da operação |

#### Dataset 2 — Limitações de formato e domínio

| Problema | O que encontrei | Impacto |
|----------|----------------|---------|
| **Textos pré-processados** | Stopwords removidas, tokenizado. Ex: `"microsoft locat server new locat appl mobil"` | Não é linguagem natural — inadequado para NLP moderno |
| **Domain shift** | Categorias de TI corporativa (Hardware, HR Support, Storage) vs suporte B2C (Billing, Refund) | Transfer learning DS2→DS1 produz resultados enganosos |

#### Limitações da solução proposta

- **Classificação por regras semânticas**: O simulador usa keyword matching, não ML/LLM. Funciona bem para demonstração, mas em produção seria substituído por API de LLM para maior acurácia com linguagem natural
- **ROI baseado em benchmarks**: Premissas (R$45/hora, AHT 20 min) são benchmarks brasileiros, não dados reais da empresa. O ROI real exigiria dados de folha de pagamento e métricas internas
- **Sem validação em dados reais**: O protótipo foi testado com exemplos escritos manualmente. Validação com tickets reais da operação é necessária antes de deploy

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.
> 
> **Formato escolhido:** Narrativa escrita. O documento completo está em [`process-log/workflow.md`](./process-log/workflow.md).

Resumo do que está documentado no process log:

- **Ferramenta usada:** Claude Opus 4.6 (Antigravity) como único assistente de IA, integrado no editor de código
e- **Decomposição do problema:** Hipóteses documentadas ANTES da EDA — todas se provaram erradas, o que redirecionou a abordagem
- **~17 iterações com a IA** ao longo de 8 etapas (EDA → análise → textos → DS2 → pivô → diagnóstico → protótipo → documentação)
- **7 erros da IA documentados** — desde assumir tipos de dados errados até propor premissas financeiras infladas
- **6 contribuições minhas** que a IA sozinha não faria — desde o pivô dados→solução até decisão de NÃO automatizar
- **Pivô explícito:** Após descobrir que os dados são sintéticos, decidi focar na **solução funcional** em vez de insistir em análise estatística sobre ruído

O processo completo, incluindo cada prompt, cada erro e cada decisão, está narrado passo a passo em [`process-log/workflow.md`](./process-log/workflow.md).

---

## Evidências

- [x] Narrativa escrita do workflow completo ([`process-log/workflow.md`](./process-log/workflow.md))
- [x] Git history (construção iterativa do código)

---

_Submissão enviada em: 16/03/2026_
