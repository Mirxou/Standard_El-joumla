#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج المنتج المحسّن - Enhanced Product Model
يحتوي على جميع العمليات المتعلقة بالمنتجات مع ميزات متقدمة
تم الدمج مع: Standard (الذكاء الاصطناعي والصلاحية) و GIMS (الموردين والمالية)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal
from enum import Enum
import sys
from pathlib import Path
import json


# ==================== التعريفات والثوابت ====================

class ProductType(Enum):
    """أنواع المنتجات"""
    SIMPLE = "بسيط"  # منتج بسيط
    VARIABLE = "متغير"  # منتج مع متغيرات (حجم، لون، إلخ)
    BUNDLE = "حزمة"  # منتج مركب (مجموعة منتجات)
    DIGITAL = "رقمي"  # منتج رقمي

class PricingPolicy(Enum):
    """سياسات التسعير"""
    STANDARD = "معياري"  # سعر موحد
    TIERED = "متدرج"  # أسعار حسب الكمية
    CUSTOMER_BASED = "عملاء"  # أسعار حسب نوع العميل
    TIME_BASED = "فترات"  # أسعار حسب الفترات الزمنية

class UnitType(Enum):
    """وحدات القياس"""
    PIECE = "قطعة"
    KG = "كيلوجرام"
    LITER = "لتر"
    METER = "متر"
    BOX = "صندوق"
    DOZEN = "دستة"
    GRAM = "جرام"
    MILLILITER = "ميلليتر"

# ==================== نماذج البيانات المساعدة ====================

@dataclass
class ProductVariant:
    """متغير المنتج - للمنتجات ذات الخصائص المختلفة"""
    id: Optional[int] = None
    product_id: Optional[int] = None
    sku: str = ""  # Stock Keeping Unit - معرف فريد للمتغير
    attributes: Dict[str, str] = field(default_factory=dict)
    cost_price: Decimal = Decimal('0.00')
    selling_price: Decimal = Decimal('0.00')
    stock_quantity: int = 0
    barcode: Optional[str] = None
    image_path: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if isinstance(self.cost_price, (int, float, str)):
            self.cost_price = Decimal(str(self.cost_price))
        if isinstance(self.selling_price, (int, float, str)):
            self.selling_price = Decimal(str(self.selling_price))
    
    @property
    def profit_margin(self) -> Decimal:
        if self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return Decimal('0.00')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'product_id': self.product_id,
            'sku': self.sku,
            'attributes': self.attributes,
            'cost_price': float(self.cost_price),
            'selling_price': float(self.selling_price),
            'stock_quantity': self.stock_quantity,
            'barcode': self.barcode,
            'image_path': self.image_path,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'profit_margin': float(self.profit_margin),
            'attributes_display': self._attributes_display()
        }
    
    def _attributes_display(self) -> str:
        if not self.attributes:
            return ""
        return " | ".join([f"{k}: {v}" for k, v in self.attributes.items()])

@dataclass
class BundleProduct:
    """منتج في حزمة"""
    id: Optional[int] = None
    bundle_id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""
    quantity: int = 1
    unit_price: Decimal = Decimal('0.00')
    
    def __post_init__(self):
        if isinstance(self.unit_price, (int, float, str)):
            self.unit_price = Decimal(str(self.unit_price))
    
    @property
    def total_price(self) -> Decimal:
        return self.unit_price * self.quantity
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'bundle_id': self.bundle_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price)
        }

@dataclass
class PricingTier:
    """مستوى التسعير المتدرج"""
    id: Optional[int] = None
    product_id: Optional[int] = None
    min_quantity: int = 0
    max_quantity: Optional[int] = None
    price: Decimal = Decimal('0.00')
    discount_percent: Decimal = Decimal('0.00')
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.price, (int, float, str)):
            self.price = Decimal(str(self.price))
        if isinstance(self.discount_percent, (int, float, str)):
            self.discount_percent = Decimal(str(self.discount_percent))
    
    def is_valid(self, quantity: int) -> bool:
        now = datetime.now()
        if quantity < self.min_quantity: return False
        if self.max_quantity and quantity > self.max_quantity: return False
        if self.valid_from and now < self.valid_from: return False
        if self.valid_until and now > self.valid_until: return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'product_id': self.product_id,
            'min_quantity': self.min_quantity,
            'max_quantity': self.max_quantity,
            'price': float(self.price),
            'discount_percent': float(self.discount_percent),
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'description': self.description
        }

@dataclass
class ProductLabel:
    """علامة رقمية للمنتج"""
    id: Optional[int] = None
    product_id: Optional[int] = None
    label_type: str = ""
    label_text: str = ""
    label_color: str = "#FF5733"
    priority: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    
    def is_current(self) -> bool:
        now = datetime.now()
        if self.start_date and now < self.start_date: return False
        if self.end_date and now > self.end_date: return False
        return self.is_active
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'product_id': self.product_id,
            'label_type': self.label_type,
            'label_text': self.label_text,
            'label_color': self.label_color,
            'priority': self.priority,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active
        }

# ==================== النموذج الرئيسي (المعدل) ====================

@dataclass
class Product:
    """
    نموذج بيانات المنتج المحسّن
    تم دمج حقول Standard (الذكاء الاصطناعي، الصلاحية) و GIMS (الموردين)
    """
    # --- الهوية الأساسية ---
    id: Optional[int] = None
    name: str = ""
    name_en: Optional[str] = None
    sku: str = ""
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    
    # --- بيانات الموردين (من GIMS) ---
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    
    # --- الخصائص ---
    product_type: str = ProductType.SIMPLE.value
    description: Optional[str] = None
    specifications: Dict[str, str] = field(default_factory=dict)
    unit: str = UnitType.PIECE.value
    
    # --- التسعير والمالية (مدمج) ---
    cost_price: Decimal = Decimal('0.00')
    base_price: Decimal = Decimal('0.00')      # سعر البيع
    wholesale_price: Decimal = Decimal('0.00') # سعر الجملة (جديد)
    tax_rate: Decimal = Decimal('0.00')        # الضريبة (جديد)
    pricing_policy: str = PricingPolicy.STANDARD.value
    
    # --- المخزون ---
    current_stock: int = 0
    reserved_stock: int = 0
    min_stock: int = 0
    reorder_point: int = 0
    max_stock: int = 0
    
    # --- التتبع والصلاحية (من Standard) ---
    is_perishable: bool = False             # قابل للتلف
    expiry_date: Optional[datetime] = None  # تاريخ الانتهاء
    batch_number: Optional[str] = None      # رقم التشغيلة
    production_date: Optional[datetime] = None
    
    # --- الذكاء الاصطناعي (من Standard AI) ---
    abc_classification: Optional[str] = None   # تصنيف الأهمية A/B/C
    ai_forecast_demand: Optional[float] = None # التنبؤ بالطلب
    last_analysis_date: Optional[datetime] = None
    
    # --- المظهر والوسائط ---
    image_path: Optional[str] = None
    images: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # --- الحالة ---
    is_active: bool = True
    is_discontinued: bool = False
    is_featured: bool = False
    
    # --- التواريخ ---
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    discontinued_date: Optional[datetime] = None
    
    # --- العلاقات ---
    variants: List[ProductVariant] = field(default_factory=list)
    bundle_items: List[BundleProduct] = field(default_factory=list)
    pricing_tiers: List[PricingTier] = field(default_factory=list)
    labels: List[ProductLabel] = field(default_factory=list)
    
    # --- إحصائيات ---
    sales_count: int = 0
    total_sold: int = 0
    average_rating: Decimal = Decimal('0.00')
    
    def __post_init__(self):
        """تحويل القيم المالية والرقمية"""
        for field_name in ['cost_price', 'base_price', 'wholesale_price', 'tax_rate', 'average_rating']:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
    
    @property
    def available_stock(self) -> int:
        return max(0, self.current_stock - self.reserved_stock)
    
    @property
    def stock_quantity(self) -> int:
        return self.current_stock
    
    @property
    def selling_price(self) -> Decimal:
        return self.base_price
    
    @selling_price.setter
    def selling_price(self, value: Decimal) -> None:
        if isinstance(value, (int, float, str)):
            self.base_price = Decimal(str(value))
        else:
            self.base_price = value
    
    @property
    def is_low_stock(self) -> bool:
        return self.current_stock <= self.min_stock
    
    @property
    def requires_reorder(self) -> bool:
        # إذا كان هناك تنبؤ ذكي والطلب المتوقع أعلى من المخزون، نطلب إعادة الشراء
        if self.ai_forecast_demand and self.ai_forecast_demand > self.current_stock:
            return True
        return self.available_stock <= self.reorder_point
    
    @property
    def profit_margin(self) -> Decimal:
        if self.cost_price > 0:
            return ((self.base_price - self.cost_price) / self.cost_price) * 100
        return Decimal('0.00')
    
    @property
    def profit_amount(self) -> Decimal:
        return self.base_price - self.cost_price
    
    @property
    def stock_value(self) -> Decimal:
        return self.cost_price * self.current_stock
    
    @property
    def active_labels(self) -> List[ProductLabel]:
        return [label for label in self.labels if label.is_current()]
    
    def get_price_for_quantity(self, quantity: int) -> Decimal:
        if self.pricing_policy == PricingPolicy.TIERED.value:
            for tier in sorted(self.pricing_tiers, key=lambda t: t.min_quantity, reverse=True):
                if tier.is_valid(quantity):
                    if tier.discount_percent > 0:
                        return self.base_price * (1 - tier.discount_percent / 100)
                    else:
                        return tier.price
        return self.base_price
    
    def add_variant(self, variant: ProductVariant) -> None:
        variant.product_id = self.id
        self.variants.append(variant)
    
    def add_bundle_item(self, item: BundleProduct) -> None:
        item.bundle_id = self.id
        self.bundle_items.append(item)
    
    def add_label(self, label: ProductLabel) -> None:
        label.product_id = self.id
        self.labels.append(label)
    
    def to_dict(self, include_related: bool = True) -> Dict[str, Any]:
        """تحويل إلى قاموس (محدث)"""
        data = {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en,
            'sku': self.sku,
            'barcode': self.barcode,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'product_type': self.product_type,
            'description': self.description,
            'specifications': self.specifications,
            'unit': self.unit,
            # المالية
            'cost_price': float(self.cost_price),
            'base_price': float(self.base_price),
            'wholesale_price': float(self.wholesale_price),
            'tax_rate': float(self.tax_rate),
            'pricing_policy': self.pricing_policy,
            # المخزون
            'current_stock': self.current_stock,
            'reserved_stock': self.reserved_stock,
            'available_stock': self.available_stock,
            'min_stock': self.min_stock,
            'reorder_point': self.reorder_point,
            'max_stock': self.max_stock,
            # التتبع والذكاء (الجديد)
            'is_perishable': self.is_perishable,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'batch_number': self.batch_number,
            'ai_forecast_demand': self.ai_forecast_demand,
            'abc_classification': self.abc_classification,
            # البيانات العامة
            'image_path': self.image_path,
            'images': self.images,
            'tags': self.tags,
            'is_active': self.is_active,
            'is_discontinued': self.is_discontinued,
            'is_featured': self.is_featured,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'discontinued_date': self.discontinued_date.isoformat() if self.discontinued_date else None,
            # الإحصائيات
            'sales_count': self.sales_count,
            'total_sold': self.total_sold,
            'average_rating': float(self.average_rating),
            'profit_margin': float(self.profit_margin),
            'profit_amount': float(self.profit_amount),
            'stock_value': float(self.stock_value),
            'is_low_stock': self.is_low_stock,
            'requires_reorder': self.requires_reorder,
            'active_labels': [label.to_dict() for label in self.active_labels]
        }
        
        if include_related:
            data.update({
                'variants': [v.to_dict() for v in self.variants],
                'bundle_items': [b.to_dict() for b in self.bundle_items],
                'pricing_tiers': [t.to_dict() for t in self.pricing_tiers],
                'labels': [l.to_dict() for l in self.labels]
            })
        
        return data

# ==================== مديرو البيانات (كما هم بدون تغيير) ====================

class ProductVariantManager:
    """مدير متغيرات المنتجات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
    
    def create_variant(self, variant: ProductVariant) -> Optional[int]:
        """إنشاء متغير منتج جديد"""
        try:
            query = """
            INSERT INTO product_variants (
                product_id, sku, attributes, cost_price, selling_price,
                stock_quantity, barcode, image_path, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            now = datetime.now()
            params = (
                variant.product_id,
                variant.sku,
                json.dumps(variant.attributes, ensure_ascii=False),
                float(variant.cost_price),
                float(variant.selling_price),
                variant.stock_quantity,
                variant.barcode,
                variant.image_path,
                variant.is_active,
                now,
                now
            )
            
            result = self.db_manager.execute_query(query, params)
            try:
                variant_id = self.db_manager.get_last_insert_id()
                if variant_id and self.logger:
                    self.logger.info(f"تم إنشاء متغير منتج جديد - SKU: {variant.sku} (ID: {variant_id})")
                return variant_id
            except Exception:
                return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء متغير المنتج: {str(e)}")
        
        return None
    
    def get_variants_by_product(self, product_id: int) -> List[ProductVariant]:
        """الحصول على جميع متغيرات منتج معين"""
        try:
            query = """
            SELECT id, product_id, sku, attributes, cost_price, selling_price,
                   stock_quantity, barcode, image_path, is_active, created_at, updated_at
            FROM product_variants
            WHERE product_id = ? AND is_active = 1
            ORDER BY created_at
            """
            
            results = self.db_manager.fetch_all(query, (product_id,))
            variants = []
            for row in results:
                variant = ProductVariant(
                    id=row[0],
                    product_id=row[1],
                    sku=row[2],
                    attributes=json.loads(row[3]) if row[3] else {},
                    cost_price=Decimal(str(row[4])),
                    selling_price=Decimal(str(row[5])),
                    stock_quantity=row[6],
                    barcode=row[7],
                    image_path=row[8],
                    is_active=bool(row[9]),
                    created_at=datetime.fromisoformat(row[10]) if row[10] else None,
                    updated_at=datetime.fromisoformat(row[11]) if row[11] else None
                )
                variants.append(variant)
            
            return variants
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على متغيرات المنتج {product_id}: {str(e)}")
            return []

class BundleProductManager:
    """مدير حزم المنتجات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
    
    def add_product_to_bundle(self, bundle_item: BundleProduct) -> Optional[int]:
        """إضافة منتج إلى حزمة"""
        try:
            query = """
            INSERT INTO bundle_products (
                bundle_id, product_id, product_name, quantity, unit_price
            ) VALUES (?, ?, ?, ?, ?)
            """
            
            params = (
                bundle_item.bundle_id,
                bundle_item.product_id,
                bundle_item.product_name,
                bundle_item.quantity,
                float(bundle_item.unit_price)
            )
            
            result = self.db_manager.execute_query(query, params)
            try:
                item_id = self.db_manager.get_last_insert_id()
                if item_id and self.logger:
                    self.logger.info(f"تم إضافة منتج إلى حزمة - ID: {item_id}")
                return item_id
            except Exception:
                return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة منتج إلى الحزمة: {str(e)}")
        
        return None

class ProductLabelManager:
    """مدير علامات المنتجات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
    
    def add_label_to_product(self, label: ProductLabel) -> Optional[int]:
        """إضافة علامة للمنتج"""
        try:
            query = """
            INSERT INTO product_labels (
                product_id, label_type, label_text, label_color, priority,
                start_date, end_date, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                label.product_id,
                label.label_type,
                label.label_text,
                label.label_color,
                label.priority,
                label.start_date,
                label.end_date,
                label.is_active
            )
            
            result = self.db_manager.execute_query(query, params)
            try:
                label_id = self.db_manager.get_last_insert_id()
                if label_id and self.logger:
                    self.logger.info(f"تم إضافة علامة للمنتج - ID: {label_id}")
                return label_id
            except Exception:
                return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة علامة للمنتج: {str(e)}")
        
        return None