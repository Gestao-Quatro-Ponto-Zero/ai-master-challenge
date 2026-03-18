/*
  # Embedding Pipeline Schema — Subfase 4.4

  ## Summary
  Extends the existing knowledge_embeddings table with provider/model tracking
  columns so the embedding pipeline can store metadata about which model produced
  each vector. Adds an embedding_status lifecycle column to knowledge_documents
  for tracking pipeline progress. Creates a proper IVFFlat vector index for
  fast cosine-similarity search.

  ## Modified Tables

  ### knowledge_embeddings
  - `provider` – (new) name of the embedding provider (e.g. "supabase-ai")
  - `model`    – (new) model identifier used to produce the vector (e.g. "gte-small")

  ### knowledge_documents
  - `embedding_status` – (new) lifecycle state of the embedding pipeline:
      unembedded | embedding | embedded | error
      Defaults to 'unembedded' for all existing rows.

  ## New Indexes
  - `idx_embeddings_vector_cosine` – IVFFlat index on knowledge_embeddings.embedding
    using vector_cosine_ops for fast approximate nearest-neighbour search.
  - `idx_knowledge_documents_embedding` – btree index on embedding_status.

  ## Security
  - No new tables; existing RLS policies continue to apply.
  - New columns are covered by the existing authenticated-user SELECT policies.

  ## Notes
  1. Vector dimension stays at 384 to match the built-in gte-small model already
     used by the rag-engine; changing dimension would require a full table rebuild.
  2. provider defaults to 'supabase-ai' and model defaults to 'gte-small' to
     correctly label any legacy rows already in the table.
  3. IVFFlat lists=100 is a sensible default; it can be rebuilt with more lists
     once the table grows beyond ~1 M rows.
*/

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'knowledge_embeddings' AND column_name = 'provider'
  ) THEN
    ALTER TABLE knowledge_embeddings
      ADD COLUMN provider text NOT NULL DEFAULT 'supabase-ai';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'knowledge_embeddings' AND column_name = 'model'
  ) THEN
    ALTER TABLE knowledge_embeddings
      ADD COLUMN model text NOT NULL DEFAULT 'gte-small';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'knowledge_documents' AND column_name = 'embedding_status'
  ) THEN
    ALTER TABLE knowledge_documents
      ADD COLUMN embedding_status text NOT NULL DEFAULT 'unembedded'
      CHECK (embedding_status IN ('unembedded', 'embedding', 'embedded', 'error'));
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_embeddings_vector_cosine
  ON knowledge_embeddings USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_embedding
  ON knowledge_documents(embedding_status);

CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_provider
  ON knowledge_embeddings(provider, model);
