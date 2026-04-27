import pytest
from unittest.mock import MagicMock, patch

# افترض أن الملف الأصلي موجود في src/security/mfa_service.py
# قم بتعديل المسار إذا كان مختلفاً
from src.security.mfa_service import MFAService
from src.core.database_manager import DatabaseManager
from src.core.encryption_manager import EncryptionManager

@pytest.fixture
def mock_db_manager(mocker):
    """Fixture لمحاكاة مدير قاعدة البيانات (DatabaseManager)."""
    return mocker.MagicMock(spec=DatabaseManager)

@pytest.fixture
def mock_encryption_manager(mocker):
    """Fixture لمحاكاة مدير التشفير (EncryptionManager)."""
    mock = mocker.MagicMock(spec=EncryptionManager)
    # محاكاة سلوك التشفير وفك التشفير
    mock.encrypt.side_effect = lambda data: f"encrypted_{data}".encode('utf-8')
    mock.decrypt.side_effect = lambda data: data.decode('utf-8').replace("encrypted_", "")
    return mock

@pytest.fixture
def mfa_service(mock_db_manager, mock_encryption_manager):
    """Fixture لإنشاء نسخة من MFAService مع اعتماديات محاكاة."""
    return MFAService(
        user_id=1,
        db_manager=mock_db_manager,
        encryption_manager=mock_encryption_manager
    )

def test_generate_mfa_secret_and_qr_code(mfa_service: MFAService):
    """
    اختبار وظيفة إنشاء سر MFA جديد ورمز QR.
    - يتحقق من أن السر يتم إنشاؤه.
    - يتحقق من أن السر يتم تشفيره قبل حفظه.
    - يتحقق من أن دالة الحفظ في قاعدة البيانات تُستدعى.
    """
    # محاكاة pyotp.random_base32 لإرجاع قيمة ثابتة يمكن التنبؤ بها
    with patch('pyotp.random_base32', return_value='TESTSECRET1234567890') as mock_random_base32:
        
        result = mfa_service.generate_mfa_secret_and_qr_code("testuser", "TestApp")

        # 1. التأكد من أن النتيجة تحتوي على البيانات المتوقعة
        assert "secret" in result
        assert result["secret"] == 'TESTSECRET1234567890'
        assert result["qr_code_data_uri"].startswith("data:image/png;base64,")

        # 2. التأكد من أن دالة إنشاء السر العشوائي قد استُدعيت مرة واحدة
        mock_random_base32.assert_called_once()

        # 3. التأكد من أن السر الجديد قد تم حفظه في قاعدة البيانات بالشكل المشفر
        mfa_service.db_manager.update_user_mfa_secret.assert_called_once_with(
            user_id=1, 
            secret="encrypted_TESTSECRET1234567890"
        )



