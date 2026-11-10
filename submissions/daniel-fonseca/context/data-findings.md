# Fatos verificados sobre os dados

> Memória de longo prazo sobre os datasets. Cada fato aqui tem origem em um script reproduzível.
> Fonte: `solution/analysis/00_data_profile.py` (rodado em 2026-11-09). Ao descobrir algo novo, adicione aqui com a origem.

## Dataset 1 — Customer Support Ticket Dataset (suraj520)

### O que o README do challenge diz vs. o que o dado tem

| README do challenge | Dado real | Implicação |
|---|---|---|
| ~30.000 registros | **8.469 tickets** (o CSV tem 29.808 linhas físicas porque as descrições têm quebras de linha) | Quem contar linhas com `wc -l` erra o volume em 3,5× |
| `Ticket Type` com 3 valores | **5 valores**: Refund request 1.752 · Technical issue 1.747 · Cancellation request 1.695 · Product inquiry 1.641 · Billing inquiry 1.634 | |
| `First Response Time` / `Time to Resolution` = tempos | São **timestamps**, não durações. Duração precisa ser derivada | |

### Cobertura das métricas

- `Closed` 2.769 · `Pending Customer Response` 2.881 · `Open` 2.819.
- Só os tickets `Closed` têm `Resolution`, `Time to Resolution` e `CSAT` (100% / 0% nos demais).
- `Open` (2.819 = 33%) **não tem primeira resposta registrada**.

### Sinais fortes de dado sintético (gerado por Faker/template)

1. **Janela de tempo de ~27h**: todos os timestamps de FRT/TTR caem entre 2023-05-31 21:53 e 2023-06-02 00:55, enquanto as compras vão de 2020-01-01 a 2021-12-30.
2. **Resolução antes da primeira resposta em 49,3%** dos tickets fechados (1.365/2.769). `TTR − FRT` vai de −23,2h a +23,5h com média −0,06h — comportamento de dois timestamps independentes e aleatórios.
3. **CSAT uniforme**: notas 1–5 com 553 / 549 / 580 / 543 / 544. Médias por canal (2,95–3,08), prioridade (2,96–3,05) e tipo (2,93–3,03) praticamente iguais. Correlação CSAT × duração = 0,02; CSAT × idade = −0,004.
4. **Distribuições uniformes** em canal (2.073–2.143), prioridade (2.063–2.192), gênero e tipo.
5. **Texto templatizado**: 100% das descrições contêm o placeholder literal `{product_purchased}`.
6. **Resoluções são texto aleatório** (lorem Faker): ex. "Offer investment fish.", "Window range building see answer job boy." — 2.769 resoluções, todas distintas, sem relação com o problema.
7. **`Ticket Subject` independe de `Ticket Type`**: ex. assunto "Cancellation request" aparece 82× como "Billing inquiry".

### Testes de significância (`solution/analysis/01_signal_tests.py`)

- **Independência total:** 28 pares de variáveis (tipo, prioridade, canal, status, assunto, produto, gênero, faixa etária) → 1 com p<0,05 (acaso esperaria ~1,4); maior V de Cramér = 0,07.
- **CSAT sem efeito de nenhuma variável:** canal p=0,28 · prioridade p=0,63 · tipo p=0,70 · assunto p=0,81 · faixa etária p=0,92 (Kruskal-Wallis).
- **Armadilha de ranking:** 80 combinações canal × prioridade × tipo têm médias de CSAT entre 2,29 (Phone/High/Refund) e 3,57 (Email/High/Product inquiry), mas o teste conjunto dá p=0,50 — amplitude produzida pelo acaso em células de 20–49 tickets.
- **Não há timestamp de abertura do ticket** → tempo até primeira resposta e tempo de resolução não são calculáveis. TTR−FRT positivo em 1.404/2.769 (mediana 6,3h), sem diferença por canal (p=0,79); Spearman CSAT × TTR−FRT = 0,02.
- Status em terços quase exatos (34,0% / 33,3% / 32,7%) — também com cara de geração aleatória; usar só como ilustração.

### Cortes do diagnóstico (`solution/analysis/02_diagnostic_cuts.py` → `output/diagnostic_cuts.csv`)

- Canal, prioridade, tipo, assunto e produto: **nenhuma** diferença significativa em % sem resposta, tempo ou CSAT (todos os p > 0,05; tabela na ADR-0003).
- Gargalo transversal: 33,3% sem 1ª resposta, 34,0% aguardando cliente.
- 1ª resposta → resolução, só nos 1.404 fechados coerentes (50,7%): média 7,6h · mediana 6,3h · p90 16,0h.
- CSAT médio 2,99 (IC 95% 2,94–3,04). Modelo com 70 variáveis: R² 0,021, ajustado −0,005.

### Viés de sobrevivência no CSAT (tese — Daniel)
O CSAT só existe para os 32,7% de tickets fechados. Os 67,3% sem resposta ou parados aguardando o cliente são os candidatos mais prováveis à insatisfação e não são medidos. Numa operação real isso **superestima** a satisfação e esconde o efeito da espera. Não dá para provar com este dado (a nota é aleatória); fica como limitação e como recomendação de instrumentação.

**Conclusão provisória (ADR-0003, ajustada pelo Daniel):** o Dataset 1 não sustenta conclusões causais sobre gargalos ou satisfação. Qualquer "o canal X é o pior" tende a ser ruído. Os campos de texto (`Resolution`) não servem como base de conhecimento para RAG.

## Dataset 2 — IT Service Ticket Classification (adisongoh)

- **47.837 documentos**, 0 duplicados, 0 conflitos de rótulo.
- 8 classes, **desbalanceadas**: Hardware 28,5% · HR Support 22,8% · Access 14,9% · Miscellaneous 14,8% · Storage 5,8% · Purchase 5,2% · Internal Project 4,4% · Administrative rights 3,7%.
- Texto **pré-processado** (minúsculas, sem stopwords, nomes removidos) — ex.: "connection with icon icon dear please setup icon per icon engineers please let other details needed thanks lead". Mediana de 26 palavras, máximo 981.
- **Não tem campo de resolução.** Serve para classificação/roteamento e busca por similaridade, não para "copiar a solução de um caso parecido".
- Rótulos parecem ter ruído (ex.: texto sobre "sip trunk gateway" rotulado como Hardware) — a medir na avaliação do classificador.

### Classificação do DS2 (holdout 9.567 · `03_classifier_eval.py`, `04_zero_shot_eval.py` → `output/*.json`)

- **Baseline TF-IDF + regressão logística:** acurácia **86,9%**, F1 macro 0,870 (pior classe: Administrative rights, F1 0,80). Curva cobertura → precisão: confiança ≥ 0,7 cobre 75% com 95,0%; ≥ 0,9 cobre 54% com 98,2%; ≥ 0,95 cobre 44% com 98,9%. Treina em 16 s, custo zero.
- **LLM zero-shot (`gpt-5.4-mini`, 400 tickets, 50 por classe):** acurácia **43,2%**, F1 macro 0,413, contra 83,5% do baseline **na mesma amostra**. Quando o LLM declara confiança ≥ 0,9 (43% dos casos), acerta só **62%** → a confiança do LLM **não é calibrada** e não serve como critério de automação. As categorias são da taxonomia interna da organização ("Miscellaneous", "Internal Project", "Administrative rights"), que o modelo não tem como adivinhar só pelo nome. Custo: ~100K tokens.

- **Embeddings (`text-embedding-3-small`, 2,19M tokens, ~US$ 0,04):** kNN k=15 → 82,5% (1536) e 82,1% (512); regressão sobre embeddings → 83,8% (1536) e 81,1% (512). **Abaixo do TF-IDF.** Quase-duplicatas treino/teste (sim ≥ 0,95): 7,3%; sem elas a acurácia cai < 1 p.p. → sem vazamento relevante.
- **TF-IDF compacto (20 mil termos):** 86,5% — cabe num JSON de ~1,4 MB.
- **Concordância TF-IDF × kNN 512, ambos ≥ 0,8:** cobertura 49,8%, precisão 99,2%. Discordância em 17% (TF-IDF acerta só 57% delas).
- **3 níveis no holdout (ADR-0010):** automático 35,9% (99,2%) · revisão 30,1% · só humano 34,0%. 11 sensíveis escapariam para o automático (0,32% dele).
- **Ponte para o DS1 (versão TF-IDF + RAG, descartada):** ≈ 24% de automação total (mesmo erro de denominador corrigido em 10/11).

- **Melhorando o RAG (`06`, `07`, `08`):** ajuste do voto (k=50, peso sim¹⁶) → 82,8% em 512 dims (+0,7 p.p.) e 83,3% em 1536. Busca híbrida (semântica + palavras-chave, RRF) → 82,8%, sem ganho. **RAG + LLM** (o LLM vê os 15 casos parecidos) → 80,8% na amostra de 400, contra 43,2% do LLM sozinho e 80,8% do voto na mesma amostra. Quando LLM e voto discordam (15%), ambos acertam só 39%.
- **Política RAG único (ADR-0010):** confiança ≥ 0,9 → 44,0% de cobertura com 98,7%; com as regras de sensibilidade: nível 1 31,2% (98,8%) · nível 2 28,4% · nível 3 40,5%. 15 sensíveis escapariam para o nível 1. Ponte para o DS1 (corrigida em 10/11): 44,4% elegíveis × 42,2% de autonomia entre não sensíveis ≈ **18,7%** de automação, ~810 h e ~R$ 17 mil/ano (`11_app_summary.py`); o valor anterior, 23%, usava um denominador errado.

### RAG no banco (`solution/analysis/09_db_rag_validation.py` → `output/db_rag_validation.json`, sessão 02)
- `classify_ticket` (pgvector HNSW, halfvec 512, só vizinhos de treino) em 500 tickets de teste (seed 42): **80,4%**, contra **80,2%** do cálculo exato local nos mesmos tickets. Concordância de categoria 99,8% e de nível 99,6%; maior diferença de confiança 0,11 (busca aproximada + halfvec). A amostra fica abaixo dos 82,8% do holdout inteiro por variação amostral (erro-padrão ≈ 1,8 p.p.).
- Níveis na amostra: 32,2% / 29,4% / 38,4%; nível 1 com 100% de acerto (161 tickets). Latência p50 64 ms / p95 142 ms (rede incluída).
- Armadilha evitada: o `ef_search` padrão do HNSW (40) é menor que k=50, e o filtro de treino descarta ~20% dos vizinhos. A função usa `ef_search = 100` + `iterative_scan = strict_order` e sempre devolve 50 vizinhos.
- Espaço real: `ds2_embeddings` 117 MB (índice HNSW 62 MB); banco inteiro 150 MB de 500.

### Lista de bloqueio (`solution/analysis/10_blocklist_eval.py` → `output/blocklist_eval.json`)
- Lista estreita de RH/jurídico (11 termos): 6 falsos positivos em 2.983 tickets do nível 1 (0,2%); pega 1 dos 15 sensíveis que escapam.
- Lista ampla (+ administrator, password, contract, leaver, absence, admin rights): 637 falsos positivos (21,4%). "administrator" sozinho gera 421.
- Os 15 escapes têm pouco conteúdo sensível (ex.: "very slow access to various sites" rotulado HR Support) → provável ruído de rótulo do DS2.

### Números do app (`solution/analysis/11_app_summary.py` → `output/app_summary.json`, 10/11)
- p-valor por dimensão e métrica (qui-quadrado do status para % sem resposta e % aguardando; Kruskal-Wallis para tempo e CSAT): nenhum < 0,05.
- Armadilha do ranking: 80 combinações canal × prioridade × tipo; pior Phone/High/Refund 2,29 (n = 31), melhor Email/High/Product inquiry 3,57 (n = 35); p conjunto = 0,50.
- ROI: 44,4% do DS1 elegível (fora reembolso, cancelamento e Critical) × 42,2% de autonomia entre não sensíveis no holdout (precisão 98,8%) = **18,7%** de automação total.
- Fluxo 1 em produção (10/11): US$ 0,0007–0,0014 por triagem; latência total 2,5–5 s.

## Estimativas técnicas derivadas (a confirmar na implementação)

- Embeddings do DS2 inteiro: ~48K docs × ~60 tokens ≈ 3M tokens → custo de centavos em `text-embedding-3-small` (confirmar preço vigente).
- Armazenamento: 1536 dims em `vector` ≈ 295 MB sem índice (~590 MB com HNSW → não cabe nos 500 MB). Em `halfvec` ≈ 147 MB (~300 MB com índice → cabe). Dimensão final decidida por medição (ADR-0004).
- Holdout DS2: 38.270 treino / 9.567 teste, 20% em cada categoria (`scripts/load_raw_datasets.py`, seed 42).
