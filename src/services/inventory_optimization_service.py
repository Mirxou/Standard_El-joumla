"""
Inventory Optimization Service - خدمة تحسين المخزون
تحليل ABC، الأرصدة الآمنة، توصيات إعادة الطلب
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
import math

from ..core.database_manager import DatabaseManager
from ..models.inventory_optimization import (
    ABCAnalysisResult, ABCCategory,
    SafetyStockConfig, ReorderStatus,
    ProductBatch, BatchStatus,
    ReorderRecommendation
)


class InventoryOptimizationService:
    """خدمة تحسين المخزون"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    # ============================================================================
    # تحليل ABC
    # ============================================================================
    
    def perform_abc_analysis(self, period_months: int = 12) -> List[ABCAnalysisResult]:
        """تنفيذ تحليل ABC على المنتجات"""
        try:
            # حساب تاريخ البدء
            end_date = date.today()
            start_date = end_date - timedelta(days=period_months * 30)
            
            # جلب بيانات المبيعات لكل منتج
            query = """
            SELECT 
                p.id as product_id,
                p.code as product_code,
                p.name as product_name,
                COALESCE(SUM(si.quantity), 0) as total_quantity,
                COALESCE(SUM(si.quantity * si.unit_price), 0) as total_value,
                COALESCE(AVG(si.unit_price), p.selling_price) as avg_price,
                p.stock_quantity as current_stock,
                p.stock_quantity * p.cost_price as stock_value,
                COUNT(DISTINCT s.id) as sale_count,
                MAX(s.sale_date) as last_sale_date
            FROM products p
            LEFT JOIN sale_items si ON p.id = si.product_id
            LEFT JOIN sales s ON si.sale_id = s.id AND s.sale_date BETWEEN ? AND ?
            WHERE p.is_active = 1
            GROUP BY p.id
            HAVING total_value > 0
            ORDER BY total_value DESC
            """
            
            rows = self.db.execute_query(query, (start_date, end_date))
            
            if not rows:
                return []
            
            # حساب الإجمالي الكلي
            total_value = sum(Decimal(str(row['total_value'])) for row in rows)
            
            # إنشاء نتائج التحليل
            results = []
            cumulative_percentage = Decimal('0')
            
            for rank, row in enumerate(rows, 1):
                sales_value = Decimal(str(row['total_value']))
                percentage = (sales_value / total_value * 100) if total_value > 0 else Decimal('0')
                cumulative_percentage += percentage
                
                # تحديد الفئة
                if cumulative_percentage <= 80:
                    category = ABCCategory.A.value
                elif cumulative_percentage <= 95:
                    category = ABCCategory.B.value
                else:
                    category = ABCCategory.C.value
                
                # حساب الأيام منذ آخر بيع
                last_sale = None
                days_since = None
                if row['last_sale_date']:
                    last_sale = date.fromisoformat(row['last_sale_date'])
                    days_since = (date.today() - last_sale).days
                
                result = ABCAnalysisResult(
                    product_id=row['product_id'],
                    product_code=row['product_code'],
                    product_name=row['product_name'],
                    annual_sales_quantity=Decimal(str(row['total_quantity'])),
                    annual_sales_value=sales_value,
                    average_unit_price=Decimal(str(row['avg_price'])),
                    current_stock=Decimal(str(row['current_stock'] or 0)),
                    stock_value=Decimal(str(row['stock_value'] or 0)),
                    abc_category=category,
                    percentage_of_total_value=percentage,
                    cumulative_percentage=cumulative_percentage,
                    rank=rank,
                    sales_frequency=row['sale_count'],
                    last_sale_date=last_sale,
                    days_since_last_sale=days_since,
                    analysis_date=date.today()
                )
                
                # توليد التوصيات
                result.generate_recommendations()
                
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error in ABC analysis: {e}")
            return []
    
    def get_abc_summary(self, results: List[ABCAnalysisResult]) -> Dict[str, Any]:
        """ملخص تحليل ABC"""
        summary = {
            'total_products': len(results),
            'category_a_count': 0,
            'category_b_count': 0,
            'category_c_count': 0,
            'category_a_value': Decimal('0'),
            'category_b_value': Decimal('0'),
            'category_c_value': Decimal('0'),
            'total_value': Decimal('0')
        }
        
        for result in results:
            summary['total_value'] += result.annual_sales_value
            
            if result.abc_category == ABCCategory.A.value:
                summary['category_a_count'] += 1
                summary['category_a_value'] += result.annual_sales_value
            elif result.abc_category == ABCCategory.B.value:
                summary['category_b_count'] += 1
                summary['category_b_value'] += result.annual_sales_value
            else:
                summary['category_c_count'] += 1
                summary['category_c_value'] += result.annual_sales_value
        
        # حساب النسب
        if summary['total_value'] > 0:
            summary['category_a_percentage'] = float((summary['category_a_value'] / summary['total_value']) * 100)
            summary['category_b_percentage'] = float((summary['category_b_value'] / summary['total_value']) * 100)
            summary['category_c_percentage'] = float((summary['category_c_value'] / summary['total_value']) * 100)
        
        return summary
    
    # ============================================================================
    # الأرصدة الآمنة (Safety Stock)
    # ============================================================================
    
    def create_safety_stock_config(self, config: SafetyStockConfig) -> SafetyStockConfig:
        """إنشاء إعدادات أرصدة آمنة لمنتج"""
        try:
            # حساب القيم التلقائية إذا لم تكن محددة
            if config.average_daily_demand > 0:
                config.calculate_safety_stock()
                config.calculate_reorder_point()
            
            query = """
            INSERT INTO safety_stock_configs (
                product_id, reorder_point, safety_stock, maximum_stock, minimum_stock,
                average_daily_demand, lead_time_days, service_level,
                holding_cost_percentage, order_cost, is_active, auto_reorder_enabled,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                config.product_id,
                float(config.reorder_point),
                float(config.safety_stock),
                float(config.maximum_stock),
                float(config.minimum_stock),
                float(config.average_daily_demand),
                config.lead_time_days,
                float(config.service_level),
                float(config.holding_cost_percentage),
                float(config.order_cost),
                config.is_active,
                config.auto_reorder_enabled,
                datetime.now(),
                datetime.now()
            )
            
            config.id = self.db.execute_update(query, params)
            return config
            
        except Exception as e:
            raise Exception(f"Failed to create safety stock config: {e}")
    
    def get_safety_stock_config(self, product_id: int) -> Optional[SafetyStockConfig]:
        """جلب إعدادات الأرصدة الآمنة لمنتج"""
        try:
            query = """
            SELECT 
                ssc.*,
                p.code as product_code,
                p.name as product_name,
                p.stock_quantity as current_stock
            FROM safety_stock_configs ssc
            JOIN products p ON ssc.product_id = p.id
            WHERE ssc.product_id = ?
            """
            
            row = self.db.execute_query(query, (product_id,))
            
            if row:
                config = SafetyStockConfig.from_dict(self._row_to_dict(row[0]))
                config.update_reorder_status()
                config.calculate_suggested_order()
                return config
            
            return None
            
        except Exception as e:
            print(f"Error getting safety stock config: {e}")
            return None
    
    def update_safety_stock_config(self, config: SafetyStockConfig):
        """تحديث إعدادات الأرصدة الآمنة"""
        try:
            config.updated_at = datetime.now()
            config.update_reorder_status()
            config.calculate_suggested_order()
            
            query = """
            UPDATE safety_stock_configs SET
                reorder_point = ?,
                safety_stock = ?,
                maximum_stock = ?,
                minimum_stock = ?,
                average_daily_demand = ?,
                lead_time_days = ?,
                service_level = ?,
                holding_cost_percentage = ?,
                order_cost = ?,
                is_active = ?,
                auto_reorder_enabled = ?,
                updated_at = ?
            WHERE id = ?
            """
            
            params = (
                float(config.reorder_point),
                float(config.safety_stock),
                float(config.maximum_stock),
                float(config.minimum_stock),
                float(config.average_daily_demand),
                config.lead_time_days,
                float(config.service_level),
                float(config.holding_cost_percentage),
                float(config.order_cost),
                config.is_active,
                config.auto_reorder_enabled,
                config.updated_at,
                config.id
            )
            
            self.db.execute_update(query, params)
            
        except Exception as e:
            raise Exception(f"Failed to update safety stock config: {e}")
    
    def get_all_safety_stock_configs(self, status_filter: Optional[str] = None) -> List[SafetyStockConfig]:
        """جلب جميع إعدادات الأرصدة الآمنة"""
        try:
            query = """
            SELECT 
                ssc.*,
                p.code as product_code,
                p.name as product_name,
                p.stock_quantity as current_stock
            FROM safety_stock_configs ssc
            JOIN products p ON ssc.product_id = p.id
            WHERE ssc.is_active = 1
            ORDER BY p.name
            """
            
            rows = self.db.execute_query(query)
            
            configs = []
            for row in rows:
                config = SafetyStockConfig.from_dict(self._row_to_dict(row))
                config.update_reorder_status()
                config.calculate_suggested_order()
                
                # تصفية حسب الحالة
                if status_filter is None or config.reorder_status == status_filter:
                    configs.append(config)
            
            return configs
            
        except Exception as e:
            print(f"Error getting safety stock configs: {e}")
            return []
    
    def calculate_demand_statistics(self, product_id: int, days: int = 90) -> Dict[str, Decimal]:
        """حساب إحصائيات الطلب لمنتج"""
        try:
            start_date = date.today() - timedelta(days=days)
            
            query = """
            SELECT 
                COALESCE(SUM(si.quantity), 0) as total_quantity,
                COUNT(DISTINCT s.id) as sale_count,
                COUNT(DISTINCT DATE(s.sale_date)) as days_with_sales
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE si.product_id = ? AND s.sale_date >= ?
            """
            
            row = self.db.execute_query(query, (product_id, start_date))
            
            if row:
                total_qty = Decimal(str(row[0]['total_quantity']))
                days_with_sales = row[0]['days_with_sales'] or 1
                
                # متوسط الطلب اليومي
                avg_daily = total_qty / days
                
                # الانحراف المعياري (تقدير بسيط)
                std_dev = avg_daily * Decimal('0.3')  # تقدير 30% من المتوسط
                
                return {
                    'total_demand': total_qty,
                    'average_daily_demand': avg_daily,
                    'std_deviation': std_dev,
                    'days_with_sales': Decimal(str(days_with_sales))
                }
            
            return {
                'total_demand': Decimal('0'),
                'average_daily_demand': Decimal('0'),
                'std_deviation': Decimal('0'),
                'days_with_sales': Decimal('0')
            }
            
        except Exception as e:
            print(f"Error calculating demand statistics: {e}")
            return {}
    
    def auto_configure_safety_stock(self, product_id: int, lead_time_days: int = 7) -> SafetyStockConfig:
        """إعداد تلقائي للأرصدة الآمنة بناءً على البيانات التاريخية"""
        try:
            # جلب معلومات المنتج
            product_query = "SELECT code, name, stock_quantity, cost_price FROM products WHERE id = ?"
            product_row = self.db.execute_query(product_query, (product_id,))
            
            if not product_row:
                raise Exception("Product not found")
            
            product = product_row[0]
            
            # حساب إحصائيات الطلب
            stats = self.calculate_demand_statistics(product_id)
            
            # إنشاء إعدادات
            config = SafetyStockConfig(
                product_id=product_id,
                product_code=product['code'],
                product_name=product['name'],
                current_stock=Decimal(str(product['stock_quantity'] or 0)),
                average_daily_demand=stats.get('average_daily_demand', Decimal('1')),
                lead_time_days=lead_time_days,
                service_level=Decimal('95')
            )
            
            # حساب القيم
            config.calculate_safety_stock(stats.get('std_deviation'))
            config.calculate_reorder_point()
            
            # تقدير الحدود
            config.minimum_stock = config.safety_stock
            config.maximum_stock = config.reorder_point * Decimal('2')
            
            # حساب EOQ
            annual_demand = stats.get('total_demand', Decimal('0')) * (365 / 90)
            config.calculate_economic_order_quantity(
                annual_demand,
                Decimal(str(product['cost_price'] or 100))
            )
            
            config.update_reorder_status()
            config.calculate_suggested_order()
            
            return config
            
        except Exception as e:
            raise Exception(f"Failed to auto-configure safety stock: {e}")
    
    # ============================================================================
    # توصيات إعادة الطلب
    # ============================================================================
    
    def generate_reorder_recommendations(self) -> List[ReorderRecommendation]:
        """توليد توصيات إعادة الطلب"""
        try:
            configs = self.get_all_safety_stock_configs()
            recommendations = []
            
            for config in configs:
                if config.reorder_status in [
                    ReorderStatus.REORDER.value,
                    ReorderStatus.CRITICAL.value,
                    ReorderStatus.STOCKOUT.value
                ]:
                    # تحديد الأولوية والإلحاح
                    if config.reorder_status == ReorderStatus.STOCKOUT.value:
                        priority = 5
                        urgency = "URGENT"
                    elif config.reorder_status == ReorderStatus.CRITICAL.value:
                        priority = 4
                        urgency = "HIGH"
                    else:
                        priority = 3
                        urgency = "MEDIUM"
                    
                    # الأسباب
                    reasons = []
                    if config.current_stock <= 0:
                        reasons.append("❌ نفاذ المخزون بالكامل")
                    elif config.current_stock <= config.minimum_stock:
                        reasons.append("⛔ أقل من الحد الأدنى")
                    elif config.current_stock <= config.reorder_point:
                        reasons.append("📦 وصل لنقطة إعادة الطلب")
                    
                    # تقدير تاريخ نفاذ المخزون
                    stockout_date = None
                    if config.days_until_stockout:
                        stockout_date = date.today() + timedelta(days=config.days_until_stockout)
                        reasons.append(f"⏰ متوقع النفاذ خلال {config.days_until_stockout} يوم")
                    
                    recommendation = ReorderRecommendation(
                        product_id=config.product_id,
                        product_code=config.product_code,
                        product_name=config.product_name,
                        current_stock=config.current_stock,
                        reorder_point=config.reorder_point,
                        safety_stock=config.safety_stock,
                        suggested_quantity=config.suggested_order_quantity,
                        priority=priority,
                        urgency=urgency,
                        reasons=reasons,
                        estimated_stockout_date=stockout_date,
                        lead_time_days=config.lead_time_days
                    )
                    
                    recommendations.append(recommendation)
            
            # ترتيب حسب الأولوية
            recommendations.sort(key=lambda x: x.priority, reverse=True)
            
            return recommendations
            
        except Exception as e:
            print(f"Error generating reorder recommendations: {e}")
            return []
    
    # ============================================================================
    # تتبع الدفعات
    # ============================================================================
    
    def create_batch(self, batch: ProductBatch) -> ProductBatch:
        """إنشاء دفعة جديدة"""
        try:
            batch.available_quantity = batch.current_quantity - batch.reserved_quantity
            batch.total_cost = batch.initial_quantity * batch.unit_cost
            batch.update_status()
            
            query = """
            INSERT INTO product_batches (
                product_id, batch_number, serial_numbers,
                initial_quantity, current_quantity, reserved_quantity, available_quantity,
                manufacturing_date, expiry_date, received_date,
                warehouse_location, rack_number, bin_number,
                supplier_id, supplier_name, purchase_order_number,
                unit_cost, total_cost, status, notes, quality_check_passed,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                batch.product_id,
                batch.batch_number,
                ','.join(batch.serial_numbers) if batch.serial_numbers else '',
                float(batch.initial_quantity),
                float(batch.current_quantity),
                float(batch.reserved_quantity),
                float(batch.available_quantity),
                batch.manufacturing_date.isoformat() if batch.manufacturing_date else None,
                batch.expiry_date.isoformat() if batch.expiry_date else None,
                batch.received_date.isoformat(),
                batch.warehouse_location,
                batch.rack_number,
                batch.bin_number,
                batch.supplier_id,
                batch.supplier_name,
                batch.purchase_order_number,
                float(batch.unit_cost),
                float(batch.total_cost),
                batch.status,
                batch.notes,
                batch.quality_check_passed,
                datetime.now(),
                datetime.now()
            )
            
            batch.id = self.db.execute_update(query, params)
            return batch
            
        except Exception as e:
            raise Exception(f"Failed to create batch: {e}")
    
    def get_batches_by_product(self, product_id: int, include_expired: bool = False) -> List[ProductBatch]:
        """جلب الدفعات حسب المنتج"""
        try:
            query = """
            SELECT * FROM product_batches
            WHERE product_id = ?
            """
            
            if not include_expired:
                query += " AND status != ?"
                params = (product_id, BatchStatus.EXPIRED.value)
            else:
                params = (product_id,)
            
            query += " ORDER BY expiry_date ASC, received_date ASC"
            
            rows = self.db.execute_query(query, params)
            
            batches = []
            for row in rows:
                batch = ProductBatch.from_dict(self._row_to_dict(row))
                batch.update_status()
                batches.append(batch)
            
            return batches
            
        except Exception as e:
            print(f"Error getting batches: {e}")
            return []
    
    def get_expiring_batches(self, days: int = 30) -> List[ProductBatch]:
        """جلب الدفعات القريبة من انتهاء الصلاحية"""
        try:
            expiry_date = date.today() + timedelta(days=days)
            
            query = """
            SELECT pb.*, p.code as product_code, p.name as product_name
            FROM product_batches pb
            JOIN products p ON pb.product_id = p.id
            WHERE pb.expiry_date IS NOT NULL
            AND pb.expiry_date <= ?
            AND pb.expiry_date >= ?
            AND pb.current_quantity > 0
            AND pb.status = ?
            ORDER BY pb.expiry_date ASC
            """
            
            rows = self.db.execute_query(query, (expiry_date, date.today(), BatchStatus.ACTIVE.value))
            
            batches = []
            for row in rows:
                batch = ProductBatch.from_dict(self._row_to_dict(row))
                batch.update_status()
                batches.append(batch)
            
            return batches
            
        except Exception as e:
            print(f"Error getting expiring batches: {e}")
            return []
    
    # ============================================================================
    # Utilities
    # ============================================================================
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """تحويل صف من قاعدة البيانات إلى قاموس"""
        if hasattr(row, 'keys'):
            return {key: row[key] for key in row.keys()}
        return row
