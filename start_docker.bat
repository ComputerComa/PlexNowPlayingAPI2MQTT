@echo off
echo.
echo ===================================
echo  Plex MQTT Bridge - Docker Setup
echo ===================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not in PATH
    echo.
    echo Please install Docker Desktop for Windows:
    echo https://docs.docker.com/desktop/install/windows-install/
    echo.
    pause
    exit /b 1
)

REM Check if Docker daemon is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker daemon is not running
    echo.
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo Docker is installed and running!
echo.

REM Check if config.json exists
if not exist "config.json" (
    echo WARNING: config.json not found
    echo.
    if exist "config.example.json" (
        echo Would you like to copy config.example.json to config.json? (y/n)
        set /p choice=
        if /i "%choice%"=="y" (
            copy "config.example.json" "config.json"
            echo.
            echo config.json created! Please edit it with your settings:
            echo - Plex token (use get_plex_token.py to get it)
            echo - MQTT broker details
            echo.
            echo Press any key to open config.json in notepad...
            pause >nul
            notepad config.json
        )
    ) else (
        echo config.example.json not found either!
        echo Please check your installation.
        pause
        exit /b 1
    )
)

echo.
echo Choose an option:
echo 1. Build and run with Docker Compose
echo 2. Just build the Docker image
echo 3. Run validation checks
echo 4. View logs of running container
echo 5. Stop the container
echo.
set /p option="Enter your choice (1-5): "

if "%option%"=="1" (
    echo.
    echo Building and starting Plex MQTT Bridge...
    docker-compose up -d
    if %errorlevel% equ 0 (
        echo.
        echo Success! Container is starting...
        echo Web interface will be available at: http://localhost:5000
        echo.
        echo To view logs: docker-compose logs -f plex-mqtt-bridge
        echo To stop: docker-compose down
    )
) else if "%option%"=="2" (
    echo.
    echo Building Docker image...
    docker build -t plex-mqtt-bridge .
) else if "%option%"=="3" (
    echo.
    echo Running validation checks...
    python validate_docker.py
) else if "%option%"=="4" (
    echo.
    echo Showing container logs...
    docker-compose logs -f plex-mqtt-bridge
) else if "%option%"=="5" (
    echo.
    echo Stopping container...
    docker-compose down
) else (
    echo Invalid option selected.
)

echo.
pause
