@echo off
REM Easy Deployment Configuration Script for Windows
REM This script provides a simple interface to configure deployment settings

setlocal enabledelayedexpansion

echo ========================================
echo   Deployment Configuration Tool
echo ========================================
echo.
echo Choose your deployment target:
echo   1. Localhost (Development)
echo   2. EC2 Instance (54.254.180.103)
echo   3. Custom Domain/IP
echo   4. Show current configuration
echo   5. Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo Configuring for localhost development...
    python scripts\configure-deployment.py --target localhost
    if !errorlevel! equ 0 (
        echo.
        echo ✅ Configuration updated successfully!
        echo You can now run: npm run dev:all
    )
) else if "%choice%"=="2" (
    echo.
    echo Configuring for EC2 instance (54.254.180.103)...
    python scripts\configure-deployment.py --target ec2
    if !errorlevel! equ 0 (
        echo.
        echo ✅ Configuration updated successfully!
        echo Ready for EC2 deployment.
    )
) else if "%choice%"=="3" (
    echo.
    set /p custom_domain="Enter your domain/IP (e.g., http://192.168.1.100): "
    echo Configuring for custom domain: !custom_domain!
    python scripts\configure-deployment.py --custom-domain "!custom_domain!"
    if !errorlevel! equ 0 (
        echo.
        echo ✅ Configuration updated successfully!
    )
) else if "%choice%"=="4" (
    echo.
    echo Current configuration preview:
    python scripts\configure-deployment.py --target localhost --dry-run
) else if "%choice%"=="5" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice. Please run the script again.
    exit /b 1
)

echo.
pause