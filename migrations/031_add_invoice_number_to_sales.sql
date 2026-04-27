-- Migration: add missing columns to sales and sale_items tables
-- Phase 7: Add missing columns for sales tracking

PRAGMA foreign_keys = ON;

-- Add columns to sales table
ALTER TABLE sales ADD COLUMN invoice_number TEXT;
ALTER TABLE sales ADD COLUMN final_amount REAL DEFAULT 0.0;

-- Add columns to sale_items table
ALTER TABLE sale_items ADD COLUMN batch_id TEXT;
ALTER TABLE sale_items ADD COLUMN discount REAL DEFAULT 0.0;
ALTER TABLE sale_items ADD COLUMN tax_amount REAL DEFAULT 0.0;

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_sales_invoice_number ON sales(invoice_number);
CREATE INDEX IF NOT EXISTS idx_sales_final_amount ON sales(final_amount);
CREATE INDEX IF NOT EXISTS idx_sale_items_batch_id ON sale_items(batch_id);

PRAGMA foreign_keys = ON;