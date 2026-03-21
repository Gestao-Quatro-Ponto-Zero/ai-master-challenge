# Governança de CRPs

## Submissão em duas partes obrigatórias

A submissão válida exige **duas partes inseparáveis**:

1. **Solução funcional** — código, configuração, documentação de produto e o que o desafio pedir como entregável técnico.
2. **Process log** — registo auditável do processo em `PROCESS_LOG.md` (e evidências ligadas), conforme [PROCESS_LOG_GUIDE.md](./PROCESS_LOG_GUIDE.md).

**Sem process log completo e alinhado ao guia, há risco elevado de desclassificação** ou penalização na avaliação, por falta de rastreabilidade do método e do uso de IA.

A **via oficial de submissão é Pull Request (PR)** no repositório: alterações integradas por PR, com narrativa e evidências referenciáveis na revisão.

## Obrigações por CRP

- **Todo CRP atualiza o process log** — pelo menos ao abrir (objetivo) e ao fechar (resultado, PR, iterações); durante o trabalho, entradas por iterações relevantes.
- **Todo CRP gera evidência** — artefatos, logs de teste, exports ou outros arquivos verificáveis em `artifacts/process-log/` (ou caminhos acordados no CRP), citados no `PROCESS_LOG.md`.
- **Toda contribuição com recurso a IA exige julgamento humano registado** — no process log: o que foi aceite, alterado ou rejeitado após revisão humana (não basta colar output da ferramenta).
- **Output genérico da IA, sem verificação e sem registo de correção, é anti-padrão** e não substitui critérios de aceite nem evidência.

## Famílias de identificadores (convivência)

| Prefixo | Função |
|---------|--------|
| `CRP-000` … `CRP-012` | Trilha principal do método / produto (números fixos do pacote). |
| `CRP-D01` … | Trilha de dados (raw, qualidade, integridade, modelos, etc.). |
| `CRP-S01` … | **Submissão e governança** — process log, evidências, checklist do desafio, PR final, auditoria de narrativa. |

Não é obrigatório renumerar CRPs existentes. Novos trabalhos de submissão usam **`CRP-Sxx`** para não colidir com futuros `CRP-013+` de produto.

## Regras operacionais

1. **Um CRP → um PR** (salvo exceção documentada no `PROCESS_LOG.md`).
2. Cada PR deve **mencionar o CRP** no título ou na descrição.
3. **Critérios de aceite** e **DoD** do CRP devem ser verificáveis (comandos, arquivos, checklist).
4. Encerramento: **atualizar obrigatoriamente** `PROCESS_LOG.md` com evidências ligadas e, quando aplicável, `LOG.md`.

## Onde está o quê

| Necessidade | Onde |
|-------------|------|
| Definição do trabalho (curado) | `crps/executed/{foundation,data,ui,product-tuning,submission}/CRP-*.md` |
| Índice de CRPs | `indexes/crp-index.csv` |
| Lista plana antiga (arquivo) | `archive/superseded/crps-root-flat-pre-SUB-08/` |
| Processo e IA | `PROCESS_LOG.md` + `artifacts/process-log/` + `docs/IA_TRACE.md` |
| Estratégia de entrega | `docs/SUBMISSION_STRATEGY.md` |
| Texto-base do README final | `docs/README_SUBMISSION_SKELETON.md` |

## CRPs de submissão (`CRP-Sxx`)

Pequenos, auditáveis, podem ser executados em paralelo ou em sequência curta antes da entrega. Ver `crps/executed/submission/` (e arquivo `archive/superseded/crps-root-flat-pre-SUB-08/CRP-S*.md` para a cópia superseded da lista plana).

## Revisão

- Revisão técnica: conforme o repositório (CI, testes).
- Revisão de submissão: narrativa forte (**resumo executivo, abordagem, resultado, recomendações, limitações**), limitações honestas e evidências — ver `CRP-S05` e `CRP-S06`.
