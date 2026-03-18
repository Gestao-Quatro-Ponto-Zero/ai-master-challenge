
/*
  # Seed Roles and Permissions

  ## Summary
  Inserts the default roles and permissions into the database.

  ## Roles
  - admin: Full system access
  - supervisor: Can manage tickets, users and view reports
  - operator: Can work with tickets
  - viewer: Read-only access

  ## Permissions (by category)
  - users: users.manage, users.view
  - roles: roles.manage, roles.view
  - tickets: tickets.view, tickets.create, tickets.assign, tickets.close, tickets.manage
  - reports: reports.view
  - settings: settings.manage

  ## Role-Permission Assignments
  - admin: all permissions
  - supervisor: tickets.*, users.view, reports.view
  - operator: tickets.view, tickets.create, tickets.close
  - viewer: tickets.view
*/

INSERT INTO roles (name, description, is_system) VALUES
  ('admin', 'Full system access. Can manage users, roles and all resources.', true),
  ('supervisor', 'Can manage tickets and users, view reports.', true),
  ('operator', 'Can work with tickets.', true),
  ('viewer', 'Read-only access to the system.', true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO permissions (name, description, category) VALUES
  ('users.manage', 'Create, update and delete users', 'users'),
  ('users.view', 'View users list and details', 'users'),
  ('roles.manage', 'Create, update roles and assign permissions', 'roles'),
  ('roles.view', 'View roles list and their permissions', 'roles'),
  ('tickets.view', 'View tickets and their details', 'tickets'),
  ('tickets.create', 'Create new tickets', 'tickets'),
  ('tickets.assign', 'Assign tickets to operators', 'tickets'),
  ('tickets.close', 'Close and resolve tickets', 'tickets'),
  ('tickets.manage', 'Full ticket management', 'tickets'),
  ('reports.view', 'View reports and analytics', 'reports'),
  ('settings.manage', 'Manage system settings', 'settings')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name IN ('tickets.view','tickets.create','tickets.assign','tickets.close','tickets.manage','users.view','roles.view','reports.view')
WHERE r.name = 'supervisor'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name IN ('tickets.view','tickets.create','tickets.close')
WHERE r.name = 'operator'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name IN ('tickets.view')
WHERE r.name = 'viewer'
ON CONFLICT DO NOTHING;
