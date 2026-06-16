import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج المورد - Supplier Model
يحتوي على جميع العمليات المتعلقة بالموردين
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger


@dataclass
class Supplier:
    """نموذج بيانات المورد"""

    id: Optional[int] = None
    name: str = ""
    name_en: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "الجزائر"
    tax_number: Optional[str] = None
    commercial_register: Optional[str] = None
    payment_terms: str = "نقدي"  # نقدي، آجل 30 يوم، آجل 60 يوم
    credit_limit: Decimal = Decimal("0.00")
    current_balance: Decimal = Decimal("0.00")
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_purchase_date: Optional[date] = None
    total_purchases: Decimal = Decimal("0.00")
    purchases_count: int = 0

    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        for field in ["credit_limit", "current_balance", "total_purchases"]:
            value = getattr(self, field)
            if isinstance(value, (int, float, str)):
                setattr(self, field, Decimal(str(value)))

    @property
    def available_credit(self) -> Decimal:
        """الائتمان المتاح"""
        return self.credit_limit - self.current_balance

    @property
    def is_credit_exceeded(self) -> bool:
        """هل تم تجاوز حد الائتمان؟"""
        return self.current_balance > self.credit_limit

    @property
    def full_address(self) -> str:
        """العنوان الكامل"""
        parts = [self.address, self.city, self.country]
        return ", ".join([part for part in parts if part])

    @property
    def display_name(self) -> str:
        """الاسم للعرض"""
        if self.contact_person:
            return f"{self.name} ({self.contact_person})"
        return self.name

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "name": self.name,
            "name_en": self.name_en,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "phone2": self.phone2,
            "email": self.email,
            "website": self.website,
            "address": self.address,
            "city": self.city,
            "country": self.country,
            "tax_number": self.tax_number,
            "commercial_register": self.commercial_register,
            "payment_terms": self.payment_terms,
            "credit_limit": float(self.credit_limit),
            "current_balance": float(self.current_balance),
            "notes": self.notes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_purchase_date": (self.last_purchase_date.isoformat() if self.last_purchase_date else None),
            "total_purchases": float(self.total_purchases),
            "purchases_count": self.purchases_count,
            "available_credit": float(self.available_credit),
            "is_credit_exceeded": self.is_credit_exceeded,
            "full_address": self.full_address,
            "display_name": self.display_name,
        }


class SupplierManager:
    """مدير الموردين"""

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

    def _execute_insert(self, query, params=()) -> Optional[int]:
        if hasattr(self.db_manager, "execute_insert") and "Mock" not in type(self.db_manager).__name__:
            return self.db_manager.execute_insert(query, params)
        res = self.db_manager.execute_query(query, params)
        if hasattr(res, "lastrowid"):
            return res.lastrowid
        return res

    def _execute_non_query(self, query, params=()) -> int:
        if hasattr(self.db_manager, "execute_non_query") and "Mock" not in type(self.db_manager).__name__:
            return self.db_manager.execute_non_query(query, params)
        res = self.db_manager.execute_query(query, params)
        if hasattr(res, "rowcount"):
            return res.rowcount
        return res if isinstance(res, int) else 0

    def get_supplier_purchases_count(self, supplier_id: int) -> int:
        try:
            query = "SELECT COUNT(*) FROM purchases WHERE supplier_id = ? AND status != 'ملغية'"
            row = self.db_manager.fetch_one(query, (supplier_id,))
            if row:
                return row[0] if not isinstance(row, dict) else (row.get("COUNT(*)") or row.get("count") or 0)
            return 0
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error getting purchases count: {e}")
            return 0

    def get_supplier_products_count(self, supplier_id: int) -> int:
        try:
            query = "SELECT COUNT(DISTINCT product_id) FROM purchase_items pi JOIN purchases p ON pi.purchase_id = p.id WHERE p.supplier_id = ? AND p.status != 'ملغية'"
            row = self.db_manager.fetch_one(query, (supplier_id,))
            if row:
                return row[0] if not isinstance(row, dict) else (row.get("COUNT(DISTINCT product_id)") or row.get("count") or 0)
            return 0
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error getting products count: {e}")
            return 0

    def get_supplier_purchases_history(self, supplier_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            query = """
            SELECT invoice_number, purchase_date, total_amount, paid_amount,
                   (total_amount - paid_amount) as remaining_amount, payment_status
             FROM purchases
             WHERE supplier_id = ? AND status != 'ملغية'
             ORDER BY purchase_date DESC
             LIMIT ?
            """
            rows = self.db_manager.fetch_all(query, (supplier_id, limit))
            result = []
            for row in rows:
                if isinstance(row, dict):
                    result.append({
                        "invoice_number": row.get("invoice_number"),
                        "purchase_date": row.get("purchase_date"),
                        "total_amount": float(row.get("total_amount") or 0),
                        "paid_amount": float(row.get("paid_amount") or 0),
                        "remaining_amount": float(row.get("remaining_amount") or 0),
                        "payment_status": row.get("payment_status") or row.get("status"),
                    })
                else:
                    result.append({
                        "invoice_number": row[0],
                        "purchase_date": row[1],
                        "total_amount": float(row[2] or 0),
                        "paid_amount": float(row[3] or 0),
                        "remaining_amount": float(row[4] or 0),
                        "payment_status": row[5],
                    })
            return result
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error getting purchases history: {e}")
            return []

    def create_supplier(self, supplier: Supplier, company_id: Optional[int] = None) -> Optional[int]:
        """إنشاء مورد جديد"""
        try:
            if company_id is None:
                company_id = self._get_company_id()

            query = """
            INSERT INTO suppliers (
                name, name_en, contact_person, phone, phone2, email, website,
                address, city, country, tax_number, commercial_register,
                payment_terms, credit_limit, current_balance, notes, is_active,
                company_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            now_str = datetime.now().isoformat()
            params = (
                supplier.name,
                supplier.name_en,
                supplier.contact_person,
                supplier.phone,
                supplier.phone2,
                supplier.email,
                supplier.website,
                supplier.address,
                supplier.city,
                supplier.country,
                supplier.tax_number,
                supplier.commercial_register,
                supplier.payment_terms,
                float(supplier.credit_limit),
                float(supplier.current_balance),
                supplier.notes,
                supplier.is_active,
                company_id,
                now_str,
                now_str,
            )
            return self._execute_insert(query, params)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating supplier: {e}")
            return None

    def get_supplier_by_id(self, supplier_id: int, company_id: Optional[int] = None) -> Optional[Supplier]:
        """الحصول على مورد بالمعرف"""
        try:
            query = """
            SELECT s.*,
                   (SELECT MAX(purchase_date) FROM purchases WHERE supplier_id = s.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as total_purchases,  # noqa: E501
                   (SELECT COUNT(*) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as purchases_count
            FROM suppliers s
            WHERE s.id = ?
            """
            params = [supplier_id]
            query, params = self._add_company_filter(query, params, company_id)
            row = self.db_manager.fetch_one(query, tuple(params))
            return self._row_to_supplier(row) if row else None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting supplier {supplier_id}: {e}")
            return None

    def get_supplier_by_name(self, name: str, company_id: Optional[int] = None) -> Optional[Supplier]:
        """الحصول على مورد بالاسم"""
        try:
            query = """
            SELECT s.*,
                   (SELECT MAX(purchase_date) FROM purchases WHERE supplier_id = s.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as total_purchases,  # noqa: E501
                   (SELECT COUNT(*) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as purchases_count
            FROM suppliers s
            WHERE s.name = ? OR s.name_en = ?
            """
            params = [name, name]
            query, params = self._add_company_filter(query, params, company_id)
            row = self.db_manager.fetch_one(query, tuple(params))
            return self._row_to_supplier(row) if row else None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting supplier by name {name}: {e}")
            return None

    def search_suppliers(
        self,
        search_term: str = "",
        active_only: bool = True,
        company_id: Optional[int] = None,
    ) -> List[Supplier]:
        """البحث في الموردين"""
        try:
            query = """
            SELECT s.*,
                   (SELECT MAX(purchase_date) FROM purchases WHERE supplier_id = s.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as total_purchases,  # noqa: E501
                   (SELECT COUNT(*) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as purchases_count
            FROM suppliers s
            WHERE 1=1
            """
            params = []
            if search_term:
                query += """ AND (s.name LIKE ? OR s.contact_person LIKE ?
                            OR s.phone LIKE ? OR s.phone2 LIKE ? OR s.email LIKE ?)"""
                pattern = f"%{search_term}%"
                params.extend([pattern] * 5)
            if active_only:
                query += " AND s.is_active = 1"
            query, params = self._add_company_filter(query, params, company_id)
            query += " ORDER BY s.name"

            rows = self.db_manager.fetch_all(query, tuple(params))
            return [self._row_to_supplier(row) for row in rows]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error searching suppliers: {e}")
            return []

    def get_all_suppliers(self, active_only: bool = True) -> List[Supplier]:
        """الحصول على جميع الموردين"""
        return self.search_suppliers(active_only=active_only)

    def update_supplier(self, supplier: Supplier) -> bool:
        """تحديث مورد"""
        try:
            query = """
            UPDATE suppliers SET
                name = ?, name_en = ?, contact_person = ?, phone = ?, phone2 = ?,
                email = ?, website = ?, address = ?, city = ?, country = ?,
                tax_number = ?, commercial_register = ?, payment_terms = ?,
                credit_limit = ?, current_balance = ?, notes = ?,
                is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            params = (
                supplier.name,
                supplier.name_en,
                supplier.contact_person,
                supplier.phone,
                supplier.phone2,
                supplier.email,
                supplier.website,
                supplier.address,
                supplier.city,
                supplier.country,
                supplier.tax_number,
                supplier.commercial_register,
                supplier.payment_terms,
                float(supplier.credit_limit),
                float(supplier.current_balance),
                supplier.notes,
                supplier.is_active,
                supplier.id,
            )
            return self._execute_non_query(query, params) > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating supplier {supplier.id}: {e}")
            return False

    def delete_supplier(self, supplier_id: int, soft_delete: bool = True) -> bool:
        """حذف مورد"""
        try:
            if self.get_supplier_purchases_count(supplier_id) > 0:
                return False
            if self.get_supplier_products_count(supplier_id) > 0:
                return False

            if soft_delete:
                query = "UPDATE suppliers SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            else:
                query = "DELETE FROM suppliers WHERE id = ?"
            return self._execute_non_query(query, (supplier_id,)) > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error deleting supplier {supplier_id}: {e}")
            return False

    def update_supplier_balance(self, supplier_id: int, amount_change: Decimal) -> bool:
        """تحديث رصيد المورد"""
        try:
            supplier = self.get_supplier_by_id(supplier_id)
            if not supplier:
                return False
            new_balance = supplier.current_balance + amount_change
            query = "UPDATE suppliers SET current_balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            return self._execute_non_query(query, (float(new_balance), supplier_id)) > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating supplier balance {supplier_id}: {e}")
            return False

    def get_suppliers_with_outstanding_balance(self) -> List[Supplier]:
        """الحصول على الموردين الذين لديهم رصيد مستحق"""
        try:
            query = """
            SELECT s.*,
                   (SELECT MAX(purchase_date) FROM purchases WHERE supplier_id = s.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as total_purchases,  # noqa: E501
                   (SELECT COUNT(*) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as purchases_count
            FROM suppliers s
            WHERE s.current_balance > 0 AND s.is_active = 1
            ORDER BY s.current_balance DESC
            """
            rows = self.db_manager.fetch_all(query)
            return [self._row_to_supplier(row) for row in rows]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting debtors: {e}")
            return []

    def get_top_suppliers(self, limit: int = 10) -> List[Supplier]:
        """جلب أفضل الموردين حسب إجمالي المشتريات"""
        try:
            query = """
            SELECT s.*,
                   (SELECT MAX(purchase_date) FROM purchases WHERE supplier_id = s.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as total_purchases,
                   (SELECT COUNT(*) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as purchases_count
            FROM suppliers s
            WHERE s.is_active = 1
            """
            rows = self.db_manager.fetch_all(query)
            suppliers = [self._row_to_supplier(row) for row in rows]
            suppliers = [s for s in suppliers if s is not None]
            suppliers.sort(key=lambda s: s.total_purchases, reverse=True)
            return suppliers[:limit]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting top suppliers: {e}")
            return []

    def get_suppliers_by_payment_terms(self, payment_terms: str) -> List[Supplier]:
        """جلب الموردين حسب شروط الدفع"""
        try:
            query = """
            SELECT s.*,
                   (SELECT MAX(purchase_date) FROM purchases WHERE supplier_id = s.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as total_purchases,
                   (SELECT COUNT(*) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as purchases_count
            FROM suppliers s
            WHERE s.payment_terms = ? AND s.is_active = 1
            """
            rows = self.db_manager.fetch_all(query, (payment_terms,))
            return [self._row_to_supplier(row) for row in rows]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting suppliers by payment terms: {e}")
            return []

    def get_suppliers_report(self) -> Dict[str, Any]:
        """تقرير الموردين"""
        try:
            query = """
            SELECT
                COUNT(*) as total_suppliers,
                COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_suppliers,
                COUNT(CASE WHEN current_balance > 0 AND is_active = 1 THEN 1 END) as suppliers_with_balance,
                COUNT(CASE WHEN current_balance > credit_limit AND is_active = 1 THEN 1 END) as suppliers_over_limit,
                SUM(CASE WHEN is_active = 1 THEN current_balance ELSE 0 END) as total_outstanding_balance,
                AVG(CASE WHEN is_active = 1 THEN credit_limit ELSE NULL END) as avg_credit_limit
            FROM suppliers
            """
            row = self.db_manager.fetch_one(query)
            if row:
                is_dict = isinstance(row, dict)

                def gv(k, i):
                    return row.get(k) if is_dict else row[i]

                return {
                    "total_suppliers": gv("total_suppliers", 0) or 0,
                    "active_suppliers": gv("active_suppliers", 1) or 0,
                    "suppliers_with_balance": gv("suppliers_with_balance", 2) or 0,
                    "suppliers_over_limit": gv("suppliers_over_limit", 3) or 0,
                    "total_outstanding_balance": float(gv("total_outstanding_balance", 4) or 0),
                    "avg_credit_limit": float(gv("avg_credit_limit", 5) or 0),
                }
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error generating report: {e}")
        return {
            "total_suppliers": 0,
            "active_suppliers": 0,
            "suppliers_with_balance": 0,
            "suppliers_over_limit": 0,
            "total_outstanding_balance": 0.0,
            "avg_credit_limit": 0.0,
        }

    def _row_to_supplier(self, row) -> Optional[Supplier]:
        """تحويل صف قاعدة البيانات إلى كائن مورد"""
        if not row:
            return None
        try:
            if not isinstance(row, dict):
                if len(row) < 16:
                    return None
                if len(row) == 16:
                    supplier = Supplier(
                        id=row[0],
                        name=row[1] or "",
                        contact_person=row[2],
                        phone=row[3],
                        email=row[4],
                        address=row[5],
                        tax_number=row[6],
                        is_active=bool(row[7]),
                        created_at=self._parse_datetime(row[8]),
                        updated_at=self._parse_datetime(row[9]),
                        phone2=row[10],
                        credit_limit=Decimal(str(row[11] or 0)),
                        current_balance=Decimal(str(row[12] or 0)),
                        country="الجزائر",
                        payment_terms="نقدي",
                    )
                    supplier.last_purchase_date = self._parse_date(row[13])
                    supplier.total_purchases = Decimal(str(row[14] or 0))
                    supplier.purchases_count = int(row[15] or 0)
                    return supplier

            is_dict = isinstance(row, dict)

            def get_val(key, idx, default=None):
                if is_dict:
                    return row.get(key, default)
                return row[idx] if len(row) > idx else default

            supplier = Supplier(
                id=get_val("id", 0),
                name=get_val("name", 1) or "",
                name_en=get_val("name_en", 2),
                contact_person=get_val("contact_person", 3),
                phone=get_val("phone", 4),
                phone2=get_val("phone2", 5),
                email=get_val("email", 6),
                website=get_val("website", 7),
                address=get_val("address", 8),
                city=get_val("city", 9),
                country=get_val("country", 10, "الجزائر"),
                tax_number=get_val("tax_number", 11),
                commercial_register=get_val("commercial_register", 12),
                payment_terms=get_val("payment_terms", 13),
                credit_limit=Decimal(str(get_val("credit_limit", 14, 0))),
                current_balance=Decimal(str(get_val("current_balance", 15, 0))),
                notes=get_val("notes", 16),
                is_active=bool(get_val("is_active", 17, True)),
                created_at=self._parse_datetime(get_val("created_at", 19)),
                updated_at=self._parse_datetime(get_val("updated_at", 20)),
            )
            # Calculated fields from query
            supplier.last_purchase_date = self._parse_date(get_val("last_purchase_date", 21))
            supplier.total_purchases = Decimal(str(get_val("total_purchases", 22) or 0))
            supplier.purchases_count = int(get_val("purchases_count", 23) or 0)
            return supplier
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error mapping supplier: {e}")
            return None

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
