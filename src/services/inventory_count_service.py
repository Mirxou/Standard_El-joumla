"""
خدمة الجرد الدوري والتسويات
Inventory Count and Adjustments Service
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from core.database_manager import DatabaseManager
from models.physical_count import (
    PhysicalCount, CountItem, StockAdjustment,
    CountStatus, AdjustmentType, AdjustmentStatus
)


class InventoryCountService:
    """خدمة إدارة الجرد الدوري"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    # ==================== Physical Counts ====================
    
    def create_count(self, count: PhysicalCount) -> int:
        """إنشاء جرد جديد"""
        query = """
            INSERT INTO physical_counts (
                count_number, count_date, scheduled_date, description,
                location, counted_by, status, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        count.created_at = datetime.now()
        count_id = self.db.execute_query(
            query,
            (
                count.count_number,
                count.count_date,
                count.scheduled_date,
                count.description,
                count.location,
                count.counted_by,
                count.status.value,
                count.notes,
                count.created_at
            )
        )
        
        # إضافة العناصر
        if count.items:
            for item in count.items:
                item.count_id = count_id
                self.add_count_item(item)
        
        return count_id
    
    def get_count_by_id(self, count_id: int) -> Optional[PhysicalCount]:
        """الحصول على جرد بالمعرف"""
        query = """
            SELECT 
                pc.*,
                u1.username as counted_by_name,
                u2.username as approved_by_name
            FROM physical_counts pc
            LEFT JOIN users u1 ON pc.counted_by = u1.id
            LEFT JOIN users u2 ON pc.approved_by = u2.id
            WHERE pc.id = ?
        """
        
        row = self.db.fetch_one(query, (count_id,))
        if not row:
            return None
        
        count = self._row_to_count(row)
        count.items = self.get_count_items(count_id)
        count.calculate_statistics()
        
        return count
    
    def get_all_counts(
        self,
        status: Optional[CountStatus] = None,
        location: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[PhysicalCount]:
        """الحصول على جميع الجرود مع فلاتر"""
        query = """
            SELECT 
                pc.*,
                u1.username as counted_by_name,
                u2.username as approved_by_name
            FROM physical_counts pc
            LEFT JOIN users u1 ON pc.counted_by = u1.id
            LEFT JOIN users u2 ON pc.approved_by = u2.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND pc.status = ?"
            params.append(status.value)
        
        if location:
            query += " AND pc.location = ?"
            params.append(location)
        
        if from_date:
            query += " AND pc.count_date >= ?"
            params.append(from_date)
        
        if to_date:
            query += " AND pc.count_date <= ?"
            params.append(to_date)
        
        query += " ORDER BY pc.count_date DESC, pc.id DESC"
        
        rows = self.db.fetch_all(query, tuple(params))
        counts = [self._row_to_count(row) for row in rows]
        
        # تحميل الإحصائيات لكل جرد
        for count in counts:
            count.items = self.get_count_items(count.id)
            count.calculate_statistics()
        
        return counts
    
    def update_count(self, count: PhysicalCount) -> bool:
        """تحديث جرد"""
        query = """
            UPDATE physical_counts SET
                count_date = ?,
                scheduled_date = ?,
                description = ?,
                location = ?,
                status = ?,
                approved_by = ?,
                approved_at = ?,
                completed_at = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
        """
        
        count.updated_at = datetime.now()
        result = self.db.execute_query(
            query,
            (
                count.count_date,
                count.scheduled_date,
                count.description,
                count.location,
                count.status.value,
                count.approved_by,
                count.approved_at,
                count.completed_at,
                count.notes,
                count.updated_at,
                count.id
            )
        )
        
        return result > 0
    
    def delete_count(self, count_id: int) -> bool:
        """حذف جرد (إذا كان مسودة فقط)"""
        # التحقق من الحالة
        count = self.get_count_by_id(count_id)
        if not count or count.status not in [CountStatus.DRAFT, CountStatus.CANCELLED]:
            return False
        
        # حذف العناصر أولاً
        self.db.execute_query("DELETE FROM count_items WHERE count_id = ?", (count_id,))
        
        # حذف الجرد
        result = self.db.execute_query("DELETE FROM physical_counts WHERE id = ?", (count_id,))
        return result > 0
    
    def start_count(self, count_id: int) -> bool:
        """بدء الجرد"""
        count = self.get_count_by_id(count_id)
        if not count:
            return False
        
        if count.start_count():
            return self.update_count(count)
        return False
    
    def complete_count(self, count_id: int) -> bool:
        """إكمال الجرد"""
        count = self.get_count_by_id(count_id)
        if not count:
            return False
        
        if count.complete_count():
            return self.update_count(count)
        return False
    
    def approve_count(self, count_id: int, user_id: int, user_name: str) -> bool:
        """اعتماد الجرد"""
        count = self.get_count_by_id(count_id)
        if not count:
            return False
        
        if count.approve(user_id, user_name):
            success = self.update_count(count)
            
            # إنشاء تسويات تلقائية للفروقات
            if success:
                self.create_adjustments_from_count(count_id, user_id, user_name)
            
            return success
        return False
    
    def cancel_count(self, count_id: int) -> bool:
        """إلغاء الجرد"""
        count = self.get_count_by_id(count_id)
        if not count:
            return False
        
        if count.cancel():
            return self.update_count(count)
        return False
    
    # ==================== Count Items ====================
    
    def add_count_item(self, item: CountItem) -> int:
        """إضافة عنصر للجرد"""
        query = """
            INSERT INTO count_items (
                count_id, product_id, product_code, product_name, product_barcode,
                system_quantity, counted_quantity, variance_quantity,
                unit_cost, system_value, counted_value, variance_value,
                location, batch_number, notes, is_counted, requires_recount,
                counted_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        item.created_at = datetime.now()
        return self.db.execute_query(
            query,
            (
                item.count_id, item.product_id, item.product_code,
                item.product_name, item.product_barcode,
                item.system_quantity, item.counted_quantity, item.variance_quantity,
                item.unit_cost, item.system_value, item.counted_value,
                item.variance_value, item.location, item.batch_number,
                item.notes, item.is_counted, item.requires_recount,
                item.counted_at, item.created_at
            )
        )
    
    def get_count_items(self, count_id: int) -> List[CountItem]:
        """الحصول على عناصر الجرد"""
        query = """
            SELECT * FROM count_items
            WHERE count_id = ?
            ORDER BY product_code
        """
        
        rows = self.db.fetch_all(query, (count_id,))
        return [self._row_to_count_item(row) for row in rows]
    
    def update_count_item(self, item: CountItem) -> bool:
        """تحديث عنصر جرد"""
        query = """
            UPDATE count_items SET
                counted_quantity = ?,
                variance_quantity = ?,
                counted_value = ?,
                variance_value = ?,
                notes = ?,
                is_counted = ?,
                requires_recount = ?,
                counted_at = ?
            WHERE id = ?
        """
        
        result = self.db.execute_query(
            query,
            (
                item.counted_quantity, item.variance_quantity,
                item.counted_value, item.variance_value,
                item.notes, item.is_counted, item.requires_recount,
                item.counted_at, item.id
            )
        )
        
        return result > 0
    
    def load_products_for_count(
        self,
        count_id: int,
        location: Optional[str] = None,
        category_id: Optional[int] = None
    ) -> int:
        """تحميل المنتجات للجرد"""
        query = """
            SELECT 
                p.id, p.sku, p.name, p.barcode,
                p.current_stock, p.cost_price
            FROM products p
            WHERE p.is_active = 1
        """
        params = []
        
        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)
        
        rows = self.db.fetch_all(query, tuple(params))
        
        items_added = 0
        for row in rows:
            item = CountItem(
                count_id=count_id,
                product_id=row['id'],
                product_code=row['sku'],
                product_name=row['name'],
                product_barcode=row['barcode'],
                system_quantity=Decimal(str(row['current_stock'])),
                unit_cost=Decimal(str(row['cost_price'])),
                location=location
            )
            item.system_value = item.system_quantity * item.unit_cost
            
            self.add_count_item(item)
            items_added += 1
        
        # تحديث إحصائيات الجرد
        count = self.get_count_by_id(count_id)
        if count:
            count.total_items = items_added
            self.update_count(count)
        
        return items_added
    
    # ==================== Stock Adjustments ====================
    
    def create_adjustment(self, adjustment: StockAdjustment) -> int:
        """إنشاء تسوية"""
        query = """
            INSERT INTO stock_adjustments (
                adjustment_number, adjustment_date, adjustment_type, reason,
                product_id, product_code, product_name,
                quantity_before, adjustment_quantity, quantity_after,
                unit_cost, adjustment_value,
                location, batch_number, count_id,
                status, created_by, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        adjustment.created_at = datetime.now()
        adjustment.calculate_after_quantity()
        
        return self.db.execute_query(
            query,
            (
                adjustment.adjustment_number, adjustment.adjustment_date,
                adjustment.adjustment_type.value, adjustment.reason,
                adjustment.product_id, adjustment.product_code, adjustment.product_name,
                adjustment.quantity_before, adjustment.adjustment_quantity,
                adjustment.quantity_after, adjustment.unit_cost, adjustment.adjustment_value,
                adjustment.location, adjustment.batch_number, adjustment.count_id,
                adjustment.status.value, adjustment.created_by,
                adjustment.notes, adjustment.created_at
            )
        )
    
    def get_adjustment_by_id(self, adjustment_id: int) -> Optional[StockAdjustment]:
        """الحصول على تسوية بالمعرف"""
        query = """
            SELECT 
                sa.*,
                u1.username as created_by_name,
                u2.username as approved_by_name
            FROM stock_adjustments sa
            LEFT JOIN users u1 ON sa.created_by = u1.id
            LEFT JOIN users u2 ON sa.approved_by = u2.id
            WHERE sa.id = ?
        """
        
        row = self.db.fetch_one(query, (adjustment_id,))
        if not row:
            return None
        
        return self._row_to_adjustment(row)
    
    def get_all_adjustments(
        self,
        status: Optional[AdjustmentStatus] = None,
        adjustment_type: Optional[AdjustmentType] = None,
        product_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[StockAdjustment]:
        """الحصول على جميع التسويات مع فلاتر"""
        query = """
            SELECT 
                sa.*,
                u1.username as created_by_name,
                u2.username as approved_by_name
            FROM stock_adjustments sa
            LEFT JOIN users u1 ON sa.created_by = u1.id
            LEFT JOIN users u2 ON sa.approved_by = u2.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND sa.status = ?"
            params.append(status.value)
        
        if adjustment_type:
            query += " AND sa.adjustment_type = ?"
            params.append(adjustment_type.value)
        
        if product_id:
            query += " AND sa.product_id = ?"
            params.append(product_id)
        
        if from_date:
            query += " AND sa.adjustment_date >= ?"
            params.append(from_date)
        
        if to_date:
            query += " AND sa.adjustment_date <= ?"
            params.append(to_date)
        
        query += " ORDER BY sa.adjustment_date DESC, sa.id DESC"
        
        rows = self.db.fetch_all(query, tuple(params))
        return [self._row_to_adjustment(row) for row in rows]
    
    def approve_adjustment(
        self,
        adjustment_id: int,
        user_id: int,
        user_name: str,
        apply_immediately: bool = True
    ) -> bool:
        """اعتماد تسوية"""
        adjustment = self.get_adjustment_by_id(adjustment_id)
        if not adjustment:
            return False
        
        if adjustment.approve(user_id, user_name):
            query = """
                UPDATE stock_adjustments SET
                    status = ?, approved_by = ?, approved_at = ?, updated_at = ?
                WHERE id = ?
            """
            
            adjustment.updated_at = datetime.now()
            self.db.execute_query(
                query,
                (
                    adjustment.status.value,
                    adjustment.approved_by,
                    adjustment.approved_at,
                    adjustment.updated_at,
                    adjustment.id
                )
            )
            
            # تطبيق التسوية على المخزون
            if apply_immediately:
                self.apply_adjustment(adjustment_id)
            
            return True
        return False
    
    def reject_adjustment(
        self,
        adjustment_id: int,
        user_id: int,
        user_name: str,
        reason: str
    ) -> bool:
        """رفض تسوية"""
        adjustment = self.get_adjustment_by_id(adjustment_id)
        if not adjustment:
            return False
        
        if adjustment.reject(user_id, user_name, reason):
            query = """
                UPDATE stock_adjustments SET
                    status = ?, approved_by = ?, approved_at = ?,
                    rejection_reason = ?, updated_at = ?
                WHERE id = ?
            """
            
            adjustment.updated_at = datetime.now()
            self.db.execute_query(
                query,
                (
                    adjustment.status.value,
                    adjustment.approved_by,
                    adjustment.approved_at,
                    adjustment.rejection_reason,
                    adjustment.updated_at,
                    adjustment.id
                )
            )
            return True
        return False
    
    def apply_adjustment(self, adjustment_id: int) -> bool:
        """تطبيق التسوية على المخزون"""
        adjustment = self.get_adjustment_by_id(adjustment_id)
        if not adjustment or not adjustment.can_be_applied:
            return False
        
        # تحديث كمية المنتج
        query = """
            UPDATE products SET
                current_stock = current_stock + ?,
                updated_at = ?
            WHERE id = ?
        """
        
        now = datetime.now()
        self.db.execute_query(
            query,
            (adjustment.adjustment_quantity, now, adjustment.product_id)
        )
        
        # وضع علامة مطبقة
        adjustment.mark_applied()
        update_query = """
            UPDATE stock_adjustments SET
                status = ?, applied_at = ?, updated_at = ?
            WHERE id = ?
        """
        
        self.db.execute_query(
            update_query,
            (adjustment.status.value, adjustment.applied_at, now, adjustment.id)
        )
        
        return True
    
    def create_adjustments_from_count(
        self,
        count_id: int,
        user_id: int,
        user_name: str
    ) -> int:
        """إنشاء تسويات من الجرد"""
        count = self.get_count_by_id(count_id)
        if not count or count.status != CountStatus.APPROVED:
            return 0
        
        adjustments_created = 0
        for item in count.items:
            if item.has_variance:
                # إنشاء تسوية
                adjustment = StockAdjustment(
                    adjustment_number=f"ADJ-{count.count_number}-{item.product_code}",
                    adjustment_date=date.today(),
                    adjustment_type=AdjustmentType.COUNT_ADJUSTMENT,
                    reason=f"تسوية من الجرد {count.count_number}",
                    product_id=item.product_id,
                    product_code=item.product_code,
                    product_name=item.product_name,
                    quantity_before=item.system_quantity,
                    adjustment_quantity=item.variance_quantity,
                    unit_cost=item.unit_cost,
                    location=item.location,
                    batch_number=item.batch_number,
                    count_id=count_id,
                    status=AdjustmentStatus.APPROVED,  # معتمدة مباشرة
                    created_by=user_id,
                    created_by_name=user_name,
                    approved_by=user_id,
                    approved_by_name=user_name,
                    approved_at=datetime.now(),
                    notes=f"تسوية تلقائية من الجرد رقم {count.count_number}"
                )
                
                adj_id = self.create_adjustment(adjustment)
                if adj_id:
                    # تطبيق التسوية مباشرة
                    self.apply_adjustment(adj_id)
                    adjustments_created += 1
        
        return adjustments_created
    
    # ==================== Reports & Statistics ====================
    
    def get_count_summary(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """ملخص الجرود"""
        query = """
            SELECT 
                COUNT(*) as total_counts,
                SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) as draft_counts,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_counts,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_counts,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_counts,
                SUM(total_items) as total_items,
                SUM(items_with_variance) as items_with_variance,
                SUM(total_variance_value) as total_variance_value
            FROM physical_counts
            WHERE 1=1
        """
        params = []
        
        if from_date:
            query += " AND count_date >= ?"
            params.append(from_date)
        
        if to_date:
            query += " AND count_date <= ?"
            params.append(to_date)
        
        row = self.db.fetch_one(query, tuple(params))
        return dict(row) if row else {}
    
    def get_adjustment_summary(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """ملخص التسويات"""
        query = """
            SELECT 
                COUNT(*) as total_adjustments,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_adjustments,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_adjustments,
                SUM(CASE WHEN status = 'applied' THEN 1 ELSE 0 END) as applied_adjustments,
                SUM(CASE WHEN adjustment_quantity > 0 THEN adjustment_quantity ELSE 0 END) as total_increases,
                SUM(CASE WHEN adjustment_quantity < 0 THEN ABS(adjustment_quantity) ELSE 0 END) as total_decreases,
                SUM(adjustment_value) as total_value
            FROM stock_adjustments
            WHERE 1=1
        """
        params = []
        
        if from_date:
            query += " AND adjustment_date >= ?"
            params.append(from_date)
        
        if to_date:
            query += " AND adjustment_date <= ?"
            params.append(to_date)
        
        row = self.db.fetch_one(query, tuple(params))
        return dict(row) if row else {}
    
    # ==================== Helper Methods ====================
    
    def _row_to_count(self, row: Dict) -> PhysicalCount:
        """تحويل صف إلى PhysicalCount"""
        return PhysicalCount(
            id=row['id'],
            count_number=row['count_number'],
            count_date=row['count_date'],
            scheduled_date=row.get('scheduled_date'),
            description=row.get('description', ''),
            location=row.get('location'),
            counted_by=row.get('counted_by'),
            counted_by_name=row.get('counted_by_name'),
            status=CountStatus(row['status']),
            approved_by=row.get('approved_by'),
            approved_by_name=row.get('approved_by_name'),
            approved_at=row.get('approved_at'),
            total_items=row.get('total_items', 0),
            counted_items=row.get('counted_items', 0),
            items_with_variance=row.get('items_with_variance', 0),
            total_variance_value=Decimal(str(row.get('total_variance_value', 0))),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            completed_at=row.get('completed_at'),
            notes=row.get('notes', '')
        )
    
    def _row_to_count_item(self, row: Dict) -> CountItem:
        """تحويل صف إلى CountItem"""
        return CountItem(
            id=row['id'],
            count_id=row['count_id'],
            product_id=row['product_id'],
            product_code=row['product_code'],
            product_name=row['product_name'],
            product_barcode=row.get('product_barcode'),
            system_quantity=Decimal(str(row['system_quantity'])),
            counted_quantity=Decimal(str(row['counted_quantity'])) if row.get('counted_quantity') is not None else None,
            variance_quantity=Decimal(str(row.get('variance_quantity', 0))),
            unit_cost=Decimal(str(row['unit_cost'])),
            system_value=Decimal(str(row.get('system_value', 0))),
            counted_value=Decimal(str(row.get('counted_value', 0))),
            variance_value=Decimal(str(row.get('variance_value', 0))),
            location=row.get('location'),
            batch_number=row.get('batch_number'),
            notes=row.get('notes', ''),
            is_counted=bool(row.get('is_counted', 0)),
            requires_recount=bool(row.get('requires_recount', 0)),
            counted_at=row.get('counted_at'),
            created_at=row.get('created_at')
        )
    
    def _row_to_adjustment(self, row: Dict) -> StockAdjustment:
        """تحويل صف إلى StockAdjustment"""
        return StockAdjustment(
            id=row['id'],
            adjustment_number=row['adjustment_number'],
            adjustment_date=row['adjustment_date'],
            adjustment_type=AdjustmentType(row['adjustment_type']),
            reason=row.get('reason', ''),
            product_id=row['product_id'],
            product_code=row['product_code'],
            product_name=row['product_name'],
            quantity_before=Decimal(str(row['quantity_before'])),
            adjustment_quantity=Decimal(str(row['adjustment_quantity'])),
            quantity_after=Decimal(str(row.get('quantity_after', 0))),
            unit_cost=Decimal(str(row['unit_cost'])),
            adjustment_value=Decimal(str(row.get('adjustment_value', 0))),
            location=row.get('location'),
            batch_number=row.get('batch_number'),
            count_id=row.get('count_id'),
            status=AdjustmentStatus(row['status']),
            created_by=row.get('created_by'),
            created_by_name=row.get('created_by_name'),
            approved_by=row.get('approved_by'),
            approved_by_name=row.get('approved_by_name'),
            approved_at=row.get('approved_at'),
            rejection_reason=row.get('rejection_reason'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            applied_at=row.get('applied_at'),
            notes=row.get('notes', '')
        )
    
    def generate_count_number(self) -> str:
        """توليد رقم جرد"""
        query = "SELECT COUNT(*) as count FROM physical_counts"
        row = self.db.fetch_one(query)
        count = row['count'] if row else 0
        return f"CNT-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
    
    def generate_adjustment_number(self) -> str:
        """توليد رقم تسوية"""
        query = "SELECT COUNT(*) as count FROM stock_adjustments"
        row = self.db.fetch_one(query)
        count = row['count'] if row else 0
        return f"ADJ-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
