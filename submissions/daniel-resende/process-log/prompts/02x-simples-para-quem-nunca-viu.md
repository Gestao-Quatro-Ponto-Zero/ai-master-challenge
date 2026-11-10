[Trecho: passagens sobre ferramentas e instruções privadas do candidato foram retiradas desta cópia antes da publicação.]

Prompt 02x of Daniel's G4 "AI Master" test (challenge 003, Lead Scorer): make the pictures simple enough for someone who has never seen them. It follows prompt 02w; when it is done you go on with prompt 02 from where you were. Nothing is pushed.

YOUR ROLE: you are still the BUILDER, the lead, in the same chat, with the interface in your own hands.

FIRST: run `date` and keep it as the real start; time box 25 minutes; copy this prompt, byte for byte, to `process-log/prompts/02x-simples-para-quem-nunca-viu.md`.

## Why
Daniel looked at your screenshots of 17:11 and his judgment is plain: the charts are complex. His bar is this: a fifteen-year-old who has never seen the tool looks at a picture and understands all of it, because the picture carries the information by itself, clean and light. Neither the seller's chart nor the manager's bars pass it.
The fault is in what was asked, not in how you drew it. Prompt 02w asked you to chart the time table (of each 100 deals open at an age, how many were won afterwards). That is a statistic, and no drawing makes a statistic obvious in ten seconds. So this prompt changes what the pictures show.
What the orchestrator saw on the screens, for the record: a rate and a count on one stage (the columns and the red block of 91), which invites a comparison that means nothing; the seller's deals floating apart from the columns; extruded columns that read as a spreadsheet's 3D chart; green, amber and red over four background tints; and, on the manager's screen, two bars per seller where a wall of red stripes shouts over everything else.

## Goal
1. The test for every picture: a fifteen-year-old, with no explanation, says in one sentence what it shows and what to do. Run that test for real (item 9) and keep only what passes.
2. The seller's picture becomes one line of time: the window. On the left a deal that has just opened, on the right the end of the window. One mark for each living deal, at its age. Near the end, one zone with its word, "esfriando". After the end, no bar and no block: one line of text, "fora da janela: N para limpar", that takes the seller to that block. No vertical axis, no rate, no column. At most three numbers on the line: where it starts, where "esfriando" starts, where it ends.
3. The time table (how many of each 100 were won at each age) leaves the first view. It stays where it already is: in "Como a ferramenta decide" and in the explanation of a deal.
4. In the list of living deals, each row gets one small bar of the time it has left, in the same colours as the line. The number of days stays beside it.
5. The ruler keeps only what the headline does not already say: the value of the living deals, how many are cooling now, the value that is parked. Three numbers, two words of label each, the unit once.
6. The manager's screen, same bar. One bar per seller, all of the same length: the part of that seller's open value that is still alive, in the colour of the living, and the rest quiet. No stripes, and no large area in the negative colour. The three counts stay as numbers. Sellers with no living deal come first, and the screen says that this is the order.
7. Colour in small doses. Large areas stay quiet; the colour of what is alive, of the alert and of what is out appears on marks, words and thin bars, never as a filled block. The colour of what is alive is Daniel's to name: if he has not named it in this chat, ask him once, in one line, and go on with the rest while you wait.
8. The depth stays and serves the reading: light, a soft shadow and the ground give the line of time a body. Nothing in perspective, nothing extruded.
9. The fifteen-year-old test, done by a fresh reviewer who receives one screenshot at a time and nothing else: "You are fifteen and have never seen this. In two sentences, what does this picture tell you, and what would you do? List every word or mark you do not understand." Save the prompt you give it; fix what it does not understand; run it again on the result.
10. Defects seen in the screenshots: the manager's hover box ends with the word "null"; in the light theme a dark fade covers the last row of the list of living deals.
11. Add to `docs/pesquisa.md`, under a new heading, the four sources below and what each one supports here, and say what had no source: none of them was found to approve decorative depth by name; keeping depth as light and shadow that carry no number is our inference from them.
12. The text check stays. Screenshots again in both themes; the diary says what changed and why, with real times; commit by explicit list. Then prompt 02 continues: Daniel uses the app.

## Sources (read by the orchestrator's research on 2026-11-10)
- Heer and Bostock, "Crowdsourcing Graphical Perception", CHI 2010, https://homes.cs.washington.edu/~jheer/files/2010-MTurk-CHI.pdf : position on a common scale is read more accurately than length, area or angle.
- Wilke, "Fundamentals of Data Visualization", chapter 26, "Don't go 3D", https://clauswilke.com/dataviz/no-3d.html : projecting 3D objects into two dimensions distorts the data; 3D bars look shorter than they are.
- Few, "Dual-Scaled Axes in Graphs", Perceptual Edge, 2008, https://www.perceptualedge.com/articles/visual_business_intelligence/dual-scaled_axes.pdf : more than one quantitative scale on one axis invites comparisons of magnitude that mean nothing.
- Laubheimer, Nielsen Norman Group, "Dashboards: Making Charts and Graphs Easier to Understand", 2017, https://www.nngroup.com/articles/dashboards-preattentive/ : position and length for quantities, colour to highlight, no 3D, read fast with a minimum of interaction.

## Acceptance (run from `ai-master-challenge/`; S=submissions/daniel-resende)
1. The page still renders its headline from a clean clone, with the texts file and without it (acceptance 3 of prompt 02, unchanged).
2. The sources are in the research file, this prompt is in the log, and the screenshots are newer than it.
   $ P=$S/docs/pesquisa.md && grep -q 'Heer' $P && grep -q 'Wilke' $P && grep -q 'Dual-Scaled' $P && grep -q 'nngroup' $P && cmp -s ../prompts/02x-simples-para-quem-nunca-viu.md $S/process-log/prompts/02x-simples-para-quem-nunca-viu.md && test -z "$(find $S/process-log/screenshots -name '0[2-9]-*.png' ! -newer ../prompts/02x-simples-para-quem-nunca-viu.md)"
3. The interface is still light.
   $ test "$(du -sk $S/solution/web | cut -f1)" -le 2048
4. The branch is still only the folder, by Daniel, the rule frozen, the disk committed (acceptance 1 of prompt 02, unchanged).
The orchestrator reads the new screenshots, reads what your fifteen-year-old reviewer answered, and looks for the word "null" on the rendered manager's screen.

## Traps
- Simple is not empty. The line of time must still let the seller tell which deals have time and which are running out; the honesty of the tool stays one gesture away, as prompt 02v set.
- A mark is a deal, never a chance: no number and no percentage sits on a mark.
- A colour that carries meaning also carries a word or a shape.
- From now on the diary, the report and the commit messages record results: what changed, why, the numbers and the screenshots.
- The rules of prompts 02v and 02w stand, except where this prompt changes what the pictures show: one line per deal; the notes of method in their panel.
- Acceptance 3 of prompt 02 still looks for the words "para limpar" in the rendered headline.
