-- =============================================================================
-- KandyPack Logistics – Seed Data
-- Run AFTER schema.sql and all stored procedures are applied (scripts/up.py).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Extension: uuidv7 (required by schema PRIMARY KEY defaults)
-- If your Postgres build already has it, the CREATE EXTENSION is a no-op.
-- -----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pg_uuidv7";

-- -----------------------------------------------------------------------------
-- Users
-- -----------------------------------------------------------------------------
INSERT INTO users (id, name, email, role) VALUES
    ('018f1e2a-0000-7000-8000-000000000001', 'Admin User',      'admin@kandypack.lk',    'admin'),
    ('018f1e2a-0000-7000-8000-000000000002', 'Logistics Mgr',   'logistics@kandypack.lk','logistics'),
    ('018f1e2a-0000-7000-8000-000000000003', 'Store Manager A', 'store_a@kandypack.lk',  'store_manager'),
    ('018f1e2a-0000-7000-8000-000000000004', 'Store Manager B', 'store_b@kandypack.lk',  'store_manager')
ON CONFLICT (email) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Stores
-- -----------------------------------------------------------------------------
INSERT INTO stores (store_name, address, manager_id, created_by, updated_by) VALUES
    ('Kandy Central Hub',  '12 Peradeniya Rd, Kandy',     '018f1e2a-0000-7000-8000-000000000003', '018f1e2a-0000-7000-8000-000000000001', '018f1e2a-0000-7000-8000-000000000001'),
    ('Colombo South Store','45 Galle Rd, Colombo 03',      '018f1e2a-0000-7000-8000-000000000004', '018f1e2a-0000-7000-8000-000000000001', '018f1e2a-0000-7000-8000-000000000001')
ON CONFLICT (store_name) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Routes  (reference store IDs by name to stay idempotent)
-- -----------------------------------------------------------------------------
INSERT INTO routes (store_id, route_name, service_area, max_delivery_time_hrs, created_by, updated_by)
SELECT s.id, 'R-01 Colombo North', 'Colombo North Zone',  4.0,
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM stores s WHERE s.store_name = 'Colombo South Store'
ON CONFLICT DO NOTHING;

INSERT INTO routes (store_id, route_name, service_area, max_delivery_time_hrs, created_by, updated_by)
SELECT s.id, 'R-02 Colombo South', 'Colombo South Zone',  5.0,
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM stores s WHERE s.store_name = 'Colombo South Store'
ON CONFLICT DO NOTHING;

INSERT INTO routes (store_id, route_name, service_area, max_delivery_time_hrs, created_by, updated_by)
SELECT s.id, 'R-03 Kandy Metro', 'Kandy Metropolitan Area', 3.0,
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM stores s WHERE s.store_name = 'Kandy Central Hub'
ON CONFLICT DO NOTHING;

-- -----------------------------------------------------------------------------
-- Trucks
-- -----------------------------------------------------------------------------
INSERT INTO trucks (store_id, license_plate, capacity, vehicle_status, route_id, created_by, updated_by)
SELECT s.id, 'CAB-1234', 50.00, 'Active', r.id,
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM stores s
JOIN routes r ON r.store_id = s.id AND r.route_name = 'R-01 Colombo North'
WHERE s.store_name = 'Colombo South Store'
ON CONFLICT (license_plate) DO NOTHING;

INSERT INTO trucks (store_id, license_plate, capacity, vehicle_status, route_id, created_by, updated_by)
SELECT s.id, 'CAB-5678', 30.00, 'Active', r.id,
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM stores s
JOIN routes r ON r.store_id = s.id AND r.route_name = 'R-02 Colombo South'
WHERE s.store_name = 'Colombo South Store'
ON CONFLICT (license_plate) DO NOTHING;

INSERT INTO trucks (store_id, license_plate, capacity, vehicle_status, route_id, created_by, updated_by)
SELECT s.id, 'NB-9900', 40.00, 'Active', r.id,
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM stores s
JOIN routes r ON r.store_id = s.id AND r.route_name = 'R-03 Kandy Metro'
WHERE s.store_name = 'Kandy Central Hub'
ON CONFLICT (license_plate) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Employees
-- -----------------------------------------------------------------------------
INSERT INTO employees (store_id, employee_name, employee_role, contact_phone, employee_status, created_by, updated_by)
SELECT s.id, 'Sunil Perera',      'DRIVER',    '0771234567', 'Available',
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM stores s WHERE s.store_name = 'Colombo South Store';

INSERT INTO employees (store_id, employee_name, employee_role, contact_phone, employee_status, created_by, updated_by)
SELECT s.id, 'Nimal Fernando',    'DRIVER',    '0779876543', 'Available',
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM stores s WHERE s.store_name = 'Colombo South Store';

INSERT INTO employees (store_id, employee_name, employee_role, contact_phone, employee_status, created_by, updated_by)
SELECT s.id, 'Kamal Silva',       'ASSISTANT', '0712223334', 'Available',
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM stores s WHERE s.store_name = 'Colombo South Store';

INSERT INTO employees (store_id, employee_name, employee_role, contact_phone, employee_status, created_by, updated_by)
SELECT s.id, 'Priyantha Bandara', 'ASSISTANT', '0755556667', 'Available',
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM stores s WHERE s.store_name = 'Colombo South Store';

INSERT INTO employees (store_id, employee_name, employee_role, contact_phone, employee_status, created_by, updated_by)
SELECT s.id, 'Roshan Kumara',     'DRIVER',    '0741112223', 'Available',
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM stores s WHERE s.store_name = 'Kandy Central Hub';

INSERT INTO employees (store_id, employee_name, employee_role, contact_phone, employee_status, created_by, updated_by)
SELECT s.id, 'Lasith Jayawardena','ASSISTANT', '0768889990', 'Available',
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM stores s WHERE s.store_name = 'Kandy Central Hub';

-- -----------------------------------------------------------------------------
-- Products
-- -----------------------------------------------------------------------------
INSERT INTO products (product_name, unit_price, space_consumption_unit, created_by, updated_by) VALUES
    ('Packaged Goods A',    1200.00, 0.50, '018f1e2a-0000-7000-8000-000000000001', '018f1e2a-0000-7000-8000-000000000001'),
    ('Beverage Crate B',    2400.00, 1.20, '018f1e2a-0000-7000-8000-000000000001', '018f1e2a-0000-7000-8000-000000000001'),
    ('Confectionery Box C',  850.00, 0.30, '018f1e2a-0000-7000-8000-000000000001', '018f1e2a-0000-7000-8000-000000000001')
ON CONFLICT DO NOTHING;

-- -----------------------------------------------------------------------------
-- Customers
-- -----------------------------------------------------------------------------
INSERT INTO customers (customer_name, address, contact_phone, default_route_id, created_by, updated_by)
SELECT 'Kandy Retailers Ltd',  '88 Temple St, Kandy',       '0812223334', r.id,
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM routes r WHERE r.route_name = 'R-01 Colombo North';

INSERT INTO customers (customer_name, address, contact_phone, default_route_id, created_by, updated_by)
SELECT 'Colombo Supermart',    '10 Galle Face, Colombo 01', '0112223335', r.id,
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM routes r WHERE r.route_name = 'R-02 Colombo South';

-- -----------------------------------------------------------------------------
-- Orders  (placed 10 days ago so the 7-day ordering rule is satisfied)
-- -----------------------------------------------------------------------------
INSERT INTO orders (customer_id, route_id, delivery_address, contact_phone, order_date, created_by, updated_by)
SELECT c.id, r.id, '88 Temple St, Kandy', '0812223334',
       CURRENT_TIMESTAMP - INTERVAL '10 days',
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM customers c
JOIN routes r ON r.id = c.default_route_id
WHERE c.customer_name = 'Kandy Retailers Ltd';

INSERT INTO orders (customer_id, route_id, delivery_address, contact_phone, order_date, created_by, updated_by)
SELECT c.id, r.id, '10 Galle Face, Colombo 01', '0112223335',
       CURRENT_TIMESTAMP - INTERVAL '10 days',
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM customers c
JOIN routes r ON r.id = c.default_route_id
WHERE c.customer_name = 'Colombo Supermart';

-- -----------------------------------------------------------------------------
-- Order Items  (initial status PLACED)
-- -----------------------------------------------------------------------------
INSERT INTO order_items (order_id, product_id, unit_price, quantity, item_lifecycle_status)
SELECT o.id, p.id, p.unit_price, 5, 'PLACED'
FROM orders o
JOIN customers c ON c.id = o.customer_id AND c.customer_name = 'Kandy Retailers Ltd'
JOIN products p ON p.product_name = 'Packaged Goods A';

INSERT INTO order_items (order_id, product_id, unit_price, quantity, item_lifecycle_status)
SELECT o.id, p.id, p.unit_price, 3, 'PLACED'
FROM orders o
JOIN customers c ON c.id = o.customer_id AND c.customer_name = 'Kandy Retailers Ltd'
JOIN products p ON p.product_name = 'Beverage Crate B';

INSERT INTO order_items (order_id, product_id, unit_price, quantity, item_lifecycle_status)
SELECT o.id, p.id, p.unit_price, 10, 'PLACED'
FROM orders o
JOIN customers c ON c.id = o.customer_id AND c.customer_name = 'Colombo Supermart'
JOIN products p ON p.product_name = 'Confectionery Box C';

-- -----------------------------------------------------------------------------
-- Train schedule + allocations so items can progress to STORE_RECEIVED
-- (departure 8 days ago so the train has already arrived at the store)
-- -----------------------------------------------------------------------------
INSERT INTO train_schedules (destination_store_id, departure_timestamp, max_capacity, created_by, updated_by)
SELECT s.id,
       CURRENT_TIMESTAMP - INTERVAL '8 days',
       500.00,
       '018f1e2a-0000-7000-8000-000000000001',
       '018f1e2a-0000-7000-8000-000000000001'
FROM stores s WHERE s.store_name = 'Colombo South Store';

-- Allocate all PLACED items to that train
INSERT INTO train_allocations (order_item_id, train_id, created_by)
SELECT oi.id, ts.id, '018f1e2a-0000-7000-8000-000000000001'
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN train_schedules ts ON ts.destination_store_id = o.route_id  -- will be corrected below
WHERE oi.item_lifecycle_status = 'PLACED'
ON CONFLICT DO NOTHING;

-- The join above used route_id; redo correctly via store_id through the route
INSERT INTO train_allocations (order_item_id, train_id, created_by)
SELECT oi.id, ts.id, '018f1e2a-0000-7000-8000-000000000001'
FROM order_items oi
JOIN orders      o  ON o.id  = oi.order_id
JOIN routes      r  ON r.id  = o.route_id
JOIN train_schedules ts ON ts.destination_store_id = r.store_id
WHERE oi.item_lifecycle_status = 'PLACED'
ON CONFLICT (order_item_id) DO NOTHING;

-- Advance items to STORE_RECEIVED (they are physically at the store, ready for truck dispatch)
UPDATE order_items
SET item_lifecycle_status = 'STORE_RECEIVED'
WHERE id IN (
    SELECT oi.id
    FROM order_items oi
    JOIN train_allocations ta ON ta.order_item_id = oi.id
    WHERE oi.item_lifecycle_status = 'PLACED'
);
