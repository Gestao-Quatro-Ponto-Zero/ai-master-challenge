/*
  # Fix CSV Import: Add Missing Unique Constraints

  ## Problem
  The CSV import was silently failing because PostgREST requires true UNIQUE
  constraints (not plain indexes) to resolve `.upsert({ onConflict: '...' })` calls.
  Two columns were missing proper unique constraints:

  1. `customers.email` — had only a plain index, not a unique constraint.
     The upsert with `onConflict: 'email'` was rejected by PostgREST, causing
     all customer rows (and consequently all ticket rows) to fail silently.

  2. `tickets.external_id` — had a partial unique index (`WHERE external_id IS NOT NULL`).
     PostgREST cannot use conditional/partial indexes as conflict targets.

  ## Changes

  ### customers table
  - Drop the plain `idx_customers_email` index
  - Add a UNIQUE constraint on `email` (allows NULLs, enforces uniqueness among non-NULL values)

  ### tickets table
  - Drop the partial unique index `tickets_external_id_key`
  - Add a full UNIQUE constraint on `external_id`
*/

-- ─── customers.email ─────────────────────────────────────────────────────────

DROP INDEX IF EXISTS idx_customers_email;

ALTER TABLE customers
  ADD CONSTRAINT customers_email_unique UNIQUE (email);

-- ─── tickets.external_id ─────────────────────────────────────────────────────

DROP INDEX IF EXISTS tickets_external_id_key;

ALTER TABLE tickets
  ADD CONSTRAINT tickets_external_id_unique UNIQUE (external_id);
