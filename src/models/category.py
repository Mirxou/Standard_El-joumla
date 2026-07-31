import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج الفئة - Category Model
يحتوي على جميع العمليات المتعلقة بفئات المنتجات
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Category:
    """نموذج بيانات الفئة"""

    id: Optional[int] = None
    name: str = ""
    name_en: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    products_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "name": self.name,
            "name_en": self.name_en,
            "description": self.description,
            "parent_id": self.parent_id,
            "parent_name": self.parent_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "products_count": self.products_count,
        }


class CategoryManager:
    """مدير الفئات"""

    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger

    def create_category(self, category: Category) -> Optional[int]:
        """إنشاء فئة جديدة"""
        try:
            query = """
            INSERT INTO categories (
                name, name_en, description, parent_id, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            now = datetime.now()
            params = (
                category.name,
                category.name_en,
                category.description,
                category.parent_id,
                category.is_active,
                now,
                now,
            )

            if hasattr(self.db_manager, "execute_insert"):
                result = self.db_manager.execute_insert(query, params)
            else:
                res = self.db_manager.execute_query(query, params)
                result = getattr(res, "lastrowid", None) or getattr(res, "last_insert_id", None)

            if result:
                if self.logger:
                    self.logger.info(f"تم إنشاء فئة جديدة: {category.name} (ID: {result})")
                return result

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء الفئة: {str(e)}")
            return None

    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """الحصول على فئة بالمعرف"""
        try:
            query = """
            SELECT c.id, c.name, c.name_en, c.description, c.parent_id, c.is_active, c.created_at, c.updated_at,
                   p.name as parent_name,
                   (SELECT COUNT(*) FROM products WHERE category_id = c.id AND is_active = 1) as products_count
            FROM categories c
            LEFT JOIN categories p ON c.parent_id = p.id
            WHERE c.id = ?
            """

            result = self.db_manager.fetch_one(query, (category_id,))
            if result:
                return self._row_to_category(result)

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الفئة {category_id}: {str(e)}")

        return None

    def get_all_categories(self, active_only: bool = True, include_products_count: bool = True) -> List[Category]:
        """الحصول على جميع الفئات"""
        try:
            if include_products_count:
                query = """
                SELECT c.id, c.name, c.name_en, c.description, c.parent_id, c.is_active, c.created_at, c.updated_at,
                       p.name as parent_name,
                       (SELECT COUNT(*) FROM products WHERE category_id = c.id AND is_active = 1) as products_count
                FROM categories c
                LEFT JOIN categories p ON c.parent_id = p.id
                """
            else:
                query = """
                SELECT c.id, c.name, c.name_en, c.description, c.parent_id, c.is_active, c.created_at, c.updated_at,
                       p.name as parent_name, 0 as products_count
                FROM categories c
                LEFT JOIN categories p ON c.parent_id = p.id
                """

            if active_only:
                query += " WHERE c.is_active = 1"

            query += " ORDER BY c.name"

            results = self.db_manager.fetch_all(query)
            return [self._row_to_category(row) for row in results]

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الفئات: {str(e)}")
            return []

    def get_parent_categories(self) -> List[Category]:
        """الحصول على الفئات الرئيسية فقط"""
        try:
            query = """
            SELECT c.id, c.name, c.name_en, c.description, c.parent_id, c.is_active, c.created_at, c.updated_at,
                   NULL as parent_name,
                   (SELECT COUNT(*) FROM products WHERE category_id = c.id AND is_active = 1) as products_count
            FROM categories c
            WHERE c.parent_id IS NULL AND c.is_active = 1
            ORDER BY c.name
            """

            results = self.db_manager.fetch_all(query)
            return [self._row_to_category(row) for row in results]

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الفئات الرئيسية: {str(e)}")
            return []

    def get_subcategories(self, parent_id: int) -> List[Category]:
        """الحصول على الفئات الفرعية لفئة معينة"""
        try:
            query = """
            SELECT c.id, c.name, c.name_en, c.description, c.parent_id, c.is_active, c.created_at, c.updated_at,
                   p.name as parent_name,
                   (SELECT COUNT(*) FROM products WHERE category_id = c.id AND is_active = 1) as products_count
            FROM categories c
            LEFT JOIN categories p ON c.parent_id = p.id
            WHERE c.parent_id = ? AND c.is_active = 1
            ORDER BY c.name
            """

            results = self.db_manager.fetch_all(query, (parent_id,))
            return [self._row_to_category(row) for row in results]

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الفئات الفرعية للفئة {parent_id}: {str(e)}")
            return []

    def search_categories(self, search_term: str) -> List[Category]:
        """البحث في الفئات"""
        try:
            query = """
            SELECT c.id, c.name, c.name_en, c.description, c.parent_id, c.is_active, c.created_at, c.updated_at,
                   p.name as parent_name,
                   (SELECT COUNT(*) FROM products WHERE category_id = c.id AND is_active = 1) as products_count
            FROM categories c
            LEFT JOIN categories p ON c.parent_id = p.id
            WHERE (c.name LIKE ? OR c.name_en LIKE ? OR c.description LIKE ?)
                  AND c.is_active = 1
            ORDER BY c.name
            """

            search_pattern = f"%{search_term}%"
            params = [search_pattern, search_pattern, search_pattern]

            results = self.db_manager.fetch_all(query, params)
            return [self._row_to_category(row) for row in results]

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث في الفئات: {str(e)}")
            return []

    def update_category(self, category: Category) -> bool:
        """تحديث فئة"""
        try:
            query = """
            UPDATE categories SET
                name = ?, name_en = ?, description = ?, parent_id = ?,
                is_active = ?, updated_at = ?
            WHERE id = ?
            """

            params = (
                category.name,
                category.name_en,
                category.description,
                category.parent_id,
                category.is_active,
                datetime.now(),
                category.id,
            )

            result = self.db_manager.execute_non_query(query, params)
            if result > 0:
                if self.logger:
                    self.logger.info(f"تم تحديث الفئة: {category.name} (ID: {category.id})")
                return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث الفئة {category.id}: {str(e)}")

        return False

    def delete_category(self, category_id: int, soft_delete: bool = True) -> bool:
        """حذف فئة"""
        try:
            # التحقق من وجود منتجات في هذه الفئة
            products_count = self.get_products_count_in_category(category_id)
            if products_count > 0:
                if self.logger:
                    self.logger.warning(f"لا يمكن حذف الفئة {category_id} - تحتوي على {products_count} منتج")
                return False

            # التحقق من وجود فئات فرعية
            subcategories = self.get_subcategories(category_id)
            if subcategories:
                if self.logger:
                    self.logger.warning(f"لا يمكن حذف الفئة {category_id} - تحتوي على فئات فرعية")
                return False

            if soft_delete:
                # حذف ناعم - تعطيل الفئة فقط
                query = "UPDATE categories SET is_active = 0, updated_at = ? WHERE id = ?"
                params = (datetime.now(), category_id)
            else:
                # حذف صلب - حذف نهائي
                query = "DELETE FROM categories WHERE id = ?"
                params = (category_id,)

            result = self.db_manager.execute_non_query(query, params)
            if result > 0:
                if self.logger:
                    action = "تعطيل" if soft_delete else "حذف"
                    self.logger.info(f"تم {action} الفئة (ID: {category_id})")
                return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف الفئة {category_id}: {str(e)}")

        return False

    def get_products_count_in_category(self, category_id: int) -> int:
        """الحصول على عدد المنتجات في فئة معينة"""
        try:
            query = "SELECT COUNT(*) FROM products WHERE category_id = ? AND is_active = 1"
            result = self.db_manager.fetch_one(query, (category_id,))
            if result:
                return result.get("COUNT(*)", result.get("count", 0)) if isinstance(result, dict) else result[0]
            return 0

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب المنتجات للفئة {category_id}: {str(e)}")
            return 0

    def get_category_tree(self) -> List[Dict[str, Any]]:
        """الحصول على شجرة الفئات"""
        try:
            # الحصول على جميع الفئات
            all_categories = self.get_all_categories(active_only=True)

            # تنظيم الفئات في شجرة
            categories_dict = {cat.id: cat.to_dict() for cat in all_categories}
            tree = []

            for category in all_categories:
                cat_dict = category.to_dict()
                cat_dict["children"] = []

                if category.parent_id is None:
                    # فئة رئيسية
                    tree.append(cat_dict)
                else:
                    # فئة فرعية
                    if category.parent_id in categories_dict:
                        parent = next((c for c in tree if c["id"] == category.parent_id), None)
                        if parent:
                            parent["children"].append(cat_dict)

            return tree

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء شجرة الفئات: {str(e)}")
            return []

    def get_categories_report(self) -> Dict[str, Any]:
        """تقرير الفئات"""
        try:
            query = """
            SELECT
                COUNT(*) as total_categories,
                COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_categories,
                COUNT(CASE WHEN parent_id IS NULL AND is_active = 1 THEN 1 END) as parent_categories,
                COUNT(CASE WHEN parent_id IS NOT NULL AND is_active = 1 THEN 1 END) as sub_categories
            FROM categories
            """

            result = self.db_manager.fetch_one(query)
            if result:
                if isinstance(result, dict):
                    return {
                        "total_categories": result.get("total_categories", 0) or 0,
                        "active_categories": result.get("active_categories", 0) or 0,
                        "parent_categories": result.get("parent_categories", 0) or 0,
                        "sub_categories": result.get("sub_categories", 0) or 0,
                    }
                return {
                    "total_categories": result[0] or 0,
                    "active_categories": result[1] or 0,
                    "parent_categories": result[2] or 0,
                    "sub_categories": result[3] or 0,
                }

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء تقرير الفئات: {str(e)}")

        return {
            "total_categories": 0,
            "active_categories": 0,
            "parent_categories": 0,
            "sub_categories": 0,
        }

    def create_default_categories(self) -> bool:
        """إنشاء فئات افتراضية إذا كانت قاعدة البيانات فارغة"""
        try:
            # التحقق من وجود فئات
            existing_count = self.db_manager.fetch_one("SELECT COUNT(*) FROM categories")
            if existing_count and existing_count[0] > 0:
                if self.logger:
                    self.logger.info("توجد فئات بالفعل في قاعدة البيانات - تخطي إنشاء الفئات الافتراضية")
                return True

            # قائمة الفئات الافتراضية
            default_categories = [
                {
                    "name": "إلكترونيات",
                    "name_en": "Electronics",
                    "description": "أجهزة إلكترونية وكهربائية",
                },
                {
                    "name": "مواد غذائية",
                    "name_en": "Food",
                    "description": "منتجات غذائية ومشروبات",
                },
                {
                    "name": "ملابس",
                    "name_en": "Clothing",
                    "description": "ملابس وأحذية وأكسسوارات",
                },
                {
                    "name": "أدوات مكتبية",
                    "name_en": "Stationery",
                    "description": "أقلام ودفاتر وأدوات مكتبية",
                },
                {
                    "name": "منظفات",
                    "name_en": "Detergents",
                    "description": "مواد تنظيف ومنتجات عناية منزلية",
                },
                {
                    "name": "ألعاب",
                    "name_en": "Toys",
                    "description": "ألعاب أطفال وهدايا",
                },
                {"name": "أخرى", "name_en": "Other", "description": "فئات متنوعة"},
            ]

            for cat_data in default_categories:
                category = Category(
                    name=cat_data["name"],
                    name_en=cat_data["name_en"],
                    description=cat_data["description"],
                    is_active=True,
                )
                self.create_category(category)

            if self.logger:
                self.logger.info(f"تم إنشاء {len(default_categories)} فئة افتراضية")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء الفئات الافتراضية: {str(e)}")
            return False

    def _row_to_category(self, row) -> Optional[Category]:
        """تحويل صف قاعدة البيانات إلى كائن فئة"""
        if not row:
            return None

        try:
            is_dict = isinstance(row, dict)

            def get_val(key, idx, default=None):
                if is_dict:
                    return row.get(key, default)
                return row[idx] if len(row) > idx else default

            return Category(
                id=get_val("id", 0),
                name=get_val("name", 1),
                name_en=get_val("name_en", 2),
                description=get_val("description", 3),
                parent_id=get_val("parent_id", 4),
                is_active=bool(get_val("is_active", 5, True)),
                created_at=self._parse_datetime(get_val("created_at", 6)),
                updated_at=self._parse_datetime(get_val("updated_at", 7)),
                parent_name=get_val("parent_name", 8),
                products_count=get_val("products_count", 9, 0),
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error mapping category: {e}")
            return None

    def _parse_datetime(self, val):
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        try:
            return datetime.fromisoformat(str(val))
        except Exception:
            return None
