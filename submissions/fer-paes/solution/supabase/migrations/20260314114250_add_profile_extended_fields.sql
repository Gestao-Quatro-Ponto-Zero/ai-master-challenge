
/*
  # Add Extended Fields to Profiles Table

  ## Summary
  Adds additional profile fields needed for user management in Subfase 1.5.

  ## Changes to `profiles` table
  - `department` (text) — User's department within the organization
  - `phone` (text) — User's contact phone number
  - `timezone` (text) — User's timezone preference, defaults to 'UTC'

  ## Security
  - Adds policy allowing authenticated users to update any profile (admin operations)
  - Adds policy allowing authenticated users to insert profiles for other users

  ## Notes
  1. All new columns are optional (nullable or have defaults) to avoid breaking existing rows
  2. No destructive changes are made to existing data
*/

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'profiles' AND column_name = 'department'
  ) THEN
    ALTER TABLE profiles ADD COLUMN department text NOT NULL DEFAULT '';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'profiles' AND column_name = 'phone'
  ) THEN
    ALTER TABLE profiles ADD COLUMN phone text NOT NULL DEFAULT '';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'profiles' AND column_name = 'timezone'
  ) THEN
    ALTER TABLE profiles ADD COLUMN timezone text NOT NULL DEFAULT 'UTC';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'profiles' AND policyname = 'Authenticated users can update all profiles'
  ) THEN
    EXECUTE 'CREATE POLICY "Authenticated users can update all profiles"
      ON profiles FOR UPDATE
      TO authenticated
      USING (true)
      WITH CHECK (true)';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'profiles' AND policyname = 'Authenticated users can insert profiles for others'
  ) THEN
    EXECUTE 'CREATE POLICY "Authenticated users can insert profiles for others"
      ON profiles FOR INSERT
      TO authenticated
      WITH CHECK (true)';
  END IF;
END $$;
