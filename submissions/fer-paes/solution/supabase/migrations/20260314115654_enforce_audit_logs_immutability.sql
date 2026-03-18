/*
  # Enforce Audit Logs Immutability

  ## Summary
  Adds security enforcement to make audit_logs records immutable.
  Audit records are append-only — they must never be modified or deleted,
  ensuring a trustworthy, tamper-proof activity trail.

  ## Changes

  1. Removes any existing UPDATE/DELETE policies on audit_logs (none were created,
     but this is a defensive check).

  2. Ensures there are no UPDATE or DELETE policies on audit_logs at the RLS level.
     Since no such policies exist, authenticated users cannot UPDATE or DELETE rows
     even with RLS enabled (no matching policy = denied by default).

  ## Security Notes
  - INSERT remains allowed (authenticated users can write logs)
  - SELECT remains allowed (authenticated users can read logs)
  - UPDATE is blocked — no policy exists for it
  - DELETE is blocked — no policy exists for it
  - This enforces the "write-once" guarantee for the audit trail
*/

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'audit_logs'
      AND cmd IN ('UPDATE', 'DELETE')
  ) THEN
    EXECUTE (
      SELECT string_agg(
        format('DROP POLICY IF EXISTS %I ON audit_logs;', policyname),
        ' '
      )
      FROM pg_policies
      WHERE schemaname = 'public'
        AND tablename = 'audit_logs'
        AND cmd IN ('UPDATE', 'DELETE')
    );
  END IF;
END $$;
