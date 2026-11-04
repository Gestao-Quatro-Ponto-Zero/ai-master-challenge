# F1 — Report (Auditoria dos dados)

Pasta da submissão = `ai-master-challenge/submissions/gustavo-covaleski/` ("a submissão"). Todos os scripts rodam com o Python do venv da submissão (`.venv/Scripts/python`).

## 1. O que foi feito

1. Passo 0: branch `submission/gustavo-covaleski` confirmado, `git status --porcelain` vazio; faltavam pandas/scikit-learn/scipy/pytest, instalados num `.venv` da submissão (decisão do Gustavo nesta sessão). Estrutura, `.gitignore` e `requirements.txt` criados.
2. `solution/comum.py` com caminhos via `Path(__file__)`, `DATA_DIR`, `PLANNING_DIR`, `OUT_DIR`, `SEED = 42` e leitores.
3. Passo 1: `f1_verificar_dados.py` (bytes, SHA-256, linhas, colunas). Contagens e colunas conferem; execução seguiu.
4. Passo 2: `f1_auditoria_ds1.py` (T1–T8).
5. Passo 3: `f1_auditoria_ds2.py` (perfil, pré-processamento, duplicados exatos, quase-duplicados com TF-IDF + cosseno ≥ 0,90, grupos, holdout congelado, exposição a vazamento).
6. Passo 4: `f1_planilha_revisao.py` (variante cega, 60 tickets). Passo 4b: `f1_adjudicacao.py` escrito; executado só contra planilhas sintéticas dos testes.
7. Passo 5: `solution/tests/test_f1.py`, 10 testes, todos passando.
8. Sequência de aceite rodada de ponta a ponta a partir de `solution/outputs/` e `planning/F1-revisao/` vazios.

## 2. Resultados

Siglas de arquivo: **[dados]** = `solution/outputs/f1_dados.json` (`f1_verificar_dados.py`); **[ds1]** = `solution/outputs/f1_ds1_auditoria.json` e `f1_ds1_fatos.csv` (`f1_auditoria_ds1.py`); **[ds2]** = `solution/outputs/f1_ds2_auditoria.json` (`f1_auditoria_ds2.py`); **[splits]** = `solution/outputs/f1_splits.csv` (`f1_auditoria_ds2.py`); **[rev]** = `planning/F1-revisao/revisao_*.csv` (`f1_planilha_revisao.py`).

### Passo 1 — arquivos [dados]

| Arquivo | Linhas de dados | Linhas físicas | Colunas | SHA-256 (12 primeiros) |
|---|---|---|---|---|
| `customer_support_tickets.csv` | 8.469 (esperado 8.469) | 29.808 | 17 | ver JSON |
| `all_tickets_processed_improved_v3.csv` | 47.837 (esperado 47.837) | 47.838 | 2 | ver JSON |

Colunas de cliente do DS1 com nome real: `Customer Name`, `Customer Email`, `Customer Age`, `Customer Gender`.

### Passo 2 — DS1 [ds1]

| Teste | Resultado medido | Confirmada |
|---|---|---|
| T1 | 8.469 linhas, 8.469 `Ticket ID` únicos | s |
| T2 | `Ticket Description`: 100,0% das linhas (8.469) com marcador; `Subject` e `Resolution`: 0%. Top 5: `{product_purchased}` 13.873, `{error_message}` 472, `{product_id}` 52, `{product_name}` 34, `{Product_purchased}` 18 | s |
| T3 | Os dois campos são timestamps. `First Response Time`: 33,29% nulo, de 2023-05-31 21:55 a 2023-06-02 00:54. `Time to Resolution`: 67,30% nulo, de 2023-05-31 21:53 a 2023-06-02 00:55. Resolução antes da 1ª resposta: 1.365 de 2.769 Closed = **49,30%** | s |
| T4 | Colunas de data: `Date of Purchase` (2020-01-01 a 2021-12-30), `First Response Time`, `Time to Resolution`. Nenhuma de abertura | s |
| T5 | Notas 1–5: 553 / 549 / 580 / 543 / 544; 67,30% nulo (100% nulo em Open e Pending, 0% em Closed). Qui² contra uniforme: 1,6663, p = 0,7968. LR (n = 2.769), macro-F1: modelo 0,2122 ± 0,0186; rótulo embaralhado 0,1871 ± 0,0092; majoritária 0,0693 (acurácia: 0,2156 ± 0,0186 / 0,1907 ± 0,0085 / 0,2095). Com duração: 0,2144 ± 0,0194 vs embaralhado 0,1910 ± 0,0054. **Critério de confirmação definido após ver os dados; aceito pelo Gustavo no portão F1** | s (ver §3 e §4) |
| T6 | Closed com duração > 0: n = 1.402. Kruskal-Wallis: prioridade H = 6,94, p = 0,0737; canal H = 1,15, p = 0,7653; tipo H = 7,00, p = 0,136. Medianas 5,27–7,12 h. **Variável de tempo sob suspeita (T3)** | s |
| T7 | Pending Customer Response 2.881, Open 2.819, Closed 2.769 → 67,30% não Closed. Open: 1ª resposta, resolução e CSAT 100% nulos. Pending: 1ª resposta 0% nula; resolução e CSAT 100% nulos. Closed: nada nulo | s |
| T8 | 5 tipos: Refund request 1.752, Technical issue 1.747, Cancellation request 1.695, Product inquiry 1.641, Billing inquiry 1.634. 8.469 e-mails válidos por regex (de 8.469 não nulos). `Resolution`: 67,30% nulo, 2.769 valores únicos (cada um aparece 1 vez) | s |

### Passo 3 — DS2 [ds2], [splits]

| Item | Resultado |
|---|---|
| 3.1 Nulos / vazios / < 3 palavras | 0 / 0 / 14 |
| 3.1 Classes (%) | Hardware 28,47; HR Support 22,82; Access 14,89; **Miscellaneous 14,76**; Storage 5,81; Purchase 5,15; Internal Project 4,43; Administrative rights 3,68 |
| 3.1 Palavras por texto | p5 10; p50 26; p95 136; máx. 981 |
| 3.1 Não ASCII | 0,00% |
| 3.1 Dados pessoais (regex) | e-mail 0; telefone 8+ dígitos 0; URL 0 |
| 3.2 Pré-processamento | maiúscula 0,00%; pontuação 0,03%; alguma palavra funcional 24,94% (`to` 16,58%, `the` 3,64%, `and` 3,54%, `of` 1,91%, `a` 1,78%, `is` 1,35%, `in` 0,00%) → **pré-processado** |
| 3.4 Duplicados exatos (após normalização) | **0** grupos, 0 tickets |
| 3.5 Pares por cosseno | ≥ 0,80: 51.483; ≥ 0,90: 10.149; ≥ 0,95: 1.961 |
| 3.5 Grupos (cos ≥ 0,90) | 45.615 grupos; 870 com tamanho ≥ 2; 6,46% dos tickets em grupos ≥ 2; maior grupo 217 (0,45% das linhas, abaixo do alerta de 1%) |
| 3.5 Conflito de rótulo | **118 tickets fora da maioria do próprio grupo** = 3,82% dos 3.092 tickets em grupos ≥ 2 = 0,25% da base. 61 grupos com mais de um rótulo somam 360 tickets, mas 144 desses 360 estão num único grupo encadeado (`group_id` 11923: Hardware 112, Storage 18, Miscellaneous 14); 41 dos 61 grupos em conflito têm tamanho 2 (`f1_ds2_auditoria.json`, `3.5_quase_duplicados`) |
| 3.6 Pares de fronteira (amostra de 20 + 20) | [0,85; 0,90): 2 de 20 com rótulo diferente; [0,90; 0,95): 3 de 20 (`planning/F1-revisao/f1_pares_fronteira.csv`) |
| 3.7 Holdout por grupo | 9.567 linhas (20,00%) |
| 3.7 Holdout aleatório | 9.568 linhas (20,00%) |
| 3.7 % por classe | diferença máxima de 0,01 p.p. entre holdout e total, nos dois holdouts |
| 3.7 Exposição a vazamento (sem modelo) | aleatório: **564 tickets do holdout (5,89%)** têm quase-duplicado no treino; por grupo: 0 (0,00%), confirmado |

### Passo 4 — planilha [rev]

- 60 tickets: Access 8, Administrative rights 6, HR Support 9, Hardware 11, Internal Project 6, Miscellaneous 8, Purchase 6, Storage 6.
- As 8 categorias válidas, exatamente como nos dados: `Access`, `Administrative rights`, `HR Support`, `Hardware`, `Internal Project`, `Miscellaneous`, `Purchase`, `Storage`.
- `rotulo_original` e `meu_rotulo` vazios (testado). Gabarito em `revisao_gabarito.csv`; pesos em `revisao_pesos.csv`.

### Passo 5 — testes

`pytest solution/tests -q` → **10 passed**.

## O que os dados permitem e não permitem afirmar

**Permitem afirmar:**
- O DS1 tem 8.469 tickets, cada um com `Ticket ID` único (T1, [ds1]).
- O DS1 tem 5 tipos de ticket, não 3, incluindo reembolso (1.752) e cancelamento (1.695) (T8, [ds1]).
- 67,30% do DS1 não está Closed, e só os Closed têm resolução e CSAT (T7, [ds1]).
- O DS1 contém nome e e-mail de cliente em 100% das linhas (8.469 e-mails válidos), útil como caso de mascaramento (T8, [ds1]).
- O DS2 tem 47.837 tickets, sem nulos, sem duplicados exatos, com 8 categorias; Miscellaneous é 14,76% (3.1, 3.4, [ds2]).
- No DS2, 6,46% dos tickets têm quase-duplicado (cos ≥ 0,90); 118 tickets divergem do rótulo majoritário do próprio grupo (3,82% dos 3.092 tickets em grupos; 0,25% da base); 144 dos 360 tickets em grupos com conflito estão num único grupo encadeado Hardware/Storage/Miscellaneous (3.5, `f1_ds2_auditoria.json` → `tickets_fora_da_maioria_do_grupo`, `maior_grupo_em_conflito`).
- Um holdout aleatório deixa 5,89% dos tickets de teste com um quase-duplicado no treino; o holdout por grupo, 0% (3.7, [ds2], [splits]).
- O texto do DS2 vem pré-processado: 0% de maiúsculas, 0,03% com pontuação, palavras funcionais majoritariamente removidas (3.2, [ds2]).

**Não permitem afirmar:**
- Nenhuma conclusão de tempo de atendimento do DS1: 49,30% dos Closed resolvem antes da 1ª resposta, e todos os timestamps caem numa janela de ~27 h (T3, [ds1]).
- Tempo de espera até a 1ª resposta: não há data de abertura (T4, [ds1]).
- Gargalo por prioridade, canal ou tipo: Kruskal-Wallis p ≥ 0,07 nos três, sobre variável já sob suspeita (T6, [ds1]).
- Fatores de satisfação: CSAT indistinguível de uniforme (p = 0,7968) e modelo sem ganho robusto sobre rótulo embaralhado (T5, [ds1]).
- Qualquer NLP sobre o texto do DS1: 100% das descrições têm marcador de template não preenchido (T2, [ds1]).
- O comportamento de um classificador/LLM sobre texto em linguagem natural a partir do DS2: o texto está degradado (3.2, [ds2]).
- Desempenho fora do inglês ou com dado pessoal real a partir do DS2: 0% não ASCII e 0 acertos de e-mail/telefone/URL (3.1, [ds2]).
- Volume anual real: o DS1 não tem data de abertura, e o volume do brief (~30 mil) segue como premissa (T1, T4).

## 3. O que contraria a hipótese ou a expectativa

- **Não existem duplicados exatos no DS2** (0, mesmo após normalização; também 0 no texto bruto). A armadilha "existem quase-duplicados" se confirma (870 grupos), mas o conjunto parece ter sido deduplicado exatamente na origem. Nenhuma aresta do grafo veio de duplicado exato.
- **T2 é mais forte que o relatado:** não ~uma fração, mas 100% das descrições têm marcador. `{product_purchased}` aparece 13.873 vezes (mais de uma por ticket).
- **Linhas físicas × registros no DS1:** o CSV tem 29.808 linhas físicas para 8.469 tickets ([dados]). A origem do "~30 mil" do brief **não foi verificada**.
- **Janela de tempo de ~27 h:** todos os timestamps de 1ª resposta e resolução estão entre 2023-05-31 21:53 e 2023-06-02 00:55, enquanto as compras vão de 2020 a 2021. Não estava entre as armadilhas listadas.
- **T5, não uniforme no modelo:** o macro-F1 do modelo (0,2122) fica 2,5 p.p. acima do rótulo embaralhado (0,1871). Pela regra que usei (ver §4), isso não conta como sinal, mas não é zero. O qui² não rejeita uniforme.
- **T6, prioridade com p = 0,0737:** perto de 0,05, mas sobre a variável de tempo invalidada por T3.
- **Texto do DS2 sem palavras funcionais na maioria:** só 24,94% dos documentos têm alguma das 7 palavras; `in` nunca aparece. Indica remoção de stopwords incompleta ou por lista.
- **Nenhum dado pessoal no texto do DS2** (0 e-mail, 0 telefone, 0 URL): o golden set de mascaramento vai depender de casos inseridos ou do DS1.

## 4. Desvios da spec

- **Dependências instaladas** (pandas 3.1.0, scikit-learn 1.9.1, scipy 1.18.1, pytest 9.2.0) num `.venv` da submissão, por decisão do Gustavo nesta sessão; numpy 2.5.4 já existia no sistema e foi reinstalado na mesma versão no venv. Dependências de transição em `pip freeze` (joblib, threadpoolctl etc.) não foram fixadas no `requirements.txt`.
- **Critério de "confirmada" não definido na spec para T3, T5, T6, T7, T8.** Usei: T1 linhas < 15 mil; T2 > 0%; T3 > 10%; T4 nenhuma coluna com open/creat/abert/submit; **T5 = s se qui² p ≥ 0,05 e (macro-F1 do modelo − embaralhado) < 2 × maior dp, parcial se só um dos dois**; T6 todos os p ≥ 0,05; T7 > 50%; T8 > 3 tipos. Todos deram `s`; a regra de T5 é a mais discutível (ver §3). Revisar no portão.
- **T5 com duração:** a spec diz "+ duração em horas se T3 permitir calcular". A duração é calculável, mas T3 confirmou que ela é inválida. Rodei as duas versões (sem e com duração); o veredito usa a versão sem duração.
- **T8 `Resolution` top 5:** os textos foram para `planning/F1-revisao/f1_ds1_resolution_top5.csv`, fora do repositório; o JSON do repo guarda só as contagens. Motivo: a convenção da fase proíbe texto de ticket no repositório. Os 5 valores aparecem 1 vez cada (todos os 2.769 são únicos).
- **Normalização (3.4):** "não alfanumérico" implementado como `[\W_]+` (Unicode); com 0% de não ASCII, equivale a `[^0-9a-z]`.
- **Cosseno em float32 com tolerância 1e-6** nos limiares (para não perder cosseno exato de 0,90 por arredondamento). Blocos de 2.000 linhas, como na spec.
- **`f1_adjudicacao.py`** aceita `--dir-revisao` e `--dir-saida` (padrão = caminhos da spec) para os testes rodarem em `tmp_path`.
- Na planilha, a amostragem por categoria foi feita a partir de um ticket por `group_id` (sorteado com seed 42) e o empate de maiores restos é resolvido por ordem alfabética.

## 5. Erros e correções durante a execução

- `pip install` falhou na 1ª tentativa por `ReadTimeoutError` em files.pythonhosted.org; refeito com `--timeout 120 --retries 5`.
- Saída do console em cp1252 quebrou acentos; os scripts rodam com `PYTHONIOENCODING=utf-8` (não afeta os arquivos gravados).
- A 1ª versão do T8 gravava os 5 textos de `Resolution` no JSON do repositório; movidos para `planning/` (ver §4).
- 0 duplicados exatos pareceu bug; conferido de forma independente (`Document.duplicated()` = 0 no bruto e no normalizado).

## 6. Pendências e decisões que dependem do Gustavo

1. **Bloqueio de commit (importante).** O `.gitignore` da raiz do repositório (linha 16) tem `submissions/`. Por isso `git status --porcelain` fica vazio e `git add submissions/gustavo-covaleski/` **não adiciona nada**. Alterar o `.gitignore` da raiz está fora do escopo permitido. A saída óbvia, `git add -f`, **também ignora o `.gitignore` da submissão** e adicionaria `.venv/` e `__pycache__/`. Antes do 1º commit, decidir como adicionar (ex.: `git add -f` só em caminhos explícitos, sem `.venv/`). Nenhum commit foi feito.
2. Regra de confirmação do T5 (§4): aceitar ou trocar.
3. Revisão cega: abrir `planning/F1-revisao/revisao_rotulos.csv` (não abrir `revisao_gabarito.csv` antes de terminar). Depois rodar `python solution/f1_adjudicacao.py preparar`.
4. Opcional: calibrar o limiar a olho com `planning/F1-revisao/f1_pares_fronteira.csv` (o limiar 0,90 não foi alterado).
5. Consequência pré-registrada do 3.2 vale para a F3 (LLM sobre texto degradado) e a F5 (injeção em texto que não é linguagem natural).

## 7. Tempo gasto × orçado

- Orçado: 45 min (teto 54 min).
- Medido pelo relógio do sistema: execução de 18:45 a ~19:00 (~15 min), mais a leitura inicial de CLAUDE.md, F0 e spec antes das 18:45 (não cronometrada) e a espera da sua resposta sobre dependências. Dentro do orçado.
