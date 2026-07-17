# PLAN — Challenge 002 (Redesign de Suporte) — Alan Gattiboni

Método: rolling-wave. Só o bloco atual vem detalhado. Ao fechar um bloco,
decupamos o próximo. Ciclo por tarefa: arquitetar, instruir Codinho, executar,
verificar, aprovar, commit.

Princípios: Incrementalidade, Modularidade, Zero dívida técnica.

---

## Bloco 0 — Fundação _(fechado)_

- [x] Fork do repo
- [x] Clone + branch `submission/alan-gattiboni`
- [x] README scaffold (template) + commit (`3e92232`)
- [x] Estrutura de pastas: `solution/`, `solution/datasets/`,
      `process-log/screenshots/`, `process-log/chat-exports/`, `docs/`
- [x] `docs/PLAN.md` criado e versionado
- [x] Ambiente confirmado: Python 3.12.4, `requirements.txt` congelado (pandas
      2.3.3, numpy 2.2.6, matplotlib 3.11.0, seaborn 0.13.2, scikit-learn 1.9.0,
      jupyterlab 4.6.1, ipykernel 7.3.0)
- [x] Datasets validados (`df.shape`, `df.columns`) e confrontados com o brief.
      Divergências: 8.469 tickets reais para o Dataset 1 (a contagem de ~30K do
      brief é linha física, não ticket); Dataset 1 sintético; datasets não
      cruzáveis. Insumo do Ato 1.
- [x] Seção `## Reprodução` na capa (`README.md`): pré-requisitos, setup do
      venv, download manual com os 2 links do Kaggle, sanity check dos
      `df.shape` (8.469 / 47.837)

---

## Bloco 1 — EDA adversarial _(fechado)_

Auditar cada fonte e concluir num veredito de qualidade. Onde o dado falha,
provar onde e como.

**Regras do bloco:**

- Cada hipótese (D1 sintético, nulos estruturais, não-cruzáveis, Miscellaneous
  preguiçoso) é uma pergunta testada para refutar ou comprovar.
- Cada achado é uma célula com evidência crua: contagem, amostra ou gráfico.
- Um módulo de auditoria por dataset, sem estado compartilhado.
- Bloco de auditoria e veredito. Medallion, gate e classificador são blocos
  posteriores.

- [x] **1.0** Scaffold do notebook: imports, load dos 2 CSVs com dtype seguro,
      esqueleto de seções. Roda e carrega sem erro.
- [x] **1.1** D1 — integridade e semântica dos nulos. Nulos 100% estruturais por
      `Ticket Status`, zero violações de coerência.
- [x] **1.2** D1 — sinteticidade. 100% das descrições com placeholder cru;
      metadados categóricos com entropia normalizada acima de 0,999 (uniformes,
      sem sinal de negócio).
- [x] **1.3** D2 — distribuição de classes. Top-3 em 66,18%; `Miscellaneous`
      difuso confirmado.
- [x] **1.4** D2 — sinal do texto. Vocabulário discriminativo por classe com
      ruído residual de pré-processamento.
- [x] **1.5** Cruzabilidade. Sem coluna, taxonomia ou identificador em comum.
- [x] **1.6** Veredito por fonte: dict `verdict` renderizado em tabela, com
      PASS/WARN/FAIL por dimensão.

**Pronto quando:** notebook roda ponta a ponta, cada hipótese testada com
evidência, veredito PASS/WARN/FAIL por fonte legível em minutos.

## Bloco 2 — Diagnóstico operacional _(fechado)_

Diagnóstico das duas fontes auditadas. A operação real sai do D2. O D1 sintético
vira achado sobre a própria medição. Notebook próprio,
`solution/02_diagnostico_operacional.ipynb`, autossuficiente.

**Regras do bloco:**

- Cada achado responde uma pergunta com evidência computada.
- Relação medida por tamanho de efeito. Em amostra grande o p-valor sinaliza
  significância para diferença irrelevante.
- Tabela e número neste bloco. Visual fica no empacotamento.
- Um notebook autossuficiente, sem estado importado do Bloco 1.

- [x] **2.1** Demanda real (D2). Top-3 `Topic_group` em 66,18% (Hardware 28,47%,
      HR Support 22,82%, Access 14,89%). Cauda de seis categorias abaixo de 6%.
- [x] **2.2** Desperdício de triagem (D2). `Miscellaneous` reúne 7.060 tickets
      (14,76%), 5.925 termos distintos, termo de topo `change` em 24,6% dos docs
      contra 80,4% de `administrator` em `Purchase`. Custo de re-roteamento a 3
      min por ticket: 353 horas.
- [x] **2.3** Lacuna de instrumentação (D1). Eta-quadrado no máximo 0,00210 nas
      9 combinações atributo por desfecho, faixa desprezível. Diferença
      `Time to
      Resolution` menos `First Response Time` negativa em 49,3%
      dos `Closed`. Os atributos não explicam os desfechos e os carimbos de
      tempo não medem duração.
- [x] **2.4** Síntese. Dict `diagnostico` com demanda, desperdício e
      instrumentação, renderizado em tabela.

**Pronto quando:** notebook roda ponta a ponta, os três achados sustentados por
número, lacuna do D1 provada por tamanho de efeito.

## Bloco 3 — Proposta de automação _(fechado)_

Desenho da automação de suporte ancorado nos achados dos Blocos 1 e 2. Documento
próprio, `solution/03_proposta_automacao.md`. Arquitetura agnóstica de fonte que
roda no D2 como prova e aponta o D1 como gap de instrumentação.

**Regras do bloco:**

- Cada decisão de automação ancorada num achado numérico dos Blocos 1 e 2.
- Cada fronteira do que fica humano justificada por um FAIL ou WARN provado.
- Desenho e decisão neste bloco. O protótipo que roda é o Bloco 4.
- IA generativa entra onde recupera sinal, com critério explícito.

- [x] **3.1** O que automatizar e o que não. Triagem automática de tickets como
      alvo, ancorada no desperdício de 2.2 (353h de re-roteamento) e no sinal de
      1.4. Fronteira do que fica humano: priorização e previsão de desfecho no
      domínio do cliente, bloqueadas pelo D1 (2.3).
- [x] **3.2** Fluxo ponta a ponta. Pipeline com portas de ingestão agnósticas de
      fonte, normalização, classificação (Bloco 4), roteamento, escalonamento
      por confiança. Papel da IA generativa com critério.
- [x] **3.3** Pré-requisito de instrumentação. O que capturar para estender a
      arquitetura ao cliente. O D1 é a prova do gap.

**Pronto quando:** documento existe, cada decisão de automação ancorada em
achado dos Blocos 1 e 2, fluxo desenhado ponta a ponta, fronteira do que não
automatizar justificada por FAIL ou WARN.

## Bloco 4 — Protótipo funcional _(fechado)_

Classificador que roda no D2 com métrica real em holdout, mais a camada de
abstenção que desvia o ticket difuso para revisão humana. Notebook próprio,
`solution/04_prototipo_classificador.ipynb`, autossuficiente. Prova o que o dado
real permite: o D2 tem rótulo e sinal, o D1 não treina classificador.

**Regras do bloco:**

- Métrica em holdout, F1-macro. As classes são desbalanceadas e a acurácia
  premia a maioria.
- Split estratificado, sem vazamento de treino para holdout.
- Classificador simples e inspecionável: TF-IDF mais um linear. Transformer é
  infra que o protótipo não pede.
- A abstenção da opção (b) é demonstrada por número, não afirmada.
- A IA generativa do fluxo (Bloco 3) é proposta. O protótipo classifica o texto
  do D2 direto.

- [x] **4.1** Classificador base com holdout. Split estratificado treino e
      holdout, TF-IDF mais linear, F1-macro contra um baseline trivial (classe
      majoritária), matriz de confusão.
- [x] **4.2** Camada de abstenção (opção b). Score de confiança e limiar. Ticket
      abaixo do limiar vai para revisão humana. Medir o ganho de qualidade na
      fração automatizada e a composição do que foi desviado, com atenção à
      participação de `Miscellaneous`.
- [x] **4.3** Contrato de inferência e síntese. Função texto para categoria,
      confiança e decisão automática ou revisão, um exemplo inspecionável, e um
      dict de resultados que o Bloco 5 consome.

**Pronto quando:** notebook roda ponta a ponta, F1-macro em holdout reportado
contra baseline, ganho da abstenção quantificado, contrato de inferência roda
num exemplo, resultados num dict para o Bloco 5.

## Bloco 5 — Empacotamento _(fechado)_

Empacotamento da submissão para avaliação. Três artefatos: a capa que o avaliador
lê, a vitrine que ele inspeciona, o PR que entrega. A capa carrega a narrativa dos
quatro blocos, o HTML é a versão visual dela, o PR aponta para a capa.

**Regras do bloco:**
- A capa é o documento avaliável. O HTML e o PR não duplicam a narrativa dela.
- HTML standalone, dados embutidos, abre do arquivo sem servidor.
- O HTML mostra o que foi feito: auditoria, gates, classificador. Sem ETL que os
  Blocos 1 a 4 não construíram.
- Cada artefato inspecionável em minutos. Nada de infra que o brief não pediu.

- [X] **5.1** Capa `README.md`. Preencher os placeholders com a narrativa real:
      Executive Summary, Abordagem, Findings com os números dos Blocos 1 a 4,
      Recomendações, Limitações, e a tabela do Process Log apontando os dev-logs.
- [X] **5.2** HTML Pipeline Inspector. Vitrine standalone com dados embutidos dos
      Blocos 1 a 4. Três seções: registro cru do D1 com os defeitos anotados,
      gates PASS/WARN/FAIL, e o classificador com predição e confiança.
- [X] **5.3** Pull Request. Corpo curto que aponta para a capa e confirma
      conformidade com as regras. Título `[Submission] Alan Gattiboni — Challenge 002`.

**Pronto quando:** capa sem placeholder órfão, HTML abre do arquivo e mostra as
três seções, PR aberto do fork para o upstream com o título correto.