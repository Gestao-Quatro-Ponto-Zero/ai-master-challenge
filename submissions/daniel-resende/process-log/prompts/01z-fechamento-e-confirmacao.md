Prompt 01z of Daniel's G4 "AI Master" test (challenge 003, Lead Scorer): close stage 1. Confirm the frozen rule on dates it never saw, record Daniel's answers, and put the product's new shape to him. You stop with his decision written down. You build no interface and generate no AI text yet.

YOUR ROLE: you are still the BUILDER, the lead, in the same chat. The orchestrator read your report, your diary and your scripts, ran the six acceptance commands of prompt 01 (all exit 0; the audit and the validation reproduced byte for byte) and recomputed your headline facts with its own script on `dados/` (all matched). This prompt is the answer to your report.

FIRST:
- Run `date` and keep it as the real start. Time box: 25 minutes. At 25, stop and report what is finished and what is not.
- Copy this prompt, byte for byte, to `process-log/prompts/01z-fechamento-e-confirmacao.md`.
- Daniel types three answers in this chat next to this prompt: the fork (yes or no), the hour he started today, the date he downloaded the dataset. If one is missing, ask him once, and go on with the rest while you wait.

## Why
Your audit found the real answer to the challenge's own hint ("o que mais importa? Olhe os dados"): only time separates, and most of the open list is past any win on record. That is a different and stronger product than "the first five". Before Daniel decides on it, three things a verifier will attack must be measured, because the report as it stands cannot answer them: rule A was revised over six rounds against the same nine cuts it is scored on; the group table sums overlapping cuts, so one stale deal is counted up to three times; and the screen needs the time signal in a seller's words, since a percentage per deal does not calibrate.

## Goal
1. Daniel's answers. Write the hour he started and the download date in the diary and in `solution/data/FONTE.md`, as he gave them. If he said yes to the fork: create the public fork `danielgresende/ai-master-challenge` and link it to this clone as the remote `origin` (from inside the clone, `gh repo fork --remote --remote-name origin` is the form the help of this laptop's `gh` describes; it was not tried here). Then `git remote -v` must show `origin` as his fork and `upstream` as the G4 repository. Do not push.
2. Freeze. `solution/validate.py` stays byte for byte as it is in commit `53f9ed2`. Everything below goes into one new script, `solution/confirm.py`, that imports the rule from `validate.py` and changes nothing in it. Save its output as `docs/confirmacao-saida.txt`.
3. M1, the frozen rule on dates it never saw. The nine cuts that shaped rule A are 2017-06-01, 06-16, 07-01, 07-16, 08-01, 08-16, 09-01, 09-16 and 10-02. Run rule A and the two references ONCE on these three cuts, fixed by the orchestrator before any run: 2017-07-08, 2017-08-24 and 2017-09-24. Same measure as before (top 5 of each seller's list, wins and won value at 90 days), and for each cut the three groups with how many deals, won, lost, without outcome and the value won. Report the result as it comes out, also if rule A loses.
4. M2, no deal counted twice. For all twelve cuts print the group figures per cut. Then print, in distinct deals: how many different deals were ever placed in each group at any cut, and how many of those were won at any time in the data. The safety of "deixar ir" is stated in distinct deals.
5. M3, the time signal in a seller's words. For deals that reached a given age still open (0, 30, 60, 90, 120, 138 days, and beyond 138), print how many there were and how many were won afterwards, lost afterwards, or were still open when the data ended. Print it as known on the reference date and as known on each of the three main cuts, so its stability shows. Say how you treat the deals that had not had time to close. This table is what the screen will say instead of a percentage ("de cada 100 negócios que chegaram abertos aos N dias, X foram ganhos depois").
6. The product's new shape, which the orchestrator proposes and Daniel decides here, in his own words:
   - One headline for the seller ("você tem N vivos, M na fila, K para limpar") and three blocks instead of "the first five".
   - Vivos: the deals still inside the window in which deals have ever closed, ordered by value, each with its countdown (days left before it leaves that window) and what happened to deals like it, in words, never a percentage per deal. Nothing on the screen may suggest that one living deal closes more often than another: your own numbers show the same win share in both living groups; the order among the living is value and the deadline.
   - Fila para engajar: the 500 Prospecting deals, shown as the seller's next work, ordered by list price, with the screen saying that nothing else in the data ranks them.
   - Limpar: the deals past the window, with the evidence in distinct deals and the action (close them in the CRM and stop spending Monday on them).
   - "Ver uma segunda-feira do passado": a short fixed list of past dates on which the screen shows what the tool would have told that seller, using only what was known then, and what happened afterwards. The validation already computes this per cut. The default is the reference date, shown with the remark that it is the last day of a quarter.
   - Manager: pipeline health in facts only: living against dead value per seller and per region, who has no living deal, the size of each queue. "Quem insiste no que não fecha" becomes the count of dead deals each seller still carries.
   - Cut: "casos parecidos" by product, sector or size, any percentage per deal, "os cinco primeiros" as a fixed number.
   - AI layer: only where there are facts: the wording of each living deal's reason and next step, the Monday briefing built from the three blocks, the manager's summary. The product is whole without it.
   For each block say, in the report, what your numbers support and what they do not.
7. Report `relatorios/01z.md` (outside the fork), in Portuguese, one page: the M1 table; M2 in distinct deals; the M3 table in a seller's words; which cuts shaped the rule and which only tested it, with the plain statement that the three new cuts overlap the old ones in time and that no period exists that the rule never saw; what the data supports in each block of the new shape; the real minutes.
8. The diary: this step with its real times, what went wrong and how you noticed. Then tell Daniel in this chat, in at most twelve lines, the M1 result and the new shape, and ask him ONE question: rule A frozen as it is, with this shape of the product: sim, não ou muda. Write his answer as he gave it under "O que o candidato decidiu", ask him for one screenshot of that exchange saved by him into `process-log/screenshots/`, commit, and stop. Do not push.

## Acceptance (run from `ai-master-challenge/`)
1. The rule is frozen and the branch is still only the submission folder, by Daniel, without trailers.
   $ git diff --quiet 53f9ed2 HEAD -- submissions/daniel-resende/solution/validate.py && test "$(git branch --show-current)" = "submission/daniel-resende" && test -z "$(git diff --name-only upstream/main...HEAD | grep -v '^submissions/daniel-resende/')" && test "$(git log upstream/main..HEAD --format='%an <%ae>' | sort -u)" = "Daniel Gomes Resende <danielgomesresende@gmail.com>" && test -z "$(git log upstream/main..HEAD --format=%B | grep -iE 'co-authored-by|generated with')"
2. Every file of the folder on disk is committed (caches aside).
   $ diff <(git -c core.quotepath=off ls-files submissions/daniel-resende | sort) <(find submissions/daniel-resende -type f -not -path '*/__pycache__/*' | sort)
3. The confirmation runs in a clean environment and reproduces the saved output byte for byte.
   $ S=submissions/daniel-resende && V=$(mktemp -d) && python3.12 -m venv "$V" && "$V/bin/pip" install -q -r $S/solution/requirements.txt && "$V/bin/python" $S/solution/confirm.py | cmp -s - $S/docs/confirmacao-saida.txt
4. The three confirmation cuts are in that output.
   $ F=submissions/daniel-resende/docs/confirmacao-saida.txt && grep -q 2017-07-08 $F && grep -q 2017-08-24 $F && grep -q 2017-09-24 $F
5. Nothing is left pending, the decision is written, and this prompt and the report are in place.
   $ S=submissions/daniel-resende && ! grep -q PENDENTE $S/process-log/DIARIO.md $S/solution/data/FONTE.md && ! grep -q 'a preencher' $S/process-log/DIARIO.md && cmp -s ../prompts/01z-fechamento-e-confirmacao.md $S/process-log/prompts/01z-fechamento-e-confirmacao.md && test -s ../relatorios/01z.md
6. If Daniel said yes to the fork: it is linked and nothing was pushed.
   $ git remote get-url origin | grep -q 'danielgresende/ai-master-challenge' && test -z "$(git ls-remote --heads origin 'submission/*')"

## Traps
- `validate.py` is frozen: import from it, do not copy a function out of it and do not edit a constant. Run as a file, `confirm.py` finds `validate.py` beside it; under `python -I` it would not, so add the script's own directory to the path explicitly.
- M1 runs once. Nothing in the rule changes after you see its result. If the result surprises you, it goes into the report as it is, with what you think explains it.
- The three confirmation dates are fixed in this prompt. Do not replace one because it has few deals: say so in the report.
- The confirmation cuts are not independent of the nine: the same deals are open across neighbouring dates. Call it what it is, a check that the rule was not tuned to particular dates.
- New files under `submissions/` are ignored until added: `git add -f <file>`, by explicit list.
- If `gh repo fork` names the remotes differently from what this prompt expects, fix the names with `git remote rename` and say what happened. A fork is public: only with Daniel's yes in this chat.
- Do not rewrite the contracts, the example facts or `PRODUTO.md` now. `PRODUTO.md` is the orchestrator's file: after Daniel decides, the orchestrator updates it from his words, and the next prompt starts by rewriting the two contracts from it.
- The screenshot is Daniel's to take. If the file is there when you commit, add it; its name in ASCII.
- The diary entry is written when the step ends, with real times from `date`.
