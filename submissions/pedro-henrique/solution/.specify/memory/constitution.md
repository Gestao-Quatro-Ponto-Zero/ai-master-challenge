# G4 Suporte Inteligente Constitution

## Core Principles

### I. Compliance de Submissão Primeiro
Toda entrega deve permanecer estritamente dentro de `submissions/pedro-henrique-silva/`. Qualquer alteração fora desse escopo é considerada violação crítica e bloqueia avanço.

### II. Valor de Produto acima de Complexidade Técnica
Cada incremento deve demonstrar valor verificável para as personas (cliente e admin). Escolhas técnicas devem favorecer simplicidade operacional e entrega rápida do MVP.

### III. Automação com Guardrails Humanos
A IA deve acelerar resolução e triagem, mas decisões de alto risco permanecem auditáveis e passíveis de intervenção humana. Baixa confiança exige fallback explícito.

### IV. Dados, Segurança e Acesso por Papel
Dados de tickets e perfis devem respeitar segregação por papel (`admin`/`customer`) e políticas de acesso. Informações sensíveis não devem ser expostas em logs, respostas ou frontend.

### V. Evidência e Reprodutibilidade
Toda métrica apresentada deve ser rastreável para fonte de dados ou script de geração. Fluxos de setup, execução e validação precisam estar documentados para reprodução em ambiente limpo.

## Non-Negotiable Constraints

- Branch de submissão: `submission/pedro-henrique-silva`.
- Estrutura obrigatória de entrega deve existir (`README.md`, `solution/`, `process-log/`, `docs/`).
- MVP deve incluir jornada de cliente com tentativa de deflexão e jornada admin com diagnóstico acionável.
- Dashboard deve consumir artefato analítico gerado offline (sem recálculo em runtime).

## Delivery Workflow

- Primeiro especificar o comportamento e critérios de sucesso.
- Depois planejar arquitetura, contratos e modelo de dados.
- Só então quebrar em tarefas executáveis e iniciar implementação.
- Cada fase deve deixar artefatos versionados e verificáveis.

## Governance

Esta constituição prevalece sobre decisões ad hoc durante o desenvolvimento. Exceções só são aceitas com justificativa explícita no plano e impacto documentado.

**Version**: 1.0.0 | **Ratified**: 2026-05-28 | **Last Amended**: 2026-05-28
