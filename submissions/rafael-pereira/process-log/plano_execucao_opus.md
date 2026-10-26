# Plano de execução — gerado pelo planejador (Claude Opus 5.5, subagente somente leitura)

> Evidência equivalente ao "Plan Mode": este é o plano integral que o orquestrador recebeu do subagente Opus antes de qualquer código, salvo sem edição. Os executores (Haiku/Sonnet) receberam as seções correspondentes como especificação.

---

## Objetivo

Executar os blocos 0 a 6 do Challenge 003 em modo autônomo, sem nada mudar fora de `submissions/rafael-pereira/`, com um commit por bloco feito pelo orquestrador. O resultado esperado:
- **Motor Python** testado: `clean → features → score → explain → validate → build → docs`.
- **Página estática** `solution/app/` que funciona em `file://`, com `data.js` gerado, 4 listas, explicações, filtros e modo teste.
- **Briefs** por vendedor.
- **Documentação:** SCOPE, DATA_QUALITY, SCORING, MODEL_CARD, DECISIONS e README no template.
- **Process log** dos blocos 0 a 6, com screenshots e as duas revisões independentes.

Desenho técnico, validado num protótipo que rodei só para leitura via `python -c` (nenhum arquivo criado):
- **Probabilidade:** P(ganho nos 90 dias seguintes | Engaging, idade) por uma logística monotônica de "platô + queda", com joelho aprendido. Ela é estimada em fotos mensais de fim de mês (de 31/03/2017 até T−90), sem vazamento.
- **Score:** valor esperado = P × preço de tabela, e o score 0–100 é esse valor em escala log.
- **Listas:** limiares tirados do modelo. Foque vai até o joelho; Reative vai até o maior ciclo já ganho; Limpe fica acima disso; Qualifique é Prospecting.
- **Validação:** rolling-origin em 4 cortes (30/06, 31/07, 31/08 e 30/09/2017), comparada a 3 baselines. A métrica primária, pré-registrada, é a receita capturada no top 20%.

## Etapas

### Bloco comum (o orquestrador cola este texto no topo de TODA etapa)

```
PREÂMBULO POWERSHELL (cole no início de cada chamada; variáveis não persistem entre chamadas):
$PM="C:\Users\Info Mania\Documents\Predictive Analytics for CRM Sales Performance"; $PY="$PM\.venv\Scripts\python.exe"; $SUB="$PM\ai-master-challenge\submissions\rafael-pereira"; $SOL="$SUB\solution"
Comandos do projeto: Set-Location $SOL; & $PY -m <módulo>. PowerShell 5.1: sem &&; use ; e if ($?) {...}. Caminhos têm espaços: sempre entre aspas.
```
- **Python:** só o venv. Tem pandas 3.1, numpy 2.4, scipy 1.17, pytest 9.1 e playwright (Edge: `p.chromium.launch(channel="msedge", headless=True)`). Não tem scikit-learn. Não instale nada e não use a rede.
- **pandas 3:**
  - Copy-on-Write: proibida a atribuição encadeada (`df[c][m]=x`); use `.loc`.
  - O texto vem com dtype `str`; datas como `datetime64[us]`.
  - Fim de mês: `pd.date_range(..., freq="ME")`.
  - Não use `inplace`, `applymap` nem `fillna(method=)`.
  - Antes de `json.dump`, converta numpy para tipos Python e NaN/NaT para `None`.
- **Encoding:** todo `open`/`to_csv`/`read_csv` com `encoding="utf-8"`. Todo CLI começa com `sys.stdout.reconfigure(encoding="utf-8")`.
- **Determinismo:** nenhum `now()` ou timestamp em arquivo gerado; sementes fixas. Rodar o build duas vezes tem que gerar bytes idênticos.
- **NÃO TOCAR:**
  - nada fora de `$SUB` (exceção única, só na E12: `$PM\kit-lead-scorer\PR.md`);
  - `solution/data/raw/*`;
  - `process-log/00_fase0_exploracao.md` e `process-log/scripts/*.py`;
  - `CLAUDE.md`, `PROMPTS.md`, `GUIA.md`, `PROMPT_AUTONOMO.md`, `docs/briefing.md`;
  - logs `process-log/NN_bloco-N.md` de blocos anteriores.
  - Não rode git nem `gitw.py commit`: quem commita é o orquestrador. Pode rodar `& $PY "$PM\tools\gitw.py" status`.
- **Process log:** `process-log/NN_bloco-N.md` (NN com 2 dígitos), com as seções:
  - Objetivo
  - Executor (o nome real do seu modelo)
  - O que foi feito (comandos)
  - Resultados (números copiados de arquivos gerados, citando o arquivo)
  - Autoverificação do checkpoint
  - O que deu errado / iterações (erros reais, testes que falharam, hipóteses descartadas, antes/depois)
  - Decisões
  - Pendências

  Registre só o que aconteceu. Nunca atribua ao Rafael algo que não esteja em `00_fase0_exploracao.md`.
- **DECISIONS:** acrescente linhas em `docs/DECISIONS.md` no formato `| 2026-10-25 | Bloco N — <decisão> (decisão autônoma do Claude) | <alternativa descartada> | <motivo com número> |`. Nunca apague linhas.
- **Números:** todo número em docs ou na UI sai de arquivo gerado.
  - A partir do bloco 2, `python -m scorer.docs` reescreve os blocos `<!-- AUTO:nome -->…<!-- /AUTO:nome -->`, e `tests/test_docs_numbers.py` confere os números da prosa.
  - Antes de terminar, rode `& $PY -m scorer.docs` e `& $PY -m pytest` (cwd `$SOL`).
- **Idioma:** PT-BR em docs e UI. Nomes de colunas, contas e produtos ficam como no dataset.
- **Ao terminar,** responda ao orquestrador com:
  - os arquivos criados ou alterados;
  - os comandos rodados e o resultado;
  - os desvios do especificado.

---

### E1 — Bloco 0: setup, dados e reprodução da fase 0
- **Executor:** haiku
- **Depende de:** —
- **Arquivos:** criar as pastas `solution/{data/processed,scorer,tests,app,briefs,tools}` e `process-log/{chat-exports,screenshots,outputs}` (pasta vazia recebe `.gitkeep`); `solution/requirements.txt`, `solution/requirements-dev.txt`, `solution/pytest.ini`, `process-log/outputs/bloco0_*.txt`, `process-log/chat-exports/LEIA-ME.md`, `docs/DECISIONS.md`, `process-log/00_bloco-0.md`.
- **O que fazer:**
  1. **Leia** `$SUB\CLAUDE.md`, `docs\briefing.md` e `PROMPT_AUTONOMO.md`.
  2. **Pastas:** crie as listadas acima. Não crie arquivos de conteúdo além dos listados.
  3. **Contagem dos CSVs** (linhas de dados, sem cabeçalho), via `& $PY -c` com pandas: `sales_pipeline` 8800, `accounts` 85, `products` 7, `sales_teams` 35. Se algo divergir, PARE e reporte sem seguir.
  4. **Dependências:**
     - `requirements.txt`: `pandas>=2.2`, `numpy>=1.26`, `scipy>=1.11`, `pytest>=8` (uma por linha).
     - `requirements-dev.txt`: `playwright>=1.40`.
     - `pytest.ini`: `[pytest]` / `testpaths = tests` / `pythonpath = .` / `addopts = -q`.
     - Rode `& $PY -m pip install -r "$SOL\requirements.txt"` (tudo deve aparecer como "already satisfied"; o venv já existe fora do repo). Registre as versões com `& $PY -m pip freeze`.
  5. **Reproduza a fase 0** sem alterar os scripts. Para cada script: `& $PY -B "$SUB\process-log\scripts\eda.py" "$SOL\data\raw" | Out-File -Encoding utf8 "$SUB\process-log\outputs\bloco0_eda.txt"`. O mesmo vale para `eda2.py` e `snapshot.py`. O planejador já confirmou que os três rodam no pandas 3.1 com exit 0. Confira contra o briefing e liste as divergências (espera-se nenhuma):
     - win rate dos fechados 0.632;
     - 5 vendedores sem deals;
     - 1.291 Engaging acima de 138 dias (0.812), valor 3.198.664 de 3.892.229;
     - `pct_won_of_all` no snapshot de 30/09: 0.502 / 0.343 / 0.067 / 0 / 0; no de 30/06: 0.529 / 0.445 / 0.216 / 0.

     O `snapshot.py` trunca colunas na impressão; a coluna `pct_won_of_all` aparece. Para os números que os scripts não imprimem, rode um `& $PY -c` e salve em `outputs/bloco0_conferencia.txt`: linhas com product=="GTXPro" (esperado 1480) e a tabela completa do snapshot com `pd.set_option("display.width",250)` e `max_columns` 30.
  6. **`docs/DECISIONS.md`:** cabeçalho `| data | decisão | alternativa descartada | motivo |` e `|---|---|---|---|`.
     - As 7 decisões do CLAUDE.md, com data `2026-10-25 (fase 0)` e texto prefixado com "Fase 0 (kit do Rafael) —". As alternativas e os motivos saem do CLAUDE.md, do briefing e do 00_fase0; por exemplo, Streamlit foi descartado porque é o default do baseline.
     - As 6 decisões de setup do orquestrador, todas com o sufixo "(decisão autônoma do Claude)":
       1. gh indisponível → git clone do original, sem fork;
       2. git indisponível → dulwich no venv, em vez de instalar o Git no sistema (evita mudar o sistema e aceitar licenças sem o usuário);
       3. Playwright usando o Edge do sistema (channel msedge), em vez de baixar o Chromium;
       4. venv em `<pasta-mãe>\.venv`, fora do repo;
       5. PROMPT_AUTONOMO.md copiado junto com o kit, como evidência do pedido;
       6. sem /export de chat por bloco (sessão autônoma única); o process log narrativo substitui.
     - Mais uma linha atribuída a "pedido do Rafael em PROMPT_AUTONOMO.md": os checkpoints "espere meu ok" viram autoverificações registradas no log.
  7. **`chat-exports/LEIA-ME.md`:** explique em 3–5 linhas por que não há exports (decisão 6) e onde está o registro (`process-log/NN_bloco-N.md`, `DECISIONS.md`, histórico de commits).
  8. **`process-log/00_bloco-0.md`:** siga o template do bloco comum, incluindo a tabela "número do briefing × número reproduzido × arquivo".
- **Pronto quando:**
  - `Test-Path` é verdadeiro para todas as pastas e arquivos acima;
  - `(Select-String -Path "$SUB\docs\DECISIONS.md" -Pattern '^\| 2026').Count -ge 14`;
  - os 4 arquivos em `process-log\outputs` existem e não estão vazios;
  - `& $PY "$PM\tools\gitw.py" status` termina com "FORA da pasta da submissão: nada".
- **Commit:** "bloco 0: setup, dados e reprodução da exploração inicial"

---

### E2 — Bloco 1: escopo (SCOPE.md) e as 4 perguntas
- **Executor:** sonnet
- **Depende de:** E1
- **Arquivos:** `docs/SCOPE.md` (novo), `docs/DECISIONS.md` (append), `process-log/01_bloco-1.md` (novo).
- **O que fazer:**
  1. **Leia:**
     - `$SUB\CLAUDE.md`, `docs\briefing.md`, `PROMPTS.md` (bloco 1), `PROMPT_AUTONOMO.md`, `process-log\00_fase0_exploracao.md`;
     - do repo: `$PM\ai-master-challenge\README.md`, `challenges\build-003-lead-scorer\README.md`, `submission-guide.md`, `CONTRIBUTING.md`, `templates\submission-template.md`.
  2. **Responda você mesmo às 4 perguntas da seção 9 do briefing.** Para cada uma: pergunta, opções, decisão e justificativa com número do briefing. Adote as recomendações abaixo, a menos que encontre evidência contrária (e registre se encontrar):
     - **Q1 (4 listas ou lista única):** 4 listas, em abas. Cada uma mapeia uma ação diferente (avançar, reativar, encerrar no CRM, qualificar), e a dor é alocação de tempo. Uma lista única misturaria ações. Cada card mostra a etiqueta, e cada lista é ordenada pelo score.
     - **Q2 (visão padrão):** visão do vendedor, com o seletor "Quem é você?" no topo. A escolha fica salva na URL (`#vendedor=...`) e reabre igual. A visão do manager é a mesma tela filtrada por manager ou região, mais uma tabela "Carteira do time" só com contagens (sem taxa de vitória por vendedor; decisão 4 do CLAUDE.md).
     - **Q3 (o que vale mais no Foque):** maior valor esperado (chance × valor). A chance é praticamente estável enquanto o deal é jovem, então, entre os vivos, quem decide é o valor. A urgência aparece como "faltam X dias".
     - **Q4 (modo backtest):** sim, entra. Torna a validação visível para a Head de RevOps e é o diferencial mais forte, ao custo de cerca de 30 min.
  3. **`docs/SCOPE.md`** (no máximo 2 páginas, cerca de 1.100 palavras), com as 7 seções do PROMPTS bloco 1:
     1. **Problema:** as duas dores, na voz da Head de RevOps.
     2. **Para quem:** vendedor (segunda de manhã: "onde ponho meu tempo esta semana?") e manager (1:1 semanal: "o que do meu time está esfriando ou é lixo?").
     3. **O quê:** MVP priorizado (Foque, Reative, Limpe, Qualifique, explicação por deal, filtros vendedor/manager/região, brief por vendedor, modo teste).
        - Fora do escopo: integração ou escrita no CRM; login; forecast financeiro; avaliação de desempenho de vendedores; score para Prospecting; tempo real; preço/desconto; notificações.
        - Tratamento combinado, que o bloco 2 implementa: Prospecting não tem data → lista Qualifique, sem score, ordenada por preço de tabela. Deal sem conta → "Conta não informada", nunca penalizado, alerta de higiene de CRM.
     4. **Como:** arquitetura em 5 linhas (motor Python puro e testado → `data.js` → HTML/CSS/JS sem build, `file://` e GitHub Pages) e a tese "frescor > atributos", com os números do briefing.
     5. **Por quê assim:** alternativas descartadas (Streamlit, ML black-box, score por atributos), cada uma com motivo.
     6. **Critérios de sucesso:** cada critério do README do challenge vira uma verificação concreta e checável. Exemplos:
        - "funciona": `python -m pytest` passa, `python -m scorer.build` regenera tudo e `index.html` abre em `file://` sem erro de console (verificado por script Playwright no bloco 4);
        - "vendedor encontra seus 3 deals de Foque em ≤ 2 interações a partir da abertura";
        - "o score supera ordenar por valor, ordenar por recência e aleatório na receita capturada pelo top 20%, em todos os cortes de backtest";
        - "cada card tem de 2 a 4 frases sem jargão".
     7. **Riscos e premissas.**

     Use só números que já estão no briefing ou no CLAUDE.md (no bloco 2 eles serão conferidos contra `facts.json`).
  4. **DECISIONS:** 4 linhas, uma por pergunta, mais as linhas da lista "fora do escopo" e dos critérios de sucesso.
  5. **`process-log/01_bloco-1.md`:** as 4 perguntas com recomendação, resposta e justificativa; a autoverificação (o PROMPTS mandava esperar o Rafael; aqui o Claude decidiu sozinho, conforme o PROMPT_AUTONOMO); e o que ficou fora do escopo.
- **Pronto quando:**
  - `docs\SCOPE.md` existe, com 7 títulos `##` numerados;
  - `((Get-Content "$SUB\docs\SCOPE.md" -Raw) -split '\s+').Count -le 1300`;
  - `01_bloco-1.md` contém "Q1", "Q2", "Q3" e "Q4";
  - DECISIONS ganhou 4 linhas ou mais "Bloco 1";
  - `gitw.py status` mostra "nada" fora da pasta.
- **Commit:** "bloco 1: escopo"

---

### E3 — Bloco 2: curadoria, investigações 2a/2b/2c e infraestrutura de números
- **Executor:** sonnet
- **Depende de:** E2
- **Arquivos:**
  - `solution/scorer/{__init__.py, config.py, fmt.py, clean.py, facts.py, docs.py}`
  - `solution/tests/{test_clean.py, test_docs_numbers.py}`
  - `solution/data/processed/{deals.csv, facts.json}`
  - `docs/DATA_QUALITY.md`, `docs/SCOPE.md` (só para ajustar números, se o teste reclamar), `docs/DECISIONS.md`, `process-log/02_bloco-2.md`
- **O que fazer:**
  1. **Leia** CLAUDE.md, briefing, SCOPE.md, PROMPTS (bloco 2) e `process-log/scripts/*.py` (referência de cálculo; não altere).
  2. **`config.py`**, com constantes e caminhos baseados em `Path(__file__)`:
     - `DEFAULT_REFERENCE_DATE="2017-12-31"`, `PRODUCT_NAME_MAP={"GTXPro":"GTX Pro"}`, `SECTOR_MAP={"technolgy":"technology"}`;
     - `HORIZON_DAYS=90`, `FIRST_SNAPSHOT="2017-03-31"`, `SENSITIVITY_FIRST_SNAPSHOT="2017-02-28"`;
     - `BACKTEST_CUTS=["2017-06-30","2017-07-31","2017-08-31","2017-09-30"]`, `UI_BACKTEST_SNAPSHOTS=["2017-06-30","2017-09-30"]`;
     - `TOP_FRAC=0.20`, `RANDOM_SEEDS=200`, `BOOTSTRAP_REPS=1000`, `KNOT_GRID=range(0,181,5)`;
     - `ALLOWED_CONSTANTS`: lista de números estruturais permitidos na prosa (90, 20, 200, 1000, 180, 100, …), cada um com comentário.
  3. **`fmt.py`** (formato PT-BR): `fmt_int(1291)→"1.291"`, `fmt_pct(0.632,1)→"63,2%"`, `fmt_usd(4821)→"US$ 4.821"`, `fmt_usd_compact(3198664)→"US$ 3,2 mi"` (e "US$ 393 mil"), `fmt_date("2017-12-31")→"31/12/2017"`.
  4. **`clean.py`** (funções puras, que nunca modificam a entrada):
     - `load_raw(raw_dir)`;
     - `normalize_products(pipeline, catalog)` usa o mapa e faz assert de que todo produto existe no catálogo;
     - `normalize_sectors(accounts)`;
     - `join_all(...)`: left joins pipeline ← products, sales_teams, accounts; assert de len == 8800, nenhum `sales_price` nulo, nenhum manager nulo;
     - `add_derived(df, reference_date)`:
       - `age_days = (reference_date − engage_date).days` só para deals abertos com `engage_date`; NaN no resto;
       - `cycle_days` só para Won/Lost;
       - `has_account`;
       - `is_open` (Engaging ou Prospecting);
       - `account_display` = account ou "Conta não informada".
     - CLI `python -m scorer.clean [--reference-date 2017-12-31]` grava `data/processed/deals.csv` (utf-8) e chama `facts.write_facts()`.
  5. **`facts.py`** gera `data/processed/facts.json` com TODOS os números de fase 0 que o briefing, o CLAUDE.md e o SCOPE citam:
     - contagens por estágio, win rate, linhas GTXPro (1.480), setor com erro;
     - sem conta (1.425 = 1.088 Engaging + 337 Prospecting; 0 entre os fechados);
     - 500 Prospecting sem data;
     - vendedores: 35 / 30 / 5;
     - ciclo máximo 138; medianas dos ciclos ganho/perdido; perdidos em até 14 dias;
     - p-valores qui-quadrado de produto e vendedor; correlação de vendedor H1×H2; AUCs numéricas;
     - faixas de idade em 31/12 (110 / 188 / 1.291; US$ 3,2 mi de US$ 3,9 mi);
     - valor de Prospecting; concentração de receita por produto;
     - tabelas dos snapshots de 30/06 e 30/09;
     - as evidências 2a, 2b e 2c abaixo.

     Estrutura do JSON: chaves descritivas em snake_case, valores numéricos crus (frações como 0.632).
  6. **Investigações, com critério de decisão pré-definido** (registre números e decisão no DATA_QUALITY, no log e no DECISIONS):

     **2a) Win rate de 82% em 2017-Q1.**
     - Calcule:
       - primeira e última `close_date`;
       - por mês de fechamento: n, win rate e mediana do ciclo (esperado: Mar 82,1%, Abr 48,6%, Mai 54,4%, Jun 82,8%, Jul 49,1%, Ago 56,8%, Set 79,2%, Out 49,3%, Nov 52,9%, Dez 78,5%);
       - win rate por trimestre de fechamento;
       - por coorte mensal de engajamento: n fechados, win rate e ciclo mínimo (esperado: out–fev com mínimos 123/96/63/36/5, sinal de truncamento à esquerda);
       - crosstab trimestre de engajamento × trimestre de fechamento (esperado: só Q ou Q+1; conte as exceções).
     - **Critério:** é artefato de recorte se valerem as três condições:
       - (i) o Q1 só tem fechamentos em março;
       - (ii) o win rate de março está a ±5 pp da média de jun/set/dez;
       - (iii) as coortes engajadas antes de 01/03/2017 não têm ciclos curtos (truncamento).
     - **Decisão esperada, se o critério se confirmar:**
       - (a) win rate por trimestre só aparece com ressalva;
       - (b) as fotos de treino do bloco 3 começam em 2017-03-31, a primeira de fim de mês dentro do período observado de fechamentos. Os deals fechados em março/2017 não entram como observação de treino. Os engajados antes e ainda abertos em 31/03 entram, porque a população aberta numa data dentro do período observado é completa;
       - (c) a foto de 28/02 entra só como sensibilidade no bloco 3, porque depende da hipótese não verificável de que o recorte removeu exatamente os fechados antes de 01/03;
       - (d) os artefatos do gerador (regra Q/Q+1, fechamentos rápidos no 1º mês do trimestre, teto de 138 dias) são documentados e NÃO são explorados pelo score.
     - **Transparência obrigatória no log:** "o planejador (Opus) viu num protótipo que começar em 28/02 piora o modelo do corte de 30/06; a regra foi justificada a priori, mas escolhida depois de ver isso, por isso 28/02 é reportado como sensibilidade."

     **2b) Vendedores sem deals.**
     - Calcule: 35 no cadastro; 30 com algum deal; quantos têm deals ABERTOS em 31/12 (protótipo: 27); nomes, manager e região dos 5 sem deals (esperado: um por time, exceto o time de Dustin Brinkmann); quais 3 têm só deals fechados.
     - **Critério:** zero deals em qualquer estágio significa "cadastro sem pipeline".
     - **Decisão:**
       - aparecem no filtro de vendedor, agrupados sob o manager, com o sufixo "(sem deals no CRM)" e estado vazio explicativo;
       - aparecem na "Carteira do time" com zeros e alerta;
       - não recebem brief; o índice de briefs os lista.
       - Os 3 só com fechados recebem "sem deals abertos".

     **2c) `close_value` / preço de tabela.**
     - Calcule: para os Won, média, mediana, p5, p95, mín e máx da razão (protótipo: média 0,996, mín 0,657, máx 1,342), no geral, por produto e por trimestre de fechamento; todos os Lost com `close_value` = 0; nenhum Won com 0.
     - **Critério:** média por produto em [0,95; 1,05] e variação entre trimestres ≤ 3 pp.
     - **Decisão:** o valor do deal aberto é `sales_price`; `close_value` só serve como desfecho no backtest.

     **Vazamento, registrar já:** todos os 1.425 sem conta estão abertos no fim. "Sem conta" equivale a "nunca fechou", então `has_account`, ou qualquer categoria "desconhecido" de setor ou porte, é proibido como feature.
  7. **Testes** (`test_clean.py`):
     - o join mantém 8.800 linhas;
     - não sobra "GTXPro" nem "technolgy";
     - `age_days` correto num Engaging escolhido do CSV: o esperado é calculado no teste com `datetime.date` a partir da string crua;
     - nenhum Won com `close_value` 0 e todos os Lost com 0;
     - Prospecting sem `engage_date`;
     - a função não altera o DataFrame de entrada (compare antes e depois).
  8. **`docs.py`:**
     - `render_blocks()` → dict nome→markdown (a partir de `facts.json`; no bloco 3 ganha `backtest_metrics.json`);
     - `inject(path)` substitui o conteúdo entre `<!-- AUTO:x -->` e `<!-- /AUTO:x -->` e dá erro em marcador sem renderizador;
     - CLI `python -m scorer.docs` (escreve) e `--check` (exit 1 se algum doc estiver desatualizado).
     - Docs cobertos: `docs/DATA_QUALITY.md`, `docs/SCOPE.md` e, depois, SCORING, MODEL_CARD e `README.md`. Fora da cobertura: briefing, DECISIONS e process-log.
  9. **`test_docs_numbers.py`:**
     - **(a)** os blocos AUTO batem com o re-render.
     - **(b)** fora dos blocos AUTO, removidos code fences, código inline, URLs, datas (dd/mm/aaaa, aaaa-mm-dd, mmm/aaaa) e anos 2016–2026, extraia os tokens:
       - `US\$\s?[\d.,]+(\s?(mi|mil))?`;
       - `[\d.,]+\s?%`;
       - decimais com vírgula;
       - inteiros ≥ 100 ou com ponto de milhar.
     - Converta cada token de PT-BR para float com a precisão exibida. O token é aceito se algum valor de `facts.json` (e depois de `backtest_metrics.json`), ou de `ALLOWED_CONSTANTS`, arredondado para a mesma precisão, bater com ele. Frações também valem ×100 para porcentagens. A falha lista o arquivo, a linha e o token.
     - Se o SCOPE (bloco 1) citar um número ausente, acrescente o cálculo em `facts.py` (se for fato real da fase 0) ou corrija o texto. Registre no log.
  10. **`docs/DATA_QUALITY.md`:** tabela "problema → evidência (número) → tratamento → impacto". Linhas:
      - GTXPro;
      - technolgy;
      - sem conta, com o risco de vazamento;
      - Prospecting sem data;
      - vendedores sem deals;
      - 82% no Q1;
      - `close_value` × tabela;
      - teto de 138 dias e regra Q/Q+1;
      - fechamentos rápidos no 1º mês do trimestre;
      - zumbis;
      - truncamento à esquerda.

      As tabelas de evidência dos itens 2a, 2b e 2c ficam em blocos AUTO (`dq-meses`, `dq-coortes`, `dq-trimestres`, `dq-razao-preco`, `dq-vendedores`).
  11. **Log** `02_bloco-2.md`, com a autoverificação: resumo 2a/2b/2c, critério × número × decisão. **DECISIONS:** linhas 2a, 2b, 2c, artefatos não explorados e a proibição de `has_account`.
- **Pronto quando:**
  - `Set-Location $SOL; & $PY -m scorer.clean; & $PY -m scorer.docs; & $PY -m pytest; & $PY -m scorer.docs --check` com exit 0;
  - `(Import-Csv "$SOL\data\processed\deals.csv").Count -eq 8800`;
  - `facts.json` contém as chaves das evidências 2a, 2b e 2c;
  - `gitw.py status` mostra "nada" fora da pasta.
- **Commit:** "bloco 2: curadoria de dados"

---

### E4 — Bloco 3a: checagem de vazamento, features, score e explicação
- **Executor:** sonnet
- **Depende de:** E3
- **Arquivos:**
  - `solution/scorer/{features.py, score.py, explain.py}`
  - `solution/tests/{test_features.py, test_score.py, test_explain.py}`
  - `process-log/03_bloco-3.md` (criar e começar)
- **O que fazer:**
  1. **Leia** CLAUDE.md, briefing, SCOPE, DATA_QUALITY, PROMPTS (bloco 3) e `facts.json`.
  2. **Antes de escrever qualquer código,** crie `03_bloco-3.md` com:

     **(a)** a seção "Planejamento (Opus) — protótipo exploratório". O texto é o seguinte (ajuste a forma, não o conteúdo):
     > "Durante o planejamento, o Claude Opus (somente leitura) rodou protótipos descartáveis via `python -c`, sem criar arquivos. (1) Uma logística segmentada sem restrição, treinada a partir de 28/02, gerou para o corte de 30/06 uma curva que SOBE com a idade até 90 dias (não monotônica), o que motivou a restrição monotônica e a regra de fotos ≥ 31/03. Essa regra foi adotada depois de ver o resultado, por isso 28/02 é reportado como sensibilidade. (2) Ordenar por recência é um baseline forte em AUC nos cortes de fim de trimestre. (3) Deals fecham no trimestre do engajamento ou no seguinte (artefato do gerador). (4) Entre 0 e 90 dias, a taxa de ganho em 90 dias fica estável, perto de 40%, e cai depois disso."

     **(b)** a seção "Checagem de vazamento — escrita antes do código". Para cada risco, a guarda e o teste:
     1. estágio final usado como estado em T → `as_of(T)` reconstrói o estado a partir das datas;
     2. rótulo de treino com evento posterior a T → só fotos S com S+H ≤ T (assert e teste);
     3. conta ausente ↔ nunca fechou → `has_account` e a categoria "desconhecido" proibidos; teste de atributos de conta só no subconjunto com conta;
     4. `close_value` como valor → só `sales_price`;
     5. parâmetros (joelho, P_fresh, a_limpe, escala do score) ajustados com dados de depois de T → tudo ajustado por corte, a partir de `as_of(T)`;
     6. explicações e números do modo teste → vêm do modelo do corte;
     7. Prospecting no passado não é reconstruível → fora do backtest (limite de cobertura, não vazamento);
     8. hiperparâmetros (H, primeira foto, grade de joelhos) escolhidos conhecendo os dados → divulgado, com sensibilidade reportada;
     9. preço de catálogo é estático → aceitável, mas documentado.
  3. **`features.py`:**
     - `month_ends(start, end)` usa `pd.date_range(start, end, freq="ME")`.
     - `as_of(deals, T)`:
       - mantém só linhas com `engage_date` não nula e ≤ T (Prospecting fica de fora);
       - para quem não fechou até T (`close_date` nula ou > T): `deal_stage="Engaging"`, `close_date=NaT`, `close_value=NaN`.
     - `open_at(view, S)`: `engage_date ≤ S` e (`close_date` NaT ou > S), mais a coluna `age_days=(S−engage_date).days` (int).
     - `training_set(view_T, T, horizon_days, first_snapshot)`:
       - para cada S em `month_ends(first_snapshot, T)` com S+H ≤ T, pega `open_at(view_T, S)`;
       - `y = (deal_stage=="Won") & (close_date ≤ S+H)`;
       - colunas: `snapshot_date`, `opportunity_id`, `age_days`, `product`, `sales_price`, `regional_office`, `sector`, `employees`, `has_account` (só para diagnóstico), `y`;
       - `assert max(S)+H ≤ T`.
  4. **`score.py`.**

     Logística estável: `fit_logistic(X, y, l2=0.0, bounds=None)` com `scipy.optimize.minimize(method="L-BFGS-B")`.
     - NLL = `sum(logaddexp(0, Xb)) − y·Xb + l2/2·||b[1:]||²`
     - gradiente analítico: `Xᵀ(σ(Xb)−y) + l2·[0, b[1:]]`

     Curva de idade, "platô + queda":
     ```
     logit P(a) = b0 + b1 · max(0, a − k) / 30,   com b1 ≤ 0
     ```
     - Para cada k em `KNOT_GRID`, ajuste (b0, b1) com o limite b1 ∈ (−∞, 0]. Escolha o k de menor NLL; em empate, o menor k.
     - k = 0 reduz o modelo a uma logística linear na idade.
     - Não há corte duro: P > 0 para toda idade.

     `@dataclass(frozen=True) AgeCurve`: `knot_days`, `intercept`, `slope_per_30d`, `base_rate`, `train_rows`, `train_snapshots`.
     - `p_win(age)`;
     - `p_fresh = σ(b0)`;
     - `halving_days = 30·(logit(p_fresh/2) − b0)/b1` (dias depois do joelho até a chance cair à metade).

     `fit_model(deals, T, cfg) → ScoreModel(curve, limpe_after_days, price_min, price_max, as_of_date)`:
     - `limpe_after_days` = maior `cycle_days` entre os Won com `close_date ≤ T` na `as_of(T)` (se for menor que k, use k);
     - `price_min` e `price_max` vêm do catálogo `products.csv`.

     `score_deals(deals, T, model, include_prospecting)`, para os Engaging em `open_at(as_of(T), T)`:
     - `p_win`;
     - `expected_value = p_win × sales_price`;
     - `score = round(100·ln(1+EV/EV_min)/ln(1+EV_max/EV_min))`, limitado a [0, 100], com `EV_min = p_fresh·price_min` e `EV_max = p_fresh·price_max`;
     - `category`: Foque se idade ≤ k; Reative se k < idade ≤ limpe_after_days; Limpe acima disso;
     - `days_to_knot`, `days_to_limpe`.

     Prospecting só entra quando `include_prospecting` (data de referência = fim dos dados): `category="Qualifique"`, `p_win`, `EV` e `score` nulos.

     Ordenação (`order_for_list`, só para UI e briefs; as métricas usam o EV):
     - Foque e Reative: EV desc → menos dias até o próximo limiar → `opportunity_id`;
     - Limpe: `sales_price` desc → idade desc;
     - Qualifique: `sales_price` desc.

     O vendedor não entra em nenhuma função.
  5. **`explain.py`.** `explain_deal(row, model) → list[str]`, de 2 a 4 frases curtas em PT-BR, números via `fmt.py`, sem a palavra "nan".
     - **Foque:**
       - "Aberto há {idade} dias. No histórico, deals em Engaging com essa idade foram ganhos em {p}% dos casos nos 90 dias seguintes."
       - "{produto}: valor de tabela {US$}; valor esperado {US$ EV}."
       - "Ainda na janela boa: a chance só começa a cair depois de {k} dias (faltam {k−idade})."
     - **Reative:**
       - "Aberto há {idade} dias: a chance de ganho em 90 dias caiu de {p_fresh}% (deal novo) para {p}%."
       - a frase de valor;
       - "Nenhum deal foi ganho depois de {a} dias aberto — faltam {a−idade} dias. Fale com o cliente esta semana."
     - **Limpe:**
       - "Aberto há {idade} dias — mais do que qualquer deal já ganho no histórico ({a} dias)."
       - "Provável deal parado ou CRM desatualizado: confirme com o cliente e encerre ou atualize."
       - "São {US$ tabela} inflando o pipeline."
     - **Qualifique:**
       - "Ainda em Prospecting, sem data de engajamento: o histórico não permite estimar a chance."
       - "{produto}: valor de tabela {US$}. Qualifique (marque a primeira conversa) ou descarte."
     - **Sem conta:** acrescente "Conta não informada no CRM — preencha; isso não muda o score."

     `how_it_works(model, headline_metrics) → 5 linhas`:
     1. a fonte (número de fotos e período);
     2. o platô de ~p_fresh% até k dias e a meia-vida de h dias depois;
     3. a fórmula do valor esperado e a escala 0–100, com a razão entre o maior e o menor preço;
     4. as listas com os limiares;
     5. o resultado do teste no passado (preenchido no bloco 3b com a média dos cortes) e "vendedor não entra no score".
  6. **Testes:**
     - **`test_features.py`:**
       - `as_of` não tem nenhuma `close_date > T` nem estágio Won/Lost com fechamento depois de T;
       - `training_set` respeita S+H ≤ T;
       - **TESTE DE MUTAÇÃO DO FUTURO:** copie os deals e, para todo `close_date > T` (T = 2017-06-30), sorteie Won/Lost, `close_value` e `close_date` em (T, 2017-12-31] com semente fixa; embaralhe produto e vendedor dos engajados depois de T; apague `account` de deals aleatórios fechados depois de T. Então `fit_model` e os scores dos abertos em T ficam IDÊNTICOS aos do original.
     - **`test_score.py`:**
       - P é monotônica não crescente de 0 a 500 dias, com P(400) > 0;
       - o ajuste recupera o joelho (±10 dias) em dados sintéticos com k=60;
       - fronteiras das categorias;
       - score em [0, 100]; deal novo do produto mais caro = 100; score monotônico no EV;
       - **justiça:** permutar `sales_agent` não muda nenhum score;
       - Prospecting fica com score nulo e categoria Qualifique.
     - **`test_explain.py`:** de 2 a 4 frases; o percentual citado é igual a `round(100·p)`; sem "nan"; texto de conta ausente presente quando aplicável.
  7. **Sanidade, contra o protótipo do planejador.** Use para achar bug, não como meta. Divergência relevante (joelho com diferença maior que 5, contagens com diferença maior que 2%) exige investigar o código antes de qualquer outra coisa:
     - **modelo em 2017-12-31:** 7 fotos (31/03 a 30/09), 13.100 linhas, k=95, b0≈−0,41 (P_fresh≈0,40), b1≈−2,59, limpe=138;
     - **hoje:** Foque 126, Reative 172, Limpe 1.291 (tabela US$ 3.198.664), Qualifique 500;
     - **joelho e linhas de treino por corte:** 30/06 → k=70 (1.330 linhas); 31/07 → 100 (2.948); 31/08 → 95 (4.483); 30/09 → 90 (6.169).
  8. **Registre no log** os erros e os testes que falharam de verdade, com o antes e o depois.
- **Pronto quando:**
  - `Set-Location $SOL; & $PY -m pytest` com exit 0;
  - `03_bloco-3.md` tem as seções "Planejamento (Opus)" e "Checagem de vazamento";
  - `& $PY -c "from scorer.score import *"` funciona.
- **Commit:** — (o bloco 3 é commitado depois da E5)

---

### E5 — Bloco 3b: validação, backtest, SCORING.md e ajuste pré-registrado
- **Executor:** sonnet
- **Depende de:** E4
- **Arquivos:**
  - `solution/scorer/validate.py`, `solution/scorer/docs.py` (estender), `solution/scorer/explain.py` (linha 5 do `how_it_works`)
  - `solution/tests/test_validate.py`
  - `solution/data/processed/{backtest_metrics.json, backtest_tables.md}`
  - `docs/SCORING.md`, `docs/DECISIONS.md`, `process-log/03_bloco-3.md` (completar)
- **O que fazer:**
  1. **Leia** `03_bloco-3.md`, `score.py`, `features.py` e DATA_QUALITY.
  2. **Métricas**, testadas com dados de brinquedo:
     - `auc(score, y)`: Mann-Whitney com rank médio (`scipy.stats.rankdata`).
     - `top_share(score, gain, frac=0.2)`: fração de `gain` no top 20% por contagem, com tratamento fracionário de empates (valor esperado sob desempate aleatório). Algoritmo:
       - ordene o score de forma decrescente;
       - agrupe os valores iguais;
       - inclua a fração `(K − acumulado)/tamanho` do grupo que cruza `K = frac·n`.
     - "Captura de ganhos" é `top_share` com `gain = y`; "receita capturada" é `top_share` com `gain = close_value` dos Won.
  3. **`evaluate_cut(deals, T)`**, para cada T em `BACKTEST_CUTS`:
     - modelo = `fit_model(deals, T)`;
     - população = Engaging em `open_at(as_of(T), T)`, incluindo zumbis;
     - desfecho vindo dos dados completos: `y` = Won (até 31/12/2017), `gain = close_value`, `y_H = Won & close_date ≤ T+90`.

     Métodos:
     - **score** = EV;
     - **p_only** = P, como diagnóstico (tem empates no platô, então a AUC dele é menor ou igual à da recência);
     - **valor** = `sales_price`;
     - **recencia** = −idade;
     - **aleatorio** = média de 200 sementes (0 a 199), mais o p5 e o p95 da receita no top 20%.

     Calcule por corte:
     - AUC, captura no top 20% e receita no top 20% de cada método;
     - Brier do P × Brier da constante (taxa base de treino), sobre `y_H`;
     - tabela de categorias: n, % ganhos, receita ganha, % da receita e valor de tabela;
     - bootstrap com 1.000 reamostragens (semente 0) dos deals do corte, para as diferenças de receita no top 20% score−valor e score−recência (IC 2,5% a 97,5%);
     - sensibilidade "só resolvidos" (deals fechados até 31/12): AUC e receita no top 20%;
     - sensibilidade "primeira foto 28/02" (mesmas métricas do score);
     - auditoria "e se houvesse vazamento?": (i) modelo ajustado com `as_of(2017-12-31)` e avaliado no corte, rotulado VAZADO e nunca reportado como resultado; (ii) AUC de `has_account` sozinho no corte, mostrando por que é proibido.
  4. **Teste de atributos.** Um atributo por vez sobre o modelo de idade, com o joelho fixo no valor da curva só de idade. One-hot com referência e L2 = 1,0 nos coeficientes do atributo. Atributos:
     - **produto** e **região** (`regional_office`): todos os deals;
     - **setor** e **porte** (tercil de `employees` calculado na tabela `accounts`): só no subconjunto com conta, tanto no treino quanto na avaliação, comparando com a curva só de idade ajustada no MESMO subconjunto.
     - Métricas por corte: Δ log-loss em `y_H` e Δ receita no top 20% (P_attr × preço).
     - **Regra pré-registrada:** o atributo entra só se melhorar o log-loss em TODOS os cortes e não piorar a receita no top 20% em nenhum. O vendedor NÃO é testado (decisão 4).
     - Esperado: nenhum entra.
  5. **Critério "bater os baselines" (pré-registrado; copie para SCORING e log ANTES de rodar):**
     - **Métrica primária:** receita capturada no top 20%. O score precisa ser maior que valor, maior que recência, e maior que a média e o p95 dos aleatórios, em TODOS os 4 cortes.
     - Diferença ≤ 0,01 conta como empate, e empate não bate.
     - AUC, captura de ganhos e Brier são reportados, mas não decidem.
     - **ANTECIPE:** P é monotônica na idade, então P sozinha nunca ordena melhor que a recência (com empates no platô, é pior). O score não é P sozinha. O ganho real aparece na receita: o score troca um pouco de taxa de acerto por mais receita. Reporte sem rodeio que a recência ganha em AUC e em captura de ganhos nos cortes de fim de trimestre, porque o gerador encerra deals no fim do trimestre seguinte. Reporte também que ela despenca em 31/07.
     - **Ajuste único, pré-definido, só se o critério falhar:** troque a curva "platô + queda" por faixas de 15 dias de idade, com taxa por faixa suavizada por pseudo-contagem α=20 rumo à taxa média de treino, forçada a não crescer com PAVA (pesos = n+α) e interpolada linearmente entre os pontos médios. Mesma janela, mesmo H, nada mais muda. Rode de novo.
     - Se ainda falhar: mantenha o modelo de melhor média na métrica primária e documente a falha com números, sem novas tentativas.
     - Corrigir bug (código que não faz o que o SCORING descreve) não conta como ajuste, mas deve ser logado com antes e depois.
     - Valores esperados pelo protótipo, para sanidade:

       | Corte | Receita top 20% — score | valor | recência | AUC score | AUC recência |
       |---|---|---|---|---|---|
       | 30/06 | ≈0,61 | ≈0,49 | ≈0,28 | ≈0,66 | ≈0,73 |
       | 31/07 | ≈0,58 | ≈0,49 | ≈0,13 | ≈0,64 | ≈0,58 |
       | 31/08 | ≈0,61 | ≈0,48 | ≈0,32 | ≈0,63 | ≈0,66 |
       | 30/09 | ≈0,65 | ≈0,47 | ≈0,47 | ≈0,65 | ≈0,83 |

       Aleatório ≈ 0,20 em todos os cortes. Limpe teve 0% de ganhos em todos os cortes; Foque, entre 33% e 49%.
  6. **`run_backtest()`** grava `data/processed/backtest_metrics.json`:
     - `config`;
     - `criterion`: regra, `passed`, `adjustment_applied`;
     - `cuts[]`: modelo do corte, métodos, Brier, bootstrap, categorias, resolvidos;
     - `media_cortes`;
     - `sensibilidade_2017-02-28`;
     - `auditoria`;
     - `atributos[]`;
     - `hoje`: modelo em 2017-12-31 e categorias com n, valor de tabela e valor esperado, incluindo Qualifique.

     Também grava `backtest_tables.md`. CLI: `python -m scorer.validate` imprime a tabela principal e PASSOU/FALHOU.
  7. **`explain.how_it_works`, linha 5:** "Testado no passado em {n} datas: o top 20% do score capturou {r}% da receita ganha depois, contra {v}% ordenando por valor e {rec}% pelos mais recentes. Vendedor não entra no score." Números da média dos cortes.
  8. **`docs/SCORING.md`.** Seções:
     1. Resumo
     2. Fórmula: P(idade), EV, escala do score e categorias, com os parâmetros de hoje em AUTO
     3. Por que assim: H=90 = 1 trimestre (toda janela contém exatamente 1 mês de fim de trimestre, o que neutraliza a sazonalidade 49%→55%→80%); monotonicidade; primeira foto; comparação com as faixas fixas do briefing (110/188/1.291 × joelho e limite aprendidos)
     4. Checagem de vazamento, com os testes
     5. Desenho do backtest e censura: os ainda abertos em 31/12 contam como "não ganho até 31/12", e a sensibilidade "resolvidos" mostra que a vantagem vem de identificar zumbis
     6. Resultados: tabela principal (corte × método: AUC | ganhos capturados no top 20% | receita capturada no top 20%), média, categorias, calibração e bootstrap
     7. Sensibilidades e auditoria
     8. Atributos testados e descartados
     9. Critério pré-registrado e se houve ajuste
     10. O que não funcionou e por quê: a curva não monotônica do protótipo; P < recência em AUC; Reative fraco nos fins de trimestre; corte de 30/06 com 1 foto só; o que mais falhou de verdade
     11. Limitações

     Todas as tabelas em AUTO: `scoring-hoje`, `scoring-modelos`, `scoring-backtest`, `scoring-media`, `scoring-categorias`, `scoring-calibracao`, `scoring-bootstrap`, `scoring-sensibilidade`, `scoring-auditoria`, `scoring-atributos`. Estenda `test_docs_numbers` para cobrir o SCORING e `backtest_metrics.json`.
  9. **`test_validate.py`:**
     - `auc` perfeita = 1, invertida = 0, tudo empatado = 0,5;
     - `top_share` com tudo empatado = 0,2;
     - JSON com 4 cortes e todas as chaves;
     - a função de critério reproduz `passed`.
  10. **Feche o `03_bloco-3.md`:** autoverificação (a tabela do backtest copiada do `backtest_tables.md`), PASSOU/FALHOU, o ajuste (se houve), o que falhou de verdade, e as perguntas de auditoria respondidas com números (vazamento, `has_account`, 28/02, resolvidos). **DECISIONS:** H=90; primeira foto; curva; grade de joelhos; limite Limpe; escala log; métrica primária; ajuste único; atributos descartados; tratamento da censura.
- **Pronto quando:**
  - `Set-Location $SOL; & $PY -m scorer.validate; & $PY -m scorer.docs; & $PY -m pytest; & $PY -m scorer.docs --check` com exit 0;
  - `backtest_metrics.json` tem 4 entradas em `cuts` e a chave `criterion.passed`;
  - SCORING.md tem a tabela com os 3 baselines nos 4 cortes;
  - `gitw.py status` mostra "nada" fora da pasta.
- **Commit:** "bloco 3: scoring e validação"

---

### E6 — Bloco 4a: build, `data.js`, interface e briefs
- **Executor:** sonnet
- **Depende de:** E5
- **Arquivos:**
  - `solution/scorer/build.py`
  - `solution/app/{index.html, style.css, app.js, data.js (gerado)}`
  - `solution/briefs/*.md` (gerados)
  - `solution/data/processed/snapshot_{2017-12-31,2017-09-30,2017-06-30}.csv`
  - `solution/tests/test_build.py`
- **O que fazer:**
  1. **Leia** CLAUDE.md, SCOPE, SCORING, `backtest_metrics.json`, `score.py` e `explain.py`.
  2. **`build.py`**: CLI `python -m scorer.build --reference-date 2017-12-31 [--out-root SOL]`. "Do zero" significa:
     - apagar `app/data.js`, `briefs/*.md` e `data/processed/snapshot_*.csv`;
     - limpar a partir do raw (gravando `deals.csv` e `facts.json`);
     - rodar `run_backtest` (grava as métricas);
     - para a data de referência (com Prospecting, se a data for o fim dos dados) e para cada `UI_BACKTEST_SNAPSHOTS` ≤ referência: `fit_model` do corte, `score_deals`, `explain_deal`, e o desfecho real nos snapshots de teste (`Ganho` com data e valor / `Perdido` / `Ainda aberto em 31/12/2017`);
     - gravar os CSVs de snapshot (colunas: id, vendedor, manager, região, conta, produto, preço, `engage_date`, idade, p, EV, score, categoria, `days_to_*`, explicação unida por " | ", desfecho);
     - gravar o `data.js`;
     - gravar os briefs;
     - rodar `docs.inject` em todos os docs;
     - imprimir o resumo e o tamanho do `data.js` (meta: < 4 MB).
     - **Asserts:** o resumo de hoje no `data.js` é igual a `backtest_metrics.json["hoje"]`, e as categorias dos snapshots de teste são iguais às do corte correspondente.
  3. **`data.js`:** `window.LEAD_DATA = {...};` com `json.dumps(ensure_ascii=False, separators=(",",":"))`, em utf-8:
     ```
     {"meta":{"reference_date","horizon_days","generated_by":"python -m scorer.build --reference-date 2017-12-31"},
      "people":{"agents":[{"name","manager","region","has_deals","n_open"}],"managers":[{"name","region"}],"regions":[...]},
      "snapshots":[{"date","mode":"hoje"|"teste","model":{knot_days,p_fresh,halving_days,limpe_after_days,...},
                    "how_it_works":[5 linhas],"summary":{Cat:{n,valor_tabela,valor_esperado}},
                    "outcome_summary":{Cat:{n,pct_ganhos,receita_ganha}} (só teste),
                    "deals":[{"id","agent","manager","region","account"(null se ausente),"product","price","engage_date","age","p","ev","score","cat","why":[...],"days_to_knot","days_to_limpe","outcome":null|{"status","close_date","close_value"}}]}],
      "backtest":{"rows":[...tabela média e por corte para o painel "Teste no passado"]}}
     ```
     Nenhum número fica escrito à mão em `app.js` ou `index.html`; todo texto com número vem do `data.js`.
  4. **Interface** (HTML, CSS e JS puros; sem build, sem CDN, sem `fetch`, sem framework). `index.html` com `lang="pt-BR"`, `meta charset utf-8`, `viewport`, e `<script src="data.js"></script><script src="app.js"></script>` no fim do body. Layout, de cima para baixo, com a AÇÃO antes dos números:
     1. **Barra compacta:** "Lead Scorer" + seletor de modo ("Hoje — 31/12/2017" | "Teste: 30/09/2017" | "Teste: 30/06/2017") + link "Como funciona o score".
     2. **Filtros:**
        - Vendedor: `select` com `optgroup` por manager; os 5 sem deals aparecem com "(sem deals no CRM)";
        - Manager; Região; botão Limpar;
        - filtros em cascata;
        - estado salvo no `location.hash` (URLSearchParams), o que funciona em `file://` e no Pages.
     3. **Frase de ação**, montada em JS a partir dos dados filtrados: "Esta semana: foque em N deals, reative M antes que esfriem, limpe K do CRM (US$ X parados) e qualifique Q."
     4. **Quatro abas, que também são os KPIs:** Foque | Reative | Limpe | Qualifique, cada uma com contagem (`data-count`) e valor. Cada aba abre com uma linha-instrução com verbo de ação.
     5. **Cards:** linha 1 conta (ou "Conta não informada") + produto; linha 2 selo do score, valor, "há X dias" e P; linha 3 a 1ª frase do "why". O clique expande para todas as frases, mais id, vendedor, manager, data de engajamento e EV. Mostra 30 por vez, com "Mostrar mais 30".
     6. **"Carteira do time":** aparece quando o filtro não é um vendedor único. Vendedor × contagens das 4 listas, em ordem alfabética, sem taxas de vitória; os sem deals aparecem com o alerta.
     7. **Modo teste:** faixa "Modo teste — o que o score recomendaria em {data} e o que aconteceu até 31/12/2017". Por lista: % de ganhos e receita (`outcome_summary`). Selo de desfecho em cada card. A aba Qualifique mostra "Indisponível no modo teste: o CRM não registra quando o deal entrou em Prospecting."
     8. **`<details>` "Como funciona o score"**, com as 5 linhas do snapshot ativo.

     Outros requisitos:
     - Se `window.LEAD_DATA` não existir, mostre a mensagem "Rode python -m scorer.build".
     - Escape de HTML; `Intl.NumberFormat('pt-BR')`; datas dd/mm/aaaa.
     - **Visual de ferramenta de trabalho:** fontes do sistema; fundo neutro; uma cor por lista (Foque verde, Reative âmbar, Limpe cinza, Qualifique azul); números tabulares; alvo de toque ≥ 44px; sem gráficos decorativos.
     - **Responsivo:** em ≤ 600px, uma coluna, filtros empilhados e KPIs em grade 2×2; em 1280px, conteúdo com largura máxima de cerca de 1100px.
     - **`data-testid` obrigatórios:** `mode-select`, `filter-agent`, `filter-manager`, `filter-region`, `filter-clear`, `action-summary`, `count-Foque`, `count-Reative`, `count-Limpe`, `count-Qualifique` (com `data-count`), `tab-<Cat>`, `deal-card` (com `data-id`), `card-why`, `outcome-badge`, `backtest-summary-<Cat>` (com `data-n` e `data-pct`), `how-it-works`, `team-table`.
  5. **Briefs** (só para a data de referência): `briefs/<slug>.md` (slug = nome em minúsculas com hífen) para cada vendedor com ≥ 1 deal aberto. Conteúdo:
     - título "Brief de segunda-feira — {vendedor} — {data}"; manager e região;
     - a frase de resumo;
     - "3 para focar" (top 3 Foque: conta, produto, valor, idade, score e a 1ª e a 3ª frases);
     - "3 para reativar";
     - "Limpe: N deals (US$ X de tabela)", com os 5 maiores;
     - "Qualifique: N (US$ X)", com os 3 maiores.

     `briefs/README.md` traz o índice (vendedor, manager e contagens) e lista os vendedores sem deals ou sem deals abertos.
  6. **`test_build.py`** roda o build com `--out-root` num `tmp_path` (copiando `data/raw`). Reduza o bootstrap via parâmetro se ficar lento. Confere:
     - `data.js` existe e faz parse (tirando o prefixo `window.LEAD_DATA = ` e o `;` final);
     - as contagens de hoje são iguais a `backtest_metrics["hoje"]`;
     - existe 1 brief por vendedor com deal aberto;
     - os 3 CSVs de snapshot existem;
     - dois builds seguidos geram `data.js` idêntico.
  7. **Rode o build real.** Abra `index.html` uma vez com Playwright só para ver se carrega; a verificação completa fica na E7. Comece o `04_bloco-4.md` com o que foi feito.
- **Pronto quando:**
  - `Set-Location $SOL; & $PY -m scorer.build --reference-date 2017-12-31; & $PY -m pytest; & $PY -m scorer.docs --check` com exit 0;
  - `Test-Path "$SOL\app\data.js"`;
  - `(Get-ChildItem "$SOL\briefs\*.md").Count -ge 28` (27 briefs + README; confirme o número real);
  - `gitw.py status` mostra "nada" fora da pasta.
- **Commit:** — (o bloco 4 é commitado depois da E7)

---

### E7 — Bloco 4b: verificação Playwright, screenshots e 3 atritos reais
- **Executor:** sonnet
- **Depende de:** E6
- **Arquivos:** `solution/tools/check_app.py`, `process-log/screenshots/*.png`, `solution/app/*` (correções), `process-log/04_bloco-4.md`, `docs/DECISIONS.md`.
- **O que fazer:**
  1. **`tools/check_app.py`**, reutilizável. Uso: `& $PY tools\check_app.py --prefix antes|depois|final` (cwd `$SOL`). Exit 1 se qualquer checagem falhar. Comportamento:
     - Abre `Path("app/index.html").resolve().as_uri()` com `sync_playwright` e `chromium.launch(channel="msedge", headless=True)`; se o Edge não existir, cai para o Chromium padrão.
     - Coleta `console` do tipo error, `pageerror` e `requestfailed`, e exige zero.
     - Lê `window.LEAD_DATA` via `page.evaluate`.
     - **Checagens:**
       - (a) sem filtro, modo hoje: o `data-count` de cada lista é igual a `backtest_metrics.json["hoje"]` e o bloco `AUTO:scoring-hoje` do SCORING contém essas contagens formatadas;
       - (b) com o filtro do vendedor com mais deals abertos (calculado a partir de `snapshot_2017-12-31.csv`), a contagem por lista é igual à do CSV filtrado; o mesmo vale para 1 manager e 1 região;
       - (c) no modo 2017-09-30 e no modo 2017-06-30, `data-n` e `data-pct` de cada lista são iguais às categorias do corte no JSON;
       - (d) "Como funciona" abre com exatamente 5 linhas;
       - (e) o 1º card expande e mostra de 2 a 4 frases;
       - (f) um vendedor sem deals mostra o estado vazio.
     - **Screenshots** em `$SUB\process-log\screenshots\{prefix}_{vista}_{largura}.png`, nas larguras 1280×800 e 390×844, para as vistas `inicio`, `vendedor`, `card-aberto`, `modo-teste` e `como-funciona`.
     - Imprime um relatório PASSOU/FALHOU por checagem.
  2. **Rode `--prefix antes`** e corrija as falhas de checagem. Isso é bug, não atrito; registre com o antes e o depois.
  3. **Passada "vendedor na segunda de manhã".** Abra e OLHE os PNGs `antes_*` com a ferramenta Read e simule as tarefas, contando cliques e rolagem:
     - T1: "sou o vendedor com mais deals abertos; quais 3 deals ataco hoje e por quê?";
     - T2: "o que está esfriando e quanto tempo tenho?";
     - T3: "quanto do meu pipeline é lixo e o que faço?";
     - T4: "no celular (390px), consigo fazer T1?";
     - T5: "como manager, o que do meu time precisa de atenção?".

     Para cada tarefa, anote o que atrapalhou, com evidência (nome do PNG e o que se vê). Não use atritos pré-escritos. Escolha os 3 atritos reais mais importantes; olhe, por exemplo, para: ação abaixo da dobra, jargão, número sem unidade, texto cortado em 390px, cliques demais, ordem confusa e explicação que não responde ao "por quê".
  4. **Corrija os 3 atritos**, rode `--prefix depois` e confirme as checagens verdes. Os pares `antes_*` e `depois_*` da mesma vista são a evidência.
  5. **Rode `--prefix final`** para os screenshots finais, em 390 e 1280.
  6. **`04_bloco-4.md`:** o que foi construído; o resultado das checagens; a tabela de atritos (atrito → evidência antes → correção → evidência depois); os bugs; e a autoverificação do checkpoint. **DECISIONS:** estrutura do `data.js`, estado no hash, tabela do time sem taxas, as 3 correções.
- **Pronto quando:**
  - `Set-Location $SOL; & $PY -m scorer.build --reference-date 2017-12-31; & $PY -m pytest; & $PY tools\check_app.py --prefix final` com exit 0;
  - existem os PNGs `final_*_390.png` e `final_*_1280.png`, e ≥ 3 pares `antes_`/`depois_`;
  - `04_bloco-4.md` lista 3 atritos com nomes de arquivo;
  - `gitw.py status` mostra "nada" fora da pasta.
- **Commit:** "bloco 4: ferramenta"

---

### E8 — Bloco 5: MODEL_CARD, README e verificação de números
- **Executor:** sonnet
- **Depende de:** E7
- **Arquivos:** `docs/MODEL_CARD.md`, `README.md` (em `$SUB`), `solution/scorer/docs.py` (blocos novos), `solution/tests/test_readme.py`, `docs/DECISIONS.md`, `process-log/05_bloco-5.md`.
- **O que fazer:**
  1. **Leia** CLAUDE.md, todos os arquivos de `docs/` e de `process-log/`, `$PM\ai-master-challenge\templates\submission-template.md` e o `backtest_metrics.json`.
  2. **`MODEL_CARD.md`** (1 página):
     - propósito e uso pretendido;
     - uso NÃO pretendido: avaliar ou ranquear vendedores, forecast financeiro, encerrar deals automaticamente;
     - dados e período (8.800 deals; engajamentos de out/2016 a dez/2017; fechamentos de mar a dez/2017; fotos de treino);
     - desempenho: bloco AUTO `mc-desempenho` com a média dos cortes e o pior corte;
     - limitações: dataset sintético, regra Q/Q+1 e teto de 138 dias, censura, contas faltantes, Prospecting sem score, só 1 foto de treino no corte de 30/06, recência melhor em AUC nos fins de trimestre;
     - riscos e mitigação: profecia autorrealizável (Limpe significa confirmar, não descartar); viés contra vendedores (vendedor fora do score, teste de permutação); valor estático;
     - quando recalibrar: a cada trimestre, ou quando a taxa de ganho em 90 dias de alguma faixa de idade se mover mais que X pp, sendo X um parâmetro documentado; ou ao migrar para um CRM real com histórico de estágios;
     - dono (RevOps) e frequência de revisão.
  3. **`README.md`** seguindo EXATAMENTE o template: mesmos títulos, mesma ordem, separadores `---`, a tabela de ferramentas e o checklist de evidências. Os placeholders em itálico são substituídos por conteúdo.
     - **Títulos obrigatórios, nesta ordem:**
       - `# Submissão — Rafael Pereira — Challenge 003`
       - `## Sobre mim`: Nome "Rafael Pereira"; LinkedIn https://www.linkedin.com/in/rafael-pereira-30122003-; Challenge "003 — Lead Scorer"
       - `## Executive Summary`
       - `## Solução` → `### Como rodar (setup)` (subseção permitida pelo "use o formato que melhor comunicar") → `### Abordagem` → `### Resultados / Findings` → `### Recomendações` → `### Limitações`
       - `## Process Log — Como usei IA` → `### Ferramentas usadas` → `### Workflow` → `### Onde a IA errou e como corrigi` → `### O que eu adicionei que a IA sozinha não faria`
       - `## Evidências`
       - linha final `_Submissão enviada em: [preencher ao abrir o PR]_`
     - **Executive Summary:** no máximo 5 frases. Abre com o achado (frescor > atributos) e o impacto (valor de tabela da lista Limpe hoje, cerca de US$ 3,2 mi, tirado do JSON). Fecha com a recomendação principal.
     - **Setup:**
       - link do GitHub Pages como `https://<seu-usuario>.github.io/ai-master-challenge/submissions/rafael-pereira/solution/app/ [ativar — Rafael]`;
       - duplo-clique em `solution/app/index.html`;
       - regenerar: `cd solution`, `pip install -r requirements.txt`, `python -m pytest`, `python -m scorer.build --reference-date 2017-12-31`;
       - verificação opcional: `pip install -r requirements-dev.txt` e `python tools/check_app.py --prefix final`.
     - **Resultados:** tabela AUTO `readme-backtest` (média e cada corte: score, valor, recência e aleatório na receita no top 20%, mais AUC); `readme-hoje` (contagens e valores das 4 listas); 2 screenshots `final_*` linkados.
     - **Recomendações para a Head de RevOps, priorizadas:**
       1. sprint de limpeza da lista Limpe;
       2. rotina de segunda com Foque e Reative;
       3. higiene do CRM: conta, data de criação, histórico de estágios;
       4. não usar win rate por vendedor (ruído);
       5. recalibrar com dados reais.
     - **Process log:**
       - ferramentas: Claude app na fase 0 (modelos citados no 00); Claude Code com Opus 5.5 planejando e Sonnet/Haiku executando, conforme os NN logs; subagente revisor de contexto limpo. Playwright/Edge e dulwich aparecem no workflow, não como ferramentas de IA;
       - workflow: 1 item por bloco, de 0 a 6;
       - "Onde a IA errou": SOMENTE episódios registrados em `process-log/` e DECISIONS. Os da fase 0 são marcados "(fase 0, com Rafael)"; os desta execução, "(autocorreção na execução autônoma)";
       - "O que eu adicionei": começa literalmente com `[RASCUNHO — Rafael revisar]`, baseado só no `00_fase0_exploracao.md`: escolha do 003 pelo ângulo de governança; não contornar o bloqueio do Kaggle; exigir backtest temporal; vendedor fora do score; 138 dias não vira regra; model card.
     - **Evidências:** marque o que existe (screenshots, git history, process log narrativo, DECISIONS, revisões independentes) e explique a ausência de chat exports (LEIA-ME).
  4. **Números:** inclua README e MODEL_CARD em `docs.py` e em `test_docs_numbers`. **`test_readme.py`:**
     - títulos na ordem;
     - executive summary com ≤ 5 frases (fim de frase por `[.!?](\s|$)`, que não quebra "1.291");
     - contém o LinkedIn e `[RASCUNHO — Rafael revisar]`;
     - links relativos para arquivos que existem.
  5. **Revise** todo número do README, do MODEL_CARD e do SCORING contra os JSONs (o teste faz isso). Liste em `05_bloco-5.md` cada divergência encontrada e corrigida. **DECISIONS:** estrutura do README, setup dentro de Solução, conteúdo do model card.
- **Pronto quando:**
  - `Set-Location $SOL; & $PY -m scorer.build --reference-date 2017-12-31; & $PY -m pytest; & $PY -m scorer.docs --check` com exit 0;
  - `Select-String -Path "$SUB\README.md" -SimpleMatch "[RASCUNHO — Rafael revisar]"` encontra o texto;
  - `Test-Path "$SUB\docs\MODEL_CARD.md"`;
  - `gitw.py status` mostra "nada" fora da pasta.
- **Commit:** "bloco 5: documentação e model card"

---

### E9 — Bloco 6: revisão independente nº 1 (feita pelo ORQUESTRADOR)
- **Executor:** orquestrador (subagente de contexto limpo; nenhum executor faz esta etapa)
- **Depende de:** E8
- **Arquivos:** `process-log/06_revisao-independente.md` (seção "Revisão 1", texto integral).
- **O que fazer:** dispare o subagente passando SÓ três caminhos: `$PM\ai-master-challenge\challenges\build-003-lead-scorer\README.md`, `$PM\ai-master-challenge\submission-guide.md` e `$SUB`. Prompt sugerido:

  > Você é avaliador do processo seletivo AI Master do G4 e já tem respostas baseline geradas por LLMs. Avalie esta submissão contra cada critério de qualidade do challenge (funciona de verdade; o scoring faz sentido e vai além do óbvio; um vendedor não técnico usa e entende; a interface ajuda a decidir; código mantível) e também documentação e process log, com nota de 1 a 5 e justificativa. Siga as instruções de setup do README ao pé da letra e diga se funcionou. O Python já existe em `<PY>`: use-o e não crie venv. Abra `solution/app/index.html` em `file://` com Playwright (`chromium.launch(channel="msedge", headless=True)`) e veja o console. Não edite nenhum arquivo. Aponte os 5 pontos mais fracos e o que pareceria "baseline de LLM".

  Salve o relatório sem filtro.
- **Pronto quando:** a seção "Revisão 1" existe no arquivo, com as notas por critério.
- **Commit:** — (vai junto do bloco 6)

### E10 — Bloco 6: correções dos critérios com nota ≤ 3
- **Executor:** sonnet
- **Depende de:** E9
- **Arquivos:** os apontados pela revisão; `process-log/06_revisao-independente.md` (seção "Correções aplicadas"); `docs/DECISIONS.md`.
- **O que fazer:**
  1. **Leia** o relatório da Revisão 1, colado pelo orquestrador, e CLAUDE.md.
  2. **Para cada critério com nota ≤ 3,** proponha e aplique a correção, com o antes e o depois.
  3. **Proibido:** mudar o modelo, os parâmetros, o critério ou a métrica primária do score (o ajuste único do bloco 3 já foi usado ou não). Uma crítica de modelagem vira limitação documentada + linha em DECISIONS. Exceção: bug em que o código diverge do SCORING; corrija e registre.
  4. **Críticas não corrigidas:** registre o motivo.
  5. **Depois de corrigir,** rode build, pytest, `docs --check` e `check_app.py --prefix final`.
- **Pronto quando:** os mesmos comandos da E8 mais `& $PY tools\check_app.py --prefix final` com exit 0; a seção "Correções aplicadas" lista critério → mudança → arquivo.
- **Commit:** —

### E11 — Bloco 6: revisão independente nº 2 (feita pelo ORQUESTRADOR)
- **Executor:** orquestrador (um NOVO subagente de contexto limpo; não lhe passe a Revisão 1)
- **Depende de:** E10
- **Arquivos:** `process-log/06_revisao-independente.md` (seção "Revisão 2", texto integral, mais uma tabela comparando as notas 1 × 2).
- **O que fazer:** mesmo prompt da E9.
- **Pronto quando:** a seção "Revisão 2" existe.
- **Commit:** —

### E12 — Bloco 6: fechamento, definição de pronto e texto do PR
- **Executor:** haiku
- **Depende de:** E11
- **Arquivos:** `process-log/06_bloco-6.md`, `docs/DECISIONS.md`; fora do repo, como permitido pelo PROMPT_AUTONOMO §6, `$PM\kit-lead-scorer\PR.md`.
- **O que fazer:**
  1. **Verificação "do zero":** apague `$SOL\app\data.js`, `$SOL\briefs\*.md` e `$SOL\data\processed\snapshot_*.csv`; rode `& $PY -m scorer.build --reference-date 2017-12-31`; confirme que todos foram recriados. Depois rode `& $PY -m pytest`, `& $PY -m scorer.docs --check` e `& $PY tools\check_app.py --prefix final`.
  2. **Checklist da definição de pronto** em `06_bloco-6.md`, cada item com o comando e o resultado:
     - `docs/` tem os 5 arquivos;
     - `process-log` tem os logs 00 a 06, os screenshots e as 2 revisões;
     - `gitw.py status` não mostra nada fora da pasta.

     Item que falhar: reporte ao orquestrador, sem consertar.
  3. **`PR.md`:**
     - título `[Submission] Rafael Pereira — Challenge 003`;
     - corpo com o executive summary copiado do README, o link do Pages (placeholder) e o checklist do CONTRIBUTING.md marcado;
     - comandos exatos:
       - fork no GitHub;
       - com git instalado: `git remote add fork https://github.com/<seu-usuario>/ai-master-challenge.git` e `git push -u fork submission/rafael-pereira`;
       - ativar o Pages: Settings → Pages → branch `submission/rafael-pereira`, pasta `/ (root)`; a URL fica em `…/submissions/rafael-pereira/solution/app/`;
       - `gh pr create --repo Gestao-Quatro-Ponto-Zero/ai-master-challenge --base main --head <seu-usuario>:submission/rafael-pereira --title "[Submission] Rafael Pereira — Challenge 003" --body-file "<PM>\kit-lead-scorer\PR.md"`.
  4. **DECISIONS:** as críticas aceitas e as recusadas.
- **Pronto quando:** todos os comandos do item 1 com exit 0; `Test-Path "$PM\kit-lead-scorer\PR.md"`; `gitw.py status` mostra "nada" fora da pasta.
- **Commit:** "bloco 6: revisão independente e correções"

## Riscos / pontos de atenção

1. **A recência é um baseline muito forte em AUC** nos cortes de fim de trimestre (0,73 e 0,83 no protótipo). O gerador encerra deals no fim do trimestre seguinte ao engajamento. Isso já está pré-registrado: a métrica primária é a receita no top 20%, e a AUC é reportada com honestidade. Não deixe executor nenhum "consertar" isso trocando métrica ou modelo depois de ver os números. Mostre também o 31/07, em que a recência despenca (captura de ganhos ≈ 0,12, abaixo do aleatório); é o argumento de robustez do score.
2. **Vazamento via conta ausente:** os 1.425 sem conta estão todos abertos no fim. Qualquer feature de conta com nível "desconhecido" vira um detector perfeito de zumbi. O teste de mutação e a auditoria (AUC de `has_account`) provam que a guarda funciona.
3. **Corte de 30/06 com 1 foto de treino** (k=70, aprendido de 1.330 linhas): o modelo é frágil. Reporte isso e mostre a sensibilidade com 28/02. A regra "≥ 31/03" foi decidida depois de o planejador ver o protótipo. Isso precisa constar no log; já está no texto da E3 e da E4.
4. **Artefatos do gerador** (regra Q/Q+1, teto de 138 dias, ciclos de 7 dias no 1º mês do trimestre, fins de trimestre com cerca de 80% de vitória). Documente-os e não os explore. Consequência honesta: a lista Reative tem taxa de vitória de 0% a 23% nos cortes. Ela fica, mas o SCORING e o MODEL_CARD explicam.
5. **Números do briefing × números do modelo:** o briefing tem Foque 110 / Reative 188 com faixas fixas de 90 e 138 dias; o modelo dá 126 / 172, com joelho aprendido em 95. O SCORING precisa explicar a diferença. Os US$ 3,2 mi da lista Limpe coincidem (limite 138).
6. **Pandas 3 e Windows:** CoW, dtype `str`, `freq="ME"`, `datetime64[us]`, JSON com tipos numpy, encoding UTF-8, caminhos com espaço, URI `file://` via `Path.as_uri()`. Os scripts da fase 0 rodam no pandas 3.1 (verificado).
7. **Determinismo:** o `gitw.py commit` adiciona tudo o que está na pasta (exceto caches). Se algum artefato carregar timestamp, todo build vira diff, e a revisão independente (que roda o build) suja o status. Os executores não podem criar arquivos temporários dentro de `$SUB`; o `tmp_path` do pytest fica fora.
8. **Revisor do bloco 6:** pode tentar criar um venv dentro da pasta, seguindo o README. O prompt manda usar `$PY`. Depois de cada revisão, rode `gitw.py status`.
9. **Tamanho do `data.js`:** cerca de 6.200 deals com explicações dão de 2 a 4 MB. Se passar de 4 MB, use chaves curtas ou explicações só no snapshot ativo. Não troque por `fetch`.
10. **Escopo e tempo:** no bloco 4, nada de polimento visual além dos 3 atritos. Se faltar tempo, siga o GUIA: cortar primeiro o modo teste, depois os briefs, depois o visual. Nunca cortar validação nem process log.
11. **O orquestrador deve:**
    - salvar este plano como `process-log/plano_execucao_opus.md` antes do commit do bloco 0 (é a evidência do "Plan Mode");
    - conferir em cada log que o modelo executor está declarado (o README do bloco 5 depende disso);
    - garantir que a E10 não mexeu no modelo.
12. **Vendedores:** 5 sem deals (um por time, exceto o de Dustin Brinkmann) e 3 só com fechados (confirmar no bloco 2). Os briefs e o teste de contagem dependem do número real de vendedores com deals abertos (protótipo: 27).
13. **GitHub Pages:** o nome de usuário é desconhecido. O README e o PR.md usam placeholder marcado, sem inventar URL.

### Critical Files for Implementation
- C:\Users\Info Mania\Documents\Predictive Analytics for CRM Sales Performance\ai-master-challenge\submissions\rafael-pereira\solution\scorer\features.py
- C:\Users\Info Mania\Documents\Predictive Analytics for CRM Sales Performance\ai-master-challenge\submissions\rafael-pereira\solution\scorer\score.py
- C:\Users\Info Mania\Documents\Predictive Analytics for CRM Sales Performance\ai-master-challenge\submissions\rafael-pereira\solution\scorer\validate.py
- C:\Users\Info Mania\Documents\Predictive Analytics for CRM Sales Performance\ai-master-challenge\submissions\rafael-pereira\solution\scorer\build.py
- C:\Users\Info Mania\Documents\Predictive Analytics for CRM Sales Performance\ai-master-challenge\submissions\rafael-pereira\solution\app\app.js