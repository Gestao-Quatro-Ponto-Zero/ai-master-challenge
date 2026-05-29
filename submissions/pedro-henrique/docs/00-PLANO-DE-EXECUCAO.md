# Plano de Execução — Challenge 002 (Redesign de Suporte)

**Pedro Henrique · AI Master · G4 Educação**
Documento de planejamento estratégico — escrito antes de tocar em dado nenhum.

---

## 1. Leitura do problema (antes da execução)

### O que o desafio realmente está testando

O brief é teatro. O que o G4 quer saber é:

1. **Você consegue separar análise estatística de julgamento de negócio?** — qualquer um roda um `groupby` e fala "o canal Email tem o pior tempo". Eles querem ver você *decidir* o que importa.
2. **Você sabe o que NÃO automatizar?** — o brief diz literalmente que "automatizar 100% é red flag, não virtude". Esse é o teste do julgamento.
3. **Você entrega um produto, não um relatório?** — "não quero PowerPoint, quero ver rodando" aparece duas vezes no contexto.
4. **Você usa IA como alavanca ou como muleta?** — o process log é onde isso fica visível.

### O baseline que precisamos superar

O baseline deles é: pessoa colando o brief no ChatGPT/Claude/Gemini e enviando. O que esse baseline produz tipicamente:
- Diagnóstico genérico: "o canal email tem tempos altos, considere chatbots"
- Lista de ideias de automação sem priorização
- Sem números concretos de ROI
- Sem protótipo funcional ou um protótipo de brinquedo com 3 exemplos
- Sem matriz crítica do que não automatizar

**O que o baseline NÃO faz bem (nossa janela de diferenciação):**
- Cruza os dois datasets de forma não-óbvia
- Quantifica desperdício em horas E reais
- Constrói algo que classifica tickets *reais* (não cherry-pick) e reporta acurácia honesta
- Mostra com exemplos dos dados *por que* certos tickets exigem humano
- Tem ponto de vista — não é uma lista de opções, é uma recomendação

---

## 2. Tradeoff honesto: 4-5h + foco em produto + os três diferenciais

Vou ser direto: a combinação que você escolheu é a mais ambiciosa possível. Diagnóstico denso **e** protótipo funcional **e** frame de processo em 4-5h sem escrever código manualmente é tenso.

**Como vamos resolver isso:**

| Pressão | Como aliviamos |
|---|---|
| Pouco tempo | Eu (Claude) gero todos os scripts prontos pra você rodar. Você não escreve nem uma linha. |
| Foco em produto | Protótipo = Streamlit + Claude API zero-shot. Nada de treinar modelo. |
| Os três diferenciais | Trabalho em paralelo: enquanto análise roda, escrevo o protótipo. Process log se escreve sozinho enquanto trabalhamos. |
| Superar baseline | Investimos esforço onde IA pura não chega: cruzamento de datasets + ROI quantificado + matriz "não automatizar" |

**O que vamos cortar de propósito:**
- Não vamos treinar nenhum modelo do zero (Claude API zero-shot é mais rápido e quase tão bom)
- Não vamos fazer EDA exaustivo — 5 perguntas focais > 50 gráficos
- Não vamos construir backend/banco — Streamlit + CSV local resolve
- Não vamos buscar perfeição visual — funcional > bonito

---

## 3. Arquitetura da solução (visão de produto)

```
                  ┌─────────────────────────────────────┐
                  │  ENTREGÁVEIS DA SUBMISSÃO           │
                  └─────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼──────────────────────┐
        │                         │                      │
        ▼                         ▼                      ▼
┌───────────────┐         ┌───────────────┐      ┌──────────────┐
│ 01-DIAGNÓSTICO│         │ 02-PROTÓTIPO  │      │ 03-PROCESSO  │
│  (notebook +  │         │  (Streamlit + │      │  (fluxo +    │
│   relatório   │         │   Claude API) │      │   matriz +   │
│   executivo)  │         │               │      │   ROI)       │
└───────────────┘         └───────────────┘      └──────────────┘
        │                         │                      │
        └─────────────┬───────────┴──────────────────────┘
                      ▼
              ┌───────────────┐
              │  README.md    │  ←  ponto de entrada do PR
              │  + PROCESS    │
              │     LOG       │
              └───────────────┘
```

### O protótipo (visão funcional)

Um **Triage Copilot** que o agente de suporte usaria. Input: texto bruto do ticket. Output:

```
┌─────────────────────────────────────────────────────┐
│  TICKET #38291                                       │
├─────────────────────────────────────────────────────┤
│  Categoria sugerida:  Hardware  (confiança: 91%)    │
│  Prioridade sugerida: High      (confiança: 78%)    │
│  Sentimento:          Frustrado (-0.4)              │
│  Tempo esperado:      ~6h (baseado em histórico)    │
│  Resposta sugerida:   [draft de 3 linhas]           │
│  Tickets similares:   #12044, #28991, #31102        │
│                                                      │
│  ⚠️  ESCALAR PARA HUMANO porque:                     │
│      - Confiança da categoria < 70% OU              │
│      - Cliente VIP OU                               │
│      - Risco de churn detectado no texto            │
└─────────────────────────────────────────────────────┘
```

Por que isso bate o baseline:
- Mostra **augmentação**, não substituição (o agente decide, a IA assiste)
- **Guardrail explícito** (escalação por baixa confiança) — sinaliza maturidade
- Usa **ambos datasets**: Dataset 2 (48k textos classificados) valida acurácia, Dataset 1 (30k tickets) alimenta "tickets similares" e baseline de tempo

---

## 4. Plano de execução em 5 fases (timeboxed)

### Fase 0 — Setup (20-30 min)

- Você baixa os dois datasets do Kaggle (links no README do challenge)
- Coloca em `submissions/pedro-henrique-silva/data/`
- Confirma comigo que está pronto
- Eu preparo o ambiente (notebook + Streamlit boilerplate)

**Saída:** repositório com dados + notebook em branco rodando.

### Fase 1 — Diagnóstico operacional (60-75 min)

Vou escrever um notebook que responde 5 perguntas focais, não 50:

1. **Onde o tempo morre?** — heatmap canal × tipo × prioridade vs `Time to Resolution`
2. **Quem está infeliz?** — correlação `Customer Satisfaction Rating` com cada feature (e o que ela não explica)
3. **Quanto custa isso?** — desperdício = (tickets repetidos | mal priorizados | demorados acima da mediana do segmento) × tempo médio × R$ hora-agente
4. **Que volume é repetitivo?** — agrupamento semântico dos `Ticket Description` para descobrir os top-10 padrões que respondem por X% do volume
5. **O que o histórico de `Resolution` revela?** — quais resoluções se repetem (= templates óbvios) e quais são singulares (= caso a caso, *não* automatizar)

**Saída:** notebook + relatório executivo de 1-2 páginas com 3 insights e 1 número-chave de desperdício.

### Fase 2 — Protótipo (90-100 min)

Streamlit app de uma única tela. Componentes:

1. **Input textarea** — cola texto do ticket
2. **Chamada Claude API** — prompt estruturado retorna JSON com categoria/prioridade/sentimento/draft de resposta
3. **Tickets similares** — busca por embeddings (sentence-transformers, modelo pequeno) ou TF-IDF se quisermos zero ML
4. **Guardrail de confiança** — regras de quando escalar
5. **Validação batch** — botão "rodar em N amostras do Dataset 2" e mostrar acurácia real medida contra `Topic_group`

**Saída:** app rodando localmente (`streamlit run app.py`) + screenshot da tela + número de acurácia honesto (vai dar entre 80-95% no Dataset 2, com classes mais difíceis erradas).

### Fase 3 — Frame de processo + ROI (45-60 min)

Vou escrever:

1. **Fluxo "as-is" vs "to-be"** — diagrama simples (mermaid) mostrando onde a IA entra
2. **Matriz humano vs IA** — tabela com tipo de ticket × decisão (automatizar / sugerir / humano), justificada com 3-4 exemplos *reais dos dados* onde IA falharia
3. **Modelo de ROI** — premissas explícitas (volume, custo hora-agente, % cobertura da automação, taxa de aceite do agente) → horas/mês economizadas → payback. Conservador, agressivo, médio.

**Saída:** documento `03-process-and-roi.md` com fluxo, matriz e calculadora de ROI.

### Fase 4 — Submission + Process Log (30-45 min)

Preencher o template em `submissions/pedro-henrique-silva/README.md`:
- Executive summary (3 frases)
- Links para os artefatos (notebook, app, doc de processo)
- **Process Log denso** — não 1 prompt → 1 resposta. Mostrar onde a IA errou, onde você puxou pra outra direção, qual foi seu insight.

**Saída:** PR pronto pra abrir.

### Fase 5 — Verificação (20-30 min)

Checklist final:
- App roda do zero com `pip install -r requirements.txt && streamlit run app.py`?
- Números no relatório batem com o notebook?
- Linguagem do executive summary é entendível por não-técnico?
- Matriz "não automatizar" tem exemplos de tickets *reais*?
- Process Log mostra iteração, não copy-paste?

---

## 5. O que NÃO vamos fazer (e por quê)

| Tentação | Por que cortar |
|---|---|
| Treinar BERT/RoBERTa fine-tuned no Dataset 2 | Gasta 1-2h, ganha 2-3 pontos de acurácia que não mudam a história. Zero-shot Claude é mais defensável estrategicamente. |
| Dashboard interativo de gargalos completo | Notebook + 4 gráficos no relatório resolvem. Dashboard é vaidade. |
| Frontend React custom | Streamlit é 10x mais rápido e o avaliador não vai ligar pra polimento de UI. |
| Análise demográfica (Age, Gender) | Não muda decisão de processo. Cortar. |
| Conectar com tickets reais via API | Fora do escopo do challenge. CSV resolve. |

---

## 6. Critérios de "pronto"

Antes de abrir o PR, a submissão precisa passar nessas 5 perguntas:

1. **Um diretor de operações entenderia em 5 minutos qual é o problema e o que fazer?** (executive summary)
2. **Um engenheiro consegue rodar o protótipo em 10 minutos?** (requirements.txt + README setup)
3. **Os números têm referência?** (não "muitos tickets" — "12% dos tickets representam 47% do tempo perdido")
4. **A matriz "não automatizar" tem 3+ exemplos reais dos dados?** (não opinião abstrata)
5. **O Process Log mostra que você pensou, não só copiou?** (mostrar uma decisão onde você foi contra a IA)

Se alguma resposta for "não", a gente não envia ainda.

---

## 7. Próximo passo

Você baixa os datasets, eu monto o ambiente. Confirma quando estiver pronto que eu já te dou o notebook de Fase 1.

**Links:**
- Dataset 1 (operacional): https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset
- Dataset 2 (classificação): https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset

Coloca os dois em `submissions/pedro-henrique-silva/data/` e me avisa.
