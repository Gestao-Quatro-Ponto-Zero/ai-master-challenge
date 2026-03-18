/*
  # Add Knowledge Base Permissions — Subfase 3.6

  ## Summary
  Inserts two new permissions for the knowledge base module:
  - `knowledge.view`   – read documents and perform searches
  - `knowledge.manage` – upload, edit, and delete documents

  Also grants both permissions to the admin role and `knowledge.view`
  to the agent role if they exist.

  ## New Permissions
  - `knowledge.view`   (category: knowledge)
  - `knowledge.manage` (category: knowledge)
*/

INSERT INTO permissions (name, description, category)
VALUES
  ('knowledge.view',   'View knowledge base documents and perform semantic searches', 'knowledge'),
  ('knowledge.manage', 'Upload, edit and delete knowledge base documents',            'knowledge')
ON CONFLICT (name) DO NOTHING;

DO $$
DECLARE
  v_admin_role_id   uuid;
  v_agent_role_id   uuid;
  v_perm_view_id    uuid;
  v_perm_manage_id  uuid;
BEGIN
  SELECT id INTO v_admin_role_id  FROM roles WHERE name = 'admin'  LIMIT 1;
  SELECT id INTO v_agent_role_id  FROM roles WHERE name = 'agent'  LIMIT 1;
  SELECT id INTO v_perm_view_id   FROM permissions WHERE name = 'knowledge.view'   LIMIT 1;
  SELECT id INTO v_perm_manage_id FROM permissions WHERE name = 'knowledge.manage' LIMIT 1;

  IF v_admin_role_id IS NOT NULL AND v_perm_view_id IS NOT NULL THEN
    INSERT INTO role_permissions (role_id, permission_id)
    VALUES (v_admin_role_id, v_perm_view_id)
    ON CONFLICT DO NOTHING;
  END IF;

  IF v_admin_role_id IS NOT NULL AND v_perm_manage_id IS NOT NULL THEN
    INSERT INTO role_permissions (role_id, permission_id)
    VALUES (v_admin_role_id, v_perm_manage_id)
    ON CONFLICT DO NOTHING;
  END IF;

  IF v_agent_role_id IS NOT NULL AND v_perm_view_id IS NOT NULL THEN
    INSERT INTO role_permissions (role_id, permission_id)
    VALUES (v_agent_role_id, v_perm_view_id)
    ON CONFLICT DO NOTHING;
  END IF;
END $$;
