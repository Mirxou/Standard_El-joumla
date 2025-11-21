#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة المنتجات المحسّنة - Enhanced Product Service
توفر عمليات متقدمة لإدارة المنتجات مع المتغيرات والحزم والتسعير
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.product_enhanced import (
    Product, ProductVariant, BundleProduct, PricingTier, ProductLabel,
    ProductType, PricingPolicy, UnitType,
    ProductVariantManager, BundleProductManager, ProductLabelManager
)

class ProductService:
    """خدمة شاملة للمنتجات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        self.variant_manager = ProductVariantManager(db_manager, logger)
        self.bundle_manager = BundleProductManager(db_manager, logger)
        self.label_manager = ProductLabelManager(db_manager, logger)
    
    # ==================== عمليات CRUD الأساسية ====================
    
    def create_product(self, product: Product) -> Optional[int]:
        """إنشاء منتج جديد مع جميع بياناته"""
        try:
            if not product.sku:
                product.sku = self._generate_sku()
            # Build insert dynamically based on existing table columns to remain compatible
            col_map = {
                'name': product.name,
                'name_en': product.name_en,
                'sku': getattr(product, 'sku', None),
                'barcode': product.barcode,
                'category_id': product.category_id,
                'supplier_id': getattr(product, 'supplier_id', None),
                'product_type': getattr(product, 'product_type', None),
                'description': product.description,
                'specifications': json.dumps(product.specifications, ensure_ascii=False) if product.specifications else None,
                'unit': product.unit,
                # map base_price -> selling_price if selling_price exists in schema
                'cost_price': float(product.cost_price) if product.cost_price is not None else None,
                'selling_price': float(product.base_price) if getattr(product, 'base_price', None) is not None else None,
                'pricing_policy': getattr(product, 'pricing_policy', None),
                'current_stock': product.current_stock,
                'reserved_stock': getattr(product, 'reserved_stock', None),
                'min_stock': getattr(product, 'min_stock', None),
                'reorder_point': getattr(product, 'reorder_point', None),
                'max_stock': getattr(product, 'max_stock', None),
                'image_path': product.image_path,
                'images': json.dumps(product.images) if product.images else None,
                'tags': json.dumps(product.tags) if product.tags else None,
                'is_active': int(product.is_active),
                'is_discontinued': int(getattr(product, 'is_discontinued', 0)),
                'is_featured': int(getattr(product, 'is_featured', 0)),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            # get existing columns from DB
            cols_info = self.db_manager.fetch_all("PRAGMA table_info(products)")
            existing_cols = [row[1] for row in cols_info] if cols_info else []

            insert_cols = []
            insert_vals = []
            for col, val in col_map.items():
                if col in existing_cols and val is not None:
                    insert_cols.append(col)
                    insert_vals.append(val)

            if not insert_cols:
                if self.logger:
                    self.logger.error('لا توجد أعمدة صالحة للإدراج في جدول المنتجات')
                return None

            placeholders = ','.join(['?'] * len(insert_cols))
            query = f"INSERT INTO products ({', '.join(insert_cols)}) VALUES ({placeholders})"
            result = self.db_manager.execute_query(query, tuple(insert_vals))
            try:
                product_id = self.db_manager.get_last_insert_id()
            except Exception:
                product_id = None
            if product_id:
                product.id = product_id
                
                # إضافة المتغيرات
                for variant in product.variants:
                    variant.product_id = product_id
                    self.variant_manager.create_variant(variant)
                
                # إضافة عناصر الحزمة
                for bundle_item in product.bundle_items:
                    bundle_item.bundle_id = product_id
                    self.bundle_manager.add_product_to_bundle(bundle_item)
                
                # إضافة مستويات التسعير
                for tier in product.pricing_tiers:
                    tier.product_id = product_id
                    self._create_pricing_tier(tier)
                
                # إضافة العلامات
                for label in product.labels:
                    label.product_id = product_id
                    self.label_manager.add_label_to_product(label)
                
                if self.logger:
                    self.logger.info(f"تم إنشاء منتج جديد: {product.name} - SKU: {product.sku}")
                
                return product_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء المنتج: {str(e)}")
        
        return None
    
    def get_product_by_id(self, product_id: int, include_related: bool = True) -> Optional[Product]:
        """الحصول على منتج بالمعرف"""
        try:
            query = """
            SELECT id, name, name_en, sku, barcode, category_id, supplier_id,
                   product_type, description, specifications, unit,
                   cost_price, base_price, pricing_policy,
                   current_stock, reserved_stock, min_stock, reorder_point, max_stock,
                   image_path, images, tags,
                   is_active, is_discontinued, is_featured,
                   created_at, updated_at, discontinued_date,
                   sales_count, total_sold, average_rating
            FROM products
            WHERE id = ? AND is_active = 1
            """
            
            row = self.db_manager.fetch_one(query, (product_id,))
            if not row:
                return None
            
            product = self._row_to_product(row)
            
            if include_related:
                # تحميل البيانات المرتبطة
                product.variants = self.variant_manager.get_variants_by_product(product_id)
                product.labels = self._get_product_labels(product_id)
                product.pricing_tiers = self._get_pricing_tiers(product_id)
                product.bundle_items = self._get_bundle_items(product_id)
            
            return product
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المنتج {product_id}: {str(e)}")
            return None
    
    def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """الحصول على منتج بـ SKU"""
        try:
            query = """
            SELECT id FROM products
            WHERE sku = ? AND is_active = 1
            LIMIT 1
            """
            
            row = self.db_manager.fetch_one(query, (sku,))
            if row:
                return self.get_product_by_id(row[0])
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المنتج بـ SKU {sku}: {str(e)}")
        
        return None
    
    def get_product_by_barcode(self, barcode: str) -> Optional[Product]:
        """الحصول على منتج برمز شريطي"""
        try:
            query = """
            SELECT id FROM products
            WHERE barcode = ? AND is_active = 1
            LIMIT 1
            """
            
            row = self.db_manager.fetch_one(query, (barcode,))
            if row:
                return self.get_product_by_id(row[0])
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المنتج برمز {barcode}: {str(e)}")
        
        return None
    
    def update_product(self, product: Product) -> bool:
        """تحديث بيانات المنتج"""
        try:
            query = """
            UPDATE products SET
                name = ?, name_en = ?, barcode = ?, category_id = ?, supplier_id = ?,
                product_type = ?, description = ?, specifications = ?, unit = ?,
                cost_price = ?, base_price = ?, pricing_policy = ?,
                current_stock = ?, reserved_stock = ?, min_stock = ?, reorder_point = ?, max_stock = ?,
                image_path = ?, images = ?, tags = ?,
                is_active = ?, is_discontinued = ?, is_featured = ?,
                updated_at = ?
            WHERE id = ?
            """
            
            params = (
                product.name, product.name_en, product.barcode, product.category_id,
                product.supplier_id, product.product_type, product.description,
                json.dumps(product.specifications, ensure_ascii=False),
                product.unit, float(product.cost_price), float(product.base_price),
                product.pricing_policy, product.current_stock, product.reserved_stock,
                product.min_stock, product.reorder_point, product.max_stock,
                product.image_path, json.dumps(product.images),
                json.dumps(product.tags),
                product.is_active, product.is_discontinued, product.is_featured,
                datetime.now(), product.id
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم تحديث المنتج: {product.name}")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث المنتج {product.id}: {str(e)}")
        
        return False
    
    def delete_product(self, product_id: int, soft_delete: bool = True) -> bool:
        """حذف منتج"""
        try:
            if soft_delete:
                # حذف ناعم - تعطيل المنتج فقط
                query = "UPDATE products SET is_active = 0, updated_at = ? WHERE id = ?"
                params = (datetime.now(), product_id)
            else:
                # حذف صلب - حذف نهائي
                query = "DELETE FROM products WHERE id = ?"
                params = (product_id,)
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم حذف المنتج ID: {product_id}")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف المنتج {product_id}: {str(e)}")
        
        return False
    
    # ==================== عمليات البحث والتصفية ====================
    
    def search_products(self, search_term: str = "", category_id: Optional[int] = None, active_only: bool = True) -> List[Product]:
        """البحث عن المنتجات"""
        try:
            # الحصول على الأعمدة المتاحة فقط
            cols_info = self.db_manager.fetch_all("PRAGMA table_info(products)")
            available_cols = {row[1] for row in cols_info} if cols_info else set()
            
            # اختيار الأعمدة الموجودة فقط من الجدول
            all_cols_to_check = ['id', 'name', 'name_en', 'sku', 'barcode', 'category_id', 'supplier_id',
                       'product_type', 'description', 'specifications', 'unit',
                       'cost_price', 'base_price', 'selling_price', 'pricing_policy',
                       'current_stock', 'reserved_stock', 'min_stock', 'reorder_point', 'max_stock',
                       'image_path', 'images', 'tags',
                       'is_active', 'is_discontinued', 'is_featured',
                       'created_at', 'updated_at', 'discontinued_date',
                       'sales_count', 'total_sold', 'average_rating']
            
            select_cols = [col for col in all_cols_to_check if col in available_cols]
            
            query = f"""
            SELECT {', '.join(select_cols)}
            FROM products
            WHERE 1=1
            """
            
            params = []
            
            if search_term:
                # Search only in available columns
                search_cols = []
                for col in ['name', 'name_en', 'sku', 'barcode', 'description']:
                    if col in available_cols:
                        search_cols.append(f"{col} LIKE ?")
                
                if search_cols:
                    query += " AND (" + " OR ".join(search_cols) + ")"
                    params.extend([f"%{search_term}%"] * len(search_cols))
            
            if active_only:
                query += " AND is_active = 1"
            
            if category_id:
                query += " AND category_id = ?"
                params.append(category_id)
            
            query += " ORDER BY name"
            
            results = self.db_manager.fetch_all(query, params)
            return [self._row_to_product(row, select_cols) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث عن المنتجات: {str(e)}")
            return []
    
    def get_low_stock_products(self, category_id: Optional[int] = None) -> List[Product]:
        """الحصول على المنتجات ذات المخزون المنخفض"""
        try:
            # Get available columns
            cols_info = self.db_manager.fetch_all("PRAGMA table_info(products)")
            available_cols = {row[1] for row in cols_info} if cols_info else set()
            
            all_cols_to_check = ['id', 'name', 'name_en', 'sku', 'barcode', 'category_id', 'supplier_id',
                       'product_type', 'description', 'specifications', 'unit',
                       'cost_price', 'selling_price', 'pricing_policy',
                       'current_stock', 'reserved_stock', 'min_stock', 'reorder_point', 'max_stock',
                       'image_path', 'images', 'tags',
                       'is_active', 'is_discontinued', 'is_featured',
                       'created_at', 'updated_at', 'discontinued_date',
                       'sales_count', 'total_sold', 'average_rating']
            
            select_cols = [col for col in all_cols_to_check if col in available_cols]
            
            # Build WHERE clause safely - only use reserved_stock if it exists
            where_clause = "WHERE is_active = 1 AND is_discontinued = 0"
            if 'reserved_stock' in available_cols:
                where_clause += " AND (current_stock - reserved_stock) <= min_stock"
            else:
                where_clause += " AND current_stock <= min_stock"
            
            query = f"""
            SELECT {', '.join(select_cols)}
            FROM products
            {where_clause}
            """
            
            params = []
            if category_id:
                query += " AND category_id = ?"
                params.append(category_id)
            
            if 'reserved_stock' in available_cols:
                query += " ORDER BY (current_stock - reserved_stock)"
            else:
                query += " ORDER BY current_stock"
            
            results = self.db_manager.fetch_all(query, params)
            return [self._row_to_product(row, select_cols) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المنتجات منخفضة المخزون: {str(e)}")
            return []
    
    def get_products_requiring_reorder(self) -> List[Product]:
        """الحصول على المنتجات التي تحتاج إلى إعادة طلب"""
        try:
            query = """
            SELECT id, name, name_en, sku, barcode, category_id, supplier_id,
                   product_type, description, specifications, unit,
                   cost_price, base_price, pricing_policy,
                   current_stock, reserved_stock, min_stock, reorder_point, max_stock,
                   image_path, images, tags,
                   is_active, is_discontinued, is_featured,
                   created_at, updated_at, discontinued_date,
                   sales_count, total_sold, average_rating
            FROM products
            WHERE (current_stock - reserved_stock) <= reorder_point
                  AND is_active = 1 AND is_discontinued = 0
            ORDER BY (current_stock - reserved_stock), reorder_point DESC
            """
            
            results = self.db_manager.fetch_all(query)
            return [self._row_to_product(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المنتجات المحتاجة لإعادة الطلب: {str(e)}")
            return []
    
    def get_featured_products(self, limit: int = 10) -> List[Product]:
        """الحصول على المنتجات المميزة"""
        try:
            query = """
            SELECT id, name, name_en, sku, barcode, category_id, supplier_id,
                   product_type, description, specifications, unit,
                   cost_price, base_price, pricing_policy,
                   current_stock, reserved_stock, min_stock, reorder_point, max_stock,
                   image_path, images, tags,
                   is_active, is_discontinued, is_featured,
                   created_at, updated_at, discontinued_date,
                   sales_count, total_sold, average_rating
            FROM products
            WHERE is_featured = 1 AND is_active = 1
            ORDER BY created_at DESC
            LIMIT ?
            """
            
            results = self.db_manager.fetch_all(query, (limit,))
            return [self._row_to_product(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المنتجات المميزة: {str(e)}")
            return []
    
    # ==================== عمليات التسعير ====================
    
    def calculate_product_price(self, product_id: int, quantity: int = 1, customer_type: Optional[str] = None) -> Optional[Decimal]:
        """حساب السعر مع الخصومات"""
        try:
            product = self.get_product_by_id(product_id, include_related=True)
            if not product:
                return None
            
            return product.get_price_for_quantity(quantity)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب سعر المنتج: {str(e)}")
            return None
    
    def _create_pricing_tier(self, tier: PricingTier) -> Optional[int]:
        """إنشاء مستوى تسعير"""
        try:
            query = """
            INSERT INTO pricing_tiers (
                product_id, min_quantity, max_quantity, price, discount_percent,
                valid_from, valid_until, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                tier.product_id, tier.min_quantity, tier.max_quantity,
                float(tier.price), float(tier.discount_percent),
                tier.valid_from, tier.valid_until, tier.description
            )
            
            result = self.db_manager.execute_query(query, params)
            try:
                return self.db_manager.get_last_insert_id()
            except Exception:
                return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء مستوى التسعير: {str(e)}")
        
        return None
    
    def _get_pricing_tiers(self, product_id: int) -> List[PricingTier]:
        """الحصول على مستويات التسعير للمنتج"""
        try:
            query = """
            SELECT id, product_id, min_quantity, max_quantity, price, discount_percent,
                   valid_from, valid_until, description
            FROM pricing_tiers
            WHERE product_id = ?
            ORDER BY min_quantity
            """
            
            results = self.db_manager.fetch_all(query, (product_id,))
            tiers = []
            for row in results:
                tier = PricingTier(
                    id=row[0],
                    product_id=row[1],
                    min_quantity=row[2],
                    max_quantity=row[3],
                    price=Decimal(str(row[4])),
                    discount_percent=Decimal(str(row[5])),
                    valid_from=datetime.fromisoformat(row[6]) if row[6] else None,
                    valid_until=datetime.fromisoformat(row[7]) if row[7] else None,
                    description=row[8]
                )
                tiers.append(tier)
            
            return tiers
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على مستويات التسعير: {str(e)}")
            return []
    
    # ==================== عمليات العلامات ====================
    
    def _get_product_labels(self, product_id: int) -> List[ProductLabel]:
        """الحصول على علامات المنتج"""
        try:
            query = """
            SELECT id, product_id, label_type, label_text, label_color, priority,
                   start_date, end_date, is_active
            FROM product_labels
            WHERE product_id = ?
            ORDER BY priority DESC
            """
            
            results = self.db_manager.fetch_all(query, (product_id,))
            labels = []
            for row in results:
                label = ProductLabel(
                    id=row[0],
                    product_id=row[1],
                    label_type=row[2],
                    label_text=row[3],
                    label_color=row[4],
                    priority=row[5],
                    start_date=datetime.fromisoformat(row[6]) if row[6] else None,
                    end_date=datetime.fromisoformat(row[7]) if row[7] else None,
                    is_active=bool(row[8])
                )
                labels.append(label)
            
            return labels
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على علامات المنتج: {str(e)}")
            return []
    
    # ==================== عمليات الحزم ====================
    
    def _get_bundle_items(self, bundle_id: int) -> List[BundleProduct]:
        """الحصول على عناصر الحزمة"""
        try:
            query = """
            SELECT id, bundle_id, product_id, product_name, quantity, unit_price
            FROM bundle_products
            WHERE bundle_id = ?
            ORDER BY product_id
            """
            
            results = self.db_manager.fetch_all(query, (bundle_id,))
            items = []
            for row in results:
                item = BundleProduct(
                    id=row[0],
                    bundle_id=row[1],
                    product_id=row[2],
                    product_name=row[3],
                    quantity=row[4],
                    unit_price=Decimal(str(row[5]))
                )
                items.append(item)
            
            return items
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على عناصر الحزمة: {str(e)}")
            return []
    
    def calculate_bundle_price(self, bundle_id: int) -> Decimal:
        """حساب سعر الحزمة الإجمالي"""
        try:
            bundle_items = self._get_bundle_items(bundle_id)
            total_price = Decimal('0.00')
            
            for item in bundle_items:
                total_price += item.total_price
            
            return total_price
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب سعر الحزمة: {str(e)}")
            return Decimal('0.00')
    
    # ==================== عمليات إحصائية ====================
    
    def get_inventory_value(self) -> Dict[str, Decimal]:
        """حساب قيمة المخزون الإجمالي"""
        try:
            query = """
            SELECT 
                SUM(current_stock * cost_price) as total_cost_value,
                SUM((current_stock - reserved_stock) * base_price) as total_selling_value,
                COUNT(*) as total_products
            FROM products
            WHERE is_active = 1
            """
            
            result = self.db_manager.fetch_one(query)
            if result:
                return {
                    'total_cost_value': Decimal(str(result[0] or 0)),
                    'total_selling_value': Decimal(str(result[1] or 0)),
                    'total_products': result[2] or 0,
                    'potential_profit': Decimal(str(result[1] or 0)) - Decimal(str(result[0] or 0))
                }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب قيمة المخزون: {str(e)}")
        
        return {
            'total_cost_value': Decimal('0.00'),
            'total_selling_value': Decimal('0.00'),
            'total_products': 0,
            'potential_profit': Decimal('0.00')
        }
    
    def get_products_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المنتجات"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_products,
                COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_products,
                COUNT(CASE WHEN is_discontinued = 1 THEN 1 END) as discontinued_products,
                COUNT(CASE WHEN (current_stock - reserved_stock) <= min_stock THEN 1 END) as low_stock_count,
                AVG(CAST(current_stock as REAL)) as avg_stock,
                MIN(current_stock) as min_stock_qty,
                MAX(current_stock) as max_stock_qty
            FROM products
            """
            
            result = self.db_manager.fetch_one(query)
            if result:
                return {
                    'total_products': result[0] or 0,
                    'active_products': result[1] or 0,
                    'discontinued_products': result[2] or 0,
                    'low_stock_count': result[3] or 0,
                    'avg_stock': int(result[4] or 0),
                    'min_stock_qty': result[5] or 0,
                    'max_stock_qty': result[6] or 0
                }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على إحصائيات المنتجات: {str(e)}")
        
        return {}
    
    # ==================== الطرق المساعدة ====================
    
    def _row_to_product(self, row, col_names=None) -> Product:
        """تحويل صف قاعدة البيانات إلى كائن منتج"""
        # إذا لم يتم توفير أسماء الأعمدة، افترض الترتيب الافتراضي
        if col_names is None:
            col_names = ['id', 'name', 'name_en', 'sku', 'barcode', 'category_id', 'supplier_id',
                        'product_type', 'description', 'specifications', 'unit',
                        'cost_price', 'base_price', 'pricing_policy',
                        'current_stock', 'reserved_stock', 'min_stock', 'reorder_point', 'max_stock',
                        'image_path', 'images', 'tags',
                        'is_active', 'is_discontinued', 'is_featured',
                        'created_at', 'updated_at', 'discontinued_date',
                        'sales_count', 'total_sold', 'average_rating']
        
        # بناء قاموس من أسماء الأعمدة والقيم
        data = dict(zip(col_names, row))
        
        # محاولة الحصول على كل قيمة مع قيمة افتراضية
        def get_value(key, default=None):
            return data.get(key, default)
        
        # تحويل JSON strings
        specs = get_value('specifications')
        specs = json.loads(specs) if specs and isinstance(specs, str) else {}
        
        images = get_value('images')
        images = json.loads(images) if images and isinstance(images, str) else []
        
        tags = get_value('tags')
        tags = json.loads(tags) if tags and isinstance(tags, str) else []
        
        # تحويل التواريخ
        def parse_date(date_str):
            if date_str and isinstance(date_str, str):
                try:
                    return datetime.fromisoformat(date_str)
                except:
                    return None
            return None
        
        # Handle base_price/selling_price mapping for schema compatibility
        base_price_val = get_value('base_price')
        if base_price_val is None:
            base_price_val = get_value('selling_price')  # fallback to selling_price from DB schema
        
        return Product(
            id=get_value('id'),
            name=get_value('name'),
            name_en=get_value('name_en'),
            sku=get_value('sku'),
            barcode=get_value('barcode'),
            category_id=get_value('category_id'),
            supplier_id=get_value('supplier_id'),
            product_type=get_value('product_type'),
            description=get_value('description'),
            specifications=specs,
            unit=get_value('unit'),
            cost_price=Decimal(str(get_value('cost_price', 0))) if get_value('cost_price') is not None else Decimal('0'),
            base_price=Decimal(str(base_price_val)) if base_price_val is not None else Decimal('0'),
            pricing_policy=get_value('pricing_policy'),
            current_stock=get_value('current_stock', 0) or 0,
            reserved_stock=get_value('reserved_stock', 0) or 0,
            min_stock=get_value('min_stock', 0) or 0,
            reorder_point=get_value('reorder_point', 0) or 0,
            max_stock=get_value('max_stock', 0) or 0,
            image_path=get_value('image_path'),
            images=images,
            tags=tags,
            is_active=bool(get_value('is_active', 1)),
            is_discontinued=bool(get_value('is_discontinued', 0)),
            is_featured=bool(get_value('is_featured', 0)),
            created_at=parse_date(get_value('created_at')),
            updated_at=parse_date(get_value('updated_at')),
            discontinued_date=parse_date(get_value('discontinued_date')),
            sales_count=get_value('sales_count', 0) or 0,
            total_sold=get_value('total_sold', 0) or 0,
            average_rating=Decimal(str(get_value('average_rating', 0))) if get_value('average_rating') is not None else Decimal('0')
        )
    
    def _generate_sku(self) -> str:
        """توليد SKU فريد"""
        import time
        return f"SKU-{int(time.time() * 1000)}"
