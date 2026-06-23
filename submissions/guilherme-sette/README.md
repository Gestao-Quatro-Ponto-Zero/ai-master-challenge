# Submissao - Guilherme Sette - Challenge 003

## Sobre mim

- **Nome:** Guilherme Sette
- **LinkedIn:** Nao informado
- **Challenge escolhido:** 003 - Lead Scorer

---

## Executive Summary

Construí uma solução funcional de lead scoring para priorizar e rotear oportunidades abertas de vendas, combinando score comercial, qualidade de dados, risco operacional e fit histórico entre vendedor, produto, setor e ticket. A entrega inclui ETL padronizada, análise crítica dos vendedores, benchmark contra baselines simples, recomendações de remanejamento com governança e um front estático dividido em portal do vendedor e portal do gerente. A principal recomendação é usar o score como sistema de triagem e decisão assistida, não como automação cega de redistribuição.

---

## Solução

A solução completa está em [`solution/lead-scorer`](./solution/lead-scorer/).

### Abordagem

1. Li o README do challenge 003 e tratei esse documento como fronteira de escopo.
2. Baixei e preservei os CSVs brutos em `data/raw`.
3. Criei ETL reproduzível em Python para normalizar dados, enriquecer oportunidades e separar pipeline fechado de pipeline aberto.
4. Modelei o score combinando histórico fechado, fit vendedor-produto/empresa/ticket, estágio, idade da oportunidade, completude de dados e regras de governança.
5. Criei saídas para vendedor e gerente, incluindo fila de aprovações para remanejamento e revisão gerencial.
6. Validei o front por screenshots e validei os dados por script automatizado.

### Resultados / Findings

- Pipeline total analisado: 8.800 oportunidades.
- Pipeline aberto pontuado: 2.089 oportunidades.
- Deals em fila de aprovação gerencial: 132.
- Recomendações de remanejamento: 22.
- Deals com conta ausente no pipeline aberto: 1.425, tratados como risco de qualidade de dados.
- Benchmark criado contra baselines `value_only`, `seller_win_rate_baseline`, `product_win_rate_baseline` e `v1_compatible_score`.

Artefatos principais:

- [`solution/lead-scorer/SOLUTION.md`](./solution/lead-scorer/SOLUTION.md)
- [`solution/lead-scorer/PROCESS_LOG.md`](./solution/lead-scorer/PROCESS_LOG.md)
- [`solution/lead-scorer/frontend/index.html`](./solution/lead-scorer/frontend/index.html)
- [`solution/lead-scorer/scripts/validate_outputs.py`](./solution/lead-scorer/scripts/validate_outputs.py)
- [`docs/frontend_visual_validation.md`](./docs/frontend_visual_validation.md)
- [`docs/project_critical_review.md`](./docs/project_critical_review.md)

### Recomendações

- Usar o score para priorização diária dos vendedores, com explicabilidade visível por deal.
- Exigir aprovação gerencial para remanejamento e `manager_review`, evitando redistribuição automática injustificável.
- Não sobrecarregar apenas os melhores vendedores; aplicar capacidade e carteira atual como restrição operacional.
- Tratar vendedores de baixa performance como `last_chance` controlado, não como destino padrão de oportunidades relevantes.
- Corrigir dados de conta antes de usar o modelo como insumo de forecast executivo.

### Limitações

- O dataset é histórico e não contém alguns sinais operacionais modernos, como origem do lead, atividade recente, SLA, próxima tarefa ou motivo textual da perda.
- A solução evita inferência temporal vazada, mas não substitui um snapshot real de CRM em produção.
- A transcrição do chat foi mantida como evidência útil, mas não é uma exportação forense oficial do cliente.
- O front é estático e pronto para demonstração local; não inclui backend, login real ou escrita de aprovações.

---

## Process Log - Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|---------------|
| Codex | Leitura do challenge, ETL, análises, modelagem de score, front estático, validações e empacotamento |
| Kaggle dataset | Fonte dos dados CRM Sales Predictive Analytics |
| Pesquisa anexada | Benchmarks e hipóteses para score/pipeline, comparadas criticamente com o universo do desafio |

### Workflow

1. Comecei pelo contexto do challenge e pelos CSVs brutos.
2. Fiz deep dive dos dados para entender tabelas, estágios, lacunas e distribuição de oportunidades.
3. Padronizei os dados por ETL reproduzível antes de modelar score.
4. Analisei vendedores por carteira, moda, mediana, desvio padrão, performance e maturidade histórica.
5. Modelei fit vendedor-produto/empresa/ticket para evitar priorização apenas por valor ou por vendedor estrela.
6. Comparei o racional com a pesquisa anexada e descartei técnicas excessivamente acadêmicas para manter execução prática.
7. Criei portal vendedor e portal gerente, com aba de cenário e aba de aprovações.
8. Rodei validações de dados, sintaxe e screenshots do front.

### Onde a IA errou e como corrigi

- O primeiro empacotamento ficou no diretório do challenge; corrigi para o padrão oficial `submissions/guilherme-sette/`.
- A tentativa de push direto no repositório oficial falhou por permissão `403`; removi a branch enviada ao fork e deixei a submissão local preparada no formato correto.
- A validação de `git diff --check` apontou CRLF/whitespace em CSVs; normalizei line endings e revalidei os dados.
- A validação visual encontrou overflow horizontal no front; ajustei CSS e recapturei screenshots.

### O que eu adicionei que a IA sozinha não faria

O julgamento central foi não transformar lead scoring em ranking ingênuo de maiores tickets. A solução trata roteamento como decisão operacional: considera fit histórico do vendedor, risco de dados, idade do deal, governança de aprovação e restrição de capacidade para não concentrar tudo em poucos vendedores. Também inclui red flags para baixa performance e uma camada de revisão humana onde a automação seria frágil.

---

## Evidências

- [x] Chat export: [`process-log/chat-exports/full_chat_transcript.md`](./process-log/chat-exports/full_chat_transcript.md)
- [x] Process log: [`process-log/PROCESS_LOG.md`](./process-log/PROCESS_LOG.md)
- [x] Screenshots do front: [`process-log/screenshots`](./process-log/screenshots/)
- [x] Git history local
- [x] Documentação crítica: [`docs`](./docs/)

---

_Submissao enviada em: 2026-06-23_
