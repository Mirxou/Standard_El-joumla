# سكريبت تشغيل التكامل الكامل
# Integration Startup Script

Write-Host "🚀 بدء تشغيل التكامل..." -ForegroundColor Green
Write-Host ""

# التحقق من Python
Write-Host "📋 التحقق من Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python غير مثبت!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ $pythonVersion" -ForegroundColor Green
Write-Host ""

# التحقق من Node.js
Write-Host "📋 التحقق من Node.js..." -ForegroundColor Yellow
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Node.js غير مثبت!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Node.js $nodeVersion" -ForegroundColor Green
Write-Host ""

# التحقق من قاعدة البيانات
Write-Host "📋 التحقق من قاعدة البيانات..." -ForegroundColor Yellow
$dbPath = "data\standard_eljoumla.db"
if (Test-Path $dbPath) {
    Write-Host "✅ قاعدة البيانات موجودة: $dbPath" -ForegroundColor Green
} else {
    Write-Host "⚠️  قاعدة البيانات غير موجودة: $dbPath" -ForegroundColor Yellow
    Write-Host "   سيتم إنشاؤها تلقائياً عند تشغيل Backend" -ForegroundColor Yellow
}
Write-Host ""

# التحقق من .env.local
Write-Host "📋 التحقق من إعدادات Frontend..." -ForegroundColor Yellow
$envPath = "web\.env.local"
if (Test-Path $envPath) {
    Write-Host "✅ ملف .env.local موجود" -ForegroundColor Green
} else {
    Write-Host "⚠️  ملف .env.local غير موجود" -ForegroundColor Yellow
    Write-Host "   سيتم استخدام القيم الافتراضية" -ForegroundColor Yellow
    Write-Host "   (NEXT_PUBLIC_API_BASE_URL=http://localhost:8001)" -ForegroundColor Yellow
}
Write-Host ""

# عرض الإعدادات
Write-Host "📊 الإعدادات الحالية:" -ForegroundColor Cyan
Write-Host "   Backend API: http://localhost:8001" -ForegroundColor White
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host ""

# السؤال عن ما يريد المستخدم تشغيله
Write-Host "ما الذي تريد تشغيله؟" -ForegroundColor Yellow
Write-Host "1. Backend API فقط" -ForegroundColor White
Write-Host "2. Frontend فقط" -ForegroundColor White
Write-Host "3. كلاهما (Backend + Frontend)" -ForegroundColor White
Write-Host ""

$choice = Read-Host "اختر (1/2/3)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "🚀 تشغيل Backend API..." -ForegroundColor Green
    Write-Host "   اضغط Ctrl+C لإيقاف" -ForegroundColor Yellow
    Write-Host ""
    Set-Location $PSScriptRoot\..
    python -m uvicorn src.api.app:app --reload --port 8001 --host 0.0.0.0
}
elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "🚀 تشغيل Frontend..." -ForegroundColor Green
    Write-Host "   تأكد من أن Backend يعمل أولاً!" -ForegroundColor Yellow
    Write-Host "   اضغط Ctrl+C لإيقاف" -ForegroundColor Yellow
    Write-Host ""
    Set-Location $PSScriptRoot\..\web
    npm run dev
}
elseif ($choice -eq "3") {
    Write-Host ""
    Write-Host "🚀 تشغيل Backend و Frontend..." -ForegroundColor Green
    Write-Host ""
    
    # تشغيل Backend في نافذة جديدة
    Write-Host "📡 بدء Backend API..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..'; python -m uvicorn src.api.app:app --reload --port 8001 --host 0.0.0.0"
    
    # انتظار قليل
    Start-Sleep -Seconds 3
    
    # تشغيل Frontend
    Write-Host "🌐 بدء Frontend..." -ForegroundColor Cyan
    Write-Host ""
    Set-Location $PSScriptRoot\..\web
    npm run dev
}
else {
    Write-Host "❌ اختيار غير صحيح!" -ForegroundColor Red
    exit 1
}

