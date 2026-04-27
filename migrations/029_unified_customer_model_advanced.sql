-- Migration: 029_unified_customer_model_advanced.sql
-- Description: Add Unified Commerce fields to customers table
-- Date: 2025-02-06

-- Add Unified Commerce columns to customers table
ALTER TABLE customers ADD COLUMN customer_type TEXT;
ALTER TABLE customers ADD COLUMN customer_group_id INTEGER;
ALTER TABLE customers ADD COLUMN customer_segment TEXT;

-- Pricing & Contracts columns
ALTER TABLE customers ADD COLUMN pricing_tier INTEGER;
ALTER TABLE customers ADD COLUMN price_list_id INTEGER;
ALTER TABLE customers ADD COLUMN contract_id INTEGER;
ALTER TABLE customers ADD COLUMN volume_discount_threshold DECIMAL(15,2);

-- Account Hierarchy columns
ALTER TABLE customers ADD COLUMN parent_account_id INTEGER;
ALTER TABLE customers ADD COLUMN account_hierarchy_level INTEGER DEFAULT 0;
ALTER TABLE customers ADD COLUMN is_headquarter BOOLEAN DEFAULT 0;

-- Payment Terms columns
ALTER TABLE customers ADD COLUMN payment_terms TEXT;
ALTER TABLE customers ADD COLUMN credit_rating TEXT;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_customers_customer_type ON customers(customer_type);
CREATE INDEX IF NOT EXISTS idx_customers_customer_segment ON customers(customer_segment);
CREATE INDEX IF NOT EXISTS idx_customers_pricing_tier ON customers(pricing_tier);
CREATE INDEX IF NOT EXISTS idx_customers_parent_account ON customers(parent_account_id);
CREATE INDEX IF NOT EXISTS idx_customers_hierarchy_level ON customers(account_hierarchy_level);

-- Create customer_groups table for grouping customers
CREATE TABLE IF NOT EXISTS customer_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    discount_percentage DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create price_lists table for custom pricing
CREATE TABLE IF NOT EXISTS price_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create price_list_items table
CREATE TABLE IF NOT EXISTS price_list_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    price_list_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    custom_price DECIMAL(15,2),
    discount_percentage DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (price_list_id) REFERENCES price_lists(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Create contracts table for B2B contracts
CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    contract_number TEXT UNIQUE,
    start_date DATE,
    end_date DATE,
    status TEXT DEFAULT 'active', -- active, expired, terminated
    terms TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Create contract_items table
CREATE TABLE IF NOT EXISTS contract_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    agreed_price DECIMAL(15,2),
    minimum_quantity INTEGER DEFAULT 0,
    discount_percentage DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Create indexes for new tables
CREATE INDEX IF NOT EXISTS idx_customer_groups_name ON customer_groups(name);
CREATE INDEX IF NOT EXISTS idx_price_lists_active ON price_lists(is_active);
CREATE INDEX IF NOT EXISTS idx_price_list_items_product ON price_list_items(product_id);
CREATE INDEX IF NOT EXISTS idx_contracts_customer ON contracts(customer_id);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);
CREATE INDEX IF NOT EXISTS idx_contract_items_contract ON contract_items(contract_id);