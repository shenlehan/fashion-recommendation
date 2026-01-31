#!/bin/bash
# AutoDL 上传失败诊断脚本

echo "========================================"
echo "上传失败诊断工具"
echo "========================================"

# 1. 检查后端服务
echo -e "\n1️⃣ 检查后端服务状态..."
if ps aux | grep -v grep | grep "uvicorn app.main:app" > /dev/null; then
    echo "✅ 后端服务正在运行"
    ps aux | grep -v grep | grep uvicorn
else
    echo "❌ 后端服务未运行！"
    echo "   启动命令: cd backend && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 6008 > ../logs/backend.log 2>&1 &"
fi

# 2. 检查端口监听
echo -e "\n2️⃣ 检查端口监听..."
if netstat -tuln | grep ":6008" > /dev/null; then
    echo "✅ 端口 6008 正在监听"
    netstat -tuln | grep ":6008"
else
    echo "❌ 端口 6008 未监听！"
fi

if netstat -tuln | grep ":6006" > /dev/null; then
    echo "✅ 端口 6006 正在监听 (前端)"
    netstat -tuln | grep ":6006"
else
    echo "❌ 端口 6006 未监听！"
fi

# 3. 测试后端健康检查
echo -e "\n3️⃣ 测试后端健康检查..."
if curl -s http://localhost:6008/health > /dev/null; then
    echo "✅ 后端健康检查成功"
    curl -s http://localhost:6008/health | python -m json.tool
else
    echo "❌ 后端健康检查失败！"
fi

# 4. 测试 API 根路径
echo -e "\n4️⃣ 测试 API 根路径..."
curl -s http://localhost:6008/ | python -m json.tool

# 5. 检查前端配置
echo -e "\n5️⃣ 检查前端配置..."
if [ -f "frontend/.env" ]; then
    echo "✅ 前端 .env 文件:"
    cat frontend/.env
else
    echo "❌ 前端 .env 文件不存在！"
fi

# 6. 检查后端日志最新内容
echo -e "\n6️⃣ 后端日志（最新20行）..."
if [ -f "logs/backend.log" ]; then
    tail -20 logs/backend.log
else
    echo "❌ 后端日志文件不存在！"
fi

# 7. 检查 uploads 目录
echo -e "\n7️⃣ 检查 uploads 目录..."
if [ -d "backend/uploads" ]; then
    echo "✅ uploads 目录存在"
    ls -lh backend/uploads | tail -10
else
    echo "⚠️ uploads 目录不存在，将自动创建"
fi

# 8. 磁盘空间
echo -e "\n8️⃣ 磁盘空间..."
df -h | grep -E "Filesystem|/root|/$"

echo -e "\n========================================"
echo "诊断完成"
echo "========================================"
echo ""
echo "常见问题修复："
echo "1. 后端未启动 → cd /root/autodl-tmp/fashion-recommendation && bash start.sh"
echo "2. 端口被占用 → pkill -f uvicorn && bash start.sh"
echo "3. 前端配置错误 → 检查 frontend/.env 中 VITE_API_BASE_URL"
echo "4. 查看实时日志 → tail -f logs/backend.log"
