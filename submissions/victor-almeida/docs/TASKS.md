# TASKS.md — Lead Scorer (Challenge 003)

## Convenção de status

- `[ ]` — Pendente (não iniciada)
- `[~]` — Em progresso
- `[x]` — Concluída

---

## Fase 1: Fundação de Dados ✅

### 1. Data Model — [specs/data_model.md](specs/data_model.md)

- [x] 1.1 Criar módulo `utils/data_loader.py` com funções `load_data()`, `load_accounts()`, `load_products()`, `load_sales_teams()`, `load_pipeline()`
- [x] 1.2 Implementar normalização de dados (GTXPro → GTX Pro, technolgy → technology)
- [x] 1.3 Implementar conversão de tipos (engage_date/close_date → datetime64, close_value → numeric)
- [x] 1.4 Calcular colunas derivadas (is_active, days_in_stage, sales_price, sector, revenue, employees, manager, regional_office via JOINs)
- [x] 1.5 Implementar validações de integridade (volumetria, PKs únicas, stages válidos, integridade referencial, nullability por stage)
- [x] 1.6 Criar módulo de constantes com preços de produtos, win rates, benchmarks de velocidade, thresholds
- [x] 1.7 Implementar `get_active_deals()` e `get_reference_date()`
- [x] 1.8 Escrever e passar todos os testes em `tests/test_data_loader.py` (27 testes)

---

## Fase 2: Motor de Scoring ✅

### 2. Scoring Engine — [specs/scoring_engine.md](specs/scoring_engine.md)

- [x] 2.1 Criar `scoring/constants.py` com pesos, STAGE_SCORES, DECAY_TABLE, thresholds de seller-fit e account-health
- [x] 2.2 Implementar `scoring/velocity.py` — cálculo de days_in_stage e score de velocidade com decay exponencial
- [x] 2.3 Implementar `scoring/seller_fit.py` — build_seller_fit_stats() e calculate_seller_fit_score() com threshold de 5 deals
- [x] 2.4 Implementar `scoring/account_health.py` — build_account_health_stats() e calculate_account_health_score() com penalidade por losses recentes
- [x] 2.5 Implementar cálculo de stage score (Prospecting=30, Engaging=70) e value score (log-scaled)
- [x] 2.6 Criar classe `ScoringEngine` em `scoring/engine.py` — orquestrador com score_pipeline() e score_single_deal()
- [x] 2.7 Implementar explainability — geração de texto explicativo para cada componente do score
- [x] 2.8 Escrever e passar todos os testes em `tests/test_scoring_engine.py` (38 testes: 4 stage + 6 value + 7 velocity + 7 seller-fit + 5 account-health + 9 integração)

---

## Fase 3: Detecção de Anomalias ✅

### 3. Deal Zombie — [specs/deal_zombie.md](specs/deal_zombie.md)

- [x] 3.1 Criar `scoring/deal_zombie.py` com função `classify_zombies()` — classificação por tempo no stage (threshold: 2× referência de 88 dias)
- [x] 3.2 Implementar severidade de zumbi (Zumbi, Zumbi Crítico, Zumbi Crônico) e estimativa de valor
- [x] 3.3 Implementar `classify_accounts()` — detecção de conta com perda recorrente (≥2 losses) e alto risco (≥5 losses)
- [x] 3.4 Implementar `get_zombie_summary()` — métricas agregadas (total zumbis, pipeline inflado, % zumbis)
- [x] 3.5 Implementar `get_zombie_summary_by_seller()` — agregação por vendedor com manager e escritório
- [x] 3.6 Escrever e passar todos os testes em `tests/test_deal_zombie.py` (19 testes: 5 classificação + 3 crítico + 4 conta + 2 valor + 3 summary + 2 sanidade)

---

## Fase 4: Ações Recomendadas ✅

### 4. Next Best Action (NBA) — [specs/next_best_action.md](specs/next_best_action.md)

- [x] 4.1 Criar `scoring/nba.py` com estruturas NBAContext, RegraAplicavel, NBAResult
- [x] 4.2 Implementar regras individuais: NBA-01 (Deal Parado), NBA-02 (Deal em Risco), NBA-04 (Seller Fit Baixo), NBA-05 (Conta Problemática), NBA-06 (Prioridade Máxima), NBA-06B (Prospecting Alto Valor), NBA-ZB (Zumbi)
- [x] 4.3 Implementar resolução de prioridade — regra de maior prioridade vira ação principal, secundárias limitadas a 2
- [x] 4.4 Implementar cálculo de contexto — top sellers por setor, referência de prospecting, percentil 75 de valor
- [x] 4.5 Implementar `calcular_nba()` e `calcular_nba_batch()` com tratamento de edge cases (sem regras → fallback, Prospecting sem dados temporais, conta nova)
- [x] 4.6 Escrever e passar todos os testes em `tests/test_nba.py` (20 testes: 9 regras + 3 prioridade + 2 zumbi + 4 edge cases + 2 dados reais)

---

## Fase 5: Interface — Componentes ✅

### 5. Formatters — [specs/ui_ux.md](specs/ui_ux.md)

- [x] 5.1 Criar `utils/formatters.py` com format_currency(), format_percentage(), format_days(), score_color(), score_label()
- [x] 5.2 Escrever e passar todos os testes em `tests/test_formatters.py` (14 testes: 5 moeda + 3 percentual + 2 dias + 4 cor)

### 6. Filtros — [specs/filters.md](specs/filters.md)

- [x] 6.1 Criar `components/filters.py` com FilterState dataclass e constantes
- [x] 6.2 Implementar cascata hierárquica (Região → Manager → Vendedor) com reset automático via session_state
- [x] 6.3 Implementar `render_filters()` — 7 filtros no sidebar agrupados (Visão + Filtros + Resumo)
- [x] 6.4 Implementar `apply_filters()` — lógica AND com boolean masking, tratamento de multiselect vazio e modos de zumbi
- [x] 6.5 Implementar `render_filter_summary()` — contagem de deals e valor total no rodapé do sidebar
- [x] 6.6 Escrever e passar todos os testes em `tests/test_filters.py` (16 testes: 5 cascata + 8 apply_filters + 3 edge cases)

### 7. Métricas — [specs/metrics_summary.md](specs/metrics_summary.md)

- [x] 7.1 Criar `components/metrics.py` com render_metrics(df_filtered, df_all, active_filters)
- [x] 7.2 Implementar 4 KPI cards (Deals Ativos, Pipeline Total, Deals Zumbis, Win Rate) com deltas condicionais
- [x] 7.3 Implementar gráfico de distribuição de score (4 faixas com cores: Crítico/Risco/Atenção/Alta)
- [x] 7.4 Implementar donut de saúde do pipeline (Saudáveis vs Zumbis)
- [x] 7.5 Implementar comparação de win rate condicional (vendedor vs time vs geral / visão por manager)
- [x] 7.6 Escrever e passar todos os testes em `tests/test_metrics.py` (17 testes: 5 KPI + 3 moeda + 4 distribuição + 2 saúde + 2 edge cases)

### 8. Pipeline View — [specs/pipeline_view.md](specs/pipeline_view.md)

- [x] 8.1 Criar `components/pipeline_view.py` com tabela de 8 colunas (Score, Deal, Conta, Produto, Valor, Stage, Dias no Stage, Vendedor)
- [x] 8.2 Implementar color coding por score (verde ≥80, amarelo 60-79, laranja 40-59, vermelho <40) e flags de zumbi
- [x] 8.3 Implementar formatação de colunas (valor em USD, dias, "Sem conta" para null, "—" para Prospecting)
- [x] 8.4 Criar `components/deal_detail.py` com expander — score breakdown (5 componentes), explicação textual, NBA card
- [x] 8.5 Implementar paginação/scroll virtual para ~2.000 deals ativos
- [x] 8.6 Escrever e passar todos os testes em `tests/test_pipeline_view.py` (16 testes: 6 integridade + 4 cor + 4 deal detail + 2 formatação)

---

## Fase 6: Integração Final

### 9. App Principal — [specs/ui_ux.md](specs/ui_ux.md)

- [ ] 9.1 Criar `app.py` — orquestrador principal do Streamlit (page config, CSS, caching, fluxo de dados)
- [ ] 9.2 Integrar todos os componentes: filters → scoring → metrics → pipeline_view → deal_detail
- [ ] 9.3 Implementar session_state para deal selecionado e estado dos filtros
- [ ] 9.4 Otimizar performance (@st.cache_data para load e scoring, target: load <3s, filtro <500ms)
- [ ] 9.5 Teste manual end-to-end: fluxo completo vendedor/manager/RevOps

---

## Fase 7: Entrega

### 10. Documentação e Submissão

- [ ] 10.1 Criar `submissions/victor-almeida/README.md` seguindo o template obrigatório
- [ ] 10.2 Criar process-log com evidências de uso de IA (screenshots, chat exports, decisões)
- [ ] 10.3 Validar que toda a solução está dentro de `submissions/victor-almeida/`
- [ ] 10.4 Testar setup do zero (pip install + streamlit run)
- [ ] 10.5 Criar PR: `[Submission] Victor Almeida — Challenge 003` na branch `submission/victor-almeida`
