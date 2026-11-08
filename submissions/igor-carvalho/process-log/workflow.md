# Workflow do projeto — G4 Sales Priority (Lead Scorer)

Como o projeto foi conduzido com a IA: para cada fase, **o que eu pedi (Solicitação)** e **o que a IA entregou (Resultado)**. Atualizado em 2026-11-07.

> As solicitações estão resumidas com as minhas palavras; as frases entre aspas são citações do pedido original.

## 1. Contexto
- Desafio: priorizar deals para o vendedor (o que fazer hoje) e dar visão de gestão ao manager.
- Dataset (Kaggle, na pasta do projeto): ~8,8 mil oportunidades, 35 vendedores, 6 managers, 3 escritórios (Central, East, West).
- Estrutura: `solution/backend` (Python), `solution/frontend` (React), `docs/`, `process-log/`.

## 2. Visão geral das fases

| Fase | Tema | Eu decidi / validei | A IA entregou |
|---|---|---|---|
| A | Escolha do modelo | Qual das 3 opções usar | 3 notebooks comparáveis e recomendação |
| B | Análise do score e regras de negócio | O que o score significa e quando um deal vira "zumbi" | Definição do score, faixas e limiares |
| C | Protótipo da tela | Foco da tela, após longa avaliação | Tela principal clicável (v1, v2, v3) |
| D | Backend | Arquitetura e contratos | Treinador, API e banco v1 |
| E | Coleções de teste e qualidade | Usar Postman, remover Bruno | Coleção, métricas de código |
| F | Organização e configuração | Pastas, usuários, `.env` | Reestruturação |
| G | Frontend real | Só a v2 vira front; React com classes | App React + TS |
| H | Regras só no backend | O front não decide nada | Endpoints com `view`, `meta`, `summary` |
| I | Treino diário e Docker | Retreino diário | Script, cron, Docker |
| J | SQLAlchemy | Um repositório por entidade | Camada de persistência |
| K | Testes de regras | Cobrir as regras de negócio | 408 testes |
| L | Revisão e documentação final | Review só como relatório | Relatório, READMEs, plano de pendências |
| M | Configuração do front | URL do backend em arquivo | `G4_API_URL` no `.env` |
| N | Funil em heatmap | Trocar o funil por heatmap; depois esconder da página | Heatmap produto x tempo (componente mantido) |
| O | Coerência com o modelo | Entender "esperado"; popup condizente com o modelo | Popup e textos alinhados (horizonte de 30 dias) |
| P | Semana x dia | A semana deve ter mais deals que o dia | Foco da semana = Alta + Média |
| Q | Sugestões do vendedor externo | Triagem e plano; só a Fase 1 | Indicadores separados, explicação por fator, confiança x completude |

## 3. Linha do tempo

### Fase A — Escolha do modelo (notebooks)
**Solicitação**
- Pedi que a IA avaliasse qual seria o melhor modelo para os dados do Kaggle que coloquei no projeto.
- Pedi **no mínimo 3 opções** para eu validar e comparar, em vez de uma resposta única: "Crie pelo menos 3 opções em que eu possa validar essas opções...".
- Eu queria analisar os resultados e escolher.

**Resultado**
- A IA respondeu com as possibilidades, cada uma em um notebook, com tabelas de comparação (A / B / C) e uma conclusão com recomendação.
- Escolhido: modelo de probabilidade de ganho com **LightGBM**, features *point-in-time* e calibração.
  - Histórico só com deals fechados até a data T; fotos semanais até T−60 dias; rótulo só se fechou até T (evita vazamento).
  - Shrinkage K=30 e janela recente de 90 dias; LightGBM (lr 0,03; 15 folhas; min_child_samples 150; early stopping 50 na última fatia temporal).
  - Calibração "shrink-to-base" (alpha entre 0,1 e 1,0); só é "útil" se o Brier superar o de uma constante.
- Backtest honesto: AUC ≈ 0,55 (IC95% 0,517–0,563), lift@20 ≈ 1,09. Modesto, mas com ganho de receita no topo.
- Plano e contrato da API: `docs/PLANO_APLICACAO.md` (seção 4).
- **Atualização:** o modelo evoluiu para prever a chance de ganho **em até 30 dias** (rótulo `won_30d`, fotos até T−30, calibração por deslocamento de nível). A calibração atual não é "útil", então a chance em % fica oculta e o modelo vale pelo ranking. Ver `solution/backend/docs/MODELO.md`.

### Fase B — Análise do score e definição das regras de negócio
**Solicitação**
- Entender o que o score deveria representar: chance de ganhar, valor ou os dois, e como isso vira ação para o vendedor.
- Definir as regras de negócio: quando um deal está em foco, quando exige decisão e quando é "zumbi" (deal parado que ninguém fecha mais).
- Quis ver a base de cada regra nos dados, não números arbitrários.

**Resultado**
- **Score** = percentil (0–100) do **valor esperado** (chance de ganhar × preço do produto) entre os deals abertos não zumbis. Combina chance e valor.
- **Regras (nesta ordem):**
  1. Prospecting → faixa `prospecting` (sem score).
  2. Idade > **138 dias** (a maior duração de um deal já fechado) → `review`, sem score.
  3. Idade > **104 dias** (P90 dos fechados) → `stale_risk`: "decidir agora".
  4. Score ≥ **80** → `focus`; ≥ **40** → `follow_up`; senão `low`.
- Os limiares vêm dos dados (no treino real: 45 / 104 / 138 dias) e ficam no model card.
- **Confiança baixa** se o vendedor tem menos de 30 deals fechados.
- Prioridade: Alta 80–100, Média 40–79, Baixa 0–39.
- Limites assumidos: o score é associação, não causa; ele ajuda a escolher, não prevê com certeza.
- **Atualização:** o score passou a ser o percentil de `p30 × preço` (receita esperada em 30 dias). Os limiares agora são quantis do ciclo fechado: P90 (`stale_risk`) e **P99** (`review`), não mais o máximo. "Decidir agora" mantém o score só para ordenar e fica limitado a 79 (nunca Alta).

### Fase C — Protótipo da tela
**Solicitação**
- Pedi um exemplo de como a **página principal** ficaria, só o front, sem backend.
- Depois **passei bastante tempo avaliando como a tela deveria ser** e entendendo qual era o foco do score: o que o vendedor precisa ver primeiro, em que ordem, e por que cada deal aparece naquela posição.
- Pedi avaliação "como vendedor sênior", melhorias e versões visuais para comparar.

**Resultado**
- Tela "Seu foco da semana": KPIs, abas por faixa, lista com score, tempo no funil e valor esperado, e painel de detalhe com o "porquê" do score.
- Iterações: KPIs na ordem Foco → A revisar → Dias abertos → Valor esperado (cada um filtra a tabela); paginação, ações rápidas, seleção em lote, modal com todos os dados, visão "Seu dia".
- Auditoria do protótipo contra o modelo (para a tela não prometer o que o modelo não entrega).
- Versões: v1 (arquivada), **v2 corporativa em azul-marinho = principal**, v3 com cores inspiradas na G4.
- Firebase não foi possível; o mapeamento para Firestore ficou em aberto.

### Fase D — Backend Python
**Solicitação**
- Construir o backend: treinador e API, com banco SQLite, sem treinar durante requisições.

**Resultado** (núcleo em `solution/backend/src/`)
- `lead_core`: features, faixas, motivos, calibração, bundle do modelo, SQLite, persistência.
- `lead_trainer`: lê dados, treina, faz backtest, calibra, compara com a versão ativa e promove (champion/challenger). Portão: IC inferior do AUC > 0,5 e sem piora > 0,005 (`--force` ignora).
- `lead_api` (FastAPI): JWT, RBAC (vendedor = próprios deals, manager = time, revops = tudo; fora do escopo = 404), erro padronizado com `request_id`, rate limit, CORS; retreino em subprocesso.
- SQLite **esquema v1 congelado** (hash verificado por teste): users, deal_feedback, model_versions, jobs.
- Dados reais: AUC 0,5502; Brier 0,2282 vs 0,2317 (calibração útil, alpha 0,75); 2.089 deals abertos pontuados.

### Fase E — Coleções de teste e qualidade
**Solicitação**
- Ter uma coleção para testar a API; depois removi o Bruno por não ser mais necessário. Pedi também uma análise de qualidade do código.

**Resultado**
- Coleção Postman v2.1 (`solution/backend/g4-lead-scorer.postman_collection.json`), rodada contra a API real sem falhas.
- Radon (complexidade média A), Ruff (sem erro de lógica) e avaliação SOLID. Backlog em `solution/backend/docs/QUALIDADE.md`.

### Fase F — Organização e configuração
**Solicitação**
- Organizar o código, criar usuários e centralizar configuração.

**Resultado**
- 37 usuários: `revops`, 6 managers e 30 vendedores. Login só por `user_key`, **sem senha** (MVP).
- `.env` lido pela API; `.env.example` como modelo; o treinador lê só variáveis do terminal.

### Fase G — Frontend real (chat separado do front)
**Solicitação**
- Mover a aplicação para uma pasta de front, usando **só a MainV2 do vendedor**.
- React com **class components, sem hooks**.
- Revisão de usabilidade antes de editar.

**Resultado**
- React 18 + TypeScript + Vite. Interface `DealsApi` com `MockDealsApi` e `HttpDealsApi`; `npm run dev` usa a API real (`vicki-laflamme`).
- ~3.400 linhas, 8 arquivos de teste (inclui teste de arquitetura e teste de integração live).
- Revisão de usabilidade: 5 divergências do plano e ~39 sugestões.
- Pendências marcadas `TODO(api)`: Adiar, Encerrar como perdido, Marcar feito, rota "Seu dia" e motivo estruturado do feedback.

### Fase H — Regras de negócio só no backend
**Solicitação**
- O front não pode ter regra de negócio; ele só exibe o que a API devolve.

**Resultado**
- Auditoria encontrou regras duplicadas no front (faixas, limiares, abas, confiança, textos).
- `GET /deals` com `view`, `priority`, `max_score`; cada deal traz `view`, `confidence_reason`, `suggested_action`.
- `GET /meta` (níveis de prioridade, views, limiares) e `GET /summary` (contagem e valor esperado por aba; zumbis não somam valor).
- Fonte única em `lead_core/constants.py`. O teste de arquitetura do front falha se aparecerem literais de regra (138, 104, 41, 80, 40) fora do mock. Sem mudar o banco nem retreinar.

### Fase I — Treino diário e Docker
**Solicitação**
- Retreinar todos os dias com leads novos e empacotar em Docker.

**Resultado**
- `scripts/run_daily.sh` / `make train-daily`: treina, loga em `var/logs/`, usa lock e recarrega a API se `G4_API_URL` estiver definido. Agendamento por `deploy/com.g4.lead-trainer.plist` (macOS) ou cron.
- Docker: `Dockerfile`, `docker-compose.yml`, `scripts/up.sh`; cron às 02:00 e API no container; modelos e banco em volumes.
- Ressalvas: **Docker não foi testado**; o treino lê CSVs, ainda sem CRM; retreinar todo dia não garante acurácia melhor (o portão só promove se passar).

### Fase J — Camada SQLAlchemy e repositórios
**Solicitação**
- Usar SQLAlchemy com **um repositório por entidade** (pasta `repository/`).

**Resultado**
- `lead_core/persistence/`: `database.py`, `models/` e `repository/` (user, feedback, model_version, job). O ORM nunca cria tabelas; o DDL segue sendo `schema_v1.sql`.
- Services, routers e `ModelRegistry` usam só repositórios; novos `AuthService` e `JobService`. Dependência: `sqlalchemy>=2.0`.

### Fase K — Testes de regras de negócio
**Solicitação**
- Testes que cubram as regras de negócio.

**Resultado**
- Suíte de 169 para **408 testes** rápidos (+ 6 lentos).
- `test_business_rules.py` (matriz de faixas, prioridade, percentil, calibração, portão de qualidade), `test_use_cases.py` (11 cenários pela API), testes por repositório e `test_architecture.py` (proíbe SQL cru fora da persistência).

### Fase L — Revisão e documentação final
**Solicitação**
- Code review do backend (SOLID, KISS, design patterns, bad smells) só como relatório; `.gitignore`; README e plano do que falta.

**Resultado**
- Relatório de review (Docs), `.gitignore` no front e no back, `README.md` e `docs/PLANO_PENDENCIAS.md`.

### Fase M — Configuração do front
**Solicitação**
- Rodar o front exigia digitar `G4_API_URL=http://localhost:8000 npm run dev`; pedi um arquivo de configuração.

**Resultado**
- `frontend/.env` com `G4_API_URL` (modelo em `.env.example`; `.env` fica fora do git). Vale para o proxy do `npm run dev` e para `npm run test:integration`; variável de shell ainda sobrescreve.
- Corrigido o import do `vite.config.ts` (`vitest/config`, sem `.js`) que impedia o `npm run dev`.

### Fase N — Funil em heatmap
**Solicitação**
- "Corrija o funil com um heatmap", junto com uma análise "como vendedor sênior". Depois pedi para **esconder** o bloco da página.

**Resultado**
- `GET /summary` ganhou `funnel` (produto x faixas de tempo no funil, com contagem e valor esperado; as faixas vêm dos limiares do modelo). O front só desenha: `FunnelHeatmap`, com troca entre deals e valor esperado e clique que filtra a lista.
- Na base de exemplo, 80 de 104 deals caíam na faixa mais velha, o que mostrou o peso dos deals a revisar.
- A régua "Tempo no funil" do detalhe usa as mesmas quatro cores, e os rótulos que se sobrepunham foram corrigidos.
- O bloco foi removido da página por pedido; o componente e o campo `funnel` continuam no código (README explica como religar).

### Fase O — Coerência com o modelo
**Solicitação**
- Perguntei o que são "valor esperado" e "preço", o que é o feedback do vendedor e se o popup "Como a prioridade é calculada" condiz com o modelo e as regras.

**Resultado**
- Valor esperado = preço × chance de fechar (em 30 dias); explicado em linguagem simples.
- O popup tinha erros: dizia que "nenhum deal passou de X dias" (X é o P99), que Prospecção usa a taxa do produto (não tem índice), e não explicava "Decidir agora" nem o horizonte. Corrigido, com o horizonte vindo de `/meta` (`horizon_days`).

### Fase P — Semana x dia
**Solicitação**
- "Seu dia" e "Foco da semana" mostravam os mesmos deals. A semana deve ter mais leads que o dia.

**Resultado**
- Decisão minha: semana = prioridade **Alta + Média** (índice 40 ou mais), fora "Decidir agora" e "A revisar".
- `VIEWS` e `VIEW_OF_BAND` no backend (a aba `focus` agrupa `focus` e `follow_up`; `follow` ficou só com `low`). "Seu dia" é o topo do foco da semana. A aba "Seguir" virou "Baixa prioridade".
- Teste de integração: todo deal do dia está na semana.

### Fase Q — Sugestões de um vendedor externo
**Solicitação**
- Analisar um documento de sugestões, ver o que cabe no front e no backend e criar um plano com o que tem relevância média a alta; depois, implementar **somente a Fase 1**.

**Resultado**
- Plano em fases: transparência, validação, produtividade, gestão. Descartado o que os dados não sustentam (alertas por atividade, decisor/concorrência, edição de dados do deal).
- **Fase 1 implementada:**
  - Detalhe com indicadores separados: índice (posição, não probabilidade), preço, valor esperado (com horizonte) e probabilidade só se a API enviar.
  - Tabela de fatores (observado, referência, peso a favor/contra) a partir de `GET /deals/{id}`.
  - "Confiança da previsão" separada de "Completude dos dados" (`data_quality`; a conta não entra no modelo).
  - A chance em % só aparece se `calibration.useful` for verdadeiro; `G4_SHOW_PROBABILITY=false` esconde sempre (padrão do código passou a `true`).
- Fases 2 a 4 (feedback estruturado, filtros e próxima ação, histórico de prioridade, visão de gestão) seguem no plano.

## 4. Decisões que valem daqui para frente
- Esquema SQLite v1 **não muda** sem pedido explícito (nova versão = `schema_v2`).
- A API **nunca treina** por request.
- **O front não tem regra de negócio.**
- Acesso a banco só pela camada de repositórios.
- A v2 é a versão principal do front.
- O índice é uma posição, não uma probabilidade; a chance em % só aparece com calibração útil.
- Foco da semana = prioridade Alta + Média; "Seu dia" sai dele.
- A URL do backend fica em `frontend/.env` (`G4_API_URL`).

## 5. Pendências
Ver `docs/PLANO_PENDENCIAS.md`. Principais: autenticação com senha (schema v2), endpoints de Adiar/Encerrar/Marcar feito, fonte dos leads novos, validar Docker e agendamento, process-log. Do plano de melhorias: Fases 2 a 4 (feedback estruturado, "Ignorar" como ação comercial, filtros, histórico de prioridade, tela de gestor); snapshots das previsões.

## 6. Como rodar
```
# backend
cd solution/backend && cp .env.example .env
python3 -m venv .venv && source .venv/bin/activate
make install && make train && make api      # docs em http://localhost:8000/docs
make test

# frontend
cd solution/frontend && npm install && cp .env.example .env   # G4_API_URL
npm run dev                                 # API real; npm run dev:mock = sem backend
npm test && npm run typecheck
```
