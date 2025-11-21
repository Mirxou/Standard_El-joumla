@echo off
chcp 65001 > nul
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║         🎭 اختبارات Playwright - اختبار الواجهة 🎭          ║
echo ║              Playwright UI Testing                             ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

echo 📦 تثبيت Playwright...
pip install playwright pytest-playwright -q
playwright install

echo.
echo ⚠️  ملاحظة مهمة:
echo   يجب تشغيل التطبيق أولاً في نافذة منفصلة قبل تشغيل الاختبارات
echo   قم بتشغيل: python main.py
echo.
pause

echo.
echo 🚀 تشغيل اختبارات Playwright...
echo.

pytest tests/e2e/ --headed --slowmo=500 --html=test_reports/playwright_tests.html --self-contained-html

echo.
echo ✅ اكتملت اختبارات Playwright!
echo 📊 التقرير: test_reports\playwright_tests.html
echo.
pause
