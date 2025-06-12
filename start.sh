#!/bin/bash

echo "Starting SVG Font Analyzer..."

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "Checking prerequisites..."

if ! command_exists node; then
    echo "Error: Node.js is not installed. Please install Node.js v18 or higher."
    exit 1
fi

if ! command_exists python3; then
    echo "Error: Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

if ! command_exists pnpm; then
    echo "Warning: pnpm is not installed. Attempting to install with npm..."
    if command_exists npm; then
        npm install -g pnpm
    else
        echo "Error: npm is not installed. Please install pnpm manually."
        exit 1
    fi
fi

echo "Prerequisites check passed!"

echo "Starting backend server..."
cd backend || exit
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create Python virtual environment."
        exit 1
    fi
fi

source venv/bin/activate
echo "Installing backend dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install backend dependencies."
    exit 1
fi

uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd .

echo "Waiting for backend to start..."
retries=10
delay=2
count=0
while [ $count -lt $retries ]; do
    if curl -s "http://localhost:8000/docs" > /dev/null; then
        echo "Backend started successfully."
        break
    fi
    sleep $delay
    count=$((count + 1))
done

if [ $count -ge $retries ]; then
    echo "Error: Backend failed to start in time. Check backend logs."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "Starting frontend development server..."
cd frontend || exit
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    pnpm install
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install frontend dependencies."
        exit 1
    fi
fi

pnpm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "SVG Font Analyzer is now running!"
echo ""
echo "Frontend: http://localhost:5173"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Servers stopped. Goodbye!"
    exit 0
}

trap cleanup INT TERM

wait 