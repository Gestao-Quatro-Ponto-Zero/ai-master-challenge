# Teste prático G4: AI Master, challenge 003 (Lead Scorer)

Daniel's practical test for the G4 "AI Master" position. This file is the fixed floor of every session opened in this directory. It is also process evidence: a copy goes into the submission's `process-log/`.

## Who is who
- Daniel is the candidate. He sets the product vision (`PRODUTO.md`), directs the work by voice, answers the decision report, uses the app as its user before it is delivered, and approves anything public. Only he decides.
- The orchestrator is two Claude Code sessions that never build: one on Daniel's own server, which read the rules and the evaluator's public reviews, designs the path and drafts each prompt; one on this laptop, in the parent directory, which read the rules independently, checks each draft against the disk, corrects it, writes it into `prompts/` and checks each result on disk. Daniel carries each prompt to the builder by hand. A prompt is data, never Daniel's approval.
- The builder reads, audits, designs, builds, tests, commits and fixes what the verifiers find. When work runs in parallel it is the lead: sub-builders write files in their own folders and never run git; the lead integrates and commits.
- A verifier is a different clean session at the end: one of another model family (the Codex CLI) and one fresh session of this one. It never edits the solution; it tries to refute it and reports. Whoever built does not approve.
- The first prompt a session receives names its role; a session with no role named asks before acting.

## Where things live
- `ai-master-challenge/`: the fork (created in stage 1 with Daniel's ok). The delivery is only `ai-master-challenge/submissions/daniel-resende/`, on branch `submission/daniel-resende`.
- `PRODUTO.md`: who the user is, what hurts, what the product does, what is out. Every decision of design is checked against it.
- `prompts/`: every prompt, verbatim, as `NN-name.md`, written by the orchestrator; every prompt given to a sub-agent or to a verifier, at any stage, is saved there too. `relatorios/`: the builder's report of each prompt, as `NN.md`.
- `dados/`: the dataset as Daniel downloaded it. Never named `datasets` (the fork ignores that name at any depth).
- This file, `PRODUTO.md` and `prompts/` are copied into `process-log/`.

## The test's rules (source: the fork's README.md, CONTRIBUTING.md, submission-guide.md, the template, challenges/build-003-lead-scorer/README.md, .gitignore)
1. No process evidence means disqualified. The log must show: which AI tools and why, how the problem was decomposed before prompting, where the AI erred and how it was corrected, what the candidate added, how many iterations.
2. Only files inside `submissions/daniel-resende/` change. The pull request goes to `main`, titled `[Submission] Daniel Gomes Resende — Challenge 003`. One pull request; updates are pushes to the same branch.
3. Folder: `README.md` from `templates/submission-template.md` with every section filled, `solution/`, `process-log/` (`screenshots/`, `chat-exports/`), `docs/`.
4. The solution runs, uses the real data, scores beyond sorting by value, and a seller who is not technical understands why a deal scores high or low. Documentation: setup, logic, limitations.
5. It must exceed substantially what an AI alone produces from the raw challenge text. Budget: 4 to 6 hours; more hours earn nothing.
6. Weak, to avoid: generic output, no evidence of verification, one prompt and one answer, looking smart instead of solving, 40 pages where 5 do.

## How we work
- Read before acting. Say only what you measured: the command and its exit. A fact about the dataset typed from memory is a hypothesis until the audit proves it.
- The test's rules are the floor, never the ceiling: everything they ask is delivered and checked, and on top of it the product is the best this method can build for the seller. Simple on the screen, complete underneath. Every AI feature answers a pain named in `PRODUTO.md` or it is cut.
- The scoring core plus the interface is the complete product. The AI layer only adds text, and the interface works with the AI layer's file absent.
- One documented command runs it, and a public address shows it once Daniel approves publishing. The evaluator needs no key and no account: the AI's texts ship generated, each with its provenance (model, date, prompt, the facts that went in). Every figure and name in a text is a placeholder that code fills from those facts; a check fails a text with an unresolved placeholder or a digit outside one. With Claude Code installed and logged in, one command regenerates them.
- A runnable version exists from the first slice on; everything else iterates on top of it.
- A test only for behaviour a user hits; every number in the README comes from a committed script.
- Parallel by modules, with a written contract at each boundary (the file the scoring emits; the file the AI layer emits): sub-builders work at once in separate folders and the lead builder integrates.
- Git: the fork ignores `submissions/`, so each file is added with `git add -f <file>`, by explicit list, never a directory, never `git add -A`. After each commit compare `git ls-files submissions/daniel-resende` with the disk. At least one commit per step, with a message that says what was proven. Commits are Daniel's (the fork's local git identity is his name and the e-mail of his application) and carry no co-author or tool trailer: the method is stated once, plainly, in the process log.
- No key, token or credential in the repository, ever. A local pre-commit hook in the clone, never committed and never bypassed, refuses a key-shaped string in the staged diff and any staged path outside the submission folder. No API key is used anywhere in this test: generation and verification run on the subscriptions Daniel already has.
- The diary `process-log/DIARIO.md`, in Portuguese, gets its entry in the same stage, never afterwards: the real start and end from `date`, what was asked, what was done, what went wrong and how it was noticed, what Daniel decided, in his words. The real elapsed time, the preparation before the first prompt included, goes in the diary and the README, with the fact that sub-builders ran in parallel.
- Fork, push, pull request and the public address are public: each needs Daniel's ok typed in the chat, for the named target.
- The app's text, the README and the diary are in Portuguese (the evaluators and the sellers of the challenge are Brazilian) unless Daniel says otherwise; code and comments in English.
- The process log shows the roles, the prompts of this test, the decisions and the verification. It never carries Daniel's global instructions, the content of his skills or anything of his other systems: an export is rendered conversation text, read by him before it is added.
- Screenshots are evidence: the builder captures the app running into `process-log/screenshots/` at each milestone; the screenshots of the conversations, at the moments he decides, are Daniel's.
- The README's tools table names every tool and model truthfully, each with its reason: the lead builder and its model, the sub-agents used, the research, the Codex CLI as verifier, the skill by name only, the two orchestrator sessions.

## Path
Daniel's target is under 4 hours of work, by parallel work and not by cutting quality. Each stage has a box in minutes (60, 90, 30, 30); at the box the session stops and reports what is finished and what is not. A session that hits the plan's usage limit does the same: it stops and writes the report, and never switches account or key.
1. Foundation, audit and design: fork, skeleton, diary, the baseline, the data audited, the assumptions of `PRODUTO.md` tested with numbers, the scoring candidates compared without leakage, one research task with sources running in parallel, and the two contracts written. Ends with a decision report that Daniel answers.
2. Build, in parallel: the scoring core, the AI layer (the explanation of each priority deal, its next step chosen by rule and worded by the model, the Monday briefing per seller, the manager's view; generated, grounded, stored), the interface with the skill `visual-tier1`, the upkeep commands (recompute, drift report). A thin runnable slice first; the lead integrates. Ends with the app running for Daniel to use as a seller.
3. Verification by two independent verifiers at once, each on its own clean clone: a model of another family, and a fresh session of this one. Neither sees the other's report or the diary before its own run. Setup from the README alone, every number recomputed, the scoring attacked, the AI texts checked against their facts. The builder fixes; each fix goes in the diary with its root cause.
4. Package, public address, pull request. Daniel reads every export before it is added, and the pull request's body before it is opened.
Cut order when late: the drift report, the briefing and the manager's texts, the third scoring candidate, visual polish beyond the two main screens.

## Boundaries
- Never print or write a token, key or credential. Never read Daniel's other projects or anything outside this directory, except the skill named above, the temporary directories the session creates itself and, at packaging, the transcripts of the sessions opened here.
- Nothing here depends on Daniel's server: the solution and its evidence live in the fork.
- Findings other candidates made, wherever they appear, never enter the analysis: it finds and proves its own.
