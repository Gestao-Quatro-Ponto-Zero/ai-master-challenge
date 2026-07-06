# G4 — Super Prompt de Consolidação de Documentação

Use este prompt para organizar toda a documentação do projeto, consolidar
anotações de manutenção, montar passo a passo operacional e gerar o documento
final em Markdown com tudo que foi feito.

---

## Prompt único (copiar e colar)

```text
[AGENT: DOC-UPDATER] [SKILL: SPEC-DRIVEN] [SKILL: MEMORY-OPT]

Objetivo:
Organizar toda a documentação do projeto Lead Scorer e gerar um documento
final único em Markdown com o histórico completo do que foi feito.

Contexto do repositório (usar como fontes oficiais):
- submissions/gabriel/process-log/PROCESS_LOG.md
- submissions/gabriel/docs/PLAN.md
- submissions/gabriel/docs/PROMPTS.md
- submissions/gabriel/solution/ (código final implementado)
- harness/*.md (harness e super prompts usados)

Tarefa:
1) Ler as fontes acima
2) Consolidar decisões, implementações, erros e correções
3) Documentar arquitetura e fluxo operacional
4) Criar documentação de manutenção (runbook)
5) Criar passo a passo de execução local
6) Registrar pendências e roadmap v2
7) Gerar 1 documento final mestre em markdown

Arquivo de saída obrigatório:
- submissions/gabriel/docs/PROJECT_MASTER_REPORT.md

Estrutura obrigatória do documento final (nesta ordem):
1. Resumo executivo (5-10 linhas)
2. Objetivo de negócio e contexto do challenge
3. Escopo implementado (o que foi entregue)
4. Arquitetura da solução (dados, scoring, app, módulos)
5. Linha do tempo de execução (extraída do PROCESS_LOG)
6. Decisões técnicas e trade-offs
7. Erros encontrados e como foram corrigidos
8. Design system e decisões de UX
9. Funcionalidades implementadas (com status)
10. Passo a passo para rodar localmente (setup -> run -> testes)
11. Guia de manutenção (runbook):
    - onde alterar regras de score
    - onde alterar UI
    - onde alterar textos/copies
    - como adicionar novos filtros
    - como depurar problemas comuns
12. Qualidade e validação:
    - testes executados
    - smoke checks
    - limitações conhecidas
13. Estrutura de pastas relevante
14. Pendências abertas e riscos
15. Roadmap v2 (priorizado)
16. Changelog consolidado por etapa
17. Checklist final de handoff

Regras obrigatórias:
- Não inventar fatos que não estejam nos arquivos fonte
- Se faltar informação, marcar explicitamente como "não registrado"
- PT-BR claro, objetivo e orientado a manutenção
- Linguagem para time misto (negócio + técnico)
- Sempre citar caminhos de arquivo quando mencionar implementações
- Transformar notas soltas em instruções operacionais acionáveis

Saídas adicionais obrigatórias:
- Atualizar submissions/gabriel/process-log/PROCESS_LOG.md com entrada final:
  [FINAL] Documentação consolidada e handoff pronto
- Criar/atualizar submissions/gabriel/docs/MAINTENANCE_NOTES.md
  com versão resumida do runbook (quick reference)

Formato de qualidade esperado:
- Documento final pronto para handoff sem contexto extra
- Índice no topo
- Seções com bullets escaneáveis
- Sem texto genérico/filler

Antes de finalizar:
- Revisar consistência entre PROCESS_LOG, PLAN e documento final
- Validar que o passo a passo local funciona de ponta a ponta
- Incluir lista de "o que um novo dev precisa ler primeiro" (onboarding de 10 minutos)
```

---

## Quando usar

- Final de sprint/challenge
- Antes de handoff para outro dev
- Antes de gravação de demo ou entrega formal
- Quando houver muita informação espalhada em docs e logs

## Resultado esperado

- Um único documento mestre com histórico + manutenção + operação
- Menos dependência de memória individual
- Onboarding muito mais rápido para qualquer pessoa que entrar no projeto
