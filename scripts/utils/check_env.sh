#!/bin/bash
# AutoDL 环境检查脚本

echo "=============================================="
echo "  Fashion Recommendation - 环境检查"
echo "=============================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass=0
check_fail=0

# 检查函数
check_item() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((check_pass++))
    else
        echo -e "${RED}✗${NC} $2"
        ((check_fail++))
    fi
}

# 1. 检查 Conda
echo "[1] Conda 环境"
echo "----------------------------------------------"
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    check_item 0 "Conda 已安装 (Miniconda)"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
    check_item 0 "Conda 已安装 (Anaconda)"
else
    check_item 1 "Conda 未安装"
fi

# 检查 pytorch 环境
if conda env list | grep -q "^pytorch "; then
    check_item 0 "pytorch 环境存在"
else
    check_item 1 "pytorch 环境不存在"
fi

# 检查 catvton 环境
if conda env list | grep -q "^catvton "; then
    check_item 0 "catvton 环境存在"
else
    check_item 1 "catvton 环境不存在"
fi

# 2. 检查 GPU
echo ""
echo "[2] GPU 状态"
echo "----------------------------------------------"
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader | head -n 1)
    GPU_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader | head -n 1)
    check_item 0 "GPU: $GPU_NAME"
    echo "  总显存: $GPU_MEM"
    echo "  已使用: $GPU_USED"
else
    check_item 1 "未检测到 NVIDIA GPU"
fi

# 3. 检查 Python 包
echo ""
echo "[3] Python 依赖 (pytorch 环境)"
echo "----------------------------------------------"
conda activate pytorch 2>/dev/null
if [ $? -eq 0 ]; then
    # 检查关键包
    python -c "import torch" 2>/dev/null
    check_item $? "torch"
    
    python -c "import transformers" 2>/dev/null
    check_item $? "transformers"
    
    python -c "import fastapi" 2>/dev/null
    check_item $? "fastapi"
    
    python -c "import uvicorn" 2>/dev/null
    check_item $? "uvicorn"
fi

echo ""
echo "[4] Python 依赖 (catvton 环境)"
echo "----------------------------------------------"
conda activate catvton 2>/dev/null
if [ $? -eq 0 ]; then
    python -c "import torch" 2>/dev/null
    check_item $? "torch"
    
    python -c "import diffusers" 2>/dev/null
    check_item $? "diffusers"
    
    python -c "import detectron2" 2>/dev/null
    check_item $? "detectron2"
fi

# 4. 检查 Node.js
echo ""
echo "[5] Node.js 环境"
echo "----------------------------------------------"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    check_item 0 "Node.js $NODE_VERSION"
    
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm -v)
        check_item 0 "npm $NPM_VERSION"
    else
        check_item 1 "npm 未安装"
    fi
else
    check_item 1 "Node.js 未安装"
fi

# 5. 检查项目文件
echo ""
echo "[6] 项目结构"
echo "----------------------------------------------"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

[ -d "$PROJECT_DIR/backend" ] && check_item 0 "backend/ 目录" || check_item 1 "backend/ 目录缺失"
[ -d "$PROJECT_DIR/frontend" ] && check_item 0 "frontend/ 目录" || check_item 1 "frontend/ 目录缺失"
[ -d "$PROJECT_DIR/ml" ] && check_item 0 "ml/ 目录" || check_item 1 "ml/ 目录缺失"

[ -f "$PROJECT_DIR/backend/app/main.py" ] && check_item 0 "backend/app/main.py" || check_item 1 "backend 入口文件缺失"
[ -f "$PROJECT_DIR/ml/vton_server.py" ] && check_item 0 "ml/vton_server.py" || check_item 1 "VTON 服务文件缺失"
[ -d "$PROJECT_DIR/frontend/node_modules" ] && check_item 0 "frontend 依赖已安装" || check_item 1 "frontend 依赖未安装"

# 6. 检查端口占用
echo ""
echo "[7] 端口状态"
echo "----------------------------------------------"
PORT_6006=$(netstat -tlnp 2>/dev/null | grep ":6006 " || ss -tlnp 2>/dev/null | grep ":6006 ")
if [ -z "$PORT_6006" ]; then
    check_item 0 "端口 6006 (前端) 空闲"
else
    echo -e "${YELLOW}⚠${NC} 端口 6006 已被占用"
    echo "  $PORT_6006"
fi

PORT_6008=$(netstat -tlnp 2>/dev/null | grep ":6008 " || ss -tlnp 2>/dev/null | grep ":6008 ")
if [ -z "$PORT_6008" ]; then
    check_item 0 "端口 6008 (后端) 空闲"
else
    echo -e "${YELLOW}⚠${NC} 端口 6008 已被占用"
    echo "  $PORT_6008"
fi

PORT_8001=$(netstat -tlnp 2>/dev/null | grep ":8001 " || ss -tlnp 2>/dev/null | grep ":8001 ")
if [ -z "$PORT_8001" ]; then
    check_item 0 "端口 8001 (VTON) 空闲"
else
    echo -e "${YELLOW}⚠${NC} 端口 8001 已被占用"
    echo "  $PORT_8001"
fi

# 7. 检查磁盘空间
echo ""
echo "[8] 磁盘空间"
echo "----------------------------------------------"
DISK_AVAIL=$(df -h $PROJECT_DIR | tail -1 | awk '{print $4}')
echo "可用空间: $DISK_AVAIL"
DISK_AVAIL_GB=$(df -BG $PROJECT_DIR | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$DISK_AVAIL_GB" -gt 30 ]; then
    check_item 0 "磁盘空间充足 (>30GB)"
else
    echo -e "${YELLOW}⚠${NC} 磁盘空间不足 (<30GB),模型下载可能失败"
fi

# 8. 检查内存
echo ""
echo "[9] 系统内存"
echo "----------------------------------------------"
MEM_TOTAL=$(free -h | grep Mem | awk '{print $2}')
MEM_AVAIL=$(free -h | grep Mem | awk '{print $7}')
echo "总内存: $MEM_TOTAL"
echo "可用内存: $MEM_AVAIL"

# 总结
echo ""
echo "=============================================="
echo "  检查结果汇总"
echo "=============================================="
echo -e "${GREEN}通过: $check_pass${NC}"
echo -e "${RED}失败: $check_fail${NC}"
echo ""

if [ $check_fail -eq 0 ]; then
    echo -e "${GREEN}✓ 环境检查全部通过,可以运行 bash start.sh 启动服务${NC}"
    exit 0
else
    echo -e "${RED}✗ 存在 $check_fail 个问题,请先运行 bash scripts/deployment/autodl_install.sh 安装依赖${NC}"
    echo ""
    echo "安装命令:"
    echo "  cd scripts/deployment && bash autodl_install.sh"
    exit 1
fi
