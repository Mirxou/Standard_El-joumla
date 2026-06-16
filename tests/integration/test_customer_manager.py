"""
Integration Tests for Customer Manager
اختبارات تكامل لـ CustomerManager
"""

import pytest

from src.models.customer import Customer, CustomerManager


@pytest.mark.requires_db
class TestCustomerManager:
    """اختبارات CustomerManager"""

    def test_create_customer(self, db_manager, sample_customer_data):
        """اختبار إنشاء عميل"""
        manager = CustomerManager(db_manager)
        customer = Customer(**sample_customer_data)

        customer_id = manager.create_customer(customer)
        assert customer_id is not None
        assert customer_id > 0

    def test_get_customer_by_id(self, db_manager, sample_customer_data):
        """اختبار الحصول على عميل بالمعرف"""
        manager = CustomerManager(db_manager)
        customer = Customer(**sample_customer_data)

        customer_id = manager.create_customer(customer)
        assert customer_id is not None

        # الحصول على العميل
        retrieved_customer = manager.get_customer_by_id(customer_id)
        assert retrieved_customer is not None
        assert retrieved_customer.id == customer_id
        assert retrieved_customer.name == sample_customer_data["name"]

    def test_get_customer_by_phone(self, db_manager, sample_customer_data):
        """اختبار الحصول على عميل برقم الهاتف"""
        manager = CustomerManager(db_manager)
        customer = Customer(**sample_customer_data)

        customer_id = manager.create_customer(customer)
        assert customer_id is not None

        # البحث برقم الهاتف
        found_customer = manager.get_customer_by_phone(sample_customer_data["phone"])
        assert found_customer is not None
        assert found_customer.phone == sample_customer_data["phone"]

    def test_search_customers(self, db_manager, sample_customer_data):
        """اختبار البحث في العملاء"""
        manager = CustomerManager(db_manager)
        customer = Customer(**sample_customer_data)

        manager.create_customer(customer)

        # البحث
        results = manager.search_customers(search_term=sample_customer_data["name"])
        assert len(results) > 0
        assert any(c.name == sample_customer_data["name"] for c in results)

    def test_update_customer(self, db_manager, sample_customer_data):
        """اختبار تحديث عميل"""
        manager = CustomerManager(db_manager)
        customer = Customer(**sample_customer_data)

        customer_id = manager.create_customer(customer)
        assert customer_id is not None

        # تحديث العميل
        customer = manager.get_customer_by_id(customer_id)
        customer.name = "عميل محدث"
        customer.email = "updated@example.com"

        success = manager.update_customer(customer)
        assert success is True

        # التحقق من التحديث
        updated_customer = manager.get_customer_by_id(customer_id)
        assert updated_customer.name == "عميل محدث"
        assert updated_customer.email == "updated@example.com"

    def test_delete_customer(self, db_manager, sample_customer_data):
        """اختبار حذف عميل"""
        manager = CustomerManager(db_manager)
        customer = Customer(**sample_customer_data)

        customer_id = manager.create_customer(customer)
        assert customer_id is not None

        # حذف العميل
        success = manager.delete_customer(customer_id)
        assert success is True

        # التحقق من الحذف
        deleted_customer = manager.get_customer_by_id(customer_id)
        assert deleted_customer is None or deleted_customer.is_active is False

    def test_get_all_customers(self, db_manager, sample_customer_data):
        """اختبار الحصول على جميع العملاء"""
        manager = CustomerManager(db_manager)

        # إنشاء عدة عملاء
        for i in range(3):
            customer_data = sample_customer_data.copy()
            customer_data["name"] = f"عميل {i}"
            customer_data["phone"] = f"012345678{i}"
            customer = Customer(**customer_data)
            manager.create_customer(customer)

        # الحصول على جميع العملاء
        all_customers = manager.get_all_customers()
        assert len(all_customers) >= 3
