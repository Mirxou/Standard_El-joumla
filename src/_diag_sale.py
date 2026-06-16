import sys

sys.path.insert(0, ".")
from decimal import Decimal

from src.core.local_database_manager import LocalDatabaseManager
from src.models.product import Product
from src.models.sale import PaymentMethod, Sale, SaleItem, SaleStatus
from src.services.inventory_service import InventoryService
from src.services.sales_service import SalesService

db = LocalDatabaseManager(":memory:")
db.initialize()
db.execute_non_query("INSERT OR IGNORE INTO categories(id,name,is_active) VALUES(1,'g',1)")
db.execute_non_query(
    "INSERT OR IGNORE INTO chart_of_accounts(account_code,account_name,account_type,is_active) VALUES('1010','AR','Asset',1)"  # noqa: E501
)
db.execute_non_query(
    "INSERT OR IGNORE INTO chart_of_accounts(account_code,account_name,account_type,is_active) VALUES('4001','Rev','Revenue',1)"  # noqa: E501
)
db.execute_non_query(
    "INSERT OR IGNORE INTO chart_of_accounts(account_code,account_name,account_type,is_active) VALUES('2010','VAT','Liability',1)"  # noqa: E501
)

inv = InventoryService(db)
pid = inv.add_product(
    Product(
        barcode="B1",
        name="P1",
        cost_price=Decimal("10"),
        selling_price=Decimal("15"),
        current_stock=100,
        min_stock=5,
        is_active=True,
    )
)
print(f"product_id={pid}")

svc = SalesService(db)
item = SaleItem(product_id=pid, quantity=5, unit_price=Decimal("15"), total_price=Decimal("75"))
sale = Sale(
    items=[item],
    total_amount=Decimal("75"),
    payment_method=PaymentMethod.CASH,
    status=SaleStatus.CONFIRMED,
)
sid = svc.create_sale(sale)
print(f"sale_id={sid}")
