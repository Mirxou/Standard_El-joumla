@echo off
chcp 65001 >nul
title الإصدار المنطقي - API Server v1.1.0

echo ===============================================
echo    الإصدار المنطقي - Logical Version
echo    API Server v1.1.0
echo ===============================================
echo.

cd /d "%~dp0"

echo [1/3] جاري التحقق من البيئة...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python غير مثبت! يرجى تثبيت Python 3.11 أو أحدث
    pause
    exit /b 1
)
echo ✅ Python جاهز

echo.
echo [2/3] جاري تحميل الإعدادات...
if not exist config\app_config.json (
    echo ❌ ملف الإعدادات غير موجود!
    pause
    exit /b 1
)
echo ✅ الإعدادات جاهزة

echo.
echo [3/3] جاري تشغيل API Server...
echo.
echo 🌐 سيتم تشغيل الخادم على:
echo    http://localhost:8000
echo    http://127.0.0.1:8000
echo.
echo 📚 للوصول للتوثيق:
echo    http://localhost:8000/docs (Swagger UI)
echo    http://localhost:8000/redoc (ReDoc)
echo.
echo ⚠️  اضغط Ctrl+C لإيقاف الخادم
echo.
echo ===============================================

python scripts\run_api_server.py

if errorlevel 1 (
    echo.
    echo ===============================================
    echo ❌ فشل تشغيل API Server!
    echo.
    echo الحلول المحتملة:
    echo 1. تأكد من تثبيت المكتبات: pip install -r requirements.txt
    echo 2. تحقق من أن المنفذ 8000 غير مستخدم
    echo 3. راجع ملف logs للمزيد من التفاصيل
    echo ===============================================
    pause
    exit /b 1
)

echo.
echo ===============================================
echo تم إيقاف API Server
echo ===============================================
pause
