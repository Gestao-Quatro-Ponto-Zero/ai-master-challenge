# Naive baseline prompt

Single-shot prompt fed to `claude -p` (sonnet, default). The brief from
`challenges/build-003-lead-scorer/README.md` is pasted verbatim. No iteration,
no follow-up, no reference to Anderson's experience, his strategic case, or
the Morning-Brief prototype. Output saved exactly as Claude produced it.

## Prompt

````text
You are helping me complete a coding challenge for a hiring process. Read the
brief below and build a Streamlit application that solves it. Use Python.

The 4 CSV files (accounts.csv, products.csv, sales_teams.csv,
sales_pipeline.csv) will be placed in a `data/` folder next to the app.

Deliver, in this order, complete and runnable:

1. `app.py` — the Streamlit application with scoring, filters
   (sales rep / manager / region / stage), and an explainability panel
2. `scoring.py` — the scoring logic, separated for clarity
3. `requirements.txt`
4. `README.md` — setup, how to run, scoring logic explained, limitations

Make reasonable choices. Don't ask me questions. Be competent.

---

# BRIEF

[full content of challenges/build-003-lead-scorer/README.md pasted here]
````
