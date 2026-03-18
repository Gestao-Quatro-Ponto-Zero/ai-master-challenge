/*
  # Add tickets.reply permission

  1. Changes
    - Adds `tickets.reply` permission to the permissions table
    - Assigns the permission to roles that already have `tickets.view` (agent, admin/superadmin)

  2. Notes
    - Safe to run multiple times due to ON CONFLICT DO NOTHING
*/

INSERT INTO permissions (name, description)
VALUES ('tickets.reply', 'Allows sending messages in ticket conversations')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT rp.role_id, p.id
FROM role_permissions rp
JOIN permissions pview ON pview.id = rp.permission_id AND pview.name = 'tickets.view'
JOIN permissions p ON p.name = 'tickets.reply'
ON CONFLICT DO NOTHING;
