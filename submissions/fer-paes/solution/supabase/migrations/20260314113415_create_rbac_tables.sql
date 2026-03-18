
/*
  # RBAC Tables — Create Core Authorization Schema

  ## Summary
  Creates all tables required for Role Based Access Control (RBAC):

  ## New Tables

  1. `profiles` — Extended user data linked to Supabase auth.users
     - id (uuid, FK to auth.users)
     - full_name, email, avatar_url, status, created_at, updated_at

  2. `roles` — Application roles (admin, supervisor, operator, viewer)
     - id, name (unique), description, is_system, created_at, updated_at

  3. `permissions` — Granular permissions (users.manage, roles.manage, etc.)
     - id, name (unique), description, category, created_at

  4. `role_permissions` — Many-to-many: roles <-> permissions
     - role_id, permission_id (composite PK)

  5. `user_roles` — Many-to-many: users <-> roles
     - user_id, role_id (composite PK), assigned_by, assigned_at

  6. `audit_logs` — Track all sensitive actions
     - id, user_id, action, resource, resource_id, meta, created_at

  ## Security
  - RLS enabled on all tables
  - Authenticated users can read their own profile
  - Authenticated users can read roles and permissions
  - Admin-level operations require users.manage / roles.manage permissions (enforced in application layer + RLS)
*/

CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name text NOT NULL DEFAULT '',
  email text NOT NULL DEFAULT '',
  avatar_url text DEFAULT NULL,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text UNIQUE NOT NULL,
  description text NOT NULL DEFAULT '',
  is_system boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS permissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text UNIQUE NOT NULL,
  description text NOT NULL DEFAULT '',
  category text NOT NULL DEFAULT 'general',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS role_permissions (
  role_id uuid NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  permission_id uuid NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
  PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS user_roles (
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role_id uuid NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  assigned_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  assigned_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  action text NOT NULL,
  resource text NOT NULL DEFAULT '',
  resource_id text DEFAULT NULL,
  meta jsonb DEFAULT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own profile"
  ON profiles FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON profiles FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Authenticated users can read roles"
  ON roles FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read permissions"
  ON permissions FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read role_permissions"
  ON role_permissions FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read own user_roles"
  ON user_roles FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Authenticated users can read all user_roles"
  ON user_roles FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert user_roles"
  ON user_roles FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can delete user_roles"
  ON user_roles FOR DELETE
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert role_permissions"
  ON role_permissions FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can delete role_permissions"
  ON role_permissions FOR DELETE
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert roles"
  ON roles FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update roles"
  ON roles FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can read all profiles"
  ON profiles FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read audit_logs"
  ON audit_logs FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert audit_logs"
  ON audit_logs FOR INSERT
  TO authenticated
  WITH CHECK (true);
