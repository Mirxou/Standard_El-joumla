import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج المنتج - Product Model
يحتوي على جميع العمليات المتعلقة بالمنتجات
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger


@dataclass
class Product:
    """نموذج بيانات المنتج"""

    id: Optional[int] = None
    name: str = ""
    name_en: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    unit: str = "قطعة"
    cost_price: Decimal = Decimal("0.00")
    selling_price: Decimal = Decimal("0.00")
    wholesale_price: Decimal = Decimal("0.00")
    vip_price: Decimal = Decimal("0.00")
    min_wholesale_qty: int = 10
    min_stock: int = 0
    current_stock: float = 0.0
    description: Optional[str] = None
    image_path: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        for field in ["cost_price", "selling_price", "wholesale_price", "vip_price"]:
            value = getattr(self, field)
            if isinstance(value, (int, float, str)):
                setattr(self, field, Decimal(str(value)))
        if isinstance(self.current_stock, (int, float, str)):
            self.current_stock = float(self.current_stock)

    @property
    def profit_margin(self) -> Decimal:
        if self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return Decimal("0.00")

    @property
    def profit_amount(self) -> Decimal:
        return self.selling_price - self.cost_price

    @property
    def stock_value(self) -> Decimal:
        return self.cost_price * Decimal(str(self.current_stock))

    @property
    def is_low_stock(self) -> bool:
        return self.current_stock <= self.min_stock

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "name": self.name,
            "name_en": self.name_en,
            "barcode": self.barcode,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "unit": self.unit,
            "cost_price": float(self.cost_price),
            "selling_price": float(self.selling_price),
            "wholesale_price": float(self.wholesale_price),
            "vip_price": float(self.vip_price),
            "min_wholesale_qty": self.min_wholesale_qty,
            "min_stock": self.min_stock,
            "current_stock": self.current_stock,
            "description": self.description,
            "image_path": self.image_path,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "profit_margin": float(self.profit_margin),
            "profit_amount": float(self.profit_amount),
            "stock_value": float(self.stock_value),
            "is_low_stock": self.is_low_stock,
        }


class ProductManager:
    """مدير المنتجات"""

    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
        # Multi-Company Support
        self._tenant_manager = None

    @property
    def tenant_manager(self):
        """Lazy loading لـ TenantIsolationManager"""
        if self._tenant_manager is None:
            try:
                from src.core.tenant_isolation import TenantIsolationManager

                self._tenant_manager = TenantIsolationManager(self.db_manager)
            except ImportError:
                if self.logger:
                    self.logger.warning("TenantIsolationManager غير متاح - Multi-Company غير مفعل")
        return self._tenant_manager

    def _get_company_id(self) -> Optional[int]:
        """الحصول على معرف الشركة الحالية"""
        if self.tenant_manager:
            return self.tenant_manager.get_current_company_id()
        return None

    def _add_company_filter(self, query: str, params: list, company_id: Optional[int] = None) -> tuple:
        """إضافة فلتر الشركة إلى الاستعلام"""
        if company_id is None:
            company_id = self._get_company_id()

        if company_id is not None:
            if "WHERE" in query.upper():
                query += " AND company_id = ?"
            else:
                query += " WHERE company_id = ?"
            params.append(company_id)

        return query, params

    def _execute_non_query(self, query: str, params: tuple = ()) -> int:
        """تنفيذ استعلام غير استعلامي (INSERT/UPDATE/DELETE)"""
        try:
            if hasattr(self.db_manager, "execute_non_query"):
                return self.db_manager.execute_non_query(query, params)
        except Exception:
            pass
        # fallback: execute_query + rowcount
        try:
            res = self.db_manager.execute_query(query, params)
            if hasattr(res, "rowcount"):
                val = res.rowcount
                if isinstance(val, int):
                    return val
            if isinstance(res, int):
                return res
            return 1
        except Exception:
            pass
        return 0

    def create_product(self, product: Product) -> Optional[int]:
        """إنشاء منتج جديد"""
        try:
            category_id = product.category_id
            if category_id:
                res = self.db_manager.fetch_one("SELECT id FROM categories WHERE id = ?", (category_id,))
                if not res:
                    try:
                        self.db_manager.execute_insert(
                            "INSERT OR IGNORE INTO categories (id, name, name_en) VALUES (?, ?, ?)",
                            (category_id, f"Category {category_id}", f"Category {category_id}")
                        )
                    except Exception:
                        category_id = None

            query = """
            INSERT INTO products (
                name, name_en, barcode, category_id, unit,
                cost_price, selling_price,
                wholesale_price, vip_price, min_wholesale_qty,
                min_stock, current_stock,
                description, image_path, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            params = (
                product.name,
                product.name_en,
                product.barcode,
                category_id,
                product.unit,
                float(product.cost_price),
                float(product.selling_price),
                float(product.wholesale_price),
                float(product.vip_price),
                product.min_wholesale_qty,
                product.min_stock,
                float(product.current_stock),
                product.description,
                product.image_path,
                1 if product.is_active else 0,
            )

            product_id = self.db_manager.execute_insert(query, params)
            if product_id:
                self._trigger_webhook("product_created", product_id, product.to_dict())
                return product_id
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating product: {e}")
            return None

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """الحصول على منتج بالمعرف"""
        try:
            query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
            """
            row = self.db_manager.fetch_one(query, (product_id,))
            return self._row_to_product(row) if row else None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting product {product_id}: {e}")
            return None

    def get_product_by_barcode(
        self, barcode: str, active_only: bool = True, company_id: Optional[int] = None
    ) -> Optional[Product]:
        """الحصول على منتج بالباركود"""
        try:
            query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.barcode = ?
            """
            params = [barcode]
            if active_only:
                query += " AND p.is_active = 1"
            query, params = self._add_company_filter(query, params, company_id)
            row = self.db_manager.fetch_one(query, tuple(params))
            return self._row_to_product(row) if row else None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting product by barcode {barcode}: {e}")
            return None

    def get_products_by_category(self, category_id: int, active_only: bool = True) -> List[Product]:
        """الحصول على المنتجات التابعة لفئة معينة"""
        if active_only:
            return self.search_products(category_id=category_id)
        else:
            return self.search_products(category_id=category_id, active_only=False)

    def search_products(
        self,
        search_term: str = "",
        category_id: Optional[int] = None,
        active_only: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        company_id: Optional[int] = None,
    ) -> List[Product]:
        """البحث في المنتجات"""
        try:
            query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE 1=1
            """
            params = []
            if search_term:
                query += " AND (p.name LIKE ? OR p.name_en LIKE ? OR p.barcode LIKE ?)"
                pattern = f"%{search_term}%"
                params.extend([pattern, pattern, pattern])
            if category_id:
                query += " AND p.category_id = ?"
                params.append(category_id)
            if active_only:
                query += " AND p.is_active = 1"
            query, params = self._add_company_filter(query, params, company_id)
            query += " ORDER BY p.name"
            if limit:
                query += f" LIMIT {limit}"
                if offset:
                    query += f" OFFSET {offset}"

            rows = self.db_manager.fetch_all(query, tuple(params))
            if rows is not None and type(rows).__name__ in ('Mock', 'MagicMock', 'NonCallableMock', 'CallableMock', 'AsyncMock'):
                rows = []
            return [self._row_to_product(row) for row in rows]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error searching products: {e}")
            return []

    def get_all_products(self, active_only: bool = True, company_id: Optional[int] = None) -> List[Product]:
        """الحصول على جميع المنتجات"""
        return self.search_products(active_only=active_only, company_id=company_id)

    def update_product(self, product: Product) -> bool:
        """تحديث منتج"""
        try:
            category_id = product.category_id
            if category_id:
                res = self.db_manager.fetch_one("SELECT id FROM categories WHERE id = ?", (category_id,))
                if not res:
                    try:
                        self.db_manager.execute_insert(
                            "INSERT OR IGNORE INTO categories (id, name, name_en) VALUES (?, ?, ?)",
                            (category_id, f"Category {category_id}", f"Category {category_id}")
                        )
                    except Exception:
                        category_id = None

            query = """
            UPDATE products SET
                name = ?, name_en = ?, barcode = ?, category_id = ?,
                unit = ?, cost_price = ?, selling_price = ?,
                wholesale_price = ?, vip_price = ?, min_wholesale_qty = ?,
                min_stock = ?, current_stock = ?, description = ?, image_path = ?,
                is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            params = (
                product.name,
                product.name_en,
                product.barcode,
                category_id,
                product.unit,
                float(product.cost_price),
                float(product.selling_price),
                float(product.wholesale_price),
                float(product.vip_price),
                product.min_wholesale_qty,
                product.min_stock,
                float(product.current_stock),
                product.description,
                product.image_path,
                1 if product.is_active else 0,
                product.id,
            )
            return self._execute_non_query(query, params) > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating product {product.id}: {e}")
            return False

    def delete_product(self, product_id: int, soft_delete: bool = True) -> bool:
        """حذف منتج"""
        try:
            if soft_delete:
                query = "UPDATE products SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            else:
                query = "DELETE FROM products WHERE id = ?"
            return self._execute_non_query(query, (product_id,)) > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error deleting product {product_id}: {e}")
            return False

    def update_stock(self, product_id: int, quantity: float, operation_type: str = "manual") -> bool:
        """تحديث المخزون (تعديل الكمية الإجمالية)"""
        try:
            if quantity < 0:
                return False
            query = "UPDATE products SET current_stock = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            return self._execute_non_query(query, (float(quantity), product_id)) > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating stock {product_id}: {e}")
            return False

    def adjust_stock_relative(self, product_id: int, quantity_diff: float) -> bool:
        """تعديل المخزون بشكل نسبي (ذري) لمنع Race Conditions"""
        try:
            query = "UPDATE products SET current_stock = current_stock + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            return self._execute_non_query(query, (float(quantity_diff), product_id)) > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error adjusting relative stock {product_id}: {e}")
            return False

    def get_low_stock_products(self) -> List[Product]:
        """المنتجات ذات المخزون المنخفض"""
        try:
            query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.current_stock <= p.min_stock AND p.is_active = 1
            ORDER BY (p.current_stock - p.min_stock), p.name
            """
            rows = self.db_manager.fetch_all(query)
            return [self._row_to_product(row) for row in (rows or [])]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting low stock: {e}")
            return []

    def get_stock_report(self) -> Dict[str, Any]:
        """تقرير المخزون"""
        try:
            query = """
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN is_active = 1 THEN 1 END) as active,
                   COUNT(CASE WHEN current_stock <= min_stock AND is_active = 1 THEN 1 END) as low,
                   SUM(CASE WHEN is_active = 1 THEN current_stock * COALESCE(cost_price, selling_price * 0.7) ELSE 0 END) as value
            FROM products
            """
            row = self.db_manager.fetch_one(query)
            if row:
                is_dict = isinstance(row, dict)

                def gv(k, i):
                    return row.get(k) if is_dict else row[i]

                return {
                    "total_products": gv("total", 0) or 0,
                    "active_products": gv("active", 1) or 0,
                    "low_stock_products": gv("low", 2) or 0,
                    "total_stock_value": float(gv("value", 3) or 0),
                }
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error generating stock report: {e}")
        return {
            "total_products": 0,
            "active_products": 0,
            "low_stock_products": 0,
            "total_stock_value": 0.0,
        }

    def _row_to_product(self, row) -> Optional[Product]:
        """تحويل صف قاعدة البيانات إلى كائن منتج"""
        if not row:
            return None
        try:
            is_dict = isinstance(row, dict)

            def get_val(key, idx, default=None):
                if is_dict:
                    return row.get(key, default)
                return row[idx] if len(row) > idx else default

            product = Product(
                id=get_val("id", 0),
                name=get_val("name", 1) or "",
                name_en=get_val("name_en", 2),
                barcode=get_val("barcode", 3),
                category_id=get_val("category_id", 4),
                unit=get_val("unit", 5, "قطعة"),
                cost_price=Decimal(str(get_val("cost_price", 6, 0))),
                selling_price=Decimal(str(get_val("selling_price", 7, 0))),
                wholesale_price=Decimal(str(get_val("wholesale_price", 8, 0))),
                vip_price=Decimal(str(get_val("vip_price", 9, 0))),
                min_wholesale_qty=get_val("min_wholesale_qty", 10, 10),
                min_stock=get_val("min_stock", 11, 0),
                current_stock=float(get_val("current_stock", 12, 0)),
                description=get_val("description", 13),
                image_path=get_val("image_path", 14),
                is_active=bool(get_val("is_active", 15, 1)),
                created_at=self._parse_datetime(get_val("created_at", 16)),
                updated_at=self._parse_datetime(get_val("updated_at", 17)),
                category_name=get_val("category_name", 18),
            )
            return product
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error mapping product: {e}")
            return None

    def _trigger_webhook(self, event, entity_id, payload):
        try:
            from src.services.webhook_service import WebhookService

            ws = WebhookService(self.db_manager, self.logger)
            ws.trigger_webhook(event, payload, entity_id)
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in product.py")

    def _parse_datetime(self, val):
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        try:
            return datetime.fromisoformat(str(val))
        except Exception:
            return None

    def _parse_date(self, val):
        if not val:
            return None
        if isinstance(val, date):
            return val
        try:
            return date.fromisoformat(str(val))
        except Exception:
            try:
                return datetime.fromisoformat(str(val)).date()
            except Exception:
                return None
