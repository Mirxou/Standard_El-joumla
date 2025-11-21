#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة إدارة الموردين (Vendor Service)
تدير سجلات الموردين، أوامر الشراء، واستعراض أداء المورد
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

class VendorService:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger

    def create_vendor(self, vendor_data: Dict[str, Any]) -> Optional[int]:
        try:
            now = datetime.now()
            q = ('INSERT INTO suppliers (name, contact_person, phone, email, address, payment_terms, credit_limit, created_at, updated_at) '
                 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)')
            params = (
                vendor_data.get('name'), vendor_data.get('contact_person'), vendor_data.get('phone'),
                vendor_data.get('email'), vendor_data.get('address'), vendor_data.get('payment_terms', 'نقدي'),
                float(vendor_data.get('credit_limit', 0)), now, now
            )
            res = self.db.execute_query(q, params)
            if res and hasattr(res, 'lastrowid'):
                return res.lastrowid
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في إنشاء مورد: {e}')
        return None

    def get_vendor(self, vendor_id: int) -> Optional[Dict[str, Any]]:
        try:
            row = self.db.fetch_one('SELECT * FROM suppliers WHERE id = ?', (vendor_id,))
            return row
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في جلب مورد {vendor_id}: {e}')
            return None

    def search_vendors(self, term: str) -> List[Dict[str, Any]]:
        try:
            like = f'%{term}%'
            rows = self.db.fetch_all('SELECT * FROM suppliers WHERE name LIKE ? OR contact_person LIKE ? OR phone LIKE ? OR email LIKE ?', (like, like, like, like))
            return rows
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في البحث عن موردين: {e}')
            return []

    def create_purchase_order(self, vendor_id: int, items: List[Dict[str, Any]], meta: Dict[str, Any] = None) -> Optional[int]:
        try:
            now = datetime.now()
            total = sum(float(i.get('quantity',1)) * float(i.get('unit_cost',0)) for i in items)
            q = 'INSERT INTO purchases (supplier_id, status, total_amount, created_at, updated_at, meta) VALUES (?, ?, ?, ?, ?, ?)'
            res = self.db.execute_query(q, (vendor_id, 'ordered', total, now, now, str(meta or {})))
            if not res or not hasattr(res, 'lastrowid'):
                return None
            po_id = res.lastrowid
            for it in items:
                self.db.execute_query('INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_cost) VALUES (?, ?, ?, ?)', (po_id, it.get('product_id'), it.get('quantity',1), float(it.get('unit_cost',0))))
            if self.logger:
                self.logger.info(f'تم إنشاء أمر شراء ID={po_id} للمورد {vendor_id}، المجموع={total}')
            return po_id
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في إنشاء أمر الشراء: {e}')
            return None

    def receive_purchase(self, purchase_id: int, received_items: List[Dict[str, Any]]) -> bool:
        try:
            # تحديث حالة المورد
            self.db.execute_query('UPDATE purchases SET status = ?, updated_at = ? WHERE id = ?', ('received', datetime.now(), purchase_id))
            for it in received_items:
                # تسجيل استلام البند وتحديث المخزون
                self.db.execute_query('INSERT INTO purchase_receipts (purchase_id, product_id, quantity, unit_cost, received_at) VALUES (?, ?, ?, ?, ?)', (purchase_id, it.get('product_id'), it.get('quantity',1), float(it.get('unit_cost',0)), datetime.now()))
                # إذا كانت خدمة المخزون متاحة، سجل حركة شراء
                try:
                    from src.services.inventory_service_enhanced import InventoryService, StockMovement
                    # استخدام مدير قاعدة البيانات الحالي لإنشاء كائن خدمة مؤقت
                    inv = InventoryService(self.db, self.logger)
                    movement = StockMovement(product_id=it.get('product_id'), movement_type='شراء', quantity=int(it.get('quantity',1)), reference_id=purchase_id, reference_type='purchase')
                    inv.record_stock_movement(movement)
                except Exception:
                    if self.logger:
                        self.logger.debug('تعذر تسوية المخزون عبر InventoryService أثناء استلام الشراء')
            if self.logger:
                self.logger.info(f'تم استلام أمر الشراء {purchase_id}')
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في استلام أمر الشراء {purchase_id}: {e}')
            return False

    def vendor_performance(self, vendor_id: int) -> Dict[str, Any]:
        try:
            # احصائيات بسيطة: متوسط زمن الاستجابة، نسبة التسليم في الموعد
            q_avg = 'SELECT AVG(julianday(received_at) - julianday(created_at)) FROM purchases WHERE supplier_id = ? AND status = "received"'
            avg_days = self.db.fetch_one(q_avg, (vendor_id,))[0] or 0
            q_total = 'SELECT COUNT(*) FROM purchases WHERE supplier_id = ?'
            total = self.db.fetch_one(q_total, (vendor_id,))[0] or 0
            q_on_time = 'SELECT COUNT(*) FROM purchases WHERE supplier_id = ? AND status = "received" AND julianday(received_at) <= julianday(expected_date)'
            on_time = self.db.fetch_one(q_on_time, (vendor_id,))[0] or 0
            return {'vendor_id': vendor_id, 'avg_lead_time_days': float(avg_days), 'total_orders': int(total), 'on_time_rate': (int(on_time)/int(total) if total>0 else 0)}
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في حساب أداء المورد {vendor_id}: {e}')
            return {}
