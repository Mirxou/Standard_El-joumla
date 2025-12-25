# Remove Duplicate and Unused Files Script
# سكريبت حذف الملفات المكررة وغير المفيدة

param(
    [switch]$WhatIf = $false,
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"
$rootPath = $PSScriptRoot
if (-not $rootPath) {
    $rootPath = Get-Location
}

Write-Host "Starting cleanup of duplicate and unused files..." -ForegroundColor Cyan
Write-Host "Directory: $rootPath" -ForegroundColor Gray
Write-Host ""

if ($WhatIf -or $DryRun) {
    Write-Host "TEST MODE: No files will be deleted" -ForegroundColor Yellow
    Write-Host ""
}

# Files to delete (100% safe)
$filesToDelete = @(
    "src\ui\dialogs\sales_dialog.py.backup",
    "web\components\inventory-management.tsx.backup",
    "web\__tests__\lib\api\client.test.ts.bak",
    "App.tsx",
    "InventoryPage.tsx",
    "index.ts",
    "productService.ts",
    "web\components\ui\use-toast.ts",
    "tree-full.txt",
    "file_tree_raw.txt",
    "test_output.txt"
)

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

Write-Host "Results:" -ForegroundColor Cyan
Write-Host "  Found $($filesFound.Count) files to delete" -ForegroundColor White

if ($filesNotFound.Count -gt 0) {
    Write-Host "  Warning: $($filesNotFound.Count) files not found:" -ForegroundColor Yellow
    foreach ($file in $filesNotFound) {
        Write-Host "    - $file" -ForegroundColor Gray
    }
}

Write-Host ""

if ($filesFound.Count -eq 0) {
    Write-Host "No files to delete!" -ForegroundColor Green
    exit 0
}

Write-Host "Files that will be deleted:" -ForegroundColor Yellow
Write-Host ""
$counter = 1
foreach ($file in $filesFound) {
    $relativePath = $file.FullName.Replace($rootPath, "").TrimStart('\')
    $size = "{0:N2} KB" -f ($file.Length / 1KB)
    Write-Host "  $counter. $relativePath ($size)" -ForegroundColor Gray
    $counter++
}

Write-Host ""

if (-not ($WhatIf -or $DryRun)) {
    Write-Host "Will delete $($filesFound.Count) files" -ForegroundColor Yellow
    $confirm = Read-Host "Continue? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "Cancelled" -ForegroundColor Red
        exit 0
    }
}

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
            Write-Host "  [OK] Deleted: $($file.Name)" -ForegroundColor Green
        } else {
            $deletedCount++
            $totalSize += $file.Length
        }
    } catch {
        Write-Host "  [ERROR] Failed to delete: $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host ""
if ($WhatIf -or $DryRun) {
    $sizeMB = "{0:N2} MB" -f ($totalSize / 1MB)
    Write-Host "[TEST MODE] Would delete $deletedCount files ($sizeMB)" -ForegroundColor Green
    Write-Host "  Run without -WhatIf to actually delete" -ForegroundColor Yellow
} else {
    $sizeMB = "{0:N2} MB" -f ($totalSize / 1MB)
    Write-Host "[SUCCESS] Deleted $deletedCount files ($sizeMB freed)" -ForegroundColor Green
    if ($errorCount -gt 0) {
        Write-Host "[WARNING] Failed to delete $errorCount files" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Cleanup completed!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: There are other duplicate files (cache_manager, rate_limiter, etc.)" -ForegroundColor Gray
Write-Host "      but they are different files with same names. See DUPLICATE_FILES_REPORT.md" -ForegroundColor Gray

