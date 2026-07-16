# Arquitetura de agentes — Challenge 004

Sistema multiagente para desenvolver a análise e estratégia social media com gates, contexto mínimo e rastreabilidade de evidências.

## Como usar

1. Abra o Claude Code nesta pasta: `cd submissions/felipe-freire`.
2. Confirme a configuração com `/memory` e `/agents`.
3. Inicie o coordenador como agente principal: `claude --agent orchestrator`.
4. Solicite a execução do Challenge 004 e forneça/aprove a fonte de dados quando necessário.
5. Acompanhe o estado em `outputs/manifests/run-manifest.yaml`.

O Orchestrator deve permanecer como agente principal porque subagentes do Claude Code não podem criar outros subagentes. Reinicie a sessão ou use `/agents` após alterar manualmente arquivos em `.claude/agents/`.

## Documentação

- [Arquitetura, fluxo, automação e armadilhas](docs/agent-architecture.md)
- [Protocolo de handoff e contexto](docs/handoff-protocol.md)
- [Estrutura de diretórios](docs/project-structure.md)
- [Regras globais](CLAUDE.md)
- [Contratos](docs/contracts/README.md)

Os prompts prontos para uso estão em `.claude/agents/`, incluindo o Software Engineer em dois modos e o GitHub Publisher isolado. Não há uma cópia em `prompts/`: manter uma única fonte evita divergência entre documentação e configuração executável.

## Primeiro gate

Antes de qualquer análise, o Planner cria `docs/execution-plan.md`; depois, o Data Engineer compreende o dataset e materializa os contratos listados em `docs/contracts/README.md`. O Software Engineer então executa a fundação técnica. Antes do Writer, o mesmo agente retorna em modo consolidação para integrar e validar o pipeline completo. Arquivos descritos como outputs futuros não são placeholders de resultado e só devem surgir durante uma execução real.
