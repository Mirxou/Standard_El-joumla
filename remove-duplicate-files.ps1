# سكريبت حذف الملفات المكررة وغير المفيدة
# Remove Duplicate and Unused Files Script
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

Write-Host "🧹 بدء حذف الملفات المكررة وغير المفيدة..." -ForegroundColor Cyan
Write-Host "📁 المجلد: $rootPath" -ForegroundColor Gray
Write-Host ""

if ($WhatIf -or $DryRun) {
    Write-Host "⚠️  وضع الاختبار: لن يتم حذف أي ملفات" -ForegroundColor Yellow
    Write-Host ""
}

# قائمة الملفات للحذف (آمنة 100%)
$filesToDelete = @(
    # ملفات Backup
    "src\ui\dialogs\sales_dialog.py.backup",
    "web\components\inventory-management.tsx.backup",
    "web\__tests__\lib\api\client.test.ts.bak",
    
    # ملفات قديمة في Root
    "App.tsx",
    "InventoryPage.tsx",
    "index.ts",
    "productService.ts",
    
    # ملفات مكررة
    "web\components\ui\use-toast.ts",  # مكرر - المستخدم هو web/hooks/use-toast.ts
    
    # ملفات مؤقتة
    "tree-full.txt",
    "file_tree_raw.txt",
    "test_output.txt"
)

# جمع الملفات الفعلية للحذف
$filesFound = @()
$filesNotFound = @()

foreach ($file in $filesToDelete) {
    $fullPath = Join-Path $rootPath $file
    if (Test-Path $fullPath) {
        $filesFound += Get-Item $fullPath
    } else {
        $filesNotFound += $file
    }
}

# عرض النتائج
Write-Host "📊 النتائج:" -ForegroundColor Cyan
Write-Host "   تم العثور على $($filesFound.Count) ملف للحذف" -ForegroundColor White

if ($filesNotFound.Count -gt 0) {
    Write-Host "   ⚠️  لم يتم العثور على $($filesNotFound.Count) ملف:" -ForegroundColor Yellow
    foreach ($file in $filesNotFound) {
        Write-Host "      - $file" -ForegroundColor Gray
    }
}

Write-Host ""

if ($filesFound.Count -eq 0) {
    Write-Host "✅ لا توجد ملفات للحذف!" -ForegroundColor Green
    exit 0
}

# عرض الملفات
Write-Host "📋 الملفات التي سيتم حذفها:" -ForegroundColor Yellow
Write-Host ""
$counter = 1
foreach ($file in $filesFound) {
    $relativePath = $file.FullName.Replace($rootPath, "").TrimStart('\')
    $size = "{0:N2} KB" -f ($file.Length / 1KB)
    Write-Host "   $counter. $relativePath ($size)" -ForegroundColor Gray
    $counter++
}

Write-Host ""

# تأكيد الحذف
if (-not ($WhatIf -or $DryRun)) {
    Write-Host "⚠️  سيتم حذف $($filesFound.Count) ملف" -ForegroundColor Yellow
    $confirm = Read-Host "❓ هل تريد المتابعة؟ (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "❌ تم الإلغاء" -ForegroundColor Red
        exit 0
    }
}

# حذف الملفات
$deletedCount = 0
$errorCount = 0
$totalSize = 0

foreach ($file in $filesFound) {
    try {
        if (-not ($WhatIf -or $DryRun)) {
            $fileSize = $file.Length
            Remove-Item -Path $file.FullName -Force -ErrorAction Stop
            $deletedCount++
            $totalSize += $fileSize
            Write-Host "   ✅ حذف: $($file.Name)" -ForegroundColor Green
        } else {
            $deletedCount++
            $totalSize += $file.Length
        }
    } catch {
        Write-Host "   ❌ خطأ في حذف: $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host ""
if ($WhatIf -or $DryRun) {
    $sizeMB = "{0:N2} MB" -f ($totalSize / 1MB)
    Write-Host "✅ وضع الاختبار: سيتم حذف $deletedCount ملف ($sizeMB)" -ForegroundColor Green
    Write-Host "   للتطبيق الفعلي، قم بتشغيل السكريبت بدون -WhatIf" -ForegroundColor Yellow
} else {
    $sizeMB = "{0:N2} MB" -f ($totalSize / 1MB)
    Write-Host "✅ تم حذف $deletedCount ملف بنجاح ($sizeMB MB freed)" -ForegroundColor Green
    if ($errorCount -gt 0) {
        Write-Host "⚠️  فشل حذف $errorCount ملفات" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✨ اكتمل التنظيف!" -ForegroundColor Cyan

# ملاحظة حول الملفات المكررة الأخرى
Write-Host ""
Write-Host "💡 ملاحظة:" -ForegroundColor Cyan
Write-Host "   هناك ملفات أخرى مكررة (cache_manager, rate_limiter, etc.)" -ForegroundColor Gray
Write-Host "   لكنها ملفات مختلفة بنفس الاسم - راجع DUPLICATE_FILES_REPORT.md" -ForegroundColor Gray
Write-Host "   لإعادة تسميتها بشكل صحيح." -ForegroundColor Gray

