# Prompt do Agente Corretor Sequencial — Iteração 00 (transcrição fiel)

**Iteração:** 00 (review gate 3x — correção sequencial) · **Arquivado em:** 2026-08-28 · **Uso:** evidência de processo (process log obrigatório). Transcrição fiel do prompt recebido pelo agente corretor; apenas formatação markdown aplicada (conteúdo preservado).

---

Você é o AGENTE CORRETOR SEQUENCIAL da ITERAÇÃO 00 de uma submissão real ao G4 AI Master Challenge. Corrija os findings materiais das três revisões read-only, preserve honestidade/proveniência e encerre o gate da Iteração 00. NÃO analise os datasets nem inicie a Iteração 01.

REPO E BRANCH
- Repo: `/tmp/opencode/ai-master-challenge-work`
- Branch: `submission/jose-nascimento`
- Pasta única permitida: `/tmp/opencode/ai-master-challenge-work/submissions/jose-nascimento/`
- Commit revisado: `efdec24ae7a5856467923c50398380ac25c0ade9`

LEIA INTEGRALMENTE ANTES DE EDITAR
- `/tmp/opencode/ai-master-review-reports/iteration-00/review-2b09e78d.md`
- `/tmp/opencode/ai-master-review-reports/iteration-00/review-17bd77aa.md`
- `/tmp/opencode/ai-master-review-reports/iteration-00/review-2c65e4af.md`
- Todos os artefatos da Iteração 00 sob `submissions/jose-nascimento/process-log/`
- `submissions/jose-nascimento/README.md`
- Instruções oficiais relevantes (`README.md`, `CONTRIBUTING.md`, `submission-guide.md`, challenge 001 README, template)

DECISÃO DE GOVERNANÇA (OBRIGATÓRIA)
- NÃO apague, reescreva ou sanitize retroativamente o prompt literal já commitado para esconder as fontes internas. O histórico existe e a evidência deve ser honesta.
- Em vez disso, registre disclosure transparente: pesquisa interna de benchmark foi usada apenas para mapear riscos/regras; nenhum número, código, fraseado ou conclusão será copiado; toda conclusão da solução será rederivada e reproduzível a partir dos 5 CSVs pelo pipeline próprio. Diferencie claramente pesquisa de benchmark de análise pública usada como fonte da solução.
- Corrija afirmações falsas de "zero ocorrências"/"nenhum path" para um escopo verdadeiro: zero cópia/citação de conclusões na solução nesta etapa; o prompt de gestão contém paths de pesquisa por transparência.

CORREÇÕES OBRIGATÓRIAS
1. `README.md`: remover a falsa data de submissão concluída; usar placeholder honesto até a Iteração 10. Não inventar LinkedIn.
2. `execution-plan.md`: adicionar política explícita de contenção alinhada ao budget 4–6h: escopo mínimo, no ML/dashboard opcional sem evidência, stop conditions, revisores paralelos, correções apenas materiais, artefatos/reports concisos. Não viole a exigência do candidato de revisão 3x após cada iteração.
3. Definir claramente a semântica dos estados: `OPEN` = executor trabalhando; `CONCLUDED` = implementação da iteração concluída e validada pelo executor; review gate 3x acompanhado separadamente no checklist/ledger; finding material pode reabrir/fixar antes da próxima etapa. Registre que Iteração 00 teve review gate e correção concluídos.
4. `iteration-00-planning-report.md`: corrigir a claim de grep/originalidade, a nota de paths, "Log (10 commits)" (deve refletir comando `git log -10`, não contagem), cross-reference incorreta e registrar hashes/review gate honestamente.
5. `orchestrator-checklist.md`: corrigir notas contraditórias E1/F2; marcar a revisão 3x da Iteração 00 como `CONCLUDED`; preservar demais itens honestos.
6. Criar um resumo versionado das revisões e ações, por exemplo `process-log/reviews/iteration-00-review-summary.md`, com: três veredictos/paths externos; findings por severidade; decisão de governança; matriz finding→ação→arquivo:linha; riscos residuais; gate final.
7. Arquivar este prompt de correção integral em `process-log/prompts/iteration-00-review-fix-prompt.md` e criar report `process-log/reports/iteration-00-review-fix-report.md` com objetivo, mudanças, validações, git, riscos e handoff.
8. Se útil para evidência, arquive uma única cópia do prompt comum dos três revisores em `process-log/prompts/iteration-00-review-prompt.md`, transcrição fiel. Não copie reports externos inteiros para o repo; o summary basta.
9. Corrija a ambiguidade sobre executor: opencode orquestra; exatamente um subagente `deepseek-max` executou a Iteração 00; três `deepseek-max` fizeram revisão read-only; este `deepseek-max` faz correção sequencial.

VALIDAÇÃO E GIT
- Antes: `git status`, `git diff`, `git log --oneline -10`; preserve tudo e não reverta mudanças alheias.
- Valide Markdown, estados permitidos, references, ausência de placeholders falsamente marcados, `git diff --check`, escopo somente na pasta permitida e matriz completa de findings.
- Use `git add -f` somente nos arquivos pretendidos (o root ignora `submissions/`).
- Commit semântico: `docs: address iteration 00 review findings`.
- Não amend, não force-push, não git config, não destructive commands.
- Push para `origin submission/jose-nascimento`; valide tracking/remoto e working tree limpo.

REPORT FINAL AO ORQUESTRADOR
Retorne report estruturado: Status PASS/BLOCKED; commit+push; matriz dos findings dos 3 reviewers e resolução; arquivos; validações; riscos residuais; handoff da Iteração 01. Não simule conclusão se algo falhar.