/*
  # Add Agents Permissions

  ## Summary
  Adds agents.view and agents.manage permissions to the system and assigns them to the admin role.

  ## New Permissions
  - `agents.view` – View agents list and details (category: agents)
  - `agents.manage` – Create, update and configure agents (category: agents)

  ## Role Assignments
  - admin: both agents.view and agents.manage
  - supervisor: agents.view only
*/

INSERT INTO permissions (name, description, category) VALUES
  ('agents.view', 'View agents list and details', 'agents'),
  ('agents.manage', 'Create, update and configure agents', 'agents')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'admin'
  AND p.name IN ('agents.view', 'agents.manage')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name = 'agents.view'
WHERE r.name = 'supervisor'
ON CONFLICT DO NOTHING;
