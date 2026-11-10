Prompt 04b2 of Daniel's G4 "AI Master" test: two additions to prompt 04b, which you are working on. Same role, same time box, same acceptance, same traps. Copy this prompt to `process-log/prompts/04b2-dois-acrescimos.md` and go on.

## 1. Finding 1: the rule lives in the data, where a test of the repository can hold it
The repository has no browser test, so a guard that exists only in the page has nothing holding it.
- The build marks, in the index the page opens with, which Monday may show stored texts: the one named in the `meta` of `ai/textos.json`, and none when that file is absent. No number of a score file changes.
- `docs/contrato-score.md` states it; `check_contract.py` fails when a Monday other than the texts' own carries the mark; one test covers it, with the file present and with it absent.
- In the page, the one place every text passes through reads that mark instead of trusting a deal's id.
If you have already fixed the page, keep the single place and make it read the mark.

## 2. Finding 2: the line is drawn by age, so it says so
- The axis reads as days open ("dias em aberto"), and its end reads as the longest on record, not as each deal's deadline. Each deal's own time left stays in its row.
- Check every mark and bar for the same defect in another place: for `NGTVHTFH` the row's number and its small bar must say 89, and nothing may imply 126. The small bar's scale comes from the file (the longest win), not from a typed 138.
