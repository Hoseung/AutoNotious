#!/bin/bash

echo "🚀 Starting AutoNotoin Application..."
echo "=================================="

cleanup() {
    echo ""
    echo "🛑 Shutting down all services..."
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📦 Activating Python virtual environment..."
source .venv/bin/activate

echo ""
echo "1️⃣  Starting LiteLLM proxy server (Port 4000)..."
gnome-terminal --title="LiteLLM Proxy" -- bash -c "source .venv/bin/activate && litellm --model gpt-4o-mini --port 4000; exec bash" &

sleep 3

echo "2️⃣  Starting Backend server (Port 8000)..."
gnome-terminal --title="Backend Server" -- bash -c "source .venv/bin/activate && cd backend && uvicorn app.main:app --reload --port 8000; exec bash" &

sleep 3

echo "3️⃣  Starting Frontend development server (Port 5173)..."
gnome-terminal --title="Frontend Server" -- bash -c "cd frontend && npm run dev; exec bash" &

sleep 5

echo ""
echo "✅ All services started!"
echo "=================================="
echo "📍 LiteLLM Proxy:  http://localhost:4000"
echo "📍 Backend API:    http://localhost:8000"
echo "📍 Frontend App:   http://localhost:5173"
echo "=================================="
echo ""

echo "🌐 Opening frontend in browser..."
xdg-open http://localhost:5173 2>/dev/null || open http://localhost:5173 2>/dev/null

echo "Press Ctrl+C to stop all services"
echo ""

wait