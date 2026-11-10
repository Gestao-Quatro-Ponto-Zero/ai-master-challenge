# AGENTS.md — Submissão Daniel Fonseca · Challenge 002 (Redesign de Suporte)

> Fonte única de verdade para **qualquer agente de IA** que trabalhe neste projeto (Claude Code, Codex, Cursor…).
> `CLAUDE.md` apenas importa este arquivo. Se você é um agente começando agora, leia este arquivo inteiro antes de agir.

## 1. Contexto em 30 segundos

- Processo seletivo **AI Master — G4 Educação**. Repositório: fork `danielcoelhof/ai-master-challenge`, branch `submission/daniel-fonseca`.
- Desafio: [`challenges/process-002-support`](../../challenges/process-002-support/README.md) — diagnóstico operacional + proposta de automação com IA + protótipo funcional + process log.
- **Humano responsável:** Daniel Fonseca. Ele direciona; a IA executa, sugere e questiona. Decisões de produto/negócio são dele.
- Stack decidida pelo Daniel: **Supabase** (Postgres + pgvector) · **Vercel** (dashboard/console) · **n8n** (orquestração, RAG, HITL, notificações) · **OpenAI API** (embeddings/LLM) · **Slack** (via n8n) + caixa de mensagens no painel para alertas; WhatsApp documentado como alternativa.
- **Timebox (Daniel):** no máximo **dois turnos noturnos — 09/11 e 10/11/2026** — incluindo vídeo e PR. Plano por turno em `context/STATE.md`. Priorize o que pontua nos critérios do challenge.

## 2. Protocolo de sessão (obrigatório — é o que garante memória entre sessões e entre harnesses)

**Ao iniciar:**
1. Ler [`context/STATE.md`](context/STATE.md) — onde paramos, próximo passo, bloqueios.
2. Ler [`context/data-findings.md`](context/data-findings.md) — fatos já verificados sobre os dados. Não re-derive; se discordar, verifique e corrija o arquivo.
3. Ler a última entrada de [`process-log/process-log.md`](process-log/process-log.md) e as ADRs em [`docs/decisions/`](docs/decisions/).

**Durante:**
- Toda decisão relevante (arquitetura, escopo, enquadramento do diagnóstico) vira uma ADR curta em `docs/decisions/` — status `Proposta` até o Daniel aprovar; depois `Aceita`.
- Quando a IA errar e for corrigida, ou quando o Daniel trouxer um julgamento que a IA não teria, registrar em [`process-log/judgment-log.md`](process-log/judgment-log.md). Isso alimenta as seções obrigatórias "Onde a IA errou" e "O que eu adicionei" do README final.
- Afirmações sobre os dados precisam de um script reproduzível em `solution/analysis/` — nada de número "de cabeça".

**Ao encerrar (ou quando o limite de uso estiver perto):**
1. Atualizar `context/STATE.md` (feito / em andamento / próximo passo / bloqueios).
2. Adicionar uma entrada em `process-log/process-log.md` (formato no próprio arquivo), indicando o harness/modelo usado.
3. Commitar com mensagem descritiva. O histórico git é evidência de processo.

## 3. Regras firmes

- **Só modificar arquivos dentro de `submissions/daniel-fonseca/`.** PRs que alteram outros arquivos são rejeitados pelo G4.
- O `.gitignore` da raiz (upstream) ignora `submissions/`. Para adicionar arquivos use **`bash scripts/git-add.sh`** (respeita o `.gitignore` desta pasta). Nunca `git add -f` na pasta inteira — isso força `.venv/`, `data/` e `.env`. Não editar o `.gitignore` da raiz.
- **Nunca commitar segredos.** Chaves vão em `.env` (ignorado) ou nas credenciais do n8n/Vercel/Supabase. `.env.example` lista apenas os nomes.
- **Isolamento de contas (diretriz do Daniel):** neste projeto use **somente** os servidores MCP `supabase-g4` e `vercel-g4` (definidos em [`.mcp.json`](.mcp.json)) e `n8n-g4` (escopo local, com token — ver `docs/setup.md`). Os servidores globais `supabase`, `vercel` e `n8n-local` pertencem a outros contextos do Daniel — **não usar** aqui.
- **Não expor a URL/IP da VPS do n8n** em arquivos versionados — usar `N8N_BASE_URL` do `.env`.
- Dados brutos ficam em `data/raw/` (ignorado). Baixar com `scripts/download_data.sh`.
- **n8n (ADR-0011):** nós nativos sempre que possível; apresentar o rascunho nó a nó ao Daniel **antes** de construir; exportar o JSON para `solution/n8n/` e documentar em `docs/n8n-flows.md`.
- Idioma das entregas: **português (pt-BR)**. Código e identificadores em inglês.
- **Abuso no app público (Daniel):** a rotina de monitoramento observa e alerta. Nenhuma ação contra abuso (pausar texto livre, bloquear IP, despublicar workflow, mudar limites, apagar dados) sem instrução clara do Daniel. Ver `docs/prd/01-prd.md` §8.1.
- **Estilo de texto (Daniel):** frases afirmativas e diretas, com o dado. Sem antagonismos do tipo "é X, não Y" e sem analogias. Vale para a interface do app, os docs e o README.
- Commits feitos por agentes terminam com o trailer de co-autoria do agente (ex.: `Co-Authored-By: Claude ... <noreply@anthropic.com>`), para deixar visível o desenvolvimento assistido por IA.
- Time budget sugerido pelo G4: 4–6h. Registrar tempo gasto por sessão no process log; priorizar o que pontua nos critérios do challenge.

## 4. Mapa do diretório

```
submissions/daniel-fonseca/
├── README.md              ← entrega final (template do G4) — preenchido no fim
├── AGENTS.md / CLAUDE.md  ← instruções para agentes (este arquivo)
├── .mcp.json              ← MCPs do projeto (Supabase/Vercel da conta dedicada), sem segredos
├── context/               ← memória persistente: STATE.md (handoff) + data-findings.md
├── docs/                  ← arquitetura, setup, design system, decisions/ (ADRs)
├── process-log/           ← evidências: narrativa, judgment-log, screenshots, chat-exports, vídeo
├── solution/              ← análise, dashboard, workflows n8n, supabase (migrations/functions)
└── scripts/               ← utilitários (download de dados, export de transcripts)
```

## 5. Comandos úteis

```bash
# dados (não precisa de credencial Kaggle)
bash scripts/download_data.sh
# perfil dos datasets (gera os números de context/data-findings.md)
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python solution/analysis/00_data_profile.py
```
