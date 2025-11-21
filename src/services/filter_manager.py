"""
مدير الفلاتر (Filter Manager)

يوفر نظام إدارة وحفظ الفلاتر المستخدمة:
- حفظ الفلاتر المفضلة
- استرجاع الفلاتر المحفوظة
- فلاتر معقدة (AND/OR)
- تطبيق سريع للفلاتر
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from ..core.database_manager import DatabaseManager


@dataclass
class SavedFilter:
    """فلتر محفوظ"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    filter_type: str = "products"  # products, customers, sales, etc.
    criteria: str = "{}"  # JSON string
    created_at: Optional[str] = None
    user_id: int = 1
    is_favorite: bool = False


class FilterManager:
    """مدير الفلاتر"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """إنشاء جدول الفلاتر المحفوظة إن لم يكن موجوداً"""
        create_query = """
            CREATE TABLE IF NOT EXISTS saved_filters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                filter_type TEXT NOT NULL,
                criteria TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER DEFAULT 1,
                is_favorite BOOLEAN DEFAULT 0,
                UNIQUE(name, user_id, filter_type)
            )
        """
        try:
            self.db.execute_query(create_query)
        except Exception:
            pass  # Table might already exist
    
    # ==================== إدارة الفلاتر ====================
    
    def save_filter(self, filter_obj: SavedFilter) -> int:
        """
        حفظ فلتر جديد
        
        Args:
            filter_obj: كائن الفلتر
        
        Returns:
            ID الفلتر المحفوظ
        """
        query = """
            INSERT INTO saved_filters (name, description, filter_type, criteria, user_id, is_favorite)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = [
            filter_obj.name,
            filter_obj.description,
            filter_obj.filter_type,
            filter_obj.criteria,
            filter_obj.user_id,
            1 if filter_obj.is_favorite else 0
        ]
        
        try:
            self.db.execute_query(query, params)
            # Get last inserted ID
            result = self.db.execute_query("SELECT last_insert_rowid() as id")
            return int(result[0]['id']) if result else 0
        except Exception as e:
            print(f"Error saving filter: {e}")
            return 0
    
    def update_filter(self, filter_id: int, filter_obj: SavedFilter) -> bool:
        """تحديث فلتر محفوظ"""
        query = """
            UPDATE saved_filters
            SET name = ?, description = ?, criteria = ?, 
                is_favorite = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        params = [
            filter_obj.name,
            filter_obj.description,
            filter_obj.criteria,
            1 if filter_obj.is_favorite else 0,
            filter_id
        ]
        
        try:
            self.db.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error updating filter: {e}")
            return False
    
    def delete_filter(self, filter_id: int) -> bool:
        """حذف فلتر"""
        query = "DELETE FROM saved_filters WHERE id = ?"
        try:
            self.db.execute_query(query, [filter_id])
            return True
        except Exception:
            return False
    
    def get_filter(self, filter_id: int) -> Optional[SavedFilter]:
        """الحصول على فلتر محدد"""
        query = "SELECT * FROM saved_filters WHERE id = ?"
        results = self.db.execute_query(query, [filter_id])
        
        if results:
            row = results[0]
            return SavedFilter(
                id=int(row['id']),
                name=str(row['name']),
                description=str(row.get('description', '')),
                filter_type=str(row['filter_type']),
                criteria=str(row['criteria']),
                created_at=str(row.get('created_at', '')),
                user_id=int(row.get('user_id', 1)),
                is_favorite=bool(row.get('is_favorite', 0))
            )
        return None
    
    def list_filters(self, filter_type: Optional[str] = None, 
                    user_id: int = 1, favorites_only: bool = False) -> List[SavedFilter]:
        """
        قائمة الفلاتر المحفوظة
        
        Args:
            filter_type: نوع الفلتر (اختياري)
            user_id: معرف المستخدم
            favorites_only: المفضلة فقط
        
        Returns:
            قائمة الفلاتر
        """
        query = "SELECT * FROM saved_filters WHERE user_id = ?"
        params = [user_id]
        
        if filter_type:
            query += " AND filter_type = ?"
            params.append(filter_type)
        
        if favorites_only:
            query += " AND is_favorite = 1"
        
        query += " ORDER BY is_favorite DESC, created_at DESC"
        
        results = self.db.execute_query(query, params)
        
        filters = []
        for row in results:
            filters.append(SavedFilter(
                id=int(row['id']),
                name=str(row['name']),
                description=str(row.get('description', '')),
                filter_type=str(row['filter_type']),
                criteria=str(row['criteria']),
                created_at=str(row.get('created_at', '')),
                user_id=int(row.get('user_id', 1)),
                is_favorite=bool(row.get('is_favorite', 0))
            ))
        
        return filters
    
    def toggle_favorite(self, filter_id: int) -> bool:
        """تبديل حالة المفضلة"""
        query = """
            UPDATE saved_filters
            SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END
            WHERE id = ?
        """
        try:
            self.db.execute_query(query, [filter_id])
            return True
        except Exception:
            return False
    
    # ==================== فلاتر سريعة مدمجة ====================
    
    def get_quick_filters(self, entity_type: str) -> List[Dict[str, Any]]:
        """
        الحصول على فلاتر سريعة مدمجة حسب نوع الكيان
        
        Args:
            entity_type: نوع الكيان (products, customers, sales)
        
        Returns:
            قائمة الفلاتر السريعة
        """
        quick_filters = {
            "products": [
                {
                    "name": "منتجات منخفضة المخزون",
                    "criteria": json.dumps({
                        "field": "current_stock",
                        "operator": "<=",
                        "value": "min_stock"
                    })
                },
                {
                    "name": "منتجات نفذت من المخزون",
                    "criteria": json.dumps({
                        "field": "current_stock",
                        "operator": "=",
                        "value": 0
                    })
                },
                {
                    "name": "منتجات عالية السعر (>1000 دج)",
                    "criteria": json.dumps({
                        "field": "price",
                        "operator": ">",
                        "value": 1000
                    })
                }
            ],
            "customers": [
                {
                    "name": "عملاء لديهم أرصدة مستحقة",
                    "criteria": json.dumps({
                        "field": "current_balance",
                        "operator": ">",
                        "value": 0
                    })
                },
                {
                    "name": "عملاء VIP (حد ائتماني >50,000)",
                    "criteria": json.dumps({
                        "field": "credit_limit",
                        "operator": ">",
                        "value": 50000
                    })
                }
            ],
            "sales": [
                {
                    "name": "مبيعات اليوم",
                    "criteria": json.dumps({
                        "field": "sale_date",
                        "operator": "=",
                        "value": "TODAY"
                    })
                },
                {
                    "name": "مبيعات هذا الشهر",
                    "criteria": json.dumps({
                        "field": "sale_date",
                        "operator": "MONTH",
                        "value": "CURRENT"
                    })
                },
                {
                    "name": "مبيعات معلقة",
                    "criteria": json.dumps({
                        "field": "status",
                        "operator": "=",
                        "value": "pending"
                    })
                }
            ]
        }
        
        return quick_filters.get(entity_type, [])
    
    # ==================== دوال مساعدة ====================
    
    def parse_criteria(self, criteria_json: str) -> Dict[str, Any]:
        """تحويل JSON إلى dict"""
        try:
            return json.loads(criteria_json)
        except json.JSONDecodeError:
            return {}
    
    def build_criteria_json(self, criteria_dict: Dict[str, Any]) -> str:
        """تحويل dict إلى JSON"""
        return json.dumps(criteria_dict, ensure_ascii=False)
    
    def export_filters(self, user_id: int = 1) -> str:
        """تصدير جميع الفلاتر إلى JSON"""
        filters = self.list_filters(user_id=user_id)
        export_data = [asdict(f) for f in filters]
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    
    def import_filters(self, json_data: str, user_id: int = 1) -> int:
        """استيراد فلاتر من JSON"""
        try:
            filters_data = json.loads(json_data)
            count = 0
            
            for filter_dict in filters_data:
                filter_obj = SavedFilter(
                    name=filter_dict['name'],
                    description=filter_dict.get('description', ''),
                    filter_type=filter_dict['filter_type'],
                    criteria=filter_dict['criteria'],
                    user_id=user_id,
                    is_favorite=filter_dict.get('is_favorite', False)
                )
                
                if self.save_filter(filter_obj) > 0:
                    count += 1
            
            return count
        except Exception as e:
            print(f"Error importing filters: {e}")
            return 0
