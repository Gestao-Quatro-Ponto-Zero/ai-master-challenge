# Process Log — Lead Scorer (Challenge 003)

**Tempo total de desenvolvimento:** 4h37min (18:23 — 23:00, 30/03/2026)

## Ferramentas utilizadas

| Ferramenta | Uso | Etapa |
|------------|-----|-------|
| Claude Code (Opus 4) | Arquitetura, implementação, debugging, revisão | Todo o projeto |
| OpenAI GPT-4o-mini | Runtime — explicações de deals, recomendações, chat IA | Integrado na aplicação |
| Agente externo (via prompt) | Validação da lógica de scoring — revisão independente | Refinamento do scoring |
| Supabase | Banco de dados PostgreSQL, autenticação OTP, RLS | Infraestrutura |
| Vite + React | Frontend SPA | Interface |
| FastAPI | API REST | Backend |

## Workflow detalhado

### Fase 1 — Discussão e arquitetura (45min)

1. **Análise do caso**: leitura completa do challenge no GitHub, identificação dos requisitos obrigatórios e critérios de qualidade.
2. **Debate de arquitetura**: discutido entre Streamlit vs React, CSV local vs Supabase, deploy local vs cloud. Decisões:
   - Supabase como banco centralizado (35 vendedores em escritórios regionais não podem depender de CSV local)
   - Deploy em cloud (Hostinger/EasyPanel) para acesso via navegador sem instalação
   - Auth OTP por email com RBAC (admin/vendedor/manager)
3. **Definição do scoring**: 9 features iniciais com pesos, baseadas em análise dos dados disponíveis.
4. **Documento de arquitetura**: `infraestrutura_base.md` criado e iterado ao longo de toda a sessão.

### Fase 2 — Dados e Supabase (40min)

1. **Análise dos CSVs**: identificadas inconsistências ("GTXPro" sem espaço, "technolgy" typo), 1.425 deals sem conta definida.
2. **Correção dos dados**: aplicadas correções antes do import.
3. **Schema SQL**: criado com FKs surrogate (IDs numéricos), check constraints por deal stage, 8 índices, 6 RLS policies com helper functions.
4. **Import**: CSV → Supabase via porta 6543 (session mode) após descobrir que porta 5432 (transaction mode) cancelava statements.
5. **Mapeamento**: staging table com nomes → tabela definitiva com IDs via SQL JOIN.

### Fase 3 — Scoring engine (1h)

1. **Versão 1**: implementação inicial com 9 features. Score range: 29-61. Todos abaixo de 70. Problema: pipeline_aging zerava para 95% dos deals, potential_value dominado pelo GTK 500, win rates homogêneos.
2. **Versão 2**: sigmoid para aging, log scale para valores, desvio amplificado para win rates. Range melhorou para 27-77.
3. **Validação externa**: prompt enviado para agente externo que identificou: feedback loop no agent_performance, product_price_tier duplicado, deals sem conta penalizados demais, Prospecting generoso demais com 0.5.
4. **Versão 3 (final)**: colapsou win_rate_sector + win_rate_product, adicionou agent_load (concentração de pipeline), reduziu agent_performance, clamp 0.05-0.95, Prospecting = 0.30, mediana parcial para deals sem conta. Range final: 39-77.

### Fase 4 — Interface (2h)

1. **Streamlit (tentativa 1)**: implementado e funcional, mas extremamente travado. Streamlit re-executa script inteiro a cada interação — inviável com 2.089 deals + filtros + expanders.
2. **Migração para React + FastAPI**: decisão de retrabalho. Backend Python preservado (scoring, IA), frontend reconstruído em React.
3. **FastAPI API**: 12 endpoints, auth JWT com cache, endpoint `/api/init` que carrega tudo de uma vez.
4. **React SPA**: Sidebar, Dashboard com gráficos, Pipeline com zonas, Histórico, Chat flutuante.
5. **Iterações visuais**: dark theme → light theme alinhado ao design system G4 (Manrope, navy/gold, cards brancos), emojis → Lucide icons, traduções PT-BR.

### Fase 5 — IA e refinamentos (30min)

1. **Chat IA**: contexto completo injetado (métricas, zonas, top 10, distribuição por produto/conta/vendedor, histórico, critérios de score).
2. **Output HTML**: prompts ajustados para retornar HTML formatado em vez de markdown.
3. **CRUD de deals**: criar oportunidade (formulário com dropdowns), classificar como Ganho/Perdido.
4. **Filtros e export**: filtros por etapa/produto/vendedor/escritório, export CSV.

## Onde a IA errou e como corrigi

### 1. Scoring comprimido (v1)
**Erro da IA**: implementou normalização min-max simples para potential_value e pipeline_aging. Com um produto custando R$26.768 e os outros abaixo de R$5.500, 6 de 7 produtos ficaram abaixo de 0.21. Com ciclo médio de 48 dias e deals ativos há 165+ dias, 95% dos deals tinham aging = 0.

**Minha correção**: identifiquei o problema analisando os dados, solicitei reformulação com log scale e sigmoid. Validei com agente externo que confirmou e sugeriu melhorias adicionais.

### 2. product_price_tier duplicado
**Erro da IA**: criou feature `product_price_tier` que era literalmente `features["product_price_tier"] = features["potential_value"]` — cópia exata, desperdiçando 5% de peso.

**Minha correção**: detectado na revisão com agente externo. Removido e peso redistribuído.

### 3. Streamlit como frontend
**Erro de decisão**: escolhi Streamlit inicialmente por rapidez, mas com 2.089 deals a interface ficou inutilizável. Cada clique de filtro re-executava todo o script Python.

**Minha correção**: migrei para React + FastAPI. Retrabalho de ~2h mas resultado muito superior.

### 4. Import via porta 5432 do Supabase
**Erro técnico**: tentei importar dados via connection pooler (porta 5432, transaction mode). Statements eram cancelados por timeout do PgBouncer.

**Minha correção**: diagnostiquei que o pooler em transaction mode não persiste `SET statement_timeout`. Mudei para porta 6543 (session mode) e imports funcionaram.

### 5. Auth OTP vs Magic Link
**Descoberta**: Supabase envia Magic Link por padrão, não código OTP numérico. O fluxo precisou ser adaptado.

### 6. Paginação do Supabase
**Erro da IA**: query inicial carregava apenas 1.000 de 8.800 registros (limite padrão do Supabase REST API).

**Minha correção**: implementei paginação com `.range(offset, offset + 999)` em loop.

### 7. Feedback loop do agent_performance
**Identificado pelo agente externo**: vendedores com win rate baixo recebiam scores piores → focavam em menos deals → perdiam mais → loop negativo. O range também era assimétrico (0.0-0.57).

**Correção**: reduzido peso de 0.12 para 0.05, simetrizado o range com multiplicador 3.

## O que eu adicionei além do que a IA sugeriu

1. **Decisão de Supabase centralizado** (em vez de CSV local) — motivada pela observação de que 35 vendedores em escritórios regionais não podem depender de arquivo local.

2. **Validação externa do scoring** — enviei prompt detalhado para agente externo avaliar a lógica. A IA que construiu o scoring não teria identificado seus próprios problemas.

3. **Migração Streamlit → React** — a IA teria continuado otimizando Streamlit indefinidamente. A decisão de retrabalho foi minha.

4. **Feature agent_load** — proposta pelo agente externo e implementada. Vendedores sobrecarregados (194 deals) têm menos capacidade de foco que vendedores com 31 deals.

5. **Design alinhado ao G4** — pesquisei o site do G4 e apliquei cores (navy/gold), tipografia (Manrope), patterns visuais.

6. **UX de classificação de deals** — botões "Ganho" (pede valor antes de confirmar) e "Perdido" (direto) no card expandido. Não foi solicitado pelo challenge.

7. **Tradução contextual** — Won/Lost → Ganho/Perdido, Engaging → Em Negociação, Win Rate → Taxa de Conversão. Decisão baseada no público-alvo (vendedores BR).

8. **Tratamento de dados inconsistentes** — correção de typos, deals sem conta, validação de integridade de FKs antes do import.

### Fase 6 — Refinamentos finais

1. **Scoring v4**: validação por agente externo identificou 8 ações prioritárias. Implementadas: clamp 0.05-0.95, agent_load reformulado (desvio da média, simétrico), potential_value com contexto da conta (70% preço + 30% preço×porte), REFERENCE_DATE configurável via env var.

2. **Dark mode completo**: substituídos todos os `bg-white` hardcoded por `var(--bg-secondary)`. Criadas variáveis de status por tema (`--won-text`, `--lost-text`, `--engaging-text`, etc.) — cores escuras no light mode, claras no dark mode.

3. **Guardrails de IA**: adicionadas regras anti-prompt injection, anti-invenção de dados, anti-vazamento de system prompt. Critérios de score atualizados no contexto (v4 com 8 features corretas).

4. **Pipeline Health Score**: indicador composto de saúde do pipeline (5 fatores: volume, qualidade, conversão, score médio, risco).

5. **Comparação side-by-side**: modal para comparar 2 oportunidades com recomendação automática de qual priorizar.

6. **CRUD de deals**: criar oportunidade (formulário com dropdowns), classificar como Ganho (com valor) ou Perdido. Bug corrigido: deals em Prospecção não tinham engage_date — agora preenchida automaticamente ao classificar.

7. **22 testes de validação**: test_scoring.py (10 checks) + test_pipeline.py (12 checks) — todos passando.

8. **Correções de build**: 4 erros TypeScript corrigidos, Dockerfile atualizado de Streamlit para FastAPI, colunas fantasma removidas do endpoint /api/init.

## Evidências

- Documento de arquitetura iterado: `infraestrutura_base.md`
- Schema SQL versionado: `supabase/schema.sql`
- Script de import: `supabase/import_pipeline.sql`
- Histórico de iterações do scoring documentado neste arquivo
- Prompt de validação externa e resposta integrados nas decisões
- Testes automatizados: `test_scoring.py` (10 validações) + `test_pipeline.py` (12 validações)
- Build de produção limpo (TypeScript + Vite)
