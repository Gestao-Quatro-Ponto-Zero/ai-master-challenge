-- Seed data for G4 Compass (Initial Users & Team Structure)

-- 1. Regional Offices
INSERT INTO regional_offices (id, name) VALUES 
('018e3000-0001-7000-8000-000000000001', 'Central'),
('018e3000-0001-7000-8000-000000000002', 'East'),
('018e3000-0001-7000-8000-000000000003', 'West')
ON CONFLICT (name) DO NOTHING;

-- 2. Managers
INSERT INTO managers (id, name, regional_office_id) VALUES 
('018e3000-0003-7000-8000-000000000001', 'Dustin Brinkmann', '018e3000-0001-7000-8000-000000000001')
ON CONFLICT (id) DO NOTHING;

-- 3. Sales Agents (Sellers)
INSERT INTO sales_agents (id, name, manager_id, regional_office_id) VALUES 
('018e3000-0004-7000-8000-000000000001', 'Anna Snelling', '018e3000-0003-7000-8000-000000000001', '018e3000-0001-7000-8000-000000000001')
ON CONFLICT (id) DO NOTHING;

-- 4. Users
-- Note: 'admin123' works in development due to handler override.
INSERT INTO users (id, name, email, password_hash, role, manager_id) VALUES 
('018e3000-0005-7000-8000-000000000001', 'Dustin Brinkmann', 'camila@g4.com', '$2a$10$Xm6/X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X', 'manager', '018e3000-0003-7000-8000-000000000001')
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (id, name, email, password_hash, role, sales_agent_id) VALUES 
('018e3000-0005-7000-8000-000000000002', 'Anna Snelling', 'joao@g4.com', '$2a$10$Xm6/X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X6X', 'seller', '018e3000-0004-7000-8000-000000000001')
ON CONFLICT (email) DO NOTHING;
