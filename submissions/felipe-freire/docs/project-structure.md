# Estrutura do projeto

```text
submissions/felipe-freire/
├── .claude/agents/        # definições executáveis dos agentes Claude Code
├── CLAUDE.md              # regras globais carregadas em toda sessão
├── data/
│   ├── raw/               # entrada imutável, normalmente fora do Git
│   └── processed/         # datasets limpos/analíticos versionados
├── dashboard/             # app, componentes, configuração e testes visuais
├── docs/                  # arquitetura, contratos, decisões e dicionário
│   └── contracts/         # schemas e contratos de handoff/dados/métricas
├── notebooks/             # exploração; não é fonte única de lógica crítica
├── outputs/
│   ├── figures/           # gráficos reproduzíveis por evidence ID
│   ├── manifests/         # estado, hashes, lineage e gates por execução
│   └── tables/            # tabelas intermediárias/finais rastreáveis
├── process-log/           # evidências de uso de IA e julgamento humano
├── reports/               # relatório executivo, técnico e verdict final
├── solution/              # pacote final curado para submissão
├── .github/workflows/     # CI criado na consolidação técnica
├── pyproject.toml         # dependências, ferramentas e comandos da fundação
├── src/
│   ├── analysis/          # métricas, EDA e inferência
│   ├── etl/               # ingestão, validação e transformação
│   └── ml/                # features, treino, avaliação e serving
└── tests/                 # unitários, integração, dados, estatística e dashboard
```

`prompts/` não é criado em paralelo: os prompts prontos para uso vivem no local nativo `.claude/agents/`, evitando duas fontes de verdade. Contratos ficam separados dos prompts porque são consumidos por código e humanos. O Software Engineer é owner da infraestrutura técnica, testes integrados e CI, não da lógica analítica. Artefatos finais nunca devem depender de arquivos temporários ou de uma conversa.
