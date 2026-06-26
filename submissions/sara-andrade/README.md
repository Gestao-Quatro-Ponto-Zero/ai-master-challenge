# Submissão — Sara Andrade — Challenge 002

## Sobre mim

**Nome:** Sara Andrade 
**LinkedIn:** www.linkedin.com/in/sara-andradee
**Challenge escolhido:** 002 — Redesign de Suporte

---

## Executive Summary

Construí o **CX Triage Copilot**, um protótipo FastAPI para triagem de tickets que classifica solicitações, aplica confidence gates e decide entre `AUTO_RESOLVE`, `AGENT_ASSIST` e `HUMAN_ESCALATION`. A principal decisão do projeto foi **não automatizar em cima de métricas operacionais que não sustentam conclusões reais**: o Dataset 1 tem 8,469 registros, mas 100% das descrições contêm o placeholder `{product_purchased}`, 49.3% dos tickets fechados têm resolução antes da primeira resposta e os tempos positivos restantes não diferem por canal de forma significativa (`Kruskal p=0.791`). Por isso, usei o Dataset 1 para auditoria, desenho de guardrails e contexto B2C; e usei o Dataset 2, com 47,837 tickets classificados de IT, para treinar o classificador que alimenta o protótipo. O modelo selecionado foi TF-IDF + Logistic Regression, com acurácia de 86.4% e F1 macro de 86.3%, superando o baseline ComplementNB.

---

## 1. Solução

A solução é um serviço de triagem com **FastAPI**, não apenas um dashboard. A escolha por API foi deliberada: um roteador de suporte real precisa receber tickets de Zendesk, Intercom, Freshdesk, HubSpot ou outro sistema e devolver uma rota operacional.

### O que a API faz

Quando um ticket entra, o serviço retorna:

- domínio provável: `B2E_IT` ou `B2C_EXTERNAL`;
- categoria IT, quando aplicável;
- confiança do modelo;
- rota operacional: `AUTO_RESOLVE`, `AGENT_ASSIST` ou `HUMAN_ESCALATION`;
- justificativa da decisão;
- resposta sugerida;
- termos de risco detectados.

### Arquitetura

```text
Ticket entra
   │
   ▼
[1] Roteador de domínio
   ├── B2E_IT ─────────► Classificador IT + confidence gate
   │                         ├── alta confiança + baixo risco → AUTO_RESOLVE
   │                         ├── confiança média → AGENT_ASSIST
   │                         └── baixa confiança/risco → HUMAN_ESCALATION
   │
   └── B2C_EXTERNAL ───► sem auto-resolução neste protótipo
                             ├── risco financeiro/emocional/crítico → HUMAN_ESCALATION
                             └── demais casos → AGENT_ASSIST
```

Essa arquitetura incorpora a principal tese do projeto: **IA deve atuar onde há sinal validado e recuar onde há risco, baixa confiança ou mudança de domínio**.

---

## 2. Abordagem

### 2.1. Primeiro passo: auditar antes de automatizar

O erro mais perigoso neste challenge seria aceitar as métricas como verdade e construir um ROI preciso em cima de dados sintéticos. Por isso, comecei com auditoria de confiabilidade:

| Teste | Resultado | Decisão |
|---|---:|---|
| Registros Dataset 1 | 8,469 | Descrever a amostra real, sem repetir o “~30k” literalmente |
| Registros Dataset 2 | 47,837 | Usar como base principal de classificação textual |
| Descrições D1 com `{product_purchased}` | 100.0% | Tratar texto D1 como template/sintético |
| Tickets fechados com delta negativo | 49.3% | Não usar tempos para ROI/gargalo causal |
| CSAT uniforme | `p=0.797` | Não inferir causalidade de satisfação |
| Status × canal | `p=0.771` | Não afirmar gargalo específico por canal |
| Delta positivo × canal | `p=0.791` | Não priorizar canais por “desperdício” temporal |
| Texto D1 → Ticket Type | acc. 21.0% | Não usar D1 para treinar classificador de tipo |

### 2.2. Correção do número 67,3%

O número `67,3%` aparece na análise, mas com a interpretação correta:

```text
Open:                      2,819 = 33,3%
Pending Customer Response: 2,881 = 34,0%
Closed:                    2,769 = 32,7%

Open + Pending = 67,3% não fechados
```

Conclusão correta:

> 67,3% dos tickets da amostra não estão fechados, mas apenas 34,0% estão em `Pending Customer Response`. Como status é independente do canal nesta base, esse número descreve a amostra, não prova um gargalo operacional real.

---

## 3. Resultado

### 3.1. Comparação de modelos

Treinei dois modelos simples, auditáveis e reproduzíveis no Dataset 2.

| Modelo | Acurácia | F1 macro | Uso |
|---|---:|---:|---|
| ComplementNB baseline | 80.9% | 79.7% | Baseline técnico |
| LogisticRegression selecionado | 86.4% | 86.3% | Modelo final da API |

A Logistic Regression foi escolhida porque tem melhor performance geral e melhor cobertura sob confidence gate.

### 3.2. Confidence gate

No modelo selecionado:

| Threshold | Cobertura | Acurácia dentro do gate |
|---:|---:|---:|
| 0.50 | 88.1% | 91.0% |
| 0.60 | 79.7% | 93.5% |
| 0.70 | 71.3% | 95.5% |
| 0.80 | 61.5% | 97.3% |
| 0.85 | 55.3% | 98.2% |
| 0.90 | 48.2% | 98.8% |
| 0.95 | 37.9% | 99.6% |

O ponto operacional recomendado é `0.80`: ele cobre 61.5% dos tickets B2E/IT com 97.3% de acurácia dentro do gate.

### 3.3. Domain shift

Ao aplicar o classificador IT do Dataset 2 no texto do Dataset 1, a distribuição colapsa:

```text
Hardware                 7551
Access                    561
Administrative rights     153
Miscellaneous             147
HR Support                 45
Storage                     7
Internal Project            5
```

Isso confirma que o modelo não deve ser aplicado cegamente em tickets B2C externos. O sistema usa esse achado como guardrail: **B2C externo não é auto-resolvido neste protótipo**.

---

## 4. Proposta de automação

### Automatizar

Automatizar apenas em contexto B2E/IT quando:

- categoria é elegível (`Access`, `Hardware`, `Storage`, `Purchase`);
- confiança ≥ 0.80;
- prioridade é `Low` ou `Medium`;
- não há termos de risco;
- o ticket não envolve direitos administrativos, RH, jurídico, privacidade, fraude, reembolso ou cancelamento.

### Assistir agente

Usar `AGENT_ASSIST` para:

- tickets B2C externos sem risco crítico;
- IT tickets com confiança média;
- categorias com necessidade de revisão;
- tickets longos que precisam de resumo, checklist ou resposta rascunho.

### Escalar humano

Usar `HUMAN_ESCALATION` para:

- prioridade `Critical`;
- baixa confiança;
- refund/cancellation;
- linguagem emocional forte;
- risco jurídico, financeiro, privacidade ou fraude;
- direitos administrativos e casos de RH.

---

## 5. Como rodar

### Instalar dependências

```bash
pip install -r requirements.txt
```

### Rodar API

```bash
cd solution
uvicorn app:app --reload
```

Depois abra:

```text
http://127.0.0.1:8000/docs
```

Use o Swagger para testar o endpoint `POST /triage`.

### Exemplo de payload

```json
{
  "text": "Please reset my password. I cannot login to my account or access the internal system.",
  "priority": "Medium",
  "channel": "Internal portal",
  "source_context": "b2e_it"
}
```

### Rodar teste em batch

```bash
cd solution
python test_batch.py
```

O script usa 100 tickets reais do Dataset 2, se o CSV estiver disponível, ou os exemplos em `solution/examples/sample_tickets.csv`.

Resultado de referência no batch test incluído no pacote:

```text
AUTO_RESOLVE:     37%
AGENT_ASSIST:     50%
HUMAN_ESCALATION: 13%
```

Esse resultado é propositalmente conservador: mesmo no domínio B2E/IT, o sistema não automatiza categorias sensíveis nem casos abaixo do gate.

---

## 6. Recomendações

1. **Começar com Agent Assist + auto-roteamento controlado**, não auto-resolução total.
2. **Implantar primeiro em B2E/IT**, onde o Dataset 2 demonstrou sinal textual real.
3. **Não usar métricas temporais do Dataset 1 para ROI ou priorização**, porque elas têm evidência forte de geração sintética.
4. **Usar confidence gate ≥ 0.80 para automação**, com fallback humano abaixo disso.
5. **Separar filas B2C e B2E**, pois os riscos e critérios de automação são diferentes.
6. **Monitorar taxa de aceite do agente, reabertura, CSAT real e erro por categoria** antes de expandir a automação.

---

## 7. Limitações

- Os datasets são públicos e não representam necessariamente uma única empresa real.
- O roteador B2C/B2E tem performance alta porque os domínios dos datasets são muito diferentes; em produção, deve ser validado com dados reais misturados.
- `predict_proba` de Logistic Regression não substitui calibração formal de probabilidade; uma próxima versão poderia usar calibração isotônica ou Platt scaling.
- O Dataset 1 não permite inferência confiável de gargalo por tempo, canal ou CSAT.
- O protótipo é local e não integra com Zendesk/Intercom; a API foi desenhada para ser integrável.

---

## 8. Process Log

O process log completo está em `process-log/process-log.md`. A evidência principal é a narrativa de iteração: múltiplas IAs sugeriram hipóteses diferentes; cada hipótese foi testada contra os dados; apenas as que sobreviveram foram incorporadas.
