@echo off
setlocal enabledelayedexpansion

REM Set UTF-8 encoding
chcp 65001 >nul 2>&1

echo ========================================
echo    Pixelle MCP Service Launcher
echo ========================================
echo.

REM Check if uv is installed
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: uv is not installed or not in PATH
    echo Please install uv first: https://docs.astral.sh/uv/getting-started/installation/
    echo.
    pause
    exit /b 1
)

echo Checking uv installation...
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Failed to run uv command
    pause
    exit /b 1
)

echo uv is available: 
uv --version
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
echo Script directory: %SCRIPT_DIR%
echo.

REM Check if required directories exist
if not exist "%SCRIPT_DIR%mcp-base" (
    echo ERROR: mcp-base directory not found
    pause
    exit /b 1
)

if not exist "%SCRIPT_DIR%mcp-server" (
    echo ERROR: mcp-server directory not found
    pause
    exit /b 1
)

if not exist "%SCRIPT_DIR%mcp-client" (
    echo ERROR: mcp-client directory not found
    pause
    exit /b 1
)

echo Starting Pixelle MCP services...
echo.

REM Start mcp-base
echo [1/3] Starting mcp-base...
start "mcp-base" cmd /k "cd /d "%SCRIPT_DIR%mcp-base" && echo Starting mcp-base... && uv sync && uv run main.py"

REM Wait for mcp-base to start
echo Waiting for mcp-base to start...
timeout /t 5 /nobreak >nul

REM Start mcp-server
echo [2/3] Starting mcp-server...
start "mcp-server" cmd /k "cd /d "%SCRIPT_DIR%mcp-server" && echo Starting mcp-server... && uv sync && uv run main.py"

REM Wait for mcp-server to start
echo Waiting for mcp-server to start...
timeout /t 5 /nobreak >nul

REM Start mcp-client
echo [3/3] Starting mcp-client...
start "mcp-client" cmd /k "cd /d "%SCRIPT_DIR%mcp-client" && echo Starting mcp-client... && uv sync && uv run main.py"

echo.
echo ========================================
echo    All services started successfully!
echo ========================================
echo.
echo Service URLs:
echo   Base Service: http://localhost:9001/docs
echo   Server:        http://localhost:9002/sse
echo   Client:        http://localhost:9003
echo.
echo Each service is running in its own command window.
echo Close the windows to stop the services.
echo.
pause 