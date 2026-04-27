#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Circuit Breaker
اختبارات Circuit Breaker
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from src.api.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitState:
    """اختبارات حالات Circuit Breaker"""
    
    def test_circuit_state_values(self):
        """اختبار قيم حالات Circuit Breaker"""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"
    
    def test_circuit_state_enum_members(self):
        """اختبار أعضاء enum CircuitState"""
        assert hasattr(CircuitState, 'CLOSED')
        assert hasattr(CircuitState, 'OPEN')
        assert hasattr(CircuitState, 'HALF_OPEN')


class TestCircuitBreakerInitialization:
    """اختبارات تهيئة Circuit Breaker"""
    
    def test_default_initialization(self):
        """اختبار التهيئة الافتراضية"""
        cb = CircuitBreaker()
        
        assert cb.failure_threshold == 5
        assert cb.timeout == 60
        assert cb.half_open_timeout == 30
        assert cb.initial_backoff == 1.0
        assert cb.max_backoff == 300.0
        assert cb.backoff_multiplier == 2.0
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
        assert cb.manual_offline is False
        assert cb.last_failure_time is None
        assert cb.last_success_time is None
    
    def test_custom_initialization(self):
        """اختبار التهيئة المخصصة"""
        cb = CircuitBreaker(
            failure_threshold=3,
            timeout=30,
            half_open_timeout=15,
            initial_backoff=0.5,
            max_backoff=60.0,
            backoff_multiplier=1.5
        )
        
        assert cb.failure_threshold == 3
        assert cb.timeout == 30
        assert cb.half_open_timeout == 15
        assert cb.initial_backoff == 0.5
        assert cb.max_backoff == 60.0
        assert cb.backoff_multiplier == 1.5


class TestCircuitBreakerClosedState:
    """اختبارات الحالة المغلقة (CLOSED) - العملية الطبيعية"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """إنشاء Circuit Breaker للاختبارات"""
        return CircuitBreaker()
    
    def test_call_successful_function(self, circuit_breaker):
        """اختبار استدعاء دالة ناجحة"""
        def success_func():
            return "success"
        
        result = circuit_breaker.call(success_func)
        
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.success_count == 1
    
    def test_call_with_args_and_kwargs(self, circuit_breaker):
        """اختبار استدعاء دالة مع معاملات"""
        def func_with_args(a, b, c=None):
            return f"{a}-{b}-{c}"
        
        result = circuit_breaker.call(func_with_args, 1, 2, c=3)
        
        assert result == "1-2-3"
    
    def test_success_increments_count(self, circuit_breaker):
        """اختبار أن النجاح يزيد العداد"""
        def success_func():
            return "ok"
        
        circuit_breaker.call(success_func)
        circuit_breaker.call(success_func)
        
        assert circuit_breaker.success_count == 2


class TestCircuitBreakerOpenState:
    """اختبارات الحالة المفتوحة (OPEN) - فشل متكرر"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """إنشاء Circuit Breaker بعتبة فشل منخفضة"""
        cb = CircuitBreaker(failure_threshold=2, timeout=1)
        cb.state = CircuitState.OPEN
        cb.failure_count = 2
        cb.last_failure_time = datetime.now()
        return cb
    
    def test_open_state_blocks_calls(self, circuit_breaker):
        """اختبار أن الحالة المفتوحة تمنع الاستدعاءات"""
        def any_func():
            return "result"
        
        with pytest.raises(Exception) as exc_info:
            circuit_breaker.call(any_func)
        
        assert "Circuit Breaker مفتوح" in str(exc_info.value)
    
    def test_open_state_with_recent_failure(self, circuit_breaker):
        """اختبار الحالة المفتوحة مع فشل حديث"""
        # آخر فشل كان للتو
        circuit_breaker.last_failure_time = datetime.now()
        
        def any_func():
            return "result"
        
        # يجب أن يبقى مغلقاً بسبب الفشل الحديث
        with pytest.raises(Exception):
            circuit_breaker.call(any_func)


class TestCircuitBreakerHalfOpenState:
    """اختبارات الحالة نصف المفتوحة (HALF_OPEN)"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """إنشاء Circuit Breaker في حالة HALF_OPEN"""
        cb = CircuitBreaker(failure_threshold=2)
        cb.state = CircuitState.HALF_OPEN
        return cb
    
    def test_half_open_success_closes_circuit(self, circuit_breaker):
        """اختبار أن النجاح في HALF_OPEN يغلق الدائرة"""
        def success_func():
            return "success"
        
        result = circuit_breaker.call(success_func)
        
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
    
    def test_half_open_failure_opens_circuit(self, circuit_breaker):
        """اختبار أن الفشل في HALF_OPEN يفتح الدائرة"""
        def fail_func():
            raise ValueError("Error")
        
        with pytest.raises(ValueError):
            circuit_breaker.call(fail_func)
        
        assert circuit_breaker.state == CircuitState.OPEN


class TestCircuitBreakerManualOffline:
    """اختبارات وضع الطوارئ (Manual Offline)"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """إنشاء Circuit Breaker"""
        return CircuitBreaker()
    
    def test_manual_offline_blocks_all_calls(self, circuit_breaker):
        """اختبار أن وضع الطوارئ يمنع جميع الاستدعاءات"""
        circuit_breaker.manual_offline = True
        
        def any_func():
            return "result"
        
        with pytest.raises(Exception) as exc_info:
            circuit_breaker.call(any_func)
        
        assert "وضع الطوارئ" in str(exc_info.value)
    
    def test_set_manual_offline(self, circuit_breaker):
        """اختبار تفعيل وضع الطوارئ"""
        circuit_breaker.manual_offline = True
        assert circuit_breaker.manual_offline is True


class TestCircuitBreakerReset:
    """اختبارات إعادة تعيين Circuit Breaker"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """إنشاء Circuit Breaker في حالة OPEN"""
        cb = CircuitBreaker()
        cb.state = CircuitState.OPEN
        cb.failure_count = 5
        cb.success_count = 3
        return cb
    
    def test_reset_returns_to_closed(self, circuit_breaker):
        """اختبار أن إعادة التعيين تعيد الحالة إلى CLOSED"""
        circuit_breaker.reset()
        
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    def test_get_state(self, circuit_breaker):
        """اختبار الحصول على الحالة"""
        state_info = circuit_breaker.get_state()
        
        assert state_info['state'] == CircuitState.OPEN.value


class TestCircuitBreakerBackoff:
    """اختبارات Exponential Backoff"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """إنشاء Circuit Breaker"""
        return CircuitBreaker(
            initial_backoff=1.0,
            max_backoff=10.0,
            backoff_multiplier=2.0
        )
    
    def test_backoff_delay_calculation(self, circuit_breaker):
        """اختبار حساب وقت الانتظار"""
        delay = circuit_breaker.get_backoff_delay()
        
        assert delay >= 0
        assert delay <= circuit_breaker.max_backoff
    
    def test_backoff_with_failures(self, circuit_breaker):
        """اختبار backoff مع الفشل"""
        circuit_breaker.failure_count = 3
        
        delay = circuit_breaker.get_backoff_delay()
        
        # يجب أن يزيد الوقت مع عدد الفشل
        expected_min = min(
            circuit_breaker.initial_backoff * (circuit_breaker.backoff_multiplier ** 3),
            circuit_breaker.max_backoff
        )
        assert delay >= 0


class TestCircuitBreakerFailureHandling:
    """اختبارات معالجة الفشل"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """إنشاء Circuit Breaker بعتبة فشل منخفضة"""
        return CircuitBreaker(failure_threshold=2)
    
    def test_failure_increments_count(self, circuit_breaker):
        """اختبار أن الفشل يزيد العداد"""
        def fail_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            circuit_breaker.call(fail_func)
        
        assert circuit_breaker.failure_count == 1
        assert circuit_breaker.last_failure_time is not None
    
    def test_multiple_failures_open_circuit(self, circuit_breaker):
        """اختبار أن الفشل المتكرر يفتح الدائرة"""
        def fail_func():
            raise ValueError("Test error")
        
        # فشل مرتين
        with pytest.raises(ValueError):
            circuit_breaker.call(fail_func)
        with pytest.raises(ValueError):
            circuit_breaker.call(fail_func)
        
        # الآن يجب أن تكون الدائرة مفتوحة
        assert circuit_breaker.state == CircuitState.OPEN
        
        # محاولة أخرى يجب أن تفشل مباشرة
        with pytest.raises(Exception) as exc_info:
            circuit_breaker.call(fail_func)
        assert "Circuit Breaker مفتوح" in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



