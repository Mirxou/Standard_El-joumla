# PowerShell Script لتشغيل مراقبة السجلات في الخلفية
# PowerShell Script to start log monitoring in background

param(
    [int]$Interval = 300,  # فترة الفحص بالثواني (افتراضي: 5 دقائق)
    [switch]$Hidden = $true  # تشغيل في نافذة مخفية
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🔍 بدء مراقبة السجلات في الخلفية" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# الحصول على مسار المشروع
$projectPath = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectPath ".venv\Scripts\python.exe"
$monitorScript = Join-Path $projectPath "scripts\monitor_logs.py"

# التحقق من وجود Python
if (-not (Test-Path $pythonPath)) {
    Write-Host "⚠️  لم يتم العثور على Python في: $pythonPath" -ForegroundColor Yellow
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $pythonPath) {
        Write-Host "❌ لم يتم العثور على Python. يرجى تثبيته أولاً." -ForegroundColor Red
        exit 1
    }
}

Write-Host "📁 مسار المشروع: $projectPath" -ForegroundColor Gray
Write-Host "🐍 مسار Python: $pythonPath" -ForegroundColor Gray
Write-Host "⏱️  فترة الفحص: $Interval ثانية ($([math]::Round($Interval/60, 1)) دقيقة)" -ForegroundColor Gray
Write-Host ""

# إنشاء ملف batch لتشغيل المراقبة
$batchFile = Join-Path $projectPath "scripts\monitor_background.bat"
$batchContent = @"
@echo off
cd /d "$projectPath"
"$pythonPath" "$monitorScript" --continuous $Interval
pause
"@

$batchContent | Out-File -FilePath $batchFile -Encoding ASCII

Write-Host "📝 تم إنشاء ملف التشغيل: $batchFile" -ForegroundColor Green
Write-Host ""

# تشغيل المراقبة
Write-Host "🚀 بدء تشغيل المراقبة..." -ForegroundColor Yellow

if ($Hidden) {
    # تشغيل في نافذة مخفية
    $process = Start-Process -FilePath $pythonPath -ArgumentList "`"$monitorScript`", `"--continuous`", `"$Interval`"" -WorkingDirectory $projectPath -WindowStyle Hidden -PassThru
    Write-Host "✅ تم تشغيل المراقبة في الخلفية (PID: $($process.Id))" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 لإيقاف المراقبة، استخدم:" -ForegroundColor Yellow
    Write-Host "   Stop-Process -Id $($process.Id)" -ForegroundColor Gray
} else {
    # تشغيل في نافذة مرئية
    Start-Process -FilePath $pythonPath -ArgumentList "`"$monitorScript`", `"--continuous`", `"$Interval`"" -WorkingDirectory $projectPath
    Write-Host "✅ تم تشغيل المراقبة في نافذة منفصلة" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📊 معلومات المراقبة:" -ForegroundColor Yellow
Write-Host "   - الملف: $monitorScript" -ForegroundColor Gray
Write-Host "   - الفترة: كل $Interval ثانية" -ForegroundColor Gray
Write-Host "   - السجلات المراقبة: exception_handler.log, database_operations.log, __main__.log" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
