# Protocolo de comunicação e handoff

## Regra central

Agentes trocam artefatos versionados, nunca memória implícita de chat. O Orchestrator envia somente objetivo local, caminhos autorizados, critérios de aceite, evidence IDs necessários e restrições. Nenhum especialista chama outro; devolve o pacote ao Orchestrator.

## Envelope obrigatório

```yaml
handoff_version: 1
run_id: "YYYYMMDD-HHMM-shortsha"
from: data-analyst
to: statistician
task_id: INF-001
objective: "validar associação entre patrocínio e engagement"
inputs:
  - path: outputs/tables/sponsorship_adjusted_input.parquet
    sha256: "..."
    contract: docs/contracts/analytical-dataset.md
evidence_ids: [EDA-SPON-001, EDA-SPON-002]
decisions_frozen: []
assumptions: []
limitations: []
acceptance_criteria: []
status: READY
```

## Evidence record

Cada finding usa: `evidence_id`, pergunta, população, período, unidade, métrica/fórmula, estimativa, intervalo, `n`, método, controles, robustez, fonte, script, limitações e estado (`EXPLORATORY`, `VALIDATED`, `REJECTED`). Estratégia e relatório podem citar somente `VALIDATED`, salvo quando rotulados explicitamente como hipótese.

## Contexto permitido

- Data Engineer recebe dados brutos e plano; não recebe recomendação desejada.
- Software Engineer (fundação) recebe escopo técnico, estrutura, contratos preliminares, requisitos de execução/qualidade e limitações; não recebe findings ou estratégia.
- Data Analyst recebe dataset validado e contrato; não recebe narrativa executiva alvo.
- Statistician recebe dataset analítico mínimo e evidence pack, nunca raw.
- Strategist recebe registros de evidência validados e restrições de negócio, nunca DataFrames.
- ML Engineer recebe feature contract e target aprovados; não recebe atributos pós-evento.
- Dashboard Builder recebe metric registry, tabelas serving e wireframe; nunca interpreta.
- Software Engineer (consolidação) recebe contratos congelados, componentes, comandos, testes esperados e limitações; pode verificar integração, mas não alterar evidências, métodos estatísticos, KPIs ou conclusões.
- Executive Writer recebe findings/decisions congelados; nunca recebe raw nem notebooks exploratórios.
- Reviewer recebe tudo que sustenta a entrega, mas opera read-only.
- GitHub Publisher recebe somente o pacote aprovado, verdict `PASS`, branch/remote alvo e autorização humana explícita.

## Solicitação de correção

```yaml
status: FAIL
issue_id: REV-STAT-003
owner: statistician
severity: BLOCKER
evidence: "intervalo não reproduz tabela fonte"
expected_fix: "recalcular e reconciliar INF-SPON-004"
impacted_artifacts: []
gates_to_rerun: [INF, STR, DOC, FINAL]
```

O receptor não corrige fora de seu domínio. Se a causa for upstream, devolve `BLOCKED_UPSTREAM` com evidência. Conflitos de evidência são escalados ao humano; não se resolve por votação entre agentes.

## Regras de escrita concorrente

- Um owner por artefato.
- Outputs de run são imutáveis; correções geram nova versão.
- Tabelas e gráficos possuem evidence ID no nome ou metadata.
- Nenhum agente edita relatório de outro; solicita correção.
- O manifest é escrito apenas pelo Orchestrator.

## Human-in-the-loop

Exigem aprovação: métrica primária, exclusões ambíguas, conclusão causal, política de investimento, decisão de ML, recomendações finais e publicação. A falta de aprovação deixa o gate em `BLOCKED`, nunca em `PASS` presumido.
