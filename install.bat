@echo off
echo PostgreSQL to DWG Conversion Tool - Installation
echo ================================================

REM Create necessary directories
echo Creating directories...
if not exist "%TARGET_PATH%" (
    echo Creating target directory: %TARGET_PATH%
    mkdir "%TARGET_PATH%"
)

if not exist "%LOG_PATH%" (
    echo Creating log directory: %LOG_PATH%
    mkdir "%LOG_PATH%"
)

REM Check if ArcGIS is installed
echo Checking for ArcGIS installation...
python -c "import arcpy" 2>nul
if errorlevel 1 (
    echo WARNING: ArcGIS Python API (arcpy) not found
    echo Please ensure ArcGIS Pro or ArcGIS Server is installed
) else (
    echo ArcGIS Python API found
)

REM Run setup test
echo Running setup test...
python test_setup.py

echo.
echo Installation completed!
echo.
echo To run the conversion tool:
echo 1. Double-click run_conversion.bat, or
echo 2. Run: python main.py
echo.
pause
