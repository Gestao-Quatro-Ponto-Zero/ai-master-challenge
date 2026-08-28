# Submissão — Jose Nascimento — Challenge 001

## Sobre mim

- **Nome:** Jose Nascimento
- **LinkedIn:** (a preencher)
- **Challenge escolhido:** 001 — Diagnóstico de Churn

---

## Executive Summary

_Em 3-5 frases: o que você fez, o que encontrou, e qual a principal recomendação._

---

## Solução

_Sua análise, protótipo, redesign ou o que o challenge pedir._

### Abordagem

### Resultados / Findings

### Recomendações

### Limitações

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| OpenCode (harness compartilhado) | Harness único para orquestrador e subagentes: gestão de sessões e agentes, permissões, contexto isolado por subagente, git e geração de evidências |
| GPT 5.6 Sol (`openai/gpt-5.6-sol`, orquestrador — perfil de máxima capacidade da sessão, "GPT 5.6 Sol Max") | Manter o contexto global/estado do projeto; decompor etapas; escrever prompts e contratos; arbitrar divergências dos revisores; decidir rework; controlar gates e risco. Não executa scripts nem edita a solução — delega a subagentes |
| DeepSeek V4 Flash (`deepseek-max`, executor — via OpenCode Go, max reasoning) | Executar cada etapa da análise: exatamente um executor por iteração, com contexto novo/limpo e escopo fechado; implementa, testa, documenta e faz commit/push |
| DeepSeek V4 Flash (`deepseek-max`, 3 revisores independentes — via OpenCode Go) | Revisar cada etapa em paralelo e em modo read-only (mesmo prompt, contextos separados), produzindo reports externos únicos com veredicto e findings |
| DeepSeek V4 Flash (`deepseek-max`, corretor sequencial — via OpenCode Go) | Ler os 3 reports de revisão, resolver findings materiais, testar, registrar o review summary e fazer commit/push |

> A descrição inicial desta tabela era curta e incompleta. A arquitetura completa (papéis, modelos, contexto, permissões, rationale, limitações e fontes) está em [`process-log/management/orchestration-architecture.md`](process-log/management/orchestration-architecture.md), adendo que é a fonte atual de verdade de ferramenta/processo.

### Workflow

1.

### Onde a IA errou e como corrigi

### O que eu adicionei que a IA sozinha não faria

---

## Evidências

- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [ ] Chat exports
- [ ] Git history (se construiu código)
- [ ] Outro: _____________

---

_Submissão enviada em: [data — a preencher somente quando o PR for efetivamente aberto, na Iteração 10]_