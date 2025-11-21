"""
نموذج بيانات المدفوعات والذمم المدينة والدائنة
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


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
    PAYABLE = "ذمة دائنة"    # نحن ندين للموردين
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
    amount: Decimal = Decimal('0.00')
    currency: str = "DZD"
    exchange_rate: Decimal = Decimal('1.00')
    amount_in_base_currency: Decimal = Decimal('0.00')
    
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
        if not self.payment_number:
            self.payment_number = self.generate_payment_number()
        
        # حساب المبلغ بالعملة الأساسية
        self.amount_in_base_currency = self.amount * self.exchange_rate
        
        if not self.created_at:
            self.created_at = datetime.now()
        
        self.updated_at = datetime.now()
    
    def generate_payment_number(self) -> str:
        """توليد رقم الدفعة"""
        now = datetime.now()
        return f"PAY-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'payment_number': self.payment_number,
            'payment_type': self.payment_type,
            'payment_method': self.payment_method,
            'status': self.status,
            'amount': float(self.amount),
            'currency': self.currency,
            'exchange_rate': float(self.exchange_rate),
            'amount_in_base_currency': float(self.amount_in_base_currency),
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'customer_id': self.customer_id,
            'supplier_id': self.supplier_id,
            'user_id': self.user_id,
            'sale_id': self.sale_id,
            'purchase_id': self.purchase_id,
            'reference_number': self.reference_number,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'notes': self.notes,
            'account_code': self.account_code,
            'cost_center': self.cost_center,
            'attachments': self.attachments
        }


@dataclass
class AccountBalance:
    """رصيد الحساب"""
    account_id: int
    account_type: str
    account_name: str
    balance: Decimal = Decimal('0.00')
    currency: str = "DZD"
    last_transaction_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'account_id': self.account_id,
            'account_type': self.account_type,
            'account_name': self.account_name,
            'balance': float(self.balance),
            'currency': self.currency,
            'last_transaction_date': self.last_transaction_date.isoformat() if self.last_transaction_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class PaymentSchedule:
    """جدولة المدفوعات"""
    id: Optional[int] = None
    payment_id: int = 0
    installment_number: int = 1
    due_date: date = field(default_factory=date.today)
    amount: Decimal = Decimal('0.00')
    paid_amount: Decimal = Decimal('0.00')
    remaining_amount: Decimal = Decimal('0.00')
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
        """هل القسط متأخر؟"""
        return self.due_date < date.today() and self.remaining_amount > 0
    
    @property
    def is_paid(self) -> bool:
        """هل القسط مدفوع بالكامل؟"""
        return self.paid_amount >= self.amount
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'installment_number': self.installment_number,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'amount': float(self.amount),
            'paid_amount': float(self.paid_amount),
            'remaining_amount': float(self.remaining_amount),
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_overdue': self.is_overdue,
            'is_paid': self.is_paid
        }


class PaymentManager:
    """مدير المدفوعات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
    
    def create_payment(self, payment: Payment) -> Optional[int]:
        """إنشاء دفعة جديدة"""
        try:
            query = """
            INSERT INTO payments (
                payment_number, payment_type, payment_method, status,
                amount, currency, exchange_rate, amount_in_base_currency,
                payment_date, due_date, customer_id, supplier_id, user_id,
                sale_id, purchase_id, reference_number, bank_name, account_number,
                notes, account_code, cost_center, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                payment.payment_number,
                payment.payment_type,
                payment.payment_method,
                payment.status,
                float(payment.amount),
                payment.currency,
                float(payment.exchange_rate),
                float(payment.amount_in_base_currency),
                payment.payment_date.isoformat() if payment.payment_date else None,
                payment.due_date.isoformat() if payment.due_date else None,
                payment.customer_id,
                payment.supplier_id,
                payment.user_id,
                payment.sale_id,
                payment.purchase_id,
                payment.reference_number,
                payment.bank_name,
                payment.account_number,
                payment.notes,
                payment.account_code,
                payment.cost_center,
                payment.created_at.isoformat() if payment.created_at else None,
                payment.updated_at.isoformat() if payment.updated_at else None
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and hasattr(result, 'lastrowid'):
                payment_id = result.lastrowid
                payment.id = payment_id
                
                # تحديث أرصدة الحسابات
                self._update_account_balances(payment)
                
                if self.logger:
                    self.logger.info(f"تم إنشاء دفعة جديدة برقم: {payment.payment_number}")
                
                return payment_id
            
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء الدفعة: {str(e)}")
            return None
    
    def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        """الحصول على دفعة بالمعرف"""
        try:
            query = "SELECT * FROM payments WHERE id = ?"
            result = self.db_manager.fetch_one(query, (payment_id,))
            
            if result:
                return self._row_to_payment(result)
            
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الدفعة {payment_id}: {str(e)}")
            return None
    
    def get_customer_payments(self, customer_id: int) -> List[Payment]:
        """الحصول على دفعات العميل"""
        try:
            query = """
            SELECT * FROM payments 
            WHERE entity_id = ? AND payment_type = 'customer_payment'
            ORDER BY payment_date DESC, created_at DESC
            """
            results = self.db_manager.fetch_all(query, (customer_id,))
            return [self._row_to_payment(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على دفعات العميل {customer_id}: {str(e)}")
            return []
    
    def get_supplier_payments(self, supplier_id: int) -> List[Payment]:
        """الحصول على دفعات المورد"""
        try:
            query = """
            SELECT * FROM payments 
            WHERE entity_id = ? AND payment_type = 'supplier_payment'
            ORDER BY payment_date DESC, created_at DESC
            """
            results = self.db_manager.fetch_all(query, (supplier_id,))
            return [self._row_to_payment(row) for row in results]
            
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
                result = self.db_manager.fetch_one(query, (
                    account_id,
                    PaymentType.CUSTOMER_PAYMENT.value,
                    PaymentStatus.COMPLETED.value
                ))
                
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
                result = self.db_manager.fetch_one(query, (
                    PaymentType.SUPPLIER_PAYMENT.value,
                    account_id,
                    PaymentType.SUPPLIER_PAYMENT.value,
                    PaymentStatus.COMPLETED.value
                ))
            
            else:
                return Decimal('0.00')
            
            if result and result[0] is not None:
                return Decimal(str(result[0]))
            
            return Decimal('0.00')
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على رصيد الحساب: {str(e)}")
            return Decimal('0.00')
    
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
            self.db_manager.execute_query(query, (
                float(amount),
                datetime.now().isoformat(),
                customer_id
            ))
            
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
            self.db_manager.execute_query(query, (
                float(amount),
                datetime.now().isoformat(),
                supplier_id
            ))
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث رصيد المورد {supplier_id}: {str(e)}")
    
    def _row_to_payment(self, row) -> Payment:
        """تحويل صف قاعدة البيانات إلى كائن دفعة"""
        return Payment(
            id=row[0],
            payment_number=row[1],
            payment_type=row[2],
            payment_method=row[3],
            status=row[4],
            amount=Decimal(str(row[5])),
            currency=row[6],
            exchange_rate=Decimal(str(row[7])),
            amount_in_base_currency=Decimal(str(row[8])),
            payment_date=date.fromisoformat(row[9]) if row[9] else None,
            due_date=date.fromisoformat(row[10]) if row[10] else None,
            customer_id=row[11],
            supplier_id=row[12],
            user_id=row[13],
            sale_id=row[14],
            purchase_id=row[15],
            reference_number=row[16],
            bank_name=row[17],
            account_number=row[18],
            notes=row[19],
            account_code=row[20],
            cost_center=row[21],
            created_at=datetime.fromisoformat(row[22]) if row[22] else None,
            updated_at=datetime.fromisoformat(row[23]) if row[23] else None
        )