@echo off
cd "c:\Users\aboun\Desktop\Logical Version trae"
echo =========================================
echo Running pytest...
echo =========================================
python -m pytest tests/unit/ -v --tb=short > pytest_output.txt 2>&1
echo Exit code: %ERRORLEVEL%
echo.
echo =========================================
echo First 50 lines of output:
echo =========================================
head -50 pytest_output.txt 2>nul || type pytest_output.txt | findstr /N "." | findstr "^[1-5][0-9]:" 2>nul || type pytest_output.txt
echo.
echo =========================================
echo Errors and Failures:
echo =========================================
type pytest_output.txt | findstr /C:"FAILED" /C:"ERROR"
echo.
pause
