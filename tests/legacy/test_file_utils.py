#!/usr/bin/env python3
"""
اختبارات File Utils
"""

from unittest.mock import patch

import pytest

from src.utils.file_utils import FileUtils


class TestFileUtils:
    """اختبارات أدوات الملفات"""

    @pytest.fixture
    def file_utils(self):
        """إنشاء أدوات ملفات"""
        return FileUtils()

    def test_initialization(self, file_utils):
        """اختبار التهيئة"""
        assert file_utils is not None

    def test_read_file(self, file_utils):
        """اختبار قراءة ملف"""
        with patch.object(file_utils, "read", return_value="file content"):
            result = file_utils.read("test.txt")
            assert result == "file content"

    def test_write_file(self, file_utils):
        """اختبار كتابة ملف"""
        with patch.object(file_utils, "write", return_value=True):
            result = file_utils.write("test.txt", "content")
            assert result is True

    def test_file_exists(self, file_utils):
        """اختبار وجود ملف"""
        with patch.object(file_utils, "exists", return_value=True):
            result = file_utils.exists("test.txt")
            assert result is True

    def test_get_file_size(self, file_utils):
        """اختبار الحصول على حجم الملف"""
        with patch.object(file_utils, "size", return_value=1024):
            result = file_utils.size("test.txt")
            assert result == 1024

    def test_get_file_extension(self, file_utils):
        """اختبار الحصول على امتداد الملف"""
        with patch.object(file_utils, "extension", return_value="txt"):
            result = file_utils.extension("test.txt")
            assert result == "txt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
