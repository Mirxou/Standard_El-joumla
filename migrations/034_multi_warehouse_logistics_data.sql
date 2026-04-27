-- Phase 6: Multi-Warehouse Management & Logistics Integration
-- Sample Data Migration

-- Insert sample data for testing
INSERT OR IGNORE INTO warehouses (code, name, city, country, is_active) VALUES
('WH001', 'Main Distribution Center', 'Riyadh', 'Saudi Arabia', 1),
('WH002', 'Jeddah Warehouse', 'Jeddah', 'Saudi Arabia', 1),
('WH003', 'Dammam Distribution', 'Dammam', 'Saudi Arabia', 1);

INSERT OR IGNORE INTO carriers (carrier_id, name, type, reliability_score, average_cost_per_kg, average_delivery_days) VALUES
('CAR001', 'Saudi Post', 'ground', 0.95, 15.00, 3),
('CAR002', 'Aramex', 'ground', 0.92, 20.00, 2),
('CAR003', 'DHL Express', 'air', 0.98, 50.00, 1);

INSERT OR IGNORE INTO routes (route_id, origin_warehouse_id, destination_warehouse_id, distance_km, estimated_duration_hours, cost_per_km) VALUES
('RT001', 'WH001', 'WH002', 950.0, 12.0, 2.50),
('RT002', 'WH001', 'WH003', 400.0, 5.0, 2.00),
('RT003', 'WH002', 'WH003', 550.0, 7.0, 2.20);
