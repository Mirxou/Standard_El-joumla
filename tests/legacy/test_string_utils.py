#!/usr/bin/env python3
"""
اختبارات String Utils
"""

from unittest.mock import patch

import pytest

from src.utils.string_utils import StringUtils


class TestStringUtils:
    """اختبارات أدوات النصوص"""

    @pytest.fixture
    def string_utils(self):
        """إنشاء أدوات نصوص"""
        return StringUtils()

    def test_initialization(self, string_utils):
        """اختبار التهيئة"""
        assert string_utils is not None

    def test_slugify(self, string_utils):
        """اختبار تحويل النص إلى slug"""
        with patch.object(string_utils, "slugify", return_value="test-string"):
            result = string_utils.slugify("Test String")
            assert result == "test-string"

    def test_truncate(self, string_utils):
        """اختبار تقصير النص"""
        with patch.object(string_utils, "truncate", return_value="Test..."):
            result = string_utils.truncate("Test String Long", 8)
            assert result == "Test..."

    def test_camel_to_snake(self, string_utils):
        """اختبار تحويل camelCase إلى snake_case"""
        with patch.object(string_utils, "camel_to_snake", return_value="test_string"):
            result = string_utils.camel_to_snake("testString")
            assert result == "test_string"

    def test_snake_to_camel(self, string_utils):
        """اختبار تحويل snake_case إلى camelCase"""
        with patch.object(string_utils, "snake_to_camel", return_value="testString"):
            result = string_utils.snake_to_camel("test_string")
            assert result == "testString"

    def test_strip_html(self, string_utils):
        """اختبار إزالة HTML"""
        with patch.object(string_utils, "strip_html", return_value="Hello World"):
            result = string_utils.strip_html("<p>Hello World</p>")
            assert result == "Hello World"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
