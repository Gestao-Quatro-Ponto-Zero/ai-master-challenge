# BASELINE

## Contexto do snapshot
- data: 2026-03-20
- escopo: execução do `CRP-000`
- objetivo: inventariar o estado real do repositório antes de novos passos técnicos

## Estado observado do repositório
Este workspace está, no momento, em perfil **documental/governança** com foco em CRPs e submissão.

Itens presentes na raiz:
- `crps/executed/` com CRPs agrupados (foundation, data, ui, product-tuning, submission) + `indexes/crp-index.csv`
- `legacy/focus-score-ui-api-crps/` (e outros `legacy/focus-score-*`) com CRPs importados por referência — fora do caminho de execução do produto
- `docs/` com artefatos de estratégia de submissão e guia de process log
- `artifacts/process-log/` com estrutura de evidências
- `data/` com CSVs do challenge
- `README.md`, `LOG.md`, `PROCESS_LOG.md`, `00-START-HERE.md`, `01-ROADMAP.md`

## Lacunas importantes no snapshot
- `docs/REPO_MAP.md` e este `docs/BASELINE.md` estavam ausentes no estado encontrado
- há descompasso entre o que o `README.md` lista como base documental e o que de fato estava materializado em `docs/`
- a camada de scripts/código de produto referenciada em partes da documentação não está visível neste snapshot atual

## Riscos de entrega
- risco de submissão inconsistente por documentação apontando artefatos não presentes
- risco de execução cega dos CRPs técnicos sem validar pré-condições de estrutura
- risco de parecer “output genérico” se o process log não registrar o estado real encontrado

## Decisão tomada no CRP-000
- congelar este baseline com foco no que está **verificável no disco**
- criar `docs/REPO_MAP.md` coerente com o snapshot atual
- registrar no `LOG.md` e `PROCESS_LOG.md` que este baseline foi refeito

## Próximos passos recomendados
1. Executar `CRP-001` para fortalecer o trilho documental sobre esta base real.
2. Antes de qualquer CRP técnico, confirmar a presença dos artefatos de código exigidos pelo respectivo CRP.
3. Manter `README.md` sincronizado com o que realmente existe no repositório.
