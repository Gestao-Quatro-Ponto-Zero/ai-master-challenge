[Trecho: passagens sobre ferramentas e instruções privadas do candidato foram retiradas desta cópia antes da publicação.]

Prompt 02w of Daniel's G4 "AI Master" test (challenge 003, Lead Scorer): the palette and the chart of the window. It continues prompt 02v inside the same box; when it is done you go on with prompt 02 from where you were. Nothing is pushed.

YOUR ROLE: you are still the BUILDER, the lead, in the same chat, with the interface in your own hands.

FIRST: run `date`; copy this prompt, byte for byte, to `process-log/prompts/02w-cor-e-grafico-da-janela.md`.

## Why
The orchestrator looked at your screenshots of 16:59. The text is where it should be: the words visible at load went from 374 to 112 and each deal is one line. Two things are not at Daniel's standard yet. The colour: white, grey, a dark green and a brown could be any dashboard. And the band of the window: a beige gradient with shadows at 30, 60, 90 and 120 days reads as a texture, not as a chart. The window is the one idea of this product; it deserves the best chart on the screen. Daniel wants the depth kept and made to his standard: it must carry the data, not decorate it.

## Goal
1. The palette. Build this product's own palette, anchored in this product, and replace the white, grey, dark green and brown of now. The direction: a cool, light page with white panels; one strong accent for what is alive; a warm colour for attention; a clear negative for what is past the window, to clean or lost; one more hue for the queue; neutral inks for the rest. A colour that carries meaning always comes with its word. The light theme is the default; the dark one stays on its button. Check that the colours can be told apart in both themes, and report the numbers.
2. The window as a chart with depth, in place of the band, made by Daniel's visual method.
   - Thin columns for the ages of the time table (0, 30, 60, 90, 120 and 138 days): of each 100 deals that reached that age open, how many were won afterwards, as known on that Monday. Each column carries its number on top, in ink. One short title names the series and the date of the count; no paragraph, no legend.
   - On the same axis of age, the seller's living deals, one mark each. Hover, focus and tap on a mark show that deal's line. No number is attached to a deal.
   - From 90 days to the end of the window the background takes a tint of attention with the word "esfriando"; past the end of the window, one block in the negative colour with the count to clean.
   - Where the table does not exist on a past Monday, the columns are absent and one line says so; the marks of the deals stay.
   - On a phone the chart becomes horizontal rows, one per age, drawn live, with no sideways scroll.
3. The images are light files with ASCII names, and the diary says only that they were made by o método visual do Daniel.
4. Under the headline, a ruler of at most six numbers, each with a two-word label and its unit: the living deals and their list value, how many are cooling, the queue, the deals to clean and their list value. Numbers, not sentences.
5. The explanation of a deal opens beside its own row and never covers the headline.
6. The text check stays and its target stays. Report its figures again.
7. Screenshots again in both themes, your reviewer who did not draw the screens looks at them, the diary says what changed and why with real times, commit by explicit list. Then prompt 02 continues: Daniel uses the app.

## Acceptance (run from `ai-master-challenge/`; S=submissions/daniel-resende)
1. The page still renders its headline from a clean clone, with the texts file and without it (acceptance 3 of prompt 02, unchanged).
2. The palette is defined for both themes.
3. The interface is still light, this prompt is in the log, and the screenshots are newer than it.
   $ test "$(du -sk $S/solution/web | cut -f1)" -le 2048 && cmp -s ../prompts/02w-cor-e-grafico-da-janela.md $S/process-log/prompts/02w-cor-e-grafico-da-janela.md && test -z "$(find $S/process-log/screenshots -name '0[2-9]-*.png' ! -newer ../prompts/02w-cor-e-grafico-da-janela.md)"
4. The branch is still only the folder, by Daniel, the rule frozen, the disk committed (acceptance 1 of prompt 02, unchanged).
The orchestrator reads the new screenshots.

## Traps
- The columns are history by age for all deals, the same fact the mark "esfriando" already states. They are not a chance per deal: no percentage and no number sits on a deal, and the title says whose count it is.
- The numbers of the columns come from the score file of that Monday, never typed into the page.
- A colour that carries meaning also carries a word or a shape: a seller who does not tell red from green must read the same screen.
- Acceptance 3 of prompt 02 still looks for the words "para limpar" in the rendered headline.
- The rules of prompt 02v stand: one line per deal; the notes of method in their panel.
