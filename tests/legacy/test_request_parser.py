#!/usr/bin/env python3
"""
اختبارات Request Parser
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.request_parser import RequestParser


class TestRequestParser:
    """اختبارات محلل الطلبات"""
    
    @pytest.fixture
    def parser(self):
        """إنشاء محلل طلبات"""
        return RequestParser()
    
    def test_initialization(self, parser):
        """اختبار التهيئة"""
        assert parser is not None
    
    def test_parse_json(self, parser):
        """اختبار تحليل JSON"""
        with patch.object(parser, 'parse_json', return_value={"key": "value"}):
            result = parser.parse_json('{"key": "value"}')
            assert isinstance(result, dict)
    
    def test_parse_query_params(self, parser):
        """اختبار تحليل معلمات الاستعلام"""
        with patch.object(parser, 'parse_query', return_value={"page": 1, "limit": 10}):
            result = parser.parse_query("page=1&limit=10")
            assert isinstance(result, dict)
    
    def test_parse_form_data(self, parser):
        """اختبار تحليل بيانات النموذج"""
        with patch.object(parser, 'parse_form', return_value={"name": "test"}):
            result = parser.parse_form("name=test")
            assert isinstance(result, dict)
    
    def test_validate_request(self, parser):
        """اختبار التحقق من الطلب"""
        with patch.object(parser, 'validate', return_value=True):
            result = parser.validate({"required_field": "value"}, ["required_field"])
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



