Prompt 04a of Daniel's G4 "AI Master" test (challenge 003, Lead Scorer): finish the README. The fixes and the three public steps come in the next prompt. Nothing is pushed.

YOUR ROLE: you are still the BUILDER, the lead, in the same chat. While you write, a verifier of another model family is attacking a clean clone of this branch; its findings come to you in the next prompt.

FIRST: run `date` and keep it as the real start; time box 12 minutes; copy this prompt to `process-log/prompts/04a-readme-final.md`.

## Why
The README's process block still holds the template's placeholder text. The template says that block is mandatory and that a submission without it is disqualified. It is also where an evaluator learns, in two minutes, what the candidate did and what the AI did.

## Goal
1. Fill every section of the README that is still the template's text, in Portuguese, short, from the diary and from the facts below. Nothing may be left of the template's examples (`_ex: ..._`), empty numbered items, unticked boxes with no decision, or `[data]`.
2. "Ferramentas usadas": a table, one row per tool, each with what it did and why it was chosen:
   - Claude Code in VS Code as the lead builder: Claude Fable 5 from 15:06 to 17:24, and Claude Opus 5.5 from 17:25 on. Daniel changed the model himself, for the last adjustments of the screen and what followed.
   - Sub-agents of Claude Code: the data audit, the scoring core, the AI layer, the reviewers who did not draw the screens, the fifteen-year-old test.
   - A research sub-agent with web search, twice: the scoring and the grounding of generated text; then the form of the chart.
   - The headless Claude Code CLI: the baseline, and the generation of the 148 texts (with the models the provenance records).
   - The Codex CLI as independent verifier, another model family, on a clean clone.
   - Two orchestrator sessions of Claude Code that never build: they planned, wrote and checked each prompt, ran the acceptance commands on clean clones, and organised the repository before publication.
   - The skill `visual-tier1`, by name only: "o método visual do Daniel".
   - The GitHub CLI.
3. "Workflow": numbered steps, one line each, in the order it happened: the rules read by two sessions and compared, and the product written before any code; the baseline; the audit; the scoring candidates compared without leakage; the rule frozen and run once on three new dates; Daniel's decision; the build in parallel; the interface redone four times; the words changed by Daniel; the repository organised; the verification; the fixes.
4. "Onde a IA errou e como corrigi": from the diary, each in one or two lines with how it was noticed: the audit's first verdict on time; the first rule that lost to sorting by value; the first group that let wins through; the baseline's first run; the table that counted the same deal several times; the chart of a statistic that no one could read in ten seconds, which the orchestrator's own prompt had asked for; the words that a seller would not know; the check of the AI texts that crashed on a clean clone. Leave a last item, "o que o verificador independente achou", with one line saying it is completed in the last step.
5. "O que eu adicionei que a IA sozinha não faria", in the first person, only facts: he refused the first plan as too small and set the rule that the test's rules are the floor and the product the ceiling; he required AI inside the product with no API key; he chose his way of working (an orchestrator that never builds, builders in parallel, an independent verifier of another family) and the time target; after the audit contradicted the first product page he decided the score and the new shape, and both pages are in the process log; he judged the first screens as too heavy with text and the charts as too complex, and set the bar that a fifteen-year-old must understand the picture; he replaced the tool's words by the ones a seller uses; he used the app and asked for the link to open the list; he approved each public step. Daniel reads this section before anything is pushed and changes whatever is not his: say so to him when you stop.
6. "Evidências": tick only what exists, each with its link: screenshots; git history; the diary; every prompt; the baseline; the verification report (added in the last step). Chat exports and screen recording stay unticked.
7. A short section "Depois da entrega": the command that recomputes everything, the drift report and what it watches, and how the real gain would be measured with a control group.
8. Three plain statements, in the process block:
   - The process log was organised before publication: scripts and instructions of the candidate's private tooling were left out, seven prompt copies are excerpts marked in their first line, and paths of the machine were replaced. Commit hashes cited inside prompts and diary belong to the local history before that; the frozen rule is `solution/validate.py` with sha256 `336760fdcc511cde2ad5d28e9437dd0b061a222b18f2f5f03e2a38164abca212`.
   - `PRODUTO.md`, `CLAUDE.md`, `prompts/` and `relatorios/`, named inside the prompts, are the working files outside the repository; what is published of them is in `process-log/` (`produto.md`, `piso.md`, `prompts/`).
   - The plan had two independent verifiers; one ran (another model family). The second, a fresh session of the same model, was cut for time.
9. The real time: Daniel started at about 13:30 and the first prompt to the builder was at 15:06; take the end from `date` when you finish and say that it is not the final number, which the last step writes. Say that sub-agents worked in parallel.
10. One commit, by explicit list. A diary entry with real times. Tell Daniel, in five lines, what to read before the push. Stop. Do not push.

## Acceptance (run from `ai-master-challenge/`, after the commit; S=submissions/daniel-resende)
1. Nothing of the template's placeholder text is left.
   $ ! grep -n -E '_ex: |\[data\]|\[Seu Nome\]|_Liste as ferramentas|_Descreva passo a passo|_A IA fez algo errado|_Qual foi seu julgamento|_Anexe ou linke' $S/README.md
2. The three statements and the frozen rule's hash are in the README.
   $ grep -q '336760fdcc511cde2ad5d28e9437dd0b061a222b18f2f5f03e2a38164abca212' $S/README.md && grep -q -i 'trechos' $S/README.md && grep -q 'piso.md' $S/README.md
3. The branch is still only the folder, by Daniel, without trailers, the disk committed, the two folders absent, the tests passing on a fresh clone.
   $ test -z "$(git diff --name-only upstream/main...HEAD | grep -v "^$S/")" && test "$(git log upstream/main..HEAD --format='%an <%ae>' | sort -u)" = "Daniel Gomes Resende <danielgomesresende@gmail.com>" && test -z "$(git log upstream/main..HEAD --format=%B | grep -iE 'co-authored-by|generated with')" && diff <(git -c core.quotepath=off ls-files $S | sort) <(find $S -type f -not -path '*/__pycache__/*' -not -path '*/solution/out/*' | sort) && test ! -e $S/solution/tools && T=$(mktemp -d) && git clone -q --branch submission/daniel-resende . "$T/c" && python3.12 -m unittest discover -s "$T/c/$S/solution/tests" -q

## Traps
- Results only, as since the repository was organised: the README, the diary and the commit message say what was done and what came out, never how a screen check works or how an image is made. The skill is named, nothing of it is described.
- Every number in the README still comes from `numbers.py` or from a saved output; do not type a new one.
- Forty pages where five do is a named weakness: the process block fits on one screen and a half.
- New files under `submissions/` are ignored until added: `git add -f <file>`, by explicit list.
