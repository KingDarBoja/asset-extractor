@echo off
REM Extract RDA files from Anno game directory
REM This script should be run whenever there is a game update

echo Extracting RDA files from Anno game directory...
echo.

uv run python -m assetextractor.extraction.extract

pause