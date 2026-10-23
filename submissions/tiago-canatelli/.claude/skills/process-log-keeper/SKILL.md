---
name: process-log-keeper
description: Mantém o process log obrigatório da submissão do Challenge 001 (sem ele, desclassificação). Use ao terminar uma fase, hipótese ou bloco de trabalho; quando a IA errar e o erro for corrigido; quando uma decisão, mudança de escopo ou corte for tomado; ao fim de cada sessão de IA (exportar conversa); e ao montar o README final de submissão a partir do template.
---

# Process log — evidência de como a IA foi usada

O G4 já tem respostas de IA "pura" para este desafio (o baseline). O process log é onde a submissão prova que **supera o baseline**: mostra decomposição do problema, iteração, verificação e julgamento humano. "1 prompt → 1 resposta → submissão" é o padrão que reprova.

Regras:
1. **Registrar na hora**, não reconstruir no final — detalhes somem.
2. **Nunca inventar ou embelezar.** Só entra o que aconteceu, com o artefato que prova (commit, arquivo, print, export). A IA pode rascunhar entradas; o Tiago revisa antes do PR.
3. **Separar quem fez o quê:** o que o Tiago pediu/decidiu × o que a IA executou/sugeriu × o que foi corrigido.
4. Curto e escaneável: o avaliador lê dezenas de submissões.

## Arquivos

| Arquivo | Quando atualizar | Formato de entrada |
|---|---|---|
| `process-log/journal.md` | fim de cada bloco de trabalho | ver §1 |
| `process-log/decisions.md` | decisão, trade-off, mudança de escopo ou corte | `### <decisão>` → pedido/contexto · opções · escolha (e quem decidiu) · motivo · consequência |
| `process-log/ai-errors.md` | sempre que a IA errar | `### <título>` → o que a IA fez · como percebi · correção · lição |
| `process-log/hypotheses.md` | cada hipótese (formato na skill `churn-data-scientist`) | — |
| `process-log/prompts.md` | prompts-chave do Tiago que mudaram a direção do trabalho | ver §2 |
| `process-log/timeline.md` | fim de cada fase | tabela fase × timebox × tempo real × o que foi cortado |
| `process-log/ai-evals.md` | quando comparar modelos, avaliar o RAG ou validar números | pergunta · esperado · obtido por modelo/configuração · veredito |
| `process-log/screenshots/` | cada tela, painel, resposta da IA, MCP funcionando, Supabase/Render | `<fase>-<nn>-<descricao>.png` |
| `process-log/chat-exports/` | fim de cada sessão de IA | `<data>-<ferramenta>-<tema>.md` |

### 1. Entrada do journal

```markdown
## <AAAA-MM-DD HH:MM> · <fase> · <tema>
- **Pedi à IA:** <o pedido, em uma frase; link para prompts.md se for chave>
- **A IA fez:** <ações concretas, com números>
- **Verifiquei / ajustei:** <o que conferi, o que mudei e por quê>
- **Resultado:** <arquivos, commits (hash), prints>
- **Próximo:** <próximo passo>
```

### 2. Entrada de prompt-chave

```markdown
### <n>. <tema>
- **Prompt (literal ou resumo fiel):** "<...>"
- **Por que esse prompt:** <qual decomposição ou julgamento estava por trás>
- **O que mudou no projeto:** <consequência, com commit>
```

## Tipos de erro da IA que valem registro

Número inventado ou não conferido · coluna/tabela/schema assumido sem olhar a fonte · conclusão causal sem teste · leakage no modelo · KPI com fórmula diferente do dicionário · código que roda mas faz a coisa errada · recomendação genérica · solução desenhada sem olhar o dado · documentação desatualizada em relação ao plano · excesso de escopo.

## Ao fechar uma fase ou sessão

1. Entrada no `journal.md` (formato §1).
2. Algum erro da IA, decisão ou prompt-chave ainda não registrado? Registrar.
3. Atualizar `timeline.md` (timebox × real).
4. Screenshot do que foi construído.
5. Exportar a conversa da sessão para `chat-exports/` (no app Claude: exportar transcript; em outras IAs: export ou print).
6. Commit pequeno, mensagem explicando o porquê.

## Montar o README final

Usar `../../templates/submission-template.md` (raiz do repositório) **sem mudar a estrutura nem os títulos**. Mapeamento:

| Seção | Fonte |
|---|---|
| Sobre mim | Nome, LinkedIn, "Challenge 001 — Diagnóstico de Churn" |
| Executive Summary | 3–5 frases do relatório do CEO |
| Abordagem | `docs/01-plano-projeto.md` + `decisions.md` (as 5 decisões que mais mudaram o rumo) |
| Resultados / Findings | hipóteses confirmadas com números + links para painel, relatório, MCP |
| Recomendações | lista priorizada (formato da skill `churn-business-analyst`) |
| Limitações | dataset sintético (crédito ao autor River @ Rivalytics), conflitos de dados, hipóteses inconclusivas, causas não validadas por experimento, cortes de `timeline.md` |
| Ferramentas usadas | tabela ferramenta → uso real (Claude Code, Supabase MCP, Kaggle MCP, Render, LLMs avaliados…) |
| Workflow | resumo numerado do `journal.md` + `timeline.md` |
| Onde a IA errou | os 3–5 melhores casos de `ai-errors.md` |
| O que eu adicionei | julgamento do Tiago: decisões de `decisions.md` em que ele escolheu, `prompts.md`, verificações que pegaram erros, priorização por MRR, cortes |
| Evidências | marcar o que existe e linkar: git history, `chat-exports/`, `screenshots/`, `ai-evals.md` |

Checklist final (do `CONTRIBUTING.md`): pasta `submissions/tiago-canatelli/` · README no template · process log presente · instruções de setup · nenhum arquivo fora da pasta alterado · PR `[Submission] Tiago Canatelli — Challenge 001`.
