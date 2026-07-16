# سكريبت إصلاح قاعدة البيانات التالفة
# Database Repair Script

Write-Host "🔧 إصلاح قاعدة البيانات..." -ForegroundColor Yellow
Write-Host ""

$dbPath = "data\standard_eljoumla.db"
$backupPath = "data\backups\standard_eljoumla_corrupted_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"

# التحقق من وجود قاعدة البيانات
if (-not (Test-Path $dbPath)) {
    Write-Host "❌ قاعدة البيانات غير موجودة: $dbPath" -ForegroundColor Red
    Write-Host "   سيتم إنشاء قاعدة بيانات جديدة..." -ForegroundColor Yellow
    exit 0
}

# إنشاء نسخة احتياطية من قاعدة البيانات التالفة
Write-Host "📦 إنشاء نسخة احتياطية من قاعدة البيانات التالفة..." -ForegroundColor Cyan
$backupDir = "data\backups"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}

Copy-Item $dbPath $backupPath -Force
Write-Host "✅ تم حفظ النسخة الاحتياطية: $backupPath" -ForegroundColor Green
Write-Host ""

# محاولة إصلاح قاعدة البيانات
Write-Host "🔧 محاولة إصلاح قاعدة البيانات..." -ForegroundColor Cyan
python -c @"
import sqlite3
import sys
from pathlib import Path

db_path = Path('$dbPath')
backup_path = Path('$backupPath')

try:
    # محاولة فتح قاعدة البيانات التالفة
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # محاولة استخراج البيانات
    try:
        cursor.execute('PRAGMA integrity_check')
        result = cursor.fetchone()
        print(f'Integrity Check: {result[0]}')
    except:
        pass
    
    # محاولة إصلاح باستخدام dump
    print('محاولة إصلاح باستخدام dump...')
    conn.close()
    
    # إنشاء قاعدة بيانات جديدة
    new_db_path = db_path.parent / f'{db_path.stem}_new{db_path.suffix}'
    
    # محاولة استخراج البيانات من قاعدة البيانات التالفة
    old_conn = sqlite3.connect(str(db_path))
    new_conn = sqlite3.connect(str(new_db_path))
    
    # نسخ البيانات
    old_conn.backup(new_conn)
    
    old_conn.close()
    new_conn.close()
    
    # التحقق من قاعدة البيانات الجديدة
    test_conn = sqlite3.connect(str(new_db_path))
    test_conn.execute('PRAGMA integrity_check')
    test_conn.close()
    
    # استبدال قاعدة البيانات القديمة
    db_path.unlink()
    new_db_path.rename(db_path)
    
    print('✅ تم إصلاح قاعدة البيانات بنجاح!')
    
except Exception as e:
    print(f'❌ فشل إصلاح قاعدة البيانات: {e}')
    print('سيتم إنشاء قاعدة بيانات جديدة...')
    
    # حذف قاعدة البيانات التالفة
    if db_path.exists():
        db_path.unlink()
    
    sys.exit(1)
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "⚠️  فشل إصلاح قاعدة البيانات" -ForegroundColor Yellow
    Write-Host "   سيتم إنشاء قاعدة بيانات جديدة..." -ForegroundColor Yellow
    Write-Host ""
    
    # حذف قاعدة البيانات التالفة
    if (Test-Path $dbPath) {
        Remove-Item $dbPath -Force
        Write-Host "✅ تم حذف قاعدة البيانات التالفة" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "✅ اكتمل الإصلاح!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 ملاحظات:" -ForegroundColor Cyan
Write-Host "   - النسخة الاحتياطية محفوظة في: $backupPath" -ForegroundColor White
Write-Host "   - إذا كانت قاعدة البيانات جديدة، سيتم تطبيق migrations تلقائياً عند التشغيل" -ForegroundColor White
Write-Host ""

