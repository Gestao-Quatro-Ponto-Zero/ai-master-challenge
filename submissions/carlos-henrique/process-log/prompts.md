# Registro de prompts

## Prompt Mestre do JourneyGraph

- **Identificação:** Prompt Mestre do JourneyGraph, lido e confirmado antes desta fase.
- **Finalidade:** estabelecer a tese do produto, os princípios de governança e causalidade, a sequência de fases, os gates de qualidade e os limites de implementação do JourneyGraph.
- **Estado:** utilizado como contexto; este registro não afirma que fases ou prompts futuros tenham sido executados.

## Prompt da Fase 0

- **Identificação:** “FASE 0 — FUNDAÇÃO, CONTEXTO E SEGURANÇA DO REPOSITÓRIO”.
- **Finalidade:** autorizar exclusivamente a fundação documental e estrutural da submissão, sua validação e um commit local.
- **Estado:** execução registrada neste commit.

### Reprodução fiel das instruções recebidas

1. Trabalhar exclusivamente em `submissions/carlos-henrique/`, sem implementar análise, modelos, journey mining, grafos, dashboard ou business case.
2. Criar a fundação do **JourneyGraph — Challenge 001: Diagnóstico de Churn**, incluindo estrutura, documentação de escopo e arquitetura, decisões, process log, política de dados e artefatos, reprodutibilidade e validação do escopo.
3. Usar o repositório `C:\Users\ataqu\Documents\GitHub\ai-master-challenge`, fork `acarloshenrique/ai-master-challenge`, branch `submission/carlos-henrique`, `origin` do fork, `upstream` oficial e HEAD esperado `4aed364d572fabe0f1fff1f0c6f32960b30fe575`.
4. Não configurar tracking, fazer push, criar branch remota ou abrir Pull Request nesta fase.
5. Formalizar D001 a D010: Challenge 001; tese do JourneyGraph; exclusão do conteúdo anterior do SupportOps Intelligence Graph; escopo único da pasta; event log antes do grafo; NetworkX antes de Neo4j; não causalidade; ausência e não substituição dos dados; Git remoto condicionado a autorização; e staging seletivo devido ao ignore de `submissions/`.
6. Antes de criar arquivos, executar `pwd`, status, branch, remotes, HEAD, diff de trabalho e diff staged. Bloquear em caso de divergência.
7. Criar exatamente 16 arquivos: README principal; README e requirements da solução; `src/__init__.py`; READMEs de scripts, tests, raw, processed, artifacts e reports; architecture, data-contract e repository-policy; workflow, prompts e decisions.
8. Não criar app, notebooks, modelos, dashboards, CSV, Parquet, GraphML, imagens, screenshots, scripts de análise ou download, bancos, cloud config, Dockerfile, CI, APIs ou código de grafo.
9. No README principal, registrar projeto, candidato, challenge, status de fundação, tese, problema, perguntas, arquitetura conceitual, escopo e exclusões, fontes esperadas, ausência dos datasets, governança, não causalidade, roadmap e ausência de resultados.
10. No README da solução, registrar propósito, arquitetura planejada, Python 3.11+, execução indisponível, dependência dos cinco datasets, ordem auditoria → event log → diagnóstico → survival → journey mining → grafo → watchlist → aplicação, ausência de APIs pagas no núcleo, reprodutibilidade e ausência de código analítico.
11. Em `requirements.txt`, listar somente pandas, numpy, scipy, statsmodels, scikit-learn, lifelines, networkx, plotly, streamlit, pyarrow, pydantic e pytest; não instalar pacotes ou gerar lockfile; adiar o pin de versões até a validação do ambiente.
12. Em `data/raw/README.md`, listar os cinco CSVs oficiais, proibir versionamento, exigir a fonte oficial e os cinco arquivos, adiar validação de nomes e schemas para a Fase 1 e proibir substituição silenciosa por dados sintéticos.
13. Em `data/processed/README.md`, reservar saídas derivadas e reproduzíveis, exigir scripts geradores e reconciliação e proibir sobrescrita de dados brutos.
14. Nos READMEs de artifacts e reports, documentar apenas categorias futuras e não criar qualquer artefato nesta fase.
15. Em `architecture.md`, descrever arquitetura planejada em camadas, fluxo das cinco fontes, event-log-first, modelo conceitual do grafo, separação descritiva/temporal/prescritiva, human-in-the-loop, experimentação, stack, opcionais, exclusões, riscos e decisões pendentes da auditoria.
16. Em `data-contract.md`, não inventar schemas; marcar chaves, colunas, granularidades, temporalidade e relacionamentos como `A CONFIRMAR NA FASE 1`; planejar testes de unicidade, integridade, missingness, duplicidade, cardinalidade, datas, ordem temporal, inflação de joins, leakage, churn recorrente e reativação.
17. Em `repository-policy.md`, registrar escopo, raiz imutável, remotes, branch, proibições de push/force push, commits, segredos, datasets, arquivos grandes, conflito do ignore e staging seguro arquivo por arquivo.
18. No process log, registrar data/hora, contexto, verificações, arquivos, validações, resultado e próximo gate; identificar o Prompt Mestre e reproduzir fielmente a Fase 0; documentar D001–D010 com contexto, decisão, justificativa, consequências e status; não inventar erros da IA.
19. Criar somente uma docstring e versão opcional em `solution/src/__init__.py`, sem qualquer lógica.
20. Validar status incluindo ignorados, listar arquivos, confirmar origem da regra de ignore, garantir diffs limitados ao caminho autorizado, legibilidade, requirements permitidos, ausência de CSV, segredos, resultados, conteúdo prévio indevido, datasets e arquivos excessivos; executar `python -m compileall submissions/carlos-henrique/solution/src`.
21. Fazer staging com `git add -f` seletivo e individual, revisar nomes e diff completo, e criar um único commit local com a mensagem `chore: establish JourneyGraph submission foundation`.
22. Após o commit, validar status, último log e estatísticas; não fazer push, não configurar upstream e não abrir PR. Retornar o relatório obrigatório da Fase 0 e solicitar o prompt da Fase 1 sem iniciar auditoria ou download.

### Critérios de bloqueio preservados

A execução deve parar se branch, árvore inicial, staging, remotes ou HEAD divergirem; se qualquer arquivo externo precisar ser alterado ou entrar no staging; se houver conteúdo prévio do Challenge 002 no clone; se arquivo oficial precisar ser modificado; se a estrutura oficial tiver mudado materialmente; ou se existir dúvida sobre exclusão ou sobrescrita.

Nenhum prompt de fase futura foi executado.

---

## Prompt da Fase 1

- **Identificação:** “FASE 1 — AUDITORIA DAS CINCO FONTES”.
- **Finalidade:** produzir uma auditoria técnica e metodológica defensável das cinco fontes reais da RavenStack.
- **Estado:** executado nesta fase; nenhuma instrução da Fase 2 foi executada.

### Reprodução fiel do escopo recebido

1. Repetir os gates Git e interromper diante de branch, HEAD, working tree ou staging divergentes.
2. Tratar os cinco CSVs como read-only, registrar bytes, SHA-256, modificação e linhas físicas antes e depois e nunca versioná-los.
3. Usar Python compatível e somente pandas, NumPy e pytest; usar o `.venv` local quando necessário.
4. Criar somente loader, auditor, CLI, testes, três relatórios e quatro artefatos nos caminhos autorizados; atualizar contrato e process log.
5. Resolver caminhos independentemente do diretório atual, tentar UTF-8 primeiro, detectar delimiter, preservar colunas e registrar dtypes inferidos sem conversão silenciosa.
6. Perfilar registros, colunas, missingness, cardinalidade, duplicidade, constantes, strings vazias, espaços, IDs, datas, negativos, sentinelas e amostras sanitizadas.
7. Validar empiricamente chaves de contas, assinaturas, uso, tickets e churn; não declarar chave primária sem completude, unicidade, estabilidade e grão coerente.
8. Testar as quatro relações mínimas, órfãos, taxas de match, cardinalidades e risco de inflação.
9. Simular joins simples e encadeado somente com chaves em memória; não salvar mega-join nem derivar métricas dele.
10. Auditar todas as datas reais e cronologias entre conta, assinatura, uso, tickets e churn, classificando erro, suspeita, comportamento possível ou decisão pendente.
11. Quantificar churn zero/único/recorrente, reativação explícita ou inferível e assinaturas após churn sem fechar a regra final.
12. Classificar leakage explícito, temporal e proxy; não remover colunas nesta fase.
13. Auditar texto e privacidade apenas com regex e contagens agregadas; não reproduzir texto, não fazer semântica e não usar LLM.
14. Gerar deterministicamente `raw_file_manifest.json`, `data_profile.json`, `schema_map.json` e `relationship_matrix.csv` em UTF-8, sem PII.
15. Gerar `data-audit.md`, `relationship-audit.md` e `temporal-audit.md` sem findings de churn.
16. Substituir pendências do contrato pelos resultados testados e usar somente statuses autorizados.
17. Adicionar decisões D011 em diante somente quando sustentadas por evidência.
18. Criar testes de presença, ausência, hash, perfil, chaves, órfãos, match, inflação, datas, cronologia, leakage, sanitização, ausência de texto e idempotência.
19. Executar pytest e compileall; registrar erros reais e correções, sem fabricá-los.
20. Revisar manualmente schemas, chaves, cardinalidades, órfãos, joins, datas, recorrência, reativação, leakage, privacidade, hashes e relatórios.
21. Validar escopo e usar staging seletivo, individual, sem adicionar CSV ou diretório inteiro.
22. Criar, somente após aprovação de todos os gates, o commit local `data: audit RavenStack source tables`.
23. Não fazer push, tracking remoto ou Pull Request.
24. Classificar a viabilidade do event log como `PASS`, `PASS_WITH_WARNINGS` ou `BLOCKED` e não avançar automaticamente.

### Proibições preservadas

Não construir event log, diagnóstico de churn, segmentação, receita em risco, survival analysis, journey mining, grafo, watchlist, dashboard, modelo preditivo ou business case. Não baixar, editar, mover, converter, copiar ou versionar os CSVs.

### Resultado do prompt

A auditoria foi executada com outputs estruturais e gate `PASS_WITH_WARNINGS`. O event log não foi iniciado.

---

## Prompt da Fase 2

- **Identificação:** “FASE 2 — CONSTRUÇÃO E VALIDAÇÃO DO EVENT LOG TEMPORAL”.
- **Finalidade:** construir uma camada temporal canônica, auditável, conservadora e reproduzível a partir das cinco fontes validadas.
- **Estado:** executado nesta fase; nenhuma instrução da Fase 3 foi executada.

### Reprodução fiel do escopo recebido

1. Repetir os gates Git, exigir a branch e o commit-base esperados e bloquear diante de working tree ou staging divergentes.
2. Recalcular as evidências da Fase 1, manter os CSVs imutáveis e impedir mega-join.
3. Definir event log com identidade, entidade, timestamp, tipo, subtipo, origem, provenance, regra, qualidade, flags, quarentena e episódio.
4. Criar IDs determinísticos e preservar ID e linha física da fonte.
5. Gerar somente eventos sustentados pelos schemas reais e preferir eventos de origem.
6. Criar ACCOUNT_CREATED, SUBSCRIPTION_STARTED/ENDED, FEATURE_USED, SUPPORT_TICKET_OPENED/CLOSED, CHURN_RECORDED e REACTIVATION_RECORDED conforme regras temporais.
7. Não criar upgrade/downgrade ou eventos comportamentais sem timestamp e regra inequívocos.
8. Formalizar EXACT_DUPLICATE, DUPLICATE_SOURCE_ID, DUPLICATE_CANDIDATE_KEY e LEGITIMATE_REPEAT_EVENT, sem alterar CSVs ou descartar registros distintos.
9. Colocar erros temporais confirmados em quarentena e usar warning para ocorrências possíveis ou ambíguas.
10. Normalizar timestamps para `datetime64[ns]`, declarar `NAIVE_SOURCE_TIME` e usar desempate técnico não causal no mesmo dia.
11. Criar um episódio por assinatura, preservar abertos, registrar sobreposição e inferir previous/next apenas por ordem temporal na conta.
12. Preservar churn recorrente e reativação explícita como eventos distintos, com sequência e intervalos permitidos.
13. Não atribuir churn a assinatura sem regra; preencher candidato apenas quando houver uma ativa exata.
14. Produzir reconciliação por fonte com diferença não explicada zero.
15. Criar três Parquet, quatro artefatos JSON, três relatórios, quatro módulos/scripts e duas suítes de teste nos caminhos autorizados.
16. Atualizar arquitetura, contrato e process logs; registrar D021 em diante somente com evidência.
17. Validar pytest, compileall, duas execuções idempotentes, hashes, PII, tamanho dos Parquet e diff completo.
18. Versionar Parquet somente se pequenos, seguros e necessários; nunca usar Git LFS.
19. Fazer staging seletivo arquivo por arquivo e criar somente o commit local `data: build validated temporal event log`.
20. Não fazer diagnóstico, findings executivos, receita em risco, survival, journey mining, grafo, watchlist, modelo, dashboard, business case, LLM, push ou Pull Request.

### Políticas preservadas

- evento inválido não desaparece;
- evento derivado declara regra;
- conta e assinatura permanecem entidades distintas;
- churn de conta não encerra ou escolhe assinatura automaticamente;
- flags snapshot sem timestamp não viram eventos históricos;
- não criar eventos para preencher lacunas;
- texto completo, nome, feedback, motivo e refund não entram nos outputs;
- informação futura não pode contaminar fases preditivas;
- toda oportunidade reconcilia com ativo, quarentena, remoção exata ou ausência aplicável.

### Resultado do prompt

O event log, a quarentena e os episódios foram construídos com reconciliação zero e gate `PASS_WITH_WARNINGS`. Nenhum diagnóstico foi iniciado.

---

## Prompt da Fase 3

- **Identificação:** “FASE 3 — DIAGNÓSTICO EXECUTIVO DE CHURN, JORNADAS E RECEITA”.
- **Finalidade:** produzir diagnóstico descritivo governado a partir do event log validado, com cutoffs, censura, sensibilidade e findings quantitativos.
- **Estado:** executado; nenhuma instrução de survival analysis foi iniciada.

### Escopo reproduzido

1. Repetir gates Git, validar HEAD, hashes, Parquets, manifestos e ausência de CSV versionado.
2. Usar `VALID + VALID_WITH_WARNING` como população principal, `VALID` como estrita e quarentena somente em Data Health.
3. Preservar grãos de conta, episódio e evento; proibir mega-join.
4. Fixar `observation_end`, cutoffs por primeiro churn, janelas 7/30/60/90 e lifetime, sem informação futura.
5. Classificar outcomes mutuamente exclusivos com prioridade documentada e ausência de churn como observação censurada.
6. Criar tabelas de features por conta e episódio, preservando episódios abertos.
7. Produzir diagnósticos de Data Health, churn recorrente, reativação, uso, suporte, MRR associado e coortes.
8. Gerar jornadas agregadas com duplicatas consecutivas colapsadas e limite de comprimento, sem sequence mining.
9. Comparar grupos por estatísticas descritivas, efeito, n e missingness, sem inferência explicativa.
10. Recalcular métricas em populações estrita e ampliada; impedir promoção de findings `UNSTABLE`.
11. Criar no máximo dez findings e cinco situações de atenção, sempre com evidência, denominador e limitação.
12. Gerar dez JSONs, cinco relatórios Markdown e três Parquets autorizados, sem PII ou IDs em agregados públicos.
13. Criar cinco suítes de teste, executar pytest, compileall, pipeline duas vezes e comparar hashes.
14. Atualizar arquitetura, contrato e process logs; registrar D031–D041.
15. Fazer staging seletivo arquivo por arquivo e criar somente o commit local `analysis: add governed churn and journey diagnostics`.

### Proibições preservadas

Não foram implementados modelo preditivo, propensão, survival analysis, Kaplan–Meier, Cox, sequence mining, grafo, embeddings, clustering, atribuição explicativa, IA de recomendação, dashboard, LLM, push ou Pull Request.

---

## Prompt da Fase 4

- **Identifica??o:** ?FASE 4 ? SURVIVAL ANALYSIS E CURVAS DE RISCO TEMPORAL?.
- **Finalidade:** construir an?lise temporal governada de tempo at? primeiro churn, censura, curvas, risco acumulado, landmarks, compara??es e sensibilidade.
- **Estado:** executado com `PASS_WITH_WARNINGS`; nenhuma instru??o da Fase 5 foi executada.

### Escopo reproduzido

1. Repetir gates Git e validar commit-base, outputs da Fase 3, hashes, 500 contas ?nicas e aus?ncia de CSV bruto versionado.
2. Usar conta como unidade, primeira assinatura como origem principal, signup como sensibilidade e primeiro churn utiliz?vel como endpoint.
3. Aplicar censura administrativa ? direita e n?o chamar censurados de retidos definitivamente.
4. Criar dataset de conta e landmarks de 30, 60 e 90 dias sem eventos futuros.
5. Estimar Kaplan?Meier, Nelson?Aalen, at-risk, intervalos, mediana e RMST sem extrapola??o.
6. Comparar grupos temporalmente defens?veis, aplicar log-rank somente com suporte e corrigir p-values por Benjamini?Hochberg.
7. Executar seis cen?rios de sensibilidade e impedir findings `UNSTABLE`.
8. Avaliar pressupostos e condicionar Cox a eventos, missingness, proporcionalidade, estabilidade e aus?ncia de leakage.
9. Gerar oito JSONs agregados, quatro relat?rios, quatro Parquets, at? seis PNGs, c?digo modular e cinco su?tes de teste.
10. Executar pytest, compileall, pipeline duas vezes, hashes, valida??o de PII, leakage, escopo e revis?o humana.
11. Atualizar arquitetura, contrato e process logs; registrar D042?D051.
12. Fazer staging seletivo, commit local exato, sem push ou Pull Request.

### Proibi??es preservadas

N?o foram constru?dos score individual, modelo preditivo operacional, ranking, causalidade, interven??o automatizada, sequence mining, grafo, embeddings, LLM, dashboard, push ou Pull Request.

---

## Fase 5 ? Journey mining e padr?es sequenciais

**Objetivo recebido:** construir sequ?ncias temporais por conta, normalizar jornadas, calcular transi??es e n-grams, minerar padr?es frequentes, comparar desfechos, analisar churn/recorr?ncia/reativa??o, reconciliar principal/estrita e criar taxonomia descritiva.

**Restri??es preservadas:** sem causalidade, score, modelo preditivo, interven??o, grafo, centralidade, comunidades, embeddings, LLM, dashboard, push ou Pull Request.

**Fontes autorizadas:** event log ativo como fonte principal; features diagn?sticas, survival datasets e artefatos de sensibilidade/qualidade apenas como complementos. Quarentena usada somente em cobertura.

**Entreg?veis:** dois Parquets, dez JSONs agregados, quatro relat?rios, seis figuras, seis m?dulos/runner, cinco su?tes de teste, documenta??o e log de decis?es D052?D063.

**Commit autorizado:** `analysis: add governed journey and sequence mining`, local e seletivo.

---

## Fase 6 ? Constru??o, an?lise e valida??o do JourneyGraph

**Objetivo recebido:** construir uma camada de conhecimento governada sobre jornadas, com grafos de inst?ncia e anal?tico, temporalidade, padr?es, outcomes, taxonomia, qualidade, m?tricas, caminhos e consultas.

**Restri??es preservadas:** sem score individual, previs?o, causalidade, recomenda??o autom?tica, contato, interven??o, embeddings, GNN, link prediction, dashboard, app, push ou Pull Request.

**Fontes autorizadas:** Parquets de jornadas, taxonomia, event log e features diagn?sticas; JSONs de padr?es, transi??es, findings, estabilidade, sensibilidade, pr?-churn, reativa??o e recorr?ncia. Nenhum CSV bruto foi carregado ou versionado.

**Estrat?gia t?cnica:** NetworkX como refer?ncia local; exporta??o Neo4j opcional e sem servidor. Identificadores p?blicos determin?sticos, an?nimos e n?o revers?veis. Dois GraphML completos e CSV de EventInstance amostrado deterministicamente.

**Gates de promo??o:** somente ROBUST/SENSITIVE, suporte m?nimo atendido, denominador positivo, `small_sample=false` e depend?ncia intradi?ria diferente de HIGH.

**Entreg?veis:**

- seis m?dulos e um runner;
- seis su?tes de teste;
- dois GraphML;
- dez JSONs agregados;
- cinco relat?rios;
- seis figuras;
- dez CSVs de n?s, doze de rela??es e quatro arquivos Cypher;
- documenta??o e decis?es D064?D074.

## Fase 7 ? Intervention Watchlist e explica??es baseadas em evid?ncia

- **Entrada:** prompt integral da Fase 7, commit-base `1c31ae22632d27ac45137af5b55acee1d6f19f86`.
- **Escopo aplicado:** watchlist governada, regras, features retrospectivas, matriz discreta, evidence packets, JourneyGraph promov?vel, outputs agregados e valida??o.
- **Restri??es preservadas:** sem modelo preditivo, probabilidade, causalidade, receita perdida/salva, LLM decisor, a??o autom?tica, dashboard, push ou PR.
- **Gate esperado:** `PASS_WITH_WARNINGS` devido a amplitude de qualidade, regra ampla e depend?ncia de warnings.
- **Commit autorizado:** `analysis: add governed intervention watchlist`.

**Commit autorizado:** `graph: build governed JourneyGraph knowledge layer`, local e seletivo.

## Fase 8 ? Experiment Lab e desenho de interven??es test?veis

- **Entrada:** prompt integral da Fase 8, commit-base `1ed6655cf86f9068f56a10af25537ea8747a25b1`.
- **Escopo aplicado:** cat?logo governado, hip?teses falsific?veis, elegibilidade, baselines, power/MDE, simula??o de randomiza??o, SAP, guardrails, stopping rules, ?tica e relat?rios.
- **Restri??es preservadas:** sem interven??o real, contato, desconto, altera??o de produto, dados futuros, resultados fabricados, uplift, infer?ncia causal, dashboard, push ou Pull Request.
- **Gate esperado:** `PASS_WITH_WARNINGS`, pois apenas um desenho est? pronto para revis?o e os demais s?o piloto, subdimensionados ou n?o vi?veis.
- **Commit autorizado:** `analysis: add governed experiment design lab`, local e seletivo.
---

## Fase 9 - Dashboard executivo e experiencia de demonstracao

- **Entrada:** prompt integral da Fase 9, commit-base `3e96b07e9f113c15ec2a9635324054c3e7b27b00`.
- **Escopo aplicado:** app Next.js local, camada JSON derivada, overview, qualidade, Journey Explorer, JourneyGraph, watchlist, Experiment Lab, governanca, Guided Demo, testes, documentacao e screenshots.
- **Restricoes preservadas:** nenhum resultado analitico alterado, nenhuma nova conclusao, nenhum dataset baixado, nenhum backend externo, PII, score, probabilidade, causalidade, receita em risco/salva, intervencao, contato, execucao experimental, push ou Pull Request.
- **Contrato de demonstracao:** tres contas reais anonimas sob rotulos DEMO, grafo reduzido/promovivel, filas separadas, experimentos `UNTESTED`, explicacoes deterministicas e cutoff fixo.
- **Gate esperado e obtido:** `PASS`, apos build, validacao responsiva, revisao visual e reprodutibilidade.
- **Commit autorizado:** `feat: add governed JourneyGraph demonstration dashboard`, local e seletivo.

---

## Rework autorizado - localização completa e anonimização do dashboard

- **Entrada:** autorização de rework sobre o HEAD `fb6f09a34be2a77b3917b798ec22ed9fd56728ff`, preservando as alterações locais existentes.
- **Escopo:** interface integralmente em pt-BR, formatação pt-BR, mensagens completas, mapas explícitos de status, anonimização de contas demo, atualização de 18 testes Vitest, 36 cenários Playwright, sete screenshots, documentação mínima e process log.
- **Restrições:** somente `submissions/carlos-henrique/`; sem alteração analítica, CSV bruto, build artifact, push ou Pull Request.
- **Commit autorizado:** `fix: complete pt-BR localization and demo anonymization`.
- **Gate esperado:** `PASS` apenas com localização completa, anonimização, testes/build verdes, screenshots revisados, diff limpo e commit local seletivo.

## Fase 10A — documentação da submissão

- **Entrada:** prompt de documentação sobre o commit-base `de4ca14c66d33319af15aae492d04caadb910ff1`.
- **Escopo:** README executivo em inglês, arquitetura atual, sete screenshots, métricas autorizadas, governança, Quick Start e navegação para evidências técnicas.
- **Restrições:** nenhuma alteração analítica, link inventado, ação externa, push, deploy ou Pull Request.
- **Resultado:** documentação criada e validada; a auditoria do Quick Start revelou incompatibilidade do alias `build:data` com o shell padrão do Windows.

## Fase 10A.1 — correção do build cross-platform e consolidação

- **Entrada:** autorização para corrigir `npm run build:data`, validar determinismo, atualizar documentação/process logs e criar commit ou commits locais.
- **Escopo:** wrapper Node padrão, package.json, teste relacionado, READMEs, arquitetura, validador documental, matriz de consistência e logs.
- **Contrato do wrapper:** paths por `import.meta.url`/`fileURLToPath`/`node:path`; `.venv` local e fallbacks comuns; `spawnSync`; `shell: false`; saída herdada; exit code propagado; um único builder.
- **Gates:** dois rebuilds idênticos com 15 JSONs, lint, typecheck, Vitest, build, documentação, links, diff, staging seletivo, commits locais, working tree limpa e nenhum push.
- **Commit strategy:** tooling cross-platform separado semanticamente da consolidação documental.

## Recovery gate before Phase 10A

- **Evidence type:** `reconstructed instruction summary`; a formulação literal e o diff transitório não foram preservados no repositório.
- **Objetivo:** interromper a finalização quando o working tree continha estado local não reconciliado, auditar o escopo, restaurar o baseline autorizado e retomar somente após branch, status e staging passarem.
- **Limite:** o registro prova a regra de recuperação e a sequência relatada; não permite atribuir o estado transitório à IA nem reconstruir nomes de arquivos ausentes do Git.

## Fase 10B — evidências de julgamento humano e colaboração com IA

- **Evidence type:** `reconstructed instruction summary` consolidado a partir do gate documental da fase; não é transcrição literal.
- **Commit-base:** `bffa9a29b3b471f876d02e5fb784fc2bb5fa7c4d`.
- **Objetivo:** criar uma trilha auditável que separe propostas assistidas, julgamento humano, erros, correções, hipóteses rejeitadas, trade-offs, intervenções, evidências e limitações.
- **Entregáveis:** sete documentos de processo, integração no README e índice, validador com relatórios JSON/Markdown, revisão adversarial, teste do avaliador e atualização curada dos logs.
- **Restrições preservadas:** nenhuma alteração analítica, funcional, visual, de dados, arquitetura, teste funcional ou ação externa; commit local seletivo e sem push.
- **Gate esperado:** `PASS` somente com links, commits, atribuição, linguagem, adversarial review, teste do avaliador, diff e estado Git aprovados.
