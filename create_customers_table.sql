-- Create customers table for Unified Commerce
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_en TEXT,
    phone TEXT,
    phone2 TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    country TEXT DEFAULT 'الجزائر',
    tax_number TEXT,
    credit_limit DECIMAL(15,2) DEFAULT 0.00,
    current_balance DECIMAL(15,2) DEFAULT 0.00,
    notes TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_purchase_date DATE,
    total_purchases DECIMAL(15,2) DEFAULT 0.00,
    purchases_count INTEGER DEFAULT 0,
    -- Unified Commerce Fields
    customer_type TEXT,
    customer_group_id INTEGER,
    customer_segment TEXT,
    pricing_tier INTEGER,
    price_list_id INTEGER,
    contract_id INTEGER,
    volume_discount_threshold DECIMAL(15,2),
    parent_account_id INTEGER,
    account_hierarchy_level INTEGER DEFAULT 0,
    is_headquarter BOOLEAN DEFAULT 0,
    payment_terms TEXT,
    credit_rating TEXT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_type ON customers(customer_type);
CREATE INDEX IF NOT EXISTS idx_customers_active ON customers(is_active);