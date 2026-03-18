/*
  # Add CSV Import Fields

  Extends the `customers` and `tickets` tables with additional columns
  needed for importing ticket data from CSV files.

  ## Changes

  ### customers table
  - `age` (integer, nullable) — Customer age from CSV
  - `gender` (text, nullable) — Customer gender from CSV

  ### tickets table
  - `external_id` (text, unique, nullable) — Original Ticket ID from the source CSV, used to prevent duplicate imports
  - `ticket_type` (text, nullable) — Type of ticket (e.g., Billing, Technical, General)
  - `product_purchased` (text, nullable) — Product/service associated with the ticket
  - `date_of_purchase` (timestamptz, nullable) — Date the product was purchased
  - `first_response_time_minutes` (integer, nullable) — Time until first operator response, in minutes
  - `time_to_resolution_minutes` (integer, nullable) — Total time to resolve the ticket, in minutes
  - `customer_satisfaction_rating` (smallint, nullable) — Customer satisfaction score (1–5)
  - `resolution_text` (text, nullable) — Resolution description text from the CSV

  ## Notes
  - All new columns are nullable to preserve existing records
  - `external_id` has a unique index to make reimports idempotent
  - No RLS changes needed as these are column additions to existing secured tables
*/

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'customers' AND column_name = 'age'
  ) THEN
    ALTER TABLE customers ADD COLUMN age integer;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'customers' AND column_name = 'gender'
  ) THEN
    ALTER TABLE customers ADD COLUMN gender text;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tickets' AND column_name = 'external_id'
  ) THEN
    ALTER TABLE tickets ADD COLUMN external_id text;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE tablename = 'tickets' AND indexname = 'tickets_external_id_key'
  ) THEN
    CREATE UNIQUE INDEX tickets_external_id_key ON tickets (external_id) WHERE external_id IS NOT NULL;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tickets' AND column_name = 'ticket_type'
  ) THEN
    ALTER TABLE tickets ADD COLUMN ticket_type text;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tickets' AND column_name = 'product_purchased'
  ) THEN
    ALTER TABLE tickets ADD COLUMN product_purchased text;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tickets' AND column_name = 'date_of_purchase'
  ) THEN
    ALTER TABLE tickets ADD COLUMN date_of_purchase timestamptz;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tickets' AND column_name = 'first_response_time_minutes'
  ) THEN
    ALTER TABLE tickets ADD COLUMN first_response_time_minutes integer;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tickets' AND column_name = 'time_to_resolution_minutes'
  ) THEN
    ALTER TABLE tickets ADD COLUMN time_to_resolution_minutes integer;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tickets' AND column_name = 'customer_satisfaction_rating'
  ) THEN
    ALTER TABLE tickets ADD COLUMN customer_satisfaction_rating smallint;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tickets' AND column_name = 'resolution_text'
  ) THEN
    ALTER TABLE tickets ADD COLUMN resolution_text text;
  END IF;
END $$;
