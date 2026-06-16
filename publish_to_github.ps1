# =============================================================
# publish_to_github.ps1
# Script لنشر مشروع Standard El-Joumla على GitHub
# =============================================================

param(
    [string]$CommitMessage = "chore: sync all changes - v6 production update",
    [string]$Branch = "v6"
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  نشر مشروع Standard El-Joumla على GitHub" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# البحث عن git
$gitExe = $null
$possiblePaths = @(
    "C:\Program Files\Git\cmd\git.exe",
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files (x86)\Git\cmd\git.exe",
    "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe",
    "C:\msys64\usr\bin\git.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $gitExe = $path
        Write-Host "[OK] تم العثور على git في: $path" -ForegroundColor Green
        break
    }
}

if (-not $gitExe) {
    # جرب من PATH
    try {
        $gitExe = (Get-Command git -ErrorAction Stop).Source
        Write-Host "[OK] git في PATH: $gitExe" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Git غير مثبت!" -ForegroundColor Red
        Write-Host ""
        Write-Host "يرجى تثبيت Git من: https://git-scm.com/download/win" -ForegroundColor Yellow
        Write-Host "ثم أعد تشغيل هذا السكريبت" -ForegroundColor Yellow
        exit 1
    }
}

function git { & $gitExe @args }

# التحقق من الـ remote
Write-Host "`n[1] فحص إعدادات Git..." -ForegroundColor Yellow
git remote -v
Write-Host ""

# إضافة الملفات
Write-Host "[2] إضافة الملفات المعدلة..." -ForegroundColor Yellow
git add -A
Write-Host "[OK] تم إضافة جميع الملفات" -ForegroundColor Green

# عرض ملخص التغييرات
Write-Host "`n[3] ملخص التغييرات:" -ForegroundColor Yellow
git status --short | Select-Object -First 50
$totalChanges = (git status --short).Count
Write-Host "إجمالي الملفات المتأثرة: $totalChanges" -ForegroundColor Cyan

# Commit
Write-Host "`n[4] إنشاء commit..." -ForegroundColor Yellow
git commit -m $CommitMessage
Write-Host "[OK] تم إنشاء الـ commit" -ForegroundColor Green

# Push
Write-Host "`n[5] رفع التغييرات إلى GitHub..." -ForegroundColor Yellow
git push origin $Branch
Write-Host "[OK] تم الرفع بنجاح!" -ForegroundColor Green

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "  تم نشر المشروع بنجاح على GitHub!" -ForegroundColor Green
Write-Host "  الرابط: https://github.com/Mirxou/Standard_El-joumla" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
