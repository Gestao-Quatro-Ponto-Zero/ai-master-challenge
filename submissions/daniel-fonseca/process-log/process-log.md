# Process log — narrativa por sessão

> Uma entrada por sessão, mais recente no fim. Formato:
> **Sessão NN — data — harness/modelo — duração aproximada**
> Objetivo · O que o Daniel direcionou · O que a IA fez · O que foi ajustado/rejeitado · Saídas (arquivos/commits) · Próximo passo

---

## Sessão 01 — 2026-11-09 — Claude Code (Opus 5.5, app desktop) — ~1h

**Objetivo:** montar a fundação do projeto antes de qualquer solução.

**Direcionamento do Daniel (prompt inicial, resumido):**
- Challenge escolhido: 002 (Redesign de Suporte).
- Stack: Supabase (conta nova, free, com rotina anti-inatividade) + Vercel (conta nova) + n8n na VPS; MCPs de Supabase/Vercel **apenas no nível do projeto**, sem tocar os conectores pessoais.
- Diagnóstico (Q1) como dashboard; automação em três níveis (automático, human-in-the-loop, só humano com alerta no WhatsApp via WAHA); RAG em n8n com OpenAI para responder com base em casos parecidos com solução validada.
- Deploy real + setup fácil de backup para o G4; alternativas ao WhatsApp (Evolution API, Slack).
- Documentação transparente do workflow com IA, memória persistente entre sessões **e entre harnesses** (Claude Code ↔ Codex), vídeo + process log.
- Design system a partir do repositório Core-Slides-G4 (João Vitor, CPTO do G4).
- Pediu explicitamente sugestões e dúvidas da IA, técnicas e de gestão.

**O que a IA fez:**
1. Clonou o fork, criou a branch `submission/daniel-fonseca`, configurou `upstream`.
2. Leu README, CONTRIBUTING, submission-guide, template e o README do challenge 002. Notou que o `.gitignore` upstream ignora `submissions/` → arquivos novos exigem `git add -f`.
3. Baixou os dois datasets pela API pública do Kaggle (sem credencial) e rodou um perfil exploratório **antes** de aceitar as premissas do brief.
4. **Achado central:** o Dataset 1 é sintético — 8.469 tickets (não ~30K), CSAT uniforme, timestamps aleatórios numa janela de 27h, 49% dos tickets "resolvidos" antes da primeira resposta, resoluções em lorem ipsum. O DS2 é real, mas não tem resoluções. Detalhes em `context/data-findings.md`.
5. Leu o Core-Slides-G4 (licença MIT) e extraiu tokens de cor/tipografia para `docs/design-system.md`.
6. Criou a estrutura de memória/documentação (ADR-0001) e o `.mcp.json` do projeto.
7. Propôs ADRs para os pontos que dependem do Daniel: enquadramento do diagnóstico (0003), adaptação do RAG (0004), critérios dos 3 níveis (0005), keep-alive (0006).

**Ajustes / pontos que dependem do Daniel:** ver "Perguntas abertas" em `context/STATE.md`.

**Saídas:** `AGENTS.md`, `CLAUDE.md`, `.mcp.json`, `.env.example`, `context/`, `docs/`, `process-log/`, `scripts/download_data.sh`, `solution/analysis/00_data_profile.py`.

**Próximo passo:** respostas do Daniel → criação das contas → diagnóstico.

### Sessão 01 — parte 2 (feedback do Daniel)

**Direcionamento do Daniel:**
- Discordou da sugestão de corte de escopo (o RAG fica) e definiu o **timebox: dois turnos noturnos (09/11 e 10/11)**, incluindo vídeo e PR.
- Aceitou o console operacional, mas como **validador da solução**, separado do dashboard (ADR-0008).
- Notificações: **Slack + caixa de mensagens no painel** em vez de WhatsApp (ADR-0007).
- Pediu explicações antes de decidir: ADR-0003 em detalhe, termos de avaliação de ML, impacto da redução de dimensões dos embeddings, cron na Vercel grátis.
- Indicou o MCP correto do n8n (VPS) e o LinkedIn.

**O que a IA fez:**
1. Consultou a doc da Vercel: plano Hobby permite cron **1×/dia** (±59 min) → ADR-0006 aceita.
2. Testou o endpoint MCP do n8n na VPS: responde, exige token (401 sem `Authorization`). Configuração documentada em escopo local, sem versionar token nem a URL/IP.
3. Escreveu `01_signal_tests.py` (qui-quadrado entre todas as variáveis, Kruskal-Wallis para CSAT, IC 95%) e detalhou a ADR-0003 com os resultados — inclusive o exemplo de ranking que parece achado e é ruído (p=0,50).
4. Registrou as decisões (ADRs 0006–0008), o plano por turno (STATE) e o judgment log (#6–#10).

**Saídas:** `solution/analysis/01_signal_tests.py`, ADRs 0003/0006/0007/0008, `docs/setup.md` (n8n), STATE com plano por turno.

### Sessão 01 — parte 3 (contas criadas)

**Direcionamento do Daniel:** contas Supabase e Vercel criadas; `n8n-g4` instalado via terminal; quer os dois datasets no Supabase antes de decidir o resto; questionou a redução de dimensões dos embeddings; sem workspace Slack — a caixa de mensagens do painel basta por enquanto.

**O que a IA fez:**
1. `claude mcp list` na pasta: `n8n-g4` ✔ conectado; `supabase-g4` e `vercel-g4` aguardando aprovação (só aprováveis numa sessão aberta na pasta).
2. Criou a migration das tabelas brutas (`ds1_tickets`, `ds2_tickets`, com RLS ligado) e o `scripts/load_raw_datasets.py` (COPY via Postgres, holdout estratificado 80/20 do DS2 já gravado na tabela). Testou as transformações localmente (8.469 / 47.837 linhas; 20% de teste em cada categoria).
3. Refez a conta de espaço com `halfvec` e mudou a ADR-0004: dimensão decidida por medição.

### Sessão 01 — parte 4 (verificação após o `/mcp`)

**Contexto:** a IA abriu uma sessão paralela para o `/mcp` e a carga. Ela descobriu que o terminal estava em `submissions/`, um nível acima, e por isso o `.mcp.json` não era lido. O Daniel conectou os MCPs na pasta certa, e o `.env` e o `.env.example` foram ajustados (comentários fora da linha do valor, Slack/WhatsApp movidos para o n8n).

**Testes feitos pela IA (sem imprimir segredos):**
- `claude mcp list`: `supabase-g4`, `vercel-g4` e `n8n-g4` ✔.
- Formato do `.env`: encontrou comentários e espaços na mesma linha da `SUPABASE_SERVICE_ROLE_KEY` (o Next.js leria isso como parte da chave) e corrigiu sem exibir valores; preencheu `N8N_BASE_URL`.
- As chaves JWT decodificadas batem com o ref novo, e a DB URL aponta para o pooler de São Paulo.
- Conexão real: contagens 8.469 / 47.837, split 9.567/38.270, RLS bloqueando anon e service role lendo.
- **`OPENAI_API_KEY` retorna 401** — falta a chave real.

### Sessão 01 — parte 5 (cruzamento e diagnóstico)

**Direcionamento do Daniel:** corrigiu a chave da OpenAI; questionou se DS1 e DS2 se relacionam pelo id (não → ADR-0009); validou as ADRs 0004, 0005 e 0009; redesenhou a resposta da ADR-0003 pergunta a pergunta (cortes antes do diagnóstico, CSAT só dos respondidos com a tese do viés de sobrevivência, incoerência visível + indicadores de custo); pediu explicação de IC e p-valor.

**O que a IA fez:** testou a chave (embedding de 1536 dims OK); escreveu a ADR-0009; escreveu e rodou `02_diagnostic_cuts.py` (5 dimensões, p-valores, IC, R² com 70 variáveis, CSV para o dashboard); reescreveu a ADR-0003 separando indicadores **medidos** de **premissas**; documentou o viés de sobrevivência em `data-findings.md`.

**Premissas de custo (Daniel escolheu "benchmarks com fonte"):** a IA pesquisou na web, abriu as fontes primárias e descartou números que não se confirmaram (ver judgment log #17). Resultado em `docs/premissas-de-custo.md` + `cost_premises.json`: 8,6 min/ticket (MetricNet/HDI), R$ 21,30/h (CAGED, CBO 4223-20, com encargos), 30K tickets/ano (brief) → ~4.300 h e ~R$ 91,6 mil/ano em mão de obra direta.

### Sessão 01 — parte 6 (classificador)

**Direcionamento do Daniel:** validou a ADR-0003 e pediu para seguir.

**O que a IA fez:**
1. Gerou os embeddings dos 47.837 tickets do DS2 em segundo plano (2,19M tokens ≈ US$ 0,04), com cache por lote.
2. Avaliou 6 métodos no mesmo holdout: TF-IDF + LR, kNN e LR sobre embeddings (1536 e 512) e LLM zero-shot (400 tickets, `gpt-5.4-mini`). Checou vazamento (quase-duplicatas).
3. Testou um TF-IDF compacto (exportável em JSON) e a concordância TF-IDF × kNN como critério do nível 1.
4. Calibrou os 3 níveis no holdout e fez a ponte com o DS1 (≈ 24% de automação total, ~R$ 22 mil/ano só no nível 1).
5. Achou e corrigiu um bug próprio (precisão por categoria sempre 100%).
6. Propôs a ADR-0010.

### Sessão 01 — parte 7 (RAG como classificador principal)

**Direcionamento do Daniel:** escolheu o RAG como classificador principal (domínio e caso prático de LLM), aceitando perder alguns pontos, e pediu para tentar melhorar o acerto só com RAG. Definiu as diretrizes do n8n: nós nativos, fluxos simples, rascunho validado antes de construir, documentação.

**O que a IA fez:** testou três caminhos — ajuste do voto (`06`), busca híbrida com RRF (`06`) e RAG + LLM com os casos recuperados no prompt (`07`, 400 tickets). O melhor foi o voto ajustado (82,8%). Calibrou a política de 3 níveis com o RAG único (`08`) e reescreveu a ADR-0010; registrou a ADR-0011.

## Sessão 02 — 2026-11-09 — Claude Code (Opus 5.5, app desktop, sessão aberta em `submissions/daniel-fonseca/`) — ~40 min

**Objetivo:** levar o RAG escolhido na ADR-0010 para o Supabase e rascunhar os fluxos do n8n para validação (ADR-0011), sem construir nada no n8n.

**Direcionamento do Daniel (via sessão principal):** usar só `supabase-g4` e `n8n-g4`; RAG no banco com voto k=50, peso sim¹⁶, 512 dims, só vizinhos do treino; validar no banco contra os 82,8% locais; n8n só para consulta; apresentar os rascunhos e esperar aprovação.

**O que a IA fez:**
1. Confirmou o `supabase-g4` (URL do projeto = ref `awiphrbtvgapuuebiouw`) e o `n8n-g4` conectados. Os servidores globais não foram usados.
2. Escreveu e aplicou via `apply_migration` a `20261109000002_rag.sql`: pgvector no schema `extensions` (evita o alerta de extensão no `public`), `ds2_embeddings` (halfvec 512 + HNSW + RLS) e a função `classify_ticket`. A função tem `search_path` fixo e execução revogada de `anon`/`authenticated`.
3. Escreveu `scripts/load_embeddings.py`: trunca para 512, renormaliza e faz COPY binário (pacote `pgvector`, 49 MB em vez de ~220 MB em texto). Derruba e recria o HNSW em volta da carga: 5 s de COPY e 33 s de índice.
4. **Pegou uma armadilha antes de medir:** o `ef_search` padrão do HNSW (40) é menor que k=50, e o filtro "só treino" descarta ~20% dos candidatos. Sem ajuste, a função devolveria menos de 50 vizinhos e o voto ficaria diferente do avaliado. Correção: `ef_search = 100` + `iterative_scan = strict_order` na própria função.
5. Validou com `solution/analysis/09_db_rag_validation.py` (500 tickets de teste): banco 80,4% × exato local 80,2% nos mesmos tickets, 99,8% de concordância e latência p50 de 64 ms. A diferença para 82,8% é da amostra, não do banco.
6. `get_advisors`: performance limpo; security só INFO de "RLS sem policy" (intencional). Banco com 150 MB de 500.
7. Consultou no `n8n-g4` a SDK reference, as best practices (triage, scheduling, chatbot; HITL sem doc) e as definições dos nós. Descobriu que o nó "Embeddings OpenAI" é sub-nó, sem saída no fluxo principal → embedding via HTTP Request com a credencial nativa da OpenAI (exceção justificada no doc).
8. Escreveu `docs/n8n-flows.md`: 3 fluxos nó a nó, credenciais dedicadas (sem reaproveitar as de outros contextos da instância), schema proposto das 5 tabelas de apoio + `match_resolutions` (não aplicado) e 6 decisões para o Daniel.

**Saídas:** `solution/supabase/migrations/20261109000002_rag.sql`, `scripts/load_embeddings.py`, `solution/analysis/09_db_rag_validation.py` + `output/db_rag_validation.json`, `docs/n8n-flows.md`, STATE e data-findings atualizados; `pgvector` em `requirements.txt`.

**Próximo passo:** Daniel valida os rascunhos e as 6 decisões → migration das tabelas de apoio → playbook-semente → construir os fluxos no n8n.

### Sessão 02 — parte 2 (decisões do Daniel sobre os fluxos)

**Direcionamento do Daniel:** confirmou o papel de cada peça (o banco guarda a memória e faz o voto; o n8n leva cada ticket novo até ela). No nível 1, o LLM adapta a solução validada, e só quando ela existe. Perguntou sobre o risco de falsos positivos da lista de bloqueio e sobre o custo do `gpt-5.4-mini` com US$ 5 de crédito. Pediu texto livre em inglês e heartbeat às 06:00.

**O que a IA fez:**
1. Mediu a lista de bloqueio no holdout (`10_blocklist_eval.py`). A lista ampla que a própria IA tinha proposto rebaixaria 21,4% do nível 1; a estreita, 0,2%. Também viu que os 15 escapes são, na maioria, ruído de rótulo.
2. Conferiu o preço do `gpt-5.4-mini` na página oficial da OpenAI: US$ 0,75 / 4,50 por 1M tokens. Estimou ~US$ 0,003 por ticket (~1.600 tickets com US$ 5), ancorado no uso real da sessão 01.
3. Atualizou o rascunho para a v2: nó "Adaptar solução validada" com o guarda-corpo `fits`, lista estreita, heartbeat às 06:00 e quadro de custo. Registrou a ADR-0012 e as entradas #26–#29 do judgment log.

**Próximo passo:** OK final do rascunho v2 → migration das tabelas de apoio → playbook-semente → credenciais no n8n → construção.

### Sessão 02 — parte 3 (construção dos fluxos)

**Direcionamento do Daniel:** confirmou que o fluxo 2 é disparado pela decisão do revisor no console, e não pelo fluxo 1. Pediu para conferir se o console cabe no plano free da Vercel (a IA conferiu na doc oficial: cabe). Aprovou o rascunho v2: "Aprovado, pode construir".

**O que a IA fez:**
1. Aplicou a migration `ops` (5 tabelas + `match_resolutions`) via `apply_migration`; advisors só INFO.
2. Leu tickets reais de cada categoria do DS2 e rascunhou o **playbook-semente**: 14 soluções em 6 categorias não sensíveis, sem prazos nem promessas. Carregou com `seed_playbook.py` (185 tokens de embedding) e testou `match_resolutions` no banco.
3. Leu a referência do SDK e os tipos de cada nó e validou os nós críticos isoladamente (OpenAI v2.3 com `json_schema`, Postgres com parâmetros em lista, HTTP com credencial predefinida). Depois validou e criou os 3 workflows **inativos**.
4. **Pegou um risco de segurança:** o n8n auto-atribuiu aos webhooks a credencial `Waha VPS (chave API)`, de outro contexto do Daniel, por ser a única Header Auth da instância. A IA tentou trocar, mas a ferramenta exige o ID de uma credencial existente. O risco ficou registrado como bloqueio: não ativar antes da troca.
5. Ajustes da construção (Set em cadeia para a política, leitura defensiva da saída do LLM, caminho de erro, heartbeat sem o If) documentados em `docs/n8n-flows.md`.
6. Versionou a fonte SDK dos fluxos em `solution/n8n/*.sdk.ts`. O JSON fica para depois do teste, porque a versão de hoje não está testada.

**Não verificado:** nenhuma execução real dos fluxos (sem credenciais). Ainda não se sabe o formato exato da saída do nó OpenAI v2.3 com `simplify`; os Set de leitura cobrem os formatos prováveis.

**Próximo passo:** Daniel cria as credenciais e revisa o playbook → IA vincula, testa ponta a ponta, exporta os JSON e ativa.

### Sessão 02 — parte 4 (10/11 · nós Supabase e teste ponta a ponta)

**Direcionamento do Daniel:** pediu para trocar os nós Postgres por nós nativos do Supabase, com a credencial do próprio Supabase. Criou as credenciais G4 no n8n, validou o playbook-semente e pediu a troca e um teste ponta a ponta.

**O que a IA fez:**
1. Antes de propor, testou se a API REST do Supabase chama `classify_ticket` com o vetor: mesmo resultado, ~250 ms, `anon` bloqueado. Conferiu os tipos do nó Supabase: ele não chama funções, então elas usam HTTP Request com a credencial Supabase (ADR-0013).
2. Migration `rest_wrappers`: `match_resolutions_json` (devolve sempre um objeto, porque o HTTP Request do n8n quebra listas em itens e para no vazio) e playbook marcado como aprovado pelo Daniel.
3. Recriou os 3 fluxos com nós Supabase. **O n8n auto-atribuiu de novo credenciais de outros contextos** (`Supabase – padaria-bi` em 9 nós, `Waha VPS` nos webhooks). A IA trocou tudo pelos IDs G4 antes da primeira execução e arquivou as versões Postgres.
4. Teste ponta a ponta com tickets do holdout: níveis 1, 2 e 3; HITL nos 4 caminhos; aprendizado; heartbeat no caminho de falha. **A 1ª execução achou um bug da IA:** a saída `json_schema` do nó OpenAI v2.3 vem como objeto, e o leitor concatenava como texto. O caminho de segurança funcionou (o ticket desceu para revisão humana em vez de responder errado). Corrigido e refeito.
5. Tentou publicar os fluxos 1 e 2 para testar o webhook de produção. A publicação do 1 foi **bloqueada pelo controle de permissões** (ativação de endpoint público precisa do OK do Daniel). A do 2 passou, e a IA a desfez para não deixar estado pela metade.

**Não verificado:** webhook de produção com o header; nó Slack. O JSON exportado está pendente (a fonte SDK está versionada).

**Próximo passo:** OK do Daniel para ativar → teste com e sem header → export JSON.

### Sessão 02 — parte 5 (10/11 · ativação)

**Direcionamento do Daniel:** "Pode ativar e testar o webhook".

**O que a IA fez:** publicou os fluxos 1 e 2 e testou o webhook de produção por script, sem imprimir a URL nem o segredo. Sem header ou com header errado: 403. Com o header certo: 200 em 3,5 s (triagem #6, nível 1). Texto vazio: 400. HITL sem header: 403. Item já decidido: 409. O fluxo 3 continua inativo até o deploy da Vercel.

### Sessão 02 — parte 6 (10/11 · PRD do app)

**Direcionamento do Daniel:** antes do export dos JSON, construir o app da Vercel, começando por um **PRD colaborativo**. Pediu que a IA tire todas as dúvidas: layout, design (base do João Vitor), KPIs, fluxos de UX e elementos.

**O que a IA fez:** releu o design system, as ADRs 0003/0005/0007–0012, as premissas de custo e o brief. Escreveu `docs/prd/00-questionario.md`: 16 blocos (A–P), cerca de 90 perguntas, cada uma com uma sugestão, as estruturais marcadas com ★, uma tabela de KPIs com fórmula e fonte, MoSCoW e ordem de construção.

**Respostas do Daniel (rodada 1) e PRD v1:**
- Enxugou a estrutura para 3 áreas com toggles: Painel (Diagnóstico · ROI · Operação), Console (Triagem · Fila · Caixa) e Como foi feito (incluindo a proposta de automação).
- Navegação: top bar com toggle; no mobile, barra centralizada no rodapé.
- Dashboard com poucos gráficos: seletor de métrica, significância em linguagem simples, forest plot + callout de sobrevivência.
- Cortes: filtros, exploração, histograma, instrumentação, painel de confiabilidade, curva com slider, ponte DS1 × DS2 e exemplos prontos.
- ROI sem "níveis", falando dos casos com autonomia da IA. Dados todos do Supabase (J2 = B).
- Pediu atenção a ataques (autenticação em aberto), destaque à sua experiência em gestão e texto sem antagonismos nem analogias.
- Pronto só depois da validação dele contra o que o G4 pede.

A IA consolidou tudo em `docs/prd/01-prd.md` e na ADR-0014, registrou a regra de estilo no AGENTS.md e levantou 7 pendências. Para a autenticação, comparou 4 opções, considerando que o PR público expõe qualquer credencial escrita nele.

**Rodada 2 (Daniel):**
- "Condução" deve ser objetiva e concisa, incluindo a ideação e a estrutura do projeto no Claude Code.
- **Sem login**, com limites de uso e uma rotina de checagem de logs que alerte. Nenhuma decisão contra abuso sem instrução clara dele.
- Não começar a construção ainda.

A IA especificou no PRD (§8 e §8.1):
- limites por IP e globais e a tabela `usage_events` com o IP em hash;
- 8 sinais de alerta;
- uma camada determinística no n8n (a cada 15 min) e uma rotina do Claude que lê os logs da Vercel, do Supabase e do n8n e só resume e alerta.

A regra de conduta também foi registrada no AGENTS.md.

### Sessão 02 — parte 7 (10/11 · plano aprovado e base do app)

**Direcionamento do Daniel:**
- R8: os alertas de uso só simulados como Slack;
- R9: rotina a cada 2 h, reportando nesta sessão, como tarefa agendada local;
- R11: ativa até ele mandar desligar;
- commit e push no fork liberados; deploy pela integração com o GitHub;
- limpar e repovoar os dados de demonstração;
- alterar o fluxo 1 em produção, com teste;
- escopo do plano: só o app.

**O que a IA fez:**
1. Commit `b893d65` das sessões 01–02 (com checagem de segredos e da URL da VPS) e push no fork.
2. Ao criar o projeto na Vercel, o MCP `vercel-g4` recebeu 403 no time `case-g4`. A IA gerou o link de autorização para o Daniel e seguiu com o resto.
3. Migration `app`. Novo script `11_app_summary.py`, com os p-valores por métrica, a armadilha do ranking, o R² e as entradas do ROI. Também o `load_analysis.py`, que publica no Supabase os resultados da análise.
4. **Achou um erro próprio:** a ponte do ROI na ADR-0010 usava um denominador que inflava a autonomia (52,4% → 42,2%). Corrigiu a ADR, o data-findings e o PRD, e registrou no judgment log (#37).
5. Fluxo 1: tokens (resposta crua da OpenAI), custo, latência e tempo por etapa gravados em `triage_runs`; republicado e testado pelo webhook nos 3 caminhos (US$ 0,0007–0,0014 por triagem).
6. `reset_demo.py`: limpou os testes e repovoou com 10 tickets reais do holdout.
7. App Next.js 16.4.6, depois de ler a documentação local da versão: Cache Components exigem `<Suspense>` para dados dinâmicos e `searchParams`. Tokens Órbita nos dois temas, shell, camada de dados só no servidor, limites de uso, heartbeat e stubs com contrato para a frente B. Conferido no navegador (desktop, mobile e escuro).
