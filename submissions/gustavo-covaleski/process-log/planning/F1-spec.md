# F1 — Auditoria dos dados (spec para o Claude Code)

- **Teto:** 45 min. Ao chegar a 54 min (120%), pare e proponha o corte no report.
- **Leia antes:** `CLAUDE.md` e `planning/F0-escopo.md`.
- **Objetivo:** medir cada armadilha conhecida dos dois datasets; congelar os grupos de quase-duplicados e o holdout **antes de qualquer modelo**; preparar a planilha da revisão manual de rótulos.
- **Saída do portão F1:** a lista do que os dados permitem e do que não permitem afirmar, com número e origem.

As consequências da seção 2 estão **pré-registradas**: foram definidas no F0, antes de ver os dados. Aplique a regra correspondente ao resultado; não reinterprete.

---

## Convenções desta fase

- Pasta da submissão: `ai-master-challenge/submissions/gustavo-covaleski/` (abaixo, "a submissão").
- Crie `solution/comum.py` com: caminhos resolvidos a partir de `Path(__file__)` (não do diretório atual), `DATA_DIR` (variável de ambiente; padrão `../../../data` relativo à submissão), `PLANNING_DIR` (`challenge-g4-ai-master/planning`), `OUT_DIR` (`solution/outputs`), `SEED = 42` e funções de leitura dos dois CSVs.
- **Arquivos que contêm texto de ticket ficam fora do repositório**, em `planning/F1-revisao/`. Dentro do repositório (`solution/outputs/`) só entram números, ids e agregados. Única exceção: a planilha final adjudicada do passo 4b, que vai para `process-log/`.
- Nenhuma saída e nenhum report podem conter nome, e-mail ou outro dado pessoal do DS1. Só contagens.
- CSVs para o Gustavo abrir no Excel: separador `;`, codificação `utf-8-sig`.

## Passo 0 — Pré-condições (pare se algo falhar)

1. **Git.** Commits são feitos só pelo Windows, com `git add submissions/gustavo-covaleski/`, e nunca nesta fase. No clone, confirme `git branch --show-current` = `submission/gustavo-covaleski`. Rode `git status --porcelain`. Se aparecer qualquer caminho fora de `submissions/gustavo-covaleski/`, **pare e reporte a lista**. Não use `checkout`, `restore` nem `reset` para "limpar". (Contexto: rodando git dentro de uma VM Linux, 11 arquivos fora da pasta apareceram modificados só por diferença de fim de linha; no Windows o esperado é estar limpo.)
2. **Ambiente.** Python ≥ 3.11; `pandas`, `numpy`, `scikit-learn`, `scipy` e `pytest` importam. Registre as versões no report. Se faltar algo, reporte qual pacote e por quê antes de instalar.
3. **Estrutura.** Crie, se não existir: `solution/outputs/`, `solution/tests/`, `process-log/chat-exports/`, `process-log/screenshots/`, `docs/`. **Não sobrescreva** `process-log/process-log.md` (já existe).
4. `.gitignore` da submissão com: `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`. Não ignore `*.csv` de forma global: os CSVs de `solution/outputs/` são entrega.
5. `requirements.txt` da submissão com as versões instaladas dos pacotes usados (fixas, `==`).

## Passo 1 — Verificar `data/` (pare se divergir) — `solution/f1_verificar_dados.py`

Para cada arquivo em `DATA_DIR`: nome, tamanho em bytes, SHA-256, número de linhas e lista exata de colunas. Saída: `solution/outputs/f1_dados.json`.

Esperado:
- `customer_support_tickets.csv` (DS1): 8.469 linhas.
- `all_tickets_processed_improved_v3.csv` (DS2): 47.837 linhas.

Colunas necessárias para a auditoria:
- DS1: `Ticket ID`, `Ticket Type`, `Ticket Description`, `Ticket Status`, `Resolution`, `Ticket Priority`, `Ticket Channel`, `First Response Time`, `Time to Resolution`, `Customer Satisfaction Rating`.
- DS2: `Document`, `Topic_group`.

**Se o número de linhas for diferente do esperado, ou se faltar uma coluna necessária: pare aqui e escreva o report só com isso.** Diferenças de nome em colunas de cliente (ex.: `Customer Email` em vez de `Email`) não param a execução: só registre os nomes reais.

## Passo 2 — Auditoria do DS1 — `solution/f1_auditoria_ds1.py` (≤ 15 min)

Saídas: `solution/outputs/f1_ds1_auditoria.json` (todos os números) e `solution/outputs/f1_ds1_fatos.csv` com as colunas `teste | armadilha | resultado | confirmada (s/n/parcial) | consequencia_aplicada`.

| Teste | O que medir | Se confirmar (consequência pré-registrada) | Se não confirmar |
|---|---|---|---|
| T1 Volume | Linhas e `Ticket ID` únicos | Uma linha no README; extrapolações usam o volume do brief como premissa editável | Usar o volume medido |
| T2 Template | % de linhas com regex `\{[^{}]+\}` em `Ticket Description`, `Ticket Subject` e `Resolution`; os 5 marcadores mais frequentes com contagem | Texto do DS1 fica fora de qualquer NLP; o DS1 entra só por metadados | O texto do DS1 pode ser usado para testar o classificador |
| T3 Tempos | Tipo real de `First Response Time` e `Time to Resolution` (timestamp ou duração), mín., máx., % nulo. Se forem timestamps: entre os `Closed` com os dois preenchidos, % com resolução antes da 1ª resposta | Horas do DS1 deixam de valer como diagnóstico; Q1 segue pelo ramo "MDE + instrumentação" | Seguir com tempos como métrica |
| T4 Abertura | Existe coluna de data de abertura? Liste as colunas de data e o intervalo de cada uma (`Date of Purchase` não é abertura) | Espera até a 1ª resposta não é mensurável; vira o evento `ticket_criado` | Calcular a espera |
| T5 CSAT | Contagem por nota, % nulo, nulos por status. Qui-quadrado contra uniforme (`scipy.stats.chisquare`). `LogisticRegression` multinomial com one-hot de tipo, prioridade, canal, produto e gênero + idade (+ duração em horas se T3 permitir calcular), `StratifiedKFold(5, shuffle=True, random_state=42)`: acurácia e macro-F1 (média ± dp) contra (a) classe majoritária e (b) o mesmo modelo com rótulo embaralhado (seed 42) | Não afirmar nenhum fator de satisfação; CSAT por ticket ligado a eventos entra na instrumentação | Reportar os fatores com tamanho de efeito na F2 |
| T6 Prioridade × tempo | Kruskal-Wallis da duração (resolução − 1ª resposta, em horas) por prioridade, entre `Closed` com duração positiva: n e mediana por grupo, H, p. Repetir uma vez por canal e uma por tipo. Marcar no resultado: "variável de tempo sob suspeita (T3)" | Sem gargalo por segmento afirmável a partir do DS1 | Vira o 1º achado da F2 |
| T7 Status | Contagem por status; cruzamento status × 1ª resposta nula, status × resolução nula, status × CSAT nulo | A análise de tempo cobre só os `Closed`; "Pending" mistura espera do cliente com espera do atendente | Análise de tempo na base inteira |
| T8 Conteúdo | Valores observados de `Ticket Type` (o brief lista 3); colunas com dado pessoal e contagem de e-mails válidos por regex (sem imprimir valores); `Resolution`: % nulo, nº de valores únicos, 5 mais frequentes com contagem (truncados em 80 caracteres) | Tipos extras (ex.: reembolso, cancelamento) entram na política da F4; dado pessoal do DS1 entra no golden set de mascaramento | Registrar |

Não faça nenhuma outra análise de segmento do DS1 (a Q1 é enxuta).

## Passo 3 — Auditoria do DS2, grupos e holdout — `solution/f1_auditoria_ds2.py` (≤ 20 min)

Saídas no repositório: `solution/outputs/f1_ds2_auditoria.json`, `solution/outputs/f1_splits.csv`. Saídas com texto (fora do repo): `planning/F1-revisao/`.

**3.1 Perfil.**
- Linhas, nulos, textos vazios ou com menos de 3 palavras.
- Distribuição das classes (n e %), incluindo o peso de `Miscellaneous`.
- Tamanho do texto em palavras: p5, p50, p95, máx.
- Idioma: % de documentos com caracteres não ASCII; 10 exemplos aleatórios (seed 42), truncados em 200 caracteres, em `planning/F1-revisao/f1_amostra_idioma.csv`.
- Dados pessoais no texto: contagem de acertos por regex de e-mail, telefone (sequência de 8+ dígitos) e URL.

**3.2 O texto já vem pré-processado?** O nome do arquivo (`processed_improved_v3`) sugere que sim. Meça: % de documentos com alguma letra maiúscula; % com pontuação; % que contêm ao menos uma palavra funcional comum do inglês (`the`, `is`, `to`, `and`, `of`, `a`, `in`). Coloque 5 exemplos aleatórios (seed 42) em `planning/F1-revisao/f1_amostra_texto.csv`.
- Se o texto estiver pré-processado (sem maiúsculas, sem pontuação ou sem palavras funcionais): **registre como achado**. Consequência pré-registrada: a comparação com LLM na F3 roda sobre texto degradado e precisa dizer isso; os testes de injeção na F5 são inseridos em texto que não é linguagem natural, e isso também precisa ser dito.

**3.3 Identificador.** `id` = índice da linha no CSV original (base 0), sem reordenar e sem remover linhas.

**3.4 Duplicados exatos.** Normalização: minúsculas; dígitos → `0`; caracteres não alfanuméricos → espaço; espaços colapsados. Conte: grupos de tamanho ≥ 2, tickets envolvidos, grupos com mais de um `Topic_group`.

**3.5 Quase-duplicados.**
- `TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)` sobre o texto normalizado.
- Similaridade de cosseno por blocos (`X[i:j] @ X.T`, blocos de 2.000 linhas); guarde só pares com cosseno ≥ 0,80 e i < j.
- Conte pares com cosseno ≥ 0,80, ≥ 0,90 e ≥ 0,95 (só para reporte).
- Arestas = duplicados exatos ∪ pares com cosseno ≥ **0,90**. Grupos = componentes conexos (`scipy.sparse.csgraph.connected_components`).
- Reporte: nº de grupos, % de tickets em grupos de tamanho ≥ 2, tamanho do maior grupo, nº de grupos e de tickets com conflito de rótulo.
- Até 30 exemplos de conflito em `planning/F1-revisao/f1_conflitos_rotulo.csv` (`group_id`, `id`, `Topic_group`, texto truncado em 300 caracteres), sorteados com seed 42.
- Se o maior grupo passar de 1% das linhas (encadeamento transitivo), **reporte e não mude o limiar**.

**3.6 Pares de fronteira (para o Gustavo calibrar o limiar a olho, opcional).** 20 pares aleatórios com cosseno em [0,85; 0,90) e 20 em [0,90; 0,95), seed 42, em `planning/F1-revisao/f1_pares_fronteira.csv` com `id_a`, `id_b`, `cosseno`, `mesmo_rotulo`, `texto_a`, `texto_b` (truncados em 300 caracteres).

**3.7 Holdout congelado.**
- Por grupo: `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)` com `y = Topic_group` e `groups = group_id`; a dobra 0 é o holdout.
- Aleatório: `train_test_split(test_size=0.2, stratify=y, random_state=42)`.
- `solution/outputs/f1_splits.csv` com `id`, `group_id`, `split_grupo` (treino/holdout), `split_aleatorio` (treino/holdout). **Sem a coluna de rótulo** (ela é reconstruída a partir do CSV bruto na leitura).
- Reporte: tamanho dos dois holdouts e % por classe em cada um × total.
- **Exposição a vazamento, sem modelo:** % dos tickets do holdout aleatório que têm um quase-duplicado (mesmo `group_id`) no treino aleatório. No holdout por grupo, o valor é 0% por construção (confirme).
- Este arquivo é o holdout oficial das fases seguintes. Não regenere nas próximas fases.

## Passo 4 — Planilha da revisão manual — `solution/f1_planilha_revisao.py` (≤ 5 min)

- Universo: holdout por grupo; um ticket por `group_id` (sorteado dentro do grupo, seed 42).
- Alocação: 5 por categoria (40) + 20 distribuídos proporcionalmente à prevalência no holdout (maiores restos); total 60; seed 42.
- Ordem das linhas embaralhada (seed 42), para que as categorias não apareçam em bloco.
- Saídas em `planning/F1-revisao/`:
  - `revisao_rotulos.csv` com `id`, `texto` (completo), `rotulo_original` (**vazio**), `meu_rotulo` (vazio), `ambiguo` (vazio), `observacao` (vazio);
  - `revisao_gabarito.csv` com `id`, `rotulo_original` (o Gustavo não abre este arquivo antes de terminar a revisão);
  - `revisao_pesos.csv` com `categoria`, `n_amostra`, `prevalencia_holdout` (para ponderar *e* na F3).
- **Variante cega: `[x] usar variante cega`** (decisão do Gustavo).
- Liste no report as 8 categorias válidas, exatamente como aparecem nos dados.
- **Nunca** preencha `meu_rotulo` nem sugira rótulo.

## Passo 4b — Adjudicação — `solution/f1_adjudicacao.py` (escrever agora; executar só quando o Gustavo pedir)

Dois modos, rodados pelo Gustavo depois da revisão cega:

1. `python solution/f1_adjudicacao.py preparar`
   - Lê `revisao_rotulos.csv` preenchida e `revisao_gabarito.csv`.
   - Valida: as 60 linhas têm `meu_rotulo` preenchido com uma das 8 categorias válidas; `ambiguo` ∈ {s, n}. Se falhar, lista as linhas com problema e para.
   - Grava `planning/F1-revisao/adjudicacao.csv` só com os tickets em que `meu_rotulo` ≠ original: `id`, `texto`, `meu_rotulo`, `rotulo_original`, `adjudicacao` (vazio), `observacao_adjudicacao` (vazio). Imprime quantos divergiram.
2. `python solution/f1_adjudicacao.py consolidar`
   - Valida: toda linha de `adjudicacao.csv` tem `adjudicacao` ∈ {`original errado`, `eu errei`, `ambíguo`}. Se falhar, lista e para.
   - Grava a planilha final de 60 linhas em `process-log/revisao_rotulos_adjudicada.csv` (`;`, `utf-8-sig`): `id`, `texto`, `rotulo_original`, `meu_rotulo`, `ambiguo`, `observacao`, `adjudicacao` (vazio onde não houve divergência), `observacao_adjudicacao`.
   - Imprime só contagens por desfecho e por categoria. **Não calcula *e* nem IC** (isso é F3).

Nesta fase, rode o modo `preparar` só contra uma planilha de teste gerada pelo próprio teste (ver passo 5), nunca contra a planilha real.

## Passo 5 — Testes — `solution/tests/test_f1.py`

- `f1_splits.csv`: `id` único e igual a `range(n)`; nenhum `group_id` aparece em treino e holdout de `split_grupo`; cada holdout tem entre 18% e 22% das linhas; as 8 classes aparecem nos dois holdouts.
- Planilha: 60 linhas; ≥ 5 por categoria; `group_id` únicos; todos os `id` pertencem ao holdout por grupo; `meu_rotulo` e `rotulo_original` inteiramente vazios; o gabarito tem os mesmos 60 `id`.
- Adjudicação, com uma planilha sintética de 3–4 linhas em diretório temporário (`tmp_path`): `preparar` recusa `meu_rotulo` vazio ou fora das categorias; lista só as divergências; `consolidar` recusa `adjudicacao` vazia ou fora dos 3 valores; a planilha final tem o mesmo número de linhas da revisão.

## Passo 6 — Report e process log

- `planning/F1-report.md` no formato da seção 8 do `CLAUDE.md`, mais uma seção **"O que os dados permitem e não permitem afirmar"**: duas listas, cada item citando o teste (T1…T8, 3.1…3.7) e o arquivo de saída.
- Acrescente a linha da F1 em `process-log/process-log.md`, com a coluna "Decisão minha" **vazia**.

## Critérios de aceite

- De um estado limpo, roda de ponta a ponta:
  ```
  python solution/f1_verificar_dados.py
  python solution/f1_auditoria_ds1.py
  python solution/f1_auditoria_ds2.py
  python solution/f1_planilha_revisao.py
  pytest solution/tests -q
  ```
- Todo número do report cita o script e o arquivo que o gerou.
- Nenhum texto de ticket, nome ou e-mail dentro do repositório.
- `git status --porcelain` só mostra caminhos dentro de `submissions/gustavo-covaleski/`.
- Nenhum commit.

## Não faça nesta fase

- Treinar classificador de tópico, medir acurácia ou vazamento com modelo, chamar LLM (tudo isso é F3).
- Remover duplicados ou corrigir rótulos. Só agrupar e contar.
- Mudar o limiar de 0,90, a seed ou a alocação porque o resultado "pareceu ruim". Reporte.
- Análise de segmento do DS1 além de T6.
- Instalar dependência nova sem registrar no report.
- `git add -A`, `git add .`, commit, push.
