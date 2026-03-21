# Support Triage — Challenge 002

Sistema de triagem de tickets de suporte com IA. Diagnostica gargalos operacionais, classifica tickets interativamente via LLM e gera proposta de redesign do fluxo de suporte.

---

## O que faz

Dois modos de uso:
1. **Diagnóstico analítico** — identifica gargalos por canal/tipo/prioridade com base nos 8.469 tickets do dataset
2. **Classificador interativo** — o analista cola o texto de um ticket novo e recebe categoria, prioridade e roteamento sugeridos pelo LLM

---

## Rotas do app

| Rota | Descrição |
|------|-----------|
| `/diagnostic` | Métricas operacionais: volume, backlog, tempo médio de resolução, CSAT, heatmap canal×tipo, estimativa de desperdício anual |
| `/triage` | Classificador interativo de tickets — input de texto livre, resposta LLM com categoria + prioridade + ação sugerida |
| `/proposal` | Proposta de redesign do processo de suporte gerada via LLM com base nos dados do diagnóstico |

---

## Como rodar

**Pré-requisito — scripts Python (pré-processamento):**

```bash
cd apps/support-triage
pip install -r scripts/requirements.txt

# Gerar os JSONs de diagnóstico
python scripts/01_diagnostic.py        # → data/diagnostic_output.json
python scripts/02_classification.py    # → data/classification_output.json
```

**App Next.js:**

```bash
# Da raiz do monorepo
pnpm dev:support-triage    # http://localhost:3003

# Ou isolado (dentro de apps/support-triage)
pnpm dev
```

**Docker (inclui os scripts Python via multi-stage build):**

```bash
docker compose up support-triage --build
```

**Variáveis de ambiente:**

```bash
OPENROUTER_API_KEY=sk-or-v1-...   # Obrigatório para /triage e /proposal funcionarem
```

Sem a API key, o classificador exibe banner "Configure API key" e a proposta não é gerada.

---

## Findings principais

- 40%+ dos tickets são problemas de billing — candidatos diretos a self-service
- Tempo médio de resolução varia 5× entre agentes para o mesmo tipo de problema
- Tickets sem resposta em 24h têm probabilidade de escalonamento 3× maior

---

## Arquitetura

Pipeline em duas etapas: scripts Python geram JSONs de diagnóstico em build time (incluídos na imagem Docker). O app Next.js consome os JSONs — sem reprocessamento em runtime. O classificador de tickets chama OpenRouter diretamente do server component com cache 24h.
