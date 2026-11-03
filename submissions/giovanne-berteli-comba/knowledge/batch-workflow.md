---
type: Implementation Contract
title: Batch work and local manual-assisted rehearsal
description: M07 import, explicit review, immutable output, timing boundaries and pending human experiment.
status: draft
sources:
  - id: protocol
    resource: ../data/workflow-protocol.json
  - id: implementation
    resource: ../solution/batch_workflow.py
  - id: interface
    resource: ../solution/batch_ui.py
  - id: reviewer-learning
    resource: ../docs/operational-learning.md
---

# Scope and authority

The user challenged the connection between classification and operating benefit,
then explicitly requested batch triage, a manual/assisted comparison and prominent
reviewer-facing learning. M07 implements these tools. H01 is the actual declared
operator rehearsal and remains pending until a person completes it. No automated
attempt may be represented as human work or realized operational savings.

# Inputs and durable state

`batch_workflow` uses a separate ignored SQLite at `data/runtime/workflow.sqlite3`
(override `TRIAGE_WORKFLOW_DB_PATH`). It adds wf_batches/events/studies tables and
reuses the unchanged Repository/TriageService for predictions in that database.
The single-ticket app/database and all frozen model, rule and evaluation sources
remain untouched. CSVs accept ticket_id,text and optional reference_category;
1–50 rows, UTF-8, up to 2 MB and 10,000 characters/text, unique IDs within a batch.
References and supplied labels never enter model features or the decision editor.
IT English context is declared by the operator, not automatically detected.

Batch start precedes upload. Content freezes on first valid import. Stable request
IDs and persisted prediction links allow explicit interrupted preparation to
resume without duplicate saved runs. Failed outcomes are retained, not silently
retried; a reviewer can supply the final class after the attempt. Duplicate action
tokens acknowledge the same decisions, conflicting or stale versions fail.
All rows need explicit confirmation; none is prechecked. Review changes append
events rather than change the model prediction. Finalization creates a stable CSV
and freezes the batch; an interruption retains its reason and attempt.

# Measurement and study protocol

Elapsed server UTC time covers start/opening the assigned batch through artifact
preparation, including waiting, pauses, input handling, review and corrections.
It excludes external CSV preparation, study setup, actual download and downstream
delivery; it is not active labor. Clock rollback is rejected. Timer boundaries and
actor type are exported, and normalized seconds/case include batch overhead.

The versioned protocol is loaded and hashed before the study. Each arm has eight
TRAIN tasks, one per supplied class. Similarity groups are unique across all 16;
paired text length and deterministic hashes choose/assign tasks without predictions.
Task order is hashed, not class-ordered, and arm order counterbalances by study ID.
Source/membership hashes and case/group manifest are saved. Labels are hidden until
both outputs are ready; manual mode cannot prepare predictions. Every actor is
operator_declared or automated_test; identity is not authenticated.

Report all completed/interrupted/prepared attempts by actor type. Descriptive time
differences, supplied-label concordance, suggestion corrections and failures remain
visible, including negative time differences and lower assisted concordance.
No automatic outlier removal, financial annualization or independent predictive
quality claim. Small balanced training samples, participant/order/learning effects
and uncertain label provenance limit interpretation. New representative operational
data and a real team pilot remain future work.

# Presentation

Full Company mode adds a batch-work tab while keeping recruitment details hidden.
Instructor adds the experiment; aggregate-only mode shows learning/instructions
without opening raw data or initializing a workflow database. The prominent
learning is owned by docs/operational-learning.md and summarized at the README,
start-here and instructor guide. The capacity simulator retains its original
unmeasured customer-domain scenarios; trial times are not inserted into it.
