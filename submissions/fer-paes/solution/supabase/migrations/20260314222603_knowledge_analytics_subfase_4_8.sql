/*
  # Knowledge Analytics — Subfase 4.8

  ## Overview
  Implements the analytics layer for the RAG Knowledge Base. Aggregates usage
  data from chunk_usage, feedback, and gap tables into queryable insights that
  power the admin analytics dashboard.

  ## New Table

  ### knowledge_analytics
  Stores pre-computed or event-driven metric snapshots. Allows external processes
  (edge functions, cron jobs) to persist aggregated metrics for historical
  trending without re-scanning large tables.
  - `metric_type`  — category of metric (document_usage, chunk_usage, query_frequency, etc.)
  - `document_id`  — optional link to a knowledge document
  - `chunk_id`     — optional link to a knowledge chunk
  - `value`        — numeric metric value
  - `metadata`     — flexible JSON payload for additional dimensions

  ## New RPC Functions

  ### get_knowledge_overview()
  Returns a single JSON object with top-level knowledge base health metrics:
  total documents, published, chunks, embeddings indexed, queries processed,
  avg feedback rating, and total gaps.

  ### get_document_usage_stats(p_limit)
  Returns the top-N documents ranked by retrieval frequency, joining usage
  counts from knowledge_chunk_usage with document titles from knowledge_documents.

  ### get_chunk_usage_stats(p_limit)
  Returns top-N chunks by retrieval count with average relevance scores.

  ### get_query_analytics(p_limit)
  Groups query_text from knowledge_chunk_usage to surface the most common
  search queries. Excludes empty queries.

  ### get_resolution_impact()
  Derives resolution impact from knowledge_feedback: total feedbacks, avg
  rating, and counts of positive (rating >= 4), neutral (=3), and negative
  (<=2) responses as a proxy for AI-assisted resolution success.

  ## Security
  - RLS enabled on knowledge_analytics
  - All RPC functions use SECURITY DEFINER for safe cross-table reads
*/

-- ─── knowledge_analytics ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS knowledge_analytics (
  id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  metric_type  text        NOT NULL,
  document_id  uuid,
  chunk_id     uuid,
  value        integer     NOT NULL DEFAULT 0,
  metadata     jsonb       NOT NULL DEFAULT '{}',
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS knowledge_analytics_metric_type_idx
  ON knowledge_analytics (metric_type);

CREATE INDEX IF NOT EXISTS knowledge_analytics_document_id_idx
  ON knowledge_analytics (document_id);

CREATE INDEX IF NOT EXISTS knowledge_analytics_created_at_idx
  ON knowledge_analytics (created_at DESC);

ALTER TABLE knowledge_analytics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can insert analytics"
  ON knowledge_analytics FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can view analytics"
  ON knowledge_analytics FOR SELECT
  TO authenticated
  USING (true);

-- ─── get_knowledge_overview ───────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_knowledge_overview()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result json;
  total_docs    bigint;
  published_docs bigint;
  total_chunks  bigint;
  embedded_chunks bigint;
  queries_processed bigint;
  avg_rating    numeric;
  total_gaps    bigint;
BEGIN
  SELECT COUNT(*) INTO total_docs FROM knowledge_documents;
  SELECT COUNT(*) INTO published_docs FROM knowledge_documents WHERE status = 'published';
  SELECT COUNT(*) INTO total_chunks FROM knowledge_chunks;
  SELECT COUNT(*) INTO embedded_chunks FROM knowledge_chunks WHERE embedding IS NOT NULL;
  SELECT COUNT(*) INTO queries_processed FROM knowledge_chunk_usage;
  SELECT ROUND(AVG(rating)::numeric, 2) INTO avg_rating FROM knowledge_feedback;
  SELECT COUNT(*) INTO total_gaps FROM knowledge_gaps;

  SELECT json_build_object(
    'total_documents',    total_docs,
    'published_documents', published_docs,
    'total_chunks',       total_chunks,
    'embedded_chunks',    embedded_chunks,
    'queries_processed',  queries_processed,
    'avg_feedback_rating', avg_rating,
    'total_gaps',         total_gaps
  ) INTO result;

  RETURN result;
END;
$$;

-- ─── get_document_usage_stats ─────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_document_usage_stats(p_limit integer DEFAULT 10)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result json;
BEGIN
  SELECT json_agg(row_order)
  INTO result
  FROM (
    SELECT
      kcu.document_id,
      kd.title                                   AS document_title,
      kd.status                                  AS document_status,
      COUNT(*)                                   AS usage_count,
      ROUND(AVG(kcu.relevance_score)::numeric, 3) AS avg_relevance
    FROM knowledge_chunk_usage kcu
    LEFT JOIN knowledge_documents kd ON kd.id = kcu.document_id
    WHERE kcu.document_id IS NOT NULL
    GROUP BY kcu.document_id, kd.title, kd.status
    ORDER BY usage_count DESC
    LIMIT p_limit
  ) row_order;

  RETURN COALESCE(result, '[]'::json);
END;
$$;

-- ─── get_chunk_usage_stats ────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_chunk_usage_stats(p_limit integer DEFAULT 10)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result json;
BEGIN
  SELECT json_agg(row_order)
  INTO result
  FROM (
    SELECT
      kcu.chunk_id,
      kcu.document_id,
      kd.title                                   AS document_title,
      kc.section_title,
      COUNT(*)                                   AS usage_count,
      ROUND(AVG(kcu.relevance_score)::numeric, 3) AS avg_relevance
    FROM knowledge_chunk_usage kcu
    LEFT JOIN knowledge_documents kd ON kd.id = kcu.document_id
    LEFT JOIN knowledge_chunks kc ON kc.id = kcu.chunk_id
    WHERE kcu.chunk_id IS NOT NULL
    GROUP BY kcu.chunk_id, kcu.document_id, kd.title, kc.section_title
    ORDER BY usage_count DESC
    LIMIT p_limit
  ) row_order;

  RETURN COALESCE(result, '[]'::json);
END;
$$;

-- ─── get_query_analytics ──────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_query_analytics(p_limit integer DEFAULT 15)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result json;
BEGIN
  SELECT json_agg(row_order)
  INTO result
  FROM (
    SELECT
      query_text,
      COUNT(*)                                   AS frequency,
      ROUND(AVG(relevance_score)::numeric, 3)    AS avg_score,
      MAX(created_at)                            AS last_seen
    FROM knowledge_chunk_usage
    WHERE query_text IS NOT NULL AND query_text <> ''
    GROUP BY query_text
    ORDER BY frequency DESC
    LIMIT p_limit
  ) row_order;

  RETURN COALESCE(result, '[]'::json);
END;
$$;

-- ─── get_resolution_impact ────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_resolution_impact()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result json;
BEGIN
  SELECT json_build_object(
    'total_feedbacks',      COUNT(*),
    'avg_rating',           ROUND(AVG(rating)::numeric, 2),
    'ai_resolved',          COUNT(*) FILTER (WHERE rating >= 4),
    'partially_resolved',   COUNT(*) FILTER (WHERE rating = 3),
    'escalated',            COUNT(*) FILTER (WHERE rating <= 2),
    'resolution_rate',      CASE WHEN COUNT(*) = 0 THEN 0
                                 ELSE ROUND((COUNT(*) FILTER (WHERE rating >= 4) * 100.0 / COUNT(*))::numeric, 1)
                            END,
    'by_source',            (
      SELECT json_object_agg(feedback_source, cnt)
      FROM (
        SELECT feedback_source, COUNT(*) AS cnt
        FROM knowledge_feedback
        GROUP BY feedback_source
      ) src
    )
  )
  INTO result
  FROM knowledge_feedback;

  RETURN COALESCE(result,
    '{"total_feedbacks":0,"avg_rating":null,"ai_resolved":0,"partially_resolved":0,"escalated":0,"resolution_rate":0,"by_source":{}}'::json
  );
END;
$$;
