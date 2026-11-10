# 02b2: AI layer, the lead's answer after reading the five texts

I read the five. They are grounded, and they are not yet good enough for a seller: the plural is typed by the model ("1 negócios vivos" would happen), zeros read badly ("Sua fila está em 0"), and the next step says nothing ("Jogada da semana: {play_label}."). Fix these, then generate all without stopping again. Time box: 15 minutes from now; if the run is throttled or passes 10 minutes, stop and keep what passed the check.

## Changes
1. Counted phrases are built by code, never by the model. `facts.py` adds phrase-valued facts with the right singular, plural and zero form, and the prompt tells the model to use them instead of a bare count next to a noun:
   - `alive_phrase`: "nenhum negócio vivo" / "1 negócio vivo" / "5 negócios vivos"
   - `queue_phrase`: "nenhum negócio na fila" / "1 negócio na fila" / "55 negócios na fila"
   - `clean_phrase`: "nada para limpar" / "1 negócio para limpar" / "52 negócios para limpar"
   - `cooling_phrase` (only when cooling > 0): "1 esfriando" / "4 esfriando"
   - `days_left_phrase` (deal, and `days_left_phrase_1..3` in the briefing): "é o último dia na janela" / "falta 1 dia na janela" / "faltam 89 dias na janela"
   - `days_open_phrase`: "aberto há 1 dia" / "aberto há 21 dias"
   - `evidence_phrase`: built from the index evidence, for example "nenhum dos 717 negócios distintos que saíram da janela foi ganho"
   - manager: `without_alive_phrase`: "nenhum vendedor sem negócio vivo" / "1 de 6 vendedores sem nenhum negócio vivo" / "2 de 6 vendedores sem nenhum negócio vivo"
   Keep the plain numeric keys as facts too (the check compares them with the score), but the prompt forbids putting a bare count placeholder directly before a noun the model would have to inflect.
2. The time-table sentence comes whole from the score: add the fact `time_sentence` (the deal's `time_sentence`, which already carries "Cerca de" and the date of the count) and drop `band_days`, `band_won_per_100` and `counted_on` from the deal facts. The model places `{time_sentence}` as its own sentence, unchanged, or leaves it out; it never rewrites it. Remove the special case for "em cada cem" from the check.
3. `next_step` must say the step AND the fact of this deal that leads to it, in one sentence, for example for a cooling deal: the step (`{play_label}`), because it passed 90 days open and `{days_left_phrase}`. For a non-cooling deal: the step, with its value and `{days_left_phrase}`. Never a reason that is not a fact given.
4. `play_label` in the facts is the sentence-case label without the final period ("Trabalhar esta semana", "Confirmar esta semana se segue de pé").
5. Briefing: three to five sentences in this order: the three counts by their phrases; where to start (the first living deals when they exist; "comece pela fila" when there is no living deal and the queue exists; when there is nothing alive and no queue, say the Monday is for cleaning and opening new deals); the clean block with `{evidence_phrase}` and the action (encerrar no CRM). A seller with no living deal has no `product_1`: the prompt must say what to write then.
6. Manager: only facts, no advice about people, no comparison of sellers' performance.
7. Update `docs/contrato-ia.md`? No: I update the contract myself. Tell me the final list of keys per kind in your report.

## Then
Regenerate from zero (the prompt hash changed), all targets, never more than two calls at once. In your final message (under 200 words): the five targets of before re-rendered, counts stored per kind, refused and why, seconds, model names, exit codes of the test and of `python check.py`, and the final list of fact keys per kind.
