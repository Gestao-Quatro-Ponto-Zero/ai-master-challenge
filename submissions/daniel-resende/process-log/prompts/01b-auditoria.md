# 01b: data audit (sub-builder)

You are a sub-builder in Daniel's G4 "AI Master" practical test (challenge 003, Lead Scorer).
I am the lead builder: I integrate and commit. You write files and NEVER run git.
Time box: 20 minutes. At 20, stop and report what is finished and what is not.

## What this is for
A tool for a non-technical seller (35 sellers, ~8,800 CRM opportunities) who has two pains:
time lost on deals that will not close, and good deals left to cool. Before any screen exists
we must know what this data can honestly say about an OPEN deal. Your audit is the ground the
scoring design and the decision report stand on: every number the report cites must be printed
by your script.

## Where things are (absolute paths)
- Fork root: `ai-master-challenge`
- Data (already copied, do not change it): `<fork>/submissions/daniel-resende/solution/data/`
  with `accounts.csv`, `products.csv`, `sales_teams.csv`, `sales_pipeline.csv`.
- The dataset's own dictionary: `dados/metadata.csv`.
- The challenge text: `<fork>/challenges/build-003-lead-scorer/README.md`.
- The product: `PRODUTO.md` (read it: section 10 tests its assumptions).

## What to write (only these two files)
1. `<fork>/submissions/daniel-resende/solution/audit.py`: ONE script.
2. `<fork>/submissions/daniel-resende/docs/auditoria-saida.txt`: the script's stdout, saved by you after the final run.

## Constraints
- Python 3.12, standard library only (`requirements.txt` is empty on purpose). On this laptop
  `python3` is 3.14 and cannot create a venv; use `python3.12`.
- The script is run from the fork root (`python3.12 submissions/daniel-resende/solution/audit.py`):
  locate the data from `__file__`, never from the current directory.
- Deterministic. It never reads the system clock: "today" for an open deal is the reference
  date taken from the data, and the script prints it.
- Nothing you remember about this public dataset is a fact. Do not search the web and do not
  read any other candidate's work. Every statement comes from what the script computes.
- Do not silently fix anything: when a key does not join, print the exact values and counts,
  state the normalisation you apply, and apply it visibly.
- Code and comments in English; printed section titles and labels in Portuguese (the evaluators
  are Brazilian). ASCII file names. Numbered sections (`== 1. ... ==`) so a report can cite "auditoria §N".
- A win rate is always Won / (Won + Lost) with its n next to it. An open deal has no outcome.

## Sections the script prints
1. Rows and keys per table: counts, uniqueness of each key.
2. Joins that do not match: pipeline to accounts, to products, to sales_teams, in both directions
   (for example sellers with no deal at all), with the exact unmatched values and their counts.
3. Missing values per column, and per column by `deal_stage`.
4. What each stage means in the data: which fields are filled at each stage; what `close_value`
   holds on an open row; for Won, how `close_value` relates to the product's `sales_price`
   (distribution of the ratio); for Lost, what it holds.
5. Dates: range of `engage_date` and of `close_date`; engagements and closings per month; the
   reference date (the last date present in the data); the age of each open deal at the reference
   date (distribution), set against the time-to-close distribution of Won and of Lost.
6. Known while open versus known only after closing (leakage), column by column.
7. Win rate and time to close (median, quartiles) by every segment the data offers, each with n:
   product, series, account sector, account size bands (revenue, employees), office location,
   subsidiary or not, seller, manager, regional office, engage month or quarter. Also history
   known at the time: the account's (and the seller's) number of earlier closed deals and their
   earlier win rate, counting only deals closed BEFORE the deal's own engage date. For each
   segment say whether the spread is larger than noise (an interval or a hand-made chi-square is enough).
8. The cooling question, without leakage. Among deals with a known outcome: of those still open
   at age a days after engage (a = 0, 15, 30, 45, 60, 90, 120, 150...), what share was eventually
   won, and the median days still left. This is what "esfriando" must rest on. Say plainly how
   the deals with no outcome at the data's end (censored) could bias this, and by how much they
   could move the numbers.
9. The open deals today: how many per stage; per seller (min, median, max of list size; sellers
   with none); per manager and region; how many open rows lack an account, an engage date or
   anything else a score would need; the value they carry (list price), in total and per seller.
10. Each assumption of `PRODUTO.md`, tested, with a verdict (SUSTENTA / NAO SUSTENTA / PARCIAL)
    and its number: are there 35 sellers, and does each have an open list long enough for a "top
    five"? Does sorting by value fail (how does win rate relate to price)? Does time in the
    pipeline lower the chance (section 8)? Is there anything knowable while a deal is open that
    separates wins from losses, and how strongly? Are there enough "similar cases" (for example
    product by sector) to say what closes and what does not? Can the manager's three questions
    (who has a stalled pipeline, who insists on what does not close, where the team's value is)
    be answered from these columns?

## Done means
- `V=$(mktemp -d) && python3.12 -m venv "$V" && "$V/bin/python" <fork>/submissions/daniel-resende/solution/audit.py > /dev/null` exits 0,
  run from the fork root, and two runs print identical output.
- `docs/auditoria-saida.txt` is that output.

## What to send back to me (your final message, under 500 words)
The findings that change a scoring design, each with its number and section; anything that
surprised you; the reference date; what an open row actually holds; which assumptions of
`PRODUTO.md` fail; what you could not determine. No praise, no summary of the method.
