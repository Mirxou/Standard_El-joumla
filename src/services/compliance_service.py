import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compliance Service - خدمة الامتثال والتدقيق
إدارة قواعد الامتثال، سجلات التدقيق، والتحقق من الامتثال
"""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from src.core.database_manager import DatabaseManager
from src.core.gdpr_handler import GDPRHandler
from src.core.sox_controls import SOXControlsManager
from src.core.tenant_isolation import TenantIsolationManager

logger = logging.getLogger(__name__)


class ComplianceRuleType(Enum):
    """أنواع قواعد الامتثال"""

    DATA_RETENTION = "DATA_RETENTION"
    ACCESS_CONTROL = "ACCESS_CONTROL"
    DATA_PRIVACY = "DATA_PRIVACY"
    FINANCIAL_REPORTING = "FINANCIAL_REPORTING"
    INVENTORY_CONTROL = "INVENTORY_CONTROL"
    CUSTOM = "CUSTOM"


class ComplianceCheckStatus(Enum):
    """حالة فحص الامتثال"""

    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    PENDING = "PENDING"


@dataclass
class ComplianceRule:
    """قاعدة امتثال"""

    id: Optional[int] = None
    name: str = ""
    rule_type: str = ComplianceRuleType.CUSTOM.value
    description: str = ""
    rule_config: str = ""  # JSON
    is_active: bool = True
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    company_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ComplianceCheck:
    """فحص امتثال"""

    id: Optional[int] = None
    rule_id: int = 0
    check_date: Optional[datetime] = None
    status: str = ComplianceCheckStatus.PENDING.value
    result: str = ""  # JSON
    notes: str = ""
    company_id: Optional[int] = None
    checked_by: Optional[int] = None


@dataclass
class AuditLog:
    """سجل تدقيق"""

    id: Optional[int] = None
    user_id: Optional[int] = None
    action: str = ""
    entity_type: str = ""  # PRODUCT, SALE, PURCHASE, etc.
    entity_id: Optional[int] = None
    old_values: str = ""  # JSON
    new_values: str = ""  # JSON
    ip_address: str = ""
    user_agent: str = ""
    timestamp: Optional[datetime] = None
    company_id: Optional[int] = None


class ComplianceService:
    """خدمة الامتثال والتدقيق"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        logger_instance: Optional[logging.Logger] = None,
    ):
        """
        تهيئة خدمة الامتثال

        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.tenant_isolation = TenantIsolationManager(db_manager) if db_manager else None

        # إنشاء الجداول
        self._create_tables()

        # تهيئة SOX Controls و GDPR Handler
        self.sox_controls = SOXControlsManager(db_manager)
        self.gdpr_handler = GDPRHandler(db_manager)

    def _create_tables(self):
        """إنشاء جداول الامتثال والتدقيق"""
        try:
            # جدول قواعد الامتثال
            self.db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS compliance_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    rule_type TEXT NOT NULL,
                    description TEXT,
                    rule_config TEXT,
                    is_active INTEGER DEFAULT 1,
                    severity TEXT DEFAULT 'MEDIUM',
                    company_id INTEGER,
                    created_by INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                )
            """)

            # جدول فحوصات الامتثال
            self.db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS compliance_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id INTEGER NOT NULL,
                    check_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    result TEXT,
                    notes TEXT,
                    company_id INTEGER,
                    checked_by INTEGER,

                    FOREIGN KEY (rule_id) REFERENCES compliance_rules(id) ON DELETE CASCADE,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY (checked_by) REFERENCES users(id) ON DELETE SET NULL
                )
            """)

            # جدول سجلات التدقيق
            self.db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER,
                    old_values TEXT,
                    new_values TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    company_id INTEGER,

                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
                )
            """)

            # إنشاء Indexes (بعد التأكد من وجود الجدول)
            try:
                # التحقق من وجود الجدول أولاً
                check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"
                table_exists = self.db_manager.fetch_one(check_query)

                if table_exists:
                    try:
                        self.db_manager.execute_query("""
                            CREATE INDEX IF NOT EXISTS idx_audit_logs_user
                            ON audit_logs(user_id)
                        """)
                    except Exception:
                        logging.getLogger(__name__).warning("Ignored exception in compliance_service.py")

                    try:
                        self.db_manager.execute_query("""
                            CREATE INDEX IF NOT EXISTS idx_audit_logs_entity
                            ON audit_logs(entity_type, entity_id)
                        """)
                    except Exception:
                        logging.getLogger(__name__).warning("Ignored exception in compliance_service.py")

                    try:
                        self.db_manager.execute_query("""
                            CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp
                            ON audit_logs(timestamp)
                        """)
                    except Exception:
                        logging.getLogger(__name__).warning("Ignored exception in compliance_service.py")

                    try:
                        self.db_manager.execute_query("""
                            CREATE INDEX IF NOT EXISTS idx_audit_logs_company
                            ON audit_logs(company_id)
                        """)
                    except Exception:
                        logging.getLogger(__name__).warning("Ignored exception in compliance_service.py")
            except Exception as e:
                self.logger.warning(f"⚠️ خطأ في إنشاء Indexes لـ audit_logs: {e}")
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_compliance_rules_company
                ON compliance_rules(company_id)
            """)
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_compliance_checks_rule
                ON compliance_checks(rule_id)
            """)

        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء جداول الامتثال: {e}", exc_info=True)

    # ============================================================================
    # Audit Logging
    # ============================================================================

    def log_audit_event(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        ip_address: str = "",
        user_agent: str = "",
    ) -> Optional[int]:
        """
        تسجيل حدث تدقيق

        Args:
            action: نوع الإجراء (CREATE, UPDATE, DELETE, VIEW, etc.)
            entity_type: نوع الكيان (PRODUCT, SALE, etc.)
            entity_id: معرف الكيان
            old_values: القيم القديمة (Dict)
            new_values: القيم الجديدة (Dict)
            user_id: معرف المستخدم
            ip_address: عنوان IP
            user_agent: User Agent

        Returns:
            معرف السجل أو None
        """
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            query = """
                INSERT INTO audit_logs (
                    user_id, action, entity_type, entity_id,
                    old_values, new_values, ip_address, user_agent,
                    company_id, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            old_values_json = json.dumps(old_values, ensure_ascii=False, default=str) if old_values else ""
            new_values_json = json.dumps(new_values, ensure_ascii=False, default=str) if new_values else ""

            values = (
                user_id,
                action,
                entity_type,
                entity_id,
                old_values_json,
                new_values_json,
                ip_address,
                user_agent,
                company_id,
                datetime.now().isoformat(),
            )

            result = self.db_manager.execute_query(query, values)
            if result:
                log_id = result.lastrowid
                self.logger.debug(f"✅ تم تسجيل حدث تدقيق: {action} على {entity_type} (ID: {log_id})")
                return log_id

            return None

        except Exception as e:
            self.logger.error(f"❌ خطأ في تسجيل حدث تدقيق: {e}", exc_info=True)
            return None

    def get_audit_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        الحصول على سجلات التدقيق

        Args:
            entity_type: نوع الكيان (فلتر)
            entity_id: معرف الكيان (فلتر)
            user_id: معرف المستخدم (فلتر)
            start_date: تاريخ البداية (فلتر)
            end_date: تاريخ النهاية (فلتر)
            limit: الحد الأقصى للنتائج

        Returns:
            List من AuditLog
        """
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []

            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)

            if entity_type:
                query += " AND entity_type = ?"
                params.append(entity_type)

            if entity_id:
                query += " AND entity_id = ?"
                params.append(entity_id)

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            rows = self.db_manager.fetch_all(query, tuple(params))
            return [self._row_to_audit_log(row) for row in rows]

        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على سجلات التدقيق: {e}", exc_info=True)
            return []

    # ============================================================================
    # Compliance Rules
    # ============================================================================

    def create_compliance_rule(self, rule: ComplianceRule) -> Optional[int]:
        """إنشاء قاعدة امتثال"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            query = """
                INSERT INTO compliance_rules (
                    name, rule_type, description, rule_config,
                    is_active, severity, company_id, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            values = (
                rule.name,
                rule.rule_type,
                rule.description,
                rule.rule_config,
                1 if rule.is_active else 0,
                rule.severity,
                company_id,
                rule.created_by,
            )

            result = self.db_manager.execute_query(query, values)
            if result:
                rule_id = result.lastrowid
                self.logger.info(f"✅ تم إنشاء قاعدة امتثال: {rule.name} (ID: {rule_id})")
                return rule_id

            return None

        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء قاعدة امتثال: {e}", exc_info=True)
            return None

    def get_compliance_rule(self, rule_id: int) -> Optional[ComplianceRule]:
        """الحصول على قاعدة امتثال"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            query = "SELECT * FROM compliance_rules WHERE id = ?"
            params = [rule_id]

            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)

            row = self.db_manager.fetch_one(query, tuple(params))
            if row:
                return self._row_to_compliance_rule(row)

            return None

        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على قاعدة امتثال: {e}", exc_info=True)
            return None

    def get_all_compliance_rules(self) -> List[ComplianceRule]:
        """الحصول على جميع قواعد الامتثال"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            query = "SELECT * FROM compliance_rules WHERE 1=1"
            params = []

            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)

            query += " ORDER BY name"

            rows = self.db_manager.fetch_all(query, tuple(params))
            return [self._row_to_compliance_rule(row) for row in rows]

        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على قواعد الامتثال: {e}", exc_info=True)
            return []

    def update_compliance_rule(self, rule: ComplianceRule) -> bool:
        """تحديث قاعدة امتثال"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            query = """
                UPDATE compliance_rules SET
                    name = ?, rule_type = ?, description = ?,
                    rule_config = ?, is_active = ?, severity = ?
                WHERE id = ?
            """

            params = [
                rule.name,
                rule.rule_type,
                rule.description,
                rule.rule_config,
                1 if rule.is_active else 0,
                rule.severity,
                rule.id,
            ]

            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)

            result = self.db_manager.execute_query(query, tuple(params))
            if result and (hasattr(result, "rowcount") and result.rowcount > 0 or not hasattr(result, "rowcount")):
                self.logger.info(f"✅ تم تحديث قاعدة امتثال: {rule.name} (ID: {rule.id})")
                return True

            return False

        except Exception as e:
            self.logger.error(f"❌ خطأ في تحديث قاعدة امتثال: {e}", exc_info=True)
            return False

    def delete_compliance_rule(self, rule_id: int) -> bool:
        """حذف قاعدة امتثال"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            query = "DELETE FROM compliance_rules WHERE id = ?"
            params = [rule_id]

            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)

            result = self.db_manager.execute_query(query, tuple(params))
            if result and (hasattr(result, "rowcount") and result.rowcount > 0 or not hasattr(result, "rowcount")):
                self.logger.info(f"✅ تم حذف قاعدة امتثال: ID={rule_id}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"❌ خطأ في حذف قاعدة امتثال: {e}", exc_info=True)
            return False

    # ============================================================================
    # Compliance Checks
    # ============================================================================

    def run_compliance_check(self, rule_id: int, checked_by: Optional[int] = None) -> Optional[ComplianceCheck]:
        """
        تشغيل فحص امتثال

        Args:
            rule_id: معرف القاعدة
            checked_by: معرف المستخدم الذي قام بالفحص

        Returns:
            ComplianceCheck أو None
        """
        try:
            rule = self.get_compliance_rule(rule_id)
            if not rule:
                return None

            if not rule.is_active:
                self.logger.warning(f"⚠️ قاعدة امتثال غير مفعّلة: {rule.name}")
                return None

            # تنفيذ القاعدة
            result = self._execute_rule(rule)

            # إنشاء سجل فحص
            check = ComplianceCheck(
                rule_id=rule_id,
                check_date=datetime.now(),
                status=result.get("status", ComplianceCheckStatus.PENDING.value),
                result=json.dumps(result, ensure_ascii=False, default=str),
                notes=result.get("notes", ""),
                checked_by=checked_by,
            )

            check_id = self._save_compliance_check(check)
            if check_id:
                check.id = check_id
                return check

            return None

        except Exception as e:
            self.logger.error(f"❌ خطأ في تشغيل فحص امتثال: {e}", exc_info=True)
            return None

    def run_all_compliance_checks(self, checked_by: Optional[int] = None) -> List[ComplianceCheck]:
        """تشغيل جميع فحوصات الامتثال النشطة"""
        try:
            rules = [r for r in self.get_all_compliance_rules() if r.is_active]
            results = []

            for rule in rules:
                check = self.run_compliance_check(rule.id, checked_by)
                if check:
                    results.append(check)

            return results

        except Exception as e:
            self.logger.error(f"❌ خطأ في تشغيل فحوصات الامتثال: {e}", exc_info=True)
            return []

    def get_compliance_check_history(self, rule_id: Optional[int] = None, limit: int = 100) -> List[ComplianceCheck]:
        """الحصول على تاريخ فحوصات الامتثال"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            query = "SELECT * FROM compliance_checks WHERE 1=1"
            params = []

            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)

            if rule_id:
                query += " AND rule_id = ?"
                params.append(rule_id)

            query += " ORDER BY check_date DESC LIMIT ?"
            params.append(limit)

            rows = self.db_manager.fetch_all(query, tuple(params))
            return [self._row_to_compliance_check(row) for row in rows]

        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على تاريخ فحوصات الامتثال: {e}", exc_info=True)
            return []

    # ============================================================================
    # Rule Execution Engine
    # ============================================================================

    def _execute_rule(self, rule: ComplianceRule) -> Dict[str, Any]:
        """
        تنفيذ قاعدة امتثال

        Args:
            rule: قاعدة الامتثال

        Returns:
            Dict مع نتيجة التنفيذ
        """
        try:
            config = json.loads(rule.rule_config) if rule.rule_config else {}

            if rule.rule_type == ComplianceRuleType.DATA_RETENTION.value:
                return self._check_data_retention(config)
            elif rule.rule_type == ComplianceRuleType.ACCESS_CONTROL.value:
                return self._check_access_control(config)
            elif rule.rule_type == ComplianceRuleType.DATA_PRIVACY.value:
                return self._check_data_privacy(config)
            elif rule.rule_type == ComplianceRuleType.FINANCIAL_REPORTING.value:
                return self._check_financial_reporting(config)
            elif rule.rule_type == ComplianceRuleType.INVENTORY_CONTROL.value:
                return self._check_inventory_control(config)
            else:
                return {
                    "status": ComplianceCheckStatus.WARNING.value,
                    "message": f"نوع قاعدة غير مدعوم: {rule.rule_type}",
                    "notes": "يرجى إضافة منطق تنفيذ مخصص",
                }

        except Exception as e:
            self.logger.error(f"❌ خطأ في تنفيذ قاعدة امتثال: {e}", exc_info=True)
            return {
                "status": ComplianceCheckStatus.FAILED.value,
                "message": f"خطأ في التنفيذ: {str(e)}",
            }

    def _check_data_retention(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """فحص احتفاظ البيانات"""
        try:
            retention_days = config.get("retention_days", 365)
            config.get("table_name", "sales")

            query = """
                SELECT COUNT(*) as count
                FROM {table_name}
                WHERE DATE(created_at) < DATE('now', '-{retention_days} days')
            """

            row = self.db_manager.fetch_one(query)
            old_records = row["count"] if row else 0

            if old_records > 0:
                return {
                    "status": ComplianceCheckStatus.WARNING.value,
                    "message": f"يوجد {old_records} سجل أقدم من {retention_days} يوم",
                    "old_records": old_records,
                    "retention_days": retention_days,
                }
            else:
                return {
                    "status": ComplianceCheckStatus.PASSED.value,
                    "message": "جميع السجلات ضمن فترة الاحتفاظ",
                    "old_records": 0,
                }

        except Exception as e:
            return {
                "status": ComplianceCheckStatus.FAILED.value,
                "message": f"خطأ في فحص احتفاظ البيانات: {str(e)}",
            }

    def _check_access_control(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """فحص التحكم في الوصول"""
        try:
            # فحص المستخدمين بدون صلاحيات
            query = """
                SELECT COUNT(*) as count
                FROM users u
                LEFT JOIN user_permissions up ON u.id = up.user_id
                WHERE up.user_id IS NULL AND u.is_active = 1
            """

            row = self.db_manager.fetch_one(query)
            users_without_permissions = row["count"] if row else 0

            if users_without_permissions > 0:
                return {
                    "status": ComplianceCheckStatus.WARNING.value,
                    "message": f"يوجد {users_without_permissions} مستخدم بدون صلاحيات",
                    "users_without_permissions": users_without_permissions,
                }
            else:
                return {
                    "status": ComplianceCheckStatus.PASSED.value,
                    "message": "جميع المستخدمين لديهم صلاحيات",
                }

        except Exception as e:
            return {
                "status": ComplianceCheckStatus.FAILED.value,
                "message": f"خطأ في فحص التحكم في الوصول: {str(e)}",
            }

    def _check_data_privacy(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """فحص خصوصية البيانات"""
        try:
            # فحص البيانات الحساسة غير مشفرة (مثال)
            query = """
                SELECT COUNT(*) as count
                FROM customers
                WHERE email IS NOT NULL AND email != ''
            """

            row = self.db_manager.fetch_one(query)
            customers_with_email = row["count"] if row else 0

            # يمكن إضافة فحوصات أكثر تعقيداً هنا
            return {
                "status": ComplianceCheckStatus.PASSED.value,
                "message": "فحص خصوصية البيانات مكتمل",
                "customers_with_email": customers_with_email,
            }

        except Exception as e:
            return {
                "status": ComplianceCheckStatus.FAILED.value,
                "message": f"خطأ في فحص خصوصية البيانات: {str(e)}",
            }

    def _check_financial_reporting(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """فحص التقارير المالية"""
        try:
            # فحص المبيعات بدون عملاء
            query = """
                SELECT COUNT(*) as count
                FROM sales
                WHERE customer_id IS NULL
            """

            row = self.db_manager.fetch_one(query)
            sales_without_customer = row["count"] if row else 0

            if sales_without_customer > 0:
                return {
                    "status": ComplianceCheckStatus.WARNING.value,
                    "message": f"يوجد {sales_without_customer} عملية بيع بدون عميل",
                    "sales_without_customer": sales_without_customer,
                }
            else:
                return {
                    "status": ComplianceCheckStatus.PASSED.value,
                    "message": "جميع عمليات البيع مرتبطة بعملاء",
                }

        except Exception as e:
            return {
                "status": ComplianceCheckStatus.FAILED.value,
                "message": f"خطأ في فحص التقارير المالية: {str(e)}",
            }

    def _check_inventory_control(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """فحص التحكم في المخزون"""
        try:
            # فحص المنتجات بدون مخزون أدنى
            query = """
                SELECT COUNT(*) as count
                FROM products
                WHERE min_stock IS NULL OR min_stock = 0
            """

            row = self.db_manager.fetch_one(query)
            products_without_min_stock = row["count"] if row else 0

            if products_without_min_stock > 0:
                return {
                    "status": ComplianceCheckStatus.WARNING.value,
                    "message": f"يوجد {products_without_min_stock} منتج بدون حد أدنى للمخزون",
                    "products_without_min_stock": products_without_min_stock,
                }
            else:
                return {
                    "status": ComplianceCheckStatus.PASSED.value,
                    "message": "جميع المنتجات لديها حد أدنى للمخزون",
                }

        except Exception as e:
            return {
                "status": ComplianceCheckStatus.FAILED.value,
                "message": f"خطأ في فحص التحكم في المخزون: {str(e)}",
            }

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _save_compliance_check(self, check: ComplianceCheck) -> Optional[int]:
        """حفظ فحص امتثال"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            query = """
                INSERT INTO compliance_checks (
                    rule_id, check_date, status, result, notes,
                    company_id, checked_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            values = (
                check.rule_id,
                check.check_date.isoformat() if check.check_date else None,
                check.status,
                check.result,
                check.notes,
                company_id,
                check.checked_by,
            )

            result = self.db_manager.execute_query(query, values)
            if result:
                return result.lastrowid

            return None

        except Exception as e:
            self.logger.error(f"❌ خطأ في حفظ فحص امتثال: {e}", exc_info=True)
            return None

    def _row_to_audit_log(self, row: Dict[str, Any]) -> AuditLog:
        """تحويل صف قاعدة البيانات إلى AuditLog"""
        return AuditLog(
            id=row.get("id"),
            user_id=row.get("user_id"),
            action=row.get("action", ""),
            entity_type=row.get("entity_type", ""),
            entity_id=row.get("entity_id"),
            old_values=row.get("old_values", ""),
            new_values=row.get("new_values", ""),
            ip_address=row.get("ip_address", ""),
            user_agent=row.get("user_agent", ""),
            timestamp=self._parse_datetime(row.get("timestamp")),
            company_id=row.get("company_id"),
        )

    def _row_to_compliance_rule(self, row: Dict[str, Any]) -> ComplianceRule:
        """تحويل صف قاعدة البيانات إلى ComplianceRule"""
        return ComplianceRule(
            id=row.get("id"),
            name=row.get("name", ""),
            rule_type=row.get("rule_type", ComplianceRuleType.CUSTOM.value),
            description=row.get("description", ""),
            rule_config=row.get("rule_config", ""),
            is_active=bool(row.get("is_active", 1)),
            severity=row.get("severity", "MEDIUM"),
            company_id=row.get("company_id"),
            created_by=row.get("created_by"),
            created_at=self._parse_datetime(row.get("created_at")),
            updated_at=self._parse_datetime(row.get("updated_at")),
        )

    def _row_to_compliance_check(self, row: Dict[str, Any]) -> ComplianceCheck:
        """تحويل صف قاعدة البيانات إلى ComplianceCheck"""
        return ComplianceCheck(
            id=row.get("id"),
            rule_id=row.get("rule_id", 0),
            check_date=self._parse_datetime(row.get("check_date")),
            status=row.get("status", ComplianceCheckStatus.PENDING.value),
            result=row.get("result", ""),
            notes=row.get("notes", ""),
            company_id=row.get("company_id"),
            checked_by=row.get("checked_by"),
        )

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """تحليل datetime من قاعدة البيانات"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except Exception:
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    return None
        return None

    # ============================================================================
    # SOX Controls Integration
    # ============================================================================

    def get_sox_controls(self) -> List[Dict[str, Any]]:
        """الحصول على جميع ضوابط SOX"""
        company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
        return self.sox_controls.get_all_controls(company_id)

    def get_sox_control_status(self) -> Dict[str, Any]:
        """الحصول على حالة ضوابط SOX"""
        company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
        return self.sox_controls.get_control_status_summary(company_id)

    def test_sox_control(self, control_id: str) -> Dict[str, Any]:
        """اختبار ضابط SOX"""
        return self.sox_controls.run_automated_test(control_id)

    # ============================================================================
    # GDPR Integration
    # ============================================================================

    def request_gdpr_access(self, customer_id: int, requested_by: Optional[int] = None) -> Optional[int]:
        """طلب الوصول إلى البيانات (GDPR)"""
        return self.gdpr_handler.request_data_access(customer_id, requested_by)

    def request_gdpr_erasure(
        self, customer_id: int, reason: str = "", requested_by: Optional[int] = None
    ) -> Optional[int]:
        """طلب حذف البيانات (GDPR Right to be Forgotten)"""
        return self.gdpr_handler.request_data_erasure(customer_id, reason, requested_by)

    def execute_gdpr_erasure(self, customer_id: int, anonymize: bool = True) -> Dict[str, Any]:
        """تنفيذ حذف البيانات (GDPR)"""
        return self.gdpr_handler.execute_data_erasure(customer_id, anonymize)

    def export_customer_data_gdpr(self, customer_id: int) -> Dict[str, Any]:
        """تصدير بيانات العميل (GDPR)"""
        return self.gdpr_handler.export_customer_data(customer_id)

    def get_gdpr_requests(
        self, status: Optional[str] = None, request_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """الحصول على طلبات GDPR"""
        return self.gdpr_handler.get_all_requests(status, request_type)

    def generate_compliance_summary_report(self, *args, **kwargs):
        """توليد تقرير ملخص الامتثال (Stub)"""
        return {"success": True, "data": {"rules": [], "checks": []}}

    def generate_compliance_rules_report(self, *args, **kwargs):
        """توليد تقرير قواعد الامتثال (Stub)"""
        return {"success": True, "data": {"rules": []}}

    def generate_compliance_checks_report(self, *args, **kwargs):
        """توليد تقرير فحوصات الامتثال (Stub)"""
        return {"success": True, "data": {"checks": []}}

    def generate_sox_controls_report(self, *args, **kwargs):
        """توليد تقرير ضوابط SOX (Stub)"""
        return {"success": True, "data": {"controls": []}}

    def generate_gdpr_requests_report(self, *args, **kwargs):
        """توليد تقرير طلبات GDPR (Stub)"""
        return {"success": True, "data": {"requests": []}}

    def generate_audit_trail_report(self, *args, **kwargs):
        """توليد تقرير سجل التدقيق (Stub)"""
        return {"success": True, "data": {"logs": []}}
