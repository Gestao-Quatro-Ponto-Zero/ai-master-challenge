# Prompt do Agente Corretor Sequencial — Iteração 01 (transcrição fiel)

**Iteração:** 01 (review gate 3x — correção sequencial) · **Arquivado em:** 2026-08-28 · **Uso:** evidência de processo (process log obrigatório). Transcrição fiel do prompt recebido pelo agente corretor; apenas formatação markdown aplicada (conteúdo preservado).

---

Você é o AGENTE CORRETOR SEQUENCIAL da ITERAÇÃO 01 de uma submissão real ao G4 AI Master Challenge. Corrija os findings convergentes das três revisões read-only, valide regressões, registre o gate e pare. NÃO inicie a Iteração 02 nem faça reconciliação/causa raiz.

REPO/ESCOPO
- Repo: `/tmp/opencode/ai-master-challenge-work`
- Branch: `submission/jose-nascimento`
- Pasta única permitida: `submissions/jose-nascimento/`
- HEAD esperado: `80f6a3f4e8a94034173226d848fecf179bc9b031`

LEIA PRIMEIRO
- `/tmp/opencode/ai-master-review-reports/iteration-01/review-38738f37.md`
- `/tmp/opencode/ai-master-review-reports/iteration-01/review-44ca5ff5.md`
- `/tmp/opencode/ai-master-review-reports/iteration-01/review-caef990c.md`
- `solution/src/01_ingest_audit.py`, relatório gerado, report/prompt It01, plano/checklist, review summary It00 e instruções oficiais.

FINDING OBRIGATÓRIO CONVERGENTE
- Quando uma coluna esperada está ausente/renomeada, o script registra S01 FAIL mas continua em checks semânticos, levanta `KeyError`, imprime traceback e não regrava `solution/evidence/01_audit_report.md`, deixando output stale. O contrato exige exit não zero + diagnóstico estruturado + relatório atualizado, sem traceback não tratado.

TAREFAS
1. Corrija o script de forma mínima e robusta: após falha estrutural de schema, pule somente checks que dependam das colunas ausentes (ou use guard equivalente), preserve checks possíveis e GARANTA que o report seja sempre gerado. Não esconda FAIL e não faça catch-all que converta bugs reais silenciosamente. Exit deve ser 1 quando há FAIL.
2. Teste em sandbox (fora do repo ou com cópia temporária):
   - baseline duas vezes: exit 0 e output determinístico;
   - arquivo ausente: exit 1 + report com FAIL, sem traceback;
   - coluna-chave ausente (`account_id`): exit 1 + report com FAIL, sem traceback;
   - coluna categórica usada semanticamente (ex.: `industry`) ausente: exit 1 + report com FAIL, sem traceback;
   - data inválida: exit 1 + report com FAIL, sem traceback.
3. Reexecute baseline no repo para atualizar o report versionado; confirme que todos os números materiais continuam iguais. Registre novo checksum se output mudar.
4. Corrija também, se forem factualmente corretos e de baixo risco, os LOWs convergentes: gates de divergência devem ser condicionais (PASS quando zero/WARN quando >0, não WARN incondicional); `usage_id` deve ser chamado chave candidata, não chave primária do brief; claim de feature nos duplicados deve refletir 19/21, não 21/21; descrição C05 não invertida; commit esperado no plano deve refletir commit real ou ser descrito como intenção. Não faça refatoração ampla.
5. Crie `process-log/reviews/iteration-01-review-summary.md`: 3 veredictos/paths; finding convergente; matriz finding→ação→arquivo/linha; recálculos que passaram; testes pós-fix; riscos; gate final.
6. Arquive este prompt integral em `process-log/prompts/iteration-01-review-fix-prompt.md` e crie `process-log/reports/iteration-01-review-fix-report.md` com workflow, patch, testes, outputs, git, decisões e handoff It02.
7. Atualize checklist/ledger para marcar review gate 3x da It01 como `CONCLUDED`, sem marcar It02. Estados apenas `PENDING`, `OPEN`, `CONCLUDED`.

VALIDAÇÃO/GIT
- Antes: status/diff/log; preserve tudo, não reverta.
- Rode syntax/import checks, baseline idempotente e cinco cenários acima, `git diff --check`, escopo, Markdown/referências, grep de traceback/paths pessoais/segredos.
- Use `git add -f` só nos paths pretendidos.
- Commit: `fix: handle schema failures in data audit`.
- Sem amend/force/config/destrutivo. Push para `origin submission/jose-nascimento`; valide local==remote e tree limpo.

REPORT FINAL
Retorne Status PASS/BLOCKED; hash/push; causa raiz técnica; patch; matriz das três revisões; resultados exatos dos 5 cenários; estabilidade dos números; arquivos; validações; riscos e handoff It02. Não finja PASS se relatório stale ou traceback persistir.