#!/bin/bash

# 1. 【关键】强制加载你刚才安装的新版 Node环境
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "=== 正在清理旧进程... ==="
pkill -f uvicorn
pkill -f vite

echo "=== 正在启动后端 (Backend) - 端口 8000... ==="
# 启动后端并记录日志
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &

echo "=== 正在启动前端 (Frontend) - 端口 5173... ==="
cd frontend
# 【关键】加上 --host 0.0.0.0 确保你能从浏览器访问
nohup npm run dev -- --host 0.0.0.0 > ../logs/frontend.log 2>&1 &

echo "✅ 服务已全部启动！"
echo "后端地址: http://$(curl -s ifconfig.me):8000"
echo "前端地址: http://$(curl -s ifconfig.me):5173 (请在浏览器访问这个)"
