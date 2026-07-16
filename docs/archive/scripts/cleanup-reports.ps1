# Cleanup Old Reports Script
# حذف ملفات التقارير القديمة

param(
    [switch]$WhatIf = $false
)

$ErrorActionPreference = "Stop"
$rootPath = $PSScriptRoot
if (-not $rootPath) {
    $rootPath = Get-Location
}

Write-Host "Cleaning up old report files..." -ForegroundColor Cyan
Write-Host "Directory: $rootPath" -ForegroundColor Gray
Write-Host ""

if ($WhatIf) {
    Write-Host "TEST MODE: No files will be deleted" -ForegroundColor Yellow
    Write-Host ""
}

# Patterns for old reports
$patterns = @(
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
    "TEST_*.md",
    "TESTING_*.md",
    "*_AUDIT*.md",
    "*_REVIEW*.md",
    "CLEANUP_*.md",
    "*_MIGRATION*.md"
)

# Exceptions - important files to keep
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
    "DUPLICATE_FILES_REPORT.md",
    "DUPLICATE_FILES_README.md",
    "CLEANUP_README.md",
    "USER_GUIDE_AR.md",
    "USAGE_GUIDE.md",
    "QUICK_START_GUIDE.md",
    "TESTING_GUIDE.md",
    "DEPLOYMENT_GUIDE.md",
    "README.DOCKER.md"
)

$filesToDelete = @()

foreach ($pattern in $patterns) {
    $found = Get-ChildItem -Path $rootPath -Filter $pattern -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        $isException = $false
        foreach ($exception in $exceptions) {
            if ($_.Name -eq $exception) {
                $isException = $true
                break
            }
        }
        -not $isException -and $_.FullName -notmatch 'node_modules|__pycache__|\.git|\.venv|coverage|htmlcov|\.next'
    }
    
    if ($found) {
        $filesToDelete += $found
    }
}

# Remove duplicates
$filesToDelete = $filesToDelete | Select-Object -Unique

Write-Host "Found $($filesToDelete.Count) report files to delete" -ForegroundColor White
Write-Host ""

if ($filesToDelete.Count -eq 0) {
    Write-Host "No files to delete!" -ForegroundColor Green
    exit 0
}

if (-not $WhatIf) {
    $confirm = Read-Host "Delete $($filesToDelete.Count) files? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "Cancelled" -ForegroundColor Red
        exit 0
    }
}

$deletedCount = 0
$totalSize = 0

foreach ($file in $filesToDelete) {
    try {
        if (-not $WhatIf) {
            $fileSize = $file.Length
            Remove-Item -Path $file.FullName -Force -ErrorAction Stop
            $deletedCount++
            $totalSize += $fileSize
        } else {
            $deletedCount++
            $totalSize += $file.Length
        }
    } catch {
        Write-Host "  [ERROR] Failed: $($file.Name)" -ForegroundColor Red
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

