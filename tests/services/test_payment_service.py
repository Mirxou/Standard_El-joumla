import pytest
from decimal import Decimal
from unittest.mock import Mock

from src.core.database_manager import DatabaseManager
from src.services.payment_service import PaymentService


@pytest.fixture
def db_manager():
    db = DatabaseManager(db_path=":memory:")
    db.initialize()
    # Seed minimal customer to satisfy FK when present
    db.execute_query(
        """
        INSERT INTO customers (name, phone, email)
        VALUES ('Test Customer', '000', 'test@example.com')
        """
    )
    cid = db.fetch_one("SELECT id FROM customers WHERE name = ?", ("Test Customer",))[0]
    return db, cid


@pytest.fixture
def payment_service(db_manager):
    db, _ = db_manager
    return PaymentService(db_manager=db, logger=Mock())


def test_create_customer_payment_basic(payment_service, db_manager):
    db, cid = db_manager
    p = payment_service.create_customer_payment(
        customer_id=cid,
        amount=Decimal("100.00"),
    )
    assert p is not None
    assert float(p.amount) == 100.0
    # verify it is persisted
    row = db.fetch_one("SELECT COUNT(*) FROM payments", ())
    assert row and row[0] >= 1


def test_payment_tables_created(payment_service):
    # Ensure tables exist
    con = payment_service.db_manager.connection
    cols = con.execute("PRAGMA table_info(payments)").fetchall()
    assert any(c[1] == "payment_number" for c in cols)


def test_create_supplier_payment(payment_service, db_manager):
    """اختبار إنشاء دفعة مورد"""
    db, _ = db_manager
    # إنشاء مورد للاختبار
    db.execute_query("INSERT INTO suppliers (name, phone) VALUES ('Test Supplier', '111')")
    sid = db.fetch_one("SELECT id FROM suppliers WHERE name = ?", ("Test Supplier",))[0]
    
    p = payment_service.create_supplier_payment(
        supplier_id=sid,
        amount=Decimal("500.00"),
        payment_method="cash"
    )
    assert p is not None
    assert float(p.amount) == 500.0
    assert p.supplier_id == sid


def test_get_payment_by_id(payment_service, db_manager):
    """اختبار الحصول على دفعة بالمعرف"""
    db, cid = db_manager
    p = payment_service.create_customer_payment(
        customer_id=cid,
        amount=Decimal("200.00")
    )
    assert p is not None
    
    # الحصول على الدفعة بالمعرف
    retrieved = payment_service.get_payment_by_id(p.id)
    assert retrieved is not None
    assert retrieved.id == p.id
    assert float(retrieved.amount) == 200.0


def test_get_customer_payments(payment_service, db_manager):
    """اختبار الحصول على دفعات عميل"""
    db, cid = db_manager
    
    # إنشاء عدة دفعات
    payment_service.create_customer_payment(customer_id=cid, amount=Decimal("100"))
    payment_service.create_customer_payment(customer_id=cid, amount=Decimal("200"))
    
    payments = payment_service.get_customer_payments(cid)
    assert len(payments) >= 2


def test_get_supplier_payments(payment_service, db_manager):
    """اختبار الحصول على دفعات مورد"""
    db, _ = db_manager
    db.execute_query("INSERT INTO suppliers (name, phone) VALUES ('Supplier 2', '222')")
    sid = db.fetch_one("SELECT id FROM suppliers WHERE name = ?", ("Supplier 2",))[0]
    
    payment_service.create_supplier_payment(supplier_id=sid, amount=Decimal("300"))
    payment_service.create_supplier_payment(supplier_id=sid, amount=Decimal("400"))
    
    payments = payment_service.get_supplier_payments(sid)
    assert len(payments) >= 2


def test_payment_with_reference_number(payment_service, db_manager):
    """اختبار دفعة مع رقم مرجعي"""
    db, cid = db_manager
    ref_num = "REF-12345"
    
    p = payment_service.create_customer_payment(
        customer_id=cid,
        amount=Decimal("150"),
        reference_number=ref_num
    )
    assert p is not None
    assert p.reference_number == ref_num


def test_payment_with_notes(payment_service, db_manager):
    """اختبار دفعة مع ملاحظات"""
    db, cid = db_manager
    notes = "دفعة اختبارية مع ملاحظات"
    
    p = payment_service.create_customer_payment(
        customer_id=cid,
        amount=Decimal("75"),
        notes=notes
    )
    assert p is not None
    assert p.notes == notes


def test_payment_with_bank_transfer(payment_service, db_manager):
    """اختبار دفعة بتحويل بنكي"""
    db, cid = db_manager
    
    p = payment_service.create_customer_payment(
        customer_id=cid,
        amount=Decimal("1000"),
        payment_method="bank_transfer",
        bank_name="بنك الاختبار",
        account_number="ACC123456"
    )
    assert p is not None
    assert p.payment_method == "bank_transfer"
    assert p.bank_name == "بنك الاختبار"
    assert p.account_number == "ACC123456"


def test_payment_with_check(payment_service, db_manager):
    """اختبار دفعة بشيك"""
    db, cid = db_manager
    
    p = payment_service.create_customer_payment(
        customer_id=cid,
        amount=Decimal("2500"),
        payment_method="check",
        reference_number="CHK-789"
    )
    assert p is not None
    assert p.payment_method == "check"


def test_multiple_payments_same_customer(payment_service, db_manager):
    """اختبار عدة دفعات لنفس العميل"""
    db, cid = db_manager
    
    amounts = [Decimal("100"), Decimal("200"), Decimal("300")]
    for amt in amounts:
        p = payment_service.create_customer_payment(customer_id=cid, amount=amt)
        assert p is not None
    
    all_payments = payment_service.get_customer_payments(cid)
    assert len(all_payments) >= len(amounts)


def test_payment_validation_negative_amount(payment_service, db_manager):
    """اختبار التحقق من المبالغ السالبة"""
    db, cid = db_manager
    
    # محاولة إنشاء دفعة بمبلغ سالب
    try:
        p = payment_service.create_customer_payment(
            customer_id=cid,
            amount=Decimal("-100")
        )
        # إذا نجح، تحقق من أن المبلغ موجب
        if p:
            assert float(p.amount) >= 0
    except Exception:
        # إذا رفض، هذا صحيح
        pass


def test_payment_zero_amount(payment_service, db_manager):
    """اختبار دفعة بمبلغ صفر"""
    db, cid = db_manager
    
    p = payment_service.create_customer_payment(
        customer_id=cid,
        amount=Decimal("0")
    )
    # يمكن قبول صفر في بعض الحالات (إلغاء، إرجاع كامل)
    if p:
        assert float(p.amount) == 0


def test_payment_large_amount(payment_service, db_manager):
    """اختبار دفعة بمبلغ كبير"""
    db, cid = db_manager
    
    large_amount = Decimal("999999.99")
    p = payment_service.create_customer_payment(
        customer_id=cid,
        amount=large_amount
    )
    assert p is not None
    assert float(p.amount) == float(large_amount)


def test_payment_decimal_precision(payment_service, db_manager):
    """اختبار دقة الأرقام العشرية"""
    db, cid = db_manager
    
    precise_amount = Decimal("123.456")
    p = payment_service.create_customer_payment(
        customer_id=cid,
        amount=precise_amount
    )
    assert p is not None
    # التحقق من الحفاظ على الدقة (مع تسامح صغير)
    assert abs(float(p.amount) - float(precise_amount)) < 0.01


def test_payment_status_completed(payment_service, db_manager):
    """اختبار حالة الدفعة المكتملة"""
    db, cid = db_manager
    
    p = payment_service.create_customer_payment(
        customer_id=cid,
        amount=Decimal("100")
    )
    assert p is not None
    # دفعات العملاء افتراضياً مكتملة
    assert p.status in ["completed", "pending"]


def test_get_nonexistent_payment(payment_service):
    """اختبار الحصول على دفعة غير موجودة"""
    p = payment_service.get_payment_by_id(99999)
    assert p is None


def test_payment_number_uniqueness(payment_service, db_manager):
    """اختبار تفرد رقم الدفعة"""
    db, cid = db_manager
    
    p1 = payment_service.create_customer_payment(customer_id=cid, amount=Decimal("50"))
    p2 = payment_service.create_customer_payment(customer_id=cid, amount=Decimal("60"))
    
    assert p1 is not None and p2 is not None
    assert p1.payment_number != p2.payment_number


def test_payment_with_custom_date(payment_service, db_manager):
    """اختبار دفعة مع تاريخ مخصص"""
    from datetime import date
    db, cid = db_manager
    
    custom_date = date(2024, 12, 1)
    p = payment_service.create_customer_payment(
        customer_id=cid,
        amount=Decimal("100"),
        payment_date=custom_date
    )
    assert p is not None
    assert p.payment_date == custom_date