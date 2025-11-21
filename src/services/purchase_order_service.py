#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة أوامر الشراء
Purchase Order Service
"""

import sqlite3
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.purchase_order import (
    PurchaseOrder, PurchaseOrderItem, POStatus, 
    POPriority, DeliveryTerms, PaymentTerms
)
from models.receiving_note import (
    ReceivingNote, ReceivingItem, SupplierEvaluation,
    ReceivingStatus, InspectionStatus, QualityRating
)
from core.database_manager import DatabaseManager


class PurchaseOrderService:
    """خدمة إدارة أوامر الشراء"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    # ===================== إنشاء وإدارة أوامر الشراء =====================
    
    def generate_po_number(self) -> str:
        """توليد رقم أمر شراء"""
        today = date.today()
        prefix = f"PO-{today.year}{today.month:02d}"
        
        query = """
        SELECT po_number FROM purchase_orders 
        WHERE po_number LIKE ? 
        ORDER BY po_number DESC LIMIT 1
        """
        
        result = self.db.execute_query(query, (f"{prefix}%",))
        
        if result and result[0][0]:
            last_number = result[0][0]
            sequence = int(last_number.split('-')[-1]) + 1
        else:
            sequence = 1
        
        return f"{prefix}-{sequence:04d}"
    
    def create_purchase_order(self, po: PurchaseOrder) -> int:
        """إنشاء أمر شراء جديد"""
        if not po.po_number:
            po.po_number = self.generate_po_number()
        
        if not po.order_date:
            po.order_date = date.today()
        
        po.created_at = datetime.now()
        po.updated_at = datetime.now()
        
        # حفظ أمر الشراء
        query = """
        INSERT INTO purchase_orders (
            po_number, supplier_id, supplier_name, supplier_contact,
            order_date, required_date, delivery_date, expected_delivery_date,
            status, priority, delivery_terms, payment_terms, currency,
            subtotal, discount_amount, tax_amount, shipping_cost, total_amount,
            notes, terms_conditions, shipping_address, billing_address,
            approved_by, approval_date, sent_date, confirmed_date,
            created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            po.po_number, po.supplier_id, po.supplier_name, po.supplier_contact,
            po.order_date.isoformat() if po.order_date else None,
            po.required_date.isoformat() if po.required_date else None,
            po.delivery_date.isoformat() if po.delivery_date else None,
            po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
            po.status.name if isinstance(po.status, POStatus) else po.status,
            po.priority.name if isinstance(po.priority, POPriority) else po.priority,
            po.delivery_terms.name if isinstance(po.delivery_terms, DeliveryTerms) else po.delivery_terms,
            po.payment_terms.name if isinstance(po.payment_terms, PaymentTerms) else po.payment_terms,
            po.currency,
            float(po.subtotal), float(po.discount_amount), float(po.tax_amount),
            float(po.shipping_cost), float(po.total_amount),
            po.notes, po.terms_conditions, po.shipping_address, po.billing_address,
            po.approved_by,
            po.approval_date.isoformat() if po.approval_date else None,
            po.sent_date.isoformat() if po.sent_date else None,
            po.confirmed_date.isoformat() if po.confirmed_date else None,
            po.created_by,
            po.created_at.isoformat() if po.created_at else None,
            po.updated_at.isoformat() if po.updated_at else None
        )
        
        po_id = self.db.execute_update(query, params)
        
        # حفظ البنود
        for item in po.items:
            self._save_po_item(po_id, item)
        
        return po_id
    
    def _save_po_item(self, po_id: int, item: PurchaseOrderItem) -> int:
        """حفظ بند أمر شراء"""
        query = """
        INSERT INTO purchase_order_items (
            purchase_order_id, product_id, product_name, product_code,
            quantity_ordered, quantity_received, quantity_pending,
            unit_price, discount_percent, tax_percent,
            subtotal, discount_amount, tax_amount, net_amount,
            required_date, expected_delivery_date, actual_delivery_date,
            specifications, quality_requirements, packaging_requirements,
            notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            po_id, item.product_id, item.product_name, item.product_code,
            float(item.quantity_ordered), float(item.quantity_received), float(item.quantity_pending),
            float(item.unit_price), float(item.discount_percent), float(item.tax_percent),
            float(item.subtotal), float(item.discount_amount), float(item.tax_amount), float(item.net_amount),
            item.required_date.isoformat() if item.required_date else None,
            item.expected_delivery_date.isoformat() if item.expected_delivery_date else None,
            item.actual_delivery_date.isoformat() if item.actual_delivery_date else None,
            item.specifications, item.quality_requirements, item.packaging_requirements,
            item.notes, datetime.now().isoformat()
        )
        
        return self.db.execute_update(query, params)
    
    def get_purchase_order(self, po_id: int) -> Optional[PurchaseOrder]:
        """الحصول على أمر شراء"""
        query = """
        SELECT * FROM purchase_orders WHERE id = ?
        """
        
        result = self.db.execute_query(query, (po_id,))
        if not result:
            return None
        
        po_data = self._row_to_dict(result[0])
        po = PurchaseOrder.from_dict(po_data)
        
        # تحميل البنود
        items_query = """
        SELECT * FROM purchase_order_items WHERE purchase_order_id = ?
        """
        items_result = self.db.execute_query(items_query, (po_id,))
        
        for item_row in items_result:
            item_data = self._row_to_dict(item_row)
            po.items.append(PurchaseOrderItem.from_dict(item_data))
        
        return po
    
    def update_purchase_order(self, po: PurchaseOrder) -> bool:
        """تحديث أمر شراء"""
        po.updated_at = datetime.now()
        
        query = """
        UPDATE purchase_orders SET
            supplier_id = ?, supplier_name = ?, supplier_contact = ?,
            order_date = ?, required_date = ?, delivery_date = ?, expected_delivery_date = ?,
            status = ?, priority = ?, delivery_terms = ?, payment_terms = ?, currency = ?,
            subtotal = ?, discount_amount = ?, tax_amount = ?, shipping_cost = ?, total_amount = ?,
            notes = ?, terms_conditions = ?, shipping_address = ?, billing_address = ?,
            approved_by = ?, approval_date = ?, sent_date = ?, confirmed_date = ?,
            updated_at = ?
        WHERE id = ?
        """
        
        params = (
            po.supplier_id, po.supplier_name, po.supplier_contact,
            po.order_date.isoformat() if po.order_date else None,
            po.required_date.isoformat() if po.required_date else None,
            po.delivery_date.isoformat() if po.delivery_date else None,
            po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
            po.status.name if isinstance(po.status, POStatus) else po.status,
            po.priority.name if isinstance(po.priority, POPriority) else po.priority,
            po.delivery_terms.name if isinstance(po.delivery_terms, DeliveryTerms) else po.delivery_terms,
            po.payment_terms.name if isinstance(po.payment_terms, PaymentTerms) else po.payment_terms,
            po.currency,
            float(po.subtotal), float(po.discount_amount), float(po.tax_amount),
            float(po.shipping_cost), float(po.total_amount),
            po.notes, po.terms_conditions, po.shipping_address, po.billing_address,
            po.approved_by,
            po.approval_date.isoformat() if po.approval_date else None,
            po.sent_date.isoformat() if po.sent_date else None,
            po.confirmed_date.isoformat() if po.confirmed_date else None,
            po.updated_at.isoformat(),
            po.id
        )
        
        self.db.execute_update(query, params)
        
        # تحديث البنود (حذف وإعادة الإدخال)
        delete_items = "DELETE FROM purchase_order_items WHERE purchase_order_id = ?"
        self.db.execute_update(delete_items, (po.id,))
        
        for item in po.items:
            self._save_po_item(po.id, item)
        
        return True
    
    def delete_purchase_order(self, po_id: int) -> bool:
        """حذف أمر شراء (soft delete)"""
        query = "UPDATE purchase_orders SET status = ? WHERE id = ?"
        self.db.execute_update(query, (POStatus.CANCELLED.name, po_id))
        return True
    
    # ===================== البحث والتصفية =====================
    
    def get_all_purchase_orders(
        self, 
        status: Optional[POStatus] = None,
        supplier_id: Optional[int] = None,
        priority: Optional[POPriority] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PurchaseOrder]:
        """الحصول على قائمة أوامر الشراء"""
        query = "SELECT * FROM purchase_orders WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status.name if isinstance(status, POStatus) else status)
        
        if supplier_id:
            query += " AND supplier_id = ?"
            params.append(supplier_id)
        
        if priority:
            query += " AND priority = ?"
            params.append(priority.name if isinstance(priority, POPriority) else priority)
        
        if from_date:
            query += " AND order_date >= ?"
            params.append(from_date.isoformat())
        
        if to_date:
            query += " AND order_date <= ?"
            params.append(to_date.isoformat())
        
        query += " ORDER BY order_date DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        results = self.db.execute_query(query, tuple(params))
        
        pos = []
        for row in results:
            po_data = self._row_to_dict(row)
            po = PurchaseOrder.from_dict(po_data)
            
            # تحميل البنود
            items_query = "SELECT * FROM purchase_order_items WHERE purchase_order_id = ?"
            items_result = self.db.execute_query(items_query, (po.id,))
            for item_row in items_result:
                item_data = self._row_to_dict(item_row)
                po.items.append(PurchaseOrderItem.from_dict(item_data))
            
            pos.append(po)
        
        return pos
    
    def get_pending_approvals(self) -> List[PurchaseOrder]:
        """الحصول على أوامر الشراء المعلقة للموافقة"""
        return self.get_all_purchase_orders(status=POStatus.PENDING_APPROVAL)
    
    def get_overdue_pos(self) -> List[PurchaseOrder]:
        """الحصول على أوامر الشراء المتأخرة"""
        query = """
        SELECT * FROM purchase_orders 
        WHERE status NOT IN (?, ?, ?)
        AND required_date < date('now')
        ORDER BY required_date
        """
        
        params = (POStatus.CLOSED.name, POStatus.CANCELLED.name, POStatus.FULLY_RECEIVED.name)
        results = self.db.execute_query(query, params)
        
        pos = []
        for row in results:
            po_data = self._row_to_dict(row)
            po = PurchaseOrder.from_dict(po_data)
            
            items_query = "SELECT * FROM purchase_order_items WHERE purchase_order_id = ?"
            items_result = self.db.execute_query(items_query, (po.id,))
            for item_row in items_result:
                item_data = self._row_to_dict(item_row)
                po.items.append(PurchaseOrderItem.from_dict(item_data))
            
            pos.append(po)
        
        return pos
    
    # ===================== سير العمل =====================
    
    def submit_for_approval(self, po_id: int, submitted_by: int) -> bool:
        """تقديم أمر شراء للموافقة"""
        po = self.get_purchase_order(po_id)
        if po and po.submit_for_approval():
            self.update_purchase_order(po)
            return True
        return False
    
    def approve_purchase_order(self, po_id: int, approved_by: int, notes: Optional[str] = None) -> bool:
        """الموافقة على أمر شراء"""
        po = self.get_purchase_order(po_id)
        if po and po.approve(approved_by, notes):
            self.update_purchase_order(po)
            return True
        return False
    
    def send_to_supplier(self, po_id: int) -> bool:
        """إرسال أمر شراء إلى المورد"""
        po = self.get_purchase_order(po_id)
        if po and po.send_to_supplier():
            self.update_purchase_order(po)
            # هنا يمكن إضافة إرسال بريد إلكتروني
            return True
        return False
    
    def confirm_by_supplier(self, po_id: int) -> bool:
        """تأكيد أمر الشراء من المورد"""
        po = self.get_purchase_order(po_id)
        if po and po.confirm_by_supplier():
            self.update_purchase_order(po)
            return True
        return False
    
    # ===================== الاستلام =====================
    
    def create_receiving_note(self, rn: ReceivingNote) -> int:
        """إنشاء إشعار استلام"""
        if not rn.receiving_number:
            rn.receiving_number = self._generate_receiving_number()
        
        if not rn.receiving_date:
            rn.receiving_date = date.today()
        
        rn.created_at = datetime.now()
        
        query = """
        INSERT INTO receiving_notes (
            receiving_number, purchase_order_id, po_number,
            supplier_id, supplier_name,
            shipment_number, carrier_name, tracking_number,
            receiving_date, shipment_date, expected_date,
            status, received_by, receiver_name,
            notes, discrepancy_notes,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            rn.receiving_number, rn.purchase_order_id, rn.po_number,
            rn.supplier_id, rn.supplier_name,
            rn.shipment_number, rn.carrier_name, rn.tracking_number,
            rn.receiving_date.isoformat() if rn.receiving_date else None,
            rn.shipment_date.isoformat() if rn.shipment_date else None,
            rn.expected_date.isoformat() if rn.expected_date else None,
            rn.status.name if isinstance(rn.status, ReceivingStatus) else rn.status,
            rn.received_by, rn.receiver_name,
            rn.notes, rn.discrepancy_notes,
            rn.created_at.isoformat() if rn.created_at else None,
            rn.updated_at.isoformat() if rn.updated_at else None
        )
        
        rn_id = self.db.execute_update(query, params)
        
        # حفظ البنود
        for item in rn.items:
            self._save_receiving_item(rn_id, item)
        
        return rn_id
    
    def _save_receiving_item(self, rn_id: int, item: ReceivingItem) -> int:
        """حفظ بند استلام"""
        query = """
        INSERT INTO receiving_items (
            receiving_id, po_item_id, product_id, product_name, product_code,
            quantity_ordered, quantity_received, quantity_accepted, quantity_rejected, quantity_damaged,
            inspection_status, quality_rating, inspection_notes, inspector_name, inspection_date,
            warehouse_location, batch_number, serial_numbers, expiry_date,
            matches_specifications, variance_reason, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            rn_id, item.po_item_id, item.product_id, item.product_name, item.product_code,
            float(item.quantity_ordered), float(item.quantity_received), float(item.quantity_accepted),
            float(item.quantity_rejected), float(item.quantity_damaged),
            item.inspection_status.name if isinstance(item.inspection_status, InspectionStatus) else item.inspection_status,
            item.quality_rating.name if isinstance(item.quality_rating, QualityRating) else item.quality_rating if item.quality_rating else None,
            item.inspection_notes, item.inspector_name,
            item.inspection_date.isoformat() if item.inspection_date else None,
            item.warehouse_location, item.batch_number, item.serial_numbers,
            item.expiry_date.isoformat() if item.expiry_date else None,
            item.matches_specifications, item.variance_reason, item.notes
        )
        
        return self.db.execute_update(query, params)
    
    def _generate_receiving_number(self) -> str:
        """توليد رقم استلام"""
        today = date.today()
        prefix = f"RN-{today.year}{today.month:02d}"
        
        query = """
        SELECT receiving_number FROM receiving_notes 
        WHERE receiving_number LIKE ? 
        ORDER BY receiving_number DESC LIMIT 1
        """
        
        result = self.db.execute_query(query, (f"{prefix}%",))
        
        if result and result[0][0]:
            last_number = result[0][0]
            sequence = int(last_number.split('-')[-1]) + 1
        else:
            sequence = 1
        
        return f"{prefix}-{sequence:04d}"
    
    def receive_shipment(self, po_id: int, receiving_note: ReceivingNote) -> bool:
        """استلام شحنة"""
        # إنشاء إشعار الاستلام
        rn_id = self.create_receiving_note(receiving_note)
        
        # تحديث كميات أمر الشراء
        po = self.get_purchase_order(po_id)
        if not po:
            return False
        
        for rn_item in receiving_note.items:
            for po_item in po.items:
                if po_item.id == rn_item.po_item_id:
                    po_item.receive_quantity(rn_item.quantity_accepted)
                    break
        
        # تحديث حالة أمر الشراء
        po.receive_shipment(receiving_note.items)
        self.update_purchase_order(po)
        
        return True
    
    # ===================== التقييم =====================
    
    def create_supplier_evaluation(self, evaluation: SupplierEvaluation) -> int:
        """إنشاء تقييم مورد"""
        evaluation.created_at = datetime.now()
        evaluation.calculate_metrics()
        
        query = """
        INSERT INTO supplier_evaluations (
            supplier_id, supplier_name,
            evaluation_period_start, evaluation_period_end,
            quality_score, delivery_score, pricing_score, communication_score, reliability_score,
            total_orders, completed_orders, on_time_deliveries, late_deliveries,
            rejected_shipments, total_value,
            on_time_delivery_rate, quality_acceptance_rate, average_lead_time_days,
            overall_score, grade,
            is_approved, is_preferred,
            notes, recommendations,
            evaluated_by, evaluation_date, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            evaluation.supplier_id, evaluation.supplier_name,
            evaluation.evaluation_period_start.isoformat() if evaluation.evaluation_period_start else None,
            evaluation.evaluation_period_end.isoformat() if evaluation.evaluation_period_end else None,
            float(evaluation.quality_score), float(evaluation.delivery_score), float(evaluation.pricing_score),
            float(evaluation.communication_score), float(evaluation.reliability_score),
            evaluation.total_orders, evaluation.completed_orders, evaluation.on_time_deliveries,
            evaluation.late_deliveries, evaluation.rejected_shipments, float(evaluation.total_value),
            float(evaluation.on_time_delivery_rate), float(evaluation.quality_acceptance_rate),
            float(evaluation.average_lead_time_days),
            float(evaluation.overall_score), evaluation.grade,
            evaluation.is_approved, evaluation.is_preferred,
            evaluation.notes, evaluation.recommendations,
            evaluation.evaluated_by,
            evaluation.evaluation_date.isoformat() if evaluation.evaluation_date else None,
            evaluation.created_at.isoformat() if evaluation.created_at else None
        )
        
        return self.db.execute_update(query, params)
    
    def get_supplier_evaluations(self, supplier_id: int) -> List[SupplierEvaluation]:
        """الحصول على تقييمات مورد"""
        query = """
        SELECT * FROM supplier_evaluations 
        WHERE supplier_id = ? 
        ORDER BY evaluation_date DESC
        """
        
        results = self.db.execute_query(query, (supplier_id,))
        
        evaluations = []
        for row in results:
            eval_data = self._row_to_dict(row)
            evaluations.append(SupplierEvaluation.from_dict(eval_data))
        
        return evaluations
    
    # ===================== الإحصائيات =====================
    
    def get_po_statistics(self, from_date: Optional[date] = None, to_date: Optional[date] = None) -> Dict[str, Any]:
        """إحصائيات أوامر الشراء"""
        query_base = "SELECT COUNT(*), SUM(total_amount) FROM purchase_orders WHERE 1=1"
        params = []
        
        if from_date:
            query_base += " AND order_date >= ?"
            params.append(from_date.isoformat())
        
        if to_date:
            query_base += " AND order_date <= ?"
            params.append(to_date.isoformat())
        
        # إجمالي
        result = self.db.execute_query(query_base, tuple(params))
        total_count = result[0][0] if result and result[0][0] else 0
        total_value = result[0][1] if result and result[0][1] else 0
        
        # حسب الحالة
        status_query = query_base + " AND status = ?"
        by_status = {}
        for status in POStatus:
            status_params = params + [status.name]
            result = self.db.execute_query(status_query, tuple(status_params))
            count = result[0][0] if result and result[0][0] else 0
            value = result[0][1] if result and result[0][1] else 0
            by_status[status.value] = {'count': count, 'value': float(value)}
        
        return {
            'total_pos': total_count,
            'total_value': float(total_value),
            'by_status': by_status
        }
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """تحويل صف إلى قاموس"""
        if not row:
            return {}
        
        cursor = self.db.conn.cursor()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        return dict(zip(columns, row))
