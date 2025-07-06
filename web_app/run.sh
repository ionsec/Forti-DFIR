#!/bin/bash

echo "Forti-DFIR Web Application Launcher"
echo "==================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

# Backend setup
echo "Setting up backend..."
cd backend

# Install Python dependencies if not already installed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null

echo "Installing backend dependencies..."
pip install flask flask-cors pandas werkzeug

# Start backend
echo ""
echo "Starting backend server on http://localhost:5000"
python simple_app.py &
BACKEND_PID=$!

# Frontend setup
cd ../frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo ""
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend
echo ""
echo "Starting frontend server on http://localhost:3000"
echo ""
echo "==================================="
echo "Application is starting..."
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:5000"
echo "Default login: admin / admin123"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "==================================="

npm start

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT