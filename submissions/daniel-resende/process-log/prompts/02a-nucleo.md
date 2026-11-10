# 02a: the scoring core (sub-builder)

You are a sub-builder in Daniel's G4 "AI Master" practical test (challenge 003, Lead Scorer).
I am the lead builder: I integrate and commit. You write files and NEVER run git.
Time box: 30 minutes. At 30, stop and report what is finished and what is not.

## What this is for
A tool a non-technical seller opens on Monday. The data showed that only time separates a win
from a loss, so the product stands on one claim: an open deal is either ALIVE (still inside the
window in which deals have ever closed: at most 138 days open, and before the end of the quarter
that follows the engage quarter) or TO CLEAN (past that window). Evidence: no win in 717 distinct
deals placed outside the window on twelve measured cuts. Two independent verifiers will attack
your work on a clean clone, so what you prove must be proven by a command.

## Read first (absolute paths; `<S>` = `ai-master-challenge/submissions/daniel-resende`)
- `<S>/docs/contrato-score.md`: THE contract. Every emitted file must obey it.
- `<S>/solution/build.py`: the lead's thin slice, already emitting all six dated files and `index.json` into `<S>/solution/out/`. From now it is yours: review it line by line against the contract, fix what is wrong, keep the emitted shape. If you believe the contract itself is wrong, do not change the shape: tell me.
- `<S>/solution/validate.py`: the FROZEN rule (`world_at`, `open_at`, `fit_rules`, `is_dead`, `deadline`, `LEAK_FIELDS`, `KNOWN_FIELDS`, `CUTS`, `EXTRA_CUTS`). Never edit it, never copy a function out of it: import it.
- `<S>/solution/confirm.py` and `<S>/docs/confirmacao-saida.txt`: the twelve cuts, the distinct-deal evidence, the time table (M3).
- `<S>/docs/contrato-ia.md` only for the boundary named below.

## Deliver (only these files; touch nothing else: not `validate.py`, `confirm.py`, `run.py`, `web/`, `ai/`)
1. `<S>/solution/build.py`, reviewed and hardened as said above.
2. `<S>/solution/check_contract.py`: exit 0 only if every file in `solution/out/` obeys the score contract (fields, types, block rules, order, ranks, headline sums, team sums, the six Mondays, `after` only in the past, no queue in the past, no percentage sign and no field of `validate.LEAK_FIELDS` as a key outside `after`, `days_left >= 0` for every living deal, `time_sentence` carries "Cerca de" and the date or is the no-history sentence). When `<S>/solution/ai/textos.json` exists, it also calls `check_texts(path)` from `<S>/solution/ai/check.py` (another sub-builder writes it; it returns a list of error strings, empty when all is well) and fails if it returns errors or if that module is missing. Each failure is printed as one line saying which file, which deal, which rule.
3. `<S>/solution/numbers.py`: prints every number the README will cite, each on a labelled line, in Portuguese, all computed from the CSVs and the frozen rule (not read from `out/`): the default Monday's totals (alive, queue, clean, with list value) overall and per region; how many of the 35 sellers have no living deal and how many have a queue; the window (138 days; closings inside the deadline out of total); the distinct-deal evidence (717, won, lost, still open); the three confirmation cuts (wins and won value of "ordenar por valor" against rule A in each seller's top 5, taken from `confirm`/`validate` functions, without re-implementing them); the time table of the default date; for each past Monday how many deals were alive and to clean and what happened to each block afterwards (won, lost, still open, won value); how many open rows lack an account; how many list prices exist and in how many of the living lists' neighbouring pairs the value ties, so the tie-break decided. Save its output as `<S>/docs/numeros-saida.txt`. Deterministic: two runs are byte-identical.
4. `<S>/solution/drift.py`: the upkeep report. `python drift.py --store` writes `<S>/solution/window.json` with the closing window as fitted on the current CSVs (longest win in days, closings known, closings after the deadline, the time-table rows, the date). `python drift.py` re-fits from the CSVs and prints, in Portuguese, how far each value moved from the stored one and a plain verdict line ("janela estável" or what moved and by how much); exit 0 in both cases, exit 1 only if the stored file is missing. Run `--store` once so the file exists.
5. `<S>/solution/tests/test_core.py` (standard library `unittest`, on the real rows, no mocks): no field of `LEAK_FIELDS` reaches a score (the dict a deal is judged from holds only `KNOWN_FIELDS`); on the twelve cuts (`confirm.SHAPING_CUTS + confirm.CONFIRM_CUTS`) every deal that `build.build_monday` lists for the Monday after the cut lands in the block the frozen rule gives it (`is_dead` at that cut); a deal past the window is never among the living; a deal already closed at the cut is never listed as work; the deadline day is alive (take a real deal, build the Monday that equals its deadline, find it among the living; and the Monday after, among the ones to clean); the queue is empty on every past Monday. The tests add `solution/` to `sys.path` themselves: they are run with `python -m unittest discover -s <S>/solution/tests`, which puts only the tests folder on the path.

## Constraints
- Python 3.12, standard library only. On this laptop use `python3.12` (`python3` is 3.14 and cannot create a venv).
- Every script locates its files from `__file__`, sets `sys.dont_write_bytecode = True` before importing siblings, never reads the system clock, and runs from any directory.
- Code and comments in English; printed text in Portuguese. ASCII file names.
- Nothing you remember about this public dataset is a fact; do not use the web; do not read other candidates' work.
- `solution/out/` is generated and never committed; `window.json` and `numeros-saida.txt` are committed by me.

## Done means (run these and paste the exit codes in your report)
    cd ai-master-challenge && S=submissions/daniel-resende
    V=$(mktemp -d) && python3.12 -m venv "$V" && "$V/bin/python" $S/solution/build.py > /dev/null && "$V/bin/python" $S/solution/check_contract.py && "$V/bin/python" -m unittest discover -s $S/solution/tests -q
    "$V/bin/python" $S/solution/numbers.py | cmp - $S/docs/numeros-saida.txt
    "$V/bin/python" $S/solution/drift.py

## Send back (final message, under 300 words)
What you changed in `build.py` and why; any place where the contract and the files disagreed; the test count and exit codes; anything a verifier could attack that you could not close. No praise.
