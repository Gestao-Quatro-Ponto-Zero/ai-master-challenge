/*
  # Add analytics.view permission and avg first response RPC

  1. Changes
    - Adds `analytics.view` permission
    - Grants it to roles that have admin/supervisor capabilities
    - Creates `get_avg_first_response_seconds()` RPC function that returns the
      average time in seconds between ticket creation and the first operator message

  2. Security
    - RPC runs with SECURITY DEFINER so it can read across rows
    - Permission check is enforced at the application layer via PermissionGuard
*/

INSERT INTO permissions (name, description, category)
VALUES ('analytics.view', 'Access to operational analytics and ticket statistics', 'analytics')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name = 'analytics.view'
WHERE r.name IN ('admin', 'supervisor', 'superadmin')
ON CONFLICT DO NOTHING;

CREATE OR REPLACE FUNCTION get_avg_first_response_seconds()
RETURNS numeric
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT AVG(
    EXTRACT(EPOCH FROM (first_op_msg.first_at - t.created_at))
  )
  FROM tickets t
  JOIN conversations c ON c.ticket_id = t.id
  JOIN (
    SELECT
      m.conversation_id,
      MIN(m.created_at) AS first_at
    FROM messages m
    WHERE m.sender_type = 'operator'
    GROUP BY m.conversation_id
  ) first_op_msg ON first_op_msg.conversation_id = c.id;
$$;
