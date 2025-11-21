-- Migration 013: Product Variants, Bundles, Pricing, Barcodes, Tags

-- Product Variants
CREATE TABLE IF NOT EXISTS product_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    sku TEXT UNIQUE,
    attributes TEXT, -- JSON string of attributes (e.g., {"size":"L","color":"Red"})
    barcode TEXT UNIQUE,
    cost_price DECIMAL(10,2),
    selling_price DECIMAL(10,2),
    current_stock INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_product_variants_product ON product_variants(product_id);
CREATE INDEX IF NOT EXISTS idx_product_variants_sku ON product_variants(sku);

-- Product Bundles (bundle is a product composed of items)
CREATE TABLE IF NOT EXISTS product_bundles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL, -- the parent product representing the bundle
    name TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_product_bundles_product ON product_bundles(product_id);

-- Bundle Items (can be product or variant)
CREATE TABLE IF NOT EXISTS product_bundle_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bundle_id INTEGER NOT NULL,
    item_type TEXT NOT NULL CHECK (item_type IN ('product','variant')),
    item_product_id INTEGER,
    item_variant_id INTEGER,
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bundle_id) REFERENCES product_bundles(id),
    FOREIGN KEY (item_product_id) REFERENCES products(id),
    FOREIGN KEY (item_variant_id) REFERENCES product_variants(id)
);

CREATE INDEX IF NOT EXISTS idx_bundle_items_bundle ON product_bundle_items(bundle_id);

-- Tiered/Advanced Pricing
CREATE TABLE IF NOT EXISTS product_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    variant_id INTEGER,
    price_type TEXT NOT NULL DEFAULT 'retail', -- retail, wholesale, customer_group
    customer_group TEXT, -- optional grouping key
    min_qty INTEGER DEFAULT 1,
    price DECIMAL(10,2) NOT NULL,
    valid_from DATE,
    valid_to DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (variant_id) REFERENCES product_variants(id)
);

CREATE INDEX IF NOT EXISTS idx_product_prices_product ON product_prices(product_id);
CREATE INDEX IF NOT EXISTS idx_product_prices_variant ON product_prices(variant_id);
CREATE INDEX IF NOT EXISTS idx_product_prices_type ON product_prices(price_type);

-- Barcodes (multiple per product/variant)
CREATE TABLE IF NOT EXISTS product_barcodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    variant_id INTEGER,
    barcode TEXT NOT NULL,
    barcode_type TEXT DEFAULT 'auto', -- ean13, code128, qrcode, auto
    is_primary BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(barcode),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (variant_id) REFERENCES product_variants(id)
);

CREATE INDEX IF NOT EXISTS idx_product_barcodes_prod ON product_barcodes(product_id);
CREATE INDEX IF NOT EXISTS idx_product_barcodes_var ON product_barcodes(variant_id);

-- Product Tags
CREATE TABLE IF NOT EXISTS product_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    UNIQUE(product_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_product_tags_product ON product_tags(product_id);
