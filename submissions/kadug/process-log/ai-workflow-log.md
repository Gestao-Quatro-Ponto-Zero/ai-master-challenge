# AI Workflow Log

## Sessao 1 - Entendimento e Arquitetura Inicial

**Data:** 2026-06-28

### Objetivo

Entender as regras do challenge 001 e transformar o direcionamento inicial em arquitetura e plano de execucao.

### Decisoes tomadas

- Challenge escolhido: `data-001-churn`.
- Entrega principal: diagnostico executivo de churn.
- Arquitetura principal: Analytics Core First + Presentation Adapters.
- Dashboard minimo: camada de apresentacao obrigatoria da nossa entrega, consumindo exports prontos.
- Estrategia de produto:
  - cruzar todas as tabelas;
  - transformar dados em narrativas;
  - transformar narrativas em acoes;
  - escrever para stakeholders nao tecnicos.

### Uso de IA

Usei Codex/GPT-5 para:

- ler o README principal, o README do challenge e o guia de submissao;
- identificar os criterios de qualidade;
- decompor a entrega em plano de 4h;
- desenhar uma arquitetura pragmaticamente alinhada ao timebox.

### Julgamento humano aplicado

- O dashboard foi classificado como diferencial, nao como dependencia.
- A analise e o process log foram definidos como itens nao cortaveis.
- A arquitetura favorece contratos simples para integracao futura com hub de ferramentas.
- A estrategia de produto foi separada da arquitetura tecnica para manter clareza entre stack, narrativa e acao.
- A decisao inicial de Angular com Worker foi revisada: Angular fica como possibilidade de produto futuro, nao como stack do challenge.
- Commits por checkpoint foram definidos como evidencia complementar de processo, sem tratar git como cronometro formal.

### Proximas iteracoes

1. Baixar dataset do Kaggle.
2. Validar schema real dos 5 CSVs.
3. Construir primeira camada analitica.
4. Fazer commits de checkpoint usando `git add -f` para a pasta ignorada `submissions/`.
5. Atualizar este log com erros, correcoes e prompts relevantes.

## Sessao 2 - Critiques Externos e Revisao Arquitetural

**Data:** 2026-06-28

### Entradas

- Critique Sonnet Max: `C:\Users\kadug\Downloads\critique-spec-churn.md`
- Critique Opus 4.6 Max: `C:\Users\kadug\Downloads\critique-spec-opus.antgvy.md`

### Decisoes aceitas

- Manter `Analytics Core First + Presentation Adapters`.
- Trocar dashboard Angular por Streamlit.
- Tratar exports como fonte da verdade.
- Adicionar `arr_at_risk` e `segment_size` em `risk_segments`.
- Criar `priority_accounts` como watchlist operacional.
- Criar `data_quality_report.md` antes dos findings.
- Incluir nota de causalidade por finding.
- Separar churn voluntario vs. involuntario quando o dataset permitir.
- Incluir comparacoes churners vs. non-churners com teste estatistico simples quando aplicavel.

### Decisoes rejeitadas ou rebaixadas

- Angular fica fora do escopo do challenge atual. Pode voltar como produto futuro, mas nao vale o custo no timebox.
- Modelo preditivo complexo nao sera prioridade. Se houver score, sera baseado em regras auditaveis.
- NLP sofisticado no feedback textual sera feito apenas se sobrar tempo; reason codes e temas basicos vem primeiro.

### Julgamento humano aplicado

Os dois critiques concordaram que a arquitetura estava correta, mas que a camada de apresentacao estava cara demais. A decisao final preserva a maturidade da arquitetura e troca a tecnologia de dashboard para reduzir risco de entrega.

## Sessao 3 - Contrato de Dados, Camada Limpa e Preflight

**Data:** 2026-06-28

### Objetivo

Transformar o `data_quality_report.md` em contrato executavel para os cinco CSVs RavenStack, sem modificar os dados brutos.

### Decisoes tomadas

- Criar `solution/analysis/build_exports.py` como script unico e reproduzivel.
- Gerar camada limpa em `solution/analysis/clean/`.
- Criar `feature_usage_row_id` porque `usage_id` tem duplicidades.
- Gerar `usage_in_subscription_window_flag` a partir de `usage_date`, `start_date` e `end_date`.
- Preservar `account_churn_flag` e `has_churn_event` como labels separados.
- Copiar `data_quality_report.md` para `solution/analysis/data_quality_report.md`.
- Registrar preflight de Python, Streamlit e pastas exigidas em `preflight_report.json`.

### Uso de IA

Usei Codex/GPT-5 para converter os requisitos do challenge e do DQ report em um pipeline auditavel, depois rodei uma revisao tecnica assistida por IA sobre schema, joins e flags de qualidade.

### Correcoes e julgamento humano

- O script foi mantido como fonte unica para evitar divergencia entre relatorio, exports e dashboard.
- A revisao tecnica passou em schema, integridade de joins e flags de qualidade.
- Os comandos globais `npm run lint`, `npm run typecheck` e `npm test` foram tentados, mas nao ha `package.json` em `C:\Projects\desafio-g4`; por isso, os gates npm nao sao aplicaveis a este workspace Python/Markdown.
- `python -m py_compile` falhou ao tentar gravar bytecode em `__pycache__` por permissao do Windows. A validacao de sintaxe foi refeita em memoria com `compile(...)`, sem depender de escrita de `.pyc`.

## Sessao 4 - Exports Canonicos e Score de Risco

**Data:** 2026-06-28

### Objetivo

Gerar os contratos canonicos que servem como fonte da verdade para report e dashboard.

### Artefatos gerados

- `account_health.csv/json`: 500 contas, uma linha por `account_id`.
- `risk_segments.csv/json`: 4 segmentos que somam 500 contas.
- `priority_accounts.csv/json`: 60 contas priorizadas por score, MRR em risco e sinais operacionais.
- `action_backlog.csv/json`: 58 acoes com dono, prioridade, esforco, confianca e gatilho.
- `executive_findings.csv/json`: 7 findings executivos com evidencia, interpretacao, decisao e rastreabilidade.
- `churner_comparison.csv/json`: comparativo auxiliar entre contas com e sem evento de churn.

### Uso de IA

Usei Codex/GPT-5 para implementar as agregacoes e rodei uma revisao de dados assistida por IA sobre contrato de export, risco de multiplicacao de linhas e score deterministico.

### Correcoes e julgamento humano

- A primeira revisao local identificou que um finding do backlog somava MRR por acao e duplicava exposicao financeira. Corrigi para reportar exposicao de portfolio sem dupla contagem.
- Adicionei `churner_comparison` para tornar os findings auditaveis sem recalcular metricas no relatorio.
- A revisao de dados passou: `account_health` tem 500 linhas e zero duplicidade de `account_id`; `risk_segments` soma 500; score e segmentos foram recomputados sem divergencias.

## Sessao 5 - Findings, Causalidade e Revisao Analitica

**Data:** 2026-06-28

### Objetivo

Transformar exports canonicos em findings executivos rastreaveis, respondendo causa, segmentos/contas em risco e acoes recomendadas.

### Uso de IA

Usei Codex/GPT-5 para gerar os primeiros findings e rodei uma revisao analitica assistida por IA antes da revisao de produto.

### Erros encontrados pela IA e correcoes aplicadas

- O primeiro export de `executive_findings` nao tinha campos explicitos suficientes para auditoria dos findings. Corrigi adicionando `evidence_summary`, `interpretation`, `owner_team`, `recommended_action`, `effort_size`, `expected_impact_metric`, `related_action_ids` e `false_causality_risk`.
- A comparacao churners vs non-churners cobria apenas `has_churn_event`. Corrigi `churner_comparison` para comparar tambem `account_churn_flag`.
- A contradicao "uso cresceu" estava coberta apenas por caveat de janela de assinatura. Corrigi criando `usage_growth_tests.csv/json`, com crescimento bruto vs crescimento valid-window por portfolio, segmento de risco, plano e labels de churn.
- A primeira tabela de causa candidata ranqueou qualidade de dados como top causa. Isso explica ambiguidade analitica, nao churn de cliente. Corrigi criando `root_cause_candidates.csv/json` com categoria de causa de negocio e rebaixando data quality para confiabilidade analitica.

### Julgamento humano aplicado

Mantive a causa raiz como candidata, nao como prova causal: "value-realization erosion before renewal". O plano recomendado e agir em Critical/High accounts e usar a cadencia de duas semanas para validar qual intervencao realmente muda risco de renovacao.

## Sessao 6 - Dashboard Streamlit como Presentation Adapter

**Data:** 2026-06-28

### Objetivo

Criar um dashboard minimo para stakeholders sem duplicar a logica analitica.

### Decisoes tomadas

- O app fica em `solution/dashboard/streamlit_app.py`.
- O dashboard le apenas exports em `solution/exports/`.
- A interface usa header executivo, KPIs, top findings, segmentos de risco, contas prioritarias, backlog e notas de data quality.
- O visual segue a direcao G4 adaptada: navy/off-white/gold, cards simples, tabelas densas e foco operacional.

### Validacoes executadas

- Import do app e carregamento dos exports: passou.
- Syntax check por `compile(...)`: passou.
- Smoke test local com Streamlit em job temporario: `http://localhost:8765` respondeu HTTP 200.
- Busca por `data/raw`, `merge(` e `groupby(` no dashboard: nao encontrada; o app nao recalcula joins nem score.

### Julgamento humano aplicado

Mantive o dashboard como camada de leitura e filtro, nao como ferramenta analitica. Isso preserva a fonte da verdade nos exports e evita que relatorio e UI discordem.
