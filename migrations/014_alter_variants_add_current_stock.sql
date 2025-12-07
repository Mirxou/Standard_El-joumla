-- Migration 014: Align product_variants stock column
PRAGMA foreign_keys = ON;

-- Add current_stock if missing
-- SQLite doesn't support IF NOT EXISTS in ALTER TABLE, so we need to check first
-- This will be handled by the migration script with try-except

-- Check if column exists before adding (handled by migration script)
-- If column already exists, this will fail gracefully
ALTER TABLE product_variants ADD COLUMN current_stock INTEGER DEFAULT 0;

-- Initialize current_stock from legacy stock_quantity when available
-- Only update if the column was successfully added
UPDATE product_variants SET current_stock = COALESCE(current_stock, stock_quantity, 0) 
WHERE current_stock IS NULL OR current_stock = 0;
