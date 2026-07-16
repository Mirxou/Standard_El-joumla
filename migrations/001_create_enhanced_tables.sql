-- Migration: create enhanced tables used by new services
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    name_en TEXT,
    sku TEXT,
    barcode TEXT,
    category_id INTEGER,
    supplier_id INTEGER,
    product_type TEXT,
    description TEXT,
    specifications TEXT,
    unit TEXT,
    cost_price REAL DEFAULT 0.0,
    base_price REAL DEFAULT 0.0,
    pricing_policy TEXT,
    current_stock INTEGER DEFAULT 0,
    reserved_stock INTEGER DEFAULT 0,
    min_stock INTEGER DEFAULT 0,
    reorder_point INTEGER DEFAULT 0,
    max_stock INTEGER DEFAULT 0,
    image_path TEXT,
    images TEXT,
    tags TEXT,
    is_active INTEGER DEFAULT 1,
    is_discontinued INTEGER DEFAULT 0,
    is_featured INTEGER DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS product_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    sku TEXT,
    attributes TEXT,
    cost_price REAL,
    selling_price REAL,
    stock_quantity INTEGER,
    barcode TEXT,
    image_path TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS bundle_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bundle_id INTEGER,
    product_id INTEGER,
    product_name TEXT,
    quantity INTEGER,
    unit_price REAL,
    FOREIGN KEY(bundle_id) REFERENCES products(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS pricing_tiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    min_quantity INTEGER,
    max_quantity INTEGER,
    price REAL,
    discount_percent REAL,
    valid_from DATETIME,
    valid_until DATETIME,
    description TEXT,
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS product_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    label_type TEXT,
    label_text TEXT,
    label_color TEXT,
    priority INTEGER,
    start_date DATETIME,
    end_date DATETIME,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    movement_type TEXT,
    quantity INTEGER,
    from_location TEXT,
    to_location TEXT,
    reference_id INTEGER,
    reference_type TEXT,
    created_at DATETIME,
    user_id INTEGER,
    notes TEXT,
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    status TEXT,
    total_amount REAL,
    created_at DATETIME,
    updated_at DATETIME,
    meta TEXT
);

CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER,
    product_id INTEGER,
    variant_id INTEGER,
    quantity INTEGER,
    unit_price REAL,
    FOREIGN KEY(sale_id) REFERENCES sales(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER,
    customer_id INTEGER,
    amount REAL,
    status TEXT,
    issued_at DATETIME,
    due_at DATETIME,
    paid_at DATETIME
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER,
    amount REAL,
    method TEXT,
    reference TEXT,
    paid_at DATETIME
);

-- audit_logs, roles, user_roles
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    object_type TEXT,
    object_id INTEGER,
    timestamp DATETIME,
    details TEXT
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    role_id INTEGER,
    assigned_at DATETIME,
    FOREIGN KEY(role_id) REFERENCES roles(id)
);
