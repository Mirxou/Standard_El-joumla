# سكريبت تنظيف الملفات غير المهمة
# Cleanup Script for Unused Files
# 
# ⚠️ تحذير: تأكد من عمل نسخة احتياطية قبل التشغيل!
# Warning: Make sure to backup before running!

param(
    [switch]$WhatIf = $false,  # عرض الملفات فقط بدون حذف
    [switch]$DryRun = $false   # نفس WhatIf
)

$ErrorActionPreference = "Stop"

# تحديد المجلد الحالي
$rootPath = $PSScriptRoot
if (-not $rootPath) {
    $rootPath = Get-Location
}

Write-Host "🧹 بدء تنظيف الملفات غير المهمة..." -ForegroundColor Cyan
Write-Host "📁 المجلد: $rootPath" -ForegroundColor Gray
Write-Host ""

if ($WhatIf -or $DryRun) {
    Write-Host "⚠️  وضع الاختبار: لن يتم حذف أي ملفات" -ForegroundColor Yellow
    Write-Host ""
}

# قائمة الأنماط للحذف
$patternsToDelete = @(
    # تقارير قديمة
    "*_SUMMARY.md",
    "*_REPORT.md",
    "*_COMPLETION*.md",
    "*_STATUS*.md",
    "*_FINAL*.md",
    "SESSION_*.md",
    "PHASE_*.md",
    "COVERAGE_*.md",
    "WINDOW_*.md",
    "MULTI_*.md",
    
    # تقارير اختبارات
    "TEST_*.md",
    "TESTING_*.md",
    
    # تقارير مراجعة
    "*_AUDIT*.md",
    "*_REVIEW*.md",
    
    # تقارير تنظيف
    "CLEANUP_*.md",
    
    # ملفات Python مؤقتة
    "_gen_tree.py",
    "_tree_gen.py",
    "check_*.py",
    "fix_*.py",
    "setup_*.py",
    "simulate_*.py",
    
    # ملفات قديمة
    "App.tsx",
    "InventoryPage.tsx",
    "index.ts",
    "productService.ts",
    "tree-full.txt",
    "file_tree_raw.txt",
    "test_output.txt"
)

# استثناءات (ملفات مهمة يجب الاحتفاظ بها)
$exceptions = @(
    "README.md",
    "requirements.txt",
    "package.json",
    "tsconfig.json",
    "docker-compose.yml",
    "Dockerfile",
    "LICENSE.txt",
    ".gitignore",
    "pytest.ini",
    "main.py",
    "FILES_REVIEW_REPORT.md",
    "FILE_TREE_CLASSIFIED.md",
    "FILE_TREE_SIMPLE.txt",
    "cleanup-unused-files.ps1"
)

# جمع الملفات للحذف
$filesToDelete = @()

foreach ($pattern in $patternsToDelete) {
    $found = Get-ChildItem -Path $rootPath -Filter $pattern -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        $isException = $false
        foreach ($exception in $exceptions) {
            if ($_.Name -eq $exception) {
                $isException = $true
                break
            }
        }
        -not $isException
    }
    
    if ($found) {
        $filesToDelete += $found
    }
}

# إزالة الملفات المكررة
$filesToDelete = $filesToDelete | Select-Object -Unique

# عرض النتائج
Write-Host "📊 النتائج:" -ForegroundColor Cyan
Write-Host "   تم العثور على $($filesToDelete.Count) ملف للحذف" -ForegroundColor White
Write-Host ""

if ($filesToDelete.Count -eq 0) {
    Write-Host "✅ لا توجد ملفات للحذف!" -ForegroundColor Green
    exit 0
}

# عرض الملفات
Write-Host "📋 الملفات التي سيتم حذفها:" -ForegroundColor Yellow
Write-Host ""
$counter = 1
foreach ($file in $filesToDelete) {
    $relativePath = $file.FullName.Replace($rootPath, "").TrimStart('\')
    Write-Host "   $counter. $relativePath" -ForegroundColor Gray
    $counter++
}

Write-Host ""

# تأكيد الحذف
if (-not ($WhatIf -or $DryRun)) {
    $confirm = Read-Host "❓ هل تريد المتابعة؟ (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "❌ تم الإلغاء" -ForegroundColor Red
        exit 0
    }
}

# حذف الملفات
$deletedCount = 0
$errorCount = 0

foreach ($file in $filesToDelete) {
    try {
        if (-not ($WhatIf -or $DryRun)) {
            Remove-Item -Path $file.FullName -Force -ErrorAction Stop
            $deletedCount++
        } else {
            $deletedCount++
        }
    } catch {
        Write-Host "   ❌ خطأ في حذف: $($file.Name)" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host ""
if ($WhatIf -or $DryRun) {
    Write-Host "✅ وضع الاختبار: سيتم حذف $deletedCount ملف" -ForegroundColor Green
    Write-Host "   للتطبيق الفعلي، قم بتشغيل السكريبت بدون -WhatIf" -ForegroundColor Yellow
} else {
    Write-Host "✅ تم حذف $deletedCount ملف بنجاح" -ForegroundColor Green
    if ($errorCount -gt 0) {
        Write-Host "⚠️  فشل حذف $errorCount ملف" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✨ اكتمل التنظيف!" -ForegroundColor Cyan

