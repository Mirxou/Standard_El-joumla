"""
خدمة البحث والفلترة المتقدمة
Advanced Search & Filter Service
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import time
import json
from datetime import datetime

from ..core.database_manager import DatabaseManager
from ..models.search import (
    SearchEntity, SearchQuery, SearchFilter, SearchResult, 
    SavedFilter, SearchSuggestion, FilterOperator, SortDirection
)


class AdvancedSearchService:
    """خدمة البحث المتقدم"""
    
    # Entity to table mapping
    ENTITY_TABLES = {
        SearchEntity.PRODUCTS: {
            'table': 'products',
            'fields': ['id', 'name', 'name_en', 'barcode', 'category_id', 
                      'description', 'unit', 'cost_price', 'selling_price', 'current_stock', 
                      'min_stock', 'is_active'],
            'search_fields': ['name', 'name_en', 'barcode', 'description'],
            'display_name': 'name'
        },
        SearchEntity.CUSTOMERS: {
            'table': 'customers',
            'fields': ['id', 'name', 'phone', 'email', 'address', 'current_balance', 
                      'credit_limit', 'is_active'],
            'search_fields': ['name', 'phone', 'email', 'address'],
            'display_name': 'name'
        },
        SearchEntity.SUPPLIERS: {
            'table': 'suppliers',
            'fields': ['id', 'name', 'phone', 'email', 'address', 'contact_person'],
            'search_fields': ['name', 'phone', 'email', 'address', 'contact_person'],
            'display_name': 'name'
        },
        SearchEntity.SALES: {
            'table': 'sales',
            'fields': ['id', 'invoice_number', 'customer_id', 'total_amount', 'final_amount', 'sale_date', 'payment_method'],
            'search_fields': ['invoice_number'],
            'display_name': 'invoice_number'
        },
        SearchEntity.PURCHASES: {
            'table': 'purchases',
            'fields': ['id', 'invoice_number', 'supplier_id', 'total_amount', 'final_amount', 'purchase_date'],
            'search_fields': ['invoice_number'],
            'display_name': 'invoice_number'
        },
        SearchEntity.QUOTES: {
            'table': 'quotes',
            'fields': ['id', 'quote_number', 'customer_id', 'customer_name', 'total_amount', 'quote_date', 'status'],
            'search_fields': ['quote_number', 'customer_name'],
            'display_name': 'quote_number'
        },
        SearchEntity.RETURNS: {
            'table': 'return_invoices',
            'fields': ['id', 'return_number', 'return_type', 'total_amount', 'return_date', 'status'],
            'search_fields': ['return_number'],
            'display_name': 'return_number'
        },
        SearchEntity.ACCOUNTS: {
            'table': 'chart_of_accounts',
            'fields': ['id', 'account_code', 'account_name', 'account_type', 'current_balance'],
            'search_fields': ['account_code', 'account_name'],
            'display_name': 'account_name'
        }
    }
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    # ==================== Main Search ====================
    def search(self, query: SearchQuery) -> SearchResult:
        """تنفيذ بحث متقدم"""
        start_time = time.time()
        
        if query.entity == SearchEntity.ALL:
            return self._search_all_entities(query)
        
        result = SearchResult(entity_type=query.entity)
        
        # Build SQL
        sql, params = self._build_search_query(query)
        
        # Execute count query
        count_sql = self._build_count_query(query)
        count_result = self.db.execute_query(count_sql, params)
        result.total_count = count_result[0]['total'] if count_result else 0
        
        # Execute search query
        records = self.db.execute_query(sql, params)
        result.records = records
        result.page = (query.offset // query.limit) + 1
        result.page_size = query.limit
        result.has_more = (query.offset + len(records)) < result.total_count
        
        result.execution_time_ms = (time.time() - start_time) * 1000
        return result
    
    def _search_all_entities(self, query: SearchQuery) -> SearchResult:
        """بحث في جميع الكيانات"""
        all_records = []
        total = 0
        
        for entity in [SearchEntity.PRODUCTS, SearchEntity.CUSTOMERS, SearchEntity.SUPPLIERS, 
                      SearchEntity.SALES, SearchEntity.PURCHASES]:
            entity_query = SearchQuery(
                entity=entity,
                keyword=query.keyword,
                limit=20,
                include_inactive=query.include_inactive
            )
            result = self.search(entity_query)
            
            for record in result.records:
                record['_entity_type'] = entity.value
            
            all_records.extend(result.records)
            total += result.total_count
        
        return SearchResult(
            entity_type=SearchEntity.ALL,
            records=all_records[:query.limit],
            total_count=total,
            page=1,
            page_size=query.limit
        )
    
    def _build_search_query(self, query: SearchQuery) -> tuple[str, List[Any]]:
        """بناء استعلام SQL"""
        config = self.ENTITY_TABLES.get(query.entity)
        if not config:
            return "", []
        
        # Base query
        fields_str = ', '.join(config['fields'])
        sql = f"SELECT {fields_str} FROM {config['table']} WHERE 1=1"
        params = []
        
        # Active filter
        if not query.include_inactive and 'is_active' in config['fields']:
            sql += " AND is_active = 1"
        
        # Keyword search
        if query.keyword:
            keyword_conditions = []
            for field in config['search_fields']:
                if query.case_sensitive:
                    keyword_conditions.append(f"{field} LIKE ?")
                else:
                    keyword_conditions.append(f"LOWER({field}) LIKE LOWER(?)")
                
                if query.whole_word:
                    params.append(f"{query.keyword}")
                else:
                    params.append(f"%{query.keyword}%")
            
            if keyword_conditions:
                sql += f" AND ({' OR '.join(keyword_conditions)})"
        
        # Custom filters
        for filt in query.filters:
            filter_sql, filter_params = self._build_filter_clause(filt)
            if filter_sql:
                sql += f" AND {filter_sql}"
                params.extend(filter_params)
        
        # Sorting
        if query.sort_by:
            order_parts = []
            for sort in query.sort_by:
                direction = "ASC" if sort.direction == SortDirection.ASC else "DESC"
                order_parts.append(f"{sort.field} {direction}")
            sql += f" ORDER BY {', '.join(order_parts)}"
        else:
            # Default sorting
            sql += f" ORDER BY id DESC"
        
        # Pagination
        sql += f" LIMIT {query.limit} OFFSET {query.offset}"
        
        return sql, params
    
    def _build_count_query(self, query: SearchQuery) -> str:
        """بناء استعلام العد"""
        sql, params = self._build_search_query(query)
        # Remove ORDER BY, LIMIT, OFFSET
        sql = sql.split("ORDER BY")[0]
        # Replace SELECT fields with COUNT(*)
        config = self.ENTITY_TABLES.get(query.entity)
        if config:
            fields_str = ', '.join(config['fields'])
            sql = sql.replace(f"SELECT {fields_str}", "SELECT COUNT(*) as total")
        return sql
    
    def _build_filter_clause(self, filt: SearchFilter) -> tuple[str, List[Any]]:
        """بناء شرط فلتر واحد"""
        field = filt.field
        op = filt.operator
        val = filt.value
        
        if op == FilterOperator.EQUALS:
            return f"{field} = ?", [val]
        elif op == FilterOperator.NOT_EQUALS:
            return f"{field} != ?", [val]
        elif op == FilterOperator.CONTAINS:
            return f"{field} LIKE ?", [f"%{val}%"]
        elif op == FilterOperator.NOT_CONTAINS:
            return f"{field} NOT LIKE ?", [f"%{val}%"]
        elif op == FilterOperator.STARTS_WITH:
            return f"{field} LIKE ?", [f"{val}%"]
        elif op == FilterOperator.ENDS_WITH:
            return f"{field} LIKE ?", [f"%{val}"]
        elif op == FilterOperator.GREATER_THAN:
            return f"{field} > ?", [val]
        elif op == FilterOperator.LESS_THAN:
            return f"{field} < ?", [val]
        elif op == FilterOperator.GREATER_OR_EQUAL:
            return f"{field} >= ?", [val]
        elif op == FilterOperator.LESS_OR_EQUAL:
            return f"{field} <= ?", [val]
        elif op == FilterOperator.BETWEEN:
            return f"{field} BETWEEN ? AND ?", [val, filt.value2]
        elif op == FilterOperator.IN:
            placeholders = ','.join(['?' for _ in val])
            return f"{field} IN ({placeholders})", val
        elif op == FilterOperator.NOT_IN:
            placeholders = ','.join(['?' for _ in val])
            return f"{field} NOT IN ({placeholders})", val
        elif op == FilterOperator.IS_NULL:
            return f"{field} IS NULL", []
        elif op == FilterOperator.IS_NOT_NULL:
            return f"{field} IS NOT NULL", []
        
        return "", []
    
    # ==================== Suggestions ====================
    def get_suggestions(self, keyword: str, entity: SearchEntity, limit: int = 10) -> List[SearchSuggestion]:
        """الحصول على اقتراحات بحث"""
        if not keyword or len(keyword) < 2:
            return []
        
        config = self.ENTITY_TABLES.get(entity)
        if not config:
            return []
        
        suggestions = []
        
        # Build query for suggestions
        display_field = config['display_name']
        sql = f"""
            SELECT DISTINCT {display_field} as text
            FROM {config['table']}
            WHERE LOWER({display_field}) LIKE LOWER(?)
            AND is_active = 1
            LIMIT ?
        """
        
        results = self.db.execute_query(sql, [f"{keyword}%", limit])
        
        for row in results:
            suggestions.append(SearchSuggestion(
                text=row['text'],
                entity=entity,
                score=1.0
            ))
        
        return suggestions
    
    # ==================== Saved Filters ====================
    def save_filter(self, saved_filter: SavedFilter) -> int:
        """حفظ فلتر"""
        sql = """
            INSERT INTO saved_filters (name, description, entity, query_data, is_default, is_shared, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now()
        self.db.execute_query(sql, [
            saved_filter.name,
            saved_filter.description,
            saved_filter.entity.name,
            saved_filter.query_data,
            saved_filter.is_default,
            saved_filter.is_shared,
            saved_filter.created_by,
            now,
            now
        ])
        return self.db.get_last_insert_id()
    
    def load_filter(self, filter_id: int) -> Optional[SavedFilter]:
        """تحميل فلتر محفوظ"""
        sql = "SELECT * FROM saved_filters WHERE id = ?"
        result = self.db.execute_query(sql, [filter_id])
        
        if not result:
            return None
        
        row = result[0]
        return SavedFilter(
            id=row['id'],
            name=row['name'],
            description=row.get('description'),
            entity=SearchEntity[row['entity']],
            query_data=row['query_data'],
            is_default=bool(row.get('is_default', 0)),
            is_shared=bool(row.get('is_shared', 0)),
            created_by=row.get('created_by'),
            created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else None
        )
    
    def list_saved_filters(self, entity: Optional[SearchEntity] = None, user_id: Optional[int] = None) -> List[SavedFilter]:
        """قائمة الفلاتر المحفوظة"""
        sql = "SELECT * FROM saved_filters WHERE 1=1"
        params = []
        
        if entity:
            sql += " AND entity = ?"
            params.append(entity.name)
        
        if user_id:
            sql += " AND (created_by = ? OR is_shared = 1)"
            params.append(user_id)
        
        sql += " ORDER BY is_default DESC, name ASC"
        
        results = self.db.execute_query(sql, params)
        filters = []
        
        for row in results:
            filters.append(SavedFilter(
                id=row['id'],
                name=row['name'],
                description=row.get('description'),
                entity=SearchEntity[row['entity']],
                query_data=row['query_data'],
                is_default=bool(row.get('is_default', 0)),
                is_shared=bool(row.get('is_shared', 0)),
                created_by=row.get('created_by')
            ))
        
        return filters
    
    def delete_filter(self, filter_id: int) -> bool:
        """حذف فلتر"""
        sql = "DELETE FROM saved_filters WHERE id = ?"
        result = self.db.execute_query(sql, [filter_id])
        return bool(result)
    
    # ==================== Helper Methods ====================
    def get_available_fields(self, entity: SearchEntity) -> List[Dict[str, str]]:
        """الحصول على الحقول المتاحة للكيان"""
        config = self.ENTITY_TABLES.get(entity)
        if not config:
            return []
        
        return [{'name': field, 'label': field.replace('_', ' ').title()} for field in config['fields']]
