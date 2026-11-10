[Trecho: passagens sobre ferramentas e instruções privadas do candidato foram retiradas desta cópia antes da publicação.]

Prompt 02z of Daniel's G4 "AI Master" test (challenge 003, Lead Scorer): the repository was organised for publication. Check where you are, fix one defect, and stop. Nothing is pushed.

YOUR ROLE: you are still the BUILDER, the lead, in the same chat.

FIRST: run `date` and keep it as the real start; time box 15 minutes; copy this prompt to `process-log/prompts/02z-repositorio-organizado-e-uma-correcao.md`.

## Why
Before anything is published, the orchestrator organised the repository with Daniel's ok. Nothing had been pushed, so the history of this branch was rewritten once, locally: scripts of the candidate's private tooling left the repository, the diary and seven prompt copies now record results only, and paths of the machine were replaced. Authors, dates and commit subjects are the same; the commit hashes changed. The repository is at the same path as before, `ai-master-challenge/` inside the test directory. From here on it is the only repository, and the two verifiers will attack exactly what it holds.

## Goal
1. Look before touching anything: `git status`, `git log -1 --format='%h %s'`, `git remote -v` and `sha256sum submissions/daniel-resende/solution/validate.py`. Expected: a clean tree; the subject "O link dos vencidos ao lado da linha do tempo abre a lista deles"; `origin` is Daniel's fork and `upstream` the G4 repository; the sha256 is `336760fdcc511cde2ad5d28e9437dd0b061a222b18f2f5f03e2a38164abca212`. The commit is `13efcdc` and the folder `submissions/daniel-resende/process-log/[pasta retirada]/` does not exist. If anything differs, and above all if that folder exists, you are in the old repository: change nothing, stop and tell Daniel.
2. `process-log/[pasta retirada]/` and `solution/tools/` are gone on purpose. Do not recreate them, and commit no script that checks screens or makes images: such scripts stay outside the fork. The diary and the commit messages, subject and body, record results: what changed, why, the numbers and the screenshots.
3. Restart the app from this clone and tell Daniel the address: `solution/out/` is not here and the run command rebuilds it.
4. One defect, found by the orchestrator on a clean clone: `python3.12 submissions/daniel-resende/solution/ai/check.py` crashes when `solution/out/` has not been built yet (`AttributeError: '_io.StringIO' object has no attribute 'reconfigure'`). `ai/facts.py` builds the score files under a redirected output and the build reconfigures the output. Fix the cause, look at `generate.py` and at any other entry that takes the same path, and add the test that would have caught it: the check run with no `out/` present.
5. One slip in the README, left by the change of words: "em relação à guardada", where the noun is now "o prazo".
6. A diary entry with real times and `relatorios/02z.md` in five lines.
7. Two commits: the first with the fix and its test; the second with the documents (the README, the diary and the copy of this prompt). Then run the acceptance below, after the last commit, and stop. Do not push.

## Acceptance (run from `ai-master-challenge/`, after the last commit; S=submissions/daniel-resende)
Commands 1 and 2 clone the branch, so they see only what is committed.
1. On a fresh clone, the check of the AI texts runs before any build.
   $ T=$(mktemp -d) && git clone -q --branch submission/daniel-resende . "$T/c" && python3.12 "$T/c/$S/solution/ai/check.py"
2. On that kind of clone, everything builds, obeys the contracts and passes the tests.
   $ T=$(mktemp -d) && git clone -q --branch submission/daniel-resende . "$T/c" && python3.12 "$T/c/$S/solution/build.py" > /dev/null && python3.12 "$T/c/$S/solution/check_contract.py" && python3.12 -m unittest discover -s "$T/c/$S/solution/tests" -q
3. The rule is the frozen one, the branch is only the folder, by Daniel, without trailers, the disk is committed, and the two folders did not come back.
   $ test "$(sha256sum $S/solution/validate.py | cut -d' ' -f1)" = "336760fdcc511cde2ad5d28e9437dd0b061a222b18f2f5f03e2a38164abca212" && test -z "$(git diff --name-only upstream/main...HEAD | grep -v "^$S/")" && test "$(git log upstream/main..HEAD --format='%an <%ae>' | sort -u)" = "Daniel Gomes Resende <danielgomesresende@gmail.com>" && test -z "$(git log upstream/main..HEAD --format=%B | grep -iE 'co-authored-by|generated with')" && diff <(git -c core.quotepath=off ls-files $S | sort) <(find $S -type f -not -path '*/__pycache__/*' -not -path '*/solution/out/*' | sort) && test ! -e $S/process-log/[pasta retirada] && test ! -e $S/solution/tools

## Traps
- Commit hashes cited in older prompts and in the diary belong to the history before the organisation. Do not edit them. From now on the frozen rule is identified by the sha256 above.
- The copies of prompts 02, 02c, 02d, 02e, 02v, 02w and 02x in the process log are excerpts and say so in their first line. Do not restore them from the originals.
- New files under `submissions/` are ignored until added: `git add -f <file>`, by explicit list. The local hook still refuses a path outside the folder and a key-shaped string.
