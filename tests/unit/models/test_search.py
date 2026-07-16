"""
اختبارات نماذج Search
Tests for Search models
"""

import unittest
from datetime import date

from src.models.search import FilterOperator, SearchEntity, SearchFilter, SortDirection


class TestSearchEntity(unittest.TestCase):
    """اختبارات SearchEntity enum"""

    def test_search_entity_values(self):
        """فحص قيم SearchEntity"""
        self.assertEqual(SearchEntity.ALL.value, "الكل")
        self.assertEqual(SearchEntity.PRODUCTS.value, "المنتجات")
        self.assertEqual(SearchEntity.CUSTOMERS.value, "العملاء")
        self.assertEqual(SearchEntity.SUPPLIERS.value, "الموردين")
        self.assertEqual(SearchEntity.SALES.value, "المبيعات")
        self.assertEqual(SearchEntity.PURCHASES.value, "المشتريات")
        self.assertEqual(SearchEntity.QUOTES.value, "عروض الأسعار")
        self.assertEqual(SearchEntity.RETURNS.value, "المرتجعات")
        self.assertEqual(SearchEntity.ACCOUNTS.value, "الحسابات")

    def test_search_entity_membership(self):
        """فحص الأعضاء"""
        entities = list(SearchEntity)
        self.assertIn(SearchEntity.PRODUCTS, entities)
        self.assertIn(SearchEntity.SALES, entities)
        self.assertEqual(len(entities), 9)


class TestFilterOperator(unittest.TestCase):
    """اختبارات FilterOperator enum"""

    def test_filter_operator_comparison(self):
        """فحص عوامل المقارنة"""
        self.assertEqual(FilterOperator.EQUALS.value, "يساوي")
        self.assertEqual(FilterOperator.NOT_EQUALS.value, "لا يساوي")
        self.assertEqual(FilterOperator.GREATER_THAN.value, "أكبر من")
        self.assertEqual(FilterOperator.LESS_THAN.value, "أصغر من")
        self.assertEqual(FilterOperator.GREATER_OR_EQUAL.value, "أكبر من أو يساوي")
        self.assertEqual(FilterOperator.LESS_OR_EQUAL.value, "أصغر من أو يساوي")

    def test_filter_operator_string(self):
        """فحص عوامل النصوص"""
        self.assertEqual(FilterOperator.CONTAINS.value, "يحتوي")
        self.assertEqual(FilterOperator.NOT_CONTAINS.value, "لا يحتوي")
        self.assertEqual(FilterOperator.STARTS_WITH.value, "يبدأ بـ")
        self.assertEqual(FilterOperator.ENDS_WITH.value, "ينتهي بـ")

    def test_filter_operator_special(self):
        """فحص العوامل الخاصة"""
        self.assertEqual(FilterOperator.BETWEEN.value, "بين")
        self.assertEqual(FilterOperator.IN.value, "ضمن")
        self.assertEqual(FilterOperator.NOT_IN.value, "ليس ضمن")
        self.assertEqual(FilterOperator.IS_NULL.value, "فارغ")
        self.assertEqual(FilterOperator.IS_NOT_NULL.value, "غير فارغ")


class TestSortDirection(unittest.TestCase):
    """اختبارات SortDirection enum"""

    def test_sort_direction_values(self):
        """فحص قيم اتجاه الترتيب"""
        self.assertEqual(SortDirection.ASC.value, "تصاعدي")
        self.assertEqual(SortDirection.DESC.value, "تنازلي")

    def test_sort_direction_count(self):
        """عدد الاتجاهات"""
        self.assertEqual(len(list(SortDirection)), 2)


class TestSearchFilter(unittest.TestCase):
    """اختبارات SearchFilter dataclass"""

    def test_search_filter_basic(self):
        """إنشاء فلتر أساسي"""
        filter_obj = SearchFilter(field="name", operator=FilterOperator.CONTAINS, value="test")
        self.assertEqual(filter_obj.field, "name")
        self.assertEqual(filter_obj.operator, FilterOperator.CONTAINS)
        self.assertEqual(filter_obj.value, "test")
        self.assertIsNone(filter_obj.value2)

    def test_search_filter_equals(self):
        """فلتر يساوي"""
        filter_obj = SearchFilter(field="id", operator=FilterOperator.EQUALS, value=123)
        self.assertEqual(filter_obj.field, "id")
        self.assertEqual(filter_obj.operator, FilterOperator.EQUALS)
        self.assertEqual(filter_obj.value, 123)

    def test_search_filter_between(self):
        """فلتر بين قيمتين"""
        filter_obj = SearchFilter(field="price", operator=FilterOperator.BETWEEN, value=100, value2=500)
        self.assertEqual(filter_obj.field, "price")
        self.assertEqual(filter_obj.operator, FilterOperator.BETWEEN)
        self.assertEqual(filter_obj.value, 100)
        self.assertEqual(filter_obj.value2, 500)

    def test_search_filter_is_null(self):
        """فلتر فارغ"""
        filter_obj = SearchFilter(field="description", operator=FilterOperator.IS_NULL)
        self.assertEqual(filter_obj.field, "description")
        self.assertEqual(filter_obj.operator, FilterOperator.IS_NULL)
        self.assertIsNone(filter_obj.value)

    def test_search_filter_to_dict(self):
        """تحويل الفلتر إلى dict"""
        filter_obj = SearchFilter(field="category", operator=FilterOperator.IN, value=[1, 2, 3])
        result = filter_obj.to_dict()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["field"], "category")
        self.assertEqual(result["operator"], "IN")
        self.assertEqual(result["value"], [1, 2, 3])

    def test_search_filter_greater_than(self):
        """فلتر أكبر من"""
        filter_obj = SearchFilter(field="stock", operator=FilterOperator.GREATER_THAN, value=10)
        self.assertEqual(filter_obj.operator, FilterOperator.GREATER_THAN)
        self.assertEqual(filter_obj.value, 10)

    def test_search_filter_starts_with(self):
        """فلتر يبدأ بـ"""
        filter_obj = SearchFilter(field="barcode", operator=FilterOperator.STARTS_WITH, value="ABC")
        self.assertEqual(filter_obj.operator, FilterOperator.STARTS_WITH)
        self.assertEqual(filter_obj.value, "ABC")

    def test_search_filter_date_range(self):
        """فلتر نطاق تواريخ"""
        start = date(2025, 1, 1)
        end = date(2025, 12, 31)
        filter_obj = SearchFilter(field="created_at", operator=FilterOperator.BETWEEN, value=start, value2=end)
        self.assertEqual(filter_obj.value, start)
        self.assertEqual(filter_obj.value2, end)


class TestSearchFilterCombinations(unittest.TestCase):
    """اختبارات تركيبات متعددة من الفلاتر"""

    def test_multiple_filters_creation(self):
        """إنشاء عدة فلاتر"""
        filters = [
            SearchFilter("name", FilterOperator.CONTAINS, "product"),
            SearchFilter("price", FilterOperator.GREATER_THAN, 100),
            SearchFilter("stock", FilterOperator.LESS_THAN, 50),
        ]
        self.assertEqual(len(filters), 3)
        self.assertEqual(filters[0].field, "name")
        self.assertEqual(filters[1].value, 100)
        self.assertEqual(filters[2].operator, FilterOperator.LESS_THAN)

    def test_filter_with_none_value(self):
        """فلتر مع قيمة None"""
        filter_obj = SearchFilter(field="notes", operator=FilterOperator.IS_NOT_NULL, value=None)
        self.assertIsNone(filter_obj.value)
        self.assertEqual(filter_obj.operator, FilterOperator.IS_NOT_NULL)


if __name__ == "__main__":
    unittest.main()
