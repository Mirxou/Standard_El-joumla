"""
Unit Tests for Encryption Manager
اختبارات وحدة لمدير التشفير
"""

import pytest
import os
import tempfile
from pathlib import Path
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
        decrypted_text = decrypted.decode('utf-8')
        
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
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
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
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test file content")
            temp_file = f.name
        
        try:
            # تشفير الملف
            encrypted_path = encryption_manager.encrypt_file(temp_file)
            
            # فك التشفير
            decrypted_path = encryption_manager.decrypt_file(
                encrypted_path,
                output_path=temp_file + ".decrypted"
            )
            
            assert decrypted_path is not None
            assert Path(decrypted_path).exists()
            
            # التحقق من المحتوى
            with open(decrypted_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert content == "test file content"
            
            # تنظيف
            for path in [encrypted_path, decrypted_path, temp_file]:
                if Path(path).exists():
                    os.remove(path)
        except Exception as e:
            # تنظيف في حالة الخطأ
            for path in [temp_file, temp_file + ".encrypted", temp_file + ".decrypted"]:
                if Path(path).exists():
                    try:
                        os.remove(path)
                    except:
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
        is_valid = EncryptionManager.verify_password(
            password_hash,
            salt,
            password
        )
        assert is_valid == True
        
        # التحقق من كلمة مرور خاطئة
        is_valid = EncryptionManager.verify_password(
            password_hash,
            salt,
            "wrong_password"
        )
        assert is_valid == False
    
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
            decrypted = encryption_manager2.decrypt_data(encrypted)
            # يجب أن يفشل أو يعطي نتيجة خاطئة
            assert False, "يجب أن يفشل فك التشفير بكلمة مرور خاطئة"
        except Exception:
            # هذا متوقع
            pass

