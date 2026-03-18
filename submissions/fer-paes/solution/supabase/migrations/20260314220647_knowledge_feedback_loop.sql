/*
  # Knowledge Feedback Loop

  ## Overview
  Implements the data layer for the RAG feedback loop system that tracks how the
  knowledge base is being used and collects quality signals to improve retrieval.

  ## New Tables

  ### 1. knowledge_chunk_usage
  Records which knowledge chunks were retrieved and used during each agent run
  or retrieval request. Enables ranking analysis to identify which chunks are
  most useful in practice.
  - `chunk_id` — reference to the specific chunk that was used
  - `document_id` — denormalized for efficient document-level aggregation
  - `agent_run_id` — the agent execution that triggered the retrieval
  - `ticket_id` — ticket context where the retrieval happened
  - `conversation_id` — conversation context
  - `query_text` — the original query that retrieved this chunk
  - `relevance_score` — the similarity/ranking score assigned at retrieval time

  ### 2. knowledge_feedback
  Stores explicit human feedback on AI responses — from operators reviewing
  agent answers or customers rating their experience.
  - `ticket_id` — ticket the feedback is about
  - `conversation_id` — conversation context
  - `agent_run_id` — optional link to the specific agent execution
  - `agent_id` — the agent that produced the response
  - `rating` — 1–5 numeric score (1=bad, 5=excellent)
  - `feedback_text` — optional free-text comment
  - `feedback_source` — who gave the feedback: operator, customer, admin
  - `created_by` — user who submitted the feedback

  ### 3. knowledge_gaps
  Tracks queries that failed to find relevant knowledge (low similarity scores
  or empty results). High-frequency gaps indicate missing documentation.
  - `query` — the search query with no good matches (unique-indexed)
  - `frequency` — how many times this gap has been observed
  - `last_seen` — when this gap was most recently triggered

  ## Security
  - RLS enabled on all three tables
  - Authenticated users can insert and read records
  - Gaps support upsert via a dedicated database function

  ## Helper Function
  `upsert_knowledge_gap(query_text)` — atomically increments frequency for
  an existing gap or creates a new record if it doesn't exist yet.
*/

-- ─── knowledge_chunk_usage ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS knowledge_chunk_usage (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  chunk_id         uuid        REFERENCES knowledge_chunks(id) ON DELETE SET NULL,
  document_id      uuid        REFERENCES knowledge_documents(id) ON DELETE SET NULL,
  agent_run_id     uuid,
  ticket_id        uuid,
  conversation_id  uuid,
  query_text       text        NOT NULL DEFAULT '',
  relevance_score  float       NOT NULL DEFAULT 0,
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS knowledge_chunk_usage_chunk_id_idx
  ON knowledge_chunk_usage (chunk_id);

CREATE INDEX IF NOT EXISTS knowledge_chunk_usage_document_id_idx
  ON knowledge_chunk_usage (document_id);

CREATE INDEX IF NOT EXISTS knowledge_chunk_usage_ticket_id_idx
  ON knowledge_chunk_usage (ticket_id);

CREATE INDEX IF NOT EXISTS knowledge_chunk_usage_created_at_idx
  ON knowledge_chunk_usage (created_at DESC);

ALTER TABLE knowledge_chunk_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can insert chunk usage"
  ON knowledge_chunk_usage FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can view chunk usage"
  ON knowledge_chunk_usage FOR SELECT
  TO authenticated
  USING (true);

-- ─── knowledge_feedback ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS knowledge_feedback (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id        uuid,
  conversation_id  uuid,
  agent_run_id     uuid,
  agent_id         uuid,
  rating           smallint    NOT NULL DEFAULT 3 CHECK (rating BETWEEN 1 AND 5),
  feedback_text    text        NOT NULL DEFAULT '',
  feedback_source  text        NOT NULL DEFAULT 'operator'
                               CHECK (feedback_source IN ('operator', 'customer', 'admin')),
  created_by       uuid        REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS knowledge_feedback_ticket_id_idx
  ON knowledge_feedback (ticket_id);

CREATE INDEX IF NOT EXISTS knowledge_feedback_rating_idx
  ON knowledge_feedback (rating);

CREATE INDEX IF NOT EXISTS knowledge_feedback_created_at_idx
  ON knowledge_feedback (created_at DESC);

ALTER TABLE knowledge_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can submit feedback"
  ON knowledge_feedback FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = created_by OR created_by IS NULL);

CREATE POLICY "Authenticated users can view all feedback"
  ON knowledge_feedback FOR SELECT
  TO authenticated
  USING (true);

-- ─── knowledge_gaps ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS knowledge_gaps (
  id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  query      text        NOT NULL,
  frequency  integer     NOT NULL DEFAULT 1,
  last_seen  timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT knowledge_gaps_query_key UNIQUE (query)
);

CREATE INDEX IF NOT EXISTS knowledge_gaps_frequency_idx
  ON knowledge_gaps (frequency DESC);

CREATE INDEX IF NOT EXISTS knowledge_gaps_last_seen_idx
  ON knowledge_gaps (last_seen DESC);

ALTER TABLE knowledge_gaps ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can upsert knowledge gaps"
  ON knowledge_gaps FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update knowledge gaps"
  ON knowledge_gaps FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can view knowledge gaps"
  ON knowledge_gaps FOR SELECT
  TO authenticated
  USING (true);

-- ─── upsert_knowledge_gap helper ─────────────────────────────────────────────

CREATE OR REPLACE FUNCTION upsert_knowledge_gap(p_query text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  INSERT INTO knowledge_gaps (query, frequency, last_seen)
  VALUES (p_query, 1, now())
  ON CONFLICT (query)
  DO UPDATE SET
    frequency = knowledge_gaps.frequency + 1,
    last_seen = now();
END;
$$;

-- ─── feedback stats RPC ───────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_feedback_stats()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result json;
BEGIN
  SELECT json_build_object(
    'total',          COUNT(*),
    'avg_rating',     ROUND(AVG(rating)::numeric, 2),
    'positive',       COUNT(*) FILTER (WHERE rating >= 4),
    'neutral',        COUNT(*) FILTER (WHERE rating = 3),
    'negative',       COUNT(*) FILTER (WHERE rating <= 2),
    'total_gaps',     (SELECT COUNT(*) FROM knowledge_gaps),
    'total_chunk_uses', (SELECT COUNT(*) FROM knowledge_chunk_usage)
  )
  INTO result
  FROM knowledge_feedback;

  RETURN COALESCE(result, '{"total":0,"avg_rating":null,"positive":0,"neutral":0,"negative":0,"total_gaps":0,"total_chunk_uses":0}'::json);
END;
$$;
