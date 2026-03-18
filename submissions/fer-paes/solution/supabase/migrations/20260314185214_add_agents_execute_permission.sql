/*
  # Add agents.execute Permission

  ## Summary
  Adds the agents.execute permission required by the Agent Router to authorize
  routing and execution calls. Assigns it to the admin role.

  ## New Permissions
  - `agents.execute` – Execute agent routing and run agent workflows (category: agents)

  ## Role Assignments
  - admin: agents.execute
*/

INSERT INTO permissions (name, description, category) VALUES
  ('agents.execute', 'Execute agent routing and run agent workflows', 'agents')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'admin'
  AND p.name = 'agents.execute'
ON CONFLICT DO NOTHING;
