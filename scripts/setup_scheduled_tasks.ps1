# PowerShell Script لتكوين جدولة المهام
# PowerShell Script to configure scheduled tasks

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📅 إعداد جدولة المهام التلقائية" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# الحصول على مسار المشروع
$projectPath = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectPath ".venv\Scripts\python.exe"
$pythonwPath = Join-Path $projectPath ".venv\Scripts\pythonw.exe"
$cleanupScript = Join-Path $projectPath "scripts\cleanup_test_logs.py"
$monitorScript = Join-Path $projectPath "scripts\monitor_logs.py"

# التحقق من وجود Python
if (-not (Test-Path $pythonPath)) {
    Write-Host "⚠️  لم يتم العثور على Python في: $pythonPath" -ForegroundColor Yellow
    Write-Host "🔍 البحث عن Python في النظام..." -ForegroundColor Yellow
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $pythonPath) {
        Write-Host "❌ لم يتم العثور على Python. يرجى تثبيته أولاً." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ تم العثور على Python: $pythonPath" -ForegroundColor Green
    # استخدام pythonw من نفس المسار إذا لم يكن في venv
    $pythonwPath = $pythonPath.Replace("python.exe", "pythonw.exe")
}

Write-Host "📁 مسار المشروع: $projectPath" -ForegroundColor Gray
Write-Host "🐍 مسار Python: $pythonPath" -ForegroundColor Gray
Write-Host ""

# 1. مهمة تنظيف السجلات اليومية
Write-Host "1️⃣  إعداد مهمة تنظيف السجلات اليومية..." -ForegroundColor Yellow

$taskName1 = "LogicalRelease_CleanupLogs"
$taskDescription1 = "تنظيف تلقائي لسجلات الاختبارات القديمة - ستاندرد الجملة"

# حذف المهمة إذا كانت موجودة
$existingTask = Get-ScheduledTask -TaskName $taskName1 -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "   🗑️  حذف المهمة الموجودة..." -ForegroundColor Gray
    Unregister-ScheduledTask -TaskName $taskName1 -Confirm:$false -ErrorAction SilentlyContinue
}

# إنشاء المهمة
$action1 = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$cleanupScript`"" -WorkingDirectory $projectPath
$trigger1 = New-ScheduledTaskTrigger -Daily -At 2am
$settings1 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal1 = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

try {
    Register-ScheduledTask -TaskName $taskName1 -Description $taskDescription1 -Action $action1 -Trigger $trigger1 -Settings $settings1 -Principal $principal1 | Out-Null
    Write-Host "   ✅ تم إنشاء المهمة: $taskName1" -ForegroundColor Green
    Write-Host "      ⏰ الوقت: يومياً في الساعة 2:00 صباحاً" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ فشل إنشاء المهمة: $_" -ForegroundColor Red
}

Write-Host ""

# 2. مهمة مراقبة السجلات المستمرة (اختيارية)
Write-Host "2️⃣  إعداد مهمة مراقبة السجلات (اختيارية)..." -ForegroundColor Yellow
Write-Host "   💡 هذه المهمة تعمل كل 5 دقائق لمراقبة الأخطاء الجديدة" -ForegroundColor Gray
Write-Host ""

$taskName2 = "LogicalRelease_MonitorLogs"
$taskDescription2 = "مراقبة مستمرة لسجلات التطبيق - ستاندرد الجملة"

# حذف المهمة إذا كانت موجودة
$existingTask2 = Get-ScheduledTask -TaskName $taskName2 -ErrorAction SilentlyContinue
if ($existingTask2) {
    Write-Host "   🗑️  حذف المهمة الموجودة..." -ForegroundColor Gray
    Unregister-ScheduledTask -TaskName $taskName2 -Confirm:$false -ErrorAction SilentlyContinue
}

# إنشاء المهمة (كل 5 دقائق)
$action2 = New-ScheduledTaskAction -Execute $pythonwPath -Argument "`"$monitorScript`" --continuous 300" -WorkingDirectory $projectPath
$trigger2 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)
$settings2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$principal2 = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Write-Host "   ❓ هل تريد تفعيل مراقبة مستمرة؟ (Y/N): " -ForegroundColor Yellow -NoNewline
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    try {
        Register-ScheduledTask -TaskName $taskName2 -Description $taskDescription2 -Action $action2 -Trigger $trigger2 -Settings $settings2 -Principal $principal2 | Out-Null
        Write-Host "   ✅ تم إنشاء المهمة: $taskName2" -ForegroundColor Green
        Write-Host "      ⏰ التكرار: كل 5 دقائق" -ForegroundColor Gray
    } catch {
        Write-Host "   ❌ فشل إنشاء المهمة: $_" -ForegroundColor Red
    }
} else {
    Write-Host "   ⏭️  تم تخطي إعداد مراقبة مستمرة" -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ اكتمل إعداد الجدولة!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 المهام المجدولة:" -ForegroundColor Yellow
Get-ScheduledTask -TaskName "LogicalRelease_*" | Format-Table TaskName, State, @{Label="Next Run Time"; Expression={(Get-ScheduledTaskInfo $_.TaskName).NextRunTime}} -AutoSize
Write-Host ""
Write-Host "💡 ملاحظات:" -ForegroundColor Yellow
Write-Host "   - يمكنك إدارة المهام من: Task Scheduler (taskschd.msc)" -ForegroundColor Gray
Write-Host "   - يمكنك تشغيل المهام يدوياً من Task Scheduler" -ForegroundColor Gray
Write-Host "   - يمكنك حذف المهام باستخدام: Unregister-ScheduledTask -TaskName <TaskName>" -ForegroundColor Gray
