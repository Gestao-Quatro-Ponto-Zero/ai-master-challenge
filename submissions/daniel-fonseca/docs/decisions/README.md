# Registro de decisões (ADRs)

Cada decisão relevante vira um arquivo curto `NNNN-titulo.md`. Status: `Proposta` (aguardando Daniel) → `Aceita` / `Rejeitada` / `Substituída por NNNN`.
O campo **Origem** deixa explícito quem trouxe a ideia — isso é parte da evidência de "como usei IA".

| # | Decisão | Status | Origem |
|---|---|---|---|
| [0001](0001-estrutura-e-memoria.md) | Estrutura do repositório e memória agnóstica de harness | Aceita | Daniel (requisito) + IA (desenho) |
| [0002](0002-stack-e-isolamento.md) | Stack Supabase + Vercel + n8n e isolamento de contas/MCP | Aceita | Daniel |
| [0003](0003-diagnostico-dataset-sintetico.md) | Como enquadrar o diagnóstico sabendo que o DS1 é sintético | Aceita | IA (achado) + Daniel (resposta por pergunta) |
| [0004](0004-rag-adaptado.md) | RAG: similaridade no DS2 + base de soluções validadas via HITL | Aceita | Daniel (ideia) + IA (adaptação) |
| [0005](0005-tres-niveis-de-automacao.md) | Política de 3 níveis: automático / revisão humana / só humano | Aceita | Daniel (ideia) + IA (critérios) |
| [0006](0006-keep-alive-supabase.md) | Keep-alive do Supabase: Vercel Cron diário + n8n | Aceita | Daniel (requisito) + IA (mecanismo) |
| [0007](0007-notificacoes-slack-e-inbox.md) | Notificações do nível 3: Slack via n8n + caixa no painel | Aceita | Daniel |
| [0008](0008-console-como-validador.md) | Console operacional como validador da solução | Aceita | IA (sugestão) + Daniel (enquadramento) |
| [0009](0009-cruzamento-ds1-ds2.md) | Cruzamento DS1 × DS2 por papel (ROI, política, taxonomia), sem join | Aceita | Daniel (pergunta) + IA (desenho) |
| [0010](0010-classificador-de-producao.md) | Classificador: RAG por similaridade como classificador único (512, k=50); LLM redige; níveis calibrados | Aceita | Daniel (escolha do RAG) + IA (medição e calibração) |
| [0011](0011-diretrizes-n8n.md) | n8n: fluxos simples com nós nativos, rascunho validado antes de construir, documentação na entrega | Aceita | Daniel |
| [0012](0012-decisoes-de-construcao-n8n.md) | n8n: nível 1 com LLM adaptando solução validada (só se existir), lista de bloqueio estreita (0,2% FP), gpt-5.4-mini, texto livre em inglês, heartbeat 06:00 | Aceita | Daniel (decisões) + IA (medição) |
| [0013](0013-nos-nativos-supabase.md) | n8n: nós nativos do Supabase (tabelas) + HTTP Request com credencial Supabase (funções do RAG via REST); wrapper `match_resolutions_json` | Aceita | Daniel (sugestão) + IA (teste e ajustes) |
| [0014](0014-arquitetura-do-app.md) | App: 3 áreas com toggles (Painel · Console · Como foi feito), dados do Supabase, frentes paralelas | Proposta | Daniel + IA |

## Modelo

```markdown
# NNNN — Título
- **Status:** Proposta | Aceita | Rejeitada
- **Data:** AAAA-MM-DD
- **Origem:** quem trouxe

## Contexto
## Decisão
## Alternativas consideradas
## Consequências
```
