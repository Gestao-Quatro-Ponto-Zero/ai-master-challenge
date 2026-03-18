/*
  # Create Knowledge Vector Search Function — Subfase 3.6

  ## Summary
  Adds the `match_knowledge_chunks` PostgreSQL function used by the
  rag-engine edge function to perform cosine-similarity vector search.

  The function accepts a query embedding vector, a match threshold, and
  a maximum result count, and returns the most semantically similar chunks
  with their parent document information.

  ## New Function

  ### match_knowledge_chunks(query_embedding, match_count, match_threshold)
  Returns:
  - `chunk_id`      – UUID of the matching chunk
  - `document_id`   – UUID of the parent document
  - `chunk_text`    – the chunk text to inject into the prompt
  - `chunk_index`   – position of the chunk in the document
  - `document_title`– title of the source document
  - `document_source`– source reference of the document
  - `similarity`    – cosine similarity score (0–1, higher = more relevant)

  ## Notes
  1. Uses `1 - (embedding <=> query_embedding)` for cosine similarity.
  2. Results are filtered by `match_threshold` and ordered by similarity.
  3. The IVFFlat index improves performance as embeddings table grows.
*/

CREATE OR REPLACE FUNCTION match_knowledge_chunks(
  query_embedding vector(384),
  match_count     int    DEFAULT 5,
  match_threshold float  DEFAULT 0.3
)
RETURNS TABLE (
  chunk_id       uuid,
  document_id    uuid,
  chunk_text     text,
  chunk_index    integer,
  document_title text,
  document_source text,
  similarity     float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    kc.id                                     AS chunk_id,
    kc.document_id,
    kc.chunk_text,
    kc.chunk_index,
    kd.title                                  AS document_title,
    kd.source                                 AS document_source,
    1 - (ke.embedding <=> query_embedding)    AS similarity
  FROM knowledge_embeddings ke
  JOIN knowledge_chunks      kc ON kc.id = ke.chunk_id
  JOIN knowledge_documents   kd ON kd.id = kc.document_id
  WHERE kd.status = 'ready'
    AND 1 - (ke.embedding <=> query_embedding) >= match_threshold
  ORDER BY ke.embedding <=> query_embedding
  LIMIT match_count;
$$;

CREATE OR REPLACE FUNCTION get_knowledge_stats()
RETURNS TABLE (
  total_documents bigint,
  ready_documents bigint,
  total_chunks    bigint,
  total_embeddings bigint
)
LANGUAGE sql STABLE
AS $$
  SELECT
    (SELECT COUNT(*) FROM knowledge_documents)              AS total_documents,
    (SELECT COUNT(*) FROM knowledge_documents WHERE status = 'ready') AS ready_documents,
    (SELECT COUNT(*) FROM knowledge_chunks)                 AS total_chunks,
    (SELECT COUNT(*) FROM knowledge_embeddings)             AS total_embeddings;
$$;
