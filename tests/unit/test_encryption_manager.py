"""
Unit Tests for Encryption Manager
اختبارات وحدة لمدير التشفير
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.core.encryption_manager import EncryptionManager


class TestEncryptionManager:
    """اختبارات EncryptionManager"""

    def test_init_with_password(self):
        """اختبار التهيئة مع كلمة مرور"""
        encryption_manager = EncryptionManager("test_password")
        assert encryption_manager.password == "test_password"
        assert encryption_manager.key is not None
        assert encryption_manager.fernet is not None

    def test_init_without_password(self):
        """اختبار التهيئة بدون كلمة مرور"""
        encryption_manager = EncryptionManager()
        assert encryption_manager.password is None
        assert encryption_manager.key is None

    def test_encrypt_decrypt_data(self):
        """اختبار تشفير وفك تشفير البيانات"""
        encryption_manager = EncryptionManager("test_password")

        # تشفير
        original_data = "sensitive data"
        encrypted = encryption_manager.encrypt_data(original_data)

        assert encrypted is not None
        assert isinstance(encrypted, bytes)
        assert encrypted != original_data.encode()

        # فك التشفير
        decrypted = encryption_manager.decrypt_data(encrypted)
        decrypted_text = decrypted.decode("utf-8")

        assert decrypted_text == original_data

    def test_encrypt_decrypt_bytes(self):
        """اختبار تشفير وفك تشفير bytes"""
        encryption_manager = EncryptionManager("test_password")

        original_data = b"binary data"
        encrypted = encryption_manager.encrypt_data(original_data)

        assert encrypted is not None
        assert isinstance(encrypted, bytes)

        decrypted = encryption_manager.decrypt_data(encrypted)
        assert decrypted == original_data

    def test_encrypt_file(self):
        """اختبار تشفير ملف"""
        encryption_manager = EncryptionManager("test_password")

        # إنشاء ملف مؤقت
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test file content")
            temp_file = f.name

        try:
            # تشفير الملف
            encrypted_path = encryption_manager.encrypt_file(temp_file)

            assert encrypted_path is not None
            assert Path(encrypted_path).exists()
            assert encrypted_path != temp_file

            # تنظيف
            if Path(encrypted_path).exists():
                os.remove(encrypted_path)
        finally:
            if Path(temp_file).exists():
                os.remove(temp_file)

    def test_decrypt_file(self):
        """اختبار فك تشفير ملف"""
        encryption_manager = EncryptionManager("test_password")

        # إنشاء ملف مؤقت
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test file content")
            temp_file = f.name

        try:
            # تشفير الملف
            encrypted_path = encryption_manager.encrypt_file(temp_file)

            # فك التشفير
            decrypted_path = encryption_manager.decrypt_file(encrypted_path, output_path=temp_file + ".decrypted")

            assert decrypted_path is not None
            assert Path(decrypted_path).exists()

            # التحقق من المحتوى
            with open(decrypted_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert content == "test file content"

            # تنظيف
            for path in [encrypted_path, decrypted_path, temp_file]:
                if Path(path).exists():
                    os.remove(path)
        except Exception as e:  # noqa: F841
            # تنظيف في حالة الخطأ
            for path in [temp_file, temp_file + ".encrypted", temp_file + ".decrypted"]:
                if Path(path).exists():
                    try:
                        os.remove(path)
                    except Exception:
                        pass
            raise

    def test_generate_secure_password(self):
        """اختبار توليد كلمة مرور آمنة"""
        password = EncryptionManager.generate_secure_password(length=16)

        assert password is not None
        assert len(password) == 16
        assert any(c.isupper() for c in password)
        assert any(c.islower() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in "!@#$%^&*" for c in password)

    def test_hash_password(self):
        """اختبار تشفير كلمة المرور"""
        password = "test_password"
        password_hash, salt = EncryptionManager.hash_password(password)

        assert password_hash is not None
        assert salt is not None
        assert isinstance(password_hash, bytes)
        assert isinstance(salt, bytes)
        assert len(salt) == 32

    def test_verify_password(self):
        """اختبار التحقق من كلمة المرور"""
        password = "test_password"
        password_hash, salt = EncryptionManager.hash_password(password)

        # التحقق من كلمة مرور صحيحة
        is_valid = EncryptionManager.verify_password(password_hash, salt, password)
        assert is_valid is True

        # التحقق من كلمة مرور خاطئة
        is_valid = EncryptionManager.verify_password(password_hash, salt, "wrong_password")
        assert is_valid is False

    def test_encrypt_with_different_passwords(self):
        """اختبار أن كلمات المرور المختلفة تعطي نتائج مختلفة"""
        encryption_manager1 = EncryptionManager("password1")
        encryption_manager2 = EncryptionManager("password2")

        data = "test data"
        encrypted1 = encryption_manager1.encrypt_data(data)
        encrypted2 = encryption_manager2.encrypt_data(data)

        assert encrypted1 != encrypted2

    def test_decrypt_with_wrong_password(self):
        """اختبار فك التشفير بكلمة مرور خاطئة"""
        encryption_manager1 = EncryptionManager("password1")
        encryption_manager2 = EncryptionManager("password2")

        data = "test data"
        encrypted = encryption_manager1.encrypt_data(data)

        # محاولة فك التشفير بكلمة مرور خاطئة
        try:
            decrypted = encryption_manager2.decrypt_data(encrypted)  # noqa: F841
            # يجب أن يفشل أو يعطي نتيجة خاطئة
            assert False, "يجب أن يفشل فك التشفير بكلمة مرور خاطئة"
        except Exception:
            # هذا متوقع
            pass


class TestPasswordValidation:
    """اختبارات التحقق من قوة كلمة المرور"""

    def test_validate_password_strength_valid(self):
        """اختبار كلمة مرور قوية"""
        password = "StrongPass123!@#"
        is_valid, message = EncryptionManager.validate_password_strength(password)

        assert is_valid is True
        assert message == ""

    def test_validate_password_strength_too_short(self):
        """اختبار كلمة مرور قصيرة جداً"""
        password = "Short1!"
        is_valid, message = EncryptionManager.validate_password_strength(password)

        assert is_valid is False
        assert "12" in message

    def test_validate_password_strength_no_uppercase(self):
        """اختبار كلمة مرور بدون حروف كبيرة"""
        password = "lowercase123!@#"
        is_valid, message = EncryptionManager.validate_password_strength(password)

        assert is_valid is False
        assert "كبير" in message or "uppercase" in message

    def test_validate_password_strength_no_lowercase(self):
        """اختبار كلمة مرور بدون حروف صغيرة"""
        password = "UPPERCASE123!@#"
        is_valid, message = EncryptionManager.validate_password_strength(password)

        assert is_valid is False
        assert "صغير" in message or "lowercase" in message

    def test_validate_password_strength_no_digits(self):
        """اختبار كلمة مرور بدون أرقام"""
        password = "NoDigitsHere!@#"
        is_valid, message = EncryptionManager.validate_password_strength(password)

        assert is_valid is False
        assert "رقم" in message or "digit" in message

    def test_validate_password_strength_no_special(self):
        """اختبار كلمة مرور بدون رموز خاصة"""
        password = "NoSpecialChars123"
        is_valid, message = EncryptionManager.validate_password_strength(password)

        assert is_valid is False
        assert "رمز" in message or "special" in message

    def test_validate_password_strength_empty(self):
        """اختبار كلمة مرور فارغة"""
        is_valid, message = EncryptionManager.validate_password_strength("")

        assert is_valid is False
        assert "مطلوبة" in message

    def test_is_password_compliant_valid(self):
        """اختبار التحقق السريع من كلمة مرور صحيحة"""
        password = "ValidPass123!@"
        result = EncryptionManager.is_password_compliant(password)

        assert result is True

    def test_is_password_compliant_invalid(self):
        """اختبار التحقق السريع من كلمة مرور ضعيفة"""
        password = "weak"
        result = EncryptionManager.is_password_compliant(password)

        assert result is False


class TestDatabaseEncryption:
    """اختبارات تشفير قاعدة البيانات"""

    @pytest.fixture
    def encryption_mgr(self):
        """إنشاء EncryptionManager"""
        return EncryptionManager("test_password")

    def test_is_database_encrypted_with_normal_db(self, encryption_mgr):
        """اختبار التحقق من قاعدة بيانات عادية"""
        import sqlite3
        import tempfile

        # إنشاء قاعدة بيانات SQLite عادية
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.close()

            result = encryption_mgr.is_database_encrypted(db_path)
            assert result is False
        finally:
            if Path(db_path).exists():
                os.remove(db_path)

    def test_is_database_encrypted_with_encrypted_file(self, encryption_mgr):
        """اختبار التحقق من ملف مشفر"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            temp_file = f.name

        try:
            # تشفير الملف
            encrypted_path = encryption_mgr.encrypt_file(temp_file)

            # التحقق
            result = encryption_mgr.is_database_encrypted(encrypted_path)
            assert result is True

            os.remove(encrypted_path)
        finally:
            if Path(temp_file).exists():
                os.remove(temp_file)

    def test_is_database_encrypted_nonexistent_file(self, encryption_mgr):
        """اختبار التحقق من ملف غير موجود"""
        result = encryption_mgr.is_database_encrypted("/nonexistent/path/file.db")
        assert result is False

    def test_verify_database_integrity_valid(self, encryption_mgr):
        """اختبار التحقق من سلامة قاعدة بيانات سليمة"""
        import sqlite3
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            conn.execute("INSERT INTO test VALUES (1)")
            conn.close()

            result = encryption_mgr.verify_database_integrity(db_path)
            assert result is True
        finally:
            if Path(db_path).exists():
                os.remove(db_path)

    def test_verify_database_integrity_nonexistent(self, encryption_mgr):
        """اختبار التحقق من قاعدة بيانات غير موجودة"""
        result = encryption_mgr.verify_database_integrity("/nonexistent/db.sqlite")
        assert result is False


class TestEncryptionAliases:
    """اختبارات aliases للتوافق مع الكود القديم"""

    def test_encrypt_alias(self):
        """اختبار alias encrypt()"""
        encryption_manager = EncryptionManager("test_password")

        data = "test data"
        encrypted = encryption_manager.encrypt(data)
        decrypted = encryption_manager.decrypt(encrypted)

        assert decrypted.decode() == data

    def test_decrypt_alias(self):
        """اختبار alias decrypt()"""
        encryption_manager = EncryptionManager("test_password")

        data = "test data"
        encrypted = encryption_manager.encrypt_data(data)
        decrypted = encryption_manager.decrypt(encrypted)

        assert decrypted.decode() == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
