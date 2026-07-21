"""
خدمة البحث المتقدم (Advanced Search Service)

توفر وظائف بحث شاملة ومتقدمة عبر النظام:
- بحث نصي كامل (Full Text Search)
- بحث متعدد المعايير
- بحث حسب النطاق والتاريخ
- دعم العوامل المنطقية (AND/OR)
"""

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..core.database_manager import DatabaseManager


class SearchField(Enum):
    """حقول البحث المتاحة"""

    PRODUCT_NAME = "product_name"
    PRODUCT_SKU = "product_sku"
    PRODUCT_BARCODE = "product_barcode"
    CUSTOMER_NAME = "customer_name"
    CUSTOMER_PHONE = "customer_phone"
    SUPPLIER_NAME = "supplier_name"
    INVOICE_NUMBER = "invoice_number"
    ALL = "all"


class SearchOperator(Enum):
    """عوامل المقارنة"""

    EQUALS = "="
    CONTAINS = "LIKE"
    STARTS_WITH = "STARTS"
    ENDS_WITH = "ENDS"
    GREATER_THAN = ">"
    LESS_THAN = "<"
    BETWEEN = "BETWEEN"
    IN = "IN"


class LogicalOperator(Enum):
    """العوامل المنطقية"""

    AND = "AND"
    OR = "OR"


class SearchCriteria:
    """معيار بحث واحد"""

    def __init__(
        self,
        field: SearchField,
        operator: SearchOperator,
        value: Any,
        logical: LogicalOperator = LogicalOperator.AND,
    ):
        self.field = field
        self.operator = operator
        self.value = value
        self.logical = logical

    def to_sql(self) -> Tuple[str, List[Any]]:
        """تحويل المعيار إلى SQL"""
        params = []

        if self.operator == SearchOperator.EQUALS:
            sql = f"{self._get_column()} = ?"
            params.append(self.value)

        elif self.operator == SearchOperator.CONTAINS:
            sql = f"{self._get_column()} LIKE ?"
            params.append(f"%{self.value}%")

        elif self.operator == SearchOperator.STARTS_WITH:
            sql = f"{self._get_column()} LIKE ?"
            params.append(f"{self.value}%")

        elif self.operator == SearchOperator.ENDS_WITH:
            sql = f"{self._get_column()} LIKE ?"
            params.append(f"%{self.value}")

        elif self.operator == SearchOperator.GREATER_THAN:
            sql = f"{self._get_column()} > ?"
            params.append(self.value)

        elif self.operator == SearchOperator.LESS_THAN:
            sql = f"{self._get_column()} < ?"
            params.append(self.value)

        elif self.operator == SearchOperator.BETWEEN:
            sql = f"{self._get_column()} BETWEEN ? AND ?"
            params.extend(self.value)  # Expect tuple/list of 2 values

        elif self.operator == SearchOperator.IN:
            placeholders = ",".join(["?"] * len(self.value))
            sql = f"{self._get_column()} IN ({placeholders})"
            params.extend(self.value)

        else:
            sql = "1=1"

        return sql, params

    def _get_column(self) -> str:
        """الحصول على اسم العمود من الحقل"""
        mapping = {
            SearchField.PRODUCT_NAME: "p.name",
            SearchField.PRODUCT_SKU: "p.sku",
            SearchField.PRODUCT_BARCODE: "p.barcode",
            SearchField.CUSTOMER_NAME: "c.name",
            SearchField.CUSTOMER_PHONE: "c.phone",
            SearchField.SUPPLIER_NAME: "s.name",
            SearchField.INVOICE_NUMBER: "inv.invoice_number",
        }
        return mapping.get(self.field, "p.name")


class SearchService:
    """خدمة البحث المتقدم"""

    ALLOWED_TABLES = {
        "sales", "purchases", "products", "customers", "suppliers",
        "sale_items", "purchase_order_items", "stock_movements",
        "payments", "quotes", "returns", "journal_entries", "accounts",
    }

    def __init__(self, db: Optional[DatabaseManager] = None, db_manager: Optional[DatabaseManager] = None):
        self.db = db or db_manager or DatabaseManager()

    # ==================== البحث العام ====================

    def search(
        self,
        entity: str,
        criteria_list: List[SearchCriteria],
        limit: int = 100,
        offset: int = 0,
        sort_by: Optional[str] = None,
        sort_order: str = "ASC",
    ) -> Dict[str, Any]:
        """البحث العام الموحد"""
        results = []
        if entity == "products":
            base_query = """
                SELECT
                    p.id,
                    p.name,
                    p.sku,
                    p.barcode,
                    p.selling_price,
                    p.cost_price,
                    p.current_stock,
                    c.name as category_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
            """
            where_clause, params = self._build_where_clause(criteria_list)
            if where_clause:
                query = f"{base_query} WHERE {where_clause}"
            else:
                query = base_query
                
            if sort_by:
                sort_col = "p.selling_price" if sort_by in ("price", "selling_price") else "p.name"
                sort_order = sort_order.upper()
                if sort_order not in ("ASC", "DESC"):
                    sort_order = "DESC"
                query += f" ORDER BY {sort_col} {sort_order}"
            else:
                query += " ORDER BY p.name"
                
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            results = self.db.execute_query(query, params)
            
        elif entity == "customers":
            results = self.search_customers(criteria_list, limit, offset)
        elif entity == "sales":
            results = self.search_sales(criteria_list, limit=limit, offset=offset)
            
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }

    def search_products(
        self, criteria_list: List[SearchCriteria], limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        البحث في المنتجات بمعايير متعددة

        Args:
            criteria_list: قائمة معايير البحث
            limit: عدد النتائج
            offset: بداية النتائج (للصفحات)

        Returns:
            قائمة المنتجات المطابقة
        """
        base_query = """
            SELECT
                p.id,
                p.name,
                p.sku,
                p.barcode,
                p.selling_price,
                p.cost_price,
                p.current_stock,
                c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
        """

        where_clause, params = self._build_where_clause(criteria_list)

        if where_clause:
            query = f"{base_query} WHERE {where_clause}"
        else:
            query = base_query

        query += " ORDER BY p.name LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        return self.db.execute_query(query, params)

    def search_customers(
        self, criteria_list: List[SearchCriteria], limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """البحث في العملاء"""
        base_query = """
            SELECT
                c.id,
                c.name,
                c.phone,
                c.email,
                c.address,
                c.current_balance,
                c.credit_limit
            FROM customers c
        """

        where_clause, params = self._build_where_clause(criteria_list)

        if where_clause:
            query = f"{base_query} WHERE {where_clause}"
        else:
            query = base_query

        query += " ORDER BY c.name LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        return self.db.execute_query(query, params)

    def search_sales(
        self,
        criteria_list: List[SearchCriteria],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """البحث في فواتير المبيعات"""
        base_query = """
            SELECT
                s.id,
                s.invoice_number,
                s.sale_date,
                c.name as customer_name,
                s.total,
                s.final_amount,
                s.payment_method,
                s.status
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
        """

        where_parts = []
        params = []

        # Date range filter
        if start_date:
            where_parts.append("DATE(s.sale_date) >= ?")
            params.append(start_date)
        if end_date:
            where_parts.append("DATE(s.sale_date) <= ?")
            params.append(end_date)

        # Custom criteria
        if criteria_list:
            custom_where, custom_params = self._build_where_clause(criteria_list)
            if custom_where:
                where_parts.append(custom_where)
                params.extend(custom_params)

        if where_parts:
            query = f"{base_query} WHERE {' AND '.join(where_parts)}"
        else:
            query = base_query

        query += " ORDER BY s.sale_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        return self.db.execute_query(query, params)

    # ==================== البحث النصي الكامل ====================

    def full_text_search(self, search_text: str, entity: str = "products", limit: int = 50) -> List[Dict[str, Any]]:
        """
        بحث نصي كامل عبر حقول متعددة

        Args:
            search_text: النص المراد البحث عنه
            entity: الجدول (products, customers, suppliers)
            limit: عدد النتائج

        Returns:
            النتائج المطابقة
        """
        search_pattern = f"%{search_text}%"

        if entity == "products":
            query = """
                SELECT
                    id, name, sku, barcode, selling_price, current_stock,
                    'product' as type
                FROM products
                WHERE name LIKE ? OR sku LIKE ? OR barcode LIKE ?
                ORDER BY name
                LIMIT ?
            """
            params = [search_pattern, search_pattern, search_pattern, limit]

        elif entity == "customers":
            query = """
                SELECT
                    id, name, phone, email, address,
                    'customer' as type
                FROM customers
                WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
                ORDER BY name
                LIMIT ?
            """
            params = [search_pattern, search_pattern, search_pattern, limit]

        elif entity == "suppliers":
            query = """
                SELECT
                    id, name, phone, email, address,
                    'supplier' as type
                FROM suppliers
                WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
                ORDER BY name
                LIMIT ?
            """
            params = [search_pattern, search_pattern, search_pattern, limit]

        else:
            return []

        return self.db.execute_query(query, params)

    def global_search(self, search_text: str, limit_per_type: int = 10) -> Dict[str, List[Dict]]:
        """
        بحث عام عبر جميع الكيانات

        Returns:
            Dict مع نتائج كل نوع
        """
        return {
            "products": self.full_text_search(search_text, "products", limit_per_type),
            "customers": self.full_text_search(search_text, "customers", limit_per_type),
            "suppliers": self.full_text_search(search_text, "suppliers", limit_per_type),
        }

    # ==================== دوال مساعدة ====================

    def _build_where_clause(self, criteria_list: List[SearchCriteria]) -> Tuple[str, List[Any]]:
        """بناء جملة WHERE من قائمة المعايير"""
        if not criteria_list:
            return "", []

        parts = []
        params = []

        for i, criteria in enumerate(criteria_list):
            sql_part, sql_params = criteria.to_sql()

            if i > 0:
                # Add logical operator
                parts.append(criteria.logical.value)

            parts.append(f"({sql_part})")
            params.extend(sql_params)

        where_clause = " ".join(parts)
        return where_clause, params

    def count_results(self, table: str, criteria_list: List[SearchCriteria]) -> int:
        """عد النتائج الكلي (للصفحات)"""
        if table not in self.ALLOWED_TABLES:
            return 0
        where_clause, params = self._build_where_clause(criteria_list)

        if where_clause:
            query = f"SELECT COUNT(*) as total FROM {table} WHERE {where_clause}"
        else:
            query = f"SELECT COUNT(*) as total FROM {table}"

        result = self.db.execute_query(query, params)
        return int(result[0]["total"]) if result else 0
