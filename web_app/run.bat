@echo off
echo Forti-DFIR Web Application Launcher
echo ===================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

:: Start backend
echo Starting backend server...
cd backend
start cmd /k "python simple_app.py"

:: Wait a moment for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend
echo Starting frontend server...
cd ../frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)

echo.
echo ===================================
echo Application is starting...
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:5000
echo Default login: admin / admin123
echo.
echo Close all command windows to stop
echo ===================================
echo.

npm start