@echo off
setlocal enabledelayedexpansion

:: new_version.bat - Automated release build script for asset-extractor
:: This script performs a complete release build with versioning and archiving

echo.
echo ============================================================
echo Asset Extractor - New Version Release Script
echo ============================================================
echo.

:: Ask for version number
set /p VERSION="Enter version number (e.g., 1.0.0): "
if "%VERSION%"=="" (
    echo Error: Version number is required
    exit /b 1
)

echo.
echo Creating release for version: %VERSION%
echo.

:: Step 1: Extract RDA files
echo ============================================================
echo Step 1/5: Extracting RDA files from game...
echo ============================================================
echo.
call extract.cmd
if errorlevel 1 (
    echo Error: Extraction failed
    exit /b 1
)

:: Step 2: Run main.py with version parameter
echo.
echo ============================================================
echo Step 2/5: Generating asset browser and creating snapshot...
echo ============================================================
echo.
uv run python main.py --version "%VERSION%"
if errorlevel 1 (
    echo Error: Asset browser generation or snapshot creation failed
    exit /b 1
)

:: Step 3: Zip the results
echo.
echo ============================================================
echo Step 3/5: Creating archive...
echo ============================================================
echo.

:: Get current date in YYYY-MM-DD format
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set DATE_STAMP=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%

set ARCHIVE_NAME=assetbrowser-%DATE_STAMP%.7z
set ASSETBROWSER_DIR=results\assetbrowser

echo Creating archive: %ARCHIVE_NAME%
echo Source directory: %ASSETBROWSER_DIR%
echo.

:: Check if 7-Zip is available
where 7z >nul 2>nul
if errorlevel 1 (
    echo Error: 7-Zip not found in PATH
    echo Please install 7-Zip and add it to your PATH, or edit this script to point to 7z.exe
    exit /b 1
)

:: Create archive with LZMA2, 1GB dictionary, compression level 7 (maximum)
7z a -t7z -m0=lzma2 -mx=7 -md=1024m "%ARCHIVE_NAME%" ".\%ASSETBROWSER_DIR%\*"
if errorlevel 1 (
    echo Error: Archive creation failed
    exit /b 1
)

echo.
echo Archive created successfully: %ARCHIVE_NAME%

:: Step 4: Export items to Google Sheets
echo.
echo ============================================================
echo Step 4/5: Exporting items to Google Sheets...
echo ============================================================
echo.
uv run python -m assetextractor.conversion.statistics.extract_items_to_gsheet
if errorlevel 1 (
    echo Warning: Google Sheets export failed (this may be expected if credentials are not configured)
    echo Continuing...
)

:: Step 5: Summary
echo.
echo ============================================================
echo Step 5/5: Release build complete!
echo ============================================================
echo.
echo Version: %VERSION%
echo Archive: %ARCHIVE_NAME%
echo Output directory: %ASSETBROWSER_DIR%
echo.
echo Next steps:
echo   1. Upload %ARCHIVE_NAME% to your distribution platform
echo   2. Verify Google Sheets export (if configured)
echo   3. Update release notes
echo.
echo ============================================================

endlocal
