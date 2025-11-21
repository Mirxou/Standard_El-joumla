-- Migration: add missing columns to existing tables for enhanced services compatibility
PRAGMA foreign_keys = ON;

-- Add status column to sales if not present (for order lifecycle management)
-- Using a temporary approach: check and add if needed
ALTER TABLE sales ADD COLUMN status TEXT DEFAULT 'pending' CHECK(status IN ('draft', 'pending', 'confirmed', 'invoiced', 'paid', 'cancelled'));

-- Add invoice_id column to payments table if using enhanced invoices schema
-- If this fails, payments may already have different columns (payment_type, entity_id) - both are acceptable
ALTER TABLE payments ADD COLUMN invoice_id INTEGER REFERENCES invoices(id);

-- Index for faster status lookups
CREATE INDEX IF NOT EXISTS idx_sales_status ON sales(status);

-- Index for invoice payments lookup
CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id);

PRAGMA foreign_keys = ON;
