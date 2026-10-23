# Onde a IA errou e como corrigi

_(registrar em tempo real — skill `process-log-keeper`)_

### Schema assumido em vez de verificado
- **O que a IA fez:** a primeira versão da skill de dados listou colunas e chaves deduzidas do README do challenge (ex.: "canal de aquisição", "CSAT de pesquisa").
- **Como percebi:** ao conferir o README original do dataset no Kaggle — os nomes reais são `referral_source`, `satisfaction_score` nos tickets, `is_reactivation` etc.
- **Correção:** skill atualizada com o schema real e com a regra "inspecionar antes de usar".
- **Lição:** documentação de segunda mão não é fonte; ir na origem.

### RAG sobre feedback de clientes proposto sem olhar o dado
- **O que a IA fez:** planejou clusterizar `feedback_text` por tema no RAG para testar a H4.
- **Como percebi:** ao validar os KPIs nos CSVs — só existem 4 textos de feedback distintos em 452 preenchidos.
- **Correção:** análise semântica descartada; H4 será testada com comportamento (uso, erros, tickets). RAG focado no conhecimento das análises.
- **Lição:** checar o conteúdo antes de desenhar a solução — de novo.

### Skill de engenharia desatualizada em relação ao próprio plano
- **O que a IA fez:** a cada mudança de escopo (Render, multi-LLM, RAG, perfis) foi anexando seções na skill de engenharia sem reorganizar; ficaram tools com nomes diferentes do plano (`query_analytics` × `run_readonly_query`), dependências faltando (OpenAI, Gemini, cliente do Kaggle MCP), endpoint 360 sem regra de concorrência e auth assumindo o segredo JWT legado do Supabase.
- **Como percebi:** na revisão da skill, lendo de ponta a ponta.
- **Correção:** skill reescrita com rotas, tools únicas, dependências por pacote, pooler em modo transaction (sem prepared statements), JWT via JWKS, limites de custo e testes por camada.

### API do SDK do MCP assumida de memória
- **O que a IA fez:** escreveu o cliente do Kaggle com `streamablehttp_client(url, headers=…)` e `result.isError`, a API de versões antigas do SDK.
- **Como percebi:** `mypy` e o import falharam com o `mcp` 2.3 instalado.
- **Correção:** inspecionei a assinatura real no pacote instalado e usei `streamable_http_client` + `create_mcp_http_client(headers=…)` + `is_error`.
- **Lição:** conferir a API da versão instalada antes de escrever integração.

### Checagem de qualidade com total errado
- **O que a IA fez:** a checagem `linhas_rejeitadas` usava como total só accounts + subscriptions.
- **Como percebi:** revisando a saída do teste de fumaça.
- **Correção:** nova migration; o total passou a ser as linhas lidas pelo silver no run.

### `git add -f` commitou `.venv` e caches (4.306 arquivos)
- **O que a IA fez:** usou `git add -f` na pasta da submissão. O `-f` ignora também o `.gitignore` interno, e entraram `.venv`, `.mypy_cache` e outros caches.
- **Como percebi:** pela lista do `git status` logo após o commit.
- **Correção:** o commit ainda era local; foi refeito com `--amend` sem esses arquivos. Criei `scripts/stage.sh`, que faz `git add -f` e depois remove o que o `.gitignore` da pasta ignora, e a skill de engenharia agora proíbe `git add -f` direto.

### Quase chamei de achado um artefato de "plano atual"
- **O que a IA fez:** o corte de churn por `plan_now` (plano da assinatura mais recente) deu p < 0,001, com Basic em 13,5 contra Pro em 9,2 por 100 contas-mês, e parecia um achado forte.
- **Como percebi:** a assinatura mais recente pode ter começado **depois** do churn (reativação). Refiz a conta pelo plano na data de cada churn contra o mix de assinaturas ativas no trimestre, e a diferença sumiu.
- **Correção:** o achado foi descartado e o caso ficou registrado em `decisions.md`.
- **Lição:** atributo medido depois do desfecho não explica o desfecho.

### Nome de variável sombreando função do statsmodels
- **O que a IA fez:** chamou o DataFrame de churn de `C`, o que quebrou o `C(...)` das fórmulas do statsmodels.
- **Correção:** renomeei para `churn` no script final.

### GRR com dupla contagem
- **O que a IA fez:** a primeira `kpi_revenue_monthly` somava o MRR dos eventos de churn e também o MRR de fim de mês de contas que voltaram no mesmo mês, o que dava GRR mensal de cerca de 45%.
- **Como percebi:** o número era implausível na primeira consulta de validação.
- **Correção:** o MRR perdido passou a ser calculado por estado (ativa no início, churnada no fim), e o MRR dos eventos ficou numa coluna separada. Ainda assim, a receita sai com ressalva (ver `decisions.md`).

### Views lentas por funções não incorporadas na consulta
- **O que a IA fez:** usou funções SQL com `set search_path = ''` dentro de views chamadas por linha.
- **Como percebi:** a consulta de validação estourou o `statement_timeout`.
- **Correção:** materializei as dimensões e calculei a data de referência uma vez por consulta (migration `gold_performance`).

### Ambiguidade de coluna em JOIN USING
- **O que a IA fez:** `join persona_catalog using (persona)` com duas tabelas à esquerda que tinham a coluna `persona`. A migration falhou e nada foi aplicado.
- **Correção:** troquei por `on pc.persona = p.persona`.

### Horários inventados no journal e na timeline
- **O que a IA fez:** escreveu os horários das fases F2–F4 por estimativa (ex.: "F3 10:55–12:10"), sem consultar o relógio.
- **Como percebi:** ao planejar o prazo final com o Tiago, conferi `date` e `git log`: eram 11:23, e a F3 tinha levado 16 minutos, não 1h15.
- **Correção:** a timeline e o journal foram reescritos com os timestamps reais dos commits.
- **Lição:** um process log só vale com dados verificáveis. A regra "nunca inventar" vale também para metadados.

### Impactos do relatório estimados em vez de consultados
- **O que a IA fez:** o primeiro rascunho do relatório trazia o "MRR em risco por público" de memória (ex.: US$ 137 mil para contas novas).
- **Como percebi:** conferindo cada número do relatório no banco antes de fechar.
- **Correção:** recalculei em `api.risk_queue` (US$ 155 mil, 185 mil e 168 mil) e deixei explícito que os impactos não se somam.

### FK do gold bloqueando o reprocessamento do silver
- **O que a IA fez:** criou `gold.risk_scores` com FK para `silver.accounts`, mas o `silver.refresh()` faz `TRUNCATE` do silver. A primeira carga funcionou porque o gold ainda não existia.
- **Como percebi:** ao testar a ingestão disparada pelo painel, que falhou com "cannot truncate a table referenced in a foreign key constraint". A transação foi desfeita e os dados ficaram intactos.
- **Correção:** removi a FK (o gold é derivado e reconstruído depois do silver) e conferi que nenhuma outra tabela fora do silver referencia o silver.
- **Lição:** testar o caminho de reprocessamento, não só a primeira carga.

### Substituição de texto que não aconteceu (trigger do agendador)
- **O que a IA fez:** usou um `str.replace` sobre uma linha que o formatador (ruff) já tinha quebrado em várias linhas. A troca não aconteceu e os runs do agendador ficavam registrados como `manual`.
- **Como percebi:** no teste em produção, o run disparado pelo pg_cron apareceu com trigger `manual`.
- **Correção:** ajustei a linha e passei a usar edições que falham se o trecho não existir.
