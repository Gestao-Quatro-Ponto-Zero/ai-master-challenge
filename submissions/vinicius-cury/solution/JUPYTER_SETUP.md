# JUPYTER_SETUP.md — OptiFlow

> Instruction for adding Jupyter notebook as an analysis assistant to the existing OptiFlow project.
> Paste this into Claude Code as an instruction.

---

## PROMPT:

```
Read JUPYTER_SETUP.md. Add Jupyter notebook support as an analysis assistant layer.

## What This Is

The notebooks are YOUR (Claude Code's) analysis scratchpad. The human will NOT code in them. Instead:

1. Human asks a question in plain language (e.g., "what's the distribution of tickets by channel?")
2. You write the notebook cells to answer it
3. You execute the notebook headlessly
4. You read the output and report back to the human
5. Important results get saved to Supabase → the dashboard app picks them up
6. The notebook itself becomes a reasoning log — process evidence for the G4 submission

The human may also ask you to:
- Update a notebook with new analysis
- Re-run with different parameters
- Save specific findings to the database
- Add markdown commentary explaining the reasoning

Notebooks are a SIDE HELPER — not part of the main app build. They exist to answer questions fast and log the analytical reasoning.

## Setup Instructions

1. Install Python analysis dependencies system-wide (no venv needed for Claude Code):
   pip install jupyter papermill nbformat pandas numpy matplotlib seaborn plotly scikit-learn supabase python-dotenv anthropic google-generativeai

2. Add papermill to analysis/requirements.txt (for human's local setup):
   jupyter
   papermill
   nbformat
   pandas
   numpy
   matplotlib
   seaborn
   plotly
   scikit-learn
   supabase
   python-dotenv
   anthropic
   google-generativeai

3. Create analysis/lib/db.py — Supabase connection for notebooks:
   - Reads SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from project root .env.local
   - get_client() → returns supabase client
   - query_to_df(table, filters=None, columns="*", limit=None) → pandas DataFrame
   - save_finding(phase, category, title, description, evidence, impact_hours, impact_cost, priority, recommendation) → writes to process_findings
   - save_classification(table, record_id, category, confidence, model, reasoning) → updates llm_* columns
   - run_query(sql) → raw SQL query via Supabase rpc (for complex joins)

4. Create analysis/lib/classify.py — LLM classification helper:
   - classify_ticket(text, taxonomy, model="haiku") → {category, confidence, reasoning}
   - batch_classify(texts, taxonomy, model, batch_size=10, progress=True) → list of results with progress bar
   - benchmark(texts, true_labels, taxonomy, models=["sonnet","haiku","gemini"]) → comparison DataFrame with accuracy, F1, cost, latency per model
   - Reads ANTHROPIC_API_KEY and GOOGLE_AI_API_KEY from .env.local

5. Create analysis/lib/notebook.py — Notebook creation/execution helper:
   - create_notebook(name, cells) → creates .ipynb file programmatically
   - add_cell(notebook_path, cell_type, content) → appends a cell to existing notebook
   - execute_notebook(notebook_path) → runs via papermill, returns output path
   - read_output(notebook_path, cell_index) → reads output of a specific cell
   - This lets you create and run notebooks entirely from the command line

6. Create analysis/lib/__init__.py (empty)

7. Create analysis/run.sh:
   #!/bin/bash
   # Execute a notebook headlessly and show output
   # Usage: ./analysis/run.sh 01_data_exploration
   NOTEBOOK="analysis/${1}.ipynb"
   OUTPUT="analysis/output/${1}_output.ipynb"
   mkdir -p analysis/output
   papermill "$NOTEBOOK" "$OUTPUT" --log-output
   echo "Output saved to $OUTPUT"

8. Create starter notebooks (these are templates — you'll fill them as the human asks questions):

   analysis/01_data_exploration.ipynb:
   - Cell 1 (code): imports — pandas, numpy, matplotlib, seaborn, sys; sys.path.insert for lib; from lib.db import *
   - Cell 2 (markdown): "# Data Exploration — Support Tickets\nThis notebook explores the raw data to understand what we have before any analysis."
   - Cell 3 (code): # Load data — placeholder: df = query_to_df("support_tickets"); df.shape
   - Cell 4 (markdown): "## Findings\n_To be filled as analysis progresses_"

   analysis/02_process_mapping.ipynb:
   - Cell 1 (code): imports + db connection
   - Cell 2 (markdown): "# Process Mapping\nInferring the as-is support process from data patterns."
   - Cell 3 (code): # placeholder
   - Cell 4 (markdown): "## Process Observations\n_To be filled_"

   analysis/03_classification.ipynb:
   - Cell 1 (code): imports + db + classify helpers
   - Cell 2 (markdown): "# Ticket Classification with LLM\nDesigning taxonomy, benchmarking models, running classification."
   - Cell 3 (code): # placeholder
   - Cell 4 (markdown): "## Classification Results\n_To be filled_"

   analysis/04_bottlenecks.ipynb:
   - Cell 1 (code): imports + db connection
   - Cell 2 (markdown): "# Bottleneck Analysis\nQuantifying time and cost impact of each problem identified."
   - Cell 3 (code): # placeholder
   - Cell 4 (markdown): "## Bottleneck Ranking\n_To be filled_"

9. Create analysis/output/ directory (gitignore output notebooks — they contain execution state)
   Add to .gitignore: analysis/output/

10. Add to CLAUDE.md under Commands Quick Reference:
    # Analysis Notebooks (Claude Code executes these — human does NOT code in them)
    papermill analysis/01_data_exploration.ipynb analysis/output/01_output.ipynb --log-output
    # Or use the helper script:
    ./analysis/run.sh 01_data_exploration

11. Add to CLAUDE.md Architecture Rules section:

    ### Analysis Notebooks (Side Helper)
    - Notebooks in analysis/ are Claude Code's analysis scratchpad
    - Human gives instructions in natural language → Claude Code writes cells, executes, reports back
    - Claude Code creates and executes notebooks headlessly via papermill — no manual Jupyter server needed
    - Results that matter get saved to Supabase via analysis/lib/db.py → the dashboard app displays them
    - Notebooks themselves are reasoning logs — they show the analytical process for G4 evidence
    - Each notebook should have markdown cells explaining WHY each analysis was done, not just code
    - When human asks "what's the X by Y?", the workflow is:
      1. Write the analysis cells in the appropriate notebook
      2. Execute with papermill
      3. Read the output
      4. Report findings to human in plain language
      5. If the finding is significant → save to process_findings table
    - DO NOT put analysis logic in the Next.js app — the app only reads results from Supabase
    - Notebooks can be re-run anytime — they should be idempotent

12. Update BACKLOG.md — add under Phase 0:
    ### P0-D — Analysis Notebook Setup
    - [ ] Python analysis packages installed
    - [ ] DB helper (analysis/lib/db.py) created and working
    - [ ] Classification helper (analysis/lib/classify.py) created
    - [ ] Notebook helper (analysis/lib/notebook.py) created
    - [ ] run.sh execution script created
    - [ ] 4 starter notebooks created (exploration, process, classification, bottlenecks)
    - [ ] Verified: can create, execute, and read notebook output from command line

13. Commit:
    git add -A
    git commit -m "feat: analysis notebook layer — papermill execution, db helpers, classification helpers, starter notebooks"

After completing, update BACKLOG.md and STOP. Wait for human to provide CSV datasets.
```
