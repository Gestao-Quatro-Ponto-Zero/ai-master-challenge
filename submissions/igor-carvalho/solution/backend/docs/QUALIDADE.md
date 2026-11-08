# Revisão de qualidade — G4 Lead Scorer

Data: 2026-11-07 · Ferramentas: radon 6 (CC/MI), ruff (E,F,W,B,SIM,UP,N), leitura do código · Testes: 158 passando.
**Nada abaixo foi implementado** — é o backlog.

## 1. Complexidade
| Métrica | Resultado |
|---|---|
| Código-fonte | ~2.000 linhas em 3 pacotes; maior arquivo 160 linhas |
| Complexidade ciclomática média | **A (2,2)** |
| Funções em B (6–10) | 11 (`assign_band` 10, `backtest` 9, `main` do CLI 8, `fit_gbm` 8, `current_user` 7, `WhatIfService.score` 7 …) |
| Funções em C (11–20) | **1**: `pipeline.run_training` (11) |
| Maintainability Index | todos os módulos em A |
| Comentários / docstrings | ~2% de linhas de comentário (docstrings curtas nas funções-chave) |
| Ruff | 79 achados, 0 erros de lógica: 29 `B008` (padrão `Depends()` do FastAPI — falso positivo), 27 `UP045` e 4 `UP035` (estilo de typing), 7 `N803`/5 `N806` (`X`, `T` — convenção de ML), 2 `B904`, 2 `B905`, 1 `B023` (falso positivo: lambda chamada na mesma iteração) |

Leitura: baixa complexidade geral; o único ponto de atenção é `run_training`, que orquestra 8 etapas.

## 2. Padrões adotados (o que está bom)
- **Camadas e dependências em uma direção**: `lead_core` ← `lead_trainer` / `lead_api`; testes automáticos garantem que a API não importa o treinador e o core não importa nenhum dos dois.
- **Uma só implementação de features** para treino, lote e what-if (teste compara os três resultados).
- **Router → Service → Store/Repository**; routers finos; erros num formato único; settings por ambiente (12-factor).
- **Injeção por construtor** (`Container`, `FakeRunner` nos testes, `clock` injetável no treino) e `DealRepository` como Protocol.
- **Esquema congelado com hash**, `schema` único e índices parciais impondo invariantes (1 modelo ativo, 1 retreino por vez).
- Pirâmide de testes: unitários, serviço/API, contrato, arquitetura, performance e dataset real.

## 3. SOLID
| Princípio | Avaliação | Observação |
|---|---|---|
| **S** — responsabilidade única | Boa, com 3 exceções | `pipeline.run_training` mistura orquestração, montagem do model card, decisão de promoção e formatação do resultado; `cli.main` mistura parsing, wiring e formatação; `ModelBundle` junta persistência, predição, explicação e score |
| **O** — aberto/fechado | Média | Novas faixas/regras exigem editar `assign_band` (if/elif); novo motor (ex.: regras) exigiria editar `ModelBundle`/`pipeline`; novos filtros em `DealQueryService._filter` idem |
| **L** — Liskov | Boa | `DealRepository` e `JobRunner` têm substitutos (Fake) usados em testes sem quebrar contratos |
| **I** — segregação de interfaces | Boa | Protocols pequenos; pequeno vazamento: serviços recebem `LoadedModel` inteiro mesmo usando só parte |
| **D** — inversão de dependência | Média | Treinador depende de `ModelRegistry`/`CsvDealRepository` concretos (só o repositório é injetável); routers acessam `container.*` direto e `session(db_path)` em `auth`/`admin` (SQL fora de repositórios); SQL cru em services |

## 4. Backlog de melhorias (para depois)
Prioridade: **P1** fazer logo · **P2** próxima sprint · **P3** quando houver necessidade. Esforço: S (<½ dia) · M (1–2 dias) · L (>2 dias).

### Estrutura / SOLID
- [ ] **P1·M** Quebrar `run_training` (CC 11) em etapas: `TrainingPipeline` com métodos `fit()`, `build_card()`, `decide_promotion()`, `persist()`; mover `closed_durations`/limiares para `lead_core.bands`.
- [ ] **P1·S** Extrair a decisão de promoção (`quality_gate` + `--force` + backtest ignorado) para uma `PromotionPolicy` testável isoladamente.
- [ ] **P2·M** Dividir `ModelBundle`: `BundleStore` (save/load), `Scorer` (predict/score) e `Explainer` (contribuições/motivos).
- [ ] **P2·M** Tornar `assign_band` data-driven (lista ordenada de regras) para abrir/fechar extensão; fazer o mesmo com filtros de `DealQueryService._filter`.
- [ ] **P2·M** Criar `UserRepository` e `FeedbackRepository` (hoje há SQL em `routers/auth`, `routers/admin` e `services/feedback`); routers só chamam services.
- [ ] **P2·S** Injetar `ModelRegistry` e `Clock` no treinador; reduzir `cli.main` (CC 8) com sub-comandos em funções registradas.
- [ ] **P3·S** Serviços receberem apenas o que usam (ex.: `ScoringContext`) em vez de `LoadedModel`.

### Desempenho / escala
- [ ] **P1·S** `ModelBundle.score` usa `iterrows` no cálculo de motivos por linha; vetorizar contribuições e montar motivos só para a página retornada (já é lazy no detalhe; revisar listagem).
- [ ] **P2·M** Rate limiter em memória é por processo; trocar por Redis (ou `slowapi` + backend compartilhado) ao rodar com vários workers.
- [ ] **P2·M** Fila de jobs real (RQ/Celery ou tabela + worker) em vez de subprocesso disparado pela API; reaproveitar o contrato `JobRunner`.
- [ ] **P3·M** Cache de listagem por (usuário, filtros) com invalidação no `refresh`; hoje cada request refiltra o DataFrame.
- [ ] **P3·L** Migrar plain `sqlite3` para SQLAlchemy + Alembic ao trocar para Postgres (o esquema v1 permanece, migrações novas seriam v2+ somente com pedido explícito).

### Modelo / produto
- [ ] **P1·M** Implementar o fallback `MODEL_ENGINE=rules` (previsto no plano): mesmo contrato, score por regras quando o portão rejeitar o GBM.
- [ ] **P1·S** Motivos: `sales_agent` entra como driver categórico opaco; agrupar em "histórico do vendedor" ou excluir da explicação.
- [ ] **P2·M** Agendar retreino (cron/CI) e registrar métricas por versão para monitorar drift (AUC por janela, distribuição de score).
- [ ] **P2·M** Pipeline de feedback → treino: usar `deal_feedback` (worked/disagree) como sinal de avaliação, não como label.
- [ ] **P3·M** Campos fora do dataset (último contato, meta, próxima ação) hoje inexistentes na API; definir fonte antes de expor.
- [ ] **P3·S** Mapeamento Firestore/Firebase do contrato (oferta ainda em aberto).

### Qualidade / operação
- [ ] **P1·S** Rodar `ruff --fix` nos 32 achados automáticos (UP045/UP035/UP037) e ajustar `B904` (`raise ... from`) e `B905` (`zip(strict=)`); configurar `per-file-ignores` para `B008` (FastAPI) e `N803/N806` (`X`, `T`).
- [ ] **P1·S** CI (GitHub Actions): ruff + pytest + radon com gate (CC ≤ 10 por função, MI ≥ A).
- [ ] **P2·S** Dockerfile (um para API, um para trainer) + `docker-compose` com volume para `artifacts/` e `var/`.
- [ ] **P2·S** Logs estruturados (JSON) com `request_id`, métricas Prometheus (`/metrics`), tracing opcional.
- [ ] **P2·S** Rotação de segredo JWT e troca do login por `user_key` por SSO/OIDC antes de produção.
- [ ] **P3·S** Testes de propriedade (hypothesis) para `score_from_ev` e filtros; cobertura (`pytest-cov`) com meta ≥ 85%.
- [ ] **P3·S** Mais docstrings/ADRs nas decisões de modelagem (point-in-time, shrinkage K=30, alvo de 30 dias, shift de nível) — ver docs/MODELO.md.
