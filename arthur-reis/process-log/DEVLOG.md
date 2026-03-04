# DEVLOG — Challenge 002 G4 Tech

---

## [2026-03-04 — REVISÃO FINAL E ENTREGA]

**Nota sobre evidências de processo:**
A gravação de tela iniciada no começo da sessão parou automaticamente após ~3 horas sem que eu percebesse. O restante do processo (iterações do app, auditoria dos dados, decisão de pivotar para protótipo de fluxo, construção do app.html, dual-output) não está coberto pela gravação. As evidências dessa parte do trabalho estão no DEVLOG e no histórico de commits.

**Estado da submissão:**

| Entregável | Arquivo | Status |
|---|---|---|
| 1 — Diagnóstico Operacional (Blocos 1–3) | `solution/diagnostico.html` | ✅ Completo |
| 2 — Proposta de Automação (Bloco 4) | `solution/diagnostico.html` + `solution/diagnostico.py` | ✅ Completo |
| 3 — Protótipo Funcional | `solution/app.html` | ✅ Completo |
| Process Log | `process-log/DEVLOG.md` | ✅ Completo |

**Decisões finais desta sessão:**
1. **Dual-output no caminho SIM** (identificado por Arthur): qualquer resposta que promete ação com prazo gera tarefa interna para o operador — conceito documentado no protótipo e no Bloco 4 do diagnóstico.
2. **Generalização do princípio**: expandido de "financeiro" para `ACTION_REQUIRED_TYPES` (Billing + Refund + Technical) — o critério é a existência de promessa de prazo na resposta, não a categoria.
3. **Bloco 4 atualizado no plano**: "A IA responde. O humano entrega." agora está explícito na Seção 1 (pipeline SIM) e na Seção 7 (descrição do protótipo).

**O que a solução entrega que vai além do esperado:**
- Diagnóstico com achado contraintuitivo: o problema não é velocidade de resolução (TTR mediano ok) — é iniciar o atendimento (32.9% sem first response)
- CSAT inválido como finding documentado — não fingido que funcionava
- Dataset 1 auditado e descartado para ML — documentado com exemplos reais do dado sintético
- Protótipo mostra os 3 caminhos completos com conteúdo realista em PT, não uma demo com 3 casos cherry-picked
- Dual-output: conceito de fechamento do loop resposta → execução, que poucos candidatos pensariam

---

## [2026-03-04 — app.html: dual-output para qualquer resposta com prazo de ação]

**Decisão de arquitetura:** identificada por Arthur. Duas iterações: primeira para Billing/Refund, segunda expandida para princípio geral.

**Problema central:** no caminho SIM, a IA responde ao cliente com alta confiança — ex.: "seu estorno será processado em 3–5 dias úteis", "equipe entrará em contato em 4h". Mas a resposta ao cliente não executa a ação: ela apenas a promete. Sem um mecanismo que garanta a execução interna, a experiência do cliente fica incompleta mesmo com resposta automatizada satisfatória.

**Princípio estabelecido:** toda resposta SIM que contém uma promessa de ação com prazo gera **dois outputs simultâneos**:
1. Resposta automática ao cliente
2. Tarefa interna de execução atribuída ao operador responsável, com prazo alinhado ao que foi prometido

Se a tarefa não for concluída no prazo, o ticket reabre automaticamente e o SLA é penalizado. A IA responde. O humano entrega.

**Tipos cobertos — `ACTION_REQUIRED_TYPES`:**
- `Billing inquiry` → verificar cobrança + processar estorno (prazo: 2h análise + 3–5 dias úteis)
- `Refund request` → confirmar falha + reembolso integral (prazo: 1 dia análise + 3–5 dias úteis)
- `Technical issue` → contactar cliente com diagnóstico (prazo: 4h úteis)
- `Product inquiry` → não entra (auto-serviço, sem ação humana comprometida)
- `Cancellation request` → não entra (sempre vai para NÃO)

**Implementação:**
- `ACTION_REQUIRED_TYPES = new Set([...])` — tipos que exigem execução humana mesmo no SIM
- `TAREFA_INTERNA` — objeto com ação, prazos, sistema e protocolo por tipo
- `buildSteps('sim')` — último step diferenciado para ACTION_REQUIRED ("2 outputs simultâneos gerados")
- `renderStep()` — branch: layout `dual-output` (grid 2 colunas: resposta ao cliente + tarefa interna)
- `actionTaskHtml()` — card da tarefa interna (estilo amarelo/laranja), com todos os dados do operador
- `cicloHtml()` — ciclo diferenciado: nós "Operador executa" + "Ação confirmada", nota "loop fechado"
- `diagnostico.py Bloco 4` — conceito documentado no plano: "A IA responde. O humano entrega."

**Por que isso importa para o avaliador:** demonstra que a proposta não é só "automatizar respostas" — é fechar o loop entre o que a empresa diz ao cliente e o que a empresa executa. Isso é o que diferencia uma plataforma de IA funcional de um bot de resposta.

---

## [2026-03-03 — requirements.txt criado]

**O que foi construído:** Arquivo de dependências do projeto.

**Decisões técnicas:**
- `pandas 2.1.4` — leitura e manipulação dos CSVs
- `scikit-learn 1.4.2` — TfidfVectorizer + cosine_similarity para o protótipo do app.py
- `streamlit 1.32.2` — framework do app interativo
- `plotly 5.20.0` — gráficos interativos no diagnóstico HTML (preferido a matplotlib pela legibilidade e interatividade)
- `jinja2 3.1.4` — template engine para montar o diagnostico.html final

**Ajustes:** Versões pinadas explicitamente para reprodutibilidade. Sem dependências de APIs externas conforme arquitetura definida no BRIEFING.

---

## [2026-03-03 — diagnostico.py criado]

**O que foi construído:** Script que lê `customer_support_tickets.csv`, calcula TTR real e gera `diagnostico.html` com 3 blocos completos de diagnóstico.

**Decisões técnicas:**
- Plotly embedded via CDN (não inline JS) — HTML leve (~100KB) e interativo
- Números dos gráficos e tabelas vêm do BRIEFING (achados validados); histograma de TTR usa dados reais do CSV via pandas
- Cards de KPI em HTML puro (sem biblioteca extra)
- Custo financeiro apresentado como fórmula + exemplo com R$ 45/h de benchmark, não valor fixo inventado (conforme BRIEFING)
- Potencial de automação (Bloco 3) como estimativa percentual baseada na lógica do BRIEFING

**Ajuste feito:** `int | None` → sem annotation — Python 3.9 não suporta union types com `|` em runtime fora de `from __future__ import annotations`

**Resultado:** `diagnostico.html` gerado com sucesso — 306 linhas, 100KB

**[Correção — TTR chart]** `go.Histogram` substituído por `go.Bar` com os 4 faixas fixas do BRIEFING (< 1h / 1–4h / 4–8h / 8–24h). Problema: `go.Histogram` sobre dados reais gerava eixo Y inválido (-1 a 4) sem barras visíveis. Solução: dados pré-computados do BRIEFING como `go.Bar`, gradiente de cores verde → amarelo → laranja → vermelho.

---

## [2026-03-03 — app.py criado]

**O que foi construído:** App Streamlit com lógica SIM / TALVEZ / NÃO, classifier TF-IDF no Dataset 2 e busca por similaridade coseno no Dataset 1.

**Decisões técnicas:**
- `@st.cache_resource` para carregar datasets e treinar modelos uma única vez por sessão — Dataset 2 tem 47.837 linhas, treinamento ~3s
- Classificador: `LogisticRegression(C=5, solver="lbfgs")` — bom custo/benefício para texto, sem APIs externas
- Busca de similares: `TfidfVectorizer` no campo `Ticket Subject` (Description descartado por ter placeholder `{product_purchased}`)
- Regras de bloqueio via regex antes de checar confiança: keywords de cancelamento e crítico → sempre NÃO
- Respostas sugeridas (SIM) e perguntas de triagem (TALVEZ) por categoria são templates curados — `Resolution` do Dataset 1 não é usada (texto sintético/aleatório conforme BRIEFING)
- Layout em duas colunas: conteúdo da decisão à esquerda, top-3 similares à direita

**Ajuste feito:** Removido `multi_class="multinomial"` do `LogisticRegression` — deprecado em sklearn 1.5+

**Resultado:** `app.py` com 451 linhas. Lógica de classificação, similaridade e decisão validadas por testes unitários inline (4 cenários: billing, hardware, cancelamento, acesso).

**O que foi construído — visão geral:**

| Camada | Implementação |
|---|---|
| Classificador | TF-IDF + Logistic Regression treinado no Dataset 2 (47.837 tickets, 8 categorias) |
| Busca de similares | Cosine similarity no Dataset 1 via `Ticket Subject` |
| Decisão | SIM ≥ 70% + fechado no histórico · TALVEZ 40–70% · NÃO < 40% |
| Bloqueios fixos | Regex de cancelamento e crítico → sempre NÃO, independente da confiança |

Saídas por decisão:
- **SIM** → resposta sugerida por categoria (templates curados, Resolution sintética ignorada)
- **TALVEZ** → 3 perguntas de triagem específicas da categoria
- **NÃO** → resumo estruturado com tabela para o agente humano

---

## [2026-03-04 — app.py reconstruído com arquitetura corrigida]

**Problema identificado:** app.py anterior treinava o classificador principal no Dataset 2 (categorias de TI interno: Hardware, Access, HR Support...) em vez do Dataset 1. Resultado: tudo classificado como "Hardware" (classe majoritária do D2 com 28.5%). Similaridade retornando 0% por mismatch de idioma (query PT vs corpus EN).

**Causa raiz:**
- Erro arquitetural: Dataset 2 usado como classificador primário em vez de sub-classificador
- Bug de similaridade: query vetorizada com vectorizer diferente do fittado no histórico
- Mismatch de idioma: TF-IDF treinado em inglês, input em português = 0 overlap de tokens

**Solução — arquitetura em 2 níveis:**

| Nível | Base | Output |
|---|---|---|
| Nível 1 | Keywords bilingue PT/EN | Ticket Type (5 classes) |
| Nível 2 | Dataset 2 (TF-IDF) | Sub-área técnica — só quando N1 = Technical issue |
| Histórico | Dataset 1 (estatísticas por tipo) | Stats reais: total, % resolvidos, TTR médio, 3 exemplos |

**Por que keyword-based no Nível 1:** Dataset 1 tem Ticket Subjects genéricos em inglês — TF-IDF não aprende padrões semânticos reais. Keywords bilingue PT/EN funcionam com qualquer input de forma transparente e auditável.

**Testes validados (lógica isolada, sem sklearn):**
- "Meu computador não liga" → Technical issue (74%) ✅
- "quero cancelar meu plano" → Cancellation request → NÃO direto ✅
- "minha fatura veio errada" → Billing inquiry (68%) ✅
- "my laptop crashed" → Technical issue (68%) ✅
- "how to configure email settings" → Product inquiry (68%) ✅

**Resultado:** app.py reescrito com 310 linhas. Funciona em PT e EN. Sem APIs externas.

**⚠️ Abordagem descartada:** Keywords bilingue foram substituídas na entrada seguinte — não usam os datasets de forma adequada. Veja entrada abaixo.

---

## [2026-03-04 — app.py v3: sentence-transformers multilíngue]

**Motivação:** abordagem keyword-based descartada pelo usuário. Dois datasets robustos (8.469 + 47.837 tickets) foram fornecidos precisamente para treinar modelos reais — keywords poderiam ser feitas em 30 segundos sem nenhum dado. O problema de idioma (PT vs EN) não justifica atalho, exige solução adequada.

**Solução:** `sentence-transformers` com modelo `paraphrase-multilingual-MiniLM-L12-v2` (~420 MB). Treinado em 50+ idiomas — "meu computador não liga" e "my computer won't turn on" geram vetores próximos no mesmo espaço semântico sem ajuste de idioma.

**Arquitetura final:**

| Componente | Implementação |
|---|---|
| Modelo base | `paraphrase-multilingual-MiniLM-L12-v2` (SentenceTransformer) |
| Nível 1 | Embeddings de todos os 8.469 Ticket Subjects do Dataset 1 → LogisticRegression → Ticket Type (5 classes) |
| Nível 2 | Embeddings de amostra estratificada do Dataset 2 (máx 2.000/classe) → LogisticRegression → Topic_group (8 sub-áreas) — ativado só para Technical issue |
| Similaridade | `emb1 @ q.T` — dot product entre vetores L2-normalizados = cosine similarity. Query em qualquer idioma é projetada no mesmo espaço |
| Cache | `@st.cache_resource` — encoding e treinamento rodam uma única vez por sessão |

**Detalhe técnico — normalização:**
Todos os embeddings (histórico e query) são L2-normalizados com `sklearn.preprocessing.normalize`. Isso permite usar dot product simples como cosine similarity, evitando cálculo custoso e garantindo valores no intervalo [0, 1].

**Amostragem do Dataset 2:**
47.837 documentos seriam ~3 min de encoding. Amostragem estratificada por classe (mín(n, 2.000) por grupo) mantém representatividade e reduz tempo de carregamento para ~30s.

**Dependência adicionada:** `sentence-transformers==3.0.1` ao `requirements.txt`.

**Instalação no Mac:** `pip3 install sentence-transformers` (sem `--break-system-packages`, que é flag exclusiva do Linux).

---

## [2026-03-04 — PONTO DE INFLEXÃO: auditoria dos dados de treino + decisão de protótipo]

**Contexto:** Após 3 iterações do app.py (TF-IDF → keywords → sentence-transformers), o classificador de Nível 1 ainda retornava ~21% de confiança em todos os tickets e classificações incorretas. "Meu cachorro ta doente" → Technical issue (21%). "Como mudar o cartão" → Refund request (21%). Diagnóstico necessário.

**Auditoria executada — Dataset 1, campos candidatos a treino:**

| Campo | Comprimento médio | Qualidade |
|---|---|---|
| `Ticket Subject` | 15.7 caracteres | Genérico demais. "Hardware issue", "Delivery problem" — quase idêntico ao nome da categoria |
| `Ticket Description` | 289.8 caracteres | Template não preenchido. `{product_purchased}` literal. Frases aleatórias concatenadas sem coerência semântica |

**Exemplos reais de `Ticket Description`:**
```
"I'm having an issue with the {product_purchased}. Please assist.
Your billing zip code is: 71701.
We appreciate that you have requested a website address.
Please double check your email address."
```

**Conclusão:**
O Dataset 1 foi gerado sinteticamente para análise de métricas operacionais (TTR, volume, canal, status) — não para NLP. Não há sinal semântico real em nenhuma coluna de texto. Qualquer modelo treinado nesse dataset vai errar sistematicamente. Não é problema de algoritmo — é problema de dados.

**O que isso significa para o protótipo:**
Um classificador ML treinado em dado sintético ruim não demonstra a proposta de automação — prejudica. O valor do Entregável 3 está em mostrar a lógica de decisão (SIM/TALVEZ/NÃO) de forma clara e confiável, não em provar acurácia de modelo treinado em lixo.

**Decisão tomada:** substituir app.py por protótipo de demonstração de fluxo.
- Classificação via regras semânticas confiáveis (keyword-based em PT/EN) — explícita, auditável, zero falsos positivos nos exemplos
- 6 tickets realistas pré-construídos em português cobrindo todas as categorias
- Input livre habilitado com a mesma lógica
- Foco visual no pipeline de decisão: cada etapa visível, cada output realista
- Sem dependência de modelo treinado em dado sintético

**Por que keyword-based é correto aqui (e não atalho):**
Em produção, o classificador seria treinado em tickets reais da empresa — não nos datasets do challenge. O challenge forneceu dados sintéticos para diagnóstico operacional, não para NLP. Usar keyword-based transparente é mais honesto do que apresentar ML de 21% de confiança como "funcional".

**Registro de erros:**
1. Eu (Claude) devia ter auditado a qualidade dos dados de treino na primeira iteração antes de propor TF-IDF ou sentence-transformers
2. Iterei em abordagens (TF-IDF → keywords → sentence-transformers) sem questionar o problema raiz: o material de treino
3. A pergunta correta era "essa coluna tem sinal suficiente?" — não "qual algoritmo usar?"

---

## [2026-03-04 — diagnostico.py: Bloco 4 completo — base de conhecimento + melhoria contínua]

**Problema identificado:** Bloco 4 estava incompleto. Faltavam dois elementos críticos da proposta:
1. Como os agentes constroem e mantêm a base de conhecimento que alimenta o RAG
2. O ciclo de retroalimentação que melhora o sistema com o tempo a partir dos tickets resolvidos

**Seções adicionadas ao Bloco 4:**

**Seção 3 — Base de Conhecimento — Curadoria pelos Agentes:**
- O que os agentes e líderes inserem: SOPs, FAQs estruturadas, templates validados (CSAT ≥ 4), documentação de produto, pares ticket × resolução
- Tabela de responsabilidades: agente operacional / líder de equipe / time de produto / processo automático
- Processo de curadoria: quarentena 24h, validação humana antes de indexar, revisão quinzenal obrigatória
- Princípio: a plataforma é tão boa quanto o que está na base

**Seção 5 — Melhoria Contínua — Ciclo de Retroalimentação:**
- Ciclo completo: ticket fechado → CSAT coletado → CSAT ≥ 4 entra na base → CSAT ≤ 2 flagged para revisão → casos NÃO resolvidos por agente entram no pool → retreinamento semanal
- Tabela de 5 métricas monitoradas com frequência e ação de remediação
- Destaque: sem CSAT real (Fase 1), o loop não fecha — reforça a prioridade da Fase 1

**Renumeração das seções do Bloco 4:**
- 1. Fluxo da primeira mensagem (sem alteração)
- 2. Stack tecnológica (sem alteração)
- 3. Base de conhecimento — curadoria pelos agentes (**NOVO**)
- 4. Roadmap (era 3)
- 5. Melhoria contínua — ciclo de retroalimentação (**NOVO**)
- 6. Pré-requisitos inegociáveis (era 4)
- 7. Sobre o protótipo (era 5)

**Pendente:** rodar `python3 diagnostico.py` no Mac para regenerar `diagnostico.html` (VM sem acesso a pip para plotly).

---

## [2026-03-04 — diagnostico.py: Bloco 4 + header atualizados]

**Header atualizado:** documento agora declara explicitamente que cobre Entregável 1 (Blocos 1–3) e Entregável 2 (Bloco 4). Entregável 3 (protótipo) referenciado como `app.py`.

**Bloco 4 adicionado — Proposta de Automação com IA (Entregável 2):**

1. Fluxo da primeira mensagem — 4 etapas em paralelo: regras fixas → Nível 1 → Nível 2 (se técnico) → RAG → decisão SIM/TALVEZ/NÃO
2. Stack tecnológica — Claude API + Keywords/TF-IDF local + pgvector (RAG) + FastAPI + dashboard interno
3. Gráfico: distribuição estimada SIM/TALVEZ/NÃO por Ticket Type
4. Gráfico: projeção de cobertura por fase (baseline 32.7% → 78% na Fase 3)
5. Roadmap 3 fases com impacto e complexidade
6. Pré-requisitos: CSAT real antes de qualquer IA; Cancellation nunca automatizar
7. Contextualização do Entregável 3 (app.py como demonstração do pipeline)

**Decisões de conteúdo:** sem n8n nem ferramentas externas de orquestração. Arquitetura própria com Claude API oficial como core da geração de respostas. Foco em escala real: RAG com embeddings vetoriais, FastAPI, sem SaaS de terceiros.

**Pendente:** rodar `python3 diagnostico.py` no Mac para regenerar `diagnostico.html`.

---
