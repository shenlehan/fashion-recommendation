#!/bin/bash

# Fashion Recommendation System Startup Script

echo "================================================"
echo "  Fashion Recommendation System - Startup"
echo "================================================"
echo ""

# Stop existing services if any
echo "Checking for existing services..."
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "  Stopped old backend" || true
pkill -f "node.*vite" 2>/dev/null && echo "  Stopped old frontend" || true
sleep 2

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# Start Backend
echo ""
echo "[1/2] Starting Backend (FastAPI + Qwen3-VL)..."
echo "-----------------------------------------------"

cd "$PROJECT_DIR/backend"

# Load conda
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  . "$HOME/miniconda3/etc/profile.d/conda.sh"
else
  echo "ERROR: Conda not found!"
  exit 1
fi

conda activate pytorch
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

echo "✓ Backend started (PID: $BACKEND_PID)"
echo "  API: http://0.0.0.0:8000"
echo "  Logs: tail -f $BACKEND_LOG"
echo ""
echo "  NOTE: Qwen3-VL model loads on first upload (~2 min)"

sleep 3

# Start Frontend
echo ""
echo "[2/2] Starting Frontend (React + Vite)..."
echo "-----------------------------------------------"

cd "$PROJECT_DIR/frontend"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!

echo "✓ Frontend started (PID: $FRONTEND_PID)"
echo "  URL: http://0.0.0.0:3000"
echo "  Logs: tail -f $FRONTEND_LOG"

sleep 5

# Health check
echo ""
echo "Health Check:"
echo "-----------------------------------------------"

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
  echo "✓ Backend: HEALTHY"
else
  echo "⚠ Backend: Starting..."
fi

if netstat -tlnp 2>/dev/null | grep -q ":3000 " || ss -tlnp 2>/dev/null | grep -q ":3000 "; then
  echo "✓ Frontend: RUNNING"
else
  echo "⚠ Frontend: Starting..."
fi

# Summary
echo ""
echo "================================================"
echo "  Startup Complete!"
echo "================================================"
echo ""
echo "Access: http://$(hostname -I | awk '{print $1}'):3000"
echo ""
echo "Commands:"
echo "  Stop:  bash stop.sh"
echo "  Logs:  tail -f $BACKEND_LOG $FRONTEND_LOG"
echo ""
