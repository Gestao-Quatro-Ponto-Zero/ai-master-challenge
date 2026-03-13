# CLAUDE.md — RavenStack Churn Intelligence

Arquivo de contexto para o Claude Code. Leia este arquivo no início de cada sessão antes de qualquer tarefa.

---

## 1. Visão geral do projeto

**RavenStack** é uma plataforma SaaS B2B de gerenciamento de projetos com modelo de assinatura recorrente. O negócio enfrenta churn crescente e precisa de inteligência acionável — não apenas dashboards, mas respostas às causas raiz.

**O que este sistema entrega:**
- Pipeline de dados raw → bronze → silver → gold (DuckDB + Parquet)
- Dashboard interativo de análise de churn (Streamlit)
- Agente conversacional que responde perguntas de negócio sobre churn (Agno + Claude)
- Diagnóstico estruturado em 3 perguntas estratégicas (ver Seção 8)

**Stack:** Python · DuckDB · Parquet · Streamlit · Agno · Claude API

---

## 2. Metodologia SDD (Spec-Driven Development)

A especificação do sistema está em `/docs/` dividida em 3 layers. Consulte cada um antes de implementar:

| Layer | Diretório | Quando consultar |
|-------|-----------|-----------------|
| Business | `docs/01-business/` | Regras de negócio, definições de churn, KPIs, playbook de retenção |
| Product | `docs/02-product/` | Casos de uso, fluxos do usuário, requisitos do dashboard e agente |
| Engineering | `docs/03-engineering/` | Schema detalhado, arquitetura do pipeline, contratos de dados |

**Nunca implemente sem ler o spec relevante primeiro.**

---

## 3. Arquitetura do sistema

```
data/raw/*.csv
      │
      ▼
┌─────────────┐
│   BRONZE    │  pipeline/bronze/ingest.py
│  (Parquet)  │  Ingestão direta, sem transformação
│ data/bronze/│  Preserva schema original
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   SILVER    │  pipeline/silver/transform.py
│  (Parquet)  │  Limpeza, tipagem, deduplicação
│ data/silver/│  Enriquecimento: churn_flag unificado, datas parsed
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    GOLD     │  pipeline/gold/aggregate.py
│  (Parquet)  │  Métricas agregadas, scores de risco
│  data/gold/ │  Pronta para consumo pelo dashboard e agente
└──────┬──────┘
       │
       ├──────────────────────┐
       ▼                      ▼
┌─────────────┐      ┌──────────────────┐
│  DASHBOARD  │      │     AGENTE       │
│  Streamlit  │      │  Agno + Claude   │
│app/dashboard│      │   app/agent/     │
└─────────────┘      └──────────────────┘
```

---

## 4. Schema real dos CSVs

Os arquivos estão em `data/raw/`. Colunas exatas:

### accounts (`ravenstack_accounts.csv`)
```
account_id, account_name, industry, country, signup_date,
referral_source, plan_tier, seats, is_trial, churn_flag
```

### subscriptions (`ravenstack_subscriptions.csv`)
```
subscription_id, account_id, start_date, end_date, plan_tier,
seats, mrr_amount, arr_amount, is_trial, upgrade_flag,
downgrade_flag, churn_flag, billing_frequency, auto_renew_flag
```

### feature_usage (`ravenstack_feature_usage.csv`)
```
usage_id, subscription_id, usage_date, feature_name,
usage_count, usage_duration_secs, error_count, is_beta_feature
```

### support_tickets (`ravenstack_support_tickets.csv`)
```
ticket_id, account_id, submitted_at, closed_at,
resolution_time_hours, priority, first_response_time_minutes,
satisfaction_score, escalation_flag
```

### churn_events (`ravenstack_churn_events.csv`)
```
churn_event_id, account_id, churn_date, reason_code,
refund_amount_usd, preceding_upgrade_flag, preceding_downgrade_flag,
is_reactivation, feedback_text
```

---

## 5. Comandos essenciais

| Comando | O que faz |
|---------|-----------|
| `/run-pipeline` | Executa bronze → silver → gold |
| `/run-dashboard` | Inicia o Streamlit dashboard |
| `/diagnose [período]` | Responde as 3 perguntas diagnósticas |
| `/check-data` | Valida CSVs e Parquets |

Ver detalhes em `.claude/commands/`.

**Execução manual:**
```bash
python pipeline/bronze/ingest.py
python pipeline/silver/transform.py
python pipeline/gold/aggregate.py
streamlit run app/dashboard/main.py
```

---

## 6. Regras de código

### DuckDB
- Sempre usar `read_parquet()` e `read_csv_auto()` — nunca carregar tudo em memória
- Conexões em modo read-only para queries de leitura: `duckdb.connect(read_only=True)`
- Prefira SQL sobre pandas para transformações — DuckDB é o motor de processamento
- Nomes de tabelas no SQL: snake_case, singular (`account`, `subscription`)

### Python
- Python 3.11+
- Dependências gerenciadas com `uv` (preferencial) ou `pip`
- Type hints em funções públicas
- Sem classes desnecessárias — funções são suficientes no pipeline
- Logging com `logging` stdlib, não `print`

### Streamlit
- Cache com `@st.cache_data` para queries pesadas
- Filtros na sidebar, visualizações no corpo principal
- Sem estado global mutável fora de `st.session_state`
- Gráficos com Plotly (interativos) ou Altair (declarativos)

### Agno (agente)
- O agente tem acesso às gold tables via DuckDB tool
- Respostas sempre em português, tom executivo
- Cada afirmação factual deve citar o número que a sustenta
- O agente DEVE usar o playbook de retenção de `docs/01-business/` para recomendar ações

---

## 7. Restrições obrigatórias

- **Nunca** modificar arquivos em `data/raw/` — são dados imutáveis
- **Nunca** fazer `rm -rf` em qualquer diretório de dados
- **Nunca** fazer `git push` sem revisão explícita do usuário
- **Nunca** hardcodar credenciais — usar variáveis de ambiente
- **Nunca** responder uma pergunta de negócio sem citar um dado que a sustente
- **Nunca** ignorar o spec em `docs/` ao implementar uma feature
- **Não** usar pandas para transformações que o DuckDB consegue fazer
- **Não** criar visualizações sem dados reais — sem dados mock no dashboard

---

## 8. As 3 Perguntas Diagnósticas

O agente e o dashboard DEVEM ser capazes de responder estas perguntas para qualquer período:

### P1: O que está causando o churn?
- Causa raiz identificada nos dados (reason_code + correlações)
- Cruzamento: churn_events × feature_usage × support_tickets × subscriptions
- Cada causa deve ter percentual do total de churns

### P2: Quais segmentos estão mais em risco?
- Segmentos: industry, plan_tier, country, referral_source
- Contas específicas com risk_score mais alto (nome + MRR em risco)
- Tendência: churn rate aumentando ou estabilizando

### P3: O que a empresa deveria fazer?
- 2-3 ações concretas com público-alvo definido
- Impacto estimado em MRR ou redução de churn rate (em pontos percentuais)
- Baseado no playbook de retenção em `docs/01-business/`

Use `/diagnose` para gerar este diagnóstico automaticamente.

---

## 9. Comportamento do agente

**Idioma:** Português brasileiro (respostas ao usuário sempre em PT-BR)

**Tom:** Executivo e direto — como um analista de dados falando com o CEO. Sem jargão técnico desnecessário.

**Formato de resposta padrão:**
1. Conclusão principal (1 frase com o número mais importante)
2. Evidências (2-3 bullets com dados)
3. Recomendação (1 ação concreta)

**Uso obrigatório do playbook:**
Antes de recomendar qualquer ação de retenção, o agente deve verificar se existe uma estratégia correspondente em `docs/01-business/`. As recomendações devem ser consistentes com o playbook.

**O que o agente NÃO faz:**
- Não especula sem dados ("provavelmente", "talvez")
- Não repete a pergunta antes de responder
- Não descreve o que vai fazer antes de fazer
- Não pede confirmação para queries de leitura

---

## Estrutura de diretórios

```
ai-master-challenge/
├── CLAUDE.md              ← Este arquivo
├── .claude/
│   ├── settings.json      ← Permissões de ferramentas
│   └── commands/
│       ├── run-pipeline.md
│       ├── run-dashboard.md
│       ├── diagnose.md
│       └── check-data.md
├── data/
│   ├── raw/               ← CSVs originais (imutáveis)
│   ├── bronze/            ← Parquet pós-ingestão
│   ├── silver/            ← Parquet pós-transformação
│   └── gold/              ← Parquet com métricas agregadas
├── pipeline/
│   ├── bronze/ingest.py
│   ├── silver/transform.py
│   └── gold/aggregate.py
├── app/
│   ├── dashboard/         ← Streamlit
│   └── agent/             ← Agno + Claude
└── docs/
    ├── 01-business/
    ├── 02-product/
    └── 03-engineering/
```
