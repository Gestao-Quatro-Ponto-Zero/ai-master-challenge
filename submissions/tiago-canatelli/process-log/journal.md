# Journal — Challenge 001

## 2026-10-23 · F0/F1 Setup e planejamento
- **Pedi à IA (Claude Code):** clonar o repositório, ler o challenge, guia e template, e planejar a execução com Supabase (data lake), painéis, MCP e skills.
- **A IA fez:** clonou o repo, leu os docs, verificou ferramentas locais (Python 3.14, Supabase CLI, gh), descobriu que o download do Kaggle exige autenticação e que o `.gitignore` ignora `submissions/`. Gerou um primeiro plano único.
- **Ajustei:** pedi a separação em plano de projeto (negócio) e plano técnico, e skills por papel (cientista de dados, business, engenharia Python), além de painel React de ingestão/catálogo e assistente com prompts editáveis.
- **Resultado:** `docs/01-plano-projeto.md`, `docs/02-plano-tecnico.md`, 4 skills em `.claude/skills/`.
- **Bloqueio:** criação do projeto Supabase `ravenstack-churn` falhou — limite de 2 projetos free ativos na organização.
- **Próximo:** liberar o Supabase, baixar dados, F2 (ingestão).

## 2026-10-23 · Validação da fonte de dados
- **Pedi à IA:** confirmar se o dataset do Kaggle é a base do projeto.
- **A IA fez:** abriu a página do dataset no navegador e leu o README do autor: schema completo, edge cases declarados (reativações, nulos, mudanças de plano, picos de beta), exigência de crédito ao autor e um notebook público sobre rejeição de 25.000 linhas.
- **Ajustei:** a skill do cientista de dados tinha nomes de colunas *supostos*; troquei pelo schema real e transformei os edge cases em checagens obrigatórias.

## 2026-10-23 · Download dos dados via MCP do Kaggle
- **Pedi à IA:** baixar o dataset pelo MCP remoto do Kaggle e avaliar sincronizar o Supabase por ele.
- **A IA fez:** testou o endpoint `https://www.kaggle.com/mcp` direto por JSON-RPC (76 tools; `download_dataset` funciona sem login e devolve URL assinada), baixou o zip para `datasets/kaggle-rivalytics/` e conferiu: 500 / 5.000 / 25.000 / 2.000 / 600 linhas, cabeçalhos iguais ao schema da skill. `get_dataset_info`: versão 1, atualizada em 2025-07-21.
- **Decisão:** o pipeline usa o Kaggle MCP como fonte, com checagem de versão + sha256 (ver `decisions.md`).
- **sha256:** accounts `348d8ba9…`, churn_events `6391c41d…`, feature_usage `c081da2b…`, subscriptions `dcf1d93c…`, support_tickets `ba000695…`.

## 2026-10-23 08:35–09:20 · F1 · Revisão das skills uma a uma
- **Pedi à IA:** revisar cada skill comigo antes de começar a execução.
- **A IA fez:** antes de apresentar cada skill, conferiu as regras nos CSVs: 77% do uso tem data anterior ao início da assinatura; as três definições de churn discordam; churn e assinaturas não se cruzam (só 6 de 600 churns coincidem com o fim de uma assinatura); `feedback_text` tem só 4 textos distintos; o churn por trimestre vai de 6 → 251.
- **Verifiquei / ajustei:**
  - escolhi `churn_events` como fonte de verdade;
  - pedi uma skill de React/UX, multi-LLM, MCP aberto para outras IAs e RAG;
  - pedi perfis de análise por área com RAG próprio e análise 360, além de painéis geral, por área e por persona de cliente;
  - decidi que tudo roda no Supabase SaaS, sem Docker.
- **Resultado:** 5 skills revisadas. Commits `3701de5`, `9ecaebe`, `f4557e8`, `4da3719`, `d0defc4`.
- **Próximo:** F2 — migrations e ingestão no Supabase.

## 2026-10-23 09:30–10:18 · F2 · Migrations e pipeline
- **Pedi à IA:** começar a F2 com migrations e ingestão no Supabase G4-Analysys.
- **A IA fez:**
  - inspecionou os formatos reais dos CSVs;
  - escreveu e aplicou 5 migrations: schemas, `ops`, bronze, silver com `silver.refresh`, qualidade (`ops.run_dq`, 16 checagens) e catálogo (`ops.refresh_catalog`);
  - validou a camada SQL com um teste de fumaça desfeito no final (`raise exception` dentro de um bloco `DO`, que força rollback): rejeição de linhas inválidas, colisão de `usage_id`, CSAT nulo, checagens e catálogo;
  - criou o pacote `ravenlake`: fonte Kaggle via SDK do MCP, upload para o bucket `raw`, COPY em lotes para o bronze e progresso em `ops.ingestion_steps`.
- **Verifiquei / ajustei:**
  - os `usage_id` duplicados (21) **não** são linhas repetidas, são eventos diferentes com o mesmo id; ficam mantidos com sufixo `#n`;
  - o CSAT só tem notas 3, 4 e 5 (nenhuma 1 ou 2), o que virou uma checagem;
  - o SDK do MCP 2.3 mudou a API (`streamable_http_client`, `is_error`), e o código foi ajustado;
  - o `uv` não instalou pelo Homebrew; foi instalado pelo PyPI num ambiente virtual dedicado.
- **Resultado:** `ravenlake version` → 1 (Kaggle MCP ok); lint, mypy e testes passando; advisors só com INFO de RLS sem policy, o que é intencional porque o acesso virá pela camada `api`.
- **Próximo:** credenciais no `.env` → `ravenlake ingest`.

## 2026-10-23 10:20–10:43 · F2 · Primeira ingestão real
- **Pedi à IA:** rodar a ingestão completa depois de eu preencher o `.env`.
- **A IA fez:**
  - conferiu o `.env` sem expor segredos e pegou que a `DATABASE_URL` estava com a URL HTTP do projeto em vez da connection string do Postgres;
  - rodou `ravenlake ingest`: Kaggle MCP → 5 arquivos no bucket `raw` → 33.100 linhas no bronze (feature_usage em 5 lotes) → silver com 0 rejeitadas → 16 checagens → catálogo com 16 tabelas e 205 colunas, em 108 s;
  - conferiu os totais de controle do silver contra os CSVs;
  - rodou de novo para testar idempotência.
- **Verifiquei / ajustei:** os totais de controle batem com o CSV (MRR 11.338.747, uso 250.525, CSAT 4.678, refunds 8.652,25); o segundo run deu `skipped`, sem duplicar o bronze; os sha256 batem com os do download manual.
- **Resultado:** `docs/data-quality.md`. Run `3f3c24da` (success) e `f0133317` (skipped).
- **Próximo:** F3 — diagnóstico (hipóteses) sobre o silver.

## 2026-10-23 10:43–10:59 · F3 · Diagnóstico
- **Pedi à IA:** testar as hipóteses sobre o silver.
- **A IA fez:**
  - carregou o silver em pandas e testou H0–H7;
  - criou a H8 a partir do que os dados mostraram (taxa por conta subindo sem explicação por segmento);
  - separou os efeitos de calendário, tempo de casa e coorte (Poisson conta-mês + logit com controles);
  - consolidou tudo em `analysis/diagnostico.py`, que gera `results/diagnostico.md`, `numbers.json` e `risk_accounts.csv`.
- **Verifiquei / ajustei:**
  - cobrei correção para múltiplas comparações;
  - descartei o artefato do "plano atual";
  - separei calendário de coorte antes de chamar de causa;
  - deixei explícito que o mecanismo (onboarding) não está nos dados.
- **Resultado:** causa raiz em `process-log/hypotheses.md` (síntese) e 432 contas ativas com MRR em risco estimado em US$ 320 mil em 90 dias.
- **Próximo:** F4 — gold (views de KPI) + score de risco em `gold.risk_scores`.

## 2026-10-23 10:59–11:14 · F4 · Camada gold e score de risco
- **Pedi à IA:** views gold de KPI e `gold.risk_scores` no Supabase.
- **A IA fez:** 4 migrations de gold.
  - **Regras de base em SQL:** `as_of_date`, `is_churned_on` e `subscription_at`.
  - **Fatos:** `fct_churn_event` e `fct_account_month` (5.807 contas-mês).
  - **Dimensões:** `dim_account` e personas.
  - **13 views de KPI:** receita, hazard, coorte, segmento, concentração, tipo de churn, reativação, suporte, churn silencioso, uso, features, motivo × comportamento e personas.
  - **Score de risco** em SQL, além de `account_360` e `gold.refresh()`.

  O pipeline passou a atualizar o gold depois da qualidade, e o comando `ravenlake gold` foi criado.
- **Verifiquei / ajustei:**
  - os números do gold batem com o diagnóstico (hazard 46,5 / 8,3; 432 contas ativas; churn de coorte em 6 meses);
  - igualei o desempate de assinaturas entre Python e SQL, e agora o MRR bate exatamente;
  - corrigi o GRR com dupla contagem;
  - materializei as dimensões por desempenho;
  - registrei a H9 (reativação em 16 dias) como inconclusiva.
- **Resultado:**
  - 7 testes passando, 4 deles conferindo o gold contra os CSVs no Supabase;
  - advisors só com INFO de RLS, como esperado;
  - MRR em risco de 90 dias: US$ 333 mil (35% nas 20 primeiras contas).
- **Próximo:** F5 — camada `api`, painel React, assistente e MCP.

## 2026-10-23 11:25–12:36 · F5/F6 · API, painel, usuários por área, deploy e relatório
- **Pedi à IA:** fechar até 13–14h com deploy no Render. Depois pedi usuários com os perfis de cada área, a visão geral para todos e um admin com todas as visões.
- **A IA fez:**
  - **Banco:** camada `api` (views só leitura e `run_readonly_query` com bloqueios testados), prompts e perfis editáveis, e papéis e usuários (`app.roles`, `app.users`, código com hash PBKDF2).
  - **API e assistente:** FastAPI com assistente Claude (`claude-opus-5-5`, tool use) e MCP em `/mcp` com bearer.
  - **Painel React:** visão geral, fila de risco + 360, ingestão + qualidade + catálogo, e assistente. O login filtra as abas e a lente da IA pelo papel.
  - **Deploy:** criação dos serviços pela API do Render, depois o relatório do CEO e o README.
- **Verifiquei / ajustei:**
  - assistente testado de ponta a ponta (24 s, 2 tools, números corretos);
  - permissões testadas por papel (Suporte recebe 403 na fila de risco e nos dados e só vê o próprio prompt);
  - em produção: health ok, e login, dados e MCP com 401 sem credencial;
  - descobri que o host direto do Supabase é só IPv6 e que a senha tinha `#`, então gerei a URL do pooler com encoding;
  - recusei usar a chave do Render colada no chat e pedi que fosse para o `.env`;
  - recalculei no banco os impactos do relatório, que no rascunho eram estimados.
- **Resultado:** https://ravenstack-dashboard.onrender.com e https://ravenstack-api.onrender.com.

## 2026-10-23 12:40–13:00 · CI/CD no Render
- **Pedi à IA:** garantir o deploy automático pelo git nesta branch.
- **A IA fez:** confirmou pela API do Render que os dois serviços acompanham o fork, na branch `submission/tiago-canatelli`, com `autoDeploy` por commit (a API já tinha redeployado sozinha em 3 pushes). Depois configurou filtros de build e testou com pushes só de documentação.
- **Verifiquei / ajustei:** caminhos relativos ao `rootDir` não filtram, e os dois serviços redeployaram. Os caminhos relativos à raiz do repositório funcionam: o dashboard parou de redeployar por mudanças fora de `apps/dashboard`. O teste final da API é este próprio commit (só documentação).

- **Ajuste:** filtro da API trocado para `ignoredPaths` (docs, process-log, report, analysis, scripts, supabase, dashboard), nos dois formatos de caminho.
- **Resultado:** o push `1b110ce` (docs) não fez deploy; o `85ccf9c` (API) fez, e a produção mostra `commit: 85ccf9c` no `/health`.

## 2026-10-23 13:40–14:20 · Ingestão contínua no Render
- **Pedi à IA:** deixar a ingestão executando no Render, alimentando o banco, visível no painel.
- **A IA fez:**
  - `ravenlake` ganhou modo `--force` e um `runner` compartilhado;
  - API: `POST /ingest` (admin/Dados) e `POST /ingest/cron`, ambos em segundo plano com trava contra execuções simultâneas;
  - painel: botão "Executar ingestão agora", atualização a cada 3 s durante a execução e runs marcados como agendado ou manual;
  - agendador: pg_cron + pg_net a cada 15 min, com o token no Vault.
- **Verifiquei / ajustei:**
  - o job avulso e o cron do Render foram recusados por serem pagos, daí a troca de agendador;
  - o teste de reprocessamento revelou a FK `gold.risk_scores` → `silver.accounts`, que bloqueava o `TRUNCATE` (corrigida);
  - o primeiro disparo deu 401 porque o processo no ar tinha subido antes da variável nova; um redeploy resolveu;
  - o trigger saía como `manual` por uma substituição de texto que não aconteceu (corrigido).
- **Resultado:** o agendador roda sozinho (`succeeded` às 14:15) e os runs `cron` aparecem no painel.
