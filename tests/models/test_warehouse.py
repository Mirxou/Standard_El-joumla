from datetime import datetime

import pytest

from src.models.warehouse import (
    Warehouse,
    WarehouseInventory,
    WarehouseTransfer,
    WarehouseManager,
    WarehouseInventoryManager,
    WarehouseTransferManager,
)


class DummyDB:
    def __init__(self):
        self.queries = []
        self.params = []
        self.insert_ids = []
        self.one_result = []
        self.all_results = []
        self.execute_results = []
        self.insert_next_id = 1

    def execute_insert(self, query, params=()):
        self.queries.append(query)
        self.params.append(params)
        new_id = self.insert_next_id
        self.insert_ids.append(new_id)
        self.insert_next_id += 1
        return new_id

    def execute_query(self, query, params=()):
        self.queries.append(query)
        self.params.append(params)
        if self.execute_results:
            return self.execute_results.pop(0)
        return list(self.all_results)


class DummyLogger:
    def __init__(self):
        self.logs = []

    def info(self, msg):
        self.logs.append(("info", msg))

    def debug(self, msg):
        self.logs.append(("debug", msg))

    def warning(self, msg):
        self.logs.append(("warning", msg))

    def error(self, msg):
        self.logs.append(("error", msg))


def test_warehouse_to_from_dict_roundtrip():
    now = datetime(2024, 1, 2, 3, 4, 5)
    w = Warehouse(
        id=5,
        code="WH1",
        name="Main",
        name_en="Main EN",
        address="Addr",
        city="City",
        country="DZ",
        phone="123",
        email="e@x",
        manager_name="Mgr",
        manager_phone="999",
        is_active=False,
        is_default=True,
        notes="note",
        created_at=now,
        updated_at=now,
        created_by=1,
        updated_by=2,
    )
    d = w.to_dict()
    assert d["is_active"] == 0
    assert d["is_default"] == 1
    w2 = Warehouse.from_dict(d)
    assert w2.code == "WH1"
    assert w2.is_default is True


def test_warehouse_manager_create_prevents_duplicates_and_sets_default(monkeypatch):
    db = DummyDB()
    logger = DummyLogger()
    mgr = WarehouseManager(db, logger)

    monkeypatch.setattr(mgr, "get_warehouse_by_code", lambda code: Warehouse(id=1, code=code))
    duplicate = mgr.create_warehouse(Warehouse(code="DUP", name="Dup"))
    assert duplicate is None

    def fake_get(code):
        return None

    unset_called = {}
    monkeypatch.setattr(mgr, "get_warehouse_by_code", fake_get)
    monkeypatch.setattr(mgr, "_unset_default_warehouse", lambda exclude_id=None: unset_called.setdefault("called", True))

    new_id = mgr.create_warehouse(Warehouse(code="NEW", name="New", is_default=True))
    assert new_id == 1
    assert unset_called.get("called") is True


def test_warehouse_manager_get_update_delete_and_filters(monkeypatch):
    db = DummyDB()
    mgr = WarehouseManager(db, DummyLogger())

    db.all_results = [{"id": 2, "code": "C1", "name": "N", "is_default": 0, "is_active": 1}]
    w = mgr.get_warehouse_by_id(2)
    assert w.id == 2

    db.all_results = [{"id": 3, "code": "C2", "name": "N", "is_default": 1, "is_active": 1}]
    w2 = mgr.get_warehouse_by_code("C2")
    assert w2.id == 3
    w3 = mgr.get_default_warehouse()
    assert w3.id == 3

    db.all_results = [
        {"id": 4, "code": "C3", "name": "N", "is_default": 0, "is_active": 1},
        {"id": 5, "code": "C4", "name": "N", "is_default": 1, "is_active": 1},
    ]
    active = mgr.get_all_warehouses()
    assert len(active) == 2

    assert mgr.update_warehouse(Warehouse(id=4, code="X", name="Y")) is True

    db.execute_results = [[{"count": 2}]]
    assert mgr.delete_warehouse(5) is False
    db.execute_results = [[{"count": 0}], []]
    assert mgr.delete_warehouse(5) is True


def test_inventory_manager_basic_flows(monkeypatch):
    db = DummyDB()
    inv_mgr = WarehouseInventoryManager(db, DummyLogger())

    db.all_results = [{"id": 1, "warehouse_id": 2, "product_id": 3, "quantity": 5.0, "reserved_quantity": 1.0, "available_quantity": 4.0, "min_stock": 0, "max_stock": 10, "reorder_point": 2, "last_movement_date": "2024-01-02T00:00:00", "last_count_date": None, "notes": None, "created_at": None, "updated_at": None, "warehouse_name": "W", "product_name": "P"}]
    inv = inv_mgr.get_inventory(2, 3)
    assert inv.warehouse_name == "W"
    assert inv.available_quantity == 4.0

    monkeypatch.setattr(inv_mgr, "get_inventory", lambda w, p: None)
    assert inv_mgr.update_quantity(1, 2, 10.0) is True

    existing = WarehouseInventory(warehouse_id=1, product_id=2, quantity=5.0, reserved_quantity=1.0)
    monkeypatch.setattr(inv_mgr, "get_inventory", lambda w, p: existing)
    assert inv_mgr.update_quantity(1, 2, 7.0, reserved_quantity=2.0) is True

    monkeypatch.setattr(inv_mgr, "get_inventory", lambda w, p: WarehouseInventory(quantity=1.0, reserved_quantity=0.0, warehouse_id=w, product_id=p))
    assert inv_mgr.adjust_quantity(1, 2, -5.0) is False

    monkeypatch.setattr(inv_mgr, "get_inventory", lambda w, p: None)
    assert inv_mgr.adjust_quantity(1, 2, 3.0) is True

    inv_obj = WarehouseInventory(quantity=5.0, reserved_quantity=1.0, warehouse_id=1, product_id=2)
    monkeypatch.setattr(inv_mgr, "get_inventory", lambda w, p: inv_obj)
    assert inv_mgr.reserve_quantity(1, 2, 2.0) is True
    assert inv_mgr.release_reserved(1, 2, 5.0) is True


def test_transfer_manager_generate_and_create(monkeypatch):
    db = DummyDB()
    trans_mgr = WarehouseTransferManager(db, DummyLogger())

    db.all_results = [{"transfer_number": "TRF-000009"}]
    num = trans_mgr.generate_transfer_number()
    assert num == "TRF-000010"

    inv_obj = WarehouseInventory(available_quantity=1.0)
    monkeypatch.setattr(trans_mgr.inventory_manager, "get_inventory", lambda w, p: inv_obj)
    assert trans_mgr.create_transfer(WarehouseTransfer(from_warehouse_id=1, to_warehouse_id=2, product_id=3, quantity=5.0)) is None

    inv_obj2 = WarehouseInventory(available_quantity=10.0)
    monkeypatch.setattr(trans_mgr.inventory_manager, "get_inventory", lambda w, p: inv_obj2)
    reserved = {}
    monkeypatch.setattr(trans_mgr.inventory_manager, "reserve_quantity", lambda w, p, q: reserved.setdefault("called", (w, p, q)) or True)
    tid = trans_mgr.create_transfer(WarehouseTransfer(from_warehouse_id=1, to_warehouse_id=2, product_id=3, quantity=2.0))
    assert tid == 1
    assert reserved["called"] == (1, 3, 2.0)


def test_transfer_manager_complete_fallback(monkeypatch):
    db = DummyDB()
    trans_mgr = WarehouseTransferManager(db, DummyLogger())
    transfer = WarehouseTransfer(id=7, from_warehouse_id=1, to_warehouse_id=2, product_id=3, quantity=4.0, status="pending")
    monkeypatch.setattr(trans_mgr, "get_transfer_by_id", lambda tid: transfer)

    releases = {}
    monkeypatch.setattr(trans_mgr.inventory_manager, "release_reserved", lambda w, p, q: releases.setdefault("rel", (w, p, q)) or True)
    adjusts = {}
    monkeypatch.setattr(trans_mgr.inventory_manager, "adjust_quantity", lambda w, p, q: adjusts.setdefault(len(adjusts), (w, p, q)) or True)

    assert trans_mgr.complete_transfer(7, received_by=9) is True
    assert releases["rel"] == (1, 3, 4.0)
    assert adjusts[0] == (1, 3, -4.0)
    assert adjusts[1] == (2, 3, 4.0)


def test_transfer_mapping_and_listing(monkeypatch):
    db = DummyDB()
    trans_mgr = WarehouseTransferManager(db, DummyLogger())
    row = {
        "id": 11,
        "transfer_number": "TRF-000011",
        "from_warehouse_id": 1,
        "to_warehouse_id": 2,
        "product_id": 3,
        "quantity": 5.0,
        "status": "pending",
        "transfer_date": "2024-01-01T10:00:00",
        "received_date": None,
        "notes": "note",
        "created_by": 1,
        "received_by": None,
        "created_at": "2024-01-01T10:00:00",
        "updated_at": "2024-01-01T10:00:00",
        "from_warehouse_name": "W1",
        "to_warehouse_name": "W2",
        "product_name": "Prod",
    }
    transfer = trans_mgr._dict_to_transfer(row)
    assert transfer.transfer_number == "TRF-000011"
    assert transfer.from_warehouse_name == "W1"

    db.all_results = [row]
    tlist = trans_mgr.get_transfers(warehouse_id=1, status="pending")
    assert len(tlist) == 1
    assert tlist[0].product_name == "Prod"
"""
اختبارات شاملة لنموذج Warehouse
Comprehensive tests for Warehouse model
"""

import unittest
from datetime import datetime
from decimal import Decimal
from src.models.warehouse import Warehouse, WarehouseInventory


class TestWarehouse(unittest.TestCase):
    """اختبارات نموذج المستودع"""

    def test_warehouse_creation(self):
        """إنشاء مستودع"""
        warehouse = Warehouse(
            code="WH001",
            name="المستودع الرئيسي",
            name_en="Main Warehouse",
            address="شارع النيل",
            city="الجزائر",
            country="الجزائر"
        )
        self.assertEqual(warehouse.code, "WH001")
        self.assertEqual(warehouse.name, "المستودع الرئيسي")
        self.assertEqual(warehouse.name_en, "Main Warehouse")
        self.assertEqual(warehouse.address, "شارع النيل")
        self.assertEqual(warehouse.city, "الجزائر")

    def test_warehouse_with_manager_info(self):
        """مستودع مع معلومات المدير"""
        warehouse = Warehouse(
            code="WH001",
            name="المستودع الرئيسي",
            manager_name="أحمد محمد",
            manager_phone="0661234567"
        )
        self.assertEqual(warehouse.manager_name, "أحمد محمد")
        self.assertEqual(warehouse.manager_phone, "0661234567")

    def test_warehouse_contact_info(self):
        """مستودع مع معلومات التواصل"""
        warehouse = Warehouse(
            code="WH001",
            name="المستودع الرئيسي",
            phone="02123456789",
            email="warehouse@example.com"
        )
        self.assertEqual(warehouse.phone, "02123456789")
        self.assertEqual(warehouse.email, "warehouse@example.com")

    def test_warehouse_is_active(self):
        """مستودع نشط"""
        warehouse = Warehouse(
            code="WH001",
            name="المستودع الرئيسي",
            is_active=True
        )
        self.assertTrue(warehouse.is_active)

    def test_warehouse_is_inactive(self):
        """مستودع غير نشط"""
        warehouse = Warehouse(
            code="WH001",
            name="المستودع الرئيسي",
            is_active=False
        )
        self.assertFalse(warehouse.is_active)

    def test_warehouse_is_default(self):
        """مستودع افتراضي"""
        warehouse = Warehouse(
            code="WH001",
            name="المستودع الرئيسي",
            is_default=True
        )
        self.assertTrue(warehouse.is_default)

    def test_warehouse_not_default(self):
        """مستودع غير افتراضي"""
        warehouse = Warehouse(
            code="WH001",
            name="المستودع الرئيسي",
            is_default=False
        )
        self.assertFalse(warehouse.is_default)

    def test_warehouse_with_notes(self):
        """مستودع مع ملاحظات"""
        warehouse = Warehouse(
            code="WH001",
            name="المستودع الرئيسي",
            notes="مستودع مجهز بأنظمة الأمان"
        )
        self.assertEqual(warehouse.notes, "مستودع مجهز بأنظمة الأمان")

    def test_warehouse_with_timestamps(self):
        """مستودع مع طوابع زمنية"""
        now = datetime.now()
        warehouse = Warehouse(
            code="WH001",
            name="المستودع الرئيسي",
            created_at=now,
            updated_at=now,
            created_by=1,
            updated_by=1
        )
        self.assertEqual(warehouse.created_at, now)
        self.assertEqual(warehouse.updated_at, now)
        self.assertEqual(warehouse.created_by, 1)
        self.assertEqual(warehouse.updated_by, 1)

    def test_warehouse_default_country(self):
        """البلد الافتراضي للمستودع"""
        warehouse = Warehouse(
            code="WH001",
            name="المستودع الرئيسي"
        )
        self.assertEqual(warehouse.country, "الجزائر")

    def test_warehouse_to_dict(self):
        """تحويل المستودع إلى قاموس"""
        now = datetime.now()
        warehouse = Warehouse(
            id=1,
            code="WH001",
            name="المستودع الرئيسي",
            name_en="Main Warehouse",
            address="شارع النيل",
            city="الجزائر",
            country="الجزائر",
            phone="02123456789",
            email="warehouse@example.com",
            manager_name="أحمد محمد",
            manager_phone="0661234567",
            is_active=True,
            is_default=False,
            notes="ملاحظات",
            created_at=now,
            updated_at=now,
            created_by=1,
            updated_by=1
        )
        
        data = warehouse.to_dict()
        
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['code'], "WH001")
        self.assertEqual(data['name'], "المستودع الرئيسي")
        self.assertEqual(data['name_en'], "Main Warehouse")
        self.assertEqual(data['is_active'], 1)
        self.assertEqual(data['is_default'], 0)

    def test_warehouse_from_dict(self):
        """إنشاء مستودع من قاموس"""
        data = {
            'id': 1,
            'code': 'WH001',
            'name': 'المستودع الرئيسي',
            'name_en': 'Main Warehouse',
            'address': 'شارع النيل',
            'city': 'الجزائر',
            'country': 'الجزائر',
            'phone': '02123456789',
            'email': 'warehouse@example.com',
            'manager_name': 'أحمد محمد',
            'manager_phone': '0661234567',
            'is_active': 1,
            'is_default': 0,
            'notes': 'ملاحظات',
            'created_by': 1,
            'updated_by': 1
        }
        
        warehouse = Warehouse.from_dict(data)
        
        self.assertEqual(warehouse.id, 1)
        self.assertEqual(warehouse.code, 'WH001')
        self.assertEqual(warehouse.name, 'المستودع الرئيسي')
        self.assertTrue(warehouse.is_active)
        self.assertFalse(warehouse.is_default)

    def test_warehouse_round_trip(self):
        """اختبار التحويل ذهاباً وإياباً"""
        warehouse = Warehouse(
            id=1,
            code="WH001",
            name="المستودع الرئيسي",
            name_en="Main Warehouse",
            address="شارع النيل",
            city="الجزائر",
            country="الجزائر",
            phone="02123456789",
            email="warehouse@example.com",
            manager_name="أحمد محمد",
            manager_phone="0661234567",
            is_active=True,
            is_default=False,
            notes="ملاحظات",
            created_by=1,
            updated_by=1
        )
        
        data = warehouse.to_dict()
        warehouse2 = Warehouse.from_dict(data)
        
        self.assertEqual(warehouse.code, warehouse2.code)
        self.assertEqual(warehouse.name, warehouse2.name)
        self.assertEqual(warehouse.is_active, warehouse2.is_active)
        self.assertEqual(warehouse.is_default, warehouse2.is_default)

    def test_warehouse_with_id(self):
        """مستودع مع معرف"""
        warehouse = Warehouse(
            id=123,
            code="WH001",
            name="المستودع الرئيسي"
        )
        self.assertEqual(warehouse.id, 123)

    def test_warehouse_code_required(self):
        """كود المستودع ضروري"""
        warehouse = Warehouse(
            code="WH001",
            name="المستودع الرئيسي"
        )
        self.assertIsNotNone(warehouse.code)
        self.assertEqual(warehouse.code, "WH001")


class TestWarehouseInventory(unittest.TestCase):
    """اختبارات مخزون المستودع"""

    def test_warehouse_inventory_creation(self):
        """إنشاء مخزون المستودع"""
        inventory = WarehouseInventory(
            warehouse_id=1,
            product_id=1,
            quantity=100.0
        )
        self.assertEqual(inventory.warehouse_id, 1)
        self.assertEqual(inventory.product_id, 1)
        self.assertEqual(inventory.quantity, 100.0)

    def test_warehouse_inventory_with_reserved(self):
        """مخزون مع كمية محجوزة"""
        inventory = WarehouseInventory(
            warehouse_id=1,
            product_id=1,
            quantity=100.0,
            reserved_quantity=20.0
        )
        self.assertEqual(inventory.quantity, 100.0)
        self.assertEqual(inventory.reserved_quantity, 20.0)

    def test_warehouse_inventory_available_quantity(self):
        """الكمية المتاحة"""
        inventory = WarehouseInventory(
            warehouse_id=1,
            product_id=1,
            quantity=100.0,
            reserved_quantity=20.0,
            available_quantity=80.0
        )
        self.assertEqual(inventory.available_quantity, 80.0)

    def test_warehouse_inventory_zero_quantity(self):
        """مخزون بكمية صفر"""
        inventory = WarehouseInventory(
            warehouse_id=1,
            product_id=1,
            quantity=0.0
        )
        self.assertEqual(inventory.quantity, 0.0)

    def test_warehouse_inventory_with_id(self):
        """مخزون مع معرف"""
        inventory = WarehouseInventory(
            id=1,
            warehouse_id=1,
            product_id=1,
            quantity=100.0
        )
        self.assertEqual(inventory.id, 1)


class TestWarehouseValidation(unittest.TestCase):
    """اختبارات التحقق من صحة المستودع"""

    def test_warehouse_unique_code(self):
        """كود المستودع يجب أن يكون فريداً"""
        warehouse1 = Warehouse(code="WH001", name="المستودع الأول")
        warehouse2 = Warehouse(code="WH001", name="المستودع الثاني")
        
        # كلاهما سيكون لهما نفس الكود
        self.assertEqual(warehouse1.code, warehouse2.code)

    def test_warehouse_empty_code(self):
        """مستودع بكود فارغ"""
        warehouse = Warehouse(code="", name="المستودع")
        self.assertEqual(warehouse.code, "")

    def test_warehouse_empty_name(self):
        """مستودع باسم فارغ"""
        warehouse = Warehouse(code="WH001", name="")
        self.assertEqual(warehouse.name, "")


class TestWarehouseEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدية"""

    def test_warehouse_with_special_characters(self):
        """مستودع باسم يحتوي على أحرف خاصة"""
        warehouse = Warehouse(
            code="WH_001",
            name="المستودع #1 - الفرع الأول"
        )
        self.assertIn("#", warehouse.name)
        self.assertIn("-", warehouse.name)

    def test_warehouse_with_long_address(self):
        """مستودع بعنوان طويل"""
        address = "شارع النيل، منطقة الزيتونة، المحافظة الأولى، الجزائر" * 3
        warehouse = Warehouse(
            code="WH001",
            name="المستودع",
            address=address
        )
        self.assertIn("شارع النيل", warehouse.address)

    def test_warehouse_with_empty_optional_fields(self):
        """مستودع بحقول اختيارية فارغة"""
        warehouse = Warehouse(
            code="WH001",
            name="المستودع",
            address=None,
            city=None,
            notes=None
        )
        self.assertIsNone(warehouse.address)
        self.assertIsNone(warehouse.city)
        self.assertIsNone(warehouse.notes)

    def test_warehouse_inventory_decimal_quantities(self):
        """مخزون بكميات عشرية"""
        inventory = WarehouseInventory(
            warehouse_id=1,
            product_id=1,
            quantity=100.5,
            reserved_quantity=20.25,
            available_quantity=80.25
        )
        self.assertEqual(inventory.quantity, 100.5)
        self.assertEqual(inventory.reserved_quantity, 20.25)

    def test_multiple_warehouses(self):
        """عدة مستودعات"""
        warehouses = [
            Warehouse(code=f"WH{i:03d}", name=f"المستودع {i}")
            for i in range(1, 6)
        ]
        
        self.assertEqual(len(warehouses), 5)
        self.assertEqual(warehouses[0].code, "WH001")
        self.assertEqual(warehouses[4].code, "WH005")

    def test_warehouse_inventory_large_quantities(self):
        """مخزون بكميات كبيرة"""
        inventory = WarehouseInventory(
            warehouse_id=1,
            product_id=1,
            quantity=999999.99,
            reserved_quantity=100000.00,
            available_quantity=899999.99
        )
        self.assertEqual(inventory.quantity, 999999.99)

    def test_warehouse_multilingual_names(self):
        """مستودع بأسماء متعددة اللغات"""
        warehouse = Warehouse(
            code="WH001",
            name="المستودع الرئيسي",
            name_en="Main Warehouse"
        )
        self.assertIsNotNone(warehouse.name)
        self.assertIsNotNone(warehouse.name_en)
        self.assertNotEqual(warehouse.name, warehouse.name_en)


if __name__ == '__main__':
    unittest.main()
