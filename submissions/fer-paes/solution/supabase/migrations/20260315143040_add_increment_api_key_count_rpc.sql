/*
  # Add RPC to atomically increment API key usage counter

  Creates a simple helper function used by the channel-ingest edge function
  to atomically increment `request_count` and update `last_used_at` on api_keys
  without a race condition.
*/

CREATE OR REPLACE FUNCTION increment_api_key_count(key_id uuid)
RETURNS void
LANGUAGE sql
SECURITY DEFINER
AS $$
  UPDATE api_keys
  SET request_count = request_count + 1,
      last_used_at  = NOW()
  WHERE id = key_id;
$$;
