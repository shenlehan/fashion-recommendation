#!/bin/bash

echo "================================================"
echo "  时尚推荐系统 - 关闭中"
echo "================================================"
echo ""

echo "正在停止服务..."
echo ""

# Stop backend
if pkill -f "uvicorn app.main:app" 2>/dev/null; then
  echo "✓ 后端已停止"
else
  echo "⚠ 未找到后端进程"
fi

# Stop frontend
if pkill -f "node.*vite" 2>/dev/null; then
  echo "✓ 前端已停止"
else
  echo "⚠ 未找到前端进程"
fi

sleep 2

# Verify
echo ""
echo "验证中:"

if pgrep -f "uvicorn app.main:app" > /dev/null; then
  echo "✗ 后端仍在运行"
else
  echo "✓ 后端已停止"
fi

if pgrep -f "node.*vite" > /dev/null; then
  echo "✗ 前端仍在运行"
else
  echo "✓ 前端已停止"
fi

echo ""
echo "关闭完成！"
echo ""

