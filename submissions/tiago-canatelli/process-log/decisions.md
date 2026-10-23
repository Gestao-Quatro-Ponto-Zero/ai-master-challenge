# Decisões

### Lógica de negócio no Postgres (gold/api)
- **Opções:** calcular KPIs no Python, no React ou no banco.
- **Escolha:** views e funções no banco.
- **Motivo:** painel, Edge Function e MCP mostram o mesmo número para a mesma pergunta.

### Prompts do assistente no banco (`app.prompt_templates`)
- **Opções:** prompts fixos no código / arquivo / tabela.
- **Escolha:** tabela com versões.
- **Motivo:** editáveis pelo painel e expostos como prompts MCP sem redeploy.

### Corte de escopo pré-definido
- **Motivo:** o escopo (~8h) passa do budget de 4–6h do desafio.
- **Regra:** cortar modelo → MCP → catálogo, nessa ordem. Diagnóstico e relatório não encolhem.

### Monorepo + deploy no Render
- **Pedido:** trabalhar como monorepo e fazer os deploys no Render.
- **Escolha:** raiz do monorepo em `submissions/tiago-canatelli/` (regra da PR); `apps/dashboard` (static site), `apps/api` (FastAPI com `/assistant` + `/mcp`), `packages/ravenlake` (cron), `packages/churn_core` (compartilhado); Blueprint `render.yaml`.
- **Consequência:** a Edge Function do Supabase prevista antes foi substituída pela API Python no Render — backend todo em uma linguagem, e assistente e MCP num serviço só.

### Fonte de dados: Kaggle MCP no pipeline
- **Opções:** download manual · API REST do Kaggle com token · MCP remoto do Kaggle.
- **Escolha:** MCP do Kaggle (`get_dataset_info` + `download_dataset`), com fonte local como fallback.
- **Motivo:** funciona sem credencial; permite sincronização incremental por versão; REST exige token.
- **Ressalva:** o dataset está na versão 1 desde 2025-07-21 — a sincronização é demonstrativa.

### Skill de React/UX, multi-LLM, MCP aberto e RAG
- **Pedido:** melhor experiência no painel, conexão com Claude pelo front, MCP para Claude e outras IAs, chaves de outros LLMs e RAG nas análises.
- **Escolhas:** skill `react-ux-engineer` (shadcn/ui); camada `churn_core.llm` com adaptadores (Anthropic padrão + OpenAI, Gemini, OpenAI-compatível); MCP streamable HTTP documentado por cliente; RAG com pgvector + full-text (busca híbrida) no próprio Supabase.
- **Regra de ouro do RAG:** números sempre das tools (ao vivo); RAG traz contexto e explicação — evita a IA citar número velho de um documento.
- **Custo:** aumenta o escopo; entrou no topo da ordem de cortes.

### Churn = `churn_events` (fonte de verdade)
- **Opções:** `accounts.churn_flag` · `churn_events` · `end_date`/flag da assinatura.
- **Escolha (confirmada pelo Tiago):** `churn_events`; churn é evento recorrente, com reativação.
- **Motivo:** as três fontes discordam (277 contas com evento e flag `False`; 35 com flag `True` sem evento; só 6 de 600 churns coincidem com fim de assinatura). Os eventos têm data, motivo e refund — é a única fonte que permite análise temporal.
- **Consequência:** KPIs de receita dependem de uma regra de MRR vigente ainda a validar; flags viram achado de qualidade no relatório.

### Perfis de análise por área, análise 360 e três camadas de painel
- **Pedido:** skills e RAGs por perfil para análise 360, cobrindo todas as áreas, com perfis padrão personalizáveis; painéis por persona de cliente, por persona analista e um geral.
- **Escolhas:** 8 perfis de fábrica (Executivo, Financeiro, CS, Suporte, Produto, Marketing, Vendas, Dados) em arquivos .md no formato SKILL.md, carregados em `app.analysis_profiles` e editáveis/versionáveis no painel; RAG por perfil via `profile_slugs`; endpoint 360 que roda as lentes em paralelo e sintetiza concordâncias e **discordâncias**; 7 personas de cliente por regra explícita, validadas contra clusterização.
- **Também aceito:** KPIs de concentração de perda e intervalo até reativação; taxa de salvamento em 3 cenários (10/20/30%).
- **Separação importante:** persona analista (quem pergunta) ≠ persona de cliente (sobre quem).

### Tudo no Supabase SaaS, sem Docker/local
- **Pedido:** testes e demais itens sempre no Supabase SaaS; nada rodando local via Docker.
- **Escolha:** um ambiente só (`G4-Analysys`) para desenvolvimento, testes e produção; CLI do Supabase só para o projeto remoto (`link`, `db push --linked`, `gen types --project-id`).
- **Como os testes não sujam os dados:** transação com rollback por padrão; testes com commit usam `run_id` de teste e limpeza automática; testes de KPI só leem.
- **Risco aceito:** não há banco para ensaiar migrations → migration destrutiva só com confirmação explícita. O plano free pausa o projeto após inatividade — reativar antes de rodar.

### MRR vigente = assinatura ativa mais recente
- **Opções:** somar todas as assinaturas ativas × usar a mais recente.
- **Escolha:** a mais recente.
- **Motivo:** o preço por licença é fixo (19 / 49 / 199 US$). Somando, a mediana seria 225 licenças por conta, contra 15 no cadastro, o que é implausível. Com a mais recente, a mediana é 25 licenças e o MRR vigente é US$ 1,04 mi.

### Não recomendar ação por canal nem por indústria
- **Contexto:** `organic` apareceu com p = 0,025 e o "plano atual" com p < 0,001.
- **Escolha:** descartar os dois. Canal não sobrevive à correção de Bonferroni (6 testes). O "plano atual" é a assinatura mais recente, muitas vezes posterior ao churn, ou seja, causalidade reversa. Pelo plano **na data do churn**, o mix de churn (35/37/32%) é quase igual ao mix ativo (33/32/35%).

### Gold com lógica no banco e o modelo de risco em SQL
- **Opções:** score em Python (statsmodels) gravado no banco × score em SQL.
- **Escolha:** SQL (`gold.refresh_risk_scores`): é a taxa empírica do último trimestre por faixa de tempo de casa × churn anterior, com encolhimento (k = 30 contas-mês) nas células pequenas. Isso equivale ao Poisson do diagnóstico, cujos preditores são categóricos.
- **Validação:** MRR em risco de 90 dias de US$ 333.467 no SQL contra US$ 334.121 no Python (0,2%). O pipeline e o cron não precisam de statsmodels.

### Materializar dimensões por desempenho
- **Problema:** funções SQL com `search_path` fixo não são incorporadas na consulta pelo Postgres. As views chamavam `as_of_date()` e `is_churned_on()` linha a linha e estouravam o timeout.
- **Escolha:** `dim_account` e `dim_customer_persona` viraram materialized views, atualizadas em `gold.refresh()`. A data de referência é calculada uma vez por consulta.

### Personas: "reincidente" = 2 ou mais churns
- **Motivo:** 87% dos churns são seguidos de volta, então "já churnou 1 vez" não distingue ninguém. Com 2 ou mais churns, ficam 127 contas.
- **Ressalva:** "âncora Enterprise" (22 contas) e "Pro anual" (24) ficam abaixo do mínimo de 30 da skill. Foram mantidas porque Âncora é 14% do MRR; isso vai para as limitações.

### KPIs de receita com ressalva explícita
- **Problema:** mesmo corrigido, o GRR mensal fica em torno de 60%, porque o "MRR vigente" oscila quando a conta troca de assinatura.
- **Escolha:** manter as views com a ressalva no comentário e usar logos, hazard e coortes como KPIs principais no painel e no relatório.

### CI/CD: deploy automático pelo git com filtros por pasta
- **Configuração no Render:** os dois serviços acompanham o fork, na branch `submission/tiago-canatelli`, com `autoDeploy: yes` (trigger: commit).
- **Filtros de build:** a API ignora docs, process-log, report, analysis, scripts, supabase, dashboard e .claude (`ignoredPaths`, caminhos a partir da raiz do repositório). O dashboard só redeploya quando muda `submissions/tiago-canatelli/apps/dashboard/**`.
- **Motivo:** antes dos filtros, cada commit de documentação redeployava a API (3 deploys inúteis no plano gratuito).
- **Prova:** o push `1b110ce` (só documentação) não disparou deploy. O push `85ccf9c` (API) disparou, e o `/health` de produção passou a mostrar `commit: 85ccf9c`. As tentativas com `paths` (relativos ao rootDir e depois à raiz) não filtraram a API e foram registradas no journal.

### Ingestão contínua: pg_cron do Supabase → API no Render
- **Pedido:** deixar a ingestão rodando no Render, alimentando o banco, e ver isso no painel.
- **Opções:** cron job do Render (pago, recusado: "new paid services not allowed") · GitHub Actions (mexeria fora da pasta da submissão) · **pg_cron + pg_net do Supabase chamando a API**.
- **Escolha:** a terceira. Custo zero; a chamada a cada 15 min também mantém o serviço gratuito do Render acordado. O token fica no Supabase Vault.
- **Prova:** o run agendado saiu como `trigger = cron` (`skipped`: Kaggle sem versão nova), e o `cron.job_run_details` mostrou `succeeded` às 14:15. A ingestão forçada pelo endpoint rodou completa (silver, DQ, gold com 432 contas, catálogo).
