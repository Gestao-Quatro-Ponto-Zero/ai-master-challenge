# Prompt 002 — Agent EDA

**Data:** 2026-03-20
**Agent:** 01_eda_agent.py
**Ferramenta:** Claude Code
**Executado por:** Lucas Reis

---

## Prompt enviado ao Claude Code

> Contexto: projeto G4 AI Master Challenge — Challenge 001 Diagnóstico de Churn.
> Leia o CLAUDE.md e docs/data_dictionary.md antes de começar.
>
> Você é o Agent 01 — EDA. Execute o arquivo solution/agents/01_eda_agent.py
> contra os 5 CSVs reais em solution/data/ e produza o perfil completo dos dados.
>
> Rode: python submissions/lucas-reis/solution/agents/01_eda_agent.py
>
> Se houver qualquer erro de importação, instale as dependências faltantes e tente novamente.
>
> [Análises específicas por tabela solicitadas: shape, nulos, distribuições, top features,
> satisfaction_score, priority incluindo urgent, churn_events antes/depois dedup,
> resumo executivo com taxa de churn e red flags]
>
> Após execução: salvar output em entry_001_eda_output.md, análise em entry_001_eda_analysis.md,
> preencher este prompt_002_eda.md.

---

## Preparação necessária

O `01_eda_agent.py` original era um profiler genérico. Foi expandido para produzir
as análises específicas por tabela solicitadas no prompt antes da execução.

**Dependências instaladas:**
```bash
pip3 install duckdb pandas numpy
```
Ambiente: Python 3 do sistema macOS (`/usr/bin/python3`), sem virtualenv.

**Comando executado:**
```bash
cd "/Users/lucasreis/.../ai-master-challenge"
python3 submissions/lucas-reis/solution/agents/01_eda_agent.py
```

**Status:** ✅ Sucesso sem erros de execução.

---

## Números mais importantes do output

| Tabela | Métrica | Valor | Importância |
|--------|---------|-------|-------------|
| accounts | churn_flag = True | **110 / 500 = 22.0%** | TARGET real do modelo |
| accounts | is_trial = True | 97 / 500 = 19.4% | Alta proporção de trials |
| subscriptions | end_date nulo | 90.28% | 90% das subs ativas |
| subscriptions | auto_renew = False | 995 = 19.9% | Sinal de intenção de sair |
| subscriptions | downgrade_flag | 218 = 4.4% | Mais baixo que esperado |
| subscriptions | upgrade_flag | 529 = 10.6% | 2.4x mais upgrades que downgrades |
| subscriptions | MRR min = $0 | Todos os tiers | ⚠️ Trials com MRR zero |
| feature_usage | Sessão mediana | 46 min | ⚠️ Muito longa — verificar |
| feature_usage | error_count max | 0.669 (feature_4) | Correlação com churn a testar |
| support_tickets | satisfaction nulo | **825 = 41.2%** | 🚨 Sinal de desengajamento |
| support_tickets | urgent tickets | 514 = 25.7% | 🚨 Alto — SLA quebrado |
| support_tickets | urgent response time | 85.5 min | 🚨 Quase igual a low (91 min) |
| churn_events | Antes dedup | 600 linhas | |
| churn_events | Depois dedup | **352 unique accounts** | ⚠️ 70.4% — ERRADO como target |
| churn_events | reason_code #1 | features 19% | Features, não preço |
| churn_events | preceding_upgrade | **64 = 18.2%** | 🚨 Buyer's remorse |
| churn_events | preceding_downgrade | 30 = 8.5% | Mais baixo que upgrade |

---

## Erros encontrados e como foram resolvidos

### Erro 1 — `python` não encontrado
```
/bin/bash: python: command not found
```
**Resolução:** usar `python3` explicitamente no macOS.

### Erro 2 — `ModuleNotFoundError: No module named 'duckdb'`
```bash
pip3 install duckdb pandas numpy
```
**Resolução:** instalação direta via pip3 do sistema.

### Descoberta crítica durante EDA
O EDA revelou que o Agent 02 usa uma **target variable errada**.
A discrepância 70.4% (churn_events dedup) vs 22.0% (accounts.churn_flag) indica que
`churn_events` captura cancelamentos de subscrições individuais, não churn de conta.

**Correção necessária:** trocar o target do Agent 02 de `latest_churn.churned`
para `a.churn_flag` (accounts.churn_flag).

---

## Decisão estratégica tomada

A leitura cuidadosa do EDA revelou que a arquitetura do Agent 02 precisava de uma
correção fundamental antes de qualquer execução. Esta decisão — parar e corrigir
antes de avançar — é um exemplo de julgamento humano que a IA não tomaria sozinha:
o script original do Agent 02 teria rodado, produzido resultados, e o erro só seria
detectado ao checar a taxa de churn de 70.4% no relatório final.

A próxima sessão deve primeiro corrigir o Agent 02 (target variable), depois executar
o cross-table analysis.
