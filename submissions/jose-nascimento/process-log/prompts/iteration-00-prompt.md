# Prompt do Agente Executor — Iteração 00 (transcrição fiel)

**Iteração:** 00 · **Arquivado em:** 2026-08-28 · **Uso:** evidência de processo (process log obrigatório). Transcrição fiel do prompt recebido pelo agente executor; apenas formatação markdown aplicada (conteúdo preservado).

---

Você é o AGENTE EXECUTOR da ITERAÇÃO 00 (planejamento e governança) de uma submissão real ao G4 AI Master Challenge. Trabalhe de forma autônoma, cuidadosa e verificável. Esta é uma etapa de planejamento; NÃO faça ainda a análise dos dados nem implemente a solução analítica.

## CONTEXTO E CAMINHOS
- Repo de trabalho/fork: `/tmp/opencode/ai-master-challenge-work`
- Branch esperada: `submission/jose-nascimento`
- Pasta exclusiva permitida pelo challenge: `/tmp/opencode/ai-master-challenge-work/submissions/jose-nascimento/`
- Instruções oficiais (leia por completo antes de editar):
  - `/tmp/opencode/ai-master-challenge-work/README.md`
  - `/tmp/opencode/ai-master-challenge-work/CONTRIBUTING.md`
  - `/tmp/opencode/ai-master-challenge-work/submission-guide.md`
  - `/tmp/opencode/ai-master-challenge-work/challenges/data-001-churn/README.md`
  - `/tmp/opencode/ai-master-challenge-work/templates/submission-template.md`
- Pesquisa interna (leia apenas como contexto, nunca copie/cite nas entregas finais):
  - `/home/ubuntu/aimaster_local/challenge-001-pipeline.md`
  - `/home/ubuntu/aimaster_local/angle-research-consolidated.md`
  - `/home/ubuntu/aimaster_local/competitors-analysis.md`
  - `/home/ubuntu/aimaster_local/evaluators-profile.md`
  - `/home/ubuntu/aimaster_local/pr-reviews-findings.md`
- Dados reais disponíveis, mas NÃO analisar nesta iteração: `/tmp/opencode/ravendata/`

## REGRAS DE ORQUESTRAÇÃO DEFINIDAS PELO CANDIDATO
- Cada etapa de execução será feita por exatamente um agente `deepseek-max`, sequencialmente.
- Ao terminar cada etapa, 3 agentes `deepseek-max` revisarão o resultado em paralelo e read-only.
- Se revisores encontrarem problemas materiais, outro agente sequencial fará as correções.
- Toda etapa deve produzir report estruturado em disco, com diretórios e filenames disciplinados.
- O plano deve ser atualizado ao fim de cada etapa, usando claramente apenas estes estados: `PENDING`, `OPEN`, `CONCLUDED`.
- O orquestrador não implementará código; apenas gerenciará agentes.

## SUA TAREFA
1. Inspecione branch, remotes, status, log e arquivos atuais. Preserve quaisquer mudanças existentes; não reverta nada.
2. Crie uma arquitetura mínima e clara de gestão dentro da pasta permitida, preferencialmente:
   - `process-log/management/execution-plan.md`
   - `process-log/management/orchestrator-checklist.md`
   - `process-log/reports/iteration-00-planning-report.md`
   Evite arquivos vazios/placeholders desnecessários. Remova `.gitkeep` apenas se ele ficar substituído por arquivos reais, e somente dentro da pasta do candidato.
3. Escreva `execution-plan.md` com um plano completo, pequeno passo por vez, até conclusão e PR. Deve incluir, no mínimo:
   - Iteração 00: planejamento/governança
   - ingestão e auditoria dos 5 datasets
   - reconciliação das definições/grãos de churn e contrato analítico
   - análise de causa raiz/coortes/onboarding economics
   - análise de ciclos de reativação + jornada completa + watchlist
   - recomendações/impacto/priorização e distinção correlação vs causalidade
   - artefato reproduzível e validação técnica (1 comando)
   - relatório executivo/visualizações
   - process log/evidências reais (incluindo prompts, erros da IA, correções e julgamento humano)
   - QA final integral contra todas as instruções oficiais
   - git/PR final
   Para cada iteração, registre: objetivo, entradas, artefatos esperados, critérios objetivos de aceitação, validações, commit esperado, dependências e status. Use exatamente `PENDING`, `OPEN`, `CONCLUDED`. Nesta entrega, Iteração 00 deve terminar `CONCLUDED`; as seguintes ficam `PENDING`.
4. Escreva `orchestrator-checklist.md`, checklist interno exaustivo porém operacional, cobrindo: regras oficiais; modificação somente da pasta; process log obrigatório; ferramenta real (opencode como orquestrador + subagentes deepseek-max); dados e licenciamento; reprodutibilidade offline; auditoria das 5 tabelas; números verificáveis; correlação/causalidade; contas específicas; impacto estimado com premissas; limitações; originalidade; ausência de referências/cópia das análises públicas; higiene do repo; commits semânticos; author do candidato; setup; PR title; revisão 3x após cada iteração. Cada item deve ter estado `PENDING`, `OPEN` ou `CONCLUDED`, não afirmar algo ainda não realizado.
5. Escreva `iteration-00-planning-report.md` estruturado com: objetivo; inspeções realizadas; arquivos criados/alterados; decisões; validações feitas; riscos/pendências; resultado da iteração; handoff explícito para Iteração 01. Inclua o prompt integral ou uma transcrição fiel dele como evidência (pode ser apêndice no report ou arquivo separado sob `process-log/prompts/`, desde que disciplinado).
6. Corrija qualquer informação incorreta no README scaffold APENAS se for claramente necessária para honestidade nesta iteração. Atenção: a ferramenta não é "Claude Code/deepseek-v4-flash"; o processo real usa opencode como orquestrador e subagentes `deepseek-max`. Não invente LinkedIn nem declare checks concluídos sem evidência.
7. Faça validações locais apropriadas para Markdown/estrutura e `git diff --check`.
8. Faça commit semântico somente dos arquivos dentro de `submissions/jose-nascimento/`, respeitando que o `.gitignore` raiz ignora `submissions/` (use `git add -f` somente nos paths pretendidos). Não altere nenhum arquivo fora da pasta. Commit sugerido: `docs: establish execution plan and governance`.
9. Faça push para `origin submission/jose-nascimento` se o commit for bem-sucedido.

## DISCIPLINA GIT
- Antes de commitar: inspecione `git status`, `git diff`, `git log --oneline -10`.
- Não use reset/checkout destrutivo; não faça amend; não force-push; não mexa em git config; não modifique fora da pasta permitida.
- Depois: valide `git status`, commit criado, arquivos no commit e remote tracking.

## REPORT FINAL PARA O ORQUESTRADOR
Retorne somente um report estruturado e objetivo com:
- Status: PASS / BLOCKED
- Commit hash e push
- Arquivos criados/alterados
- Validações executadas e resultados
- Riscos/pendências para revisores
- Handoff da Iteração 01
Se algo bloquear, documente exatamente e NÃO finja conclusão.