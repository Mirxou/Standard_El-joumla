from typing import List, Dict, Any
from ..core.database_manager import DatabaseManager
from datetime import datetime

class WholesaleQuoteService:
    """
    خدمة إدارة عروض الجملة (Wholesale Quote / Cart)
    Tracks items added to a potential deal and calculates aggregate metrics.
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.items: List[Dict[str, Any]] = []
        
    def add_item(self, product_data: Dict[str, Any], quantity: float) -> None:
        """
        إضافة منتج لعرض السعر
        """
        # Check if already exists, update qty if so
        for item in self.items:
            if item['id'] == product_data['id']:
                item['quantity'] += quantity
                self._recalc_item(item)
                return

        # Add new item
        item = {
            'id': product_data['id'],
            'name': product_data['name'],
            'sku': product_data.get('sku', ''),
            'wholesale_price': float(product_data.get('wholesale_price', 0)),
            'cost_price': float(product_data.get('cost_price', 0)),
            'quantity': quantity
        }
        self._recalc_item(item)
        self.items.append(item)

    def _recalc_item(self, item: Dict[str, Any]):
        """Calculate line totals"""
        qty = item['quantity']
        w_price = item['wholesale_price']
        c_price = item['cost_price']
        
        item['total_val'] = qty * w_price
        item['total_cost'] = qty * c_price
        item['total_profit'] = item['total_val'] - item['total_cost']

    def remove_item(self, product_id: Any) -> None:
        """إزالة منتج"""
        self.items = [i for i in self.items if i['id'] != product_id]

    def clear(self) -> None:
        """تفريغ العرض"""
        self.items = []

    def get_summary(self) -> Dict[str, Any]:
        """
        الحصول على ملخص العرض (الإجماليات والهوامش)
        """
        total_items = len(self.items)
        total_qty = sum(i['quantity'] for i in self.items)
        total_val = sum(i['total_val'] for i in self.items)
        total_cost = sum(i['total_cost'] for i in self.items)
        total_profit = total_val - total_cost
        
        margin_percent = 0.0
        if total_val > 0:
            margin_percent = (total_profit / total_val) * 100
            
        return {
            "item_count": total_items,
            "total_qty": total_qty,
            "total_value": total_val,
            "total_profit": total_profit,
            "margin_percent": margin_percent
        }

    def save_quote(self, customer_name: str) -> int:
        """
        حفظ عرض السعر في قاعدة البيانات
        """
        import json
        
        summary = self.get_summary()
        items_json = json.dumps(self.items, ensure_ascii=False)
        
        sql = """
            INSERT INTO wholesale_quotes 
            (customer_name, total_value, total_profit, item_count, items_json)
            VALUES (?, ?, ?, ?, ?)
        """
        params = [
            customer_name, 
            summary['total_value'], 
            summary['total_profit'], 
            summary['item_count'], 
            items_json
        ]
        
        return self.db.execute_update(sql, params)

    def get_recent_quotes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        جلب أحدث عروض الأسعار المحفوظة
        """
        sql = """
            SELECT id, customer_name, total_value, total_profit, item_count, created_at, items_json
            FROM wholesale_quotes
            ORDER BY created_at DESC
            LIMIT ?
        """
        rows = self.db.fetch_all(sql, [limit])
        quotes = []
        for row in rows:
            quotes.append({
                'id': row[0],
                'customer_name': row[1],
                'total_value': row[2],
                'total_profit': row[3],
                'item_count': row[4],
                'created_at': row[5],
                'items_json': row[6]
            })
        return quotes

    def load_quote(self, quote_id: int) -> bool:
        """
        تحميل عرض سعر معين إلى السلة الحالية
        """
        import json
        sql = "SELECT items_json FROM wholesale_quotes WHERE id = ?"
        row = self.db.fetch_one(sql, [quote_id])
        
        if not row:
            return False
            
        try:
            items_data = json.loads(row[0])
            self.items = items_data
            return True
        except Exception as e:
            print(f"Error loading quote {quote_id}: {e}")
            return False

    def delete_quote(self, quote_id: int) -> bool:
        """
        حذف عرض سعر
        """
        sql = "DELETE FROM wholesale_quotes WHERE id = ?"
        try:
            self.db.execute_update(sql, [quote_id])
            return True
        except Exception:
            return False

    def convert_to_sale(self, quote_id: int) -> str:
        """
        تحويل عرض السعر إلى بيع (فاتورة نقدية)
        Returns: Invoice Number if success, else None
        """
        import json
        
        # 1. Load Quote Data
        sql = "SELECT customer_name, total_value, items_json FROM wholesale_quotes WHERE id = ?"
        row = self.db.fetch_one(sql, [quote_id])
        if not row:
            raise Exception("Quote not found")
            
        customer_name, total_val, items_json = row
        items = json.loads(items_json)
        
        # 2. Generate Invoice Number (Simple Format: J-Timestamp)
        invoice_number = f"J-{datetime.now().strftime('%y%m%d-%H%M%S')}"
        
        # 3. Insert into Sales
        # Mapping: 
        # customer_name -> customer_name (Text)
        # total_val -> total_amount, final_amount, paid_amount
        # payment_method -> 'نقدي' (Arabic for Cash, judging by existing data)
        # status -> 'paid'
        
        sql_sale = """
            INSERT INTO sales 
            (invoice_number, customer_name, total_amount, final_amount, 
             payment_method, status, sale_date, created_at, 
             paid_amount, remaining_amount, discount_amount, tax_amount)
            VALUES (?, ?, ?, ?, 'نقدي', 'paid', DATE('now'), DATETIME('now'), ?, 0, 0, 0)
        """
        sale_id = self.db.execute_update(sql_sale, [
            invoice_number, customer_name, total_val, total_val, 
            total_val # paid_amount matches total
        ])
        
        if not sale_id:
            raise Exception("Failed to create sale record")
            
            # 4. Insert Items & Update Stock
        for item in items:
            p_id = item['id']
            qty = item['quantity']
            price = item['wholesale_price']
            total = item['total_val']
            
            # Enrich with cost/profit if available in item data
            cost = item.get('cost_price', 0)
            profit = item.get('total_profit', 0)
            
            # Find Batch (Simple Logic: Pick batch with positive stock or just latest)
            # In a full system, this would be FIFO. Here we satisfy the constraint.
            sql_batch = "SELECT id FROM product_batches WHERE product_id = ? ORDER BY current_quantity DESC LIMIT 1"
            batch_row = self.db.fetch_one(sql_batch, [p_id])
            if batch_row:
                batch_id = batch_row[0]
                # Update Batch Qty
                sql_update_batch = "UPDATE product_batches SET current_quantity = current_quantity - ? WHERE id = ?"
                self.db.execute_update(sql_update_batch, [qty, batch_id])
            else:
                # Fallback: Validation should arguably fail here if strict, 
                # but for now we might insert NULL if allowed or handle error.
                # Schema said NOT NULL, so we MUST have a batch. 
                # If no batch exists, we can't sell in this strict schema.
                # However, for legacy/migration data, maybe we check if we can create one?
                # Let's assume there's always a batch or fail.
                # Actually, let's try to find ANY batch or raise.
                # If product exists but no batch, it's a data consistency issue in strict mode.
                raise Exception(f"No batch found for product {p_id}")

            # Add Sale Item
            sql_item = """
                INSERT INTO sale_items (sale_id, product_id, batch_id, quantity, unit_price, total_price, cost_price, profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.execute_update(sql_item, [sale_id, p_id, batch_id, qty, price, total, cost, profit])
            
            # Update Stock (Product Level)
            sql_stock = "UPDATE products SET current_stock = current_stock - ? WHERE id = ?"
            self.db.execute_update(sql_stock, [qty, p_id])
            
        return invoice_number

