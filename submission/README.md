# Submissão — Eduardo Hasson — Challenge 002

## Sobre mim

- **Nome:** Eduardo Hasson
- **LinkedIn:** 
- **Challenge escolhido:** 002 — Redesign de Suporte (Operações / CX)

---

## Executive Summary

Analisei ~8,5k tickets operacionais e ~48k tickets classificados. O principal problema não é um canal específico, e sim a **ausência de triagem inteligente**: 67% dos tickets permanecem abertos ou pendentes e a satisfação média dos tickets fechados está estagnada em 2,99/5.

Propus um fluxo de automação realista que classifica, prioriza e sugere respostas apenas para tickets de baixo risco, enquanto protege casos sensíveis (refunds, hardware complexo, linguagem emocional e baixa confiança do modelo).  

Entreguei um **protótipo funcional** (TF-IDF + Logistic Regression, 85,3% de acurácia) que demonstra a classificação + decisão de roteamento + resposta sugerida em tempo real.

**Principal recomendação:** implementar triagem automática com regras de “o que não automatizar” antes de qualquer tentativa de resposta 100% autônoma.

---

## Solução

### Abordagem

1. **Diagnóstico quantitativo** do Dataset 1 (métricas operacionais + texto).
2. **Análise de classificação** com o Dataset 2 (48k tickets já rotulados em 8 categorias).
3. Definição clara do que automatizar e, principalmente, **do que não automatizar**.
4. Construção de um protótipo mínimo viável que prova o conceito.

Priorizei julgamento de processo e realismo operacional em vez de maximizar automação.

### Resultados / Findings

#### 1. Diagnóstico Operacional

| Métrica | Valor | Interpretação |
|---------|-------|---------------|
| Tickets não fechados (Open + Pending) | **67,3%** | Backlog estrutural. Time acima da capacidade. |
| Satisfação média (apenas Closed) | **2,99 / 5** | Estagnada. Quase neutra. |
| Diferença de satisfação entre canais | Muito pequena (Chat 3,08 → Phone 2,95) | O problema não é canal. |
| Pior combinação observada | Social media + Technical issue | Satisfação mais baixa. |
| Volume por tipo e canal | Quase equilibrado | Não existe um “vilão” de volume. |

**Conclusão do diagnóstico:**  
A operação gasta capacidade humana em tickets de baixa complexidade e falta de triagem inteligente, enquanto tickets complexos e de alto risco emocional competem no mesmo fluxo.

#### 2. Proposta de Automação

**O que automatizar:**
- Classificação automática do ticket
- Sugestão de prioridade
- Roteamento para a fila correta
- Respostas sugeridas para tickets de baixo risco e alta confiança
- Detecção de linguagem emocional alta

**O que NÃO automatizar (e por quê):**

| Situação | Motivo de não automatizar |
|----------|---------------------------|
| Refund e Cancellation com reclamação | Envolve dinheiro + alto risco de churn |
| Technical issue complexo / intermitente | Exige diagnóstico em etapas |
| Linguagem emocional forte | Resposta genérica piora a situação |
| Baixa confiança do modelo (< 70%) | Melhor escalar do que errar |
| Direitos administrativos e compras | Risco de segurança e orçamento |

**Fluxo proposto:**

```
Ticket chega
    ↓
IA classifica + calcula confiança + detecta emoção
    ↓
┌─────────────────────────────────────────────────────┐
│ Alta confiança + baixo risco → resposta sugerida    │
│                     + fila N1 (revisão rápida)      │
│                                                     │
│ Confiança média ou tipo sensível → humano com       │
│                     contexto já preenchido          │
│                                                     │
│ Baixa confiança ou emoção alta → agente sênior      │
└─────────────────────────────────────────────────────┘
    ↓
Agente revisa / edita / descarta a sugestão
    ↓
Feedback do agente melhora o modelo continuamente
```

#### 3. Protótipo Funcional

Localização: pasta `prototype/`

- **Modelo:** TF-IDF + Logistic Regression
- **Acurácia de validação:** 85,3%
- **Categorias:** Hardware, HR Support, Access, Storage, Purchase, Internal Project, Administrative rights, Miscellaneous
- **Regras de negócio embutidas:** prioridade, envio para sênior, quando sugerir resposta
- **Interface:** CLI + Streamlit

**Como rodar:**

```bash
# Instalar dependências
pip install -r requirements.txt

# Via linha de comando
python ticket_ai_assistant.py "texto do ticket aqui"

# Interface visual
streamlit run app_streamlit.py
```

O protótipo retorna:
- Categoria + confiança
- Prioridade sugerida
- Flag “enviar para sênior”
- Resposta sugerida (quando aplicável)
- Detecção de emoção alta
- Top 3 categorias

### Recomendações

1. **Curto prazo (0-30 dias):** Implementar a classificação + roteamento automático com as regras de “não automatizar”. Medir redução de tempo de triagem.
2. **Médio prazo:** Adicionar respostas sugeridas apenas nas categorias de baixo risco e alta confiança. Treinar o time a aceitar/editar/descartar.
3. **Métricas de sucesso:** % de tickets com resposta sugerida aceita, tempo médio de primeira resposta nos tickets simples, satisfação nos tickets automatizados vs. manuais.
4. **Não fazer:** Resposta 100% autônoma em refunds, cancelamentos e problemas técnicos complexos.

### Limitações

- Dataset 1 tem timestamps de resolução ruidosos (valores negativos e inconsistentes) → não foi possível calcular horas desperdiçadas com alta precisão.
- O modelo atual é TF-IDF (rápido e interpretável). Em produção, embeddings + modelo mais moderno melhorariam a acurácia em textos mais ambíguos.
- Templates de resposta são genéricos e precisam ser refinados com a base real de conhecimento da empresa.
- Não foi feito fine-tuning com feedback de agentes (seria o próximo ciclo natural).

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|---------------|
| Grok (xAI) | Análise exploratória, diagnóstico, desenho da proposta de automação, regras de negócio, construção e refinamento do protótipo, estruturação da entrega |
| Python + scikit-learn | Treinamento do classificador e implementação das regras |

### Workflow

1. Li o brief completo e os dois datasets antes de qualquer prompt de solução.
2. Fiz análise exploratória (volume, status, satisfação, cruzamentos) para entender a realidade operacional.
3. Identifiquei que os tempos de resolução eram pouco confiáveis e foquei no backlog + satisfação + padrões de classificação.
4. Desenhei a proposta de automação priorizando o que **não** automatizar (julgamento de processo).
5. Treinei um classificador no Dataset 2 (85,3% de acurácia) e embuti regras de negócio no protótipo.
6. Testei com exemplos reais de diferentes riscos (storage simples, hardware, emoção alta, etc.).
7. Estruturei a entrega focando em clareza para o Diretor de Operações.

### Onde a IA errou e como corrigi

- Em algumas iterações a IA tendia a propor automação excessiva. Corrigi explicitamente limitando resposta automática apenas a categorias de baixo risco + alta confiança.
- Os dados de tempo de resolução do Dataset 1 eram inconsistentes. Em vez de forçar um cálculo de “horas desperdiçadas” impreciso, foquei em backlog e satisfação (mais honestos).

### O que eu adicionei que a IA sozinha não faria

- A distinção clara e justificada do que **não** automatizar (refunds, emoção alta, baixa confiança, direitos administrativos).
- A regra de ouro: “IA só age de forma semi-autônoma quando confiança é alta **e** o risco é baixo”.
- O foco em realismo operacional em vez de maximizar a taxa de automação.
- A decisão de usar um modelo simples e interpretável (TF-IDF) em vez de ir direto para LLM, priorizando velocidade de implantação e explicabilidade para o time de suporte.

---

## Evidências

- Código do protótipo e modelo treinados estão na pasta `prototype/`
- Análise e decisões documentadas neste README
- Process log acima descreve o raciocínio e as correções

---

_Submissão preparada em: 07/08/2026_
