-- Migration 014: Align product_variants stock column
PRAGMA foreign_keys = ON;

-- Add current_stock if missing
ALTER TABLE product_variants ADD COLUMN current_stock INTEGER DEFAULT 0;

-- Initialize current_stock from legacy stock_quantity when available
UPDATE product_variants SET current_stock = COALESCE(current_stock, stock_quantity, 0);
