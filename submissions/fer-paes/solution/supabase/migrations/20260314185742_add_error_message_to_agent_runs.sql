/*
  # Add error_message column to agent_runs

  ## Summary
  Adds the error_message column to agent_runs so the Agent Executor can store
  failure details when a run transitions to the 'failed' status.

  ## Changes
  - `agent_runs.error_message` (text, nullable) — human-readable error detail
    recorded when status = 'failed'
*/

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'agent_runs' AND column_name = 'error_message'
  ) THEN
    ALTER TABLE agent_runs ADD COLUMN error_message text DEFAULT NULL;
  END IF;
END $$;
