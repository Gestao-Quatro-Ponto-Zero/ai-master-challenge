/*
  # Add system.internal Permission

  ## Overview
  Registers the `system.internal` permission required by the LLM Router Engine
  for internal service-to-service execution. This permission is assigned to
  admin and supervisor roles.

  ## Changes
  - New permission: `system.internal` in category `system`
  - Assigned to: admin, supervisor
*/

INSERT INTO permissions (name, description, category)
VALUES ('system.internal', 'Execute internal system services and LLM router', 'system')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'admin' AND p.name = 'system.internal'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'supervisor' AND p.name = 'system.internal'
ON CONFLICT DO NOTHING;
