# Fix Database Paths Script
# إصلاح مسارات قاعدة البيانات المبرمجة

param(
    [switch]$WhatIf = $false
)

$ErrorActionPreference = "Stop"
$rootPath = $PSScriptRoot
if (-not $rootPath) {
    $rootPath = Get-Location
}

Write-Host "Fixing hardcoded database paths..." -ForegroundColor Cyan
Write-Host "Directory: $rootPath" -ForegroundColor Gray
Write-Host ""

if ($WhatIf) {
    Write-Host "TEST MODE: No files will be modified" -ForegroundColor Yellow
    Write-Host ""
}

# Files to fix: [file, old_pattern, new_code]
$filesToFix = @(
    @(
        "src/api/server.py",
        'REAL_DB_PATH = r"C:\\Users\\pc\\Desktop\\الإصدار المنطقي trae\\data\\logical_release.db"',
        @'
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
REAL_DB_PATH = str(project_root / "data" / "logical_release.db")
'@
    ),
    @(
        "fix_email.py",
        'DB_PATH = r"c:\\Users\\pc\\Desktop\\Logical Version trae\\data\\logical_release.db"',
        @'
from pathlib import Path
project_root = Path(__file__).parent.parent
DB_PATH = str(project_root / "data" / "logical_release.db")
'@
    )
)

$fixedCount = 0
$errors = @()

foreach ($fileInfo in $filesToFix) {
    $filePath = Join-Path $rootPath $fileInfo[0]
    $oldPattern = $fileInfo[1]
    $newCode = $fileInfo[2]
    
    if (-not (Test-Path $filePath)) {
        Write-Host "  [NOT FOUND] $($fileInfo[0])" -ForegroundColor DarkGray
        continue
    }
    
    $content = Get-Content -Path $filePath -Raw -Encoding UTF8
    
    if ($content -match [regex]::Escape($oldPattern)) {
        Write-Host "  [FIX] $($fileInfo[0])" -ForegroundColor Yellow
        
        if (-not $WhatIf) {
            try {
                # Replace the old pattern with new code
                $newContent = $content -replace [regex]::Escape($oldPattern), $newCode
                Set-Content -Path $filePath -Value $newContent -Encoding UTF8 -NoNewline
                $fixedCount++
                Write-Host "    [OK] Fixed" -ForegroundColor Green
            } catch {
                Write-Host "    [ERROR] Failed: $($_.Exception.Message)" -ForegroundColor Red
                $errors += $fileInfo[0]
            }
        } else {
            $fixedCount++
        }
    } else {
        Write-Host "  [SKIP] $($fileInfo[0]) (pattern not found or already fixed)" -ForegroundColor Gray
    }
}

Write-Host ""
if ($WhatIf) {
    Write-Host "[TEST MODE] Would fix $fixedCount files" -ForegroundColor Green
} else {
    Write-Host "[SUCCESS] Fixed $fixedCount files" -ForegroundColor Green
    if ($errors.Count -gt 0) {
        Write-Host "  Errors: $($errors.Count) files failed" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Fix operation completed!" -ForegroundColor Cyan

