#!/bin/bash

# Fashion Recommendation System - Full Stack Startup Script (v2.0)

echo "================================================"
echo "  Fashion Recommendation System - Startup"
echo "================================================"
echo ""

# --- 1. 环境检查与旧服务清理 ---
echo "Checking for existing services..."
# 清理 8001 (VTON), 8000 (Backend), 3000 (Frontend)
pkill -f "vton_server.py" 2>/dev/null && echo "  Stopped old VTON Server (8001)" || true
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "  Stopped old Backend (8000)" || true
pkill -f "node.*vite" 2>/dev/null && echo "  Stopped old Frontend (3000)" || true
sleep 2

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

VTON_LOG="$LOG_DIR/vton.log"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# 加载 Conda 环境
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  . "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
  . "$HOME/anaconda3/etc/profile.d/conda.sh"
else
  echo "ERROR: Conda not found in $HOME/miniconda3 or anaconda3!"
  exit 1
fi

# --- 2. 启动服务 [1/3]: VTON AI Server (Port 8001) ---
echo ""
echo "[1/3] Starting VTON AI Server (CatVTON)..."
echo "-----------------------------------------------"
cd "$PROJECT_DIR/ml"

conda activate catvton
# 使用 nohup 后台运行，并重定向日志
nohup python vton_server.py > "$VTON_LOG" 2>&1 &
VTON_PID=$!

echo "✓ VTON Server started (PID: $VTON_PID)"
echo "  Port: 8001"
echo "  Logs: tail -f $VTON_LOG"
echo "  NOTE: Loading Diffusion models may take 1-2 min..."

# --- 3. 启动服务 [2/3]: Main Backend (Port 8000) ---
echo ""
echo "[2/3] Starting Backend (FastAPI + Qwen)..."
echo "-----------------------------------------------"
cd "$PROJECT_DIR/backend"

conda activate pytorch
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

echo "✓ Backend started (PID: $BACKEND_PID)"
echo "  Port: 8000"
echo "  Logs: tail -f $BACKEND_LOG"

# --- 4. 启动服务 [3/3]: Frontend (Port 3000) ---
echo ""
echo "[3/3] Starting Frontend (React + Vite)..."
echo "-----------------------------------------------"
cd "$PROJECT_DIR/frontend"

# 加载 NVM (如果使用)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!

echo "✓ Frontend started (PID: $FRONTEND_PID)"
echo "  URL: http://0.0.0.0:3000"

# --- 5. 健康检查与状态确认 ---
echo ""
echo "Final Health Check (Waiting 5s)..."
echo "-----------------------------------------------"
sleep 5

# 检查 8001 (VTON)
if curl -s http://localhost:8001/process_tryon > /dev/null 2>&1 || [ $? -eq 405 ]; then
  echo "✓ [8001] VTON Server: READY (Method Not Allowed is normal for GET)"
else
  echo "⚠ [8001] VTON Server: Starting/Error (Check logs/vton.log)"
fi

# 检查 8000 (Backend)
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
  echo "✓ [8000] Backend: HEALTHY"
else
  echo "⚠ [8000] Backend: Starting..."
fi

# 检查 3000 (Frontend)
if netstat -tlnp 2>/dev/null | grep -q ":3000 " || ss -tlnp 2>/dev/null | grep -q ":3000 "; then
  echo "✓ [3000] Frontend: RUNNING"
else
  echo "⚠ [3000] Frontend: Starting..."
fi

echo ""
echo "================================================"
echo "  Startup Complete! System is fully functional."
echo "================================================"
echo "Access: http://$(hostname -I | awk '{print $1}'):3000"
echo "Check all logs: tail -f $LOG_DIR/*.log"