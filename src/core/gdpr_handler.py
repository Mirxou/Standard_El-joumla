import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GDPR Handler - معالج GDPR
معالجة متطلبات General Data Protection Regulation
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GDPRRequest:
    """طلب GDPR"""

    id: Optional[int] = None
    request_type: str = ""  # ACCESS, RECTIFICATION, ERASURE, PORTABILITY
    customer_id: Optional[int] = None
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, REJECTED
    requested_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    request_data: str = ""  # JSON
    response_data: str = ""  # JSON
    company_id: Optional[int] = None
    requested_by: Optional[int] = None


class GDPRHandler:
    """معالج GDPR"""

    def __init__(self, db_manager):
        """
        تهيئة معالج GDPR

        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db_manager = db_manager
        self.logger = logger
        self._create_tables()

    def _create_tables(self):
        """إنشاء جداول GDPR"""
        try:
            self.db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS gdpr_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_type TEXT NOT NULL,
                    customer_id INTEGER,
                    status TEXT DEFAULT 'PENDING',
                    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    request_data TEXT,
                    response_data TEXT,
                    company_id INTEGER,
                    requested_by INTEGER,

                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY (requested_by) REFERENCES users(id) ON DELETE SET NULL
                )
            """)

            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_gdpr_requests_customer
                ON gdpr_requests(customer_id)
            """)
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_gdpr_requests_status
                ON gdpr_requests(status)
            """)

        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء جداول GDPR: {e}", exc_info=True)

    # ============================================================================
    # Right to Access (حق الوصول)
    # ============================================================================

    def request_data_access(self, customer_id: int, requested_by: Optional[int] = None) -> Optional[int]:
        """
        طلب الوصول إلى البيانات (Right to Access)

        Args:
            customer_id: معرف العميل
            requested_by: معرف المستخدم الذي طلب الوصول

        Returns:
            معرف الطلب أو None
        """
        try:
            company_id = self._get_company_id()

            query = """
                INSERT INTO gdpr_requests (
                    request_type, customer_id, status, requested_by, company_id
                ) VALUES (?, ?, ?, ?, ?)
            """

            result = self.db_manager.execute_query(query, ("ACCESS", customer_id, "PENDING", requested_by, company_id))

            if result:
                request_id = result.lastrowid
                self.logger.info(f"✅ تم إنشاء طلب وصول إلى البيانات للعميل: {customer_id}")
                return request_id

            return None

        except Exception as e:
            self.logger.error(f"❌ خطأ في طلب الوصول إلى البيانات: {e}", exc_info=True)
            return None

    def export_customer_data(self, customer_id: int) -> Dict[str, Any]:
        """
        تصدير بيانات العميل (لـ Right to Access)

        Args:
            customer_id: معرف العميل

        Returns:
            Dict مع بيانات العميل
        """
        try:
            # جمع جميع بيانات العميل
            customer_data = {}

            # بيانات العميل الأساسية
            customer_query = "SELECT * FROM customers WHERE id = ?"
            customer_row = self.db_manager.fetch_one(customer_query, (customer_id,))
            if customer_row:
                customer_data["customer"] = dict(customer_row)

            # المبيعات
            sales_query = "SELECT * FROM sales WHERE customer_id = ?"
            sales_rows = self.db_manager.fetch_all(sales_query, (customer_id,))
            customer_data["sales"] = [dict(row) for row in sales_rows]

            # المدفوعات
            payments_query = "SELECT * FROM payments WHERE customer_id = ?"
            payments_rows = self.db_manager.fetch_all(payments_query, (customer_id,))
            customer_data["payments"] = [dict(row) for row in payments_rows]

            # سجلات التدقيق المتعلقة بالعميل
            audit_query = """
                SELECT * FROM audit_logs
                WHERE entity_type = 'CUSTOMER' AND entity_id = ?
            """
            audit_rows = self.db_manager.fetch_all(audit_query, (customer_id,))
            customer_data["audit_logs"] = [dict(row) for row in audit_rows]

            return {
                "success": True,
                "customer_id": customer_id,
                "exported_at": datetime.now().isoformat(),
                "data": customer_data,
            }

        except Exception as e:
            self.logger.error(f"❌ خطأ في تصدير بيانات العميل: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    # ============================================================================
    # Right to Rectification (حق التصحيح)
    # ============================================================================

    def request_data_rectification(
        self,
        customer_id: int,
        corrections: Dict[str, Any],
        requested_by: Optional[int] = None,
    ) -> Optional[int]:
        """
        طلب تصحيح البيانات (Right to Rectification)

        Args:
            customer_id: معرف العميل
            corrections: التصحيحات المطلوبة
            requested_by: معرف المستخدم الذي طلب التصحيح

        Returns:
            معرف الطلب أو None
        """
        try:
            company_id = self._get_company_id()

            query = """
                INSERT INTO gdpr_requests (
                    request_type, customer_id, status, request_data, requested_by, company_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            """

            request_data_json = json.dumps(corrections, ensure_ascii=False, default=str)

            result = self.db_manager.execute_query(
                query,
                (
                    "RECTIFICATION",
                    customer_id,
                    "PENDING",
                    request_data_json,
                    requested_by,
                    company_id,
                ),
            )

            if result:
                request_id = result.lastrowid
                self.logger.info(f"✅ تم إنشاء طلب تصحيح بيانات للعميل: {customer_id}")
                return request_id

            return None

        except Exception as e:
            self.logger.error(f"❌ خطأ في طلب تصحيح البيانات: {e}", exc_info=True)
            return None

    # ============================================================================
    # Right to Erasure / Right to be Forgotten (حق الحذف)
    # ============================================================================

    def request_data_erasure(
        self, customer_id: int, reason: str = "", requested_by: Optional[int] = None
    ) -> Optional[int]:
        """
        طلب حذف البيانات (Right to be Forgotten)

        Args:
            customer_id: معرف العميل
            reason: سبب الطلب
            requested_by: معرف المستخدم الذي طلب الحذف

        Returns:
            معرف الطلب أو None
        """
        try:
            company_id = self._get_company_id()

            query = """
                INSERT INTO gdpr_requests (
                    request_type, customer_id, status, request_data, requested_by, company_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            """

            request_data = {"reason": reason}
            request_data_json = json.dumps(request_data, ensure_ascii=False, default=str)

            result = self.db_manager.execute_query(
                query,
                (
                    "ERASURE",
                    customer_id,
                    "PENDING",
                    request_data_json,
                    requested_by,
                    company_id,
                ),
            )

            if result:
                request_id = result.lastrowid
                self.logger.info(f"✅ تم إنشاء طلب حذف بيانات للعميل: {customer_id}")
                return request_id

            return None

        except Exception as e:
            self.logger.error(f"❌ خطأ في طلب حذف البيانات: {e}", exc_info=True)
            return None

    def execute_data_erasure(self, customer_id: int, anonymize: bool = True) -> Dict[str, Any]:
        """
        تنفيذ حذف البيانات (Right to be Forgotten)

        Args:
            customer_id: معرف العميل
            anonymize: إذا كان True، يتم إخفاء الهوية بدلاً من الحذف الكامل

        Returns:
            Dict مع نتيجة التنفيذ
        """
        try:
            if anonymize:
                # إخفاء الهوية بدلاً من الحذف الكامل
                anonymized_name = f"ANONYMIZED_{hashlib.md5(str(customer_id).encode()).hexdigest()[:8]}"
                anonymized_email = f"{anonymized_name}@anonymized.local"

                update_query = """
                    UPDATE customers SET
                        name = ?,
                        email = ?,
                        phone = NULL,
                        address = NULL,
                        notes = 'Data anonymized per GDPR request'
                    WHERE id = ?
                """

                self.db_manager.execute_query(update_query, (anonymized_name, anonymized_email, customer_id))

                return {
                    "success": True,
                    "customer_id": customer_id,
                    "action": "anonymized",
                    "message": "تم إخفاء هوية البيانات بنجاح",
                }
            else:
                # حذف كامل (يجب توخي الحذر!)
                # ملاحظة: قد نحتاج لحذف البيانات المرتبطة أولاً
                delete_query = "DELETE FROM customers WHERE id = ?"
                self.db_manager.execute_query(delete_query, (customer_id,))

                return {
                    "success": True,
                    "customer_id": customer_id,
                    "action": "deleted",
                    "message": "تم حذف البيانات بنجاح",
                }

        except Exception as e:
            self.logger.error(f"❌ خطأ في تنفيذ حذف البيانات: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    # ============================================================================
    # Right to Data Portability (حق قابلية نقل البيانات)
    # ============================================================================

    def request_data_portability(
        self, customer_id: int, format: str = "JSON", requested_by: Optional[int] = None
    ) -> Optional[int]:
        """
        طلب قابلية نقل البيانات (Right to Data Portability)

        Args:
            customer_id: معرف العميل
            format: صيغة البيانات (JSON, CSV, XML)
            requested_by: معرف المستخدم الذي طلب النقل

        Returns:
            معرف الطلب أو None
        """
        try:
            company_id = self._get_company_id()

            query = """
                INSERT INTO gdpr_requests (
                    request_type, customer_id, status, request_data, requested_by, company_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            """

            request_data = {"format": format}
            request_data_json = json.dumps(request_data, ensure_ascii=False, default=str)

            result = self.db_manager.execute_query(
                query,
                (
                    "PORTABILITY",
                    customer_id,
                    "PENDING",
                    request_data_json,
                    requested_by,
                    company_id,
                ),
            )

            if result:
                request_id = result.lastrowid
                self.logger.info(f"✅ تم إنشاء طلب قابلية نقل بيانات للعميل: {customer_id}")
                return request_id

            return None

        except Exception as e:
            self.logger.error(f"❌ خطأ في طلب قابلية نقل البيانات: {e}", exc_info=True)
            return None

    def export_customer_data_portable(self, customer_id: int, format: str = "JSON") -> Dict[str, Any]:
        """
        تصدير بيانات العميل بصيغة قابلة للنقل

        Args:
            customer_id: معرف العميل
            format: صيغة البيانات (JSON, CSV, XML)

        Returns:
            Dict مع البيانات المصدرة
        """
        try:
            data = self.export_customer_data(customer_id)

            if format == "JSON":
                return data
            elif format == "CSV":
                # يمكن إضافة تحويل إلى CSV هنا
                return {"success": False, "error": "CSV export not implemented yet"}
            elif format == "XML":
                # يمكن إضافة تحويل إلى XML هنا
                return {"success": False, "error": "XML export not implemented yet"}
            else:
                return {"success": False, "error": f"Unsupported format: {format}"}

        except Exception as e:
            self.logger.error(f"❌ خطأ في تصدير البيانات القابلة للنقل: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def get_all_requests(
        self, status: Optional[str] = None, request_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """الحصول على جميع طلبات GDPR"""
        try:
            query = "SELECT * FROM gdpr_requests WHERE 1=1"
            params = []

            company_id = self._get_company_id()
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)

            if status:
                query += " AND status = ?"
                params.append(status)

            if request_type:
                query += " AND request_type = ?"
                params.append(request_type)

            query += " ORDER BY requested_at DESC"

            rows = self.db_manager.fetch_all(query, tuple(params))
            return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على طلبات GDPR: {e}", exc_info=True)
            return []

    def update_request_status(
        self,
        request_id: int,
        status: str,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """تحديث حالة طلب GDPR"""
        try:
            query = """
                UPDATE gdpr_requests SET
                    status = ?,
                    response_data = ?,
                    completed_at = ?
                WHERE id = ?
            """

            response_json = json.dumps(response_data, ensure_ascii=False, default=str) if response_data else ""
            completed_at = datetime.now().isoformat() if status == "COMPLETED" else None

            result = self.db_manager.execute_query(query, (status, response_json, completed_at, request_id))

            if result:
                self.logger.info(f"✅ تم تحديث حالة طلب GDPR: {request_id}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"❌ خطأ في تحديث حالة طلب GDPR: {e}", exc_info=True)
            return False

    def _get_company_id(self) -> Optional[int]:
        """الحصول على معرف الشركة الحالية"""
        try:
            from src.core.tenant_isolation import TenantIsolationManager

            tenant_isolation = TenantIsolationManager(self.db_manager)
            return tenant_isolation.get_current_company_id()
        except Exception:
            return None
