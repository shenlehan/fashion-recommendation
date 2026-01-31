# AutoDL 实例部署指南

## 一、租用实例要求

### 最低配置
- **GPU**: RTX 4090 (24GB) / A5000 (24GB)
- **内存**: 30GB+
- **存储**: 80GB+
- **镜像**: PyTorch 2.0+ / Python 3.10

### 推荐配置
- **GPU**: A100 (40GB)
- **内存**: 50GB+
- **存储**: 100GB+

---

## 二、快速部署 (一键启动)

### 1. 上传代码到实例
```bash
# 方法1: 通过 AutoDL 文件管理界面上传压缩包后解压
cd /root/autodl-tmp
unzip fashion-recommendation.zip

# 方法2: 通过 Git 克隆 (如果代码在 GitHub)
# cd /root/autodl-tmp
# git clone <你的仓库地址> fashion-recommendation
```

### 2. 一键安装环境
```bash
cd /root/autodl-tmp/fashion-recommendation
bash autodl_install.sh
```

### 3. 启动所有服务
```bash
bash start.sh
```

服务启动后访问:
- 前端: `http://你的实例IP:3000`
- 后端API: `http://你的实例IP:8000/docs`
- VTON服务: `http://你的实例IP:8001`

---

## 三、手动部署 (详细步骤)

### Step 1: 环境准备

#### 1.1 创建 Conda 环境
```bash
# 后端环境 (Qwen3-VL)
conda create -n pytorch python=3.10 -y
conda activate pytorch
pip install torch==2.4.0 torchvision==0.19.0 -i https://pypi.tuna.tsinghua.edu.cn/simple

# 前端 AI 环境 (CatVTON)
conda create -n catvton python=3.10 -y
conda activate catvton
pip install torch==2.4.0 torchvision==0.19.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 1.2 安装 Node.js
```bash
# 使用 NVM 安装 Node.js 18+
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18
nvm use 18
```

### Step 2: 安装依赖

#### 2.1 后端依赖
```bash
cd /root/autodl-tmp/fashion-recommendation/backend
conda activate pytorch
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 Qwen-VL
pip install transformers>=4.37.0 accelerate qwen-vl-utils -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 2.2 AI 服务依赖 (CatVTON)
```bash
cd /root/autodl-tmp/fashion-recommendation/ml/CatVTON
conda activate catvton
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 detectron2 (用于 DensePose)
python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
```

#### 2.3 前端依赖
```bash
cd /root/autodl-tmp/fashion-recommendation/frontend
npm install --registry=https://registry.npmmirror.com
```

### Step 3: 下载模型权重

#### 3.1 自动下载脚本
```bash
cd /root/autodl-tmp/fashion-recommendation/ml
conda activate catvton

# 下载 CatVTON 核心模型
python download_model.py

# 下载 DensePose 权重
python download_densepose.py

# 下载 AutoMask 权重
python download_automask.py
```

#### 3.2 手动下载 (如果自动下载失败)
```bash
# 设置 HuggingFace 镜像
export HF_ENDPOINT=https://hf-mirror.com

# 下载 CatVTON 权重
cd /root/autodl-tmp/fashion-recommendation/ml
huggingface-cli download zhengchong/CatVTON --local-dir ./CatVTON/model/catvton

# 下载 Stable Diffusion Inpainting
huggingface-cli download booksforcharlie/stable-diffusion-inpainting --local-dir ./CatVTON/model/sd-inpainting
```

### Step 4: 数据库初始化
```bash
cd /root/autodl-tmp/fashion-recommendation/backend
conda activate pytorch
python init_db.py
```

### Step 5: 配置环境变量

#### 5.1 后端环境变量
```bash
# backend/.env (如需要)
cat > /root/autodl-tmp/fashion-recommendation/backend/.env << 'EOF'
DATABASE_URL=sqlite:///./fashion.db
VTON_SERVER_URL=http://localhost:8001
EOF
```

#### 5.2 前端环境变量
```bash
# frontend/.env
cat > /root/autodl-tmp/fashion-recommendation/frontend/.env << 'EOF'
VITE_API_BASE_URL=http://你的实例IP:8000
EOF
```

### Step 6: 启动服务

#### 方法1: 使用启动脚本 (推荐)
```bash
cd /root/autodl-tmp/fashion-recommendation
bash start.sh
```

#### 方法2: 手动分别启动
```bash
# Terminal 1: 启动 VTON Server (端口 8001)
cd /root/autodl-tmp/fashion-recommendation/ml
conda activate catvton
python vton_server.py

# Terminal 2: 启动 Backend (端口 8000)
cd /root/autodl-tmp/fashion-recommendation/backend
conda activate pytorch
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 3: 启动 Frontend (端口 3000)
cd /root/autodl-tmp/fashion-recommendation/frontend
npm run dev
```

---

## 四、常见问题排查

### 1. 端口被占用
```bash
# 查看端口占用
netstat -tulnp | grep -E "3000|8000|8001"

# 杀死进程
kill -9 <PID>
```

### 2. CUDA Out of Memory
```bash
# 方案1: 减少 batch size (修改 vton_server.py)
# num_inference_steps=50 -> 30

# 方案2: 使用 CPU (不推荐,超慢)
# device = "cpu"

# 方案3: 清理显存
python -c "import torch; torch.cuda.empty_cache()"
```

### 3. 模型下载失败
```bash
# 切换到 HuggingFace 镜像
export HF_ENDPOINT=https://hf-mirror.com

# 或使用代理
# export HTTP_PROXY=http://127.0.0.1:7890
# export HTTPS_PROXY=http://127.0.0.1:7890
```

### 4. 前端无法连接后端
检查:
1. AutoDL 安全组开放 3000, 8000, 8001 端口
2. `frontend/.env` 中的 API 地址是否正确
3. 后端是否正常启动: `curl http://localhost:8000/health`

### 5. 查看日志
```bash
# 查看所有服务日志
tail -f /root/autodl-tmp/fashion-recommendation/logs/*.log

# 单独查看
tail -f /root/autodl-tmp/fashion-recommendation/logs/backend.log
tail -f /root/autodl-tmp/fashion-recommendation/logs/vton.log
tail -f /root/autodl-tmp/fashion-recommendation/logs/frontend.log
```

---

## 五、性能优化建议

### 1. 模型加速
- 使用 `torch.compile()` (PyTorch 2.0+)
- 启用 xFormers 优化
- 使用 float16 精度

### 2. 镜像持久化
```bash
# AutoDL 提供「保存镜像」功能
# 环境配置完成后,在控制台保存自定义镜像
# 下次直接使用该镜像,无需重复配置
```

### 3. 数据持久化
```bash
# 将数据库和上传文件放在 /root/autodl-tmp (持久化目录)
# 避免放在 /root 或系统盘 (可能会被清空)
```

---

## 六、停止服务

```bash
cd /root/autodl-tmp/fashion-recommendation
bash stop.sh
```

---

## 七、自动重启 (可选)

创建 systemd 服务 (需要 root 权限):
```bash
sudo tee /etc/systemd/system/fashion-app.service > /dev/null << 'EOF'
[Unit]
Description=Fashion Recommendation System
After=network.target

[Service]
Type=forking
User=root
WorkingDirectory=/root/autodl-tmp/fashion-recommendation
ExecStart=/bin/bash /root/autodl-tmp/fashion-recommendation/start.sh
ExecStop=/bin/bash /root/autodl-tmp/fashion-recommendation/stop.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable fashion-app
sudo systemctl start fashion-app
```

---

## 八、AutoDL 专用优化

### 1. JupyterLab 集成
AutoDL 默认提供 JupyterLab,可通过 Terminal 执行命令:
```bash
cd /root/autodl-tmp/fashion-recommendation
bash start.sh
```

### 2. SSH 连接
```bash
# 获取 SSH 连接命令 (在 AutoDL 控制台)
ssh -p <端口> root@<实例IP>

# 使用 VSCode Remote SSH 连接
# 更方便的开发体验
```

### 3. 端口映射
AutoDL 自动映射所有端口,无需额外配置。

访问地址:
- `http://<实例IP>:3000` (前端)
- `http://<实例IP>:8000` (后端)
- `http://<实例IP>:8001` (VTON)

---

## 九、资源监控

```bash
# GPU 使用情况
watch -n 1 nvidia-smi

# 内存使用
htop

# 磁盘空间
df -h
```

---

## 联系支持

遇到问题请检查:
1. 日志文件: `logs/*.log`
2. 端口占用: `netstat -tulnp`
3. 显存占用: `nvidia-smi`
