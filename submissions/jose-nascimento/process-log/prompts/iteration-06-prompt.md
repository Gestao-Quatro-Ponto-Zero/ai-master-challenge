# Prompt integral — Iteração 06 (reprodutibilidade e execução em um comando)

Arquivado em 2026-08-28 pelo executor antes da implementação (prática das
Iterações 01–05). Texto integral recebido pelo agente executor:

---

Você é o AGENTE EXECUTOR ÚNICO da ITERAÇÃO 06 — reprodutibilidade e execução em um comando — do G4 AI Master Challenge. Integre os scripts 01–05 sem mudar resultados analíticos. NÃO escreva relatório executivo final (It07) nem process log final (It08)/PR.

REPO
- `/tmp/opencode/ai-master-challenge-work`, branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`, HEAD `e0c6b7ec582aa1e356d8e05e3afb99edaebdbbd2`.
- Leia instruções oficiais, plano/checklist, scripts/evidence/reviews, `.gitignore`, requirements e manifests de outputs.

OBJETIVO
Um avaliador em clone fresco, offline quanto aos dados, deve conseguir instalar dependências documentadas e regenerar deterministicamente todos os artefatos das It01–05 com **um comando**, recebendo falha útil/nonzero se estrutura/invariantes quebram.

TAREFAS
1. Inspecione imports reais de todos scripts e versões runtime. Minimize `requirements.txt`: remova dependências não usadas (DuckDB/seaborn/Jupyter etc. se de fato não importadas); use pins/constraints defensáveis e documente Python/versões testadas. Não adicione framework.
2. Crie na raiz da pasta do candidato:
   - `run.sh` executável, `set -euo pipefail`, resolve path próprio, preflight Python/deps/data, executa scripts 01→05 em ordem, propaga exit code, sem rede, sem paths pessoais, resumo final curto;
   - `Makefile` mínimo (`all`, estágios úteis, `verify`, `clean-derived` apenas se seguro). `make all` deve chamar o mesmo pipeline, não duplicar lógica;
   - `solution/README.md` com setup Linux/macOS, venv opcional, `pip install -r requirements.txt`, um comando, outputs, estrutura, tempo/memória medidos, troubleshooting, definições/lenses, aviso de dados inclusos/licença.
3. Crie verificador mínimo `solution/src/06_verify_pipeline.py` (stdlib/pandas apenas se necessário), sem reimplementar análises. Deve verificar:
   - manifesto de 5 raw CSVs, scripts 01–05, evidence 01–05, account_month/tables e exatamente 6 PNGs;
   - CSVs parseáveis, outputs não vazios, Markdown presente, ausência dos 4 PNGs pruned;
   - outputs materiais consistentes (use contracts/gates existentes, não hardcode números de dados sem derivação);
   - zero arquivos binários proibidos (`.db/.duckdb/.sqlite`, venv/cache), paths pessoais/segredos em `solution/`;
   - exit 1 + diagnóstico estruturado em falha.
4. `run.sh` deve executar o verificador ao final. `make verify` executa só o verificador; stages podem ser targets mas `all` é fonte única.
5. Clean behavior: `clean-derived` nunca apaga raw/process-log; liste explicitamente arquivos regeneráveis ou não ofereça target se arriscado. Em clone limpo, pipeline não deve criar arquivos untracked/fora da pasta/4 PNGs removidos.
6. Testes obrigatórios:
   - clone fresco/local da branch em sandbox, sem copiar `/tmp/opencode/ravendata`, executar `./run.sh` usando somente raw commitados;
   - rodar 2× e `make all`; outputs byte-idênticos e tree sem mudanças após regeneração (exceto permissões pretendidas já commitadas);
   - executar de outro CWD;
   - simular dependency/data/schema ausente em sandbox: exit nonzero, mensagem útil, sem traceback/stale;
   - `make verify`; shellcheck se disponível (não instalar), `bash -n`, py_compile, imports;
   - medir tempo e peak-ish memory de forma honesta (aproximação declarada), sem prometer benchmark universal.
7. Verifique file mode executável de run.sh no git; CRLF; POSIX/bash; locale/timezone determinismo.
8. Evidência:
   - prompt integral `process-log/prompts/iteration-06-prompt.md`;
   - report `process-log/reports/iteration-06-reproducibility-report.md` com ambiente, versões, comandos/resultados, clone fresco, falhas, runtime/memória, errors reais, git/handoff;
   - decisions se houver trade-off pin/ranges;
   - atualize plano/checklist: It06 CONCLUDED após validação, gate 3x PENDING, futuras PENDING.
9. Não altere outputs analíticos por conveniência. Se versão pin muda bytes, investigue; não normalize silenciosamente. Preserve exatamente 6 PNGs.

CONTENÇÃO
- Sem Docker, CI, pre-commit, tox, poetry, uv lock, notebook, dashboard. Shell+requirements+Makefile+verificador basta.

GIT
- status/diff/log antes; só pasta; `git add -f`; filemode correto.
- Commit `build: one-command reproducible pipeline`.
- Sem amend/force/config/destrutivo; push/local==remote/tree limpo; diff-check/links/segredos.

ACEITAÇÃO
- `./run.sh` em clone fresco passa offline aos dados; `make all` igual; 2× determinista; verifier passa/falha corretamente; dependências mínimas; docs de setup; sem outputs extras; process/git completos.

REPORT FINAL
PASS/BLOCKED; hash/push; comando único; deps/versions; fresh-clone tests; runtime/memory; deterministic hashes/tree; failure tests; files; risks/handoff It07. BLOCKED se depender de `/tmp` externo, rede em runtime ou gerar diff/untracked.

---