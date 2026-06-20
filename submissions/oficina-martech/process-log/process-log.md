# Process Log — Lead Scorer (Challenge 003) — Oficina Martech

> Como usei IA para construir o **Foco**. Registro capturado ao longo do trabalho (evidências de execução em `execucoes/`).

> ▶ **Demo ao vivo:** https://ai-master-challenge-whltkcmfjkn7qsrufhr3es.streamlit.app/ (Streamlit Cloud — Main file path `submissions/oficina-martech/solution/app/main.py`, branch `submission/oficina-martech`). Ou rode **local em 3 comandos** (`make setup && make run`) — SQLite + Streamlit, sem API key nem Docker; o banco auto-inicializa no primeiro boot (`_ensure_db` em `solution/app/main.py`).
>
> 🔁 **Reorganização de estrutura (2026-06-20):** a pasta foi reorganizada para o layout do `CONTRIBUTING.md` — `README.md` (template) na raiz, código em `solution/`, evidências em `process-log/` (`execucoes/` · `screenshots/` · `chat-exports/`) e documentação de apoio em `docs/`. Caminhos nos docs vivos foram atualizados; as transcrições em `chat-exports/` foram preservadas como registro histórico (mencionam caminhos antigos de propósito). App revalidado de `solution/`: **31 passed + boot HTTP 200**.

## Ferramentas usadas
| Ferramenta | Para quê | Por quê |
|------------|----------|---------|
| **Claude Code Opus 4.8 (High)** | **Mapeamento inicial**: leitura do contexto e do brief, entendimento das 4 tabelas, hipóteses H1–H5 antes de abrir os dados — depois EDA, design do scoring, código do núcleo e do app, testes, tema/UI da marca | escolhido por raciocínio profundo em contexto longo; consegue analisar + codificar no mesmo loop sem perder coerência entre fases |
| Codex 5.5 (High) | polish visual direto no app em `localhost:8501`: removeu `st.code` escuro do brief (substituiu por painel claro de prioridades acionáveis), corrigiu tokens ink escuros remanescentes, ajustou segmented control Lista/Kanban | iteração visual rápida com preview ao vivo |
| **OpenCode + GLM 5.2** | **revisão do modelo de scoring + correção de calibração** — identificou que urgência estava calibrada na distribuição errada (Won median 57d ≠ open deals median 165d), propôs clamp do winrate e fix de tier para deals stale | análise independente de dados que Claude Code Opus não havia feito |
| Python (pandas) | exploração dos dados e protótipo do scoring | rápido para cruzar as 4 tabelas |
| Streamlit + SQLite | app e persistência | roda em qualquer máquina, sem servidor |

A IA foi a alavanca de execução; o meu papel foi **decidir o que medir, desconfiar dos resultados e cortar o que não tinha sinal**.

---

## Fase 1 — Entender (hipóteses ANTES de olhar os dados)

Dataset: 4 CSVs (pipeline ~8.800, accounts 85, products 7, sales_teams 35). Universo de decisão = deals abertos (Prospecting/Engaging).

Hipóteses que escrevi antes de rodar qualquer análise:
- **H1 (óbvio):** `deal_stage` é o maior preditor de fechamento.
- **H2 (aposta):** win-rate varia por **vendedor**, **produto** e combinações; a feature diferenciadora seria o histórico de win-rate da célula do deal com smoothing bayesiano.
- **H3 (urgência data-driven):** "deal esfriando" = dias desde `engage_date` acima do ciclo mediano real dos Won — não um threshold chutado.
- **H4 (valor × probabilidade):** priorizar por valor esperado, não por valor bruto.
- **H5 (higiene):** já tinha visto `GTXPro` vs `GTX Pro` no preview — verificar joins, nulos e datas antes de modelar.

---

## Fase 2 — EDA (achados verificados nos dados) → `execucoes/eda-output.txt`
- **Universo a scorar: 2.089 deals abertos** (1.589 Engaging + 500 Prospecting). Won 4.238, Lost 2.473.
- **Win-rate global 63,2% — sinal fraco e quase só no vendedor:**
  - **Vendedor: 55%–70% (spread 15pp)** ← único sinal forte
  - Produto 60–65%, setor 61–65%, regional 62–64%, manager 62–64%, faixa de valor 62–64% → **todos ~chapados (3–5pp)**
- **Ciclo (Won): mediana 57d, p75 88d, p90 106d, máx 138d.** Lost morre rápido (mediana 14d). Esses percentis ancoram a urgência em **curva sino** (pico na janela 57–88d, decai até 138d, piso além) — não um corte monotônico "quanto mais velho, mais urgente", que premiaria cadáveres.
- **Higiene:** `GTXPro`≠`GTX Pro` (corrigido no seed); **1.425 deals sem `account`** (**68% dos abertos** — o denominador correto é 2089 abertos, não 8800 total); **500 sem `engage_date` = os Prospecting** (sem aging → renormalizar pesos).
- Valor não muda a probabilidade → priorizar por **valor esperado**.

## Revisão de cálculos pelo GLM 5.2 (OpenCode)

O GLM 5.2 rodou uma análise independente dos dados e identificou um erro de calibração no scoring que o Claude Code Opus não havia detectado:

| Achado | Impacto |
|--------|---------|
| `days_open` dos deals **abertos** (Engaging): mediana **165d**, p75=263d, p90=319d | A urgência foi calibrada no ciclo dos **Won** (mediana 57d) — distribuições completamente diferentes |
| `STALE_DAYS` foi recalibrado para **138d** (= Won mais velho da história) — não mais 3×mediana (171d) | Resultado real: **1.291 de 2.089 abertos (61,8%)** caem em stale — pipeline genuinamente inflado, reportado como insight |
| `smoothed_winrate` sem clamp `[0,1]` | Pode gerar pontos negativos ou > 100 em edge cases |
| `tier` não rebaixava deals stale | Um deal 🔥 Foco Agora com 400d aberto mantinha o tier — inconsistência de decisão |

Fixes identificados: recalibrar urgência na distribuição dos **abertos** (não dos Won), clamp de win-rate, derivar tier levando em conta `is_stale`, excluir deals sem conta do brief.

Evidência: `screenshots/glm52-analise-calculos.png`

## Auditoria final GLM 5.2 — gaps identificados e status (2026-06-19)

| # | Gap identificado | Por quê importa | Status |
|---|-----------------|-----------------|--------|
| 1 | **Limiar stale inconsistente entre código e docs** — código usava `WON_MAX_DAYS=138d`, docs diziam `3× mediana (171d)` | Red flag: quem lê os docs e o código vê números diferentes | ✅ Corrigido — docs alinhados para `138d` |
| 2 | **Denominador errado em "sem conta"** — `1425/8800=16%` em vez de `1425/2089=68%` dos abertos | Bug factual no insight central de RevOps: 16% parece ruim, 68% é crítico | ✅ Corrigido — denominador agora `open_deals` (2089) |
| 3 | **Evidências de texto desatualizadas** — arquivos de execução gerados antes das correções de scoring e UI | Evidence que contradiz o código atual custa credibilidade na avaliação | ✅ Corrigido — pytest.txt (28), eda-output.txt, smoke-test regenerados |
| 4 | **Screenshots** — recapturados após o fix do denominador e o reorder de Saúde | Telas refletem o app vigente (68% sobre abertos, Higiene no topo) | ✅ Recapturado |
| 5 | **Filtro Regional ignorado em Saúde** — `view_saude()` lia `outcome` global sem aplicar `selected_region` | Dado errado ao filtrar por regional | ✅ Corrigido pelo GLM 5.2 via OpenCode |
| – | (opcional) Modularizar `main.py` + type hints + loop de feedback | Polimento técnico C5/C4 — não bloqueia submissão | 🔵 Fora do escopo desta entrega |

Evidência da auditoria: `screenshots/glm52-tasklist-bugs.png`

## Reconciliação final 138d + 68% (Opus 4.8 High) — 2026-06-19

Após a auditoria acima, fechei TODA a inconsistência numérica (código × docs × evidências) rodando o código para obter os números reais — sem reusar números de iterações antigas.

**Números reais (código atual, rodados, não chutados):**
- **Stale (`days_open > 138d`): 1.291 de 2.089 abertos = 61,8%** (o antigo "37%/171d" era de iteração descartada).
- **Max `days_open` no top-10 Foco Agora: 94d** (< 138 por construção — o "168" da evidência velha era impossível com o código atual; stale é rebaixado a Baixa Prioridade).
- **Sem conta: 1.425 / 2.089 = 68,2%** dos abertos (não 16% sobre 8.800 — Won/Lost têm conta 100%, o buraco é só nos abertos).
- Brief do dia **não** repete "conta não atribuída" (deals sem conta são excluídos do brief).

**O que foi alinhado:**
- `main.py` (sidebar Saúde): `total_deals` → `open_deals` no % sem conta (app não mostra mais 16% num card e 68% noutro).
- `config.py`: comentário órfão "48% passam de 171d" corrigido para o limiar vigente (138d / 61,8%).
- `decisoes.md` (D2 e D4), `README.md`, `PLANO-DO-PROJETO.md`, `branding/UI-UX.md`, `SUBMISSION.md`: todos os "3×mediana (171d)", "37%", "16% sem conta" e "teto dinâmico p90 dos abertos" reescritos para a lógica vigente (`STALE_DAYS=138d`, sino ancorada nos Won, 68% dos abertos).
- Nova migração **`0005_health_sem_conta_abertos.sql`**: `deals_sem_conta` agora filtra por abertos (numerador e denominador no mesmo universo).
- `score-distribuicao.txt` regenerado por um gerador versionado (`notebooks/score_distribuicao.py`) — reprodutível, não mais script inline perdido.

**Bug extra encontrado e corrigido:** `seed.py` imprimia o painel de saúde com labels embaralhados (`total=2017-12-31 abertos=8800…`) porque a migração 0004 inseriu `as_of_date` como 1ª coluna e o `SELECT *` posicional não foi atualizado. Trocado por colunas explícitas → `total=8800 abertos=2089 sem_conta=1425 ciclo_won=52d`.

**Validação:** `make test` → **31 passed**; `score-distribuicao.txt` confirma `is_stale > 138d` (sem "171"/"37%"), `max top-10 = 94 < 138`, brief sem "não atribuída". Screenshots da tela Saúde recapturados com o número vigente (68% sobre abertos).

## Pós-auditoria: red flags documentais + teto de qualidade (Opus 4.8 High) — 2026-06-19

Fechei os red flags restantes apontados pelo avaliador e subi o teto de código:

**Inconsistências documentais (red flags):**
- **`PLANO-DO-PROJETO.md` §6C** ainda descrevia a urgência como **monotônica** (≤57 ok / 57-88 alerta / >88 crítico) — modelo antigo. O código usa **curva sino** (esquentando 0→57 / platô 57→88 / decai 88→138 / piso além). Reescrito o §6C, a linha-resumo (§ tabela) e o exemplo de explainability (o "64d passando do ciclo" virou "64d na janela ideal", que é o correto).
- **Contagem de testes:** README, process-log e SUBMISSION diziam "25 testes"; a execução real é **28**. Alinhados todos (4 ocorrências).
- **`tela-saude.png`** mostrava 16% (denominador velho) e o próprio process-log admitia "foto velha" — entregava o flagrante. Foto recapturada com 68%; auto-acusação removida do log.

**Teto de qualidade (código):**
- **Modularização (`main.py` 653 → 148 linhas):** extraí as 3 telas para **`app/views.py`** (`view_foco` / `view_time` / `view_saude`), cada uma recebendo dados por **parâmetro explícito tipado** (DataFrame filtrado, health, outcome) em vez de globais. `main.py` ficou só com setup + sidebar + dispatch. Validado: boot HTTP 200 + `AppTest` renderiza as 3 views sem exceção.
- **Display = mecanismo no breakdown:** o card mostrava "fecha 70%" mas os **pontos** derivam de `percentile_rank(P)` — display ≠ mecanismo. Agora mostra **"fecha 70% · top 4%"** (o percentil real que gera os pontos), idem para tamanho do deal ("top 6%"). O vendedor entende por que 70% rende 43 pontos: é o rank vs o time, não o % absoluto.

**Validação:** `make test` → **31 passed**; boot real **HTTP 200**; `AppTest` das 3 views sem exceção.

## Documento de redesenho de processo (Opus 4.8 High) — 2026-06-20

Criei `docs/REDESENHO-DE-PROCESSO.md` (1–2 páginas, linguagem de negócio) e linkei na lista de docs do topo do `README.md`. Objetivo: mostrar que pensamos **além da ferramenta** — em como o time de vendas passa a operar (As-Is → To-Be por papel, mudanças na origem do CRM, papéis/responsabilidades, métricas de sucesso, riscos de adoção). O app Foco segue como a estrela; este é o complemento de rotina.

Todos os números saem das fontes do projeto, sem inventar e **consistentes** com o que já estava escrito (checados em `decisoes.md`, `GUIA-DO-PRODUTO.md`, `process-log/execucoes/`): 61,8% stale (1.291/2.089, >138d), 68% sem conta (1.425/2.089), base 63,2%, spread vendedor 55–70%, receita em risco R$ 302.340 (88–138d). Só documentação — nenhuma mudança de código, scoring, pesos, 138d ou denominador 68%.

## Brief do dia humano e opinativo (Opus 4.8 High) — 2026-06-20

O brief (`brief_do_dia`, `solution/scoring/model.py` — alimenta o download .txt) era uma concatenação que parecia automática: `"GTX Plus Pro com Hatfan (score 67); GTX Plus Pro com Zathunicon (score 67)..."` — nome + score, sem dizer *por que* cada deal é prioridade.

**O que mudou (só o TEXTO — scoring/pesos/138d/68% intactos):**
- Abertura humana: `"Bom dia, {nome}. Você tem N deals quentes pra atacar hoje — comece por estes:"`.
- 3–5 must-acts **numerados**, um por linha, cada um liderando pelo **driver que MAIS pesa naquele deal** (lido dos `pontos` do breakdown real, não inventado):
  - urgência sob pressão (janela fechando, severity alerta/crítico) → lidera com a janela: *"a janela está fechando (120d)… Aja hoje."*;
  - senão, o maior contribuidor de pontos: tamanho → *"R$ 5.482, o maior ticket da sua lista"*; probabilidade → *"você fecha 65% dos seus deals neste perfil"*.
  - um driver secundário reforça no tom de conselho de gestor (*"…e você fecha 65%…"*).
- **Números 100% do deal real** (`P`, `sales_price`, `urgency_label`/`days_open`); se falta dado de um driver, ele não é mencionado.
- Mantido: exclui stale e sem conta, e o download em .txt.

**Validação:** `make test` → **31 passed** (2 novos nesta sessão: `test_brief_traz_motivo_por_driver` valida que cada must-act traz o driver — não só nome+score; `test_brief_driver_varia_por_deal` valida que deals diferentes lideram por drivers diferentes). Teste antigo `test_brief_retorna_top_n` atualizado (`startswith("Bom dia, …")`).

## Reprodutibilidade + organização do app (Opus 4.8 High) — 2026-06-20

Endereçados 3 pontos de estrutura encontrados na análise:
- **Dependências pinadas:** `requirements.txt` saiu de `>=` (pandas>=2.0, streamlit>=1.30, pytest>=7.0) para **`==`** nas versões do ambiente validado (`pandas==2.3.3`, `streamlit==1.50.0`, `pytest==8.4.2`). Reprodutibilidade não depende de release futuro.
- **Type hints completos no app:** `app/views.py` já saíra tipado da modularização; completei as anotações de parâmetro e retorno nos componentes do tema e nas funções de setup do `main.py` (`get_data() -> tuple[pd.DataFrame, dict, dict]`). Tipagem consistente do core ao app.
- **`app/theme.py` (836 linhas) quebrado em pacote `app/theme/`** por responsabilidade: `tokens.py` (paleta/estilos), `styles.py` (CSS + injeção), `components.py` (HTML dos cards/breakdown/brief/funil), `__init__.py` (façade que reexporta — `from app.theme import X` inalterado). **Aparência idêntica provada por hash:** SHA-256 do `CSS` e dos renders dos componentes **byte-idênticos** antes/depois.

**Validação:** `make test` → **31 passed**; boot real **HTTP 200**; golden-hash CSS+componentes idêntico.

## Seção de diagnóstico de negócio no README (Opus 4.8 High) — 2026-06-20

Adicionei uma seção curta **"Diagnóstico de negócio"** logo após a intro do `README.md` (antes de "Rodar" e da explicação da solução), em narrativa problema-primeiro, para deixar explícito que entendemos o *problema* antes de mostrar a solução. Documentação apenas — **nenhuma mudança de código** (scoring, pesos, threshold 138d e denominador 68% intactos e já validados). Duas ideias, ambas com números das nossas fontes (`decisoes.md` D4/V6, `execucoes/score-distribuicao.txt`), sem inventar nada:
- **Priorização = duas perguntas, não uma nota:** "Vale a pena?" (o Score) vs "Dá pra trabalhar?" (viabilidade — stale >138d ou sem conta). Tornei visível que cruzar esses dois eixos foi **decisão de design**, não efeito colateral das regras de tier (por isso score-alto-mas-morto → Baixa Prioridade; sem conta → fora do brief).
- **Causa-raiz do pipeline inflado:** priorização "no feeling" + ninguém limpa o morto → inchaço que se realimenta. Quantificado: **61,8% (1.291/2.089) stale** e **68% (1.425/2.089) sem conta**. Alinhado com a abertura do `PLANO-DO-PROJETO.md` §1 ("no feeling", custo duplo) para não divergir.

## Correções aplicadas pelo GLM 5.2 (OpenCode) — 2026-06-19

Além da calibração de urgência, o GLM 5.2 identificou e corrigiu um segundo bug:

**Filtro Regional ignorado na Saúde (`view_saude()` lia `outcome` global sem aplicar `selected_region`)**
- Selecionar Oeste/Centro/Leste na sidebar agora filtra **todos** os dados do scoreboard: KPIs, funil, breakdown por produto e ranking de vendedores refletem só a regional escolhida
- A tabela "Por regional" desaparece quando uma regional específica está ativa (redundante no contexto)
- A caption exibe a regional selecionada como contexto
- "Todas" mantém a visão global com comparativo entre as 3 regionais
- Evidência: `screenshots/glm52-fix-regional-saude.png`

## Onde a IA errou e como corrigi (o julgamento humano)
- **H2 refutada pelos dados:** eu apostei que produto/setor/região diferenciariam o win-rate. A EDA mostrou spread <5pp — só o **vendedor** tem sinal (15pp). Decisão: **descartar produto/setor/região** e não inflar o modelo com ruído. A IA "colando o brief" pesaria todas as features igualmente; o valor aqui foi **testar e rejeitar** com evidência. (`decisoes.md` D1)
- **Bug do `days_open`:** a primeira versão da view calculava a idade do deal com `julianday('now')`. Como o dataset é histórico (~2017), **todo deal aparecia com 3.000+ dias** e a urgência saturava (tudo "crítico"). Percebi ao inspecionar o top-3 do score (3199 dias). Corrigi ancorando à **última data do dataset** (`MAX(close_date)`) → `days_open` 9–423d. (`decisoes.md` V7)
- **P contava duas vezes:** ao revisar o scoring, vi que o componente de valor usava `P × sales_price` — com a probabilidade já tendo componente próprio, isso fazia P pesar duas vezes e contrariava os pesos do config. Corrigi: valor = **tamanho do deal puro**; `expected_value` virou métrica informativa (monetização de risco), fora do score. Teste de regressão `test_value_independe_de_P`.
- **Limiar de "deal morto" mal calibrado:** o primeiro limiar (p90 = 106d) marcava 69% do pipeline como morto. Recalibrei para **`WON_MAX_DAYS = 138d`** (nenhum deal Won na história passou disso — dado-driven, sem chute). Versão anterior usava 3× mediana (171d), substituída após análise GLM 5.2. (`decisoes.md` D4)
- **Breakdown divergindo do score:** o score era `round(soma exata)` e o breakdown somava parcelas arredondadas — divergiam em casos de borda. Passei a **derivar o score da soma das parcelas do breakdown**: a invariante "soma == score" passou a valer por construção (verificada nos 2.089 deals).
- **UI gerada veio não-finalizada (refino visual com Codex):** a interface entregue **não subia** — a função `breakdown_html` tinha ficado **sem o `def`** (o corpo virou código órfão depois do `return` de `kanban_head_html`) e o `main.py` a importava → `ImportError` no boot. O `config.toml` ainda apontava para a paleta do tema antigo (roxo) em vez do indigo da marca, e telas além do "Foco do Dia" ficaram incompletas no padrão visual novo. Corrigi o `def`, alinhei o `config.toml`/tema ao `BRANDING.md`, validei o **boot real (HTTP 200) + a suíte de testes** e finalizei as telas. Lição: **UI gerada por IA exige checagem de import/boot e cobertura de todas as telas**, não só da tela principal.

## O que adicionei que a IA sozinha não faria
- Rejeição **empírica** de features óbvias (spread medido, não assumido).
- Thresholds de aging derivados do **ciclo real** (57/88d), não chutados.
- Detecção do join quebrado (`GTXPro`) e do buraco de RevOps (**68% dos abertos sem conta**) **antes** de modelar.
- Transformei o app de "mostra dados" em **ferramenta de decisão**: brief do dia, receita em risco em R$, seção "Revisar/Descartar" e camada de ação persistida.

## Evidências
- `execucoes/eda-output.txt` — EDA (sinal por dimensão, ciclo, higiene)
- `execucoes/install-migrate-seed.txt` — instalação do zero (counts 7/85/35/8800)
- `execucoes/score-distribuicao.txt` — distribuição dos scores + invariante breakdown==score
- `execucoes/pytest.txt` — 31 testes
- `execucoes/app-smoke-test.txt` — as 3 views + clique de ação persistido
- `screenshots/tela-foco-lista.png` — Foco do Dia · Lista (cards com badge ⚠ sem conta, ação por deal)
- `screenshots/tela-foco-kanban.png` — Foco do Dia · Kanban (3 colunas por tier, cards compactos)
- `screenshots/tela-foco-brief.png` — Brief do dia expandido (must-acts numerados liderados pelo **motivo opinativo** — driver dominante: ticket / win-rate / janela — + ação por linha e badge de tier; mesma fonte do brief `.txt`)
- `screenshots/tela-foco-breakdown.png` — "Por que esse score?" expandido (fator a fator, com **percentil "· top 75% / top 6%"** — display = mecanismo — e badge ⚠ sem conta no card)
- `screenshots/tela-time.png` — Visão Time (rep cards + botão "Ver deals →" drill-down, R$ 54.467 em risco)
- `screenshots/tela-time-tabela.png` — Time · tabela completa (Foco Agora / pipeline / em risco / revisar por vendedor)
- `screenshots/tela-saude.png` — Saúde · Higiene no topo (2.089 deals, **68% dos abertos sem conta**, R$ 302.340 em risco, breakdown sem conta por vendedor)
- `screenshots/tela-saude-scoreboard.png` — Saúde · scoreboard histórico (conversão 63,2%, R$ 10 mi, funil, por produto/regional, ranking)
- `screenshots/claude-design-interface.png` — Claude Opus 4.8 prototipando a interface
- `screenshots/opencode-glm52-validacao.png` — GLM 5.2 validando boot + fixes
- `screenshots/glm52-analise-calculos.png` — GLM 5.2 revisando calibração de urgência
- `screenshots/glm52-auditoria-pipeline.png` — GLM 5.2 auditoria das métricas (8800 registros)
- `screenshots/glm52-fix-regional-saude.png` — GLM 5.2 corrigindo filtro Regional em Saúde
- `screenshots/codex55-polish-visual.png` — Codex 5.5 High aplicando polish visual

---

## Brief visual e .txt unificados numa fonte única — 2026-06-20

O brief de **texto** (download .txt) já era opinativo — must-acts numerados, cada um liderado pelo **driver dominante** do deal (urgência / tamanho / win-rate). O **painel visual** da tela Foco do Dia, porém, ainda mostrava chips mecânicos (`tier · valor esperado · status · ação`). Dois lugares contando histórias diferentes — risco real de divergirem depois.

**Correção (sem tocar em scoring, pesos, 138d nem denominador 68% — só renderização):**
- Extraí `brief_must_acts(df, agent, n, exclude)` em `solution/scoring/model.py` como **fonte única**: devolve `{first, count, items[]}`, cada item com deal + motivo opinativo (driver dominante) + ação já resolvidos.
- `brief_do_dia` (.txt) e `brief_panel_html` (painel HTML) passaram a **consumir a mesma fonte** — o .txt renderiza em texto, o painel estiliza em HTML. Mesma lógica, dois formatos: não há como divergirem.
- Saída do `.txt` preservada byte-a-byte (refatoração pura); os testes existentes do brief continuam válidos.
- O painel agora abre com a saudação (nome + N deals quentes, igual ao .txt) e cada item lidera pelo **motivo** opinativo, mantendo o badge de tier (🔥/⭐/⏳) como elemento visual. Chips mecânicos e o CSS órfão (`.brief-meta`/`.brief-chip`) removidos.
- Teste novo `test_brief_txt_e_painel_mesma_fonte`: garante que painel e .txt têm o mesmo nº de itens e os mesmos deal+motivo+ação (trava anti-divergência). Suíte: **31 passed**.
- Validação: **boot real HTTP 200** + render do painel com dados reais (greeting + motivo + badge, sem chips).

> ✅ **Recaptura feita:** `screenshots/tela-foco-brief.png` atualizado com o painel opinativo novo (Anna Snelling, 5 deals — motivo liderando por ticket/win-rate, badge de tier, sem chips). Legendas atualizadas aqui e no `README.md`.

---

## Reconciliação de evidência — 2026-06-20

O código avançou (brief opinativo + teste anti-divergência → 31 testes) mas os artefatos de evidência e a contagem de testes nos docs ficaram para trás, criando contradição evidência↔código. Passada final para zerar isso — **sem tocar em scoring/pesos/138d/68%**:

- **`score-distribuicao.txt` regenerado** pelo gerador atual (`notebooks/score_distribuicao.py`): a linha do `Brief (...)` agora sai no **formato opinativo** (must-acts numerados com driver dominante), não mais `"nome (score 67)"`. De quebra, corrigi o `dest` do gerador, que ainda apontava para o diretório antigo `evidencias/` (inexistente pós-reorganização) em vez de `process-log/execucoes/`.
- **`pytest.txt` regenerado** com a saída crua atual (`-o addopts=` para o cabeçalho completo): **31 passed**, `collected 31 items`.
- **`install-migrate-seed.txt` regenerado** pelo run real (pip + migrate --reset + seed).
- **Contagem de testes normalizada para 31** em todo o documento: `README.md` (Executive Summary + Process Log), `docs/GUIA-DO-PRODUTO.md` (como rodar + árvore), `solution/requirements.txt` (comentário do env), `app-smoke-test.txt` (resumo), o índice de Evidências acima e também as linhas `**Validação:** make test → …` das sessões anteriores. A suíte atual tem 31 testes — deixei **todas as menções em 31** para o leitor não tropeçar em contagens divergentes ao longo do log; essa é a referência única.
- **Novo alvo `make evidence`** (em `solution/Makefile`): regenera os três `.txt` determinísticos num comando só, pra essa defasagem não voltar a acontecer. Documentado no `GUIA-DO-PRODUTO.md`. (`app-smoke-test.txt` continua manual — é narrativa interativa das telas.) Também adicionei `PYTHON ?= python` ao Makefile (permite `make … PYTHON=python3` em ambientes sem `python` no PATH).
- **Placeholders de "Demo ao vivo (a preencher após o deploy)"** trocados por uma frase limpa de que o app roda local em 3 comandos (`README.md` ×2, `GUIA` ×1, banner do topo deste log) — sem checkbox vazio nem "a preencher", que liam como inacabado. Se eu publicar no Streamlit Cloud depois, aí incluo a URL. **(Atualização do mesmo dia: app publicado no Streamlit Cloud — URL ao vivo adicionada no README, GUIA e banner deste log.)**

**Validação:** `make test` → **31 passed**; `make evidence` regenera os três artefatos sem erro; nenhum `score 67` em `score-distribuicao.txt`; nenhuma contagem de teste defasada apresentada como estado atual.
