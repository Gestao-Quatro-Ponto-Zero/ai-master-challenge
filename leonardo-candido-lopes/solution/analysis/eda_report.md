# Desafio 002 — Redesign de Suporte · Auditoria e Análise Exploratória (EDA)

**Candidato:** Leonardo Candido Lopes · **Data da análise:** 08/11/2026
**Escopo:** auditoria + EDA dos 2 datasets oficiais. **Sem modelagem e sem protótipo** nesta etapa.
**Reprodutibilidade:** scripts em `analysis/` (`explore_data.py`, `eda_d1.py`, `eda_d2.py`, `eda_d2_clean.py`); resultados brutos em `eda_d1_results.json`, `eda_d1_extra.json`, `eda_d2_results.json`, `eda_d2_clean_results.json`; gráficos em `analysis/charts/*.json` (Plotly). Arquivos originais em `data/` **não foram alterados**.

> **Legenda:** **[FATO]** = medido diretamente nos dados · **[HIPÓTESE]** = interpretação plausível, ainda não comprovada · **[DECISÃO]** = escolha metodológica registrada.

---

## 1. Resumo executivo da auditoria

**Dataset 1 — `customer_support_tickets.csv` (8.469 tickets × 17 colunas).** O briefing citava ~29.807 registros, mas esse número corresponde às **linhas físicas** do arquivo (8.469 registros + 21.338 quebras de linha dentro das descrições + 1 cabeçalho). Validei com o leitor `csv` e com os dois motores do pandas: todos os registros têm exatamente 17 campos e os IDs vão de 1 a 8.469, sem lacunas. A auditoria encontrou **evidência forte e convergente de que o dataset é sintético**: (a) 100% das descrições contêm o placeholder literal `{product_purchased}`; (b) 100% dos e-mails são `@example.com/.org/.net`; (c) as resoluções são frases aleatórias sem nenhum termo de suporte ("Try capital clearly never color toward story."); (d) **todas** as variáveis categóricas e numéricas são estatisticamente uniformes e **independentes entre si** (12 de 12 testes qui-quadrado com p > 0,05, V de Cramér ≤ 0,07); (e) os dois campos de "tempo" são **timestamps** concentrados em ~27 horas, e **49,3% dos tickets fechados teriam sido "resolvidos" antes da primeira resposta**. Consequência prática: **não dá para calcular tempo de primeira resposta, tempo de resolução nem SLA reais com esse dataset**, e nenhum gargalo por canal/prioridade/tipo se diferencia do acaso. Ele serve para entender o **esquema de campos** de uma operação de suporte, não para gerar KPIs.

**Dataset 2 — `all_tickets_processed_improved_v3.csv` (47.837 textos × 2 colunas).** É um corpus de tickets de **TI interna corporativa** (help desk), já pré-processado: tudo em minúsculas, sem pontuação e sem dígitos. Não tem nulos nem duplicatas exatas. As 8 classes são **desbalanceadas** (Hardware 28,5% vs Administrative rights 3,7%; razão de 7,7×), mas a menor classe ainda tem 1.760 exemplos. Os textos têm mediana de 26 palavras. Depois de remover o boilerplate de e-mail (38% dos tokens), várias classes mostram vocabulário bem distintivo: Purchase (`po`, `purchased`, `receipts`), Storage (`folder`, `mailbox`, `accept/decline`), Access (`confluence`, `password`, `reset`). **Hardware e Miscellaneous** são as classes mais ambíguas. O dataset tem **bom potencial para treinar um classificador de triagem**, com duas ressalvas: a classe "Miscellaneous" funciona como categoria-coringa, e "HR Support" é mais "acesso a sistemas de RH/onboarding" do que RH no sentido clássico. **Não existe chave entre os dois datasets**, e os domínios são diferentes (B2C eletrônicos vs TI interna).

---

## 2. Diagnóstico da qualidade dos dados

### 2.1 Dataset 1 — estrutura, nulos, duplicatas

| Indicador | Valor encontrado | n | Interpretação operacional |
|---|---:|---:|---|
| Shape real | 8.469 × 17 | 8.469 | [FATO] Os ~29.807 do briefing são linhas físicas, não registros. |
| Linhas com nº de campos ≠ 17 | 0 | 8.469 | [FATO] Leitura íntegra; nenhuma linha descartada. |
| Nulos em `Resolution`, `Time to Resolution`, `Customer Satisfaction Rating` | 5.700 (67,3%) | 8.469 | [FATO] Nulos **estruturais**: só tickets `Closed` têm esses campos. |
| Nulos em `First Response Time` | 2.819 (33,3%) | 8.469 | [FATO] Exatamente os tickets `Open` (2.819). `Pending` tem 1ª resposta e não tem resolução. |
| Duplicatas exatas (com ou sem ID) | 0 | 8.469 | [FATO] |
| E-mails repetidos | 149 | 8.469 | [FATO] Mesmo e-mail com **nomes diferentes** (0 duplicatas nome+e-mail): não identifica cliente recorrente. |
| Descrições repetidas | 392 | 8.469 | [FATO] Reflexo do uso de templates. |
| Domínios de e-mail | example.com 2.904 · example.org 2.796 · example.net 2.769 | 8.469 | [FATO] 100% domínios reservados para exemplo (RFC 2606). |
| Nomes com sufixo (MD, PhD, DDS, Jr., II…) | 164 | 8.469 | [FATO] Padrão típico da biblioteca Faker. [HIPÓTESE] |
| Tipos de dados | 2 numéricas (ID, idade), 1 float (satisfação), 14 texto; datas armazenadas como texto | — | [DECISÃO] Datas convertidas para datetime só dentro da análise. |

### 2.2 Dataset 1 — evidências de dados sintéticos

**Teste de uniformidade (qui-quadrado de aderência, H0 = distribuição uniforme)**

| Variável | Categorias | Mín–máx por categoria | p-valor | Leitura |
|---|---:|---:|---:|---|
| Ticket Channel | 4 | 2.073–2.143 | 0,718 | Uniforme |
| Ticket Priority | 4 | 2.063–2.192 | 0,205 | Uniforme |
| Ticket Type | 5 | 1.634–1.752 | 0,115 | Uniforme |
| Ticket Status | 3 | 2.769–2.881 | 0,328 | Uniforme |
| Ticket Subject | 16 | 478–576 | 0,023 | Quase uniforme |
| Product Purchased | 42 | 178–240 | 0,478 | Uniforme |
| Customer Age (18–70) | 53 | 137–186 | 0,550 | Uniforme |
| Customer Satisfaction (1–5), n=2.769 | 5 | 543–580 | 0,797 | Uniforme |
| Customer Gender | 3 | 2.686–2.896 | 0,007 | Leve desvio |

[FATO] Em uma operação real, seria esperado que alguns canais concentrassem volume, que Critical fosse minoria e que a satisfação tivesse viés (normalmente em forma de J, concentrada em 4–5). Aqui, tudo tem o mesmo peso.

**Teste de independência (qui-quadrado de contingência)**

| Par de variáveis | n | p-valor | V de Cramér | Esperado numa operação real |
|---|---:|---:|---:|---|
| Type × Subject | 8.469 | 0,981 | 0,034 | **Forte** dependência (assunto "Refund" → tipo "Refund") |
| Product × Subject | 8.469 | 0,335 | 0,070 | Dependência (software não tem "bateria") |
| Priority × Channel | 8.469 | 0,079 | 0,025 | Alguma dependência |
| Priority × Type | 8.469 | 0,561 | 0,021 | Alguma dependência |
| Type × Channel | 8.469 | 0,458 | 0,022 | Alguma dependência |
| Priority × Status | 8.469 | 0,227 | 0,022 | Alguma dependência |
| Channel × Status | 8.469 | 0,771 | 0,014 | Alguma dependência |
| Type × Status | 8.469 | 0,339 | 0,023 | Alguma dependência |
| Gender × Type | 8.469 | 0,664 | 0,019 | Independência é plausível |
| Priority × Satisfação | 2.769 | 0,400 | 0,039 | Dependência |
| Channel × Satisfação | 2.769 | 0,468 | 0,038 | Dependência |
| Type × Satisfação | 2.769 | 0,257 | 0,042 | Dependência |

**Incoerências semânticas concretas**

| Indicador | Valor encontrado | n | Interpretação |
|---|---:|---:|---|
| Tickets com assunto "Refund request" cujo tipo **não** é "Refund request" | 79,3% | 576 | [FATO] Tipo e assunto foram sorteados de forma independente (≈ 4/5, que é o esperado por acaso com 5 tipos). |
| Produtos de software (Office, Photoshop, AutoCAD) com assunto Battery/Hardware/Display | 92 | 577 | [FATO] Combinações fisicamente impossíveis. |
| Descrições com termos de bateria/carregador: assunto "Battery life" vs outros assuntos | 7,7% vs 7,3% | 8.469 | [FATO] A descrição não conversa com o assunto. O mesmo vale para Network (6,7% vs 6,9%), Display (12,1% vs 10,4%) e Account access (10,6% vs 9,5%). |
| Primeiras frases distintas nas descrições | 16 | 8.469 | [FATO] "I'm having an issue with the {product_purchased}." abre 5.868 descrições (69,3%). As 10 frases de abertura mais comuns cobrem 88,7% dos tickets. |
| Resoluções contendo algum termo de suporte (replace, reset, refund, install, password…) | 0,0% | 2.769 | [FATO] Todas as 2.769 resoluções são únicas, com mediana de 5 palavras e sem sentido (geradas aleatoriamente). |

**Timestamps**

| Indicador | Valor encontrado | n | Interpretação |
|---|---:|---:|---|
| Faixa de `First Response Time` | 31/05/2023 21:55 → 02/06/2023 00:54 | 5.650 | [FATO] 96,2% caem em um único dia (01/06/2023). |
| Faixa de `Date of Purchase` | 01/01/2020 → 30/12/2021 | 8.469 | [FATO] **Não existe data/hora de abertura do ticket.** |
| Mesmo valor de "segundos" em 1ª resposta e resolução | 100% | 2.769 | [FATO] A resolução = 1ª resposta ± um número inteiro de minutos. |
| Tickets com resolução **antes** da 1ª resposta | 1.365 (49,3%) | 2.769 | [FATO] Impossível numa operação real. |
| Delta (Resolução − 1ª resposta) vs distribuição triangular em ±24h | KS p = 0,166 (não rejeita); desvio-padrão 9,56h vs 9,80h teórico | 2.769 | [FATO] Bate com a **diferença entre dois horários sorteados de forma independente em um dia de 24h**. [HIPÓTESE forte] Os dois horários foram gerados de forma independente. |
| Distribuição da 1ª resposta por hora do dia | 199–292 tickets/hora (madrugada ≈ horário comercial) | 5.650 | [FATO] Não tem o pico diurno que se espera de uma operação real. |

**Conclusão da seção 2.2** — [HIPÓTESE com evidência forte e convergente] O Dataset 1 foi **gerado sinteticamente**: as variáveis foram sorteadas de forma independente a partir de distribuições uniformes, e os textos vêm de templates com placeholders não preenchidos. Nenhuma evidência isolada prova isso, mas **8 sinais independentes** apontam na mesma direção, e nenhum aponta na direção contrária.

### 2.3 Dataset 2 — estrutura e qualidade

| Indicador | Valor encontrado | n | Interpretação operacional |
|---|---:|---:|---|
| Shape | 47.837 × 2 (`Document`, `Topic_group`) | 47.837 | [FATO] |
| Nulos | 0 | 47.837 | [FATO] |
| Duplicatas exatas / após normalizar espaços | 0 / 0 | 47.837 | [FATO] |
| Quase-duplicatas (mesmas 15 primeiras palavras) | 646 registros em 365 grupos | 47.837 | [FATO] Tipicamente threads de e-mail (re:/fw:). |
| …desses grupos, com **rótulos conflitantes** | 38 | 365 | [FATO] Ruído de rotulagem localizado (~10% dos grupos de quase-duplicatas). |
| Textos com maiúsculas / dígitos | 0% / 0% | 47.837 | [FATO] Corpus já pré-processado (lowercase, sem números, pontuação removida, palavras truncadas como "se ca"). |
| Textos com < 5 palavras | 133 (0,28%) | 47.837 | [FATO] Ex.: "annual leave se ca", "new starter please". Pouco informativos. |
| Textos com < 10 palavras | 2.291 (4,8%) | 47.837 | [FATO] |
| Textos com > 300 palavras | 413 (0,9%) | 47.837 | [FATO] Threads longas; máximo de 981 palavras. |
| Vocabulário total / palavras que aparecem uma única vez | 12.327 / 2.715 | 47.837 | [FATO] Vocabulário corporativo restrito. |
| Share de tokens que são boilerplate (hi, please, regards, dias, meses, stopwords) | 38,1% | 47.837 | [FATO] Precisa de limpeza antes de qualquer análise lexical. |

---

## 3. Principais descobertas quantitativas

### 3.1 Dataset 1 — volumes e status

| Indicador | Valor encontrado | n | Interpretação operacional |
|---|---:|---:|---|
| Status | Pending Customer Response 2.881 (34,0%) · Open 2.819 (33,3%) · Closed 2.769 (32,7%) | 8.469 | [FATO] Só 1/3 fechado. [HIPÓTESE, se fosse real] Backlog alto e 34% parado esperando o cliente. |
| Canal | Email 25,3% · Phone 25,2% · Social media 25,0% · Chat 24,5% | 8.469 | [FATO] Sem canal dominante (artificial). |
| Prioridade | Medium 25,9% · Critical 25,1% · High 24,6% · Low 24,4% | 8.469 | [FATO] 1 em cada 4 tickets é "Critical": inflação de prioridade ou dado artificial. |
| Tipo | Refund 20,7% · Technical 20,6% · Cancellation 20,0% · Product inquiry 19,4% · Billing 19,3% | 8.469 | [FATO] |
| Assunto | 16 assuntos, de 5,6% (Display issue) a 6,8% (Refund request) | 8.469 | [FATO] |

### 3.2 Dataset 1 — satisfação

| Indicador | Valor encontrado | n | Interpretação operacional |
|---|---:|---:|---|
| Distribuição das notas 1/2/3/4/5 | 553 / 549 / 580 / 543 / 544 (19,6–20,9% cada) | 2.769 | [FATO] Distribuição plana. Sem a concentração típica em 4–5. |
| Mediana da satisfação | 3 | 2.769 | [FATO] |
| Spearman satisfação × delta de tempo (todos os fechados) | ρ = 0,022 (p = 0,25) | 2.769 | [FATO] Nenhuma relação. |
| Spearman satisfação × delta (só delta ≥ 0) | ρ = 0,003 (p = 0,92) | 1.404 | [FATO] Nenhuma relação. |
| % de notas 4–5 por faixa de tempo (0–2h … 16–24h) | 37,1% a 43,1%, sem tendência | 1.404 | [FATO] Ver heatmap. |
| Satisfação média por prioridade | 2,96 (Critical) a 3,05 (Low) | 2.769 | [FATO] Diferença nula na prática (média usada só porque a mediana é 3 em todos os grupos). |
| Satisfação média por canal | 2,95 (Phone) a 3,08 (Chat) | 2.769 | [FATO] |
| Spearman satisfação × idade | ρ = −0,004 | 2.769 | [FATO] |

### 3.3 Dataset 2 — distribuição de classes

| Categoria | Tickets | % | Mediana de palavras (P25–P75) |
|---|---:|---:|---:|
| Hardware | 13.617 | 28,5% | 32 (19–60) |
| HR Support | 10.915 | 22,8% | 24 (16–41) |
| Access | 7.125 | 14,9% | 22 (15–38) |
| Miscellaneous | 7.060 | 14,8% | 27 (17–48) |
| Storage | 2.777 | 5,8% | 21 (14–37) |
| Purchase | 2.464 | 5,2% | 30 (22–38) |
| Internal Project | 2.119 | 4,4% | 24 (17–40) |
| Administrative rights | 1.760 | 3,7% | 30 (19–55) |
| **Total** | **47.837** | **100%** | **26 (17–46); P90 = 91** |

[FATO] Razão entre a maior e a menor classe = **7,7×**. As 4 maiores classes somam 81%. O comprimento varia entre classes (Kruskal-Wallis p < 0,001), mas as medianas ficam todas entre 21 e 32 palavras. Em caracteres: mediana 175, P25 110, P75 304, P90 612.

### 3.4 Dataset 2 — vocabulário e ambiguidade (após limpeza de boilerplate)

**Palavras distintivas por classe** (frequência de documentos na classe vs fora dela, mínimo de 50 documentos):

| Categoria | Termos mais distintivos | Força do sinal |
|---|---|---|
| Purchase | receipts, ordered, purchased, po, consideration | Muito forte: "po" aparece em 70,6% da classe e em 0,6% do resto. Textos parecem templates de sistema de compras. |
| Storage | decline, wants, folder, archiving, size, mailbox | Forte: "folder" em 28,8% vs 0,6%. Pedidos de acesso a pastas e cota de mailbox. |
| Administrative rights | upgrading, outlook, upgrade, windows, endpoint | Forte: "outlook" em 28,2% vs 0,3%. |
| Access | confluence, git, expire, license, reset, password | Forte: "confluence" em 19,6% vs 0,4%. |
| Internal Project | pipeline, codes, project, code, pas | Médio |
| HR Support | starter, timecard, forwarder, allowance, oracle | Médio; "new starter" (onboarding) domina |
| Hardware | socket, room, charger, conference, rooms | **Fraco**: termos raros (≤ 4,5% da classe) |
| Miscellaneous | copier, mailing, approving, scanner, approvals | **Fraco**: classe-coringa |

**Pares de classes com maior sobreposição de vocabulário** (cosseno das frequências; 0 = nada em comum, 1 = idêntico):

| Par | Cosseno | Jaccard top-200 | Leitura |
|---|---:|---:|---|
| Hardware × Miscellaneous | 0,625 | 0,498 | Par mais ambíguo |
| Hardware × Access | 0,560 | 0,498 | Ambíguo |
| Hardware × HR Support | 0,530 | 0,356 | Ambíguo |
| Hardware × Administrative rights | 0,492 | 0,413 | Moderado |
| HR Support × Miscellaneous | 0,480 | 0,394 | Moderado |
| … | … | … | … |
| Storage × Purchase (menor) | 0,102 | 0,201 | Bem separados |

[FATO] Antes da limpeza, o cosseno entre classes ia de 0,37 a 0,89, inflado por saudações e datas. Depois da limpeza, vai de 0,10 a 0,63. **Purchase é a classe mais separada de todas** (cosseno ≤ 0,24 com todas as outras).

**Sondagem da qualidade dos rótulos** (onde ficam os documentos que contêm uma palavra-chave "óbvia"):

| Palavra | Docs | % na classe esperada | Para onde vai o resto | Leitura |
|---|---:|---:|---|---|
| laptop | 1.685 | 85,1% Hardware | Admin rights 7,1% | Coerente |
| purchase | 2.128 | 78,8% Purchase | HR Support 11,8% | Coerente |
| password | 1.646 | 70,8% Access | **Hardware 19,9%** | Parte de "reset de senha" foi rotulada como Hardware [HIPÓTESE: ruído ou critério de rotulagem diferente] |
| project | 2.307 | 47,5% Internal Project | Misc 16,3% | Termo genérico |
| storage | 797 | 32,2% Storage | HR Support 31,9%, Hardware 25,1% | Ambíguo |
| disk | 311 | 10,3% Storage | **Hardware 46,9%** | Plausível (disco = peça física) |
| administrator | 3.287 | **1,2%** Admin rights | **Purchase 60,2%** | Não é erro: o template de compras contém "log as administrator" |
| salary | 90 | 37,8% HR Support | Hardware 31,1% | Suspeito, mas n pequeno |

[FATO] Só **20,1%** dos documentos de "HR Support" contêm termos clássicos de RH (salary, payroll, leave, holiday, employee, contract, benefits…). As palavras mais frequentes da classe são *access, new, starter, oracle, form*. [HIPÓTESE] "HR Support" significa, na prática, suporte a **sistemas de RH e onboarding de novos colaboradores**, não atendimento de RH em geral.

### 3.5 Cruzamento entre datasets

| Indicador | Valor encontrado | n | Interpretação |
|---|---:|---:|---|
| Colunas em comum / chave de relacionamento | 0 / nenhuma | — | [FATO] Sem ID, e-mail, nome ou data compartilhados. Join impossível. |
| Domínio | D1 = suporte B2C de eletrônicos de consumo · D2 = help desk de TI interna corporativa | — | [FATO] Populações diferentes. |
| % dos tokens de D1 (assunto + descrição) que existem no vocabulário de D2 | 80,5% | 8.469 textos | [FATO] Alto, porque inclui palavras comuns. |
| % das palavras distintas de D1 que existem em D2 | 57,8% | 6.233 palavras | [FATO] Mais de 40% do vocabulário de D1 não existe em D2. |
| Interseção top-300 palavras D1 × top-300 D2 | 98 de 300 | — | [FATO] Sobreposição de vocabulário central baixa → **mudança de domínio** (domain shift). |
| Tickets de D1 cujo assunto **não tem categoria correspondente** em D2 (Refund, Payment, Delivery, Cancellation, Product recommendation) | 2.667 (31,5%) | 8.469 | [FATO sobre contagem; HIPÓTESE sobre o mapeamento] A categoria "Purchase" de D2 é compra interna (pedido de compra/PO), não pagamento de cliente. |

---

## 4. Gargalos operacionais identificados

### 4.1 O que os dados permitem e não permitem afirmar

| Métrica pedida | Calculável? | Motivo |
|---|---|---|
| Tempo de primeira resposta (mediana, percentis, por canal) | **Não** | [FATO] Não existe timestamp de abertura do ticket. `First Response Time` é um horário, não uma duração. |
| Tempo de resolução real | **Não** | [FATO] Mesmo motivo. A única diferença calculável (Resolução − 1ª resposta) é negativa em 49,3% dos casos. |
| SLA de tickets Critical (24h/48h/72h) | **Não como KPI** | [FATO] Por construção, todo delta fica entre −24h e +24h, então qualquer SLA ≥ 24h dá 100% de forma artificial. |
| Top 10 piores combinações canal × prioridade × tipo | **Não de forma confiável** | [FATO] A pior combinação não supera o acaso (teste de permutação p = 0,154). |
| Volume por canal, tipo e prioridade | Sim | Seção 3.1, mas a distribuição é artificialmente uniforme. |
| Status e backlog | Sim | Seção 3.1. |
| Satisfação × tempo | Sim (resultado nulo) | Seção 3.2. |

### 4.2 Teste de consistência temporal (ILUSTRATIVO — não usar como KPI)

[DECISÃO] Para cumprir o escopo pedido e documentar a evidência, calculei o "proxy" **Resolução − 1ª resposta** em duas versões: todos os tickets `Closed` (n = 2.769) e somente os que têm delta ≥ 0 (n = 1.404, descartando os 1.365 negativos e mantendo os 2 iguais a zero). **Esses números descrevem o gerador do dataset, não uma operação.**

| Recorte | n | P25 | Mediana | P75 | P90 | P95 |
|---|---:|---:|---:|---:|---:|---:|
| Todos os Closed | 2.769 | −6,93h | 0,17h | 6,48h | 12,77h | 16,06h |
| Closed com delta ≥ 0 | 1.404 | 3,00h | 6,34h | 11,35h | 16,00h | 18,51h |

| Segmento (delta ≥ 0) | Faixa de medianas entre grupos | Kruskal-Wallis p | % de deltas negativos por grupo (todos os Closed) |
|---|---|---:|---|
| Canal (4) | 6,05h (Phone) – 6,52h (Chat) | 0,791 | 47,3% – 52,7% |
| Prioridade (4) | 5,87h (Medium) – 7,12h (High); Critical 5,98h | 0,091 | 48,1% – 50,9% |
| Tipo (5) | 5,27h (Billing) – 6,98h (Product inquiry) | 0,160 | 47,4% – 51,8% |

**Tickets Critical** — 2.129 no total, 726 fechados, 352 com delta negativo, **374 com delta válido**: ≤ 4h = 36,9% · ≤ 8h = 64,2% · ≤ 12h = 78,9% · ≤ 24h/48h/72h = **100% (artefato: o delta máximo possível é ~24h)**.

**"Top 10 piores combinações"** (79 de 80 combinações têm n ≥ 10; mediana de n por combinação = 17):

| # | Canal | Prioridade | Tipo | n | Mediana (h) | P90 (h) |
|---:|---|---|---|---:|---:|---:|
| 1 | Chat | Low | Technical issue | 15 | 13,23 | 16,70 |
| 2 | Phone | High | Refund request | 13 | 12,65 | 17,87 |
| 3 | Chat | High | Refund request | 22 | 12,45 | 18,40 |
| 4 | Email | Medium | Product inquiry | 14 | 9,67 | 13,17 |
| 5 | Phone | Low | Cancellation request | 10 | 9,25 | 16,07 |
| 6 | Social media | Medium | Billing inquiry | 14 | 9,24 | 17,51 |
| 7 | Email | High | Billing inquiry | 11 | 9,22 | 13,07 |
| 8 | Email | High | Cancellation request | 16 | 9,16 | 16,28 |
| 9 | Social media | Low | Product inquiry | 23 | 9,13 | 17,92 |
| 10 | Social media | High | Refund request | 20 | 8,94 | 19,97 |

[FATO] Ao embaralhar os deltas aleatoriamente entre as combinações (2.000 permutações), a "pior mediana" que aparece só por acaso tem mediana de ~12h e P95 de 14,3h. A pior observada (13,2h) está **dentro do que o acaso produz** (p = 0,154). Com n de 10 a 23 por célula, **esse ranking é ruído**.

Outliers: nenhum outlier pelo critério IQR no recorte válido (n = 1.404). As anomalias reais são estruturais: deltas negativos, timestamps comprimidos em 27h e satisfação plana.

### 4.3 Gargalos que os dados sustentam (com cautela)

1. **[FATO] Ausência de instrumentação de tempo.** O próprio dataset demonstra o primeiro gargalo de qualquer redesign: sem `created_at`, `first_response_at` e `resolved_at` confiáveis, não dá para medir SLA. Esse é um achado de **governança de dados**, não um detalhe técnico.
2. **[FATO] Backlog e tickets parados.** 67,3% dos tickets não estão fechados, e 34,0% estão em "Pending Customer Response". [HIPÓTESE, já que o dado é sintético] Numa operação real com esse perfil, follow-up automático e regras de fechamento por inatividade seriam alavancas prioritárias.
3. **[FATO] Prioridade sem efeito.** Critical não é atendido mais rápido (Kruskal p = 0,09; mediana 5,98h vs 7,08h em Low) e representa 25% do volume. [HIPÓTESE] Se fosse real, isso indicaria que a priorização não muda o roteamento, o que é um problema clássico de triagem.
4. **[FATO] Classificação manual incoerente.** Tipo e assunto não têm relação (V = 0,034). [HIPÓTESE] Numa operação real, isso apontaria para categorização manual não confiável, justamente o problema que um classificador treinado no Dataset 2 resolveria.

---

## 5. Oportunidades preliminares de automação

Só listo o que os dados sustentam. Nada aqui foi modelado ou testado ainda.

| # | Oportunidade | Evidência nos dados | Força da evidência |
|---|---|---|---|
| 1 | **Triagem/roteamento automático por categoria** (classificador de texto) | D2: 47.837 textos rotulados, ≥ 1.760 por classe, vocabulário distintivo em 5 de 8 classes | **Alta** para o domínio de TI interna; **a validar** fora dele |
| 2 | **Fila dedicada/autoatendimento para Purchase** (pedidos de compra, confirmação de recebimento) | Textos padronizados: "po" em 70,6%, "purchased" em 65,3%, "receipts" em 47,3% da classe | Alta |
| 3 | **Autoatendimento de Storage** (aprovar/recusar acesso a pasta, aumentar cota de mailbox) | "folder" 28,8%, "accept" 27,2%, "decline" 25,7%, "wants" 26,8% da classe | Alta |
| 4 | **Reset de senha / desbloqueio / acesso self-service** | "password" em 1.646 docs (70,8% em Access); "reset" em 10,3% de Access; "confluence" em 19,6% | Média-alta |
| 5 | **Follow-up automático para "Pending Customer Response"** | D1: 34,0% dos tickets nesse status | **Baixa** (dado sintético; vale como hipótese de processo) |
| 6 | **Recategorização automática dos tickets do D1** (preencher a categoria que hoje é incoerente) | Type × Subject independentes (V = 0,034) | Média como problema; **sem gabarito** para medir o ganho no D1 |

**Uso do Dataset 2 como corpus de treino para o Dataset 1:**
- **Entrada no D1:** `Ticket Subject` + `Ticket Description` (removendo o placeholder `{product_purchased}`), aplicando o mesmo pré-processamento do D2 (lowercase, sem pontuação e dígitos, remoção de boilerplate).
- **Colunas enriquecidas no D1:** nova coluna `predicted_topic_group` (8 classes do D2) + `prediction_confidence`, com regra de fallback para fila humana quando a confiança for baixa. A partir delas, dá para derivar uma `routing_queue` e uma flag `automation_candidate`.
- **Riscos (fatos medidos):** (a) domain shift: só 98 das top-300 palavras coincidem; (b) 31,5% dos tickets do D1 têm assuntos (reembolso, pagamento, entrega, cancelamento, recomendação) **sem classe correspondente** no D2; (c) **não existe gabarito no D1** para medir a acurácia, já que tipo e assunto são aleatórios. Qualquer métrica de desempenho precisa ser medida em um holdout do D2, e a aplicação no D1 deve ser apresentada como **demonstração do fluxo**, não como resultado validado.

---

## 6. Limitações metodológicas

1. **Dataset 1 não serve para KPIs operacionais.** Não tem timestamp de abertura; os timestamps existentes são incoerentes (49,3% negativos) e as variáveis são independentes por construção. Os números de tempo da seção 4.2 são ilustrativos.
2. **A conclusão de "dado sintético" é inferência.** Ela é forte (8 sinais convergentes), mas eu não tenho a documentação de origem do dataset. Testes de aderência com n grande detectam desvios mínimos; por isso, a força da evidência está na **combinação** de uniformidade, independência, placeholders e timestamps, não em um p-valor isolado.
3. **A contagem do briefing (~29.807) não bate com a de registros (8.469).** A diferença está explicada (quebras de linha dentro dos campos de texto) e documentada. Nenhuma linha foi descartada.
4. **O Dataset 2 já chega pré-processado.** Sem maiúsculas, pontuação nem números, e com palavras truncadas. Isso limita features (por exemplo, códigos de erro e números de PO se perderam) e exige replicar o mesmo pré-processamento em qualquer texto novo.
5. **A qualidade dos rótulos do D2 foi avaliada por sondagem, não por revisão manual completa.** As sondagens por palavra-chave indicam ruído localizado (ex.: 19,9% dos docs com "password" estão em Hardware; 38 grupos de quase-duplicatas com rótulos conflitantes), mas a taxa real de erro de rotulagem só vai aparecer com um classificador + revisão das confusões.
6. **A lista de boilerplate é uma decisão manual.** Stopwords do sklearn + saudações, dias e meses (356 termos). Uma lista diferente mudaria um pouco os cossenos, mas não a ordem dos pares mais ambíguos (que ficou estável antes e depois da limpeza: Hardware × Miscellaneous em 1º).
7. **Média usada pontualmente:** só para satisfação por grupo, porque a mediana é 3 em todos os grupos e não discrimina. Sempre com o n informado.
8. **Sem dados financeiros.** Nenhum dos datasets tem custo, headcount, salário, volume histórico ou meta de SLA. **ROI não é calculável só com os dados.** Faltam:
   - custo por agente/hora (ou salário + encargos) e headcount por nível (N1/N2);
   - Tempo Médio de Atendimento (TMA, ou AHT) real por categoria e canal;
   - volume mensal real e sazonalidade;
   - metas de SLA por prioridade e multas/penalidades contratuais;
   - taxa atual de reabertura e de transferência entre filas (re-roteamento);
   - custo da ferramenta/infra de IA (licença, tokens, manutenção);
   - custo de erro (ticket roteado errado → minutos de retrabalho);
   - taxa de resolução no primeiro contato (FCR) e impacto de churn/CSAT em receita.

---

## 7. Recomendações para a próxima etapa

1. **Reposicionar o Dataset 1 como "caso de auditoria".** Usar os achados da seção 2.2 como diferencial da submissão: mostra que eu valido o dado antes de construir em cima dele. Usar o D1 só pelo **esquema de campos** (canal, prioridade, status, satisfação) para desenhar o fluxo-alvo e a instrumentação necessária.
2. **Usar o Dataset 2 como base do protótipo de triagem.** Começar com um baseline simples e explicável (TF-IDF + modelo linear), medindo F1 por classe em holdout estratificado, e depois comparar com um LLM zero/few-shot. Reportar a matriz de confusão com foco em Hardware × Miscellaneous × Access.
3. **Desenhar o redesign em cima de 3 alavancas sustentadas pelos dados:** triagem automática, autoatendimento das classes padronizadas (Purchase, Storage, reset de senha) e instrumentação de tempo (created/first_response/resolved) como pré-requisito de qualquer SLA.
4. **ROI por cenários parametrizados**, em planilha com premissas editáveis (custo/hora, TMA, volume, % automatizável por classe), rotulando claramente o que é premissa de mercado e o que vem dos dados. Nunca apresentar como número medido.
5. **Demonstração no D1:** aplicar o classificador nos textos do D1 só para ilustrar o fluxo (distribuição das categorias previstas + % de baixa confiança → fila humana), deixando explícito que não há gabarito.

---

## 8. Decisões que precisam de aprovação do usuário antes de avançar

| # | Decisão | Minha recomendação |
|---|---|---|
| 1 | Tratar o Dataset 1 como **sintético** e **não** derivar KPIs de tempo/SLA dele, apresentando a auditoria como achado da submissão | **Sim.** É a postura defensável diante de uma banca, e transforma uma limitação em prova de rigor. |
| 2 | Usar o Dataset 2 como **base principal** do protótipo de triagem/roteamento | **Sim** |
| 3 | Manter as **8 classes** como estão ou consolidar/renomear (ex.: "HR Support" → "Sistemas de RH / Onboarding"; tratar "Miscellaneous" como fila humana) | Manter as 8 no treino e decidir a consolidação depois de ver a matriz de confusão |
| 4 | Limpeza do D2: remover os **133 textos com < 5 palavras** e os **38 grupos de quase-duplicatas com rótulo conflitante** | Remover do treino e documentar (impacto < 1% do corpus) |
| 5 | Tratamento do desbalanceamento (7,7×): pesos por classe vs reamostragem | Pesos por classe + métrica F1-macro (não acurácia) |
| 6 | Mapeamento dos assuntos do D1 → classes do D2, e destino dos 31,5% sem correspondência (reembolso, pagamento, entrega, cancelamento, recomendação) | Criar uma fila "Financeiro/Comercial" fora do classificador de TI e declarar a limitação |
| 7 | Fonte das premissas de ROI: **você tem números reais** da sua experiência (custo/hora, TMA, volume) ou uso benchmarks públicos rotulados como premissa? | Usar faixas de mercado como premissa editável. Se você tiver referências da sua operação (sem dados sigilosos), elas deixam o caso mais forte. |
| 8 | Enquadramento do redesign: triagem + autoatendimento + instrumentação de SLA como pilares | **Sim.** Conecta direto com o seu case "Link de Análise Especial" (de 2–5 dias para tempo real). |

---

### Anexo — Gráficos gerados (`analysis/charts/`)

| Arquivo | Conteúdo |
|---|---|
| `d1_volumes.json` | Volume por canal, prioridade e tipo (D1) |
| `d1_box_resolution.json` | Boxplot do proxy de tempo por canal e prioridade (ilustrativo) |
| `d1_delta_hist.json` | Histograma do delta Resolução − 1ª resposta (evidência de sinteticidade) |
| `d1_sat_heatmap.json` | Satisfação × faixa de tempo (% por linha) |
| `d1_sat_dist.json` | Distribuição das notas de satisfação |
| `d2_categories.json` | Distribuição por categoria (D2) |
| `d2_length.json` | Comprimento dos textos por categoria (D2) |
| `d2_overlap.json` | Similaridade de vocabulário entre categorias, após limpeza (D2) |
