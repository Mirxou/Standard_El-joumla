# Cleanup Python Files Script
# حذف الملفات المؤقتة والقديمة

param(
    [switch]$WhatIf = $false
)

$ErrorActionPreference = "Stop"
$rootPath = $PSScriptRoot
if (-not $rootPath) {
    $rootPath = Get-Location
}

Write-Host "Cleaning up temporary Python files..." -ForegroundColor Cyan
Write-Host "Directory: $rootPath" -ForegroundColor Gray
Write-Host ""

if ($WhatIf) {
    Write-Host "TEST MODE: No files will be deleted" -ForegroundColor Yellow
    Write-Host ""
}

# Files to delete (100% safe)
$filesToDelete = @(
    # Old database files
    "standard.db",
    "test_db.db",
    
    # Temporary scripts
    "_gen_tree.py",
    "_tree_gen.py",
    
    # Documentation Python files (print only)
    "DEADLOCK_FIX_SUMMARY.py",
    "SOLUTION_SUMMARY.py",
    
    # Old Node.js files
    "package.json",
    "package-lock.json"
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

Write-Host "Found $($filesFound.Count) files to delete" -ForegroundColor White

if ($filesNotFound.Count -gt 0) {
    Write-Host "Warning: $($filesNotFound.Count) files not found:" -ForegroundColor Yellow
    foreach ($file in $filesNotFound) {
        Write-Host "  - $file" -ForegroundColor Gray
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

if (-not $WhatIf) {
    $confirm = Read-Host "Delete $($filesFound.Count) files? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "Cancelled" -ForegroundColor Red
        exit 0
    }
}

$deletedCount = 0
$totalSize = 0

foreach ($file in $filesFound) {
    try {
        if (-not $WhatIf) {
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
        Write-Host "  [ERROR] Failed: $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
if ($WhatIf) {
    $sizeMB = "{0:N2} MB" -f ($totalSize / 1MB)
    Write-Host "[TEST MODE] Would delete $deletedCount files ($sizeMB)" -ForegroundColor Green
} else {
    $sizeMB = "{0:N2} MB" -f ($totalSize / 1MB)
    Write-Host "[SUCCESS] Deleted $deletedCount files ($sizeMB freed)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Cleanup completed!" -ForegroundColor Cyan

