#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة المبيعات - Sales Service
تحتوي على جميع العمليات المتعلقة بالمبيعات ونقاط البيع
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from decimal import Decimal
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.sale import Sale, SaleItem, SaleManager, SaleStatus, PaymentMethod
from src.models.product import Product, ProductManager
from src.models.customer import Customer, CustomerManager
from src.services.exchange_rate_service import ExchangeRateService
from src.services.workflow_service import WorkflowService
from src.services.inventory_service import InventoryService
from src.services.accounting_service import AccountingService

@dataclass
class SalesReport:
    """تقرير المبيعات"""
    total_sales: int
    total_revenue: float
    total_profit: float
    average_sale_value: float
    top_products: List[Dict[str, Any]]
    top_customers: List[Dict[str, Any]]
    sales_by_day: List[Dict[str, Any]]
    sales_by_payment_method: List[Dict[str, Any]]
    period_start: date
    period_end: date

@dataclass
class DailySummary:
    """ملخص يومي للمبيعات"""
    date: date
    total_sales: int
    total_revenue: float
    total_profit: float
    cash_sales: float
    card_sales: float
    credit_sales: float
    returns: float
    net_sales: float

@dataclass
class POSSession:
    """جلسة نقطة البيع"""
    id: Optional[int] = None
    user_id: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    opening_cash: float = 0.0
    closing_cash: float = 0.0
    total_sales: float = 0.0
    total_returns: float = 0.0
    cash_in_drawer: float = 0.0
    is_active: bool = True

class SalesService:
    """خدمة المبيعات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        self.sale_manager = SaleManager(db_manager, logger)
        self.product_manager = ProductManager(db_manager, logger)
        self.customer_manager = CustomerManager(db_manager, logger)
        self.inventory_service = InventoryService(db_manager, logger)
        self.accounting_service = AccountingService(db_manager)
        self.exchange_rate_service = ExchangeRateService(db_manager, logger)
        self.current_session: Optional[POSSession] = None
        # Lazy loading لـ WorkflowService
        self._workflow_service = None
    
    @property
    def workflow_service(self):
        """Lazy loading لـ WorkflowService"""
        if self._workflow_service is None:
            try:
                self._workflow_service = WorkflowService(self.db_manager, self.logger)
            except ImportError:
                if self.logger:
                    self.logger.warning("WorkflowService غير متاح - Workflow Engine غير مفعل")
        return self._workflow_service
    
    # ===== إدارة المبيعات =====
    
    def create_sale(self, sale: Sale, user_id: Optional[int] = None) -> Optional[int]:
        """إنشاء فاتورة مبيعات جديدة"""
        try:
            # التحقق من توفر المنتجات
            for item in sale.items:
                product = self.product_manager.get_product_by_id(item.product_id)
                if not product:
                    if self.logger:
                        self.logger.warning(f"المنتج {item.product_id} غير موجود")
                    return None
                
                if product.current_stock < item.quantity:
                    if self.logger:
                        self.logger.warning(f"كمية غير كافية للمنتج {product.name}")
                    return None
            
            # Multi-Currency: حساب المبالغ بالعملة الأساسية
            if sale.currency_id:
                try:
                    # الحصول على العملة الأساسية
                    base_currency = self.exchange_rate_service.currency_manager.get_base_currency()
                    if base_currency:
                        # الحصول على سعر الصرف
                        exchange_rate = self.exchange_rate_service.get_exchange_rate(
                            sale.currency_id,
                            base_currency.id,
                            sale.sale_date
                        )
                        
                        if exchange_rate:
                            sale.exchange_rate = exchange_rate
                            # حساب المبلغ بالعملة الأساسية
                            sale.base_amount = sale.total_amount * exchange_rate
                            sale.converted_amount = sale.total_amount
                            
                            if self.logger:
                                self.logger.debug(
                                    f"تم حساب المبلغ بالعملة الأساسية: {sale.base_amount} "
                                    f"(سعر الصرف: {exchange_rate})"
                                )
                        else:
                            # إذا لم يوجد سعر صرف، استخدم المبلغ الأساسي
                            sale.base_amount = sale.total_amount
                            sale.converted_amount = sale.total_amount
                            sale.exchange_rate = Decimal('1.0')
                    else:
                        # إذا لم توجد عملة أساسية، استخدم المبلغ الأساسي
                        sale.base_amount = sale.total_amount
                        sale.converted_amount = sale.total_amount
                        sale.exchange_rate = Decimal('1.0')
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"خطأ في حساب سعر الصرف: {str(e)}")
                    # في حالة الخطأ، استخدم المبلغ الأساسي
                    sale.base_amount = sale.total_amount
                    sale.converted_amount = sale.total_amount
                    sale.exchange_rate = Decimal('1.0')
            else:
                # إذا لم تكن هناك عملة محددة، استخدم المبلغ الأساسي
                sale.base_amount = sale.total_amount
                sale.converted_amount = sale.total_amount
                sale.exchange_rate = Decimal('1.0')
            
            # إنشاء الفاتورة
            sale_id = self.sale_manager.create_sale(sale)
            if sale_id:
                try:
                    # --- بدء ربط الخدمات (Glue Code) ---
                    
                    # 1. تحديث المخزون
                    for item in sale.items:
                        self.inventory_service.adjust_stock(
                            product_id=item.product_id,
                            quantity_change=-item.quantity,
                            reason="sale",
                            reference_id=sale_id
                        )
                    
                    # 2. إنشاء قيد محاسبي
                    self.accounting_service.create_sale_journal_entry(sale)
                    
                    # 3. تحديث رصيد العميل
                    if sale.customer_id:
                        self.customer_manager.update_balance(sale.customer_id, sale.final_amount, "increase")

                    # 4. تحديث جلسة نقطة البيع
                    if self.current_session:
                        self._update_session_sales(sale.total_amount)
                        
                except Exception as e:
                    # Transaction Rollback Strategy
                    # في حالة حدوث أي خطأ بعد إنشاء الفاتورة، نقوم بحذف الفاتورة لضمان سلامة البيانات
                    if self.logger:
                        self.logger.error(f"فشل في معالجة ما بعد البيع، جاري التراجع: {e}")
                    self.sale_manager.delete_sale(sale_id)
                    return None

                # بدء سير العمل إذا كان متاحاً
                if self.workflow_service and user_id:
                    try:
                        # الحصول على company_id من Sale (إذا كان متوفراً)
                        company_id = getattr(sale, 'company_id', None)
                        
                        instance_id = self.workflow_service.start_workflow_for_entity(
                            entity_type="sale",
                            entity_id=sale_id,
                            initiated_by=user_id,
                            workflow_id=None,  # استخدام الافتراضي
                            company_id=company_id,
                            notes=f"فاتورة مبيعات: {sale.invoice_number}",
                            metadata={'invoice_number': sale.invoice_number, 'customer_id': sale.customer_id}
                        )
                        
                        if instance_id and self.logger:
                            self.logger.info(f"تم بدء سير العمل للفاتورة {sale_id} (instance: {instance_id})")
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"فشل بدء سير العمل للفاتورة {sale_id}: {e}")
                        # لا نوقف العملية إذا فشل بدء سير العمل
                
                if self.logger:
                    self.logger.info(f"تم إنشاء فاتورة مبيعات جديدة: {sale_id}")
            
            return sale_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء فاتورة المبيعات: {str(e)}")
            return None
    
    def add_sale_item(self, sale_id: int, product_id: int, quantity: float, 
                     unit_price: Optional[float] = None, discount: float = 0.0) -> bool:
        """إضافة منتج لفاتورة المبيعات"""
        try:
            # الحصول على المنتج
            product = self.product_manager.get_product_by_id(product_id)
            if not product:
                if self.logger:
                    self.logger.warning(f"المنتج {product_id} غير موجود")
                return False
            
            # التحقق من توفر الكمية
            if product.current_stock < quantity:
                if self.logger:
                    self.logger.warning(f"كمية غير كافية للمنتج {product.name}")
                return False
            
            # استخدام سعر البيع الافتراضي إذا لم يتم تحديد سعر
            if unit_price is None:
                unit_price = product.selling_price
            
            # إنشاء عنصر المبيعات
            sale_item = SaleItem(
                sale_id=sale_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount
            )
            
            # إضافة العنصر
            success = self.sale_manager.add_sale_item(sale_item)
            if success:
                # تحديث إجمالي الفاتورة
                self._update_sale_total(sale_id)
                
                if self.logger:
                    self.logger.info(f"تم إضافة منتج {product.name} للفاتورة {sale_id}")
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة منتج للفاتورة: {str(e)}")
            return False
    
    def remove_sale_item(self, sale_id: int, product_id: int) -> bool:
        """حذف منتج من فاتورة المبيعات"""
        try:
            success = self.sale_manager.remove_sale_item(sale_id, product_id)
            if success:
                # تحديث إجمالي الفاتورة
                self._update_sale_total(sale_id)
                
                if self.logger:
                    self.logger.info(f"تم حذف المنتج {product_id} من الفاتورة {sale_id}")
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف منتج من الفاتورة: {str(e)}")
            return False
    
    def complete_sale(self, sale_id: int, payment_method: str, 
                     amount_paid: float, user_id: Optional[int] = None) -> bool:
        """إتمام فاتورة المبيعات"""
        try:
            # الحصول على الفاتورة
            sale = self.sale_manager.get_sale_by_id(sale_id)
            if not sale:
                return False
            
            # التحقق من حالة الفاتورة
            if sale.status != SaleStatus.PENDING.value:
                if self.logger:
                    self.logger.warning(f"لا يمكن إتمام الفاتورة {sale_id} - الحالة: {sale.status}")
                return False
            
            # التحقق من المبلغ المدفوع
            if amount_paid < sale.total_amount:
                if self.logger:
                    self.logger.warning(f"المبلغ المدفوع أقل من إجمالي الفاتورة")
                return False
            
            # إتمام الفاتورة
            success = self.sale_manager.complete_sale(sale_id, payment_method, amount_paid)
            if success:
                # تحديث رصيد العميل إذا كان الدفع آجل
                if payment_method == PaymentMethod.CREDIT.value and sale.customer_id:
                    self.customer_manager.update_balance(
                        sale.customer_id, 
                        sale.total_amount, 
                        "increase"
                    )
                
                # تحديث جلسة نقطة البيع
                if self.current_session and payment_method == PaymentMethod.CASH.value:
                    self.current_session.cash_in_drawer += amount_paid
                
                if self.logger:
                    self.logger.info(f"تم إتمام فاتورة المبيعات {sale_id}")
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إتمام فاتورة المبيعات {sale_id}: {str(e)}")
            return False
    
    def cancel_sale(self, sale_id: int, reason: str = "", user_id: Optional[int] = None) -> bool:
        """إلغاء فاتورة المبيعات (Legacy - استخدام cancel_invoice بدلاً منها)"""
        return self.cancel_invoice(sale_id, reason, user_id)
    
    def cancel_invoice(self, sale_id: int, cancellation_reason: str = "", user_id: Optional[int] = None) -> bool:
        """
        إلغاء فاتورة مع استعادة المخزون وإرجاع المال - ACID Transaction (نسخة آمنة)
        
        الخوارزمية:
        1. التحقق المسبق: وجود الفاتورة وحالتها
        2. بدء Transaction (تلقائي في SQLite)
        3. استعادة المخزون من sale_items (مع فحص الأعمدة ديناميكياً)
        4. تعديل رصيد العميل (مع فحص الأعمدة)
        5. تحديث حالة الفاتورة (مع فحص الأعمدة)
        6. Commit أو Rollback
        
        Args:
            sale_id: معرف الفاتورة
            cancellation_reason: سبب الإلغاء
            user_id: معرف المستخدم الذي قام بالإلغاء
            
        Returns:
            bool: True إذا نجحت العملية، False إذا فشلت
        """
        connection = None
        cursor = None
        
        try:
            # ===== المرحلة 1: التحقق المسبق (Pre-Flight Checks) =====
            if self.logger:
                self.logger.info(f"🔍 بدء عملية إلغاء الفاتورة {sale_id}")
            
            # جلب الفاتورة
            sale = self.sale_manager.get_sale_by_id(sale_id)
            if not sale:
                if self.logger:
                    self.logger.error(f"❌ الفاتورة {sale_id} غير موجودة")
                return False
            
            # التحقق من حالة الفاتورة
            if sale.status == SaleStatus.CANCELLED.value:
                if self.logger:
                    self.logger.warning(f"⚠️ الفاتورة {sale_id} ملغاة مسبقاً")
                return False
            
            # ===== المرحلة 2: فتح "منطقة الأمان" (Begin Transaction) =====
            # الحصول على الاتصال الخام للتحكم في المعاملة
            connection = self.db_manager.connection
            if not connection and self.db_manager.pool:
                connection = self.db_manager.pool.get_connection()
            
            if not connection:
                if self.logger:
                    self.logger.error("❌ لا يوجد اتصال بقاعدة البيانات")
                return False
            
            cursor = connection.cursor()
            
            # ملاحظة: sqlite3 في بايثون يبدأ المعاملة ضمنياً عند أول أمر تعديل
            # لا نكتب cursor.execute("BEGIN") لتجنب الأخطاء
            
            # ===== المرحلة 3: حلقة استعادة المخزون (The Restock Loop) =====
            
            # 1. تحديد هيكل جدول العناصر ديناميكياً
            has_variant_col = False
            try:
                cursor.execute("PRAGMA table_info(sale_items)")
                item_cols = [row[1] for row in cursor.fetchall()]
                has_variant_col = 'variant_id' in item_cols
            except:
                pass
            
            # 2. بناء الاستعلام بناءً على الأعمدة الموجودة
            if has_variant_col:
                items_query = "SELECT product_id, variant_id, quantity FROM sale_items WHERE sale_id = ?"
            else:
                items_query = "SELECT product_id, quantity FROM sale_items WHERE sale_id = ?"
            
            cursor.execute(items_query, (sale_id,))
            sale_items = cursor.fetchall()
            
            if not sale_items:
                if self.logger:
                    self.logger.warning(f"⚠️ الفاتورة {sale_id} فارغة")
                # لا نوقف العملية، ربما هي فاتورة فارغة، نكمل لتغيير الحالة
            
            # 3. التحقق من أعمدة التحديث (updated_at) في الجداول الأخرى لتجنب الانهيار
            cursor.execute("PRAGMA table_info(products)")
            prod_cols = [row[1] for row in cursor.fetchall()]
            prod_has_updated = 'updated_at' in prod_cols
            
            try:
                cursor.execute("PRAGMA table_info(product_variants)")
                var_cols = [row[1] for row in cursor.fetchall()]
                var_has_updated = 'updated_at' in var_cols
            except:
                var_has_updated = False
            
            # 4. تنفيذ الاستعادة
            for item in sale_items:
                product_id = item[0]
                # استخراج البيانات بذكاء حسب طول الصف
                if has_variant_col and len(item) > 2:
                    variant_id = item[1]
                    quantity = item[2]
                else:
                    variant_id = None
                    quantity = item[1] if len(item) > 1 else 0
                
                if quantity <= 0:
                    continue  # تجاهل الكميات الصفرية أو السالبة (إرجاعات)
                
                # أ) استعادة المتغير (Variant)
                if variant_id:
                    check_var = "SELECT id FROM product_variants WHERE id = ?"
                    cursor.execute(check_var, (variant_id,))
                    if cursor.fetchone():
                        if var_has_updated:
                            sql = "UPDATE product_variants SET current_stock = current_stock + ?, updated_at = ? WHERE id = ?"
                            cursor.execute(sql, (quantity, datetime.now(), variant_id))
                        else:
                            sql = "UPDATE product_variants SET current_stock = current_stock + ? WHERE id = ?"
                            cursor.execute(sql, (quantity, variant_id))
                        
                        if self.logger:
                            self.logger.debug(f"✅ تم استعادة {quantity} وحدة للمتغير {variant_id}")
                    else:
                        variant_id = None  # المتغير محذوف، نعيد للمنتج الرئيسي
                        if self.logger:
                            self.logger.warning(f"⚠️ المتغير {variant_id} غير موجود، استخدام المنتج الرئيسي {product_id}")
                
                # ب) استعادة المنتج الرئيسي (إذا لم يكن متغير أو المتغير محذوف)
                if not variant_id:
                    if prod_has_updated:
                        sql = "UPDATE products SET current_stock = current_stock + ?, updated_at = ? WHERE id = ?"
                        cursor.execute(sql, (quantity, datetime.now(), product_id))
                    else:
                        sql = "UPDATE products SET current_stock = current_stock + ? WHERE id = ?"
                        cursor.execute(sql, (quantity, product_id))
                    
                    if self.logger:
                        self.logger.debug(f"✅ تم استعادة {quantity} وحدة للمنتج {product_id}")
            
            # ===== المرحلة 4: التصحيح المالي (Financial Rollback) =====
            # عند الإلغاء، إذا كان هناك مبلغ متبقي (دين)، يجب إرجاعه للعميل
            # إذا كان remaining_amount = 100، فهذا يعني أن العميل مدين بـ 100
            # عند الإلغاء، يجب أن نرجع هذا المبلغ (نطرح الدين من الرصيد)
            # لكن إذا كان create_sale لا يحدث الرصيد تلقائياً، فلا داعي لتعديله هنا
            # سنتحقق من أن الفاتورة لديها remaining_amount > 0 فقط
            if sale.customer_id and sale.remaining_amount and sale.remaining_amount > 0:
                cursor.execute("SELECT current_balance FROM customers WHERE id = ?", (sale.customer_id,))
                cust_res = cursor.fetchone()
                if cust_res:
                    curr_bal = Decimal(str(cust_res[0]))
                    # عند الإلغاء، نرجع المبلغ المتبقي (نطرح الدين)
                    # إذا كان العميل مديناً بـ 100 (remaining_amount = 100)
                    # وكان رصيده الحالي = 100 (دين)، بعد الإلغاء يصبح 0
                    # إذا كان رصيده الحالي = 0، بعد الإلغاء يصبح -100 (نرجع المبلغ)
                    # لكن هذا يعتمد على كيفية تحديث الرصيد عند إنشاء الفاتورة
                    # سنفترض أن remaining_amount يمثل الدين الذي يجب إرجاعه
                    new_bal = curr_bal - sale.remaining_amount
                    
                    # التحقق من وجود updated_at في العملاء
                    cursor.execute("PRAGMA table_info(customers)")
                    cust_cols = [row[1] for row in cursor.fetchall()]
                    
                    if 'updated_at' in cust_cols:
                        sql = "UPDATE customers SET current_balance = ?, updated_at = ? WHERE id = ?"
                        cursor.execute(sql, (float(new_bal), datetime.now(), sale.customer_id))
                    else:
                        sql = "UPDATE customers SET current_balance = ? WHERE id = ?"
                        cursor.execute(sql, (float(new_bal), sale.customer_id))
                    
                    if self.logger:
                        self.logger.info(f"💰 تم تعديل رصيد العميل {sale.customer_id}: {curr_bal} → {new_bal}")
                else:
                    if self.logger:
                        self.logger.warning(f"⚠️ العميل {sale.customer_id} غير موجود - تم تخطي تعديل الرصيد")
            
            # ===== المرحلة 5: الختم النهائي (Status Update) =====
            existing_notes = sale.notes or ""
            note_text = f"\n[إلغاء] {cancellation_reason} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})" if cancellation_reason else f"\n[إلغاء] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            final_notes = existing_notes + note_text
            
            # التحقق من updated_at في sales (غالباً موجود لكن للاحتياط)
            cursor.execute("PRAGMA table_info(sales)")
            sale_cols = [row[1] for row in cursor.fetchall()]
            
            # استخدام القيمة الإنجليزية للحالة (قاعدة البيانات تستخدم الإنجليزية)
            cancelled_status = 'cancelled'  # القيمة المتوقعة في قاعدة البيانات
            
            if 'updated_at' in sale_cols:
                sql = "UPDATE sales SET status = ?, notes = ?, updated_at = ? WHERE id = ?"
                cursor.execute(sql, (cancelled_status, final_notes, datetime.now(), sale_id))
            else:
                sql = "UPDATE sales SET status = ?, notes = ? WHERE id = ?"
                cursor.execute(sql, (cancelled_status, final_notes, sale_id))
            
            if self.logger:
                self.logger.info(f"📝 تم تحديث حالة الفاتورة {sale_id} إلى 'ملغاة'")
            
            # ===== المرحلة 6: الاعتماد (Commit) =====
            connection.commit()
            if self.logger:
                self.logger.info(f"✅ تم إلغاء الفاتورة {sale_id} واستعادة المخزون")
            
            # تحديث الجلسة (في الذاكرة فقط)
            if self.current_session:
                self.current_session.total_returns += float(sale.total_amount)
            
            return True
            
        except Exception as e:
            if connection:
                try:
                    connection.rollback()
                except:
                    pass
            if self.logger:
                self.logger.error(f"❌ فشل إلغاء الفاتورة (ROLLBACK): {e}")
                import traceback
                self.logger.error(traceback.format_exc())
            return False
            
        finally:
            # إغلاق المؤشر فقط، لا نغلق الاتصال لأنه قد يكون مشتركاً (Pooled)
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
    
    def search_sales(self, query: str = "", customer_id: Optional[int] = None,
                    start_date: Optional[date] = None, end_date: Optional[date] = None,
                    status: Optional[str] = None, limit: int = 100) -> List[Sale]:
        """البحث في المبيعات"""
        try:
            return self.sale_manager.search_sales(query, customer_id, start_date, end_date, status, limit)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث في المبيعات: {str(e)}")
            return []
    
    # ===== إدارة جلسات نقطة البيع =====
    
    def start_pos_session(self, user_id: int, opening_cash: float = 0.0) -> Optional[int]:
        """بدء جلسة نقطة البيع"""
        try:
            # التحقق من عدم وجود جلسة نشطة
            if self.current_session and self.current_session.is_active:
                if self.logger:
                    self.logger.warning("يوجد جلسة نشطة بالفعل")
                return None
            
            # إنشاء جلسة جديدة
            query = """
            INSERT INTO pos_sessions (user_id, start_time, opening_cash, cash_in_drawer, is_active)
            VALUES (?, ?, ?, ?, 1)
            """
            
            now = datetime.now()
            params = (user_id, now, opening_cash, opening_cash)
            
            result = self.db_manager.execute_query(query, params)
            if result and hasattr(result, 'lastrowid'):
                session_id = result.lastrowid
                
                self.current_session = POSSession(
                    id=session_id,
                    user_id=user_id,
                    start_time=now,
                    opening_cash=opening_cash,
                    cash_in_drawer=opening_cash,
                    is_active=True
                )
                
                if self.logger:
                    self.logger.info(f"تم بدء جلسة نقطة البيع {session_id}")
                
                return session_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في بدء جلسة نقطة البيع: {str(e)}")
        
        return None
    
    def end_pos_session(self, closing_cash: float, user_id: Optional[int] = None) -> bool:
        """إنهاء جلسة نقطة البيع"""
        try:
            if not self.current_session or not self.current_session.is_active:
                if self.logger:
                    self.logger.warning("لا توجد جلسة نشطة لإنهائها")
                return False
            
            # تحديث الجلسة
            query = """
            UPDATE pos_sessions SET
                end_time = ?, closing_cash = ?, is_active = 0
            WHERE id = ?
            """
            
            now = datetime.now()
            params = (now, closing_cash, self.current_session.id)
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                self.current_session.end_time = now
                self.current_session.closing_cash = closing_cash
                self.current_session.is_active = False
                
                if self.logger:
                    self.logger.info(f"تم إنهاء جلسة نقطة البيع {self.current_session.id}")
                
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنهاء جلسة نقطة البيع: {str(e)}")
        
        return False
    
    def get_current_session(self) -> Optional[POSSession]:
        """الحصول على الجلسة الحالية"""
        return self.current_session
    
    # ===== التقارير والإحصائيات =====
    
    def generate_sales_report(self, start_date: date, end_date: date) -> SalesReport:
        """إنشاء تقرير المبيعات"""
        try:
            # إحصائيات عامة
            sales_stats = self._get_sales_statistics(start_date, end_date)
            
            # أفضل المنتجات
            top_products = self._get_top_selling_products(start_date, end_date)
            
            # أفضل العملاء
            top_customers = self._get_top_customers(start_date, end_date)
            
            # المبيعات حسب اليوم
            sales_by_day = self._get_sales_by_day(start_date, end_date)
            
            # المبيعات حسب طريقة الدفع
            sales_by_payment = self._get_sales_by_payment_method(start_date, end_date)
            
            report = SalesReport(
                total_sales=sales_stats['total_sales'],
                total_revenue=sales_stats['total_revenue'],
                total_profit=sales_stats['total_profit'],
                average_sale_value=sales_stats['average_sale_value'],
                top_products=top_products,
                top_customers=top_customers,
                sales_by_day=sales_by_day,
                sales_by_payment_method=sales_by_payment,
                period_start=start_date,
                period_end=end_date
            )
            
            return report
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء تقرير المبيعات: {str(e)}")
            return SalesReport(
                total_sales=0, total_revenue=0, total_profit=0, average_sale_value=0,
                top_products=[], top_customers=[], sales_by_day=[], sales_by_payment_method=[],
                period_start=start_date, period_end=end_date
            )
    
    def get_daily_summary(self, target_date: date) -> DailySummary:
        """الحصول على ملخص يومي للمبيعات"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue,
                SUM(CASE WHEN payment_method = 'نقدي' THEN total_amount ELSE 0 END) as cash_sales,
                SUM(CASE WHEN payment_method = 'بطاقة' THEN total_amount ELSE 0 END) as card_sales,
                SUM(CASE WHEN payment_method = 'آجل' THEN total_amount ELSE 0 END) as credit_sales,
                SUM(CASE WHEN status = 'ملغي' THEN total_amount ELSE 0 END) as returns
            FROM sales
            WHERE DATE(sale_date) = ? AND status != 'ملغي'
            """
            
            result = self.db_manager.fetch_one(query, (target_date.isoformat(),))
            
            if result:
                total_revenue = result[1] or 0
                returns = result[5] or 0
                net_sales = total_revenue - returns
                
                # حساب الربح (يتطلب تكلفة المنتجات)
                profit = self._calculate_daily_profit(target_date)
                
                summary = DailySummary(
                    date=target_date,
                    total_sales=result[0] or 0,
                    total_revenue=total_revenue,
                    total_profit=profit,
                    cash_sales=result[2] or 0,
                    card_sales=result[3] or 0,
                    credit_sales=result[4] or 0,
                    returns=returns,
                    net_sales=net_sales
                )
                
                return summary
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الملخص اليومي: {str(e)}")
        
        return DailySummary(
            date=target_date, total_sales=0, total_revenue=0, total_profit=0,
            cash_sales=0, card_sales=0, credit_sales=0, returns=0, net_sales=0
        )
    
    # ===== الدوال المساعدة =====
    
    def _update_sale_total(self, sale_id: int):
        """تحديث إجمالي الفاتورة"""
        try:
            query = """
            UPDATE sales SET
                total_amount = (
                    SELECT SUM((quantity * unit_price) - discount)
                    FROM sale_items
                    WHERE sale_id = ?
                ),
                updated_at = ?
            WHERE id = ?
            """
            
            params = (sale_id, datetime.now(), sale_id)
            self.db_manager.execute_query(query, params)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث إجمالي الفاتورة {sale_id}: {str(e)}")
    
    def _update_session_sales(self, amount: float):
        """تحديث مبيعات الجلسة"""
        if self.current_session:
            self.current_session.total_sales += amount
    
    def _get_sales_statistics(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """الحصول على إحصائيات المبيعات"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as average_sale_value
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ? AND status = 'مكتمل'
            """
            
            result = self.db_manager.fetch_one(query, (start_date.isoformat(), end_date.isoformat()))
            
            if result:
                # حساب الربح الإجمالي
                total_profit = self._calculate_period_profit(start_date, end_date)
                
                return {
                    'total_sales': result[0] or 0,
                    'total_revenue': result[1] or 0,
                    'average_sale_value': result[2] or 0,
                    'total_profit': total_profit
                }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على إحصائيات المبيعات: {str(e)}")
        
        return {'total_sales': 0, 'total_revenue': 0, 'average_sale_value': 0, 'total_profit': 0}
    
    def _get_top_selling_products(self, start_date: date, end_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على أفضل المنتجات مبيعاً"""
        try:
            query = """
            SELECT 
                p.id, p.name, 
                SUM(si.quantity) as total_quantity,
                SUM(si.quantity * si.unit_price - si.discount) as total_revenue
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ? AND s.status = 'مكتمل'
            GROUP BY p.id, p.name
            ORDER BY total_quantity DESC
            LIMIT ?
            """
            
            results = self.db_manager.fetch_all(query, (start_date.isoformat(), end_date.isoformat(), limit))
            
            return [
                {
                    'product_id': row[0],
                    'product_name': row[1],
                    'total_quantity': row[2],
                    'total_revenue': row[3]
                }
                for row in results
            ]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على أفضل المنتجات: {str(e)}")
            return []
    
    def _get_top_customers(self, start_date: date, end_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على أفضل العملاء"""
        try:
            query = """
            SELECT 
                c.id, c.name,
                COUNT(s.id) as total_purchases,
                SUM(s.total_amount) as total_spent
            FROM customers c
            JOIN sales s ON c.id = s.customer_id
            WHERE DATE(s.sale_date) BETWEEN ? AND ? AND s.status = 'مكتمل'
            GROUP BY c.id, c.name
            ORDER BY total_spent DESC
            LIMIT ?
            """
            
            results = self.db_manager.fetch_all(query, (start_date.isoformat(), end_date.isoformat(), limit))
            
            return [
                {
                    'customer_id': row[0],
                    'customer_name': row[1],
                    'total_purchases': row[2],
                    'total_spent': row[3]
                }
                for row in results
            ]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على أفضل العملاء: {str(e)}")
            return []
    
    def _get_sales_by_day(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """الحصول على المبيعات حسب اليوم"""
        try:
            query = """
            SELECT 
                DATE(sale_date) as sale_date,
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ? AND status = 'مكتمل'
            GROUP BY DATE(sale_date)
            ORDER BY sale_date
            """
            
            results = self.db_manager.fetch_all(query, (start_date.isoformat(), end_date.isoformat()))
            
            return [
                {
                    'date': row[0],
                    'total_sales': row[1],
                    'total_revenue': row[2]
                }
                for row in results
            ]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المبيعات حسب اليوم: {str(e)}")
            return []
    
    def _get_sales_by_payment_method(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """الحصول على المبيعات حسب طريقة الدفع"""
        try:
            query = """
            SELECT 
                payment_method,
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ? AND status = 'مكتمل'
            GROUP BY payment_method
            ORDER BY total_revenue DESC
            """
            
            results = self.db_manager.fetch_all(query, (start_date.isoformat(), end_date.isoformat()))
            
            return [
                {
                    'payment_method': row[0],
                    'total_sales': row[1],
                    'total_revenue': row[2]
                }
                for row in results
            ]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المبيعات حسب طريقة الدفع: {str(e)}")
            return []
    
    def _calculate_daily_profit(self, target_date: date) -> float:
        """حساب ربح يوم محدد"""
        try:
            query = """
            SELECT SUM(
                (si.unit_price - p.cost_price) * si.quantity - si.discount
            ) as total_profit
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.sale_date) = ? AND s.status = 'مكتمل'
            """
            
            result = self.db_manager.fetch_one(query, (target_date.isoformat(),))
            return result[0] if result and result[0] else 0.0
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب الربح اليومي: {str(e)}")
            return 0.0
    
    def _calculate_period_profit(self, start_date: date, end_date: date) -> float:
        """حساب ربح فترة محددة"""
        try:
            query = """
            SELECT SUM(
                (si.unit_price - p.cost_price) * si.quantity - si.discount
            ) as total_profit
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ? AND s.status = 'مكتمل'
            """
            
            result = self.db_manager.fetch_one(query, (start_date.isoformat(), end_date.isoformat()))
            return result[0] if result and result[0] else 0.0
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب ربح الفترة: {str(e)}")
            return 0.0