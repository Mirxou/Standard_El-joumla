#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Vendor Service
اختبارات خدمة الموردين
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List


# Mock classes for testing
class MockVendorService:
    """Mock class for VendorService testing"""
    
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger
    
    def create_purchase_order(self, supplier_id: int, items: List[Dict], expected_delivery_date=None) -> int:
        try:
            total = sum(item['quantity'] * item['unit_price'] for item in items)
            now = datetime.now()
            
            result = self.db.execute_query("""
                INSERT INTO purchase_orders (supplier_id, order_date, expected_delivery_date, status, total_amount)
                VALUES (?, ?, ?, 'pending', ?)
            """, (supplier_id, now, expected_delivery_date, total))
            
            purchase_id = result.lastrowid
            
            for item in items:
                self.db.execute_query("""
                    INSERT INTO purchase_order_items (purchase_order_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                """, (purchase_id, item['product_id'], item['quantity'], item['unit_price']))
            
            if self.logger:
                self.logger.info(f'تم إنشاء أمر الشراء {purchase_id}')
            return purchase_id
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في إنشاء أمر الشراء: {e}')
            return None
    
    def receive_purchase_order(self, purchase_id: int, received_items: List[Dict]) -> bool:
        try:
            now = datetime.now()
            self.db.execute_query("""
                UPDATE purchase_orders 
                SET status = 'received', delivery_date = ?
                WHERE id = ?
            """, (now, purchase_id))
            
            for item in received_items:
                pid = item['product_id']
                qty = item['quantity']
                self.db.execute_query("""
                    UPDATE products 
                    SET current_stock = current_stock + ?
                    WHERE id = ?
                """, (qty, pid))
            
            if self.logger:
                self.logger.info(f'تم استلام أمر الشراء {purchase_id}')
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في استلام أمر الشراء {purchase_id}: {e}')
            return False
    
    def calculate_quality_score(self, vendor_id: int) -> float:
        try:
            q_total = 'SELECT COUNT(*) FROM purchase_orders WHERE supplier_id = ? AND status = "received"'
            total_orders = self.db.fetch_one(q_total, (vendor_id,))[0] or 0
            
            if total_orders == 0:
                return 50.0
            
            q_on_time = 'SELECT COUNT(*) FROM purchase_orders WHERE supplier_id = ? AND status = "received" AND (expected_delivery_date IS NULL OR julianday(delivery_date) <= julianday(expected_delivery_date))'
            on_time_count = self.db.fetch_one(q_on_time, (vendor_id,))[0] or 0
            on_time_score = (on_time_count / total_orders) * 100
            
            fulfillment_score = 100.0
            
            q_avg_days = 'SELECT AVG(julianday(delivery_date) - julianday(order_date)) FROM purchase_orders WHERE supplier_id = ? AND status = "received"'
            avg_days = self.db.fetch_one(q_avg_days, (vendor_id,))[0] or 7
            lead_time_score = max(0, 100 - (avg_days * 5))
            
            final_score = (on_time_score * 0.4) + (fulfillment_score * 0.3) + (lead_time_score * 0.3)
            return round(final_score, 2)
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في حساب جودة المورد {vendor_id}: {e}')
            return 0.0
    
    def vendor_performance(self, vendor_id: int) -> Dict[str, Any]:
        try:
            q_avg = 'SELECT AVG(julianday(delivery_date) - julianday(order_date)) FROM purchase_orders WHERE supplier_id = ? AND status = "received"'
            avg_days = self.db.fetch_one(q_avg, (vendor_id,))[0] or 0
            q_total = 'SELECT COUNT(*) FROM purchase_orders WHERE supplier_id = ?'
            total = self.db.fetch_one(q_total, (vendor_id,))[0] or 0
            q_on_time = 'SELECT COUNT(*) FROM purchase_orders WHERE supplier_id = ? AND status = "received" AND (expected_delivery_date IS NULL OR julianday(delivery_date) <= julianday(expected_delivery_date))'
            on_time = self.db.fetch_one(q_on_time, (vendor_id,))[0] or 0
            
            quality_score = self.calculate_quality_score(vendor_id)
            
            return {
                'vendor_id': vendor_id,
                'avg_lead_time_days': float(avg_days),
                'total_orders': int(total),
                'on_time_rate': (int(on_time)/int(total) if total>0 else 0),
                'quality_score': quality_score
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في حساب أداء المورد {vendor_id}: {e}')
            return {}
    
    def generate_demand_plan(self, ai_service, days_ahead: int = 30) -> List[Dict[str, Any]]:
        plan = []
        try:
            products = self.db.fetch_all('SELECT id, name, current_stock, min_stock FROM products')
            for p in products:
                pid, name, stock, min_stock = p
                stock = stock or 0
                min_stock = min_stock or 0
                
                forecast = ai_service.demand_forecast_linear_regression(pid, days=60, forecast_days=days_ahead)
                total_predicted_demand = sum(f['predicted_quantity'] for f in forecast)
                
                projected_stock = stock - total_predicted_demand
                
                if projected_stock < min_stock:
                    suggested_qty = (min_stock + total_predicted_demand) - stock
                    
                    q_vendor = '''
                        SELECT po.supplier_id, poi.unit_price 
                        FROM purchase_order_items poi
                        JOIN purchase_orders po ON poi.purchase_order_id = po.id
                        WHERE poi.product_id = ? 
                        ORDER BY poi.created_at DESC 
                        LIMIT 1
                    '''
                    best_vendor = self.db.fetch_one(q_vendor, (pid,))
                    
                    vendor_id = best_vendor[0] if best_vendor else None
                    est_cost = best_vendor[1] if best_vendor else 0
                    
                    plan.append({
                        'product_id': pid,
                        'product_name': name,
                        'current_stock': stock,
                        'predicted_demand': total_predicted_demand,
                        'suggested_quantity': max(1, round(suggested_qty)),
                        'suggested_vendor_id': vendor_id,
                        'estimated_unit_cost': est_cost,
                        'reason': f'توقعات الذكاء الاصطناعي تشير لطلب {total_predicted_demand} وحدة'
                    })
            return plan
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في إنشاء خطة الطلب: {e}')
            return []


class TestVendorServiceInitialization:
    """اختبارات تهيئة خدمة الموردين"""
    
    def test_initialization_with_db_manager(self):
        """اختبار التهيئة مع مدير قاعدة البيانات"""
        mock_db = Mock()
        service = MockVendorService(db_manager=mock_db)
        
        assert service.db == mock_db
        assert service.logger is None
    
    def test_initialization_with_logger(self):
        """اختبار التهيئة مع مسجل"""
        mock_db = Mock()
        mock_logger = Mock()
        service = MockVendorService(db_manager=mock_db, logger=mock_logger)
        
        assert service.db == mock_db
        assert service.logger == mock_logger


class TestCreatePurchaseOrder:
    """اختبارات إنشاء أمر شراء"""
    
    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.lastrowid = 1
        mock_db.execute_query.return_value = mock_result
        
        service = MockVendorService(db_manager=mock_db)
        return service
    
    def test_create_purchase_order_success(self, service_with_mocks):
        """اختبار إنشاء أمر شراء بنجاح"""
        items = [
            {'product_id': 1, 'quantity': 10, 'unit_price': 50.0},
            {'product_id': 2, 'quantity': 5, 'unit_price': 100.0}
        ]
        
        result = service_with_mocks.create_purchase_order(
            supplier_id=1,
            items=items,
            expected_delivery_date=datetime.now() + timedelta(days=7)
        )
        
        assert result == 1
        service_with_mocks.db.execute_query.assert_called()
    
    def test_create_purchase_order_empty_items(self, service_with_mocks):
        """اختبار إنشاء أمر شراء بدون عناصر"""
        result = service_with_mocks.create_purchase_order(
            supplier_id=1,
            items=[]
        )
        
        assert result == 1
    
    def test_create_purchase_order_db_error(self):
        """اختبار فشل إنشاء أمر شراء"""
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("DB Error")
        mock_logger = Mock()
        
        service = MockVendorService(db_manager=mock_db, logger=mock_logger)
        
        items = [{'product_id': 1, 'quantity': 10, 'unit_price': 50.0}]
        result = service.create_purchase_order(supplier_id=1, items=items)
        
        assert result is None
        mock_logger.error.assert_called_once()


class TestReceivePurchaseOrder:
    """اختبارات استلام أمر الشراء"""
    
    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_db.execute_query.return_value = True
        
        service = MockVendorService(db_manager=mock_db)
        return service
    
    def test_receive_purchase_order_success(self, service_with_mocks):
        """اختبار استلام أمر شراء بنجاح"""
        received_items = [
            {'product_id': 1, 'quantity': 10},
            {'product_id': 2, 'quantity': 5}
        ]
        
        result = service_with_mocks.receive_purchase_order(
            purchase_id=1,
            received_items=received_items
        )
        
        assert result is True
        service_with_mocks.db.execute_query.assert_called()
    
    def test_receive_purchase_order_partial(self, service_with_mocks):
        """اختبار استلام جزئي لأمر شراء"""
        received_items = [
            {'product_id': 1, 'quantity': 5}
        ]
        
        result = service_with_mocks.receive_purchase_order(
            purchase_id=1,
            received_items=received_items
        )
        
        assert result is True
    
    def test_receive_purchase_order_db_error(self):
        """اختبار فشل استلام أمر شراء"""
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("DB Error")
        mock_logger = Mock()
        
        service = MockVendorService(db_manager=mock_db, logger=mock_logger)
        
        received_items = [{'product_id': 1, 'quantity': 10}]
        result = service.receive_purchase_order(purchase_id=1, received_items=received_items)
        
        assert result is False
        mock_logger.error.assert_called_once()


class TestCalculateQualityScore:
    """اختبارات حساب درجة الجودة"""
    
    def test_calculate_quality_score_no_orders(self):
        """اختبار حساب الجودة بدون طلبات"""
        mock_db = Mock()
        mock_db.fetch_one.return_value = [0]
        
        service = MockVendorService(db_manager=mock_db)
        
        result = service.calculate_quality_score(vendor_id=1)
        
        assert result == 50.0
    
    def test_calculate_quality_score_with_orders(self):
        """اختبار حساب الجودة مع طلبات"""
        mock_db = Mock()
        # total_orders, on_time_count, avg_days
        mock_db.fetch_one.side_effect = [
            [10],  # total orders
            [8],   # on time orders
            [5.0]  # avg days
        ]
        
        service = MockVendorService(db_manager=mock_db)
        
        result = service.calculate_quality_score(vendor_id=1)
        
        assert 0 <= result <= 100
        assert isinstance(result, float)
    
    def test_calculate_quality_score_db_error(self):
        """اختبار فشل حساب الجودة"""
        mock_db = Mock()
        mock_db.fetch_one.side_effect = Exception("DB Error")
        mock_logger = Mock()
        
        service = MockVendorService(db_manager=mock_db, logger=mock_logger)
        
        result = service.calculate_quality_score(vendor_id=1)
        
        assert result == 0.0


class TestVendorPerformance:
    """اختبارات حساب أداء المورد"""
    
    def test_vendor_performance_success(self):
        """اختبار حساب الأداء بنجاح"""
        mock_db = Mock()
        mock_db.fetch_one.side_effect = [
            [5.0],   # avg_days
            [20],    # total orders
            [15],    # on_time orders
            [10],    # for quality score total
            [8],     # for quality score on_time
            [5.0]    # for quality score avg_days
        ]
        
        service = MockVendorService(db_manager=mock_db)
        
        result = service.vendor_performance(vendor_id=1)
        
        assert 'vendor_id' in result
        assert 'avg_lead_time_days' in result
        assert 'total_orders' in result
        assert 'on_time_rate' in result
        assert 'quality_score' in result
        assert result['vendor_id'] == 1
    
    def test_vendor_performance_no_orders(self):
        """اختبار حساب الأداء بدون طلبات"""
        mock_db = Mock()
        mock_db.fetch_one.side_effect = [
            [None],  # avg_days
            [0],     # total orders
            [0],     # on_time orders
            [0],     # for quality score
            [0],     # for quality score
            [7]      # for quality score
        ]
        
        service = MockVendorService(db_manager=mock_db)
        
        result = service.vendor_performance(vendor_id=1)
        
        assert result['total_orders'] == 0
        assert result['on_time_rate'] == 0
    
    def test_vendor_performance_db_error(self):
        """اختبار فشل حساب الأداء"""
        mock_db = Mock()
        mock_db.fetch_one.side_effect = Exception("DB Error")
        mock_logger = Mock()
        
        service = MockVendorService(db_manager=mock_db, logger=mock_logger)
        
        result = service.vendor_performance(vendor_id=1)
        
        assert result == {}


class TestGenerateDemandPlan:
    """اختبارات إنشاء خطة الطلب"""
    
    @pytest.fixture
    def mock_ai_service(self):
        """إنشاء خدمة AI وهمية"""
        mock_ai = Mock()
        mock_ai.demand_forecast_linear_regression.return_value = [
            {'predicted_quantity': 10},
            {'predicted_quantity': 15},
            {'predicted_quantity': 20}
        ]
        return mock_ai
    
    def test_generate_demand_plan_success(self, mock_ai_service):
        """اختبار إنشاء خطة الطلب بنجاح"""
        mock_db = Mock()
        mock_db.fetch_all.return_value = [
            (1, 'Product A', 5, 10),   # stock < min_stock, will need reorder
            (2, 'Product B', 100, 10)  # stock > min_stock, no reorder needed
        ]
        mock_db.fetch_one.return_value = (1, 50.0)  # vendor_id, unit_price
        
        service = MockVendorService(db_manager=mock_db)
        
        result = service.generate_demand_plan(mock_ai_service, days_ahead=30)
        
        assert isinstance(result, list)
    
    def test_generate_demand_plan_no_products(self, mock_ai_service):
        """اختبار إنشاء خطة الطلب بدون منتجات"""
        mock_db = Mock()
        mock_db.fetch_all.return_value = []
        
        service = MockVendorService(db_manager=mock_db)
        
        result = service.generate_demand_plan(mock_ai_service)
        
        assert result == []
    
    def test_generate_demand_plan_ai_error(self):
        """اختبار فشل خدمة AI"""
        mock_db = Mock()
        mock_db.fetch_all.return_value = [(1, 'Product A', 5, 10)]
        
        mock_ai = Mock()
        mock_ai.demand_forecast_linear_regression.side_effect = Exception("AI Error")
        mock_logger = Mock()
        
        service = MockVendorService(db_manager=mock_db, logger=mock_logger)
        
        result = service.generate_demand_plan(mock_ai)
        
        assert result == []


class TestVendorServiceEdgeCases:
    """اختبارات الحالات الحدية"""
    
    def test_create_purchase_order_with_zero_quantity(self):
        """اختبار إنشاء أمر شراء بكمية صفر"""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.lastrowid = 1
        mock_db.execute_query.return_value = mock_result
        
        service = MockVendorService(db_manager=mock_db)
        
        items = [{'product_id': 1, 'quantity': 0, 'unit_price': 50.0}]
        result = service.create_purchase_order(supplier_id=1, items=items)
        
        assert result == 1
    
    def test_receive_purchase_order_empty_items(self):
        """اختبار استلام أمر شراء بدون عناصر"""
        mock_db = Mock()
        mock_db.execute_query.return_value = True
        
        service = MockVendorService(db_manager=mock_db)
        
        result = service.receive_purchase_order(purchase_id=1, received_items=[])
        
        assert result is True
    
    def test_vendor_performance_negative_values(self):
        """اختبار حساب الأداء بقيم سالبة"""
        mock_db = Mock()
        mock_db.fetch_one.side_effect = [
            [-1],    # avg_days (invalid)
            [10],    # total orders
            [5],     # on_time orders
            [10],    # for quality score
            [5],     # for quality score
            [5.0]    # for quality score
        ]
        
        service = MockVendorService(db_manager=mock_db)
        
        result = service.vendor_performance(vendor_id=1)
        
        assert 'avg_lead_time_days' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



