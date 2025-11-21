@echo off
setlocal enabledelayedexpansion

REM Configure these if needed
set REMOTE=origin
set BRANCH=master
set TAG=v5.1.0

echo Verifying git repository...
git rev-parse --is-inside-work-tree >NUL 2>&1 || (echo Not a git repository. & exit /b 1)

echo.
echo Current remotes:
git remote -v

echo.
echo Pushing branch %BRANCH% to %REMOTE% ...
git push %REMOTE% %BRANCH%
if errorlevel 1 goto :error

echo.
echo Pushing tag %TAG% to %REMOTE% ...
git push %REMOTE% %TAG%
if errorlevel 1 goto :error

echo.
echo Done. Release v%TAG% pushed successfully.
exit /b 0

:error
echo.
echo Push failed. Ensure remote is configured and you have permission.
exit /b 1
