# 02b3: AI layer, finishing round asked by the lead

The 148 texts pass the check and three wording flaws are visible on the screen. Fix them and regenerate once. Time box: 8 minutes; if throttled, stop and keep the 148 that exist (restore them if you had to discard them: do not leave the file empty).

1. Sentence case. A phrase placeholder that starts a sentence renders with a capital: I saw "aberto há 69 dias. faltam 69 dias na janela". Make the renderer capitalise the first letter of the filled text at the start of a part and after ". ", "! " or "? " (only when that letter came from a placeholder or is lower-case), and make the check compare with the same renderer.
2. Phrases never follow a verb. "você tem nenhum negócio vivo" is wrong Portuguese. The prompt must tell the model to give the three counts as a list after a colon, never after "tem" or "você tem", for example: "Sua segunda: {alive_phrase}, {queue_phrase} e {clean_phrase}." and for the manager: "Time: {alive_phrase}, {queue_phrase} e {clean_phrase}."
3. No label that repeats the phrase. "para limpar: 195 negócios para limpar" repeats itself; the phrases already carry their own noun.
4. Add to the check a refusal for the exact patterns "tem nenhum" and for the same three-word sequence appearing twice within one sentence, with a test for each.

Keep everything else. Final message under 120 words: counts stored per kind, refused, seconds, exit codes of the test and of `python check.py`, and the briefing of Anna Snelling and the text of manager Cara Losch as rendered.
