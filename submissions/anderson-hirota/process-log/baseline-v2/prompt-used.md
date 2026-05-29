# v2 self-critique prompt

Second iteration. Fed Claude its own v1 output and asked for honest
self-critique + improved version. Still no human domain expertise leaked
in — purely "AI iterating on its own work".

What is NOT in this prompt:
- Findings from running v1 on real data (clustering, sector NaN %, historical timestamps)
- "Próxima ação", coaching, composability with Morning-Brief
- Anything from Anderson's case-g4-ai-master.md
- Specific feature suggestions

What IS in this prompt:
- The original brief
- The v1 code (app.py + scoring.py + README.md)
- Instructions to critique its own work and ship a better version

## Prompt

````text
I built a Streamlit lead scorer for a coding challenge. Before I ship it, I
want you to honestly critique what you produced and write an improved
version.

Critique rules:
- Read the code as if a senior engineer / RevOps lead were reviewing it
- Find at least 5 substantive weaknesses (logic bugs, design flaws,
  weak features, missing edge cases, poor UX, etc.)
- Do not invent context I haven't given you. Only critique what's in the
  code and the brief.

Then ship v2 — full files, runnable, addressing your critique.

Output structure:
1. Critique (numbered list, terse)
2. v2 files in fenced code blocks labeled with filename, in this order:
   app.py, scoring.py, requirements.txt, README.md

---

# BRIEF
[full brief pasted]

---

# v1 CODE I WROTE
[full app.py + scoring.py + README.md pasted]
````
