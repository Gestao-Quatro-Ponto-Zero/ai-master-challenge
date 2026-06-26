# Process Log — Como usei IA

Este process log é parte obrigatória da submissão. O objetivo não é mostrar que “usei IA para gerar uma resposta”, mas demonstrar **como usei IA estrategicamente, onde desconfiei das respostas, o que testei e o que corrigi**.

---

## 1. Ferramentas usadas

| Ferramenta | Para que usei | Como validei |
|---|---|---|
| ChatGPT / Universal Primer | Estrutura inicial da solução, proposta de automação, políticas de guardrail | Testei as conclusões contra os CSVs antes de aceitar |
| Claude | Crítica da solução, comparação de abordagens, sugestão de FastAPI e process log mais forte | Reproduzi os números e corrigi interpretações |
| Qwen / outra IA | Insight de separação B2C vs B2E | Mantive como arquétipo, mas não como prova de que os datasets são da mesma empresa |
| Python / pandas / scipy / sklearn | Auditoria de dados, testes estatísticos, modelagem, comparação de modelos | Resultados salvos em `solution/outputs/metrics.json` |
| FastAPI | Protótipo funcional de roteamento | Testável em `/docs` e por `solution/test_batch.py` |

---

## 2. Como decompus o problema antes de promptar

Antes de pedir uma solução para qualquer IA, separei o challenge em quatro perguntas:

1. **Os dados permitem diagnóstico operacional confiável?**
2. **Qual parte dos dados tem sinal suficiente para automação?**
3. **Onde a IA deve atuar e onde deve sair de cena?**
4. **Como provar isso com algo rodando, não só com apresentação?**

Essa decomposição mudou o projeto. Em vez de começar treinando um modelo ou montando dashboard, comecei verificando se as métricas operacionais eram confiáveis.

---

## 3. Iterações realizadas

### Iteração 1 — Ideia genérica de automação

Primeiras respostas de IA sugeriram caminhos previsíveis:

- classificador de tickets;
- roteamento automático;
- dashboard de gargalos;
- resposta sugerida.

Essas ideias eram úteis, mas genéricas. A decisão humana foi transformar isso em uma arquitetura de três rotas:

```text
AUTO_RESOLVE
AGENT_ASSIST
HUMAN_ESCALATION
```

Isso evitou a red flag de “automatizar tudo”.

---

### Iteração 2 — Auditoria do Dataset 1

Antes de aceitar diagnósticos por canal, prioridade ou CSAT, auditei o Dataset 1.

Principais achados:

| Verificação | Resultado |
|---|---:|
| Registros no Dataset 1 | 8,469 |
| Registros no Dataset 2 | 47,837 |
| Descrições D1 com `{product_purchased}` | 100.0% |
| Tickets fechados com delta negativo | 49.3% |
| CSAT uniforme | `p=0.797` |
| Status × canal | `p=0.771` |
| Delta positivo × canal | `p=0.791` |

Conclusão: o Dataset 1 é útil para demonstrar guardrails e riscos de automação, mas não é confiável para calcular gargalo real por tempo/canal ou ROI baseado em tempo.

---

### Iteração 3 — Correção do “67,3%”

Uma IA interpretou que `67,3%` dos tickets estavam aguardando cliente.

Eu testei:

```text
Open:                      2,819 = 33,3%
Pending Customer Response: 2,881 = 34,0%
Closed:                    2,769 = 32,7%
```

Correção:

```text
Errado: 67,3% aguardando cliente.
Certo: 67,3% não fechados = Open + Pending.
```

Além disso, como `Ticket Status × Ticket Channel` tem `p=0.771`, não usei esse número como evidência de gargalo por canal.

---

### Iteração 4 — Hipótese de auto-close / churn silencioso

Outra hipótese sugerida por IA era que tickets fechados muito rápido indicariam “auto-close” e gerariam churn silencioso.

Eu rejeitei essa narrativa porque:

- muitos tickets “rápidos” se confundem com os deltas negativos;
- a diferença de CSAT não sustentava uma conclusão forte;
- os timestamps parecem sorteados dentro de uma janela artificial.

Decisão: não construir narrativa executiva em cima desse sinal.

---

### Iteração 5 — Insight B2C vs B2E

Um insight de IA que sobreviveu foi a separação semântica entre os datasets:

- Dataset 1: suporte externo/consumo, com produtos como GoPro, LG TV, Philips Hue, Amazon Echo etc.
- Dataset 2: suporte interno/IT, com categorias como Access, Hardware, HR Support, Storage, Purchase.

Eu mantive esse insight, mas com caveat:

> Os datasets representam dois arquétipos úteis de suporte, mas não provam que são filas de uma mesma empresa.

Essa distinção entrou no protótipo como roteamento de domínio.

---

### Iteração 6 — Teste de classificador no Dataset 1

Uma ideia inicial era treinar um classificador usando `Ticket Description` e `Ticket Subject` do Dataset 1 para prever `Ticket Type`.

Teste realizado:

```text
Acurácia: 21.0%
F1 macro: 20.8%
```

Como há 5 classes quase balanceadas, esse resultado é próximo de aleatório. Decisão: **não usar Dataset 1 para classificador de tipo**.

---

### Iteração 7 — Classificador no Dataset 2

No Dataset 2, comparei dois modelos:

| Modelo | Acurácia | F1 macro |
|---|---:|---:|
| ComplementNB baseline | 80.9% | 79.7% |
| LogisticRegression selecionado | 86.4% | 86.3% |

Escolhi Logistic Regression porque venceu em acurácia e F1 macro, mantendo simplicidade e auditabilidade.

---

### Iteração 8 — Confidence gate

A IA sugeriu usar o modelo para roteamento automático. Eu adicionei um gate explícito de confiança.

No modelo final:

```text
threshold 0.80
cobertura: 61.5%
acurácia dentro do gate: 97.3%
```

Decisão: automatizar apenas acima do threshold e somente em categorias elegíveis/baixo risco.

---

### Iteração 9 — Domain shift

Testei aplicar o classificador IT do Dataset 2 no texto do Dataset 1.

Resultado:

```text
Hardware                 7551
Access                    561
Administrative rights     153
Miscellaneous             147
HR Support                 45
Storage                     7
Internal Project            5
```

O modelo colapsou em `Hardware` para a maioria dos tickets do Dataset 1. Isso confirmou mudança de domínio.

Decisão: Dataset 1/B2C externo **não recebe auto-resolução** no protótipo. Ele vira `AGENT_ASSIST` ou `HUMAN_ESCALATION`.

---

### Iteração 10 — Troca de Streamlit por FastAPI

Várias IAs recomendaram Streamlit. Eu escolhi FastAPI como protótipo principal.

Motivo:

- Streamlit demonstra uma tela;
- FastAPI demonstra um serviço integrável;
- o Diretor pediu “algo rodando”;
- um roteador real precisa receber tickets via API;
- o Swagger `/docs` já serve como demo interativa.

Decisão: FastAPI como núcleo da solução; scripts e gráficos como evidência.

---

## 4. Onde a IA errou e como corrigi

| Sugestão/afirmação da IA | Problema | Correção |
|---|---|---|
| “67,3% estão aguardando cliente” | Confundiu `Open + Pending` com apenas `Pending` | Corrigi para “67,3% não fechados; 34,0% Pending” |
| “Diagnosticar gargalo por canal usando Time to Resolution” | 49,3% dos deltas são negativos; positivos ainda não diferem por canal | Removi ROI/gargalo baseado em tempo |
| “Atacar Social media/Email por desperdício recuperável” | O desperdício vinha de timestamps sintéticos | Mantive apenas como exemplo metodológico, não recomendação final |
| “Usar Resolution como feature” | Data leakage: resolução só existe depois do atendimento | Usei Resolution apenas como dado pós-atendimento, não na triagem |
| “Aplicar modelo IT diretamente em B2C” | Domain shift; colapso em Hardware | Adicionei roteador de domínio e bloqueio de auto-resolução B2C |
| “Automatizar refund/cancellation por volume” | Risco financeiro/emocional | Reembolso/cancelamento vão para humano ou agent assist |
| “Usar acurácia geral como métrica suficiente” | Erros têm custos diferentes | Adicionei F1 macro, gate de confiança e fallback humano |
| “Fazer dashboard Streamlit” | Menos próximo de integração real | Troquei para FastAPI com Swagger |

---

## 5. O que eu adicionei que a IA sozinha não faria

1. **Adjudicação entre múltiplas IAs**: não escolhi a resposta mais bonita; testei cada hipótese.
2. **Correção do 67,3%**: mantive o número, mas com interpretação correta.
3. **Remoção de ROI falso**: não usei timestamps sintéticos para inventar economia.
4. **Domain shift guardrail**: o sistema sabe quando não aplicar o classificador.
5. **B2C/B2E como arquitetura**: não apenas insight textual, mas regra de roteamento.
6. **FastAPI em vez de dashboard**: protótipo mais próximo de produção.
7. **Confidence gate explícito**: automação vira decisão controlada, não chute.
8. **Política de não automação**: critical, refund, cancellation, HR, admin rights, legal/privacy/fraud.

---

## 6. Quantas iterações foram necessárias

Foram 10 iterações principais:

1. leitura do brief;
2. estrutura inicial;
3. auditoria do Dataset 1;
4. correção do 67,3%;
5. avaliação de hipótese de auto-close;
6. validação B2C/B2E;
7. teste fraco do Dataset 1 como classificador;
8. comparação NB vs Logistic Regression no Dataset 2;
9. domain shift;
10. implementação FastAPI.

---

## 7. Evidências

Arquivos gerados:

```text
solution/outputs/metrics.json
solution/outputs/tables/model_comparison.csv
solution/outputs/tables/gate_table_logreg.csv
solution/outputs/tables/gate_table_nb.csv
solution/outputs/tables/domain_shift_distribution.csv
solution/outputs/charts/model_comparison.png
solution/outputs/charts/confidence_gate_logreg.png
solution/outputs/charts/domain_shift_distribution.png
solution/outputs/charts/timestamp_delta_quality.png
solution/outputs/charts/batch_route_distribution.png
solution/app.py
solution/triage.py
solution/test_batch.py
```

Além desta narrativa escrita, podem ser adicionados prints das conversas com IA em `process-log/screenshots/`.

---

## 8. Submissão enviada em 25/06/26

## Onde eu duvidei da IA, testei e tomei decisões próprias

Uma parte central do processo foi não aceitar as respostas das IAs como verdade. Usei múltiplas ferramentas para gerar hipóteses, mas tratei cada hipótese como algo a ser validado contra os dados.

A lógica foi:

1. pedir hipóteses para IA;
2. identificar afirmações verificáveis;
3. transformar essas afirmações em testes;
4. manter apenas o que sobrevivesse aos dados;
5. redesenhar a solução quando a hipótese inicial não se sustentava.

### Hipóteses geradas por IA vs. validação

| Hipótese sugerida por IA | Por que parecia plausível | Como eu testei | Resultado | Decisão própria |
|---|---|---|---|---|
| “67,3% dos tickets estão aguardando cliente.” | O número aparecia ao somar tickets sem resolução final. | Comparei a distribuição real de `Ticket Status`. | `Pending Customer Response` era 34,0%. O número 67,3% correspondia a `Open + Pending`, ou seja, tickets não fechados. | Corrigi a interpretação: usei 67,3% apenas como “tickets não fechados”, não como “aguardando cliente”. |
| “O canal X é o maior gargalo operacional.” | O Dataset 1 tem canal, status e timestamps, então parecia natural procurar gargalos por canal. | Testei associação entre status e canal com qui-quadrado e analisei tempos por canal. | `Ticket Status × Channel` teve p≈0,771, indicando independência. Na subamostra com tempos positivos, os tempos por canal também não diferiram significativamente. | Não usei canal como evidência forte de gargalo. Mantive canal como input operacional, mas não como base para ROI. |
| “Basta remover tempos negativos e usar o restante para calcular desperdício.” | Filtrar dados inválidos parece uma limpeza razoável. | Verifiquei os tickets fechados e calculei `Time to Resolution - First Response Time`. Depois testei se a subamostra positiva tinha sinal por canal. | 49,3% dos tickets fechados tinham duração negativa. Mesmo nos tempos positivos, a distribuição parecia artificial e os canais não se diferenciavam de forma significativa. | Rejeitei ROI e recomendações baseadas em tempo de resolução do Dataset 1. Usei o Dataset 1 para auditoria, guardrails e desenho de processo, não para estimar economia direta. |
| “Podemos treinar um classificador no Dataset 1 para prever `Ticket Type`.” | O Dataset 1 tem `Ticket Description`, `Ticket Subject` e `Ticket Type`. | Treinei um classificador textual simples usando texto do Dataset 1. | O desempenho ficou próximo de aleatório para as classes existentes. | Não usei o Dataset 1 como base principal de classificação textual. |
| “O Dataset 2 pode classificar diretamente todos os tickets do Dataset 1.” | O Dataset 2 tem 47K tickets classificados e parecia ideal para treinar o modelo. | Treinei modelo no Dataset 2 e apliquei a lógica ao contexto do Dataset 1. | O modelo funciona no domínio interno/IT, mas existe mudança de domínio entre Dataset 2 e Dataset 1. | Criei um guardrail de domain shift: o classificador de IT só é usado para B2E/IT. Em B2C externo, o sistema não auto-resolve. |
| “Automatizar tickets de refund/cancellation economiza muito tempo.” | Refund e cancellation aparecem como categorias relevantes em suporte ao cliente. | Avaliei o tipo de decisão envolvida nesses tickets. | Mesmo quando recorrentes, esses tickets envolvem dinheiro, insatisfação, exceção comercial ou risco de churn. | Bloqueei auto-resolução para refund, cancellation, termos emocionais negativos e prioridade crítica. Esses casos vão para `HUMAN_ESCALATION` ou `AGENT_ASSIST`. |
| “Streamlit seria suficiente para demonstrar o protótipo.” | Streamlit é rápido para demo visual. | Comparei o tipo de solução com o fluxo real de suporte. | Um roteador de tickets real precisa integrar com Zendesk/Intercom/Freshdesk por API. | Troquei a ideia inicial de dashboard por FastAPI, porque a solução é um motor de decisão integrável, não apenas uma tela de análise. |

### Decisões que tomei contra sugestões iniciais das IAs

#### 1. Não usei o Dataset 1 para ROI baseado em tempo

A decisão mais importante foi não calcular ROI a partir de `Time to Resolution` do Dataset 1. Embora fosse possível gerar uma conta aparentemente convincente, os timestamps tinham sinais fortes de geração sintética:

- parte relevante dos tickets fechados tinha resolução anterior à primeira resposta;
- os tempos positivos restantes não apresentavam diferença significativa por canal;
- a distribuição temporal parecia artificial;
- status e canal pareciam independentes.

Por isso, preferi um ROI qualitativo/paramétrico e foquei o protótipo naquilo que era verificável: classificação textual no Dataset 2, confidence gate e política de automação.

#### 2. Não automatizei todo ticket com alta confiança

Mesmo quando o sistema detecta domínio ou categoria com alta confiança, a decisão final não depende só do modelo. A rota também considera:

- prioridade;
- domínio B2C vs. B2E;
- termos de risco;
- sensibilidade financeira;
- possibilidade de churn;
- baixa confiança;
- mudança de domínio.

Isso evita a red flag de “automatizar tudo”. A regra final ficou:

- `AUTO_RESOLVE`: somente B2E/IT, baixa ou média prioridade, alta confiança e baixo risco;
- `AGENT_ASSIST`: casos úteis para resumo, sugestão de resposta e checklist, mas sem resposta automática;
- `HUMAN_ESCALATION`: casos críticos, financeiros, emocionais, ambíguos ou fora do domínio validado.

#### 3. Troquei dashboard por API

Algumas sugestões iniciais iam na direção de dashboard ou Streamlit. Eu optei por FastAPI porque o problema real é roteamento operacional.

Um dashboard ajuda a ver o problema.  
Uma API ajuda a mudar o fluxo.

A FastAPI simula o serviço que ficaria entre a plataforma de atendimento e a fila dos agentes. Ela recebe um ticket, aplica classificação, confiança e guardrails, e devolve uma rota operacional.

#### 4. Comparei modelos em vez de aceitar o primeiro resultado

Testei mais de uma abordagem para classificação textual. Mantive um modelo simples e auditável, mas comparei baseline e modelo final.

A versão final usa `TF-IDF + LogisticRegression`, porque apresentou melhor desempenho que o baseline `TF-IDF + ComplementNB`.

Resultado documentado no `/model-card`:

- modelo selecionado: `TF-IDF + LogisticRegression`;
- baseline: `TF-IDF + ComplementNB`;
- acurácia do modelo selecionado: aproximadamente 86%;
- F1 macro: aproximadamente 86%;
- confidence gate recomendado: 0,80;
- tickets dentro do gate tiveram acurácia mais alta.

A decisão não foi “o modelo parece bom”. Foi: “o modelo foi comparado, medido e colocado atrás de um gate de confiança”.

### O que eu adicionei que a IA sozinha não faria

O maior valor humano foi transformar respostas conflitantes das IAs em hipóteses testáveis.

As IAs geraram boas ideias, mas também produziram conclusões confiantes sobre dados frágeis. Minha contribuição foi:

1. separar afirmações verificáveis de recomendações genéricas;
2. testar estatisticamente as hipóteses;
3. rejeitar conclusões baseadas em métricas sintéticas;
4. preservar apenas os insights que sobreviveram;
5. transformar os limites encontrados em guardrails de produto;
6. construir uma API funcional que incorpora esses guardrails.

A solução final não é “IA para suporte”. É uma política operacional codificada:

> automatizar onde há evidência, assistir onde há ambiguidade e escalar onde há risco.

### Iterações realizadas

| Iteração | O que mudou | Motivo |
|---|---|---|
| 1 | Ideia inicial de diagnóstico por canal, prioridade e tempo. | Era a leitura mais direta do enunciado. |
| 2 | Auditoria dos dados antes do diagnóstico. | Percebi sinais de inconsistência nos timestamps e textos. |
| 3 | Rejeição de conclusões baseadas em tempo do Dataset 1. | Os testes mostraram que os tempos não sustentavam inferência operacional confiável. |
| 4 | Uso do Dataset 2 como base principal para classificação textual. | O Dataset 2 tinha labels textuais mais adequados para treinar classificador. |
| 5 | Inclusão de guardrail B2C/B2E. | Apliquei a distinção entre suporte interno/IT e suporte externo/cliente. |
| 6 | Troca de Streamlit/dashboard para FastAPI. | Uma API representa melhor um roteador real de tickets. |
| 7 | Teste manual no Swagger com três cenários. | Validei `AUTO_RESOLVE`, `AGENT_ASSIST` e `HUMAN_ESCALATION`. |
| 8 | Teste em batch com `test_batch.py`. | Evitei cherry-picking e demonstrei comportamento em lote. |

### Evidências geradas

As evidências estão em `process-log/screenshots/`:

- `00_fastapi_docs_home.png`: API FastAPI aberta com endpoints;
- `01_auto_resolve_password_reset.png`: ticket B2E/IT de acesso retornando `AUTO_RESOLVE`;
- `02_agent_assist_b2c_product_help.png`: ticket B2C externo retornando `AGENT_ASSIST`;
- `03_human_escalation_refund_angry.png`: refund + cliente irritado retornando `HUMAN_ESCALATION`;
- `04_batch_test_distribution.png`: execução em lote com distribuição das rotas;
- `05_model_card.png`: modelo, baseline, confidence gate e guardrails;

Essas evidências mostram tanto o processo de validação quanto o protótipo funcionando.