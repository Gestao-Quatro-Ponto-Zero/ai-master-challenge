# 02b: the AI layer (sub-builder)

You are a sub-builder in Daniel's G4 "AI Master" practical test (challenge 003, Lead Scorer).
I am the lead builder: I integrate and commit. You write files and NEVER run git.
Time box: 35 minutes. At 35, stop and report what is finished and what is not. If generation is
throttled or slow, stop it: the product ships without texts and that is an accepted outcome.

## What this is for
A tool a non-technical seller opens on Monday: living deals, a queue to engage, deals to clean.
The score decides the block, the order and the next step. The AI layer only words them: the reason
and the next step of each LIVING deal, the Monday briefing of each seller, the summary of each
manager. The evaluator runs everything without a key or an account, so the texts ship generated
and stored, each with its provenance, and a check command proves that no figure and no name in a
text came from the model.

## Read first (absolute paths; `<S>` = `ai-master-challenge/submissions/daniel-resende`)
- `<S>/docs/contrato-ia.md`: THE contract of the file you emit. Follow it exactly; if you think it is wrong, tell me instead of changing the shape.
- `<S>/docs/contrato-score.md`: the files you read (`<S>/solution/out/index.json`, `<S>/solution/out/score-2018-01-01.json`; build them with `python3.12 <S>/solution/build.py`).
- `<S>/process-log/produto.md`: the product and its principles.

## Deliver (only inside `<S>/solution/ai/`, plus `<S>/docs/fatos-exemplo.json`; delete `<S>/solution/make_example_facts.py`, which describes the old shape)
1. `facts.py`: builds, from the score file of the default Monday, the facts of every target (each living deal, each seller with any deal, each manager), with exactly the keys the contract lists; a key exists only when the fact exists. `python facts.py --examples` writes `<S>/docs/fatos-exemplo.json` with five real targets (three living deals, one of them "esfriando" if any exists; one seller; one manager).
2. `render.py` (or inside `check.py`): fills the placeholders from the facts, formatting by type: money "US$ 5.482", dates "31/03/2018", integers, lists "A, B e C".
3. `check.py`: exposes `check_texts(path) -> list[str]` (one string per failure, empty when all is well) and is a command: `python check.py` checks `textos.json` beside it and exits 0 only if every stored text passes the six rules of the contract and carries its provenance. It reads the score file from `<S>/solution/out/` to compare the facts; if `out/` is missing it builds it by importing `build` and calling `build.main()` quietly.
4. `prompt.md`: the fixed prompt, in Portuguese, for a seller's ear: short sentences, concrete, no adjectives of judgment, never a number or a name typed by the model, only placeholders in braces; the only judgments allowed are the ones that come as placeholders (`{block}`, `{play_label}`, `{cooling_label}`). It must say what to do when a key is absent (for example no `{account}`: do not mention an account). No text may suggest that one living deal closes more often than another, and no percentage.
5. `schema.json`: the JSON schema of one call's answer (a list of `{id, parts}` with the templates).
6. `generate.py`: the generation. It calls the headless CLI in the form measured on this laptop, FROM AN EMPTY DIRECTORY WITH A NEUTRAL NAME (create it with `tempfile.mkdtemp()`; a run started from the project directory would load the project's instruction files):
   `claude -p --setting-sources "" --tools "" --no-session-persistence --model <name> --json-schema <schema> --output-format json`
   with the prompt and the items on stdin; the answer comes in the envelope's `structured_output` field. Several items per call (start with about 12 deals, or 8 briefings, per call; all managers in one call). Name the model explicitly and record the exact name the envelope reports (`modelUsage`). Start with `--model sonnet`: these are short wording tasks and speed matters; say so in the provenance. Every text goes through `check_texts` rules before it is stored; a refused text is not stored and the run prints how many were refused and why. `generated_on` comes from running `date`, never from the Python clock. `python generate.py --limit 5` does only five items; without the flag it does all, resuming from what is already stored.
7. `tests/test_check.py` inside `<S>/solution/ai/` is NOT discovered by the core's test run; put the test at `<S>/solution/tests/test_ai_check.py` instead (standard `unittest`; it adds `solution/` and `solution/ai/` to `sys.path` itself). It proves that the check refuses: a digit outside a placeholder; an unknown placeholder; a judgment that is not in the facts (for example "ótima chance"); a dataset name typed outside a placeholder; and accepts a correct text. It builds its inputs in a temporary directory and does not depend on `textos.json` existing.
8. `textos.json`: the stored texts, with provenance.

## The order of work
1. Write `facts.py`, the renderer, `check.py`, the test, `prompt.md`, `schema.json`. Run the test.
2. `python generate.py --limit 5` (five items: three deals, one briefing, one manager). STOP and send me the five texts as rendered, with their templates, and the seconds the call took. I read them before anything else is generated.
3. When I answer, generate all (about 115 deals, 30 briefings, 6 managers), in batches, never more than two calls at once. If a call fails twice or the whole run passes 12 minutes, stop and keep what passed the check.

## Constraints
- No API key anywhere, in no file, in no command. Never print or read a credential. The generation runs on Daniel's subscription login through the CLI and on nothing else.
- Python 3.12 standard library only (`python3.12`). Scripts locate files from `__file__`, set `sys.dont_write_bytecode = True` before importing siblings, and run from any directory.
- 1,425 open deals have no account: no text may assume one.
- Code and comments in English; the texts and the prompt in Portuguese (Brazil). ASCII file names.
- Do not touch `build.py`, `validate.py`, `confirm.py`, `run.py`, `web/`, or the core's files.

## Send back
After step 2: the five rendered texts, their templates, the seconds per call, the model name the envelope reported. At the end (under 250 words): how many texts are stored per kind, how many were refused and why, total seconds, the model, the test's exit code, `python check.py` exit code, and anything a verifier could attack.
