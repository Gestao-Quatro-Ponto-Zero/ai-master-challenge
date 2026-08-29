# Prompt — Iteração 01 · Ingestão e auditoria dos 5 datasets

Transcrição fiel do prompt recebido pelo agente executor desta iteração (arquivado por evidência de processo, conforme regra de governança).

---

Você é o AGENTE EXECUTOR ÚNICO da ITERAÇÃO 01 — Ingestão e auditoria dos 5 datasets — de uma submissão real ao G4 AI Master Challenge. Execute somente esta iteração, de ponta a ponta, com disciplina de evidência e git. NÃO avance para reconciliação de churn (Iteração 02) nem para conclusões de negócio.

REPO/BRANCH/ESCOPO
- Repo: `/tmp/opencode/ai-master-challenge-work`
- Branch: `submission/jose-nascimento`
- Pasta única permitida para alterações: `/tmp/opencode/ai-master-challenge-work/submissions/jose-nascimento/`
- Dados-fonte locais (somente leitura): `/tmp/opencode/ravendata/`
- Instruções oficiais: leia `README.md`, `CONTRIBUTING.md`, `submission-guide.md`, `challenges/data-001-churn/README.md` e o template antes de editar.
- Governança: leia integralmente `submissions/jose-nascimento/process-log/management/execution-plan.md`, `orchestrator-checklist.md`, reports/reviews da Iteração 00. Obedeça política de contenção 4–6h e originalidade.

OBJETIVO
Criar uma ingestão offline, reproduzível e auditável dos cinco CSVs RavenStack; provar estrutura/qualidade/integridade com checks executáveis e relatório gerado pelo código. Esta fase identifica problemas de dados, mas NÃO escolhe ainda uma definição de churn nem declara causa raiz.

TAREFAS OBRIGATÓRIAS
1. Inspecione branch/status/log/remotes. Preserve tudo; não reverta mudanças.
2. No início lógico da etapa, trate Iteração 01 como `OPEN`; ao terminar e validar o executor, marque-a `CONCLUDED` no plano. Demais iterações permanecem `PENDING`. Atualize checklist apenas com fatos comprovados.
3. Copie os 5 CSVs, byte-for-byte, para um path claro dentro da solução, preferencialmente `submissions/jose-nascimento/solution/data/raw/`. Compare MD5 origem/destino e contagens. Inclua `solution/data/raw/README.md` com origem oficial Kaggle citada pelo challenge, licença MIT conforme README oficial, snapshot/checksums, row counts, propósito e nota de uso offline. Não inclua links de análises públicas/concorrentes.
4. Implemente script mínimo e legível `solution/src/01_ingest_audit.py` (ou nome equivalente previsto no plano) com paths relativos ao próprio projeto, sem rede e sem hardcode `/tmp`/home. O script deve:
   - carregar os cinco CSVs;
   - validar presença, schema mínimo e row counts esperados como faixa/valor do brief;
   - reportar colunas/tipos, nulos, duplicatas de linha e de chaves candidatas;
   - validar FKs `account_id` e `subscription_id` entre tabelas;
   - parsear/validar datas e ordens temporais;
   - validar ranges/valores impossíveis para campos numéricos e categóricos relevantes;
   - verificar pelo menos: MRR/ARR, flags vs datas, CSAT/domínio, IDs duplicados, assinaturas sem uso, janelas de datas;
   - distinguir `PASS`, `WARN` e `FAIL`: anomalia esperada de qualidade deve ser WARN; arquivo/schema/chave estrutural ausente deve ser FAIL;
   - gerar deterministicamente `solution/evidence/01_audit_report.md` com metodologia, checks, números e proveniência.
5. Execute o script a partir da pasta da submissão; valide idempotência (duas execuções com output estável, checksum ou diff). Faça 3 verificações manuais independentes dos achados mais materiais diretamente nos CSVs (Python/csv/pandas é permitido; registre comando/metodologia e resultado). Não use números de pesquisa interna como fonte.
6. Documente parecer de sinteticidade somente com evidência objetiva (ex.: padrões/distribuições), sem extrapolar causa de negócio. Registre limitações da auditoria.
7. Atualize `requirements.txt` apenas se realmente necessário; sem dependências desnecessárias. Não implemente DuckDB/ML/dashboard.
8. Evidência de processo:
   - arquive este prompt integral em `process-log/prompts/iteration-01-prompt.md`;
   - crie `process-log/reports/iteration-01-ingest-audit-report.md` com objetivo, workflow, decisões, arquivos, resultados, 3 verificações manuais, comandos de validação, problemas/erros reais encontrados e corrigidos (não inventar), riscos e handoff da Iteração 02;
   - se houver decisão relevante, registre claramente julgamento do executor vs output da IA.
9. Remova `.gitkeep` de `solution/` se substituído por arquivos reais. Não altere nada fora da pasta do candidato.
10. Valide: execução offline, duas execuções idênticas, `git diff --check`, ausência de paths pessoais/segredos, escopo do diff, Markdown, checksums, nomes de arquivos, working tree esperado.

GIT
- Antes do commit: `git status`, `git diff`, `git log --oneline -10`.
- Root ignora `submissions/`: use `git add -f` apenas nos paths pretendidos.
- Commit semântico esperado: `feat: ingest and audit RavenStack datasets`.
- Não amend, não force-push, não config, não comandos destrutivos.
- Push para `origin submission/jose-nascimento`; depois valide HEAD local/remoto e working tree limpo.

CRITÉRIOS DE ACEITAÇÃO
- 5 CSVs no repo, MD5 iguais à origem, licença/fonte documentadas, pipeline sem rede.
- Script roda exit 0 quando estrutura essencial está íntegra, produz report auditável e não esconde WARNs.
- Todos os cinco datasets auditados e conectividade das chaves testada.
- Pelo menos 3 achados materiais rechecados independentemente e registrados.
- Sem conclusão prematura de causa raiz; plano/checklist/report honestamente atualizados.
- Commit/push completos e somente na pasta permitida.

REPORT FINAL AO ORQUESTRADOR
Retorne report estruturado com: Status PASS/BLOCKED; commit+push; arquivos; resumo dos checks PASS/WARN/FAIL; 3 verificações manuais; erros reais/correções; validações; riscos; handoff exato da Iteração 02. Se qualquer critério falhar, use BLOCKED e não finja conclusão.