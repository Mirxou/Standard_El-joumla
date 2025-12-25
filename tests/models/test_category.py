"""
اختبارات شاملة لنموذج Category
Comprehensive tests for Category model
"""

import unittest
from datetime import datetime
from src.models.category import Category, CategoryManager


class TestCategoryCreation(unittest.TestCase):
    """اختبارات إنشاء فئة"""

    def test_category_basic_creation(self):
        """إنشاء فئة أساسية"""
        category = Category(
            name="الملابس",
            description="فئة الملابس والأزياء"
        )
        self.assertEqual(category.name, "الملابس")
        self.assertEqual(category.description, "فئة الملابس والأزياء")

    def test_category_default_active(self):
        """الفئة نشطة افتراضياً"""
        category = Category(name="الملابس")
        self.assertTrue(category.is_active)

    def test_category_default_products_count(self):
        """عدد المنتجات الافتراضي صفر"""
        category = Category(name="الملابس")
        self.assertEqual(category.products_count, 0)

    def test_category_with_id(self):
        """فئة مع معرف"""
        category = Category(
            id=1,
            name="الملابس"
        )
        self.assertEqual(category.id, 1)

    def test_category_with_english_name(self):
        """فئة مع اسم إنجليزي"""
        category = Category(
            name="الملابس",
            name_en="Clothes"
        )
        self.assertEqual(category.name_en, "Clothes")

    def test_category_inactive(self):
        """فئة غير نشطة"""
        category = Category(
            name="الملابس",
            is_active=False
        )
        self.assertFalse(category.is_active)

    def test_category_with_products_count(self):
        """فئة مع عدد منتجات"""
        category = Category(
            name="الملابس",
            products_count=25
        )
        self.assertEqual(category.products_count, 25)

    def test_category_with_timestamps(self):
        """فئة مع طوابع زمنية"""
        now = datetime.now()
        category = Category(
            name="الملابس",
            created_at=now,
            updated_at=now
        )
        self.assertEqual(category.created_at, now)
        self.assertEqual(category.updated_at, now)


class TestCategoryHierarchy(unittest.TestCase):
    """اختبارات الهرمية في الفئات"""

    def test_category_no_parent(self):
        """فئة بدون فئة أب"""
        category = Category(
            name="الملابس",
            parent_id=None
        )
        self.assertIsNone(category.parent_id)
        self.assertIsNone(category.parent_name)

    def test_category_with_parent_id(self):
        """فئة مع فئة أب"""
        category = Category(
            name="الملابس الرجالية",
            parent_id=1,
            parent_name="الملابس"
        )
        self.assertEqual(category.parent_id, 1)
        self.assertEqual(category.parent_name, "الملابس")

    def test_category_parent_name(self):
        """اسم الفئة الأب"""
        category = Category(
            name="الملابس الرجالية",
            parent_id=1,
            parent_name="الملابس"
        )
        self.assertIsNotNone(category.parent_name)
        self.assertEqual(category.parent_name, "الملابس")

    def test_subcategory_hierarchy(self):
        """هرمية فئة فرعية"""
        parent = Category(
            id=1,
            name="الملابس"
        )
        child = Category(
            id=2,
            name="الملابس الرجالية",
            parent_id=parent.id,
            parent_name=parent.name
        )
        self.assertEqual(child.parent_id, parent.id)


class TestCategorySerialization(unittest.TestCase):
    """اختبارات تسلسل بيانات الفئة"""

    def test_category_to_dict(self):
        """تحويل الفئة إلى قاموس"""
        category = Category(
            id=1,
            name="الملابس",
            name_en="Clothes",
            description="فئة الملابس",
            is_active=True,
            products_count=10
        )
        category_dict = category.to_dict()
        
        self.assertEqual(category_dict['id'], 1)
        self.assertEqual(category_dict['name'], "الملابس")
        self.assertEqual(category_dict['name_en'], "Clothes")
        self.assertEqual(category_dict['description'], "فئة الملابس")
        self.assertTrue(category_dict['is_active'])
        self.assertEqual(category_dict['products_count'], 10)

    def test_category_to_dict_with_timestamps(self):
        """تحويل فئة مع طوابع زمنية"""
        now = datetime.now()
        category = Category(
            id=1,
            name="الملابس",
            created_at=now,
            updated_at=now
        )
        category_dict = category.to_dict()
        
        self.assertIsNotNone(category_dict['created_at'])
        self.assertIsNotNone(category_dict['updated_at'])

    def test_category_to_dict_with_parent(self):
        """تحويل فئة فرعية إلى قاموس"""
        category = Category(
            id=2,
            name="الملابس الرجالية",
            parent_id=1,
            parent_name="الملابس"
        )
        category_dict = category.to_dict()
        
        self.assertEqual(category_dict['parent_id'], 1)
        self.assertEqual(category_dict['parent_name'], "الملابس")

    def test_category_to_dict_none_values(self):
        """تحويل فئة مع قيم None"""
        category = Category(
            name="الملابس",
            description=None,
            parent_id=None,
            created_at=None
        )
        category_dict = category.to_dict()
        
        self.assertIsNone(category_dict['description'])
        self.assertIsNone(category_dict['parent_id'])
        self.assertIsNone(category_dict['created_at'])


class TestCategoryProperties(unittest.TestCase):
    """اختبارات خصائص الفئة"""

    def test_category_name(self):
        """اسم الفئة"""
        category = Category(name="الملابس")
        self.assertEqual(category.name, "الملابس")

    def test_category_empty_name(self):
        """فئة باسم فارغ"""
        category = Category(name="")
        self.assertEqual(category.name, "")

    def test_category_long_name(self):
        """فئة باسم طويل"""
        long_name = "الملابس والأزياء والملحقات والحقائب والأحذية"
        category = Category(name=long_name)
        self.assertEqual(category.name, long_name)

    def test_category_description(self):
        """وصف الفئة"""
        desc = "هذه فئة الملابس التي تشمل جميع أنواع الملابس"
        category = Category(
            name="الملابس",
            description=desc
        )
        self.assertEqual(category.description, desc)


class TestCategoryEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدية"""

    def test_category_zero_products(self):
        """فئة بدون منتجات"""
        category = Category(
            name="الملابس",
            products_count=0
        )
        self.assertEqual(category.products_count, 0)

    def test_category_large_products_count(self):
        """فئة بعدد كبير من المنتجات"""
        category = Category(
            name="الملابس",
            products_count=10000
        )
        self.assertEqual(category.products_count, 10000)

    def test_category_with_special_characters(self):
        """فئة باسم يحتوي على أحرف خاصة"""
        category = Category(
            name="الملابس & الأزياء (النسائية)",
            description="فئة الملابس النسائية #جديد"
        )
        self.assertIn("&", category.name)
        self.assertIn("#", category.description)

    def test_category_both_languages(self):
        """فئة باللغة العربية والإنجليزية"""
        category = Category(
            name="الملابس",
            name_en="Clothes"
        )
        self.assertEqual(category.name, "الملابس")
        self.assertEqual(category.name_en, "Clothes")

    def test_multiple_categories_hierarchy(self):
        """هرمية متعددة المستويات"""
        # المستوى الأول
        parent = Category(id=1, name="الملابس")
        
        # المستوى الثاني
        child = Category(id=2, name="الملابس الرجالية", parent_id=1, parent_name="الملابس")
        
        # المستوى الثالث
        grandchild = Category(id=3, name="الملابس الرجالية - قمصان", parent_id=2, parent_name="الملابس الرجالية")
        
        self.assertIsNone(parent.parent_id)
        self.assertEqual(child.parent_id, parent.id)
        self.assertEqual(grandchild.parent_id, child.id)

    def test_category_activation_toggle(self):
        """تبديل حالة تفعيل الفئة"""
        category = Category(
            name="الملابس",
            is_active=True
        )
        self.assertTrue(category.is_active)
        
        category.is_active = False
        self.assertFalse(category.is_active)

    def test_category_timestamps_update(self):
        """تحديث الطوابع الزمنية"""
        now = datetime.now()
        category = Category(
            name="الملابس",
            created_at=now
        )
        
        later = datetime.now()
        category.updated_at = later
        
        self.assertEqual(category.created_at, now)
        self.assertEqual(category.updated_at, later)

    def test_category_id_zero(self):
        """فئة برقم معرف صفر"""
        category = Category(id=0, name="الملابس")
        self.assertEqual(category.id, 0)

    def test_category_parent_id_large(self):
        """معرف الفئة الأب كبير جداً"""
        category = Category(
            id=999999,
            name="فئة فرعية",
            parent_id=999998
        )
        self.assertEqual(category.id, 999999)
        self.assertEqual(category.parent_id, 999998)


class DummyCatResult:
    def __init__(self, rowcount=1, lastrowid=1):
        self.rowcount = rowcount
        self.lastrowid = lastrowid


class DummyCategoryDB:
    def __init__(self):
        self.fetch_one_results = []
        self.fetch_all_results = []
        self.execute_query_calls = []
        self.last_insert_id = 1

    def fetch_one(self, query, params=()):
        if self.fetch_one_results:
            return self.fetch_one_results.pop(0)
        return None

    def fetch_all(self, query, params=()):
        if self.fetch_all_results:
            return self.fetch_all_results.pop(0)
        return []

    def execute_query(self, query, params=()):
        self.execute_query_calls.append((query, params))
        return DummyCatResult(rowcount=1, lastrowid=self.last_insert_id)


class TestCategoryManager(unittest.TestCase):
    def test_create_category_returns_id(self):
        db = DummyCategoryDB()
        db.last_insert_id = 7
        manager = CategoryManager(db)
        category = Category(name="ملابس")

        new_id = manager.create_category(category)

        self.assertEqual(new_id, 7)

    def test_delete_category_blocks_when_has_products_or_children(self):
        db = DummyCategoryDB()
        db.fetch_one_results.append((3,))
        db.fetch_all_results.append([(1,)])
        manager = CategoryManager(db)

        result = manager.delete_category(1)

        self.assertFalse(result)

    def test_get_category_tree_builds_children(self):
        db = DummyCategoryDB()
        parent = (1, "Parent", None, None, None, 1, None, None, None, 0)
        child = (2, "Child", None, None, 1, 1, None, None, "Parent", 0)
        db.fetch_all_results.append([parent, child])

        manager = CategoryManager(db)
        tree = manager.get_category_tree()

        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['children'][0]['name'], "Child")


if __name__ == '__main__':
    unittest.main()
