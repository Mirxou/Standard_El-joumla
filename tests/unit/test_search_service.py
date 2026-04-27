#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Search Service
اختبارات خدمة البحث
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
from src.services.search_service import SearchService, SearchCriteria, SearchOperator, LogicalOperator


class TestSearchCriteria:
    """اختبارات معايير البحث"""
    
    def test_search_criteria_creation(self):
        """اختبار إنشاء معايير البحث"""
        criteria = SearchCriteria(
            field='name',
            operator=SearchOperator.CONTAINS,
            value='test',
            logical=LogicalOperator.AND
        )
        
        assert criteria.field == 'name'
        assert criteria.operator == SearchOperator.CONTAINS
        assert criteria.value == 'test'
        assert criteria.logical == LogicalOperator.AND
    
    def test_search_criteria_to_sql_contains(self):
        """اختبار تحويل معايير البحث إلى SQL - يحتوي على"""
        criteria = SearchCriteria(
            field='name',
            operator=SearchOperator.CONTAINS,
            value='test'
        )
        
        sql, params = criteria.to_sql()
        
        assert 'LIKE' in sql
        assert '%test%' in params
    
    def test_search_criteria_to_sql_equals(self):
        """اختبار تحويل معايير البحث إلى SQL - يساوي"""
        criteria = SearchCriteria(
            field='id',
            operator=SearchOperator.EQUALS,
            value=1
        )
        
        sql, params = criteria.to_sql()
        
        assert '=' in sql
        assert 1 in params
    
    def test_search_criteria_to_sql_greater_than(self):
        """اختبار تحويل معايير البحث إلى SQL - أكبر من"""
        criteria = SearchCriteria(
            field='price',
            operator=SearchOperator.GREATER_THAN,
            value=100
        )
        
        sql, params = criteria.to_sql()
        
        assert '>' in sql
        assert 100 in params
    
    def test_search_criteria_to_sql_between(self):
        """اختبار تحويل معايير البحث إلى SQL - بين"""
        criteria = SearchCriteria(
            field='date',
            operator=SearchOperator.BETWEEN,
            value=['2024-01-01', '2024-01-31']
        )
        
        sql, params = criteria.to_sql()
        
        assert 'BETWEEN' in sql
        assert len(params) == 2


class TestSearchServiceInitialization:
    """اختبارات تهيئة خدمة البحث"""
    
    def test_initialization_with_db_manager(self):
        """اختبار التهيئة مع مدير قاعدة البيانات"""
        mock_db = Mock()
        
        service = SearchService(db_manager=mock_db)
        
        assert service.db == mock_db
    
    def test_initialization_without_db_manager(self):
        """اختبار التهيئة بدون مدير قاعدة بيانات"""
        with patch('src.services.search_service.DatabaseManager') as mock_db_class:
            mock_db = Mock()
            mock_db_class.return_value = mock_db
            
            service = SearchService()
            
            assert service.db == mock_db


class TestSearchProducts:
    """اختبارات البحث في المنتجات"""
    
    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        
        mock_db.execute_query.return_value = [
            {
                'id': 1,
                'name': 'Test Product',
                'sku': 'SKU001',
                'price': 100.0,
                'stock': 50
            },
            {
                'id': 2,
                'name': 'Another Product',
                'sku': 'SKU002',
                'price': 200.0,
                'stock': 30
            }
        ]
        
        service = SearchService(db_manager=mock_db)
        return service
    
    def test_search_products_success(self, service_with_mocks):
        """اختبار البحث عن المنتجات بنجاح"""
        criteria_list = [
            SearchCriteria(
                field='name',
                operator=SearchOperator.CONTAINS,
                value='Product'
            )
        ]
        
        result = service_with_mocks.search('products', criteria_list)
        
        assert result['success'] is True
        assert len(result['results']) == 2
        assert result['count'] == 2
    
    def test_search_products_empty_result(self, service_with_mocks):
        """اختبار البحث بدون نتائج"""
        service_with_mocks.db.execute_query.return_value = []
        
        criteria_list = [
            SearchCriteria(
                field='name',
                operator=SearchOperator.CONTAINS,
                value='NonExistent'
            )
        ]
        
        result = service_with_mocks.search('products', criteria_list)
        
        assert result['success'] is True
        assert len(result['results']) == 0
        assert result['count'] == 0
    
    def test_search_products_with_pagination(self, service_with_mocks):
        """اختبار البحث مع تقسيم الصفحات"""
        criteria_list = [
            SearchCriteria(
                field='name',
                operator=SearchOperator.CONTAINS,
                value='Product'
            )
        ]
        
        result = service_with_mocks.search('products', criteria_list, limit=10, offset=0)
        
        assert result['success'] is True
        assert 'results' in result


class TestSearchCustomers:
    """اختبارات البحث في العملاء"""
    
    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        
        mock_db.execute_query.return_value = [
            {
                'id': 1,
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '1234567890'
            },
            {
                'id': 2,
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'phone': '0987654321'
            }
        ]
        
        service = SearchService(db_manager=mock_db)
        return service
    
    def test_search_customers_by_name(self, service_with_mocks):
        """اختبار البحث عن العملاء بالاسم"""
        criteria_list = [
            SearchCriteria(
                field='name',
                operator=SearchOperator.CONTAINS,
                value='John'
            )
        ]
        
        result = service_with_mocks.search('customers', criteria_list)
        
        assert result['success'] is True
        assert len(result['results']) == 2
    
    def test_search_customers_by_email(self, service_with_mocks):
        """اختبار البحث عن العملاء بالبريد الإلكتروني"""
        criteria_list = [
            SearchCriteria(
                field='email',
                operator=SearchOperator.CONTAINS,
                value='example.com'
            )
        ]
        
        result = service_with_mocks.search('customers', criteria_list)
        
        assert result['success'] is True


class TestFullTextSearch:
    """اختبارات البحث النصي الكامل"""
    
    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        
        mock_db.execute_query.return_value = [
            {
                'id': 1,
                'name': 'Product A',
                'description': 'This is a great product',
                'relevance': 0.9
            },
            {
                'id': 2,
                'name': 'Product B',
                'description': 'Another great product',
                'relevance': 0.8
            }
        ]
        
        service = SearchService(db_manager=mock_db)
        return service
    
    def test_full_text_search_products(self, service_with_mocks):
        """اختبار البحث النصي الكامل في المنتجات"""
        result = service_with_mocks.full_text_search('great', 'products', limit=10)
        
        assert isinstance(result, list)
        assert len(result) == 2
    
    def test_full_text_search_customers(self, service_with_mocks):
        """اختبار البحث النصي الكامل في العملاء"""
        result = service_with_mocks.full_text_search('John', 'customers', limit=10)
        
        assert isinstance(result, list)


class TestGlobalSearch:
    """اختبارات البحث العام"""
    
    def test_global_search_success(self):
        """اختبار البحث العام بنجاح"""
        mock_db = Mock()
        
        mock_db.execute_query.return_value = [
            {'id': 1, 'name': 'Test', 'relevance': 1.0}
        ]
        
        service = SearchService(db_manager=mock_db)
        
        # Mock full_text_search to return consistent results
        service.full_text_search = Mock(return_value=[
            {'id': 1, 'name': 'Test Product'},
            {'id': 2, 'name': 'Test Customer'},
            {'id': 3, 'name': 'Test Supplier'}
        ])
        
        result = service.global_search('test', limit_per_type=10)
        
        assert 'products' in result
        assert 'customers' in result
        assert 'suppliers' in result
    
    def test_global_search_empty_query(self):
        """اختبار البحث العام باستعلام فارغ"""
        mock_db = Mock()
        
        service = SearchService(db_manager=mock_db)
        service.full_text_search = Mock(return_value=[])
        
        result = service.global_search('', limit_per_type=10)
        
        assert 'products' in result
        assert 'customers' in result
        assert 'suppliers' in result
        assert len(result['products']) == 0


class TestBuildWhereClause:
    """اختبارات بناء جملة WHERE"""
    
    def test_build_where_clause_single_criteria(self):
        """اختبار بناء WHERE مع معيار واحد"""
        mock_db = Mock()
        service = SearchService(db_manager=mock_db)
        
        criteria_list = [
            SearchCriteria(
                field='name',
                operator=SearchOperator.CONTAINS,
                value='test'
            )
        ]
        
        where_clause, params = service._build_where_clause(criteria_list)
        
        assert 'name' in where_clause
        assert 'LIKE' in where_clause
        assert len(params) == 1
    
    def test_build_where_clause_multiple_criteria(self):
        """اختبار بناء WHERE مع معايير متعددة"""
        mock_db = Mock()
        service = SearchService(db_manager=mock_db)
        
        criteria_list = [
            SearchCriteria(
                field='name',
                operator=SearchOperator.CONTAINS,
                value='test',
                logical=LogicalOperator.AND
            ),
            SearchCriteria(
                field='price',
                operator=SearchOperator.GREATER_THAN,
                value=100,
                logical=LogicalOperator.AND
            )
        ]
        
        where_clause, params = service._build_where_clause(criteria_list)
        
        assert 'AND' in where_clause
        assert len(params) == 2
    
    def test_build_where_clause_empty_list(self):
        """اختبار بناء WHERE مع قائمة فارغة"""
        mock_db = Mock()
        service = SearchService(db_manager=mock_db)
        
        where_clause, params = service._build_where_clause([])
        
        assert where_clause == ""
        assert params == []


class TestCountResults:
    """اختبارات عد النتائج"""
    
    def test_count_results_success(self):
        """اختبار عد النتائج بنجاح"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [{'total': 100}]
        
        service = SearchService(db_manager=mock_db)
        
        criteria_list = [
            SearchCriteria(
                field='name',
                operator=SearchOperator.CONTAINS,
                value='test'
            )
        ]
        
        result = service.count_results('products', criteria_list)
        
        assert result == 100
    
    def test_count_results_no_criteria(self):
        """اختبار عد النتائج بدون معايير"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [{'total': 1000}]
        
        service = SearchService(db_manager=mock_db)
        
        result = service.count_results('products', [])
        
        assert result == 1000
    
    def test_count_results_empty_result(self):
        """اختبار عد النتائج مع نتيجة فارغة"""
        mock_db = Mock()
        mock_db.execute_query.return_value = []
        
        service = SearchService(db_manager=mock_db)
        
        result = service.count_results('products', [])
        
        assert result == 0


class TestSearchWithSorting:
    """اختبارات البحث مع الترتيب"""
    
    def test_search_with_sorting(self):
        """اختبار البحث مع ترتيب النتائج"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {'id': 1, 'name': 'A', 'price': 10},
            {'id': 2, 'name': 'B', 'price': 20},
            {'id': 3, 'name': 'C', 'price': 30}
        ]
        
        service = SearchService(db_manager=mock_db)
        
        criteria_list = []
        
        result = service.search(
            'products',
            criteria_list,
            sort_by='price',
            sort_order='DESC'
        )
        
        assert result['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



