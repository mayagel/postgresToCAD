@echo off
echo PostgreSQL to DWG Conversion Tool
echo ================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Run the test setup first
echo Running setup test...
python test_setup.py
echo.

REM Ask user if they want to continue
set /p continue="Do you want to run the conversion? (y/n): "
if /i "%continue%" neq "y" (
    echo Conversion cancelled.
    pause
    exit /b 0
)

REM Run the main conversion
echo Running conversion...
python main.py

echo.
echo Conversion completed. Check the log files for details.
pause
