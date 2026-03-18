/*
  # Add resolution_notes to tickets

  ## Changes
  - New column `resolution_notes` (text, nullable) on the `tickets` table
  - Stores the documented solution applied to resolve the ticket
  - Visible and editable in the ticket detail view for all channel types
  - Particularly prominent for phone-channel tickets where registering the solution is the primary workflow

  ## Security
  - No new RLS policies needed; inherits existing policies on the tickets table
*/

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tickets' AND column_name = 'resolution_notes'
  ) THEN
    ALTER TABLE tickets ADD COLUMN resolution_notes text DEFAULT NULL;
  END IF;
END $$;
