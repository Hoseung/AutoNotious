#!/bin/bash

echo "🚀 Starting AutoNotoin Application with tmux..."
echo "=============================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

SESSION_NAME="autonotoin"

if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "⚠️  Session '$SESSION_NAME' already exists. Killing it..."
    tmux kill-session -t $SESSION_NAME
    sleep 1
fi

echo "📦 Creating tmux session: $SESSION_NAME"
tmux new-session -d -s $SESSION_NAME -n "LiteLLM"

echo "1️⃣  Starting LiteLLM proxy server (Port 4000)..."
tmux send-keys -t $SESSION_NAME:0 "source .venv/bin/activate && litellm --model gpt-4o-mini --port 4000" C-m

echo "2️⃣  Starting Backend server (Port 8000)..."
tmux new-window -t $SESSION_NAME:1 -n "Backend"
tmux send-keys -t $SESSION_NAME:1 "source .venv/bin/activate && cd backend && uvicorn app.main:app --reload --port 8000" C-m

echo "3️⃣  Starting Frontend development server (Port 5173)..."
tmux new-window -t $SESSION_NAME:2 -n "Frontend"
tmux send-keys -t $SESSION_NAME:2 "cd frontend && npm run dev" C-m

sleep 5

echo ""
echo "✅ All services started in tmux session!"
echo "=============================================="
echo "📍 LiteLLM Proxy:  http://localhost:4000"
echo "📍 Backend API:    http://localhost:8000"
echo "📍 Frontend App:   http://localhost:5173"
echo "=============================================="
echo ""
echo "📌 Tmux Commands:"
echo "   View all windows:    tmux attach -t $SESSION_NAME"
echo "   Switch windows:      Ctrl+b then 0/1/2"
echo "   Detach from tmux:    Ctrl+b then d"
echo "   Kill all services:   tmux kill-session -t $SESSION_NAME"
echo ""

echo "🌐 Opening frontend in browser..."
sleep 2
xdg-open http://localhost:5173 2>/dev/null || open http://localhost:5173 2>/dev/null

echo "Attaching to tmux session..."
echo "Press Ctrl+b then d to detach, or Ctrl+b then x to kill current pane"
tmux attach -t $SESSION_NAME