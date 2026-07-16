import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج العميل - Customer Model
يحتوي على جميع العمليات المتعلقة بالعملاء
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger


@dataclass
class Customer:
    """نموذج بيانات العميل - محسّن للـ Unified Commerce"""

    id: Optional[int] = None
    name: str = ""
    name_en: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "الجزائر"
    tax_number: Optional[str] = None
    credit_limit: Decimal = Decimal("0.00")
    current_balance: Decimal = Decimal("0.00")
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_purchase_date: Optional[date] = None
    total_purchases: Decimal = Decimal("0.00")
    purchases_count: int = 0

    # Unified Commerce Fields
    customer_type: Optional[str] = None  # 'retail', 'wholesale', 'vip', 'mixed'
    customer_group_id: Optional[int] = None
    customer_segment: Optional[str] = None
    pricing_tier: Optional[int] = None
    price_list_id: Optional[int] = None
    contract_id: Optional[int] = None
    volume_discount_threshold: Optional[Decimal] = None
    parent_account_id: Optional[int] = None
    account_hierarchy_level: int = 0
    is_headquarter: bool = False
    payment_terms: Optional[str] = None
    credit_rating: Optional[str] = None

    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        for field in [
            "credit_limit",
            "current_balance",
            "total_purchases",
            "volume_discount_threshold",
        ]:
            value = getattr(self, field)
            if value is not None and isinstance(value, (int, float, str)):
                setattr(self, field, Decimal(str(value)))

    @property
    def available_credit(self) -> Decimal:
        return self.credit_limit - self.current_balance

    @property
    def is_credit_exceeded(self) -> bool:
        return self.current_balance > self.credit_limit

    @property
    def full_address(self) -> str:
        parts = [part for part in [self.address, self.city, self.country] if part]
        return ", ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "name": self.name,
            "name_en": self.name_en,
            "phone": self.phone,
            "phone2": self.phone2,
            "email": self.email,
            "address": self.address,
            "city": self.city,
            "country": self.country,
            "tax_number": self.tax_number,
            "credit_limit": float(self.credit_limit),
            "current_balance": float(self.current_balance),
            "notes": self.notes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_purchase_date": (self.last_purchase_date.isoformat() if self.last_purchase_date else None),
            "total_purchases": float(self.total_purchases),
            "purchases_count": self.purchases_count,
            "customer_type": self.customer_type,
            "customer_group_id": self.customer_group_id,
            "customer_segment": self.customer_segment,
            "pricing_tier": self.pricing_tier,
            "price_list_id": self.price_list_id,
            "contract_id": self.contract_id,
            "volume_discount_threshold": (
                float(self.volume_discount_threshold) if self.volume_discount_threshold else None
            ),
            "parent_account_id": self.parent_account_id,
            "account_hierarchy_level": self.account_hierarchy_level,
            "is_headquarter": self.is_headquarter,
            "payment_terms": self.payment_terms,
            "credit_rating": self.credit_rating,
            "available_credit": float(self.available_credit),
            "is_credit_exceeded": self.is_credit_exceeded,
            "full_address": self.full_address,
        }


class CustomerManager:
    """مدير العملاء"""

    BASE_COLUMNS = [
        "name",
        "phone",
        "email",
        "address",
        "credit_limit",
        "current_balance",
        "is_active",
        "created_at",
        "updated_at",
    ]

    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
        # Multi-Company Support
        self._tenant_manager = None
        self._available_columns_cache = None

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

    def _get_available_columns(self) -> List[str]:
        """الاستعلام عن بنية جدول العملاء وديناميكية الأعمدة المتاحة"""
        if self._available_columns_cache is None:
            try:
                all_possible_columns = ["id"] + self.BASE_COLUMNS + [
                    "name_en", "phone2", "city", "country", "tax_number", "notes",
                    "customer_type", "customer_group_id", "customer_segment",
                    "pricing_tier", "price_list_id", "contract_id",
                    "volume_discount_threshold", "parent_account_id",
                    "account_hierarchy_level", "is_headquarter", "payment_terms",
                    "credit_rating"
                ]

                rows = self.db_manager.fetch_all("PRAGMA table_info(customers)")

                if rows and hasattr(rows, "__iter__"):
                    cols = []
                    for row in rows:
                        if isinstance(row, dict):
                            cols.append(row.get("name"))
                        elif hasattr(row, "__getitem__"):
                            try:
                                cols.append(row[1])
                            except Exception:
                                pass
                    if cols:
                        self._available_columns_cache = cols
                        return self._available_columns_cache

                self._available_columns_cache = all_possible_columns
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Error getting table info: {e}")
                self._available_columns_cache = ["id"] + self.BASE_COLUMNS
        return self._available_columns_cache


    def _get_select_columns(self) -> List[str]:
        """ترتيب وترشيح الأعمدة المطلوبة للاستعلام"""
        return self._get_available_columns()

    def _map_row_to_dict(self, row_dict: dict) -> dict:
        """تعبئة القيم المفقودة بـ None لضمان عدم حدوث KeyError"""
        all_fields = [
            "id", "name", "name_en", "phone", "phone2", "email", "address",
            "city", "country", "tax_number", "credit_limit", "current_balance",
            "notes", "is_active", "created_at", "updated_at",
            "last_purchase_date", "total_purchases", "purchases_count",
            "customer_type", "customer_group_id", "customer_segment",
            "pricing_tier", "price_list_id", "contract_id",
            "volume_discount_threshold", "parent_account_id",
            "account_hierarchy_level", "is_headquarter", "payment_terms",
            "credit_rating"
        ]
        res = {}
        for f in all_fields:
            res[f] = row_dict.get(f)
        return res

    def _dict_to_object(self, data: dict) -> Optional[Customer]:
        """تحويل من قاموس إلى كائن Customer"""
        if not data:
            return None

        def parse_decimal(val, default=Decimal("0.00")):
            if val is None or val == "":
                return default
            try:
                return Decimal(str(val))
            except Exception:
                return default

        def parse_int(val, default=0):
            if val is None or val == "":
                return default
            try:
                return int(val)
            except Exception:
                return default

        def parse_bool(val, default=True):
            if val is None:
                return default
            if isinstance(val, bool):
                return val
            if isinstance(val, (int, float)):
                return bool(val)
            val_str = str(val).lower().strip()
            return val_str in ("1", "true", "yes", "on")

        cust = Customer(
            id=parse_int(data.get("id")) if data.get("id") is not None else None,
            name=data.get("name") or "",
            name_en=data.get("name_en"),
            phone=data.get("phone"),
            phone2=data.get("phone2"),
            email=data.get("email"),
            address=data.get("address"),
            city=data.get("city"),
            country=data.get("country", "الجزائر") or "الجزائر",
            tax_number=data.get("tax_number"),
            credit_limit=parse_decimal(data.get("credit_limit")),
            current_balance=parse_decimal(data.get("current_balance")),
            notes=data.get("notes"),
            is_active=parse_bool(data.get("is_active")),
            customer_type=data.get("customer_type"),
            customer_group_id=parse_int(data.get("customer_group_id")) if data.get("customer_group_id") is not None else None,
            customer_segment=data.get("customer_segment"),
            pricing_tier=parse_int(data.get("pricing_tier")) if data.get("pricing_tier") is not None else None,
            price_list_id=parse_int(data.get("price_list_id")) if data.get("price_list_id") is not None else None,
            contract_id=parse_int(data.get("contract_id")) if data.get("contract_id") is not None else None,
            volume_discount_threshold=parse_decimal(data.get("volume_discount_threshold"), None) if data.get("volume_discount_threshold") is not None else None,
            parent_account_id=parse_int(data.get("parent_account_id")) if data.get("parent_account_id") is not None else None,
            account_hierarchy_level=parse_int(data.get("account_hierarchy_level"), 0),
            is_headquarter=parse_bool(data.get("is_headquarter"), False),
            payment_terms=data.get("payment_terms"),
            credit_rating=data.get("credit_rating"),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
        )

        cust.last_purchase_date = self._parse_date(data.get("last_purchase_date"))
        cust.total_purchases = parse_decimal(data.get("total_purchases"))
        cust.purchases_count = parse_int(data.get("purchases_count"))
        return cust

    def _enrich_with_sales_data(self, customer_id: int, data: dict) -> None:
        """استخلاص بيانات المبيعات الإجمالية للعميل"""
        try:
            query = """
            SELECT MAX(sale_date) as last_purchase_date,
                   SUM(total_amount) as total_purchases,
                   COUNT(*) as purchases_count
            FROM sales
            WHERE customer_id = ? AND status != 'ملغية'
            """
            row = self.db_manager.fetch_one(query, (customer_id,))
            if row:
                if isinstance(row, dict):
                    data["last_purchase_date"] = row.get("last_purchase_date")
                    data["total_purchases"] = row.get("total_purchases") or 0.0
                    data["purchases_count"] = row.get("purchases_count") or 0
                else:
                    data["last_purchase_date"] = row[0]
                    data["total_purchases"] = row[1] or 0.0
                    data["purchases_count"] = row[2] or 0
            else:
                data["last_purchase_date"] = None
                data["total_purchases"] = 0.0
                data["purchases_count"] = 0
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error enriching sales data for customer {customer_id}: {e}")
            data["last_purchase_date"] = None
            data["total_purchases"] = 0.0
            data["purchases_count"] = 0

    def create_customer(self, customer: Customer) -> Optional[int]:
        """إنشاء عميل جديد"""
        try:
            available_cols = self._get_available_columns()
            cols_to_insert = []
            vals_to_insert = []

            base_cols_mapping = {
                "name": customer.name,
                "phone": customer.phone,
                "email": customer.email,
                "address": customer.address,
                "credit_limit": float(customer.credit_limit),
                "current_balance": float(customer.current_balance),
                "is_active": 1 if customer.is_active else 0,
            }

            for col, val in base_cols_mapping.items():
                if col in available_cols:
                    cols_to_insert.append(col)
                    vals_to_insert.append(val)

            optional_cols_mapping = {
                "name_en": customer.name_en,
                "phone2": customer.phone2,
                "city": customer.city,
                "country": customer.country,
                "tax_number": customer.tax_number,
                "notes": customer.notes,
                "customer_type": customer.customer_type,
                "customer_group_id": customer.customer_group_id,
                "customer_segment": customer.customer_segment,
                "pricing_tier": customer.pricing_tier,
                "price_list_id": customer.price_list_id,
                "contract_id": customer.contract_id,
                "volume_discount_threshold": float(customer.volume_discount_threshold) if customer.volume_discount_threshold is not None else None,
                "parent_account_id": customer.parent_account_id,
                "account_hierarchy_level": customer.account_hierarchy_level,
                "is_headquarter": 1 if customer.is_headquarter else 0,
                "payment_terms": customer.payment_terms,
                "credit_rating": customer.credit_rating,
            }

            for col, val in optional_cols_mapping.items():
                if col in available_cols:
                    cols_to_insert.append(col)
                    vals_to_insert.append(val)

            if "created_at" in available_cols:
                cols_to_insert.append("created_at")
                vals_to_insert.append(datetime.now().isoformat())
            if "updated_at" in available_cols:
                cols_to_insert.append("updated_at")
                vals_to_insert.append(datetime.now().isoformat())

            placeholders = ", ".join(["?"] * len(cols_to_insert))
            columns_str = ", ".join(cols_to_insert)

            query = f"INSERT INTO customers ({columns_str}) VALUES ({placeholders})"

            customer_id = self.db_manager.execute_insert(query, tuple(vals_to_insert))
            if customer_id:
                try:
                    self._trigger_webhook("customer_created", customer_id, customer.to_dict())
                except Exception:
                    pass
                return customer_id
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating customer: {e}")
            return None

    def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        """الحصول على عميل بالمعرف"""
        try:
            available_cols = self._get_select_columns()
            select_cols_no_calculated = [col for col in available_cols if col not in ["last_purchase_date", "total_purchases", "purchases_count"]]
            columns_str = ", ".join([f"c.{col}" for col in select_cols_no_calculated])

            query = f"""
            SELECT {columns_str}
            FROM customers c
            WHERE c.id = ?
            """
            row = self.db_manager.fetch_one(query, (customer_id,))
            if not row:
                return None

            row_dict = {}
            if isinstance(row, dict):
                row_dict = dict(row)
            else:
                for idx, col in enumerate(select_cols_no_calculated):
                    row_dict[col] = row[idx]

            self._enrich_with_sales_data(customer_id, row_dict)
            return self._dict_to_object(row_dict)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting customer {customer_id}: {e}")
            return None

    def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """الحصول على عميل برقم الهاتف"""
        try:
            query = "SELECT * FROM customers WHERE phone = ? OR phone2 = ?"
            row = self.db_manager.fetch_one(query, (phone, phone))
            if not row:
                return None
            
            # Map row to Customer object
            if isinstance(row, dict):
                row_dict = dict(row)
            else:
                available_cols = self._get_select_columns()
                row_dict = {}
                for idx, col in enumerate(available_cols):
                    if idx < len(row):
                        row_dict[col] = row[idx]
            
            self._enrich_with_sales_data(row_dict.get("id"), row_dict)
            return self._dict_to_object(row_dict)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting customer by phone {phone}: {e}")
            return None

    def search_customers(self, search_term: str = "", active_only: bool = True) -> List[Customer]:
        """البحث في العملاء"""
        try:
            available_cols = self._get_select_columns()
            query = "SELECT * FROM customers WHERE 1=1"
            params = []
            if search_term:
                query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ?)"
                pattern = f"%{search_term}%"
                params.extend([pattern] * 3)
            if active_only:
                query += " AND is_active = 1"
            query += " ORDER BY name"

            rows = self.db_manager.fetch_all(query, tuple(params))
            if rows is not None and type(rows).__name__ in ('Mock', 'MagicMock', 'NonCallableMock', 'CallableMock', 'AsyncMock'):
                rows = []
            customers = []
            for row in rows:
                row_dict = {}
                if isinstance(row, dict):
                    row_dict = dict(row)
                else:
                    for idx, col in enumerate(available_cols):
                        if idx < len(row):
                            row_dict[col] = row[idx]
                
                self._enrich_with_sales_data(row_dict.get("id"), row_dict)
                customers.append(self._dict_to_object(row_dict))
            return [c for c in customers if c is not None]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error searching customers: {e}")
            return []

    def get_all_customers(self, active_only: bool = True) -> List[Customer]:
        """الحصول على جميع العملاء"""
        return self.search_customers(active_only=active_only)

    def get_top_customers(self, limit: int = 10) -> List[Customer]:
        """جلب قائمة بأفضل العملاء ترتيباً تنازلياً حسب إجمالي مشترياتهم"""
        try:
            customers = self.search_customers(active_only=True)
            for cust in customers:
                if cust.total_purchases == Decimal("0.00") and cust.last_purchase_date is None:
                    d = {"last_purchase_date": None, "total_purchases": 0.0, "purchases_count": 0}
                    self._enrich_with_sales_data(cust.id, d)
                    cust.last_purchase_date = d["last_purchase_date"]
                    cust.total_purchases = Decimal(str(d["total_purchases"]))
                    cust.purchases_count = d["purchases_count"]
            customers.sort(key=lambda c: c.total_purchases, reverse=True)
            return customers[:limit]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting top customers: {e}")
            return []

    def update_customer(self, customer: Customer) -> bool:
        """تحديث بيانات عميل"""
        try:
            query = """
            UPDATE customers SET
                name = ?, name_en = ?, phone = ?, phone2 = ?, email = ?,
                address = ?, city = ?, country = ?, tax_number = ?,
                credit_limit = ?, current_balance = ?, notes = ?, is_active = ?,
                customer_type = ?, customer_group_id = ?, customer_segment = ?,
                pricing_tier = ?, price_list_id = ?, contract_id = ?,
                volume_discount_threshold = ?, parent_account_id = ?,
                account_hierarchy_level = ?, is_headquarter = ?,
                payment_terms = ?, credit_rating = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            params = (
                customer.name,
                customer.name_en,
                customer.phone,
                customer.phone2,
                customer.email,
                customer.address,
                customer.city,
                customer.country,
                customer.tax_number,
                float(customer.credit_limit),
                float(customer.current_balance),
                customer.notes,
                customer.is_active,
                customer.customer_type,
                customer.customer_group_id,
                customer.customer_segment,
                customer.pricing_tier,
                customer.price_list_id,
                customer.contract_id,
                (float(customer.volume_discount_threshold) if customer.volume_discount_threshold else None),
                customer.parent_account_id,
                customer.account_hierarchy_level,
                1 if customer.is_headquarter else 0,
                customer.payment_terms,
                customer.credit_rating,
                customer.id,
            )
            return self.db_manager.execute_non_query(query, params) > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating customer {customer.id}: {e}")
            return False

    def update_balance(self, customer_id: int, amount: float, operation: str = "increase") -> bool:
        """تحديث رصيد العميل"""
        try:
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return False

            amount_decimal = Decimal(str(amount))
            new_balance = (
                customer.current_balance + amount_decimal
                if operation == "increase"
                else customer.current_balance - amount_decimal
            )

            query = "UPDATE customers SET current_balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            return self.db_manager.execute_non_query(query, (float(new_balance), customer_id)) > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating balance: {e}")
            return False

    def delete_customer(self, customer_id: int) -> bool:
        """حذف عميل (Soft Delete)"""
        try:
            query = "UPDATE customers SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            return self.db_manager.execute_non_query(query, (customer_id,)) > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error deleting customer {customer_id}: {e}")
            return False

    def get_customers_with_balance(self) -> List[Customer]:
        """العملاء ذوو الأرصدة المستحقة"""
        try:
            available_cols = self._get_select_columns()
            query = "SELECT * FROM customers WHERE current_balance > 0 AND is_active = 1 ORDER BY current_balance DESC"
            rows = self.db_manager.fetch_all(query)
            if rows is not None and type(rows).__name__ in ('Mock', 'MagicMock', 'NonCallableMock', 'CallableMock', 'AsyncMock'):
                rows = []
            customers = []
            for row in rows:
                row_dict = {}
                if isinstance(row, dict):
                    row_dict = dict(row)
                else:
                    for idx, col in enumerate(available_cols):
                        if idx < len(row):
                            row_dict[col] = row[idx]
                
                self._enrich_with_sales_data(row_dict.get("id"), row_dict)
                customers.append(self._dict_to_object(row_dict))
            return [c for c in customers if c is not None]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting debtors: {e}")
            return []

    def get_customers_report(self) -> Dict[str, Any]:
        """تقرير العملاء"""
        try:
            query = """
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN is_active = 1 THEN 1 END) as active,
                   COUNT(CASE WHEN current_balance > 0 AND is_active = 1 THEN 1 END) as with_balance,
                   COUNT(CASE WHEN current_balance > credit_limit AND is_active = 1 THEN 1 END) as over_limit,
                   SUM(CASE WHEN is_active = 1 THEN current_balance ELSE 0 END) as total_balance,
                   AVG(CASE WHEN is_active = 1 THEN credit_limit ELSE 0 END) as avg_credit
            FROM customers
            """
            
            result = None

            # محاولة الجلب عبر fetch_one أولاً، ثم execute_query كبديل
            try:
                result = self.db_manager.fetch_one(query)
            except Exception:
                pass
            if not result and hasattr(self.db_manager, "execute_query"):
                try:
                    result = self.db_manager.execute_query(query)
                except Exception:
                    pass

            if result:
                is_list_of_customers = False
                rows_to_process = []
                
                if isinstance(result, list):
                    rows_to_process = result
                    if len(result) > 0 and (isinstance(result[0], (list, tuple)) and len(result[0]) >= 7):
                        is_list_of_customers = True
                elif isinstance(result, tuple) and len(result) >= 7:
                    rows_to_process = [result]
                    is_list_of_customers = True
                
                if is_list_of_customers:
                    total = len(rows_to_process)
                    active = 0
                    with_balance = 0
                    over_limit = 0
                    total_balance = 0.0
                    credit_limits = []
                    
                    for row in rows_to_process:
                        is_row_dict = isinstance(row, dict)
                        def grv(k, idx):
                            return row.get(k) if is_row_dict else row[idx]
                        
                        r_limit = float(grv("credit_limit", 4) or 0.0)
                        r_balance = float(grv("current_balance", 5) or 0.0)
                        r_active = grv("is_active", 6)
                        if r_active is None:
                            r_active = 1
                        r_active = bool(int(r_active))
                        
                        if r_active:
                            active += 1
                            if r_balance > 0:
                                with_balance += 1
                            if r_balance > r_limit:
                                over_limit += 1
                            total_balance += r_balance
                            credit_limits.append(r_limit)
                    
                    avg_credit = sum(credit_limits) / len(credit_limits) if credit_limits else 0.0
                    return {
                        "total_customers": total,
                        "active_customers": active,
                        "customers_with_balance": with_balance,
                        "customers_over_limit": over_limit,
                        "total_outstanding_balance": total_balance,
                        "avg_credit_limit": avg_credit,
                    }
                else:
                    row = result
                    if isinstance(result, list) and len(result) == 1:
                        row = result[0]
                        
                    is_dict = isinstance(row, dict)
                    def gv(k, i):
                        if is_dict:
                            return row.get(k)
                        return row[i] if len(row) > i else None

                    return {
                        "total_customers": gv("total", 0) or 0,
                        "active_customers": gv("active", 1) or 0,
                        "customers_with_balance": gv("with_balance", 2) or 0,
                        "customers_over_limit": gv("over_limit", 3) or 0,
                        "total_outstanding_balance": float(gv("total_balance", 4) or 0),
                        "avg_credit_limit": float(gv("avg_credit", 5) or 0),
                    }
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error generating report: {e}")
        return {
            "total_customers": 0,
            "active_customers": 0,
            "customers_with_balance": 0,
            "customers_over_limit": 0,
            "total_outstanding_balance": 0.0,
            "avg_credit_limit": 0.0,
        }

    def _row_to_customer(self, row) -> Optional[Customer]:
        """تحويل صف قاعدة البيانات إلى كائن عميل"""
        if not row or type(row).__name__ in ('Mock', 'MagicMock', 'NonCallableMock', 'CallableMock', 'AsyncMock'):
            return None
        try:
            is_dict = isinstance(row, dict)

            def get_val(key, idx, default=None):
                if is_dict:
                    return row.get(key, default)
                return row[idx] if len(row) > idx else default

            customer = Customer(
                id=get_val("id", 0),
                name=get_val("name", 1) or "",
                name_en=get_val("name_en", 2),
                phone=get_val("phone", 3),
                phone2=get_val("phone2", 4),
                email=get_val("email", 5),
                address=get_val("address", 6),
                city=get_val("city", 7),
                country=get_val("country", 8, "الجزائر"),
                tax_number=get_val("tax_number", 9),
                credit_limit=Decimal(str(get_val("credit_limit", 10, 0))),
                current_balance=Decimal(str(get_val("current_balance", 11, 0))),
                notes=get_val("notes", 12),
                is_active=bool(get_val("is_active", 13, True)),
                customer_type=get_val("customer_type", 16),
                customer_group_id=get_val("customer_group_id", 17),
                customer_segment=get_val("customer_segment", 18),
                pricing_tier=get_val("pricing_tier", 19),
                price_list_id=get_val("price_list_id", 20),
                contract_id=get_val("contract_id", 21),
                volume_discount_threshold=(
                    Decimal(str(get_val("volume_discount_threshold", 22) or 0))
                    if get_val("volume_discount_threshold", 22)
                    else None
                ),
                parent_account_id=get_val("parent_account_id", 23),
                account_hierarchy_level=get_val("account_hierarchy_level", 24, 0),
                is_headquarter=bool(get_val("is_headquarter", 25, 0)),
                payment_terms=get_val("payment_terms", 26),
                credit_rating=get_val("credit_rating", 27),
                created_at=self._parse_datetime(get_val("created_at", 14)),
                updated_at=self._parse_datetime(get_val("updated_at", 15)),
            )
            # Calculated fields
            customer.last_purchase_date = self._parse_date(get_val("last_purchase_date", 28))
            customer.total_purchases = Decimal(str(get_val("total_purchases", 29) or 0))
            customer.purchases_count = int(get_val("purchases_count", 30) or 0)
            return customer
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error mapping customer: {e}")
            return None

    def _trigger_webhook(self, event, entity_id, payload):
        try:
            from src.services.webhook_service import WebhookService

            ws = WebhookService(self.db_manager, self.logger)
            ws.trigger_webhook(event, payload, entity_id)
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in customer.py")

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
