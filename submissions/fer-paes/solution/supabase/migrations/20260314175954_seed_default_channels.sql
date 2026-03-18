/*
  # Seed Default Channels

  1. Summary
     Seeds the three default channels required by the Channel Layer (Subfase 2.6):
     chat, email, and api.

  2. Changes
     - Inserts channel records for 'chat', 'email', and 'api' if they do not already exist
     - All channels are active by default

  3. Notes
     - Uses INSERT ... ON CONFLICT DO NOTHING to be idempotent
     - RLS is already enabled on channels table from prior migration
*/

INSERT INTO channels (name, type, is_active, config)
VALUES
  ('Chat', 'chat', true, '{"description": "Live chat widget"}'),
  ('Email', 'email', true, '{"description": "Email webhook integration"}'),
  ('API', 'api', true, '{"description": "External API integration"}')
ON CONFLICT DO NOTHING;
