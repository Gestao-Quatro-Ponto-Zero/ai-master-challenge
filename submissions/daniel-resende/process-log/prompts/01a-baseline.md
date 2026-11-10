# 01a: baseline ("an AI alone"), run by the lead builder as a background command

No sub-agent and no instruction text: the only input is the raw text of
`challenges/build-003-lead-scorer/README.md`, sent once on stdin to the strongest
model available on this laptop, in a clean context (no settings, no instruction
files, no tools, no session kept), from an empty directory.

Command (run from an empty directory; `README` is a byte copy of the challenge README):

    claude -p --setting-sources "" --tools "" --no-session-persistence --model fable --output-format json < README > out.json

`--output-format json` only wraps the answer so that the model the CLI actually
resolved can be read from the envelope; the answer text is the `result` field.

What is kept in the submission:
- `process-log/baseline/prompt.md`: what was sent (byte copy of the challenge README).
- `process-log/baseline/resposta.md`: the exact command and the model at the top, then the answer.

Nothing the answer proposes is executed.
