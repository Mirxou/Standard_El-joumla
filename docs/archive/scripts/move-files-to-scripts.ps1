# Move Python Files to Scripts Script
# نقل ملفات Python من Root إلى scripts/

param(
    [switch]$WhatIf = $false
)

$ErrorActionPreference = "Stop"
$rootPath = $PSScriptRoot
if (-not $rootPath) {
    $rootPath = Get-Location
}

Write-Host "Moving Python files from Root to scripts/..." -ForegroundColor Cyan
Write-Host "Directory: $rootPath" -ForegroundColor Gray
Write-Host ""

if ($WhatIf) {
    Write-Host "TEST MODE: No files will be moved" -ForegroundColor Yellow
    Write-Host ""
}

# Ensure directories exist
$scriptsDir = Join-Path $rootPath "scripts"
$utilitiesDir = Join-Path $scriptsDir "utilities"
$testsDir = Join-Path $rootPath "tests"
$integrationTestsDir = Join-Path $testsDir "integration"
$unitTestsDir = Join-Path $testsDir "unit"
$performanceTestsDir = Join-Path $testsDir "performance"

if (-not $WhatIf) {
    New-Item -ItemType Directory -Force -Path $utilitiesDir | Out-Null
    New-Item -ItemType Directory -Force -Path $integrationTestsDir | Out-Null
    New-Item -ItemType Directory -Force -Path $unitTestsDir | Out-Null
    New-Item -ItemType Directory -Force -Path $performanceTestsDir | Out-Null
}

# Files to move: [source, destination]
$filesToMove = @(
    # Check scripts -> scripts/utilities/
    @("check_app_status.py", "scripts/utilities/"),
    @("check_default_password.py", "scripts/utilities/"),
    @("check_fk_schema.py", "scripts/utilities/"),
    @("check_permissions.py", "scripts/utilities/"),
    @("check_perms_direct.py", "scripts/utilities/"),
    @("check_role_structure.py", "scripts/utilities/"),
    @("check_schema_perms.py", "scripts/utilities/"),
    @("check_telemetry.py", "scripts/utilities/"),
    @("check_user_permissions.py", "scripts/utilities/"),
    
    # Fix scripts -> scripts/utilities/
    @("fix_admin_password.py", "scripts/utilities/"),
    @("fix_email.py", "scripts/utilities/"),
    @("fix_role_permissions_table.py", "scripts/utilities/"),
    
    # Setup scripts -> scripts/utilities/
    @("setup_icons.py", "scripts/utilities/"),
    @("setup_permissions.py", "scripts/utilities/"),
    @("setup_roles_and_perms.py", "scripts/utilities/"),
    
    # Other scripts -> scripts/
    @("generate_dummy_data.py", "scripts/"),
    @("simulate_inventory_load.py", "scripts/"),
    @("run_migration.py", "scripts/"),
    @("clear_cache.py", "scripts/utilities/"),
    @("reset_password.py", "scripts/utilities/"),
    
    # Test files -> tests/
    @("test_api_sales_flow.py", "tests/integration/"),
    @("test_application_quick.py", "tests/integration/"),
    @("test_window_manager_integration.py", "tests/integration/"),
    @("test_window_manager_smoke_test.py", "tests/integration/"),
    @("test_workflow_sale_to_payment.py", "tests/integration/"),
    @("test_mfa_service.py", "tests/unit/"),
    @("test_purchase_service.py", "tests/unit/"),
    @("test_performance.py", "tests/performance/")
)

$movedCount = 0
$skippedCount = 0
$errors = @()

Write-Host "Files to move:" -ForegroundColor Yellow
Write-Host ""

foreach ($fileInfo in $filesToMove) {
    $sourceFile = $fileInfo[0]
    $destDir = $fileInfo[1]
    $sourcePath = Join-Path $rootPath $sourceFile
    $destPath = Join-Path $rootPath $destDir
    $destFile = Join-Path $destPath $sourceFile
    
    if (Test-Path $sourcePath) {
        if (Test-Path $destFile) {
            Write-Host "  [SKIP] $sourceFile -> $destDir (already exists)" -ForegroundColor Yellow
            $skippedCount++
        } else {
            Write-Host "  [MOVE] $sourceFile -> $destDir" -ForegroundColor Gray
            
            if (-not $WhatIf) {
                try {
                    Move-Item -Path $sourcePath -Destination $destFile -Force -ErrorAction Stop
                    $movedCount++
                } catch {
                    Write-Host "    [ERROR] Failed: $($_.Exception.Message)" -ForegroundColor Red
                    $errors += $sourceFile
                }
            } else {
                $movedCount++
            }
        }
    } else {
        Write-Host "  [NOT FOUND] $sourceFile" -ForegroundColor DarkGray
    }
}

Write-Host ""
if ($WhatIf) {
    Write-Host "[TEST MODE] Would move $movedCount files" -ForegroundColor Green
    if ($skippedCount -gt 0) {
        Write-Host "  Skipped: $skippedCount files (already exist)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[SUCCESS] Moved $movedCount files" -ForegroundColor Green
    if ($skippedCount -gt 0) {
        Write-Host "  Skipped: $skippedCount files (already exist)" -ForegroundColor Yellow
    }
    if ($errors.Count -gt 0) {
        Write-Host "  Errors: $($errors.Count) files failed" -ForegroundColor Red
        foreach ($error in $errors) {
            Write-Host "    - $error" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "Move operation completed!" -ForegroundColor Cyan

