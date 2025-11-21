-- ====================================
-- Migration: 004 - Quotes and Returns System
-- Created: 2025-11-17
-- Description: Tables for quotes and return invoices management
-- ====================================

-- ====================================
-- جدول عروض الأسعار (Quotes)
-- ====================================
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_number TEXT NOT NULL UNIQUE,
    customer_id INTEGER,
    customer_name TEXT,
    customer_phone TEXT,
    customer_email TEXT,
    customer_address TEXT,
    
    -- Dates
    quote_date DATE NOT NULL,
    valid_until DATE,
    sent_date DATE,
    response_date DATE,
    
    -- Status: DRAFT, SENT, ACCEPTED, REJECTED, EXPIRED, CONVERTED, CANCELLED
    status TEXT NOT NULL DEFAULT 'DRAFT',
    
    -- Amounts
    subtotal REAL NOT NULL DEFAULT 0.0,
    discount_amount REAL NOT NULL DEFAULT 0.0,
    discount_percentage REAL NOT NULL DEFAULT 0.0,
    tax_amount REAL NOT NULL DEFAULT 0.0,
    total_amount REAL NOT NULL DEFAULT 0.0,
    
    -- Terms
    payment_terms TEXT,
    delivery_terms TEXT,
    
    -- Notes
    notes TEXT,
    internal_notes TEXT,
    terms_and_conditions TEXT,
    
    -- Conversion tracking
    converted_to_sale_id INTEGER,
    converted_date DATE,
    
    -- Audit
    created_by INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (converted_to_sale_id) REFERENCES sales(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ====================================
-- جدول بنود عروض الأسعار (Quote Items)
-- ====================================
CREATE TABLE IF NOT EXISTS quote_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    product_barcode TEXT,
    description TEXT,
    
    -- Quantities and pricing
    quantity REAL NOT NULL DEFAULT 1.0,
    unit_price REAL NOT NULL DEFAULT 0.0,
    
    -- Discounts
    discount_amount REAL NOT NULL DEFAULT 0.0,
    discount_percentage REAL NOT NULL DEFAULT 0.0,
    
    -- Tax
    tax_amount REAL NOT NULL DEFAULT 0.0,
    tax_percentage REAL NOT NULL DEFAULT 15.0,
    
    -- Total
    total_amount REAL NOT NULL DEFAULT 0.0,
    
    notes TEXT,
    
    FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

-- ====================================
-- جدول فواتير المرتجعات (Return Invoices)
-- ====================================
CREATE TABLE IF NOT EXISTS return_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_number TEXT NOT NULL UNIQUE,
    
    -- Type: SALE_RETURN or PURCHASE_RETURN
    return_type TEXT NOT NULL DEFAULT 'SALE_RETURN',
    
    -- Original invoice reference
    original_sale_id INTEGER,
    original_purchase_id INTEGER,
    original_invoice_number TEXT,
    
    -- Contact info (customer or supplier)
    customer_id INTEGER,
    supplier_id INTEGER,
    contact_name TEXT,
    contact_phone TEXT,
    
    -- Dates
    return_date DATE NOT NULL,
    original_invoice_date DATE,
    
    -- Status: PENDING, APPROVED, REJECTED, COMPLETED, CANCELLED
    status TEXT NOT NULL DEFAULT 'PENDING',
    
    -- Reason: DEFECTIVE, DAMAGED, WRONG_ITEM, EXPIRED, NOT_AS_DESCRIBED, CUSTOMER_REQUEST, OVERSTOCK, OTHER
    return_reason TEXT,
    description TEXT,
    
    -- Amounts
    subtotal REAL NOT NULL DEFAULT 0.0,
    discount_amount REAL NOT NULL DEFAULT 0.0,
    tax_amount REAL NOT NULL DEFAULT 0.0,
    total_amount REAL NOT NULL DEFAULT 0.0,
    
    -- Refund details
    -- Method: CASH, CREDIT_NOTE, EXCHANGE, BANK_TRANSFER, STORE_CREDIT
    refund_method TEXT,
    refund_amount REAL NOT NULL DEFAULT 0.0,
    refund_date DATE,
    refund_reference TEXT,
    
    -- Credit note
    credit_note_number TEXT,
    credit_note_amount REAL NOT NULL DEFAULT 0.0,
    
    -- Exchange tracking
    exchange_sale_id INTEGER,
    
    -- Notes
    notes TEXT,
    internal_notes TEXT,
    
    -- Audit
    created_by INTEGER,
    approved_by INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at DATETIME,
    
    FOREIGN KEY (original_sale_id) REFERENCES sales(id) ON DELETE SET NULL,
    FOREIGN KEY (original_purchase_id) REFERENCES purchases(id) ON DELETE SET NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
    FOREIGN KEY (exchange_sale_id) REFERENCES sales(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ====================================
-- جدول بنود المرتجعات (Return Items)
-- ====================================
CREATE TABLE IF NOT EXISTS return_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_id INTEGER NOT NULL,
    
    -- Reference to original item
    original_sale_item_id INTEGER,
    original_purchase_item_id INTEGER,
    
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    product_barcode TEXT,
    
    -- Quantities
    quantity_returned REAL NOT NULL DEFAULT 0.0,
    quantity_original REAL NOT NULL DEFAULT 0.0,
    
    -- Pricing
    unit_price REAL NOT NULL DEFAULT 0.0,
    discount_amount REAL NOT NULL DEFAULT 0.0,
    tax_amount REAL NOT NULL DEFAULT 0.0,
    total_amount REAL NOT NULL DEFAULT 0.0,
    
    -- Return details
    -- Reason: DEFECTIVE, DAMAGED, WRONG_ITEM, EXPIRED, NOT_AS_DESCRIBED, CUSTOMER_REQUEST, OVERSTOCK, OTHER
    return_reason TEXT,
    condition TEXT,
    restockable INTEGER NOT NULL DEFAULT 1,
    
    notes TEXT,
    
    FOREIGN KEY (return_id) REFERENCES return_invoices(id) ON DELETE CASCADE,
    FOREIGN KEY (original_sale_item_id) REFERENCES sale_items(id) ON DELETE SET NULL,
    FOREIGN KEY (original_purchase_item_id) REFERENCES purchase_items(id) ON DELETE SET NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

-- ====================================
-- Indexes for Quotes
-- ====================================
CREATE INDEX IF NOT EXISTS idx_quotes_customer 
ON quotes(customer_id);

CREATE INDEX IF NOT EXISTS idx_quotes_status 
ON quotes(status);

CREATE INDEX IF NOT EXISTS idx_quotes_date 
ON quotes(quote_date);

CREATE INDEX IF NOT EXISTS idx_quotes_valid_until 
ON quotes(valid_until);

CREATE INDEX IF NOT EXISTS idx_quotes_number 
ON quotes(quote_number);

CREATE INDEX IF NOT EXISTS idx_quote_items_quote 
ON quote_items(quote_id);

CREATE INDEX IF NOT EXISTS idx_quote_items_product 
ON quote_items(product_id);

-- ====================================
-- Indexes for Returns
-- ====================================
CREATE INDEX IF NOT EXISTS idx_returns_customer 
ON return_invoices(customer_id);

CREATE INDEX IF NOT EXISTS idx_returns_supplier 
ON return_invoices(supplier_id);

CREATE INDEX IF NOT EXISTS idx_returns_status 
ON return_invoices(status);

CREATE INDEX IF NOT EXISTS idx_returns_type 
ON return_invoices(return_type);

CREATE INDEX IF NOT EXISTS idx_returns_date 
ON return_invoices(return_date);

CREATE INDEX IF NOT EXISTS idx_returns_number 
ON return_invoices(return_number);

CREATE INDEX IF NOT EXISTS idx_returns_original_sale 
ON return_invoices(original_sale_id);

CREATE INDEX IF NOT EXISTS idx_returns_original_purchase 
ON return_invoices(original_purchase_id);

CREATE INDEX IF NOT EXISTS idx_return_items_return 
ON return_items(return_id);

CREATE INDEX IF NOT EXISTS idx_return_items_product 
ON return_items(product_id);

CREATE INDEX IF NOT EXISTS idx_return_items_original_sale 
ON return_items(original_sale_item_id);

CREATE INDEX IF NOT EXISTS idx_return_items_original_purchase 
ON return_items(original_purchase_item_id);
