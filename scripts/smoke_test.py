#!/usr/bin/env python3
"""Smoke test script: creates minimal schema, then runs create->order->confirm->invoice->payment flow."""
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))

from core.database_manager import DatabaseManager
from services.product_service_enhanced import ProductService
from models.product_enhanced import Product as EnhancedProduct
from services.sales_service_enhanced import SalesService
from services.billing_service import BillingService


def ensure_tables(db):
    # load migration SQL files in order
    migrations = [
        ROOT / 'migrations' / '001_create_enhanced_tables.sql',
        ROOT / 'migrations' / '002_add_missing_columns.sql'
    ]
    
    for mig_file in migrations:
        if mig_file.exists():
            sql = mig_file.read_text(encoding='utf-8')
            # split by semicolon; execute statements that are not empty
            for stmt in sql.split(';'):
                s = stmt.strip()
                if s:
                    try:
                        db.execute_query(s)
                    except Exception as e:
                        # ALTER TABLE ... ADD COLUMN may fail if column exists; this is OK
                        if 'duplicate column' not in str(e).lower() and 'already exists' not in str(e).lower():
                            print('WARN: failed to execute statement:', e)
        else:
            print(f'Migration file {mig_file.name} not found; continuing')
    return True


def run():
    print('Starting smoke test...')
    db = DatabaseManager(':memory:')
    # initialize opens the sqlite connection and creates core tables
    db.initialize()

    ok = ensure_tables(db)
    if not ok:
        print('Failed to ensure tables')
        return

    # instantiate services
    product_svc = ProductService(db)
    inventory_svc = None
    try:
        from services.inventory_service_enhanced import InventoryService
        inventory_svc = InventoryService(db)
    except Exception:
        inventory_svc = None

    sales_svc = SalesService(db, inventory_service=inventory_svc, product_service=product_svc)
    billing = BillingService(db)

    # create product
    p = EnhancedProduct(
        name='Test Product',
        sku='SMOKE-001',
        barcode='000001',
        cost_price=Decimal('50.00'),
        base_price=Decimal('100.00'),
        current_stock=10,
        min_stock=1,
        is_active=True
    )

    print('Creating product...')
    pid = product_svc.create_product(p)
    print('Product id:', pid)

    # create order
    items = [{'product_id': pid, 'quantity': 2, 'unit_price': 100}]
    print('Creating order...')
    order_id = sales_svc.create_order(customer_id=None, items=items)
    print('Order id:', order_id)

    # confirm order
    print('Confirming order...')
    confirmed = sales_svc.confirm_order(order_id)
    print('Order confirmed:', confirmed)

    # generate invoice
    print('Generating invoice...')
    invoice_id = billing.generate_invoice(order_id)
    print('Invoice id:', invoice_id)

    # record payment
    if invoice_id:
        print('Recording payment...')
        paid = billing.record_payment(invoice_id, Decimal('200.00'), method='cash', reference=None)
        print('Payment recorded:', paid)

    print('Smoke test finished')


if __name__ == '__main__':
    run()
