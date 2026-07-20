"""
نموذج بيانات المدفوعات والذمم المدينة والدائنة
"""
import logging

import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


class PaymentType(Enum):
    """أنواع المدفوعات"""

    CUSTOMER_PAYMENT = "دفعة عميل"  # دفعة من العميل (ذمة مدينة)
    SUPPLIER_PAYMENT = "دفعة مورد"  # دفعة للمورد (ذمة دائنة)
    EXPENSE = "مصروف"
    INCOME = "إيراد"
    REFUND = "استرداد"


class PaymentMethod(Enum):
    """طرق الدفع"""

    CASH = "نقدي"
    BANK_TRANSFER = "تحويل بنكي"
    CHECK = "شيك"
    CREDIT_CARD = "بطاقة ائتمان"
    DEBIT_CARD = "بطاقة خصم"
    ONLINE = "دفع إلكتروني"


class PaymentStatus(Enum):
    """حالات المدفوعات"""

    PENDING = "معلق"
    COMPLETED = "مكتمل"
    CANCELLED = "ملغي"
    FAILED = "فاشل"
    REFUNDED = "مسترد"


class AccountType(Enum):
    """أنواع الحسابات"""

    RECEIVABLE = "ذمة مدينة"  # العملاء يدينون لنا
    PAYABLE = "ذمة دائنة"  # نحن ندين للموردين
    CASH = "نقدية"
    BANK = "بنكي"
    EXPENSE = "مصروف"
    INCOME = "إيراد"


@dataclass
class Payment:
    """نموذج بيانات الدفعة"""

    id: Optional[int] = None
    payment_number: str = ""  # رقم الدفعة
    payment_type: str = PaymentType.CUSTOMER_PAYMENT.value
    payment_method: str = PaymentMethod.CASH.value
    status: str = PaymentStatus.PENDING.value

    # المبلغ والعملة
    amount: Decimal = Decimal("0.00")
    currency: str = "DZD"  # للتوافق مع الكود القديم
    # Multi-Currency Support
    currency_id: Optional[int] = None  # معرف العملة المستخدمة
    exchange_rate: Decimal = Decimal("1.00")
    base_amount: Optional[Decimal] = None  # المبلغ بالعملة الأساسية
    converted_amount: Optional[Decimal] = None  # المبلغ بالعملة المحددة
    amount_in_base_currency: Decimal = Decimal("0.00")  # للتوافق مع الكود القديم

    # التواريخ
    payment_date: date = field(default_factory=date.today)
    due_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # الأطراف المعنية
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    user_id: Optional[int] = None  # المستخدم الذي أدخل الدفعة

    # الفواتير المرتبطة
    sale_id: Optional[int] = None
    purchase_id: Optional[int] = None

    # تفاصيل إضافية
    reference_number: Optional[str] = None  # رقم مرجعي (رقم الشيك، رقم التحويل، إلخ)
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    notes: Optional[str] = None

    # معلومات المحاسبة
    account_code: Optional[str] = None
    cost_center: Optional[str] = None

    # الملفات المرفقة
    attachments: List[str] = field(default_factory=list)

    def __post_init__(self):
        """معالجة ما بعد الإنشاء"""
        # توليد رقم الدفعة إذا لم يكن موجوداً
        if not self.payment_number:
            self.payment_number = self.generate_payment_number()

        # تعيين التواريخ
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # حساب المبلغ بالعملة الأساسية
        if self.exchange_rate and self.exchange_rate > 0:
            self.amount_in_base_currency = self.amount * self.exchange_rate
        else:
            self.amount_in_base_currency = self.amount

    def generate_payment_number(self) -> str:
        """توليد رقم الدفعة مع ضمان التفرد"""
        import secrets

        now = datetime.now()
        # إضافة جزء عشوائي وجزء من التوقيت بالملي ثانية لضمان التفرد في الاختبارات السريعة
        return f"PAY-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "payment_number": self.payment_number,
            "payment_type": self.payment_type,
            "payment_method": self.payment_method,
            "status": self.status,
            "amount": float(self.amount),
            "currency": self.currency,  # للتوافق مع الكود القديم
            # Multi-Currency Support
            "currency_id": self.currency_id,
            "exchange_rate": float(self.exchange_rate),
            "base_amount": float(self.base_amount) if self.base_amount else None,
            "converted_amount": (float(self.converted_amount) if self.converted_amount else None),
            "amount_in_base_currency": float(self.amount_in_base_currency),  # للتوافق مع الكود القديم
            "payment_date": (self.payment_date.isoformat() if self.payment_date else None),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "customer_id": self.customer_id,
            "supplier_id": self.supplier_id,
            "user_id": self.user_id,
            "sale_id": self.sale_id,
            "purchase_id": self.purchase_id,
            "reference_number": self.reference_number,
            "bank_name": self.bank_name,
            "account_number": self.account_number,
            "notes": self.notes,
            "account_code": self.account_code,
            "cost_center": self.cost_center,
            "attachments": self.attachments,
        }


@dataclass
class AccountBalance:
    """رصيد الحساب"""

    account_id: int
    account_type: str
    account_name: str
    balance: Decimal = Decimal("0.00")
    currency: str = "DZD"
    last_transaction_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "account_id": self.account_id,
            "account_type": self.account_type,
            "account_name": self.account_name,
            "balance": float(self.balance),
            "currency": self.currency,
            "last_transaction_date": (self.last_transaction_date.isoformat() if self.last_transaction_date else None),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class PaymentSchedule:
    """جدولة المدفوعات"""

    id: Optional[int] = None
    payment_id: int = 0
    installment_number: int = 1
    due_date: date = field(default_factory=date.today)
    amount: Decimal = Decimal("0.00")
    paid_amount: Decimal = Decimal("0.00")
    remaining_amount: Decimal = Decimal("0.00")
    status: str = PaymentStatus.PENDING.value
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """معالجة ما بعد الإنشاء"""
        self.remaining_amount = self.amount - self.paid_amount

        if not self.created_at:
            self.created_at = datetime.now()

        self.updated_at = datetime.now()

    @property
    def is_overdue(self) -> bool:
        return self.due_date < date.today() and self.remaining_amount > 0

    @property
    def is_paid(self) -> bool:
        """هل القسط مدفوع بالكامل؟"""
        return self.paid_amount >= self.amount

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "payment_id": self.payment_id,
            "installment_number": self.installment_number,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "amount": float(self.amount),
            "paid_amount": float(self.paid_amount),
            "remaining_amount": float(self.remaining_amount),
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_overdue": self.is_overdue,
            "is_paid": self.is_paid,
        }


class PaymentManager:
    """مدير المدفوعات"""

    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger

    def create_payment(self, payment: Payment) -> Optional[int]:
        """إنشاء دفعة جديدة مع بناء INSERT ديناميكي واعتماداً على الاتصال للحصول على lastrowid"""
        try:
            conn = self.db_manager.connection
            cols_info = conn.execute("PRAGMA table_info(payments)").fetchall()
            available = {c[1] for c in cols_info}
            # Predefine value_map to avoid UnboundLocalError on partial failures
            value_map: Dict[str, Any] = {}
            try:
                print(f"[PaymentManager.create_payment] columns available: {sorted(list(available))[:6]} ...")
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in payment.py")

            # Multi-Currency: حساب المبالغ
            base_amount = payment.base_amount if payment.base_amount is not None else payment.amount
            converted_amount = payment.converted_amount if payment.converted_amount is not None else payment.amount
            exchange_rate = float(payment.exchange_rate) if payment.exchange_rate else 1.0

            # تطبيع نوع الدفعة ليتوافق مع قيود CHECK المحتملة
            type_mapping = {
                "دفعة عميل": "customer_payment",
                "دفعة مورد": "supplier_payment",
                "مصروف": "expense",
                "إيراد": "income",
                "استرداد": "refund",
            }
            normalized_type = type_mapping.get(payment.payment_type, payment.payment_type)

            # Normalize status to satisfy CHECK constraints
            status_map = {
                "معلق": "pending",
                "pending": "pending",
                "مكتمل": "completed",
                "completed": "completed",
                "ملغى": "cancelled",
                "cancelled": "cancelled",
                "فشل": "failed",
                "failed": "failed",
            }
            try:
                norm_status = status_map.get(str(payment.status).strip())
            except Exception:
                norm_status = None
            if norm_status:
                payment.status = norm_status
            else:
                # Default to a safe status allowed by CHECK constraints
                if payment.status is None:
                    payment.status = "completed"

            # Normalize payment_method to satisfy CHECK constraints
            method_map = {
                "نقد": "cash",
                "نقدي": "cash",
                "cash": "cash",
                "شيك": "check",
                "check": "check",
                "تحويل بنكي": "bank_transfer",
                "bank_transfer": "bank_transfer",
                "بطاقة ائتمان": "credit_card",
                "credit_card": "credit_card",
                "بطاقة خصم": "debit_card",
                "debit_card": "debit_card",
            }
            try:
                norm_method = method_map.get(str(payment.payment_method).strip())
            except Exception:
                norm_method = None
            if norm_method:
                payment.payment_method = norm_method
            else:
                # Default to a safe method allowed by CHECK constraints
                if payment.payment_method is None:
                    payment.payment_method = "cash"

            # Safe default for amount_in_base_currency
            try:
                amount_in_base_currency_val = (
                    payment.amount_in_base_currency if payment.amount_in_base_currency is not None else payment.amount
                )
            except Exception:
                amount_in_base_currency_val = payment.amount

            # Ensure timestamps
            now_iso = datetime.now().isoformat()
            # Ensure required fields
            if not payment.payment_number:
                try:
                    payment.payment_number = f"PMT-{int(datetime.now().timestamp()*1000)}"
                except Exception:
                    payment.payment_number = f"PMT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            if not payment.payment_date:
                payment.payment_date = date.today()

            # Build value_map defensively to avoid unbound errors
            def safe_float(val, default=None):
                try:
                    return float(val)
                except Exception:
                    return default

            # Build values
            try:
                value_map["payment_number"] = payment.payment_number
                value_map["payment_type"] = normalized_type
                value_map["payment_method"] = payment.payment_method
                value_map["status"] = payment.status
                value_map["amount"] = safe_float(payment.amount, 0.0)
                value_map["currency"] = payment.currency
                value_map["exchange_rate"] = exchange_rate
                amt_base = amount_in_base_currency_val if amount_in_base_currency_val is not None else payment.amount
                value_map["amount_in_base_currency"] = safe_float(amt_base, 0.0)
                value_map["entity_id"] = payment.customer_id if payment.customer_id is not None else payment.supplier_id
                value_map["currency_id"] = payment.currency_id
                value_map["base_amount"] = safe_float(base_amount, None)
                value_map["converted_amount"] = safe_float(converted_amount, None)
                value_map["payment_date"] = payment.payment_date
                value_map["due_date"] = payment.due_date
                value_map["customer_id"] = payment.customer_id
                value_map["supplier_id"] = payment.supplier_id
                value_map["user_id"] = payment.user_id
                value_map["sale_id"] = payment.sale_id
                value_map["purchase_id"] = payment.purchase_id
                value_map["reference_number"] = payment.reference_number
                value_map["bank_name"] = payment.bank_name
                value_map["account_number"] = payment.account_number
                value_map["notes"] = payment.notes
                value_map["account_code"] = payment.account_code
                value_map["cost_center"] = payment.cost_center
                value_map["created_at"] = payment.created_at or now_iso
                value_map["updated_at"] = payment.updated_at or now_iso
            except Exception as ve:
                try:
                    print(f"[PaymentManager.create_payment] value_map build error: {ve}")
                except Exception:
                    logging.getLogger(__name__).warning("Ignored exception in payment.py")
                # Minimal fields to allow insert
                value_map = {
                    "payment_number": payment.payment_number,
                    "payment_type": normalized_type,
                    "payment_method": payment.payment_method,
                    "status": payment.status,
                    "amount": safe_float(payment.amount, 0.0),
                    "currency": payment.currency,
                    "exchange_rate": exchange_rate,
                    "amount_in_base_currency": safe_float(payment.amount, 0.0),
                    "payment_date": payment.payment_date,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                }

            insert_cols = [c for c in value_map.keys() if c in available]
            if not insert_cols:
                # Ensure we have at least a minimal set
                minimal = [
                    c
                    for c in (
                        "payment_number",
                        "payment_type",
                        "payment_method",
                        "status",
                        "amount",
                        "currency",
                        "exchange_rate",
                        "amount_in_base_currency",
                        "payment_date",
                        "created_at",
                        "updated_at",
                    )
                    if c in available
                ]
                insert_cols = minimal
            # Align placeholders count
            placeholders = ", ".join(["?" for _ in insert_cols])
            query = f"INSERT INTO payments ({', '.join(insert_cols)}) VALUES ({placeholders})"
            insert_vals = []
            for c in insert_cols:
                v = value_map[c]
                if isinstance(v, (datetime, date)):
                    insert_vals.append(v.isoformat())
                else:
                    insert_vals.append(v)

            cursor = conn.cursor()
            try:
                cursor.execute(query, tuple(insert_vals))
                conn.commit()
            except Exception as ex:
                try:
                    print(
                        f"[PaymentManager.create_payment] execute error: {ex}\nQuery: {query}\nCols: {insert_cols}\nVals sample: {insert_vals[:6]}"  # noqa: E501
                    )
                except Exception:
                    logging.getLogger(__name__).warning("Ignored exception in payment.py")
                raise
            payment_id = cursor.lastrowid
            if not payment_id:
                cursor.execute("SELECT last_insert_rowid()")
                r = cursor.fetchone()
                payment_id = r[0] if r else None
            if not payment_id:
                # Immediate same-connection lookup by unique payment_number - most reliable
                try:
                    cursor.execute(
                        "SELECT id FROM payments WHERE payment_number = ? ORDER BY id DESC LIMIT 1",
                        (payment.payment_number,),
                    )
                    row = cursor.fetchone()
                    if row:
                        payment_id = row[0]
                        try:
                            print(
                                f"[PaymentManager.create_payment] Retrieved payment_id={payment_id} via payment_number lookup"  # noqa: E501
                            )
                        except Exception:
                            logging.getLogger(__name__).warning("Ignored exception in payment.py")
                except Exception as e:
                    try:
                        print(f"[PaymentManager.create_payment] payment_number lookup error: {e}")
                    except Exception:
                        logging.getLogger(__name__).warning("Ignored exception in payment.py")
            if not payment_id:
                # Direct max(id) fallback if column exists
                try:
                    if "id" in available:
                        cursor.execute("SELECT id FROM payments ORDER BY id DESC LIMIT 1")
                        rmax = cursor.fetchone()
                        if rmax:
                            payment_id = rmax[0]
                except Exception:
                    if not payment_id:
                        # Try rowid if table supports it
                        cursor.execute(
                            "SELECT rowid FROM payments WHERE payment_number = ? ORDER BY rowid DESC LIMIT 1",
                            (payment.payment_number,),
                        )
                        row = cursor.fetchone()
                        if row:
                            payment_id = row[0]
                    if not payment_id:
                        # Try by created_at newest if id exists
                        try:
                            if "created_at" in available and ("id" in available or "payment_id" in available):
                                idc = "id" if "id" in available else "payment_id"
                                cursor.execute(f"SELECT {idc} FROM payments ORDER BY created_at DESC LIMIT 1")
                                r2 = cursor.fetchone()
                                if r2:
                                    payment_id = r2[0]
                        except Exception:
                            logging.getLogger(__name__).warning("Ignored exception in payment.py")
                except Exception:
                    logging.getLogger(__name__).warning("Ignored exception in payment.py")
            # تحديث أرصدة الحسابات - wrapped in try-except لمنع blocking للـ return
            try:
                self._update_account_balances(payment)
            except Exception as balance_err:
                # تسجيل الخطأ لكن عدم إيقاف العملية
                if self.logger:
                    self.logger.warning(f"تحذير: فشل تحديث أرصدة الحسابات: {balance_err}")
                try:
                    print(f"[PaymentManager.create_payment] balance update failed: {balance_err}")
                except Exception:
                    logging.getLogger(__name__).warning("Ignored exception in payment.py")

            if self.logger:
                self.logger.info(f"تم إنشاء دفعة جديدة برقم: {payment.payment_number} - ID: {payment_id}")

            return payment_id

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء الدفعة: {str(e)}")
            return None

    def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        """الحصول على دفعة بالمعرف"""
        try:
            # استخدام اتصال مباشر مع row_factory للحصول على dict
            conn = (
                self.db_manager.connection
                if hasattr(self.db_manager, "connection") and self.db_manager.connection
                else self.db_manager.get_connection()
            )
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM payments WHERE id = ?"
            cursor.execute(query, (payment_id,))
            result = cursor.fetchone()

            if result:
                payment_obj = self._row_to_payment_dict(dict(result))
                return payment_obj

            return None

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الدفعة {payment_id}: {str(e)}")
            return None

    def get_customer_payments(self, customer_id: int) -> List[Payment]:
        """الحصول على دفعات العميل"""
        try:
            conn = (
                self.db_manager.connection
                if hasattr(self.db_manager, "connection") and self.db_manager.connection
                else None
            )
            if conn is None:
                if self.logger:
                    self.logger.error("خطأ: لا يمكن الوصول لاتصال قاعدة البيانات")
                return []
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM payments
                WHERE customer_id = ? AND payment_type = 'customer_payment'
                ORDER BY payment_date DESC, created_at DESC
            """,
                (customer_id,),
            )
            rows = cursor.fetchall()
            return [self._row_to_payment_dict(dict(row)) for row in rows]

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على دفعات العميل {customer_id}: {str(e)}")
            return []

    def get_supplier_payments(self, supplier_id: int) -> List[Payment]:
        """الحصول على دفعات المورد"""
        try:
            conn = (
                self.db_manager.connection
                if hasattr(self.db_manager, "connection") and self.db_manager.connection
                else None
            )
            if conn is None:
                if self.logger:
                    self.logger.error("خطأ: لا يمكن الوصول لاتصال قاعدة البيانات")
                return []
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM payments
                WHERE supplier_id = ? AND payment_type = 'supplier_payment'
                ORDER BY payment_date DESC, created_at DESC
            """,
                (supplier_id,),
            )
            rows = cursor.fetchall()
            return [self._row_to_payment_dict(dict(row)) for row in rows]

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على دفعات المورد {supplier_id}: {str(e)}")
            return []

    def get_overdue_payments(self) -> List[Payment]:
        """الحصول على المدفوعات المتأخرة"""
        try:
            query = """
            SELECT * FROM payments
            WHERE due_date < ? AND status != ?
            ORDER BY due_date ASC
            """
            today = date.today().isoformat()
            results = self.db_manager.fetch_all(query, (today, PaymentStatus.COMPLETED.value))
            return [self._row_to_payment(row) for row in results]

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المدفوعات المتأخرة: {str(e)}")
            return []

    def get_account_balance(self, account_type: str, account_id: int) -> Decimal:
        """الحصول على رصيد الحساب"""
        try:
            if account_type == AccountType.RECEIVABLE.value:
                # ذمة مدينة - العملاء
                query = """
                SELECT COALESCE(SUM(
                    CASE
                        WHEN payment_type = ? THEN -amount_in_base_currency
                        ELSE amount_in_base_currency
                    END
                ), 0) as balance
                FROM payments
                WHERE entity_id = ? AND payment_type = ? AND status = ?
                """
                result = self.db_manager.fetch_one(
                    query,
                    (
                        PaymentType.CUSTOMER_PAYMENT.value,
                        account_id,
                        PaymentType.CUSTOMER_PAYMENT.value,
                        PaymentStatus.COMPLETED.value,
                    ),
                )

            elif account_type == AccountType.PAYABLE.value:
                # ذمة دائنة - الموردين
                query = """
                SELECT COALESCE(SUM(
                    CASE
                        WHEN payment_type = ? THEN -amount_in_base_currency
                        ELSE amount_in_base_currency
                    END
                ), 0) as balance
                FROM payments
                WHERE entity_id = ? AND payment_type = ? AND status = ?
                """
                result = self.db_manager.fetch_one(
                    query,
                    (
                        PaymentType.SUPPLIER_PAYMENT.value,
                        account_id,
                        PaymentType.SUPPLIER_PAYMENT.value,
                        PaymentStatus.COMPLETED.value,
                    ),
                )

            else:
                return Decimal("0.00")

            if result:
                val = result["balance"] if isinstance(result, dict) else (result[0] if len(result) > 0 else None)
                if val is not None:
                    return Decimal(str(val))

            return Decimal("0.00")

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على رصيد الحساب: {str(e)}")
            return Decimal("0.00")

    def _update_account_balances(self, payment: Payment):
        """تحديث أرصدة الحسابات"""
        try:
            # تحديث رصيد العميل أو المورد حسب نوع الدفعة
            if payment.customer_id and payment.payment_type == PaymentType.CUSTOMER_PAYMENT.value:
                # دفعة من العميل - تقليل الذمة المدينة
                self._update_customer_balance(payment.customer_id, -payment.amount_in_base_currency)

            elif payment.supplier_id and payment.payment_type == PaymentType.SUPPLIER_PAYMENT.value:
                # دفعة للمورد - تقليل الذمة الدائنة
                self._update_supplier_balance(payment.supplier_id, -payment.amount_in_base_currency)

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث أرصدة الحسابات: {str(e)}")

    def _update_customer_balance(self, customer_id: int, amount: Decimal):
        """تحديث رصيد العميل"""
        try:
            query = """
            UPDATE customers
            SET current_balance = current_balance + ?,
                updated_at = ?
            WHERE id = ?
            """
            self.db_manager.execute_query(query, (float(amount), datetime.now().isoformat(), customer_id))

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث رصيد العميل {customer_id}: {str(e)}")

    def _update_supplier_balance(self, supplier_id: int, amount: Decimal):
        """تحديث رصيد المورد"""
        try:
            query = """
            UPDATE suppliers
            SET current_balance = current_balance + ?,
                updated_at = ?
            WHERE id = ?
            """
            self.db_manager.execute_query(query, (float(amount), datetime.now().isoformat(), supplier_id))

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث رصيد المورد {supplier_id}: {str(e)}")

    def _row_to_payment(self, row) -> Payment:
        """تحويل صف قاعدة البيانات إلى كائن دفعة

        Schema المتوقع: id, payment_number, payment_type, payment_method, status,
        amount, currency, exchange_rate, amount_in_base_currency,
        currency_id, base_amount, converted_amount (Multi-Currency),
        payment_date, due_date, customer_id, supplier_id, user_id,
        sale_id, purchase_id, reference_number, bank_name, account_number,
        notes, account_code, cost_center, created_at, updated_at (27 عمود)
        """
        row_len = len(row)

        # قراءة حقول Multi-Currency - الأعمدة 9-11
        currency_id = row[9] if row_len > 9 and row[9] is not None else None

        base_amount = (
            Decimal(str(row[10])) if row_len > 10 and row[10] is not None and not isinstance(row[10], str) else None
        )
        converted_amount = (
            Decimal(str(row[11])) if row_len > 11 and row[11] is not None and not isinstance(row[11], str) else None
        )

        return Payment(
            id=row[0] if row_len > 0 else None,
            payment_number=row[1] if row_len > 1 else "",
            payment_type=row[2] if row_len > 2 else PaymentType.CUSTOMER_PAYMENT.value,
            payment_method=row[3] if row_len > 3 else PaymentMethod.CASH.value,
            status=row[4] if row_len > 4 else PaymentStatus.PENDING.value,
            amount=(Decimal(str(row[5])) if row_len > 5 and row[5] is not None else Decimal("0")),
            currency=row[6] if row_len > 6 else "DZD",  # للتوافق مع الكود القديم
            exchange_rate=(Decimal(str(row[7])) if row_len > 7 and row[7] is not None else Decimal("1.0")),
            amount_in_base_currency=(
                Decimal(str(row[8])) if row_len > 8 and row[8] is not None else Decimal("0")
            ),  # للتوافق مع الكود القديم
            # Multi-Currency Support
            currency_id=currency_id,
            base_amount=base_amount,
            converted_amount=converted_amount,
            payment_date=(date.fromisoformat(row[12]) if row_len > 12 and row[12] else None),
            due_date=date.fromisoformat(row[13]) if row_len > 13 and row[13] else None,
            customer_id=row[14] if row_len > 14 else None,
            supplier_id=row[15] if row_len > 15 else None,
            user_id=row[16] if row_len > 16 else None,
            sale_id=row[17] if row_len > 17 else None,
            purchase_id=row[18] if row_len > 18 else None,
            reference_number=row[19] if row_len > 19 else None,
            bank_name=row[20] if row_len > 20 else None,
            account_number=row[21] if row_len > 21 else None,
            notes=row[22] if row_len > 22 else None,
            account_code=row[23] if row_len > 23 else None,
            cost_center=row[24] if row_len > 24 else None,
            created_at=(datetime.fromisoformat(row[25]) if row_len > 25 and row[25] else None),
            updated_at=(datetime.fromisoformat(row[26]) if row_len > 26 and row[26] else None),
        )

    def _row_to_payment_dict(self, row_dict: dict) -> Payment:
        """تحويل dict إلى كائن دفعة (أكثر موثوقية من row indices)"""

        def safe_decimal(value):
            if value is None:
                return None
            try:
                return Decimal(str(value))
            except Exception:
                return None

        def safe_date(value):
            if not value:
                return None
            try:
                if isinstance(value, date):
                    return value
                return date.fromisoformat(value)
            except Exception:
                return None

        def safe_datetime(value):
            if not value:
                return None
            try:
                if isinstance(value, datetime):
                    return value
                return datetime.fromisoformat(value)
            except Exception:
                return None

        return Payment(
            id=row_dict.get("id"),
            payment_number=row_dict.get("payment_number", ""),
            payment_type=row_dict.get("payment_type", PaymentType.CUSTOMER_PAYMENT.value),
            payment_method=row_dict.get("payment_method", PaymentMethod.CASH.value),
            status=row_dict.get("status", PaymentStatus.PENDING.value),
            amount=safe_decimal(row_dict.get("amount")) or Decimal("0"),
            currency=row_dict.get("currency", "DZD"),
            exchange_rate=safe_decimal(row_dict.get("exchange_rate")) or Decimal("1.0"),
            amount_in_base_currency=safe_decimal(row_dict.get("amount_in_base_currency")) or Decimal("0"),
            currency_id=row_dict.get("currency_id"),
            base_amount=safe_decimal(row_dict.get("base_amount")),
            converted_amount=safe_decimal(row_dict.get("converted_amount")),
            payment_date=safe_date(row_dict.get("payment_date")),
            due_date=safe_date(row_dict.get("due_date")),
            customer_id=row_dict.get("customer_id"),
            supplier_id=row_dict.get("supplier_id"),
            user_id=row_dict.get("user_id"),
            sale_id=row_dict.get("sale_id"),
            purchase_id=row_dict.get("purchase_id"),
            reference_number=row_dict.get("reference_number"),
            bank_name=row_dict.get("bank_name"),
            account_number=row_dict.get("account_number"),
            notes=row_dict.get("notes"),
            account_code=row_dict.get("account_code"),
            cost_center=row_dict.get("cost_center"),
            created_at=safe_datetime(row_dict.get("created_at")),
            updated_at=safe_datetime(row_dict.get("updated_at")),
        )
