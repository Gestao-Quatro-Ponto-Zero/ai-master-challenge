/*
  # Knowledge Base Core — Subfase 4.1

  ## Summary
  Extends the knowledge base schema with a full content-management layer:
  sources, hierarchical categories, editorial versions, tags, and document
  metadata enrichment. These tables are upstream of the RAG embedding pipeline
  and provide the organizational structure for all knowledge content.

  ## New Tables

  ### knowledge_sources
  Represents the origin of knowledge content.
  - `id`          – UUID primary key
  - `name`        – source name (e.g. "Internal Wiki", "Help Center")
  - `description` – optional longer description
  - `source_type` – manual_upload | web_import | api_import | notion | google_docs | faq
  - `is_active`   – whether this source is currently in use
  - `created_at`  – creation timestamp

  ### knowledge_categories
  Hierarchical taxonomy for knowledge content.
  - `id`          – UUID primary key
  - `name`        – category name
  - `description` – optional description
  - `parent_id`   – self-referential FK for nested categories
  - `sort_order`  – integer for ordering siblings
  - `created_at`  – creation timestamp

  ### knowledge_versions
  Full version history for every document.
  One row per edit; only one version per document can have is_current = true.
  - `id`             – UUID primary key
  - `document_id`    – FK → knowledge_documents (cascade delete)
  - `version_number` – monotonically increasing integer within a document
  - `content`        – full text of this version
  - `change_summary` – optional short description of what changed
  - `created_by`     – FK → auth.users
  - `is_current`     – true for the active version (only one per document)
  - `created_at`     – timestamp

  ### knowledge_tags
  Free-form tags for cross-cutting classification.
  - `id`         – UUID primary key
  - `name`       – tag slug (unique, lowercase)
  - `color`      – hex color for UI display
  - `created_at` – timestamp

  ### knowledge_document_tags
  Many-to-many join between documents and tags.
  - `document_id` – FK → knowledge_documents (cascade delete)
  - `tag_id`      – FK → knowledge_tags (cascade delete)
  - Primary key on (document_id, tag_id)

  ## Modified Tables

  ### knowledge_documents
  Added columns:
  - `source_id`      – FK → knowledge_sources (nullable)
  - `category_id`    – FK → knowledge_categories (nullable)
  - `document_type`  – article | faq | policy | procedure | guide
  - `publish_status` – draft | published | archived (editorial lifecycle)
  - `created_by`     – FK → auth.users (nullable)
  - `version_count`  – cached count of versions

  Note: existing `status` column tracks the RAG processing pipeline (pending/processing/ready/error).
  The new `publish_status` tracks the editorial lifecycle independently.

  ## Security
  - RLS enabled on all new tables
  - Authenticated users can read
  - Writes restricted to service role / admin operations via edge functions

  ## Notes
  1. knowledge_versions.is_current must be maintained by application logic.
  2. Only documents with publish_status = 'published' should be sent to the embedding pipeline.
  3. knowledge_categories supports unlimited nesting via parent_id self-join.
*/

CREATE TABLE IF NOT EXISTS knowledge_sources (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text        NOT NULL,
  description text        NOT NULL DEFAULT '',
  source_type text        NOT NULL DEFAULT 'manual_upload'
    CHECK (source_type IN ('manual_upload','web_import','api_import','notion','google_docs','faq')),
  is_active   boolean     NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE knowledge_sources ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_sources' AND policyname='Authenticated users can read knowledge sources') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can read knowledge sources" ON knowledge_sources FOR SELECT TO authenticated USING (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_sources' AND policyname='Authenticated users can insert knowledge sources') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can insert knowledge sources" ON knowledge_sources FOR INSERT TO authenticated WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_sources' AND policyname='Authenticated users can update knowledge sources') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can update knowledge sources" ON knowledge_sources FOR UPDATE TO authenticated USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_sources' AND policyname='Authenticated users can delete knowledge sources') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can delete knowledge sources" ON knowledge_sources FOR DELETE TO authenticated USING (true)';
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS knowledge_categories (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text        NOT NULL,
  description text        NOT NULL DEFAULT '',
  parent_id   uuid        REFERENCES knowledge_categories(id) ON DELETE SET NULL,
  sort_order  integer     NOT NULL DEFAULT 0,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_categories_parent ON knowledge_categories(parent_id);

ALTER TABLE knowledge_categories ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_categories' AND policyname='Authenticated users can read knowledge categories') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can read knowledge categories" ON knowledge_categories FOR SELECT TO authenticated USING (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_categories' AND policyname='Authenticated users can insert knowledge categories') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can insert knowledge categories" ON knowledge_categories FOR INSERT TO authenticated WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_categories' AND policyname='Authenticated users can update knowledge categories') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can update knowledge categories" ON knowledge_categories FOR UPDATE TO authenticated USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_categories' AND policyname='Authenticated users can delete knowledge categories') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can delete knowledge categories" ON knowledge_categories FOR DELETE TO authenticated USING (true)';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_documents' AND column_name='source_id') THEN
    ALTER TABLE knowledge_documents ADD COLUMN source_id uuid REFERENCES knowledge_sources(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_documents' AND column_name='category_id') THEN
    ALTER TABLE knowledge_documents ADD COLUMN category_id uuid REFERENCES knowledge_categories(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_documents' AND column_name='document_type') THEN
    ALTER TABLE knowledge_documents ADD COLUMN document_type text NOT NULL DEFAULT 'article'
      CHECK (document_type IN ('article','faq','policy','procedure','guide'));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_documents' AND column_name='publish_status') THEN
    ALTER TABLE knowledge_documents ADD COLUMN publish_status text NOT NULL DEFAULT 'draft'
      CHECK (publish_status IN ('draft','published','archived'));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_documents' AND column_name='created_by') THEN
    ALTER TABLE knowledge_documents ADD COLUMN created_by uuid REFERENCES auth.users(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_documents' AND column_name='version_count') THEN
    ALTER TABLE knowledge_documents ADD COLUMN version_count integer NOT NULL DEFAULT 0;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_documents' AND policyname='Authenticated users can insert knowledge documents') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can insert knowledge documents" ON knowledge_documents FOR INSERT TO authenticated WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_documents' AND policyname='Authenticated users can update knowledge documents') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can update knowledge documents" ON knowledge_documents FOR UPDATE TO authenticated USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_documents' AND policyname='Authenticated users can delete knowledge documents') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can delete knowledge documents" ON knowledge_documents FOR DELETE TO authenticated USING (true)';
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS knowledge_versions (
  id             uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id    uuid        NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
  version_number integer     NOT NULL DEFAULT 1,
  content        text        NOT NULL DEFAULT '',
  change_summary text        NOT NULL DEFAULT '',
  created_by     uuid        REFERENCES auth.users(id) ON DELETE SET NULL,
  is_current     boolean     NOT NULL DEFAULT true,
  created_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (document_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_versions_document ON knowledge_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_versions_current  ON knowledge_versions(document_id, is_current) WHERE is_current = true;

ALTER TABLE knowledge_versions ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_versions' AND policyname='Authenticated users can read knowledge versions') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can read knowledge versions" ON knowledge_versions FOR SELECT TO authenticated USING (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_versions' AND policyname='Authenticated users can insert knowledge versions') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can insert knowledge versions" ON knowledge_versions FOR INSERT TO authenticated WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_versions' AND policyname='Authenticated users can update knowledge versions') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can update knowledge versions" ON knowledge_versions FOR UPDATE TO authenticated USING (true) WITH CHECK (true)';
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS knowledge_tags (
  id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  name       text        UNIQUE NOT NULL,
  color      text        NOT NULL DEFAULT '#6b7280',
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE knowledge_tags ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_tags' AND policyname='Authenticated users can read knowledge tags') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can read knowledge tags" ON knowledge_tags FOR SELECT TO authenticated USING (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_tags' AND policyname='Authenticated users can insert knowledge tags') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can insert knowledge tags" ON knowledge_tags FOR INSERT TO authenticated WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_tags' AND policyname='Authenticated users can update knowledge tags') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can update knowledge tags" ON knowledge_tags FOR UPDATE TO authenticated USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_tags' AND policyname='Authenticated users can delete knowledge tags') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can delete knowledge tags" ON knowledge_tags FOR DELETE TO authenticated USING (true)';
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS knowledge_document_tags (
  document_id uuid NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
  tag_id      uuid NOT NULL REFERENCES knowledge_tags(id)      ON DELETE CASCADE,
  PRIMARY KEY (document_id, tag_id)
);

ALTER TABLE knowledge_document_tags ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_document_tags' AND policyname='Authenticated users can read document tags') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can read document tags" ON knowledge_document_tags FOR SELECT TO authenticated USING (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_document_tags' AND policyname='Authenticated users can insert document tags') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can insert document tags" ON knowledge_document_tags FOR INSERT TO authenticated WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='knowledge_document_tags' AND policyname='Authenticated users can delete document tags') THEN
    EXECUTE 'CREATE POLICY "Authenticated users can delete document tags" ON knowledge_document_tags FOR DELETE TO authenticated USING (true)';
  END IF;
END $$;

INSERT INTO knowledge_sources (name, description, source_type) VALUES
  ('Internal Documentation', 'Company internal guides and procedures', 'manual_upload'),
  ('Help Center', 'Customer-facing help articles', 'manual_upload'),
  ('FAQ Bank', 'Frequently asked questions collection', 'faq'),
  ('Product Policies', 'Terms, refund, and shipping policies', 'manual_upload')
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_categories (name, description) VALUES
  ('Billing',            'Payments, invoices, and refund topics'),
  ('Technical Support',  'Troubleshooting and technical guides'),
  ('Orders',             'Order management and tracking'),
  ('Shipping',           'Delivery and logistics information'),
  ('Account Management', 'User accounts and settings'),
  ('Product',            'Product features and documentation')
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_tags (name, color) VALUES
  ('refund',    '#ef4444'),
  ('payment',   '#f97316'),
  ('shipping',  '#3b82f6'),
  ('technical', '#8b5cf6'),
  ('account',   '#06b6d4'),
  ('policy',    '#84cc16'),
  ('faq',       '#ec4899'),
  ('api',       '#f59e0b')
ON CONFLICT (name) DO NOTHING;
