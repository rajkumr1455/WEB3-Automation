@echo off
echo ============================================================
echo  Web3 Hunter - Cleanup Script
echo ============================================================
echo.
echo This script will remove unnecessary files to save ~35MB
echo.
pause

echo.
echo Removing duplicate documentation...
del /F NEXT_STEPS.md 2>nul
del /F WINDOWS_SETUP.md 2>nul
del /F FOUNDRY_INSTALL.md 2>nul
del /F ROADMAP.md 2>nul

echo.
echo Removing old/superseded scripts...
del /F analyze_dvd.py 2>nul
del /F main.py 2>nul
del /F validate_env.py 2>nul
del /F setup_session.ps1 2>nul

echo.
echo Removing large unnecessary file...
del /F foundry.zip 2>nul

echo.
echo ============================================================
echo  Cleanup Complete!
echo ============================================================
echo.
echo Files removed:
echo   - 4 duplicate documentation files
echo   - 4 superseded scripts
echo   - 1 large zip file (35MB)
echo.
echo Space saved: ~35MB
echo.
echo Your project structure is now clean and organized!
echo.
pause
