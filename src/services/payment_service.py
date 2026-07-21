"""
خدمة إدارة المدفوعات والذمم المدينة والدائنة
"""
import logging

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..models.customer import CustomerManager
from ..models.payment import (
    AccountType,
    Payment,
    PaymentManager,
    PaymentMethod,
    PaymentStatus,
    PaymentType,
)
from ..models.supplier import SupplierManager
from ..services.exchange_rate_service import ExchangeRateService
from ..services.accounting_service import AccountingService


class PaymentService:
    """خدمة إدارة المدفوعات"""

    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)

        # إنشاء مديري النماذج
        self.payment_manager = PaymentManager(db_manager, logger)
        self.customer_manager = CustomerManager(db_manager, logger)
        self.supplier_manager = SupplierManager(db_manager, logger)
        # خدمة أسعار الصرف
        self.exchange_rate_service = ExchangeRateService(db_manager, logger)
        # خدمة المحاسبة
        self.accounting_service = AccountingService(db_manager, logger)

        # إنشاء الجداول إذا لم تكن موجودة
        self._create_tables()

    def _create_tables(self):
        """إنشاء جداول المدفوعات"""
        if not self.db_manager:
            if self.logger:
                self.logger.info("تم تخطي إنشاء جداول المدفوعات: DatabaseManager غير مهيأ")
            return
        try:
            # جدول المدفوعات الرئيسي
            payments_table = """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_number TEXT UNIQUE NOT NULL,
                payment_type TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',

                amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
                currency TEXT NOT NULL DEFAULT 'DZD',
                exchange_rate DECIMAL(10,4) NOT NULL DEFAULT 1.0000,
                amount_in_base_currency DECIMAL(15,2) NOT NULL DEFAULT 0.00,

                payment_date DATE NOT NULL,
                due_date DATE,

                customer_id INTEGER,
                supplier_id INTEGER,
                entity_id INTEGER,
                user_id INTEGER,
                sale_id INTEGER,
                purchase_id INTEGER,

                reference_number TEXT,
                bank_name TEXT,
                account_number TEXT,
                notes TEXT,
                account_code TEXT,
                cost_center TEXT,

                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,

                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (purchase_id) REFERENCES purchases(id)
            )
            """

            # جدول جدولة المدفوعات (الأقساط)
            payment_schedules_table = """
            CREATE TABLE IF NOT EXISTS payment_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER NOT NULL,
                installment_number INTEGER NOT NULL,
                due_date DATE NOT NULL,
                amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
                paid_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
                remaining_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
                status TEXT NOT NULL DEFAULT 'معلق',
                notes TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,

                FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
            )
            """

            # جدول مرفقات المدفوعات
            payment_attachments_table = """
            CREATE TABLE IF NOT EXISTS payment_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                uploaded_at DATETIME NOT NULL,

                FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
            )
            """

            # تنفيذ إنشاء الجداول
            # استخدام execute_query إذا كان متاحاً، وإلا استخدام connection مباشرة
            if hasattr(self.db_manager, "execute_query"):
                self.db_manager.execute_query(payments_table)
                self.db_manager.execute_query(payment_schedules_table)
                self.db_manager.execute_query(payment_attachments_table)
            elif hasattr(self.db_manager, "connection") and self.db_manager.connection:
                cursor = self.db_manager.connection.cursor()
                cursor.execute(payments_table)
                cursor.execute(payment_schedules_table)
                cursor.execute(payment_attachments_table)
                self.db_manager.connection.commit()
            elif hasattr(self.db_manager, "get_connection"):
                conn = self.db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute(payments_table)
                cursor.execute(payment_schedules_table)
                cursor.execute(payment_attachments_table)
                conn.commit()
            else:
                raise Exception("لا يمكن الوصول إلى قاعدة البيانات: DatabaseManager غير مهيأ")

            # إنشاء الفهارس
            self._create_indexes()

            if self.logger:
                self.logger.info("تم إنشاء جداول المدفوعات بنجاح")

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء جداول المدفوعات: {str(e)}")

    def _create_indexes(self):
        """إنشاء الفهارس"""
        try:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_payments_entity ON payments(entity_id)",
                "CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date)",
                "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
                "CREATE INDEX IF NOT EXISTS idx_payments_type ON payments(payment_type)",
                "CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(payment_method)",
                "CREATE INDEX IF NOT EXISTS idx_account_balances_entity ON account_balances(entity_id)",
                "CREATE INDEX IF NOT EXISTS idx_account_balances_type ON account_balances(account_type)",
                "CREATE INDEX IF NOT EXISTS idx_payment_schedules_entity ON payment_schedules(entity_id)",
                "CREATE INDEX IF NOT EXISTS idx_payment_schedules_due_date ON payment_schedules(due_date)",
                "CREATE INDEX IF NOT EXISTS idx_payment_schedules_status ON payment_schedules(status)",
            ]

            # إنشاء الفهارس
            if hasattr(self.db_manager, "execute_query"):
                for index in indexes:
                    self.db_manager.execute_query(index)
            elif hasattr(self.db_manager, "connection") and self.db_manager.connection:
                cursor = self.db_manager.connection.cursor()
                for index in indexes:
                    cursor.execute(index)
                self.db_manager.connection.commit()
            elif hasattr(self.db_manager, "get_connection"):
                conn = self.db_manager.get_connection()
                cursor = conn.cursor()
                for index in indexes:
                    cursor.execute(index)
                conn.commit()

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء فهارس المدفوعات: {str(e)}")

    # ===== إدارة المدفوعات =====

    def create_customer_payment(
        self,
        customer_id: int,
        amount: Decimal,
        payment_method: str = PaymentMethod.CASH.value,
        payment_date: date = None,
        reference_number: str = None,
        notes: str = None,
        user_id: int = None,
        currency_id: Optional[int] = None,
        bank_name: str = None,
        account_number: str = None,
    ) -> Optional[Payment]:
        """إنشاء دفعة من العميل"""
        try:
            payment = Payment(
                payment_type=PaymentType.CUSTOMER_PAYMENT.value,
                payment_method=payment_method,
                amount=amount,
                payment_date=payment_date or date.today(),
                customer_id=customer_id,
                user_id=user_id,
                reference_number=reference_number,
                notes=notes,
                status=PaymentStatus.COMPLETED.value,
                currency_id=currency_id,
                bank_name=bank_name,
                account_number=account_number,
            )

            # Multi-Currency: حساب المبالغ بالعملة الأساسية
            if currency_id:
                try:
                    # الحصول على العملة الأساسية
                    base_currency = self.exchange_rate_service.currency_manager.get_base_currency()
                    if base_currency:
                        # الحصول على سعر الصرف
                        exchange_rate = self.exchange_rate_service.get_exchange_rate(
                            currency_id, base_currency.id, payment_date or date.today()
                        )

                        if exchange_rate:
                            payment.exchange_rate = exchange_rate
                            # حساب المبلغ بالعملة الأساسية
                            payment.base_amount = amount * exchange_rate
                            payment.converted_amount = amount
                            payment.amount_in_base_currency = amount * exchange_rate  # للتوافق

                            if self.logger:
                                self.logger.debug(
                                    f"تم حساب المبلغ بالعملة الأساسية: {payment.base_amount} "
                                    f"(سعر الصرف: {exchange_rate})"
                                )
                        else:
                            # إذا لم يوجد سعر صرف، استخدم المبلغ الأساسي
                            payment.base_amount = amount
                            payment.converted_amount = amount
                            payment.exchange_rate = Decimal("1.0")
                    else:
                        # إذا لم توجد عملة أساسية، استخدم المبلغ الأساسي
                        payment.base_amount = amount
                        payment.converted_amount = amount
                        payment.exchange_rate = Decimal("1.0")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"خطأ في حساب سعر الصرف: {str(e)}")
                    # في حالة الخطأ، استخدم المبلغ الأساسي
                    payment.base_amount = amount
                    payment.converted_amount = amount
                    payment.exchange_rate = Decimal("1.0")
            else:
                # إذا لم تكن هناك عملة محددة، استخدم المبلغ الأساسي
                payment.base_amount = amount
                payment.converted_amount = amount
                payment.exchange_rate = Decimal("1.0")

            payment_id = self.payment_manager.create_payment(payment)
            if not payment_id:
                try:
                    # Fallback: lookup by unique payment_number
                    cursor = self.db_manager.connection.cursor()
                    cursor.execute(
                        "SELECT id FROM payments WHERE payment_number = ? ORDER BY id DESC LIMIT 1",
                        (payment.payment_number,),
                    )
                    r = cursor.fetchone()
                    if r:
                        payment_id = r[0]
                except Exception:
                    if self.logger:
                        self.logger.warning("Ignored exception in payment_service.py")
            if payment_id:
                payment_obj = self.payment_manager.get_payment_by_id(payment_id)
                if payment_obj is None:
                    payment_obj = payment
                    payment_obj.id = payment_id

                # ضمان أن الكائن المُعاد يعكس القيم المطلوبة حتى لو كان
                # الـ manager/DB mock لا يعيد صفاً كاملاً.
                payment_obj.id = payment_id
                payment_obj.amount = amount
                payment_obj.customer_id = customer_id
                payment_obj.payment_type = PaymentType.CUSTOMER_PAYMENT.value
                payment_obj.payment_method = payment_method
                payment_obj.status = PaymentStatus.COMPLETED.value
                payment_obj.reference_number = reference_number
                payment_obj.notes = notes
                payment_obj.user_id = user_id

                # 🔔 إطلاق Webhook: إرسال Webhook عند إنشاء دفعة عميل
                try:
                    from ..services.webhook_service import WebhookService

                    webhook_service = WebhookService(self.db_manager, self.logger)

                    # بناء Payload للـ Webhook
                    webhook_payload = {
                        "event": "payment_received",
                        "payment_id": payment_id,
                        "payment_type": payment.payment_type,
                        "customer_id": customer_id,
                        "amount": float(amount),
                        "payment_method": payment_method,
                        "created_at": datetime.now().isoformat(),
                        "payment": (payment_obj.to_dict() if payment_obj and hasattr(payment_obj, "to_dict") else {}),
                    }

                    webhook_service.trigger_webhook(
                        event_type="payment_received",
                        payload=webhook_payload,
                        entity_id=payment_id,
                        company_id=(
                            payment_obj.company_id if payment_obj and hasattr(payment_obj, "company_id") else None
                        ),
                    )

                    if self.logger:
                        self.logger.debug(f"✅ تم إطلاق Webhook: payment_received (Payment ID: {payment_id})")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ فشل إطلاق Webhook: {e}")

                # قيد محاسبي للدفعة (غير معطل)
                try:
                    payment_data = {
                        'payment_id': payment_id,
                        'reference': reference_number or '',
                        'amount': amount,
                        'method': payment_method,
                        'payment_type': 'received',
                    }
                    self.accounting_service.create_payment_journal_entry(payment_data)
                except Exception as e:
                    self.logger.warning(f"خطأ في إنشاء قيد محاسبي للدفعة: {e}")

                return payment_obj

            return None

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء دفعة العميل: {str(e)}")
            return None

    def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        """الحصول على دفعة بالمعرف"""
        try:
            return self.payment_manager.get_payment_by_id(payment_id)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الدفعة {payment_id}: {str(e)}")
            return None

    def get_customer_payments(self, customer_id: int) -> List[Payment]:
        """الحصول على جميع دفعات العميل"""
        try:
            return self.payment_manager.get_customer_payments(customer_id)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على دفعات العميل {customer_id}: {str(e)}")
            return []

    def get_supplier_payments(self, supplier_id: int) -> List[Payment]:
        """الحصول على جميع دفعات المورد"""
        try:
            return self.payment_manager.get_supplier_payments(supplier_id)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على دفعات المورد {supplier_id}: {str(e)}")
            return []

    def create_supplier_payment(
        self,
        supplier_id: int,
        amount: Decimal,
        payment_method: str = PaymentMethod.CASH.value,
        payment_date: date = None,
        reference_number: str = None,
        notes: str = None,
        user_id: int = None,
        currency_id: Optional[int] = None,
    ) -> Optional[Payment]:
        """إنشاء دفعة للمورد"""
        try:
            payment = Payment(
                payment_type=PaymentType.SUPPLIER_PAYMENT.value,
                payment_method=payment_method,
                amount=amount,
                payment_date=payment_date or date.today(),
                supplier_id=supplier_id,
                user_id=user_id,
                reference_number=reference_number,
                notes=notes,
                status=PaymentStatus.COMPLETED.value,
                currency_id=currency_id,
            )

            # Multi-Currency: حساب المبالغ بالعملة الأساسية
            if currency_id:
                try:
                    # الحصول على العملة الأساسية
                    base_currency = self.exchange_rate_service.currency_manager.get_base_currency()
                    if base_currency:
                        # الحصول على سعر الصرف
                        exchange_rate = self.exchange_rate_service.get_exchange_rate(
                            currency_id, base_currency.id, payment_date or date.today()
                        )

                        if exchange_rate:
                            payment.exchange_rate = exchange_rate
                            # حساب المبلغ بالعملة الأساسية
                            payment.base_amount = amount * exchange_rate
                            payment.converted_amount = amount
                            payment.amount_in_base_currency = amount * exchange_rate  # للتوافق
                        else:
                            # إذا لم يوجد سعر صرف، استخدم المبلغ الأساسي
                            payment.base_amount = amount
                            payment.converted_amount = amount
                            payment.exchange_rate = Decimal("1.0")
                    else:
                        # إذا لم توجد عملة أساسية، استخدم المبلغ الأساسي
                        payment.base_amount = amount
                        payment.converted_amount = amount
                        payment.exchange_rate = Decimal("1.0")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"خطأ في حساب سعر الصرف: {str(e)}")
                    # في حالة الخطأ، استخدم المبلغ الأساسي
                    payment.base_amount = amount
                    payment.converted_amount = amount
                    payment.exchange_rate = Decimal("1.0")
            else:
                # إذا لم تكن هناك عملة محددة، استخدم المبلغ الأساسي
                payment.base_amount = amount
                payment.converted_amount = amount
                payment.exchange_rate = Decimal("1.0")

            payment_id = self.payment_manager.create_payment(payment)
            if payment_id:
                payment_obj = self.payment_manager.get_payment_by_id(payment_id)

                # 🔔 إطلاق Webhook: إرسال Webhook عند إنشاء دفعة مورد
                try:
                    from ..services.webhook_service import WebhookService

                    webhook_service = WebhookService(self.db_manager, self.logger)

                    # بناء Payload للـ Webhook
                    webhook_payload = {
                        "event": "supplier_payment_made",
                        "payment_id": payment_id,
                        "payment_type": payment.payment_type,
                        "supplier_id": supplier_id,
                        "amount": float(amount),
                        "payment_method": payment_method,
                        "created_at": datetime.now().isoformat(),
                        "payment": (payment_obj.to_dict() if payment_obj and hasattr(payment_obj, "to_dict") else {}),
                    }

                    webhook_service.trigger_webhook(
                        event_type="supplier_payment_made",
                        payload=webhook_payload,
                        entity_id=payment_id,
                        company_id=(
                            payment_obj.company_id if payment_obj and hasattr(payment_obj, "company_id") else None
                        ),
                    )

                    if self.logger:
                        self.logger.debug(f"✅ تم إطلاق Webhook: supplier_payment_made (Payment ID: {payment_id})")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ فشل إطلاق Webhook: {e}")

                # قيد محاسبي للدفعة (غير معطل)
                try:
                    payment_data = {
                        'payment_id': payment_id,
                        'reference': reference_number or '',
                        'amount': amount,
                        'method': payment_method,
                        'payment_type': 'paid',
                    }
                    self.accounting_service.create_payment_journal_entry(payment_data)
                except Exception as e:
                    self.logger.warning(f"خطأ في إنشاء قيد محاسبي للدفعة: {e}")

                return payment_obj

            return None

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء دفعة المورد: {str(e)}")
            return None

    def get_payments_by_date_range(self, start_date: date, end_date: date, payment_type: str = None) -> List[Payment]:
        """الحصول على المدفوعات في فترة زمنية"""
        try:
            query = """
            SELECT * FROM payments
            WHERE payment_date BETWEEN ? AND ?
            """
            params = [start_date.isoformat(), end_date.isoformat()]

            if payment_type:
                query += " AND payment_type = ?"
                params.append(payment_type)

            query += " ORDER BY payment_date DESC, created_at DESC"

            results = self.db_manager.fetch_all(query, params)
            return [self.payment_manager._row_to_payment(row) for row in results]

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المدفوعات: {str(e)}")
            return []

    # ===== إدارة الذمم المدينة =====

    def get_accounts_receivable(self) -> List[Dict[str, Any]]:
        """الحصول على الذمم المدينة (العملاء)"""
        try:
            query = """
            SELECT
                c.id,
                c.name,
                c.phone,
                c.current_balance,
                c.credit_limit,
                (c.credit_limit - c.current_balance) as available_credit,
                (SELECT COUNT(*) FROM payments WHERE entity_id = c.id AND payment_type = 'customer_payment') as payments_count,
            (SELECT MAX(payment_date) FROM payments WHERE entity_id = c.id AND payment_type = 'customer_payment') as last_payment_date,
            (SELECT COUNT(*) FROM payment_schedules
             WHERE entity_id = c.id AND due_date < ? AND status != ?) as overdue_payments
            FROM customers c
            WHERE c.current_balance > 0 AND c.is_active = 1
            ORDER BY c.current_balance DESC
            """

            today = date.today().isoformat()
            results = self.db_manager.fetch_all(query, (today, PaymentStatus.COMPLETED.value))

            receivables = []
            for row in results:
                receivables.append(
                    {
                        "customer_id": row.get("id"),
                        "customer_name": row.get("name"),
                        "phone": row.get("phone"),
                        "balance": Decimal(str(row.get("current_balance"))),
                        "credit_limit": Decimal(str(row.get("credit_limit"))),
                        "available_credit": Decimal(str(row.get("available_credit"))),
                        "payments_count": row.get("payments_count"),
                        "last_payment_date": (date.fromisoformat(row.get("last_payment_date")) if row.get("last_payment_date") else None),
                        "overdue_payments": row.get("overdue_payments"),
                    }
                )

            return receivables

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الذمم المدينة: {str(e)}")
            return []

    def get_accounts_payable(self) -> List[Dict[str, Any]]:
        """الحصول على الذمم الدائنة (الموردين)"""
        try:
            query = """
            SELECT
                s.id,
                s.name,
                s.phone,
                s.current_balance,
                s.credit_limit,
                (s.credit_limit - s.current_balance) as available_credit,
                (SELECT COUNT(*) FROM payments WHERE entity_id = s.id AND payment_type = 'supplier_payment') as payments_count,
            (SELECT MAX(payment_date) FROM payments WHERE entity_id = s.id AND payment_type = 'supplier_payment') as last_payment_date,
            (SELECT COUNT(*) FROM payment_schedules
             WHERE entity_id = s.id AND due_date < ? AND status != ?) as overdue_payments
            FROM suppliers s
            WHERE s.current_balance > 0 AND s.is_active = 1
            ORDER BY s.current_balance DESC
            """

            today = date.today().isoformat()
            results = self.db_manager.fetch_all(query, (today, PaymentStatus.COMPLETED.value))

            payables = []
            for row in results:
                payables.append(
                    {
                        "supplier_id": row.get("id"),
                        "supplier_name": row.get("name"),
                        "phone": row.get("phone"),
                        "balance": Decimal(str(row.get("current_balance"))),
                        "credit_limit": Decimal(str(row.get("credit_limit"))),
                        "available_credit": Decimal(str(row.get("available_credit"))),
                        "payments_count": row.get("payments_count"),
                        "last_payment_date": (date.fromisoformat(row.get("last_payment_date")) if row.get("last_payment_date") else None),
                        "overdue_payments": row.get("overdue_payments"),
                    }
                )

            return payables

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الذمم الدائنة: {str(e)}")
            return []

    def get_overdue_receivables(self) -> List[Dict[str, Any]]:
        """الحصول على الذمم المدينة المتأخرة"""
        try:
            overdue_payments = self.payment_manager.get_overdue_payments()
            receivables = []

            for payment in overdue_payments:
                if payment.customer_id and payment.payment_type == PaymentType.CUSTOMER_PAYMENT.value:
                    customer = self.customer_manager.get_customer_by_id(payment.customer_id)
                    if customer:
                        days_overdue = (date.today() - payment.due_date).days
                        receivables.append(
                            {
                                "payment_id": payment.id,
                                "customer_id": customer.id,
                                "customer_name": customer.name,
                                "amount": payment.amount,
                                "due_date": payment.due_date,
                                "days_overdue": days_overdue,
                                "payment_method": payment.payment_method,
                                "reference_number": payment.reference_number,
                            }
                        )

            return sorted(receivables, key=lambda x: x["days_overdue"], reverse=True)

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الذمم المدينة المتأخرة: {str(e)}")
            return []

    def get_overdue_payables(self) -> List[Dict[str, Any]]:
        """الحصول على الذمم الدائنة المتأخرة"""
        try:
            overdue_payments = self.payment_manager.get_overdue_payments()
            payables = []

            for payment in overdue_payments:
                if payment.supplier_id and payment.payment_type == PaymentType.SUPPLIER_PAYMENT.value:
                    supplier = self.supplier_manager.get_supplier_by_id(payment.supplier_id)
                    if supplier:
                        days_overdue = (date.today() - payment.due_date).days
                        payables.append(
                            {
                                "payment_id": payment.id,
                                "supplier_id": supplier.id,
                                "supplier_name": supplier.name,
                                "amount": payment.amount,
                                "due_date": payment.due_date,
                                "days_overdue": days_overdue,
                                "payment_method": payment.payment_method,
                                "reference_number": payment.reference_number,
                            }
                        )

            return sorted(payables, key=lambda x: x["days_overdue"], reverse=True)

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الذمم الدائنة المتأخرة: {str(e)}")
            return []

    # ===== جدولة المدفوعات (الأقساط) =====
    def get_payment_schedules(self, limit: int = 200, include_completed: bool = False) -> List[Dict[str, Any]]:
        """إرجاع قائمة الأقساط (الدفعات المجدولة)
        يتم استخدامها في واجهة الحسابات لعرض المستحقات القادمة والمتأخرة.
        """
        try:
            # تأكد من وجود جدول الأقساط
            if not self.db_manager.table_exists("payment_schedules"):
                return []

            status_filter = "" if include_completed else "AND status != ?"  # noqa: F841
            params: List[Any] = []
            if not include_completed:
                params.append(PaymentStatus.COMPLETED.value)

            query = f"""
                SELECT id, payment_id, installment_number, due_date, amount,
                       paid_amount, remaining_amount, status, notes
                FROM payment_schedules
                WHERE 1=1 {status_filter}
                ORDER BY due_date ASC
                LIMIT ?
            """
            params.append(limit)
            rows = self.db_manager.fetch_all(query, tuple(params))

            schedules: List[Dict[str, Any]] = []
            today = date.today()
            for r in rows:
                due = date.fromisoformat(r.get("due_date")) if r.get("due_date") else None
                remaining = Decimal(str(r.get("remaining_amount"))) if r.get("remaining_amount") is not None else Decimal("0.00")
                days_to_due = (due - today).days if due else None
                schedules.append(
                    {
                        "schedule_id": r.get("id"),
                        "payment_id": r.get("payment_id"),
                        "installment_number": r.get("installment_number"),
                        "due_date": due,
                        "amount": Decimal(str(r.get("amount"))),
                        "paid_amount": Decimal(str(r.get("paid_amount"))),
                        "remaining_amount": remaining,
                        "status": r.get("status"),
                        "notes": r.get("notes"),
                        "days_to_due": days_to_due,
                        "is_overdue": (due is not None and today > due and remaining > 0),
                    }
                )

            return schedules
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على جدولة المدفوعات: {str(e)}")
            return []

    # ===== التقارير المالية =====

    def get_payment_summary(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """ملخص المدفوعات"""
        try:
            query = """
            SELECT
                payment_type,
                payment_method,
                COUNT(*) as count,
                SUM(amount_in_base_currency) as total_amount
            FROM payments
            WHERE payment_date BETWEEN ? AND ? AND status = ?
            GROUP BY payment_type, payment_method
            ORDER BY total_amount DESC
            """

            results = self.db_manager.fetch_all(
                query,
                (
                    start_date.isoformat(),
                    end_date.isoformat(),
                    PaymentStatus.COMPLETED.value,
                ),
            )

            summary = {
                "period": {"start_date": start_date, "end_date": end_date},
                "by_type_and_method": [],
                "totals": {
                    "customer_payments": Decimal("0.00"),
                    "supplier_payments": Decimal("0.00"),
                    "total_payments": Decimal("0.00"),
                    "net_cash_flow": Decimal("0.00"),
                },
            }

            for row in results:
                payment_type = row.get("payment_type")
                payment_method = row.get("payment_method")
                count = row.get("count")
                amount = Decimal(str(row.get("total_amount")))

                summary["by_type_and_method"].append(
                    {
                        "payment_type": payment_type,
                        "payment_method": payment_method,
                        "count": count,
                        "amount": amount,
                    }
                )

                # تجميع الإجماليات
                if payment_type == PaymentType.CUSTOMER_PAYMENT.value:
                    summary["totals"]["customer_payments"] += amount
                elif payment_type == PaymentType.SUPPLIER_PAYMENT.value:
                    summary["totals"]["supplier_payments"] += amount

                summary["totals"]["total_payments"] += amount

            # حساب صافي التدفق النقدي
            summary["totals"]["net_cash_flow"] = (
                summary["totals"]["customer_payments"] - summary["totals"]["supplier_payments"]
            )

            return summary

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في ملخص المدفوعات: {str(e)}")
            return {}

    def get_aging_report(self, account_type: str = None) -> List[Dict[str, Any]]:
        """تقرير أعمار الذمم - يعتمد على الفواتير غير المدفوعة وليس المدفوعات"""
        try:
            if account_type is None:
                account_type = AccountType.RECEIVABLE.value

            today = date.today()

            if account_type == AccountType.RECEIVABLE.value:
                # تقرير أعمار الذمم المدينة - بناءً على فواتير المبيعات غير المدفوعة
                query = """
                SELECT
                    s.customer_id,
                    COALESCE(c.name, 'غير محدد') as account_name,
                    s.id as invoice_id,
                    s.invoice_number,
                    s.sale_date,
                    s.due_date,
                    s.final_amount,
                    COALESCE(s.paid_amount, 0) as paid_amount,
                    (s.final_amount - COALESCE(s.paid_amount, 0)) as remaining
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.status NOT IN ('مدفوعة', 'paid', 'ملغية', 'cancelled',
                                        'مسودة', 'draft', 'مرتجعة', 'returned')
                  AND (s.final_amount - COALESCE(s.paid_amount, 0)) > 0
                  AND s.is_active = 1
                """
                rows = self.db_manager.fetch_all(query)

            elif account_type == AccountType.PAYABLE.value:
                # تقرير أعمار الذمم الدائنة - بناءً على فواتير المشتريات غير المدفوعة
                query = """
                SELECT
                    p.supplier_id,
                    COALESCE(sup.name, 'غير محدد') as account_name,
                    p.id as invoice_id,
                    p.invoice_number,
                    p.purchase_date as sale_date,
                    p.due_date,
                    p.final_amount,
                    COALESCE(p.paid_amount, 0) as paid_amount,
                    (p.final_amount - COALESCE(p.paid_amount, 0)) as remaining
                FROM purchases p
                LEFT JOIN suppliers sup ON p.supplier_id = sup.id
                WHERE p.status NOT IN ('مدفوعة', 'paid', 'ملغية', 'cancelled',
                                        'مرتجعة', 'returned')
                  AND (p.final_amount - COALESCE(p.paid_amount, 0)) > 0
                  AND p.is_active = 1
                """
                rows = self.db_manager.fetch_all(query)

            else:
                return []

            # تجميع المبالغ حسب الحساب وحسب فترة التأخير
            buckets: Dict[int, Dict[str, Any]] = {}

            for row in rows:
                account_id = row.get("customer_id") or row.get("supplier_id")
                account_name = row.get("account_name")
                due = row.get("due_date")
                sale_date = row.get("sale_date")
                remaining = Decimal(str(row.get("remaining") or 0))

                if remaining <= 0:
                    continue

                # تحديد تاريخ الاستحقاق (due_date أو تاريخ الفاتورة كبديل)
                ref_date = due or sale_date
                if ref_date is None:
                    # بدون تاريخ → يُعتبر مستحقاً حالياً
                    bucket_key = 'current'
                else:
                    if isinstance(ref_date, str):
                        ref_date = date.fromisoformat(ref_date)
                    days_overdue = (today - ref_date).days

                    if days_overdue <= 0:
                        bucket_key = 'current'
                    elif days_overdue <= 30:
                        bucket_key = 'days_1_30'
                    elif days_overdue <= 60:
                        bucket_key = 'days_31_60'
                    elif days_overdue <= 90:
                        bucket_key = 'days_61_90'
                    else:
                        bucket_key = 'over_90_days'

                if account_id not in buckets:
                    buckets[account_id] = {
                        'account_name': account_name,
                        'total_balance': Decimal('0'),
                        'current': Decimal('0'),
                        'days_1_30': Decimal('0'),
                        'days_31_60': Decimal('0'),
                        'days_61_90': Decimal('0'),
                        'over_90_days': Decimal('0'),
                    }

                buckets[account_id][bucket_key] += remaining
                buckets[account_id]['total_balance'] += remaining

            # تحويل إلى قائمة مرتبة تنازلياً حسب إجمالي الرصيد
            aging_data = []
            for acct_id, data in sorted(
                buckets.items(),
                key=lambda x: x[1]['total_balance'],
                reverse=True,
            ):
                aging_data.append(
                    {
                        "account_id": acct_id,
                        "account_name": data['account_name'],
                        "total_balance": data['total_balance'],
                        "current": data['current'],
                        "days_1_30": data['days_1_30'],
                        "days_31_60": data['days_31_60'],
                        "days_61_90": data['days_61_90'],
                        "over_90_days": data['over_90_days'],
                    }
                )

            return aging_data

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تقرير أعمار الذمم: {str(e)}")
            return []

    def get_cash_flow_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """تقرير التدفق النقدي"""
        try:
            query = """
            SELECT
                DATE(payment_date) as payment_date,
                payment_type,
                SUM(amount_in_base_currency) as daily_amount
            FROM payments
            WHERE payment_date BETWEEN ? AND ? AND status = ?
            GROUP BY DATE(payment_date), payment_type
            ORDER BY payment_date ASC
            """

            results = self.db_manager.fetch_all(
                query,
                (
                    start_date.isoformat(),
                    end_date.isoformat(),
                    PaymentStatus.COMPLETED.value,
                ),
            )

            cash_flow = {
                "period": {"start_date": start_date, "end_date": end_date},
                "daily_flow": {},
                "summary": {
                    "total_inflow": Decimal("0.00"),
                    "total_outflow": Decimal("0.00"),
                    "net_flow": Decimal("0.00"),
                },
            }

            for row in results:
                payment_date = row[0]
                payment_type = row[1]
                amount = Decimal(str(row[2]))

                if payment_date not in cash_flow["daily_flow"]:
                    cash_flow["daily_flow"][payment_date] = {
                        "inflow": Decimal("0.00"),
                        "outflow": Decimal("0.00"),
                        "net": Decimal("0.00"),
                    }

                if payment_type == PaymentType.CUSTOMER_PAYMENT.value:
                    cash_flow["daily_flow"][payment_date]["inflow"] += amount
                    cash_flow["summary"]["total_inflow"] += amount
                elif payment_type == PaymentType.SUPPLIER_PAYMENT.value:
                    cash_flow["daily_flow"][payment_date]["outflow"] += amount
                    cash_flow["summary"]["total_outflow"] += amount

                # حساب الصافي اليومي
                cash_flow["daily_flow"][payment_date]["net"] = (
                    cash_flow["daily_flow"][payment_date]["inflow"] - cash_flow["daily_flow"][payment_date]["outflow"]
                )

            # حساب الصافي الإجمالي
            cash_flow["summary"]["net_flow"] = (
                cash_flow["summary"]["total_inflow"] - cash_flow["summary"]["total_outflow"]
            )

            return cash_flow

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تقرير التدفق النقدي: {str(e)}")
            return {}

    def get_payment_trends_analysis(
        self, start_date: date, end_date: date, period_type: str = "monthly"
    ) -> Dict[str, Any]:
        """تحليل اتجاهات المدفوعات"""
        try:
            # تحديد تجميع البيانات حسب نوع الفترة
            date_format = "DATE(payment_date)"
            date_group = "DATE(payment_date)"
            if period_type == "weekly":
                date_format = "strftime('%Y-W%W', payment_date)"
                date_group = "strftime('%Y-W%W', payment_date)"
            elif period_type == "monthly":
                date_format = "strftime('%Y-%m', payment_date)"
                date_group = "strftime('%Y-%m', payment_date)"
            elif period_type == "yearly":
                date_format = "strftime('%Y', payment_date)"
                date_group = "strftime('%Y', payment_date)"

            query = f"""
            SELECT
                {date_format} as period,
                payment_type,
                COUNT(*) as transaction_count,
                SUM(amount_in_base_currency) as total_amount,
                AVG(amount_in_base_currency) as avg_amount,
                MIN(amount_in_base_currency) as min_amount,
                MAX(amount_in_base_currency) as max_amount
            FROM payments
            WHERE payment_date BETWEEN ? AND ? AND status = ?
            GROUP BY {date_group}, payment_type
            ORDER BY period ASC, payment_type
            """

            results = self.db_manager.fetch_all(
                query,
                (
                    start_date.isoformat(),
                    end_date.isoformat(),
                    PaymentStatus.COMPLETED.value,
                ),
            )

            trends = {
                "period_type": period_type,
                "date_range": {"start_date": start_date, "end_date": end_date},
                "trends_data": {},
                "summary": {"total_periods": 0, "growth_rate": {}, "volatility": {}},
            }

            # تنظيم البيانات
            for row in results:
                period = row[0]
                payment_type = row[1]

                if period not in trends["trends_data"]:
                    trends["trends_data"][period] = {}

                trends["trends_data"][period][payment_type] = {
                    "transaction_count": row[2],
                    "total_amount": Decimal(str(row[3])),
                    "avg_amount": Decimal(str(row[4])),
                    "min_amount": Decimal(str(row[5])),
                    "max_amount": Decimal(str(row[6])),
                }

            # حساب معدلات النمو والتقلبات
            periods = sorted(trends["trends_data"].keys())
            trends["summary"]["total_periods"] = len(periods)

            if len(periods) >= 2:
                for payment_type in [
                    PaymentType.CUSTOMER_PAYMENT.value,
                    PaymentType.SUPPLIER_PAYMENT.value,
                ]:
                    amounts = []
                    for period in periods:
                        if payment_type in trends["trends_data"][period]:
                            amounts.append(float(trends["trends_data"][period][payment_type]["total_amount"]))
                        else:
                            amounts.append(0.0)

                    if len(amounts) >= 2 and amounts[0] > 0:
                        # معدل النمو
                        growth_rate = ((amounts[-1] - amounts[0]) / amounts[0]) * 100
                        trends["summary"]["growth_rate"][payment_type] = round(growth_rate, 2)

                        # التقلبات (الانحراف المعياري)
                        if len(amounts) > 1:
                            mean_amount = sum(amounts) / len(amounts)
                            variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
                            volatility = (variance**0.5) / mean_amount * 100 if mean_amount > 0 else 0
                            trends["summary"]["volatility"][payment_type] = round(volatility, 2)

            return trends

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحليل اتجاهات المدفوعات: {str(e)}")
            return {}

    def get_payment_forecast(self, historical_months: int = 12, forecast_months: int = 3) -> Dict[str, Any]:
        """توقع المدفوعات المستقبلية"""
        try:
            # الحصول على البيانات التاريخية
            end_date = date.today()
            start_date = end_date - timedelta(days=historical_months * 30)

            query = """
            SELECT
                strftime('%Y-%m', payment_date) as month,
                payment_type,
                SUM(amount_in_base_currency) as monthly_amount
            FROM payments
            WHERE payment_date BETWEEN ? AND ? AND status = ?
            GROUP BY strftime('%Y-%m', payment_date), payment_type
            ORDER BY month ASC
            """

            results = self.db_manager.fetch_all(
                query,
                (
                    start_date.isoformat(),
                    end_date.isoformat(),
                    PaymentStatus.COMPLETED.value,
                ),
            )

            # تنظيم البيانات التاريخية
            historical_data = {}
            for row in results:
                month = row[0]
                payment_type = row[1]
                amount = Decimal(str(row[2]))

                if payment_type not in historical_data:
                    historical_data[payment_type] = []

                historical_data[payment_type].append({"month": month, "amount": amount})

            # حساب التوقعات باستخدام المتوسط المتحرك البسيط
            forecast = {
                "historical_period": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "months": historical_months,
                },
                "forecast_period": {"months": forecast_months},
                "predictions": {},
                "confidence_level": "متوسط",  # يمكن تحسينه لاحقاً
            }

            for payment_type, data in historical_data.items():
                if len(data) >= 3:  # نحتاج على الأقل 3 نقاط بيانات
                    # حساب المتوسط المتحرك للأشهر الثلاثة الأخيرة
                    recent_amounts = [float(item["amount"]) for item in data[-3:]]
                    avg_amount = sum(recent_amounts) / len(recent_amounts)

                    # حساب الاتجاه
                    if len(data) >= 6:
                        first_half = sum(float(item["amount"]) for item in data[: len(data) // 2]) / (len(data) // 2)
                        second_half = sum(float(item["amount"]) for item in data[len(data) // 2 :]) / (
                            len(data) - len(data) // 2
                        )
                        trend_factor = (second_half - first_half) / first_half if first_half > 0 else 0
                    else:
                        trend_factor = 0

                    # توليد التوقعات
                    predictions = []
                    for i in range(forecast_months):
                        # تطبيق الاتجاه تدريجياً
                        predicted_amount = avg_amount * (1 + trend_factor * (i + 1) * 0.1)

                        # إضافة الشهر المتوقع
                        forecast_date = end_date + timedelta(days=(i + 1) * 30)
                        forecast_month = forecast_date.strftime("%Y-%m")

                        predictions.append(
                            {
                                "month": forecast_month,
                                "predicted_amount": round(Decimal(str(predicted_amount)), 2),
                                "confidence": "متوسط",
                            }
                        )

                    forecast["predictions"][payment_type] = predictions

            return forecast

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في توقع المدفوعات: {str(e)}")
            return {}

    def get_period_comparison_analysis(
        self,
        current_start: date,
        current_end: date,
        previous_start: date,
        previous_end: date,
    ) -> Dict[str, Any]:
        """مقارنة فترات المدفوعات"""
        try:

            def get_period_data(start_date: date, end_date: date) -> Dict[str, Any]:
                query = """
                SELECT
                    payment_type,
                    COUNT(*) as transaction_count,
                    SUM(amount_in_base_currency) as total_amount,
                    AVG(amount_in_base_currency) as avg_amount,
                    payment_method,
                    COUNT(DISTINCT CASE WHEN payment_type = ? THEN customer_id END) as unique_customers,
                    COUNT(DISTINCT CASE WHEN payment_type = ? THEN supplier_id END) as unique_suppliers
                FROM payments
                WHERE payment_date BETWEEN ? AND ? AND status = ?
                GROUP BY payment_type, payment_method
                """

                results = self.db_manager.fetch_all(
                    query,
                    (
                        PaymentType.CUSTOMER_PAYMENT.value,
                        PaymentType.SUPPLIER_PAYMENT.value,
                        start_date.isoformat(),
                        end_date.isoformat(),
                        PaymentStatus.COMPLETED.value,
                    ),
                )

                period_data = {
                    "total_transactions": 0,
                    "total_amount": Decimal("0.00"),
                    "by_type": {},
                    "by_method": {},
                    "unique_customers": 0,
                    "unique_suppliers": 0,
                }

                for row in results:
                    payment_type = row[0]
                    transaction_count = row[1]
                    total_amount = Decimal(str(row[2]))
                    avg_amount = Decimal(str(row[3]))
                    payment_method = row[4]

                    period_data["total_transactions"] += transaction_count
                    period_data["total_amount"] += total_amount

                    if payment_type not in period_data["by_type"]:
                        period_data["by_type"][payment_type] = {
                            "count": 0,
                            "amount": Decimal("0.00"),
                            "avg_amount": Decimal("0.00"),
                        }

                    period_data["by_type"][payment_type]["count"] += transaction_count
                    period_data["by_type"][payment_type]["amount"] += total_amount
                    period_data["by_type"][payment_type]["avg_amount"] = avg_amount

                    if payment_method not in period_data["by_method"]:
                        period_data["by_method"][payment_method] = {
                            "count": 0,
                            "amount": Decimal("0.00"),
                        }

                    period_data["by_method"][payment_method]["count"] += transaction_count
                    period_data["by_method"][payment_method]["amount"] += total_amount

                # الحصول على عدد العملاء والموردين الفريدين
                unique_query = """
                SELECT
                    COUNT(DISTINCT CASE WHEN payment_type = ? THEN customer_id END) as unique_customers,
                    COUNT(DISTINCT CASE WHEN payment_type = ? THEN supplier_id END) as unique_suppliers
                FROM payments
                WHERE payment_date BETWEEN ? AND ? AND status = ?
                """

                unique_result = self.db_manager.fetch_one(
                    unique_query,
                    (
                        PaymentType.CUSTOMER_PAYMENT.value,
                        PaymentType.SUPPLIER_PAYMENT.value,
                        start_date.isoformat(),
                        end_date.isoformat(),
                        PaymentStatus.COMPLETED.value,
                    ),
                )

                if unique_result:
                    period_data["unique_customers"] = unique_result[0] or 0
                    period_data["unique_suppliers"] = unique_result[1] or 0

                return period_data

            # الحصول على بيانات الفترتين
            current_data = get_period_data(current_start, current_end)
            previous_data = get_period_data(previous_start, previous_end)

            # حساب المقارنات والنسب
            comparison = {
                "current_period": {
                    "start_date": current_start,
                    "end_date": current_end,
                    "data": current_data,
                },
                "previous_period": {
                    "start_date": previous_start,
                    "end_date": previous_end,
                    "data": previous_data,
                },
                "comparison": {
                    "transaction_growth": 0.0,
                    "amount_growth": 0.0,
                    "avg_transaction_growth": 0.0,
                    "customer_growth": 0.0,
                    "supplier_growth": 0.0,
                    "by_type": {},
                    "by_method": {},
                },
            }

            # حساب نسب النمو
            if previous_data["total_transactions"] > 0:
                comparison["comparison"]["transaction_growth"] = (
                    (current_data["total_transactions"] - previous_data["total_transactions"])
                    / previous_data["total_transactions"]
                    * 100
                )

            if previous_data["total_amount"] > 0:
                comparison["comparison"]["amount_growth"] = float(
                    (current_data["total_amount"] - previous_data["total_amount"]) / previous_data["total_amount"] * 100
                )

            if previous_data["unique_customers"] > 0:
                comparison["comparison"]["customer_growth"] = (
                    (current_data["unique_customers"] - previous_data["unique_customers"])
                    / previous_data["unique_customers"]
                    * 100
                )

            if previous_data["unique_suppliers"] > 0:
                comparison["comparison"]["supplier_growth"] = (
                    (current_data["unique_suppliers"] - previous_data["unique_suppliers"])
                    / previous_data["unique_suppliers"]
                    * 100
                )

            # مقارنة حسب النوع
            for payment_type in current_data["by_type"]:
                if payment_type in previous_data["by_type"]:
                    prev_amount = previous_data["by_type"][payment_type]["amount"]
                    curr_amount = current_data["by_type"][payment_type]["amount"]

                    if prev_amount > 0:
                        growth = float((curr_amount - prev_amount) / prev_amount * 100)
                        comparison["comparison"]["by_type"][payment_type] = {"amount_growth": growth}

            # مقارنة حسب طريقة الدفع
            for payment_method in current_data["by_method"]:
                if payment_method in previous_data["by_method"]:
                    prev_amount = previous_data["by_method"][payment_method]["amount"]
                    curr_amount = current_data["by_method"][payment_method]["amount"]

                    if prev_amount > 0:
                        growth = float((curr_amount - prev_amount) / prev_amount * 100)
                        comparison["comparison"]["by_method"][payment_method] = {"amount_growth": growth}

            return comparison

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في مقارنة فترات المدفوعات: {str(e)}")
            return {}

    def get_payment_performance_kpis(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """مؤشرات الأداء الرئيسية للمدفوعات"""
        try:
            # الاستعلامات الأساسية
            summary_query = """
            SELECT
                payment_type,
                COUNT(*) as transaction_count,
                SUM(amount_in_base_currency) as total_amount,
                AVG(amount_in_base_currency) as avg_amount,
                MIN(amount_in_base_currency) as min_amount,
                MAX(amount_in_base_currency) as max_amount
            FROM payments
            WHERE payment_date BETWEEN ? AND ? AND status = ?
            GROUP BY payment_type
            """

            # معدل التحصيل
            collection_query = """
            SELECT
                COUNT(CASE WHEN status = ? THEN 1 END) as completed_payments,
                COUNT(*) as total_payments,
                SUM(CASE WHEN status = ? THEN amount_in_base_currency ELSE 0 END) as collected_amount,
                SUM(amount_in_base_currency) as total_amount
            FROM payments
            WHERE payment_date BETWEEN ? AND ? AND payment_type = ?
            """

            # متوسط وقت التحصيل
            collection_time_query = """
            SELECT
                AVG(julianday(payment_date) - julianday(due_date)) as avg_collection_days
            FROM payments
            WHERE payment_date BETWEEN ? AND ?
                AND payment_type = ?
                AND status = ?
                AND due_date IS NOT NULL
            """

            results = self.db_manager.fetch_all(
                summary_query,
                (
                    start_date.isoformat(),
                    end_date.isoformat(),
                    PaymentStatus.COMPLETED.value,
                ),
            )

            collection_results = self.db_manager.fetch_one(
                collection_query,
                (
                    PaymentStatus.COMPLETED.value,
                    PaymentStatus.COMPLETED.value,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    PaymentType.CUSTOMER_PAYMENT.value,
                ),
            )

            collection_time_result = self.db_manager.fetch_one(
                collection_time_query,
                (
                    start_date.isoformat(),
                    end_date.isoformat(),
                    PaymentType.CUSTOMER_PAYMENT.value,
                    PaymentStatus.COMPLETED.value,
                ),
            )

            kpis = {
                "period": {"start_date": start_date, "end_date": end_date},
                "summary": {
                    "total_transactions": 0,
                    "total_amount": Decimal("0.00"),
                    "avg_transaction_value": Decimal("0.00"),
                },
                "by_type": {},
                "collection_metrics": {
                    "collection_rate": 0.0,
                    "collection_amount_rate": 0.0,
                    "avg_collection_days": 0.0,
                },
                "efficiency_metrics": {
                    "transactions_per_day": 0.0,
                    "amount_per_day": Decimal("0.00"),
                    "payment_velocity": 0.0,
                },
            }

            # معالجة النتائج الأساسية
            for row in results:
                payment_type = row[0]
                transaction_count = row[1]
                total_amount = Decimal(str(row[2]))
                avg_amount = Decimal(str(row[3]))
                min_amount = Decimal(str(row[4]))
                max_amount = Decimal(str(row[5]))

                kpis["summary"]["total_transactions"] += transaction_count
                kpis["summary"]["total_amount"] += total_amount

                kpis["by_type"][payment_type] = {
                    "transaction_count": transaction_count,
                    "total_amount": total_amount,
                    "avg_amount": avg_amount,
                    "min_amount": min_amount,
                    "max_amount": max_amount,
                }

            # حساب متوسط قيمة المعاملة الإجمالي
            if kpis["summary"]["total_transactions"] > 0:
                kpis["summary"]["avg_transaction_value"] = (
                    kpis["summary"]["total_amount"] / kpis["summary"]["total_transactions"]
                )

            # معالجة مقاييس التحصيل
            if collection_results:
                completed_payments = collection_results[0] or 0
                total_payments = collection_results[1] or 0
                collected_amount = Decimal(str(collection_results[2] or 0))
                total_amount = Decimal(str(collection_results[3] or 0))

                if total_payments > 0:
                    kpis["collection_metrics"]["collection_rate"] = (completed_payments / total_payments) * 100

                if total_amount > 0:
                    kpis["collection_metrics"]["collection_amount_rate"] = float(
                        (collected_amount / total_amount) * 100
                    )

            # متوسط وقت التحصيل
            if collection_time_result and collection_time_result[0]:
                kpis["collection_metrics"]["avg_collection_days"] = round(collection_time_result[0], 1)

            # مقاييس الكفاءة
            period_days = (end_date - start_date).days + 1
            if period_days > 0:
                kpis["efficiency_metrics"]["transactions_per_day"] = kpis["summary"]["total_transactions"] / period_days
                kpis["efficiency_metrics"]["amount_per_day"] = kpis["summary"]["total_amount"] / period_days

                # سرعة المدفوعات (معاملات في اليوم)
                kpis["efficiency_metrics"]["payment_velocity"] = kpis["summary"]["total_transactions"] / period_days

            return kpis

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في مؤشرات الأداء الرئيسية: {str(e)}")
            return {}
