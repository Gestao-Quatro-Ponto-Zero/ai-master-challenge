/*
  # Add description to tickets + conversation initialization support

  ## Summary
  This migration adds a `description` text column to the `tickets` table
  to store the original message body (e.g. from email/CSV import). It also
  adds a helper function to create the initial conversation + customer message
  for tickets imported via CSV that already have a description.

  ## Changes

  ### tickets table
  - Add `description` (text, nullable): stores the original ticket body/message text
    as provided by the customer at ticket creation time (e.g. email body, CSV description)

  ## Notes
  - Existing tickets are unaffected (description defaults to NULL)
  - The CSV import will populate this field going forward
  - The UI uses this to show the original message in the email thread view
*/

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tickets' AND column_name = 'description'
  ) THEN
    ALTER TABLE tickets ADD COLUMN description text;
  END IF;
END $$;
