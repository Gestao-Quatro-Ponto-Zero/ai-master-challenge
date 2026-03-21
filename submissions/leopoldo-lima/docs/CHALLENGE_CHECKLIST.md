# Checklist — critérios do desafio

Preencha este arquivo ao executar **`CRP-S04`**. Copie os critérios **literais** do *submission guide* / rubrica oficial do desafio (para não haver deriva de significado).

## Instruções

1. Colar ou transcrever cada critério numa linha da tabela.
2. Na coluna **Evidência**, usar paths relativos, nomes de testes ou comandos reproduzíveis.
3. Estado: `ok` | `parcial` | `N/A` (com justificação curta).

## Tabela

| # | Critério (literal do guia) | Evidência no repo | Estado | Notas |
|---|----------------------------|-------------------|--------|-------|
| 1 | Solução funcional e executável | `src/api/app.py`, `public/`, `docs/SETUP.md`, `docs/RUNBOOK.md`, `python .\scripts\tasks.py dev` | ok | API + UI shell com fluxo de ranking/detalhe e trilha de execução documentada |
| 2 | Process log obrigatório e auditável | `PROCESS_LOG.md`, `docs/PROCESS_LOG_GUIDE.md`, `artifacts/process-log/`, `docs/SUBMISSION_STRATEGY.md` | ok | Entradas por CRP com evidências, erros/correções e convenção de paths relativos |
| 3 | Rastreabilidade de uso de IA e julgamento humano | `PROCESS_LOG.md`, `docs/IA_TRACE.md` | ok | Uso de IA registrado com revisão/correção humana explícita nos CRPs executados |
| 4 | Evidência de qualidade automatizada | `tests/`, `docs/TEST_STRATEGY.md`, `docs/QUALITY_GATES.md`, `.github/workflows/ci-pr.yml`, `.github/workflows/frontend-ci.yml`, `python .\scripts\tasks.py build` | parcial | Gates locais validados; execução remota de Actions depende do repositório Git remoto |
| 5 | Narrativa de submissão (summary, abordagem, resultado, recomendações, limitações) | `README.md`, `docs/README_SUBMISSION_SKELETON.md`, `docs/DEMO_SCRIPT.md` | ok | README alinhado ao esqueleto de submissão e ancorado em evidências do repo |
| 6 | Limitações e trade-offs explícitos | `README.md`, `docs/RUNBOOK.md`, `PROCESS_LOG.md` | ok | Limitações reais sem ocultar riscos (Docker daemon, métricas em memória, escopo UI) |

## Revisão

- Data da última validação (matriz item a item): **2026-03-20 (CRP-REAL-10)** — ver **`docs/FINAL_AUDIT_CHALLENGE_003.md`** (status `ATENDE` / `ATENDE PARCIALMENTE` / `NÃO ATENDE` + parecer **SUBMETER**). Cruzamento com o *submission guide* formalizado em **`docs/SUBMISSION_GUIDE_AUDIT.md` (CRP-SUB-01, 2026-03-21)**.
- Validação anterior: 2026-03-20 (CRP-S04).
- Responsável: Equipa Lead Scorer (execução via CRPs).
- Critério de honestidade aplicado: quando a prova depende de ambiente externo (ex.: Actions remota), o estado foi marcado como `parcial`; a auditoria REAL-10 confirma gaps não bloqueantes (filtro dedicado por vendedor, CI remoto, PNG opcionais).
