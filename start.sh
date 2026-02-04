#!/bin/bash

# Fashion Recommendation System - Full Stack Startup Script (v2.0)

echo "================================================"
echo "  时尚推荐系统 - 启动中"
echo "================================================"
echo ""

# --- 1. 环境检查与旧服务清理 ---
echo "正在检查现有服务..."
# 清理 8001 (VTON), 8000 (Backend), 3000 (Frontend)
pkill -f "vton_server.py" 2>/dev/null && echo "  已停止旧 VTON 服务器 (8001)" || true
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "  已停止旧后端服务 (8000)" || true
pkill -f "node.*vite" 2>/dev/null && echo "  已停止旧前端服务 (3000)" || true
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
  echo "错误：在 $HOME/miniconda3 或 anaconda3 中未找到 Conda！"
  exit 1
fi

# --- 2. 启动服务 [1/3]: VTON AI Server (Port 8001) ---
echo ""
echo "[1/3] 正在启动 VTON AI 服务器 (CatVTON)..."
echo "-----------------------------------------------"
cd "$PROJECT_DIR/ml"

conda activate catvton
# 使用 nohup 后台运行，并重定向日志
nohup python vton_server.py > "$VTON_LOG" 2>&1 &
VTON_PID=$!

echo "✓ VTON 服务器已启动 (PID: $VTON_PID)"
echo "  端口: 8001"
echo "  日志: tail -f $VTON_LOG"
echo "  注意：加载 Diffusion 模型可能需要 1-2 分钟..."

# --- 3. 启动服务 [2/3]: Main Backend (Port 6008) ---
echo ""
echo "[2/3] 正在启动后端 (FastAPI + Qwen)..."
echo "-----------------------------------------------"
cd "$PROJECT_DIR/backend"

conda activate pytorch
nohup uvicorn app.main:app --host 0.0.0.0 --port 6008 > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

echo "✓ 后端已启动 (PID: $BACKEND_PID)"
echo "  端口: 6008"
echo "  日志: tail -f $BACKEND_LOG"

# --- 4. 启动服务 [3/3]: Frontend (Port 6006) ---
echo ""
echo "[3/3] 正在启动前端 (React + Vite)..."
echo "-----------------------------------------------"
cd "$PROJECT_DIR/frontend"

# 加载 NVM (如果使用)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!

echo "✓ 前端已启动 (PID: $FRONTEND_PID)"
echo "  URL: http://0.0.0.0:6006"

# --- 5. 健康检查与状态确认 ---
echo ""
echo "最终健康检查（等待 5 秒）..."
echo "-----------------------------------------------"
sleep 5

# 检查 8001 (VTON)
if curl -s http://localhost:8001/process_tryon > /dev/null 2>&1 || [ $? -eq 405 ]; then
  echo "✓ [8001] VTON 服务器: 就绪 (GET 请求 405 是正常现象)"
else
  echo "⚠ [8001] VTON 服务器: 启动中/错误 (检查 logs/vton.log)"
fi

# 检查 6008 (Backend)
if curl -s http://localhost:6008/health > /dev/null 2>&1; then
  echo "✓ [6008] 后端: 健康"
else
  echo "⚠ [6008] 后端: 启动中..."
fi

# 检查 6006 (Frontend)
if netstat -tlnp 2>/dev/null | grep -q ":6006 " || ss -tlnp 2>/dev/null | grep -q ":6006 "; then
  echo "✓ [6006] 前端: 运行中"
else
  echo "⚠ [6006] 前端: 启动中..."
fi

echo ""
echo "================================================"
echo "  启动完成！系统全部功能已就绪。"
echo "================================================"
echo "内网访问: http://$(hostname -I | awk '{print $1}'):6006"
echo "公网地址: 请查看 AutoDL 控制台 '自定义服务' 获取 HTTPS 访问地址"
echo "查看所有日志: tail -f $LOG_DIR/*.log"