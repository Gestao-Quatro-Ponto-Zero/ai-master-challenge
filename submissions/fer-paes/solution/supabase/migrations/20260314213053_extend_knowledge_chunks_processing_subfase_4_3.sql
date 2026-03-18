/*
  # Extend Knowledge Chunks & Add Processing Status — Subfase 4.3

  ## Summary
  Extends the existing knowledge_chunks table with structural metadata fields
  needed by the Document Processing & Chunking pipeline. Also adds a processing
  status column to knowledge_documents for lifecycle tracking.

  ## Modified Tables

  ### knowledge_chunks
  - `version_id`     – (new) FK → knowledge_versions(id), links chunk to the
                       specific document version it was produced from
  - `token_count`    – (new) estimated token count for the chunk (int)
  - `section_title`  – (new) heading of the section the chunk belongs to
  - `metadata`       – (new) JSONB bag of keywords, document_title, strategy, etc.

  ### knowledge_documents
  - `processing_status` – (new) lifecycle state of the document processing
                          pipeline: unprocessed | processing | processed | error

  ## Security
  - No new tables → existing RLS policies on knowledge_chunks and
    knowledge_documents continue to apply.
  - New columns are readable by authenticated users through the existing
    SELECT policies.

  ## Notes
  1. `version_id` is nullable so legacy chunks created before this migration
     are not invalidated.
  2. `token_count` defaults to 0 and is filled in by the edge function.
  3. `processing_status` defaults to 'unprocessed' for all existing documents.
*/

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'knowledge_chunks' AND column_name = 'version_id'
  ) THEN
    ALTER TABLE knowledge_chunks ADD COLUMN version_id uuid REFERENCES knowledge_versions(id) ON DELETE SET NULL;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'knowledge_chunks' AND column_name = 'token_count'
  ) THEN
    ALTER TABLE knowledge_chunks ADD COLUMN token_count integer NOT NULL DEFAULT 0;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'knowledge_chunks' AND column_name = 'section_title'
  ) THEN
    ALTER TABLE knowledge_chunks ADD COLUMN section_title text NOT NULL DEFAULT '';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'knowledge_chunks' AND column_name = 'metadata'
  ) THEN
    ALTER TABLE knowledge_chunks ADD COLUMN metadata jsonb NOT NULL DEFAULT '{}';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'knowledge_documents' AND column_name = 'processing_status'
  ) THEN
    ALTER TABLE knowledge_documents
      ADD COLUMN processing_status text NOT NULL DEFAULT 'unprocessed'
      CHECK (processing_status IN ('unprocessed', 'processing', 'processed', 'error'));
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_version
  ON knowledge_chunks(version_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_processing
  ON knowledge_documents(processing_status);
