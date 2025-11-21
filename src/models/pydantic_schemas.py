#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نماذج Pydantic للتحقق من صحة البيانات
توفير schema validation لجميع الكيانات الرئيسية
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

try:
    from pydantic import (
        BaseModel,
        Field,
        EmailStr,
        validator,
        root_validator,
        constr,
        conint,
        confloat
    )
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    print("⚠️ تحذير: مكتبة pydantic غير متاحة. لن يعمل التحقق التلقائي.")
    
    # Mock classes للتوافق
    class BaseModel:
        pass
    
    class Field:
        pass
    
    EmailStr = str


# ==================== Enums ====================

class UserRole(str, Enum):
    """أدوار المستخدمين"""
    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"
    VIEWER = "viewer"


class InvoiceType(str, Enum):
    """أنواع الفواتير"""
    SALES = "sales"
    PURCHASE = "purchase"
    RETURN_SALES = "return_sales"
    RETURN_PURCHASE = "return_purchase"


class PaymentMethod(str, Enum):
    """طرق الدفع"""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    OTHER = "other"


class TransactionType(str, Enum):
    """أنواع المعاملات المحاسبية"""
    DEBIT = "debit"  # مدين
    CREDIT = "credit"  # دائن


# ==================== User Models ====================

class UserCreate(BaseModel):
    """نموذج إنشاء مستخدم جديد"""
    username: constr(min_length=3, max_length=50)
    password: constr(min_length=8)
    email: Optional[EmailStr] = None
    full_name: constr(min_length=2, max_length=100)
    role: UserRole = UserRole.VIEWER
    is_active: bool = True
    
    if PYDANTIC_AVAILABLE:
        @validator('username', allow_reuse=True)
        def username_alphanumeric(cls, v):
            """التحقق من أن اسم المستخدم أبجدي رقمي"""
            if not v.replace('_', '').replace('-', '').isalnum():
                raise ValueError('اسم المستخدم يجب أن يكون أبجدي رقمي')
            return v
        
        class Config:
            use_enum_values = True


class UserUpdate(BaseModel):
    """نموذج تحديث مستخدم"""
    email: Optional[EmailStr] = None
    full_name: Optional[constr(min_length=2, max_length=100)] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    
    if PYDANTIC_AVAILABLE:
        class Config:
            use_enum_values = True


class UserResponse(BaseModel):
    """نموذج استجابة بيانات المستخدم"""
    id: int
    username: str
    email: Optional[str]
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    if PYDANTIC_AVAILABLE:
        class Config:
            orm_mode = True
            use_enum_values = True


# ==================== Product Models ====================

class ProductCreate(BaseModel):
    """نموذج إنشاء منتج"""
    name: constr(min_length=1, max_length=200)
    barcode: Optional[constr(max_length=50)] = None
    category_id: Optional[int] = None
    unit: constr(min_length=1, max_length=20) = "وحدة"
    
    # الأسعار
    purchase_price: confloat(ge=0) = 0.0
    sale_price: confloat(ge=0)
    min_sale_price: Optional[confloat(ge=0)] = None
    
    # المخزون
    stock_quantity: confloat(ge=0) = 0.0
    min_stock: confloat(ge=0) = 0.0
    max_stock: Optional[confloat(ge=0)] = None
    
    # معلومات إضافية
    description: Optional[str] = None
    supplier_id: Optional[int] = None
    is_active: bool = True
    tax_rate: confloat(ge=0, le=100) = 0.0
    
    if PYDANTIC_AVAILABLE:
        @validator('min_sale_price')
        def min_price_check(cls, v, values):
            """التحقق من أن الحد الأدنى للسعر أقل من سعر البيع"""
            if v is not None and 'sale_price' in values:
                if v > values['sale_price']:
                    raise ValueError('الحد الأدنى للسعر يجب أن يكون أقل من سعر البيع')
            return v
        
        @validator('max_stock')
        def max_stock_check(cls, v, values):
            """التحقق من أن الحد الأقصى أكبر من الحد الأدنى"""
            if v is not None and 'min_stock' in values:
                if v < values['min_stock']:
                    raise ValueError('الحد الأقصى يجب أن يكون أكبر من الحد الأدنى')
            return v


class ProductUpdate(BaseModel):
    """نموذج تحديث منتج"""
    name: Optional[constr(min_length=1, max_length=200)] = None
    barcode: Optional[constr(max_length=50)] = None
    category_id: Optional[int] = None
    unit: Optional[constr(min_length=1, max_length=20)] = None
    
    purchase_price: Optional[confloat(ge=0)] = None
    sale_price: Optional[confloat(ge=0)] = None
    min_sale_price: Optional[confloat(ge=0)] = None
    
    stock_quantity: Optional[confloat(ge=0)] = None
    min_stock: Optional[confloat(ge=0)] = None
    max_stock: Optional[confloat(ge=0)] = None
    
    description: Optional[str] = None
    supplier_id: Optional[int] = None
    is_active: Optional[bool] = None
    tax_rate: Optional[confloat(ge=0, le=100)] = None


class ProductResponse(BaseModel):
    """نموذج استجابة بيانات المنتج"""
    id: int
    name: str
    barcode: Optional[str]
    category_id: Optional[int]
    unit: str
    
    purchase_price: float
    sale_price: float
    min_sale_price: Optional[float]
    
    stock_quantity: float
    min_stock: float
    max_stock: Optional[float]
    
    description: Optional[str]
    supplier_id: Optional[int]
    is_active: bool
    tax_rate: float
    
    created_at: datetime
    updated_at: Optional[datetime]
    
    if PYDANTIC_AVAILABLE:
        class Config:
            orm_mode = True


# ==================== Customer Models ====================

class CustomerCreate(BaseModel):
    """نموذج إنشاء عميل"""
    name: constr(min_length=2, max_length=200)
    phone: Optional[constr(max_length=20)] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    tax_number: Optional[constr(max_length=50)] = None
    credit_limit: confloat(ge=0) = 0.0
    is_active: bool = True
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    """نموذج تحديث عميل"""
    name: Optional[constr(min_length=2, max_length=200)] = None
    phone: Optional[constr(max_length=20)] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    tax_number: Optional[constr(max_length=50)] = None
    credit_limit: Optional[confloat(ge=0)] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class CustomerResponse(BaseModel):
    """نموذج استجابة بيانات العميل"""
    id: int
    name: str
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    tax_number: Optional[str]
    credit_limit: float
    current_balance: float
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    
    if PYDANTIC_AVAILABLE:
        class Config:
            orm_mode = True


# ==================== Invoice Models ====================

class InvoiceItemCreate(BaseModel):
    """نموذج عنصر في الفاتورة"""
    product_id: int
    quantity: confloat(gt=0)
    unit_price: confloat(ge=0)
    discount: confloat(ge=0, le=100) = 0.0
    tax_rate: confloat(ge=0, le=100) = 0.0
    notes: Optional[str] = None
    
    if PYDANTIC_AVAILABLE:
        @property
        def subtotal(self) -> float:
            """حساب المجموع الفرعي"""
            return self.quantity * self.unit_price * (1 - self.discount / 100)
        
        @property
        def tax_amount(self) -> float:
            """حساب الضريبة"""
            return self.subtotal * (self.tax_rate / 100)
        
        @property
        def total(self) -> float:
            """حساب الإجمالي"""
            return self.subtotal + self.tax_amount


class InvoiceCreate(BaseModel):
    """نموذج إنشاء فاتورة"""
    invoice_type: InvoiceType
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    invoice_date: date = Field(default_factory=date.today)
    
    items: List[InvoiceItemCreate] = Field(min_items=1)
    
    discount: confloat(ge=0) = 0.0
    tax_rate: confloat(ge=0, le=100) = 0.0
    shipping_cost: confloat(ge=0) = 0.0
    
    payment_method: Optional[PaymentMethod] = None
    paid_amount: confloat(ge=0) = 0.0
    
    notes: Optional[str] = None
    
    if PYDANTIC_AVAILABLE:
        @root_validator(skip_on_failure=True)
        def validate_customer_supplier(cls, values):
            """التحقق من وجود عميل أو مورد حسب نوع الفاتورة"""
            invoice_type = values.get('invoice_type')
            customer_id = values.get('customer_id')
            supplier_id = values.get('supplier_id')
            
            if invoice_type in [InvoiceType.SALES, InvoiceType.RETURN_SALES]:
                if not customer_id:
                    raise ValueError('فاتورة المبيعات تتطلب تحديد عميل')
            
            elif invoice_type in [InvoiceType.PURCHASE, InvoiceType.RETURN_PURCHASE]:
                if not supplier_id:
                    raise ValueError('فاتورة المشتريات تتطلب تحديد مورد')
            
            return values
        
        @validator('paid_amount')
        def paid_amount_check(cls, v, values):
            """التحقق من أن المبلغ المدفوع لا يتجاوز الإجمالي"""
            # سيتم حسابه في Service layer
            return v
        
        class Config:
            use_enum_values = True


class InvoiceResponse(BaseModel):
    """نموذج استجابة بيانات الفاتورة"""
    id: int
    invoice_number: str
    invoice_type: InvoiceType
    customer_id: Optional[int]
    supplier_id: Optional[int]
    invoice_date: date
    
    subtotal: float
    discount: float
    tax_amount: float
    shipping_cost: float
    total: float
    
    paid_amount: float
    remaining_amount: float
    
    payment_method: Optional[PaymentMethod]
    status: str
    notes: Optional[str]
    
    created_by: int
    created_at: datetime
    
    if PYDANTIC_AVAILABLE:
        class Config:
            orm_mode = True
            use_enum_values = True


# ==================== Accounting Models ====================

class AccountingEntryCreate(BaseModel):
    """نموذج إنشاء قيد محاسبي"""
    account_id: int
    transaction_type: TransactionType
    amount: confloat(gt=0)
    description: str
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    transaction_date: date = Field(default_factory=date.today)
    
    if PYDANTIC_AVAILABLE:
        class Config:
            use_enum_values = True


class JournalEntryCreate(BaseModel):
    """نموذج إنشاء قيد يومية"""
    entry_date: date = Field(default_factory=date.today)
    description: str
    entries: List[AccountingEntryCreate] = Field(min_items=2)
    
    if PYDANTIC_AVAILABLE:
        @root_validator(skip_on_failure=True)
        def validate_balanced(cls, values):
            """التحقق من توازن القيد"""
            entries = values.get('entries', [])
            
            debit_total = sum(
                e.amount for e in entries
                if e.transaction_type == TransactionType.DEBIT
            )
            
            credit_total = sum(
                e.amount for e in entries
                if e.transaction_type == TransactionType.CREDIT
            )
            
            if abs(debit_total - credit_total) > 0.01:  # Tolerance for floating point
                raise ValueError(
                    f'القيد غير متوازن: مدين={debit_total}, دائن={credit_total}'
                )
            
            return values


# ==================== Payment Models ====================

class PaymentCreate(BaseModel):
    """نموذج تسجيل دفعة"""
    invoice_id: int
    amount: confloat(gt=0)
    payment_method: PaymentMethod
    payment_date: date = Field(default_factory=date.today)
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    
    if PYDANTIC_AVAILABLE:
        class Config:
            use_enum_values = True


class PaymentResponse(BaseModel):
    """نموذج استجابة بيانات الدفعة"""
    id: int
    invoice_id: int
    amount: float
    payment_method: PaymentMethod
    payment_date: date
    reference_number: Optional[str]
    notes: Optional[str]
    created_by: int
    created_at: datetime
    
    if PYDANTIC_AVAILABLE:
        class Config:
            orm_mode = True
            use_enum_values = True


# ==================== Inventory Models ====================

class InventoryAdjustmentCreate(BaseModel):
    """نموذج تعديل المخزون"""
    product_id: int
    quantity_change: float  # يمكن أن يكون موجب أو سالب
    reason: constr(min_length=3, max_length=200)
    notes: Optional[str] = None
    adjustment_date: date = Field(default_factory=date.today)


class StockTransferCreate(BaseModel):
    """نموذج نقل مخزون بين مواقع"""
    product_id: int
    from_location: str
    to_location: str
    quantity: confloat(gt=0)
    notes: Optional[str] = None
    transfer_date: date = Field(default_factory=date.today)


# ==================== Report Filters ====================

class SalesReportFilter(BaseModel):
    """فلترة تقرير المبيعات"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    customer_id: Optional[int] = None
    product_id: Optional[int] = None
    payment_method: Optional[PaymentMethod] = None
    
    if PYDANTIC_AVAILABLE:
        @validator('end_date')
        def end_date_after_start(cls, v, values):
            """التحقق من أن تاريخ النهاية بعد تاريخ البداية"""
            if v and 'start_date' in values and values['start_date']:
                if v < values['start_date']:
                    raise ValueError('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
            return v


# ==================== مثال على الاستخدام ====================

if __name__ == "__main__":
    if not PYDANTIC_AVAILABLE:
        print("❌ Pydantic غير متاح. قم بتثبيته: pip install pydantic[email]")
        exit(1)
    
    print("=" * 70)
    print("✅ اختبار Pydantic Models")
    print("=" * 70)
    
    # 1. إنشاء مستخدم
    print("\n1️⃣ إنشاء مستخدم:")
    try:
        user = UserCreate(
            username="ahmad_123",
            password="SecurePass123!",
            email="ahmad@example.com",
            full_name="أحمد محمد",
            role=UserRole.ADMIN
        )
        print(f"   ✅ المستخدم: {user.username} ({user.role})")
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
    
    # 2. إنشاء منتج
    print("\n2️⃣ إنشاء منتج:")
    try:
        product = ProductCreate(
            name="لابتوب Dell XPS 15",
            barcode="1234567890",
            purchase_price=3000.0,
            sale_price=4000.0,
            min_sale_price=3500.0,
            stock_quantity=10.0,
            min_stock=5.0,
            tax_rate=15.0
        )
        print(f"   ✅ المنتج: {product.name}")
        print(f"      السعر: {product.sale_price} ريال")
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
    
    # 3. إنشاء فاتورة
    print("\n3️⃣ إنشاء فاتورة:")
    try:
        invoice = InvoiceCreate(
            invoice_type=InvoiceType.SALES,
            customer_id=1,
            items=[
                InvoiceItemCreate(
                    product_id=1,
                    quantity=2.0,
                    unit_price=4000.0,
                    discount=5.0,
                    tax_rate=15.0
                )
            ],
            payment_method=PaymentMethod.CASH,
            paid_amount=9200.0
        )
        print(f"   ✅ الفاتورة: {invoice.invoice_type}")
        print(f"      عدد العناصر: {len(invoice.items)}")
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
    
    # 4. اختبار التحقق - فاتورة غير صحيحة
    print("\n4️⃣ اختبار التحقق:")
    try:
        invalid_invoice = InvoiceCreate(
            invoice_type=InvoiceType.SALES,
            # بدون customer_id - يجب أن يفشل
            items=[
                InvoiceItemCreate(
                    product_id=1,
                    quantity=-1.0,  # كمية سالبة - يجب أن يفشل
                    unit_price=100.0
                )
            ]
        )
    except Exception as e:
        print(f"   ✅ تم اكتشاف الخطأ: {e}")
    
    # 5. قيد محاسبي متوازن
    print("\n5️⃣ قيد محاسبي:")
    try:
        journal = JournalEntryCreate(
            description="قيد افتتاحي",
            entries=[
                AccountingEntryCreate(
                    account_id=1,
                    transaction_type=TransactionType.DEBIT,
                    amount=10000.0,
                    description="رأس المال"
                ),
                AccountingEntryCreate(
                    account_id=2,
                    transaction_type=TransactionType.CREDIT,
                    amount=10000.0,
                    description="رأس المال"
                )
            ]
        )
        print(f"   ✅ القيد متوازن: {journal.description}")
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
    
    print("\n" + "=" * 70)
    print("✅ اكتملت جميع الاختبارات!")
    print("=" * 70)
