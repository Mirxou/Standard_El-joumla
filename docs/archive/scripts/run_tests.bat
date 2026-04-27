@echo off
cd "c:\Users\aboun\Desktop\Logical Version trae"
python -m pytest tests/unit/test_backup_service.py -v > test_output.txt 2>&1
echo Exit code: %ERRORLEVEL%
type test_output.txt
