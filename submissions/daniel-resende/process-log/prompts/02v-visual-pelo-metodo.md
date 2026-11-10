[Trecho: passagens sobre ferramentas e instruções privadas do candidato foram retiradas desta cópia antes da publicação.]

Prompt 02v of Daniel's G4 "AI Master" test (challenge 003, Lead Scorer): redo the interface by Daniel's visual method. It interrupts step 3c of prompt 02; when it is done you go on with prompt 02 from where you were. Nothing is pushed.

YOUR ROLE: you are still the BUILDER, the lead, in the same chat. The interface stays in your own hands. The core and the AI layer are not touched by this prompt, except where a text has to become shorter.

FIRST:
- Run `date` and keep it as the real start of this step. It runs inside the 90-minute box of prompt 02; if the box ends, stop and report.
- Copy this prompt, byte for byte, to `process-log/prompts/02v-visual-pelo-metodo.md`.

## Why
The seller's screen as it was rendered at 16:29 carries too much text for a seller who is not technical: a briefing paragraph beside the headline, a chart with its own paragraph and legend, a note of method under each block, two paragraphs under every deal. It reads like a report. Part of that is the orchestrator's doing: prompt 02 asked for many sentences on the screen. Daniel wants this product's screens made by his visual method, by you.

## Goal
1. The seller's first view, at 1366 by 768 and at 1920 by 1080, with no scrolling of the page: the headline, the three counts and the first living deals. Lists scroll inside their own panel.
2. One line per deal by default: the product, the account when there is one, the value, the days left, the mark "esfriando". Everything that explains it (the AI's text, the sentence of the time table, what "valor" is, the reason of the next step) opens on hover and on keyboard focus on a desktop, and on a tap on a phone, and closes again.
3. The notes of method leave the first view: the caveat about the order, the date of each count, the model that worded the texts, the table behind the window. They go into one panel, "Como a ferramenta decide", and one line of note at the foot of the screen. Nothing that prompt 02 required is deleted: every one of those sentences stays reachable in one action.
4. The briefing is a button that copies it, and may open it; it is not a paragraph beside the headline.
5. The window is read without a paragraph: the picture carries it, and the numbers under each age appear on hover.
6. "Para limpar" by default: the count, the value, one line of evidence, the action. The list opens on request.
7. On a phone (412 wide) the first living deal is reached within the first screen and a half, with no table and no paragraph before it.
8. The manager's screen and "ver uma segunda-feira do passado" follow the same discipline.
9. One element made by hand, with depth, that carries the one idea of this product, the window a deal has to close in. If, after trying, it does not help the seller read the screen in ten seconds, leave it out and say why in the report.
10. A text check: the words visible when the seller's view loads at 1366 by 768, before and after this prompt, and the longest visible paragraph. Target: at most a third of the words there are now, and no visible paragraph above twenty words in the first view.
11. Screenshots again, in place of the ones saved at 16:29; your reviewer who did not draw the screens looks at the new ones; the diary says what changed and why, with real times. Commit by explicit list. Then go on with prompt 02: Daniel uses the app.

## Acceptance (run from `ai-master-challenge/`; S=submissions/daniel-resende)
1. The page still renders its headline from a clean clone, with the texts file and without it (acceptance 3 of prompt 02, unchanged).
2. [item retirado desta cópia]
3. The interface is still light and the prompt is in the log.
   $ test "$(du -sk $S/solution/web | cut -f1)" -le 2048 && cmp -s ../prompts/02v-visual-pelo-metodo.md $S/process-log/prompts/02v-visual-pelo-metodo.md
4. The screenshots are new.
   $ test -z "$(find $S/process-log/screenshots -name '0[2-9]-*.png' ! -newer ../prompts/02v-visual-pelo-metodo.md)"
5. The branch is still only the folder, by Daniel, the rule frozen, the disk committed (acceptance 1 of prompt 02, unchanged).
The numbers of the text check, before and after, go in `relatorios/02.md`; the orchestrator reads the new screenshots.

## Traps
- Hiding is not deleting. A sentence that honesty requires must still be one hover, focus or tap away, and reachable by keyboard and by a screen reader.
- Hover does not exist on a phone: every explanation that opens on hover also opens on tap.
- Acceptance 3 of prompt 02 still looks for the words "para limpar" in the rendered headline, and the page must still work with the texts file absent.
- No percentage per deal, and nothing that suggests one living deal closes more often than another: a visual with depth must not rank what the data does not rank.
- An image is a file in the pull request: keep it small and give it an ASCII name. No external request when the page loads.
- If shortening needs the AI texts themselves shorter, regenerate through the same check; a text that fails the check does not go on the screen.
