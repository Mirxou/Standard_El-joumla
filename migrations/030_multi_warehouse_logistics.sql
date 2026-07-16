-- Phase 6: Multi-Warehouse Management & Logistics Integration
-- Database Schema for Warehouses, Transfers, Shipments, Carriers, and Routes

-- Create warehouses table
CREATE TABLE IF NOT EXISTS warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('primary', 'secondary', 'distribution', 'retail')),
    capacity INTEGER NOT NULL,
    current_stock INTEGER DEFAULT 0,
    manager_id INTEGER,
    contact_info TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create warehouse_transfers table
CREATE TABLE IF NOT EXISTS warehouse_transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_id TEXT UNIQUE NOT NULL,
    from_warehouse_id TEXT NOT NULL,
    to_warehouse_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_cost DECIMAL(10,2),
    total_cost DECIMAL(10,2),
    status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'in_transit', 'completed', 'cancelled')),
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    requested_by INTEGER,
    approved_by INTEGER,
    approved_at TIMESTAMP,
    scheduled_date TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_warehouse_id) REFERENCES warehouses(warehouse_id),
    FOREIGN KEY (to_warehouse_id) REFERENCES warehouses(warehouse_id)
);

-- Create carriers table
CREATE TABLE IF NOT EXISTS carriers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carrier_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('ground', 'air', 'sea', 'rail')),
    contact_info TEXT,
    api_endpoint TEXT,
    api_key TEXT,
    is_active BOOLEAN DEFAULT 1,
    reliability_score DECIMAL(3,2) DEFAULT 0.0,
    average_cost_per_kg DECIMAL(8,2),
    average_delivery_days INTEGER,
    service_areas TEXT, -- JSON array of service areas
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create shipments table
CREATE TABLE IF NOT EXISTS shipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id TEXT UNIQUE NOT NULL,
    transfer_id TEXT,
    carrier_id TEXT NOT NULL,
    tracking_number TEXT UNIQUE,
    origin_address TEXT NOT NULL,
    destination_address TEXT NOT NULL,
    weight_kg DECIMAL(8,2),
    volume_m3 DECIMAL(8,2),
    shipping_cost DECIMAL(10,2),
    estimated_delivery TIMESTAMP,
    actual_delivery TIMESTAMP,
    status TEXT NOT NULL CHECK (status IN ('created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'returned')),
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    insurance_amount DECIMAL(10,2),
    special_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transfer_id) REFERENCES warehouse_transfers(transfer_id),
    FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id)
);

-- Create routes table for logistics optimization
CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id TEXT UNIQUE NOT NULL,
    origin_warehouse_id TEXT NOT NULL,
    destination_warehouse_id TEXT NOT NULL,
    carrier_id TEXT,
    distance_km DECIMAL(8,2),
    estimated_duration_hours DECIMAL(6,2),
    cost_per_km DECIMAL(6,2),
    fuel_efficiency DECIMAL(4,2),
    traffic_factor DECIMAL(3,2) DEFAULT 1.0,
    weather_factor DECIMAL(3,2) DEFAULT 1.0,
    is_active BOOLEAN DEFAULT 1,
    last_optimized TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (origin_warehouse_id) REFERENCES warehouses(code),
    FOREIGN KEY (destination_warehouse_id) REFERENCES warehouses(code),
    FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id)
);

-- Create shipment_events table for tracking
CREATE TABLE IF NOT EXISTS shipment_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_description TEXT,
    location TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recorded_by TEXT,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_warehouses_location ON warehouses(location);
CREATE INDEX IF NOT EXISTS idx_warehouses_type ON warehouses(type);
CREATE INDEX IF NOT EXISTS idx_transfers_status ON warehouse_transfers(status);
CREATE INDEX IF NOT EXISTS idx_transfers_from_warehouse ON warehouse_transfers(from_warehouse_id);
CREATE INDEX IF NOT EXISTS idx_transfers_to_warehouse ON warehouse_transfers(to_warehouse_id);
CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments(status);
CREATE INDEX IF NOT EXISTS idx_shipments_carrier ON shipments(carrier_id);
CREATE INDEX IF NOT EXISTS idx_shipments_transfer ON shipments(transfer_id);
CREATE INDEX IF NOT EXISTS idx_routes_origin_dest ON routes(origin_warehouse_id, destination_warehouse_id);
CREATE INDEX IF NOT EXISTS idx_events_shipment ON shipment_events(shipment_id);