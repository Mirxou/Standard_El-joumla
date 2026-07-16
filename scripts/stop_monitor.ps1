# PowerShell Script لإيقاف مراقبة السجلات
# PowerShell Script to stop log monitoring

Write-Host "🔍 البحث عن عمليات مراقبة السجلات..." -ForegroundColor Yellow

# البحث عن عمليات Python التي تشغل monitor_logs.py
$processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*monitor_logs.py*"
}

if ($processes.Count -eq 0) {
    Write-Host "ℹ️  لا توجد عمليات مراقبة نشطة" -ForegroundColor Gray
    exit 0
}

Write-Host "📊 تم العثور على $($processes.Count) عملية:" -ForegroundColor Green
$processes | ForEach-Object {
    Write-Host "   PID: $($_.Id) - $($_.ProcessName)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "❓ هل تريد إيقاف جميع عمليات المراقبة؟ (Y/N): " -ForegroundColor Yellow -NoNewline
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    $processes | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        Write-Host "✅ تم إيقاف العملية PID: $($_.Id)" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "✅ تم إيقاف جميع عمليات المراقبة" -ForegroundColor Green
} else {
    Write-Host "⏭️  تم الإلغاء" -ForegroundColor Gray
}

