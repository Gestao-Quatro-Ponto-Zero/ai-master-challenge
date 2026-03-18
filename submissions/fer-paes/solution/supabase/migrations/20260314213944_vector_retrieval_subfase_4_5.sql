/*
  # Vector Index & Retrieval — Subfase 4.5

  ## Summary
  Adds the database layer needed by the retrieval pipeline: a full-text keyword
  search function, a retrieval_logs table for analytics, and a GIN index on
  knowledge_chunks.chunk_text to accelerate full-text queries.

  ## New Tables

  ### retrieval_logs
  Tracks every knowledge retrieval call for analytics and debugging.
  - `id`           – UUID primary key
  - `query`        – the raw search query
  - `strategy`     – semantic | keyword | hybrid
  - `result_count` – number of chunks returned
  - `top_score`    – highest relevance score in the result set
  - `latency_ms`   – round-trip duration in milliseconds
  - `agent_id`     – optional FK to agent that triggered the retrieval
  - `created_at`   – timestamp

  ## New Functions

  ### search_keyword_chunks(query_text, match_count, min_rank)
  Full-text search over knowledge_chunks using PostgreSQL tsvector/tsquery.
  Returns ranked results with a normalized rank score (0–1).

  ### get_retrieval_stats()
  Aggregated statistics for the retrieval pipeline dashboard.

  ## New Indexes

  - `idx_chunks_fts` – GIN index on to_tsvector('english', chunk_text) for
    fast full-text search.

  ## Security
  - RLS enabled on retrieval_logs
  - Authenticated users can read/insert their own log rows
  - SQL functions are STABLE / SECURITY DEFINER where needed

  ## Notes
  1. search_keyword_chunks uses plainto_tsquery (safe against injection).
  2. ts_rank_cd normalises by document length, giving a 0–1 comparable score.
  3. Hybrid reranking (0.7 × semantic + 0.3 × keyword) is handled in the
     edge function, not in SQL, to keep the DB functions composable.
*/

CREATE INDEX IF NOT EXISTS idx_chunks_fts
  ON knowledge_chunks USING GIN (to_tsvector('english', chunk_text));

CREATE TABLE IF NOT EXISTS retrieval_logs (
  id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  query        text        NOT NULL,
  strategy     text        NOT NULL DEFAULT 'semantic'
    CHECK (strategy IN ('semantic', 'keyword', 'hybrid')),
  result_count integer     NOT NULL DEFAULT 0,
  top_score    float       NOT NULL DEFAULT 0,
  latency_ms   integer     NOT NULL DEFAULT 0,
  agent_id     uuid        REFERENCES agents(id) ON DELETE SET NULL,
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_retrieval_logs_created  ON retrieval_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_retrieval_logs_strategy ON retrieval_logs(strategy);
CREATE INDEX IF NOT EXISTS idx_retrieval_logs_agent    ON retrieval_logs(agent_id);

ALTER TABLE retrieval_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can insert retrieval logs"
  ON retrieval_logs FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can read retrieval logs"
  ON retrieval_logs FOR SELECT
  TO authenticated
  USING (true);

CREATE OR REPLACE FUNCTION search_keyword_chunks(
  query_text  text,
  match_count int   DEFAULT 5,
  min_rank    float DEFAULT 0.01
)
RETURNS TABLE (
  chunk_id        uuid,
  document_id     uuid,
  chunk_text      text,
  chunk_index     integer,
  section_title   text,
  document_title  text,
  document_source text,
  keyword_score   float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    kc.id                                                              AS chunk_id,
    kc.document_id,
    kc.chunk_text,
    kc.chunk_index,
    COALESCE(kc.section_title, '')                                    AS section_title,
    kd.title                                                          AS document_title,
    kd.source                                                         AS document_source,
    ts_rank_cd(
      to_tsvector('english', kc.chunk_text),
      plainto_tsquery('english', query_text)
    )::float                                                          AS keyword_score
  FROM knowledge_chunks kc
  JOIN knowledge_documents kd ON kd.id = kc.document_id
  WHERE kd.status = 'ready'
    AND to_tsvector('english', kc.chunk_text) @@ plainto_tsquery('english', query_text)
    AND ts_rank_cd(
          to_tsvector('english', kc.chunk_text),
          plainto_tsquery('english', query_text)
        ) >= min_rank
  ORDER BY keyword_score DESC
  LIMIT match_count;
$$;

CREATE OR REPLACE FUNCTION get_retrieval_stats()
RETURNS TABLE (
  total_searches    bigint,
  semantic_searches bigint,
  keyword_searches  bigint,
  hybrid_searches   bigint,
  avg_result_count  float,
  avg_latency_ms    float,
  avg_top_score     float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    COUNT(*)                                                  AS total_searches,
    COUNT(*) FILTER (WHERE strategy = 'semantic')            AS semantic_searches,
    COUNT(*) FILTER (WHERE strategy = 'keyword')             AS keyword_searches,
    COUNT(*) FILTER (WHERE strategy = 'hybrid')              AS hybrid_searches,
    ROUND(AVG(result_count)::numeric, 2)::float              AS avg_result_count,
    ROUND(AVG(latency_ms)::numeric, 1)::float                AS avg_latency_ms,
    ROUND(AVG(top_score)::numeric, 4)::float                 AS avg_top_score
  FROM retrieval_logs;
$$;
