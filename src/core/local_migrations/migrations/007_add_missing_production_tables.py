import logging
def upgrade(db_manager) -> bool:
    """إضافة جداول الإنتاج المفقودة (أوامر الشراء، خطط الدفع، وتوسيع المنتجات)"""
    queries = [
        """
        CREATE TABLE IF NOT EXISTS user_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            permission TEXT NOT NULL,
            granted_by INTEGER,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """,
        """
        ALTER TABLE sale_items ADD COLUMN discount DECIMAL(10, 2) DEFAULT 0.00;
        """,
        """
        ALTER TABLE sale_items ADD COLUMN tax_amount DECIMAL(10, 2) DEFAULT 0.00;
        """,
        """
        ALTER TABLE products ADD COLUMN sku TEXT;
        """,
        """
        ALTER TABLE products ADD COLUMN supplier_id INTEGER;
        """,
        """
        ALTER TABLE products ADD COLUMN product_type TEXT;
        """,
        """
        ALTER TABLE products ADD COLUMN specifications TEXT;
        """,
        """
        ALTER TABLE products ADD COLUMN base_price DECIMAL(10, 2);
        """,
        """
        ALTER TABLE products ADD COLUMN pricing_policy TEXT;
        """,
        """
        ALTER TABLE products ADD COLUMN reserved_stock DECIMAL(10, 2) DEFAULT 0;
        """,
        """
        ALTER TABLE products ADD COLUMN reorder_point DECIMAL(10, 2);
        """,
        """
        ALTER TABLE products ADD COLUMN max_stock DECIMAL(10, 2);
        """,
        """
        ALTER TABLE products ADD COLUMN images TEXT;
        """,
        """
        ALTER TABLE products ADD COLUMN tags TEXT;
        """,
        """
        ALTER TABLE products ADD COLUMN is_discontinued INTEGER DEFAULT 0;
        """,
        """
        ALTER TABLE products ADD COLUMN is_featured INTEGER DEFAULT 0;
        """,
        """
        ALTER TABLE products ADD COLUMN discontinued_date TIMESTAMP;
        """,
        """
        ALTER TABLE products ADD COLUMN sales_count INTEGER DEFAULT 0;
        """,
        """
        ALTER TABLE products ADD COLUMN total_sold DECIMAL(10, 2) DEFAULT 0;
        """,
        """
        ALTER TABLE products ADD COLUMN average_rating DECIMAL(3, 2) DEFAULT 0;
        """,
        """
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT UNIQUE NOT NULL,
            supplier_id INTEGER NOT NULL,
            supplier_name TEXT,
            supplier_contact TEXT,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            required_date TIMESTAMP,
            delivery_date TIMESTAMP,
            expected_delivery_date TIMESTAMP,
            status TEXT DEFAULT 'DRAFT',
            priority TEXT,
            delivery_terms TEXT,
            payment_terms TEXT,
            currency TEXT,
            subtotal DECIMAL(10, 2) DEFAULT 0.00,
            discount_amount DECIMAL(10, 2) DEFAULT 0.00,
            tax_amount DECIMAL(10, 2) DEFAULT 0.00,
            shipping_cost DECIMAL(10, 2) DEFAULT 0.00,
            total_amount DECIMAL(10, 2) DEFAULT 0.00,
            notes TEXT,
            terms_conditions TEXT,
            shipping_address TEXT,
            billing_address TEXT,
            approved_by INTEGER,
            approval_date TIMESTAMP,
            sent_date TIMESTAMP,
            confirmed_date TIMESTAMP,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT,
            sku TEXT,
            description TEXT,
            quantity DECIMAL(10, 2) NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            discount_amount DECIMAL(10, 2) DEFAULT 0.00,
            tax_amount DECIMAL(10, 2) DEFAULT 0.00,
            total_price DECIMAL(10, 2) NOT NULL,
            received_qty DECIMAL(10, 2) DEFAULT 0.00,
            FOREIGN KEY(po_id) REFERENCES purchase_orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS payment_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_number TEXT UNIQUE NOT NULL,
            invoice_id INTEGER,
            invoice_number TEXT,
            customer_id INTEGER,
            customer_name TEXT NOT NULL,
            plan_name TEXT,
            description TEXT,
            total_amount DECIMAL(10, 2) NOT NULL,
            down_payment DECIMAL(10, 2) NOT NULL,
            financed_amount DECIMAL(10, 2),
            number_of_installments INTEGER NOT NULL,
            installment_amount DECIMAL(10, 2) NOT NULL,
            frequency TEXT,
            interest_rate DECIMAL(5, 2),
            total_interest DECIMAL(10, 2),
            late_fee_type TEXT,
            late_fee_value DECIMAL(10, 2),
            grace_period_days INTEGER,
            start_date DATE NOT NULL,
            end_date DATE,
            status TEXT DEFAULT 'ACTIVE',
            total_paid DECIMAL(10, 2) DEFAULT 0.00,
            total_remaining DECIMAL(10, 2) DEFAULT 0.00,
            total_late_fees DECIMAL(10, 2) DEFAULT 0.00,
            notes TEXT,
            terms_conditions TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS payment_installments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_plan_id INTEGER NOT NULL,
            installment_number INTEGER NOT NULL,
            principal_amount DECIMAL(10, 2),
            interest_amount DECIMAL(10, 2),
            due_date DATE NOT NULL,
            status TEXT DEFAULT 'PENDING',
            amount_paid DECIMAL(10, 2) DEFAULT 0.00,
            remaining_amount DECIMAL(10, 2) DEFAULT 0.00,
            payment_date TIMESTAMP,
            late_fee DECIMAL(10, 2) DEFAULT 0.00,
            total_amount DECIMAL(10, 2) DEFAULT 0.00,
            payment_method TEXT,
            payment_reference TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(payment_plan_id) REFERENCES payment_plans(id)
        )
        """,
    ]

    try:
        for query in queries:
            try:
                db_manager.execute_update(query)
            except Exception:
                # ignore duplicate column errors
                logging.getLogger(__name__).warning("Ignored exception in 007_add_missing_production_tables.py")
        return True
    except Exception as e:
        db_manager.logger.error(f"Error applying migration 007: {e}")
        return False


def downgrade(db_manager) -> bool:
    return True
