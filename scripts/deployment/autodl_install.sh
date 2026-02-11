#!/bin/bash
# Fashion Recommendation System - AutoDL 自动安装脚本
# 适用于 AutoDL 实例环境

set -e  # 遇到错误立即退出

echo "=============================================="
echo "  Fashion Recommendation - AutoDL 部署"
echo "=============================================="
echo ""

# 获取项目根目录（脚本在 scripts/deployment/ 目录下，向上两级即为项目根目录）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
echo "📁 项目目录: $PROJECT_DIR"

# ===== 1. 检查基础环境 =====
echo ""
echo "[1/6] 检查基础环境..."
echo "----------------------------------------------"

# 检查 Conda
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    echo "✓ 找到 Miniconda"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
    echo "✓ 找到 Anaconda"
else
    echo "❌ 未找到 Conda! 正在安装 Miniconda..."
    cd /tmp
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
    source $HOME/miniconda3/etc/profile.d/conda.sh
    conda init bash
    echo "✓ Miniconda 安装完成"
fi

# 检查 GPU
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -n 1)
    echo "✓ GPU: $GPU_INFO"
else
    echo "⚠ 未检测到 GPU,将使用 CPU (速度会很慢)"
fi

# ===== 2. 创建 Conda 环境 =====
echo ""
echo "[2/6] 创建 Conda 环境..."
echo "----------------------------------------------"

# 2.1 后端环境 (pytorch)
if conda env list | grep -q "^pytorch "; then
    echo "✓ pytorch 环境已存在,跳过创建"
else
    echo "创建 pytorch 环境 (用于后端 FastAPI + Qwen3-VL)..."
    conda create -n pytorch python=3.10 -y
    echo "✓ pytorch 环境创建完成"
fi

# 2.2 前端 AI 环境 (catvton)
if conda env list | grep -q "^catvton "; then
    echo "✓ catvton 环境已存在,跳过创建"
else
    echo "创建 catvton 环境 (用于 VTON 服务)..."
    conda create -n catvton python=3.10 -y
    echo "✓ catvton 环境创建完成"
fi

# ===== 3. 安装 PyTorch (两个环境都需要) =====
echo ""
echo "[3/6] 安装 PyTorch..."
echo "----------------------------------------------"

# 使用清华镜像加速
PIP_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"

# 安装到 pytorch 环境
conda activate pytorch
echo "正在 pytorch 环境中安装 PyTorch 2.4.0..."
pip install torch==2.4.0 torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu121 || \
pip install torch==2.4.0 torchvision==0.19.0 -i $PIP_INDEX
echo "✓ pytorch 环境的 PyTorch 安装完成"

# 安装到 catvton 环境
conda activate catvton
echo "正在 catvton 环境中安装 PyTorch 2.4.0..."
pip install torch==2.4.0 torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu121 || \
pip install torch==2.4.0 torchvision==0.19.0 -i $PIP_INDEX
echo "✓ catvton 环境的 PyTorch 安装完成"

# ===== 4. 安装后端依赖 =====
echo ""
echo "[4/6] 安装后端依赖..."
echo "----------------------------------------------"

conda activate pytorch
cd "$PROJECT_DIR/backend"

echo "安装 FastAPI 及其依赖 (包含Redis缓存)..."
pip install -r requirements.txt -i $PIP_INDEX

echo "安装 Qwen-VL 相关库..."
pip install transformers>=4.37.0 accelerate>=0.20.0 qwen-vl-utils einops timm -i $PIP_INDEX

echo "✓ 后端依赖安装完成"

# 检查Redis并提示
 echo ""
echo "ℹ️  天气系统缓存配置:"
if command -v redis-server &> /dev/null; then
    echo "  ✓ Redis 已安装 (优化缓存)"
else
    echo "  ⚠ Redis 未安装 (将使用内存缓存)"
    echo "  可选安装: apt-get install redis-server -y"
fi
echo ""

# 初始化数据库
echo "初始化数据库..."
python init_db.py
echo "✓ 数据库初始化完成"

# ===== 5. 安装 VTON 服务依赖 =====
echo ""
echo "[5/6] 安装 VTON 服务依赖..."
echo "----------------------------------------------"

conda activate catvton
cd "$PROJECT_DIR/ml"

# 设置 HuggingFace 镜像
export HF_ENDPOINT=https://hf-mirror.com

echo "安装 CatVTON 依赖..."
cd CatVTON
pip install -r requirements.txt -i $PIP_INDEX

echo "安装 detectron2 (用于 DensePose)..."
# 方法1: 尝试预编译包
if pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu121/torch2.4/index.html 2>/dev/null; then
    echo "✓ 使用预编译包安装成功"
else
    # 方法2: 从清华镜像 GitHub 克隆编译
    echo "预编译包失败，尝试源码编译..."
    cd /tmp
    git clone https://github.com.cnpmjs.org/facebookresearch/detectron2.git || \
    git clone https://gitclone.com/github.com/facebookresearch/detectron2.git || \
    git clone https://hub.fastgit.xyz/facebookresearch/detectron2.git
    
    if [ -d "/tmp/detectron2" ]; then
        cd detectron2
        python -m pip install -e .
        echo "✓ 源码编译安装成功"
    else
        echo "⚠ detectron2 安装失败，VTON功能可能受影响"
        echo "   可以稍后手动安装: pip install detectron2"
    fi
fi

echo "✓ VTON 服务依赖安装完成"

# ===== 6. 安装前端依赖 =====
echo ""
echo "[6/6] 安装前端依赖..."
echo "----------------------------------------------"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js! 正在通过 NVM 安装..."
    
    # 安装 NVM
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
    
    # 加载 NVM
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    
    # 安装 Node.js 18
    nvm install 18
    nvm use 18
    echo "✓ Node.js 安装完成"
else
    NODE_VERSION=$(node -v)
    echo "✓ 已安装 Node.js $NODE_VERSION"
fi

cd "$PROJECT_DIR/frontend"

# 使用淘宝镜像加速
echo "安装前端依赖 (使用淘宝镜像)..."
npm install --registry=https://registry.npmmirror.com

echo "✓ 前端依赖安装完成"

# ===== 7. 下载模型权重 =====
echo ""
echo "[额外] 下载模型权重..."
echo "----------------------------------------------"
echo "⚠ 模型文件较大 (~20GB),首次启动时会自动下载"
echo "  如需手动下载,请执行:"
echo "  cd $PROJECT_DIR/ml && conda activate catvton"
echo "  python download_model.py"
echo ""

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/backend/uploads"

# ===== 完成 =====
echo ""
echo "=============================================="
echo "  ✨ 安装完成！"
echo "=============================================="
echo ""
echo "📝 下一步操作:"
echo "  1. 启动服务: cd /root/autodl-tmp/fashion-recommendation && bash start.sh"
echo "  2. 访问前端: http://$(hostname -I | awk '{print $1}'):3000"
echo "  3. 查看日志: tail -f logs/*.log"
echo ""
echo "📦 已创建的 Conda 环境:"
echo "  - pytorch (后端)"
echo "  - catvton (VTON服务)"
echo ""
echo "⚙️ 服务端口:"
echo "  - Frontend: 3000"
echo "  - Backend API: 8000"
echo "  - VTON Server: 8001"
echo ""
echo "💡 提示:"
echo "  - 首次上传图片时,Qwen3-VL 模型会自动下载 (~16GB)"
echo "  - 首次使用 VTON 功能时,CatVTON 模型会自动下载 (~5GB)"
echo "  - 预计总下载: ~25GB,请确保磁盘空间充足"
echo "  - Redis缓存(可选): 会自动降级为内存缓存，不影响使用"
echo ""
echo "🔧 故障排查:"
echo "  - 查看详细文档: cat AUTODL_SETUP.md"
echo "  - 端口占用: netstat -tulnp | grep -E '3000|8000|8001'"
echo "  - GPU状态: nvidia-smi"
echo ""
