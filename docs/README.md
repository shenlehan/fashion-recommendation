# Fashion Recommendation System

基于 AI 的智能穿搭推荐系统，集成 Qwen3-VL 视觉理解和 CatVTON 虚拟试衣功能。

## 快速开始

### AutoDL 实例部署 (推荐)

**一键部署命令:**

```bash
cd /root/autodl-tmp/fashion-recommendation/scripts/deployment
bash autodl_install.sh  # 安装环境

cd /root/autodl-tmp/fashion-recommendation
bash start.sh           # 启动所有服务
```

**详细文档:**
- [AutoDL 快速启动指南](./QUICKSTART_AUTODL.md) - 3分钟部署
- [AutoDL 详细部署文档](./AUTODL_SETUP.md) - 完整配置说明
- [代码上传指南](./UPLOAD_GUIDE.md) - Windows 到 AutoDL

**Windows 用户快速上传:**

1. 编辑 `upload_to_autodl.ps1`，填入你的 AutoDL 实例信息
2. 运行: `powershell -ExecutionPolicy Bypass -File .\upload_to_autodl.ps1`

---

# 核心功能

1. **智能衣橱管理** - 拍照上传，AI 自动识别分类
2. **语义搜索** - 「红色连衣裙」「运动风外套」智能检索
3. **场景推荐** - 根据天气、场合、风格推荐穿搭
4. **多轮对话调整** - 连续优化穿搭方案（"换个外套"、"更暖色系"）
5. **虚拟试衣 (VTON)** - 实时预览上身效果

---

## 技术架构

### 后端
- **FastAPI** - 高性能 Web 框架
- **Qwen3-VL** - 阿里通义千问多模态模型 (8B)
- **SQLite** - 轻量级数据库
- **Redis** - 天气数据缓存
- **OpenWeatherMap API** - 天气数据源
- **APScheduler** - 定时任务调度
- **httpx** - 异步HTTP客户端

### 前端
- **React 19.1** - 现代化 UI 框架
- **Vite** - 极速开发服务器
- **Axios** - HTTP 客户端

### AI 服务
- **CatVTON** - 虚拟试衣 (Diffusion Model, ICLR 2025)
- **AutoMasker** - 自动掩码生成 (DensePose + SCHP)
- **Qwen3-VL** - 衣物识别和推荐生成
- **RAG检索** - sentence-transformers + CLIP + ChromaDB

---

## 系统要求

### 最低配置
- GPU: RTX 4090 (24GB) / A5000 (24GB)
- 内存: 30GB+
- 存储: 80GB+
- Python: 3.10+
- Node.js: 18+

### 推荐配置 (AutoDL)
- GPU: A100 (40GB)
- 内存: 50GB+
- 存储: 100GB+
- 镜像: PyTorch 2.0+

---

## 本地部署 (非 AutoDL)

### 1. 克隆项目
```bash
git clone <repository-url>
cd fashion-recommendation
```

### 2. 创建 Conda 环境
```bash
# 后端环境
conda create -n pytorch python=3.10 -y
conda activate pytorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# VTON 环境
conda create -n catvton python=3.10 -y
conda activate catvton
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 3. 安装依赖
```bash
# 后端
cd backend
conda activate pytorch
pip install -r requirements.txt

# VTON 服务
cd ../ml/CatVTON
conda activate catvton
pip install -r requirements.txt
pip install 'git+https://github.com/facebookresearch/detectron2.git'

# 前端
cd ../../frontend
npm install
```

### 4. 启动服务
```bash
# 使用启动脚本
bash start.sh

# 或手动启动
# Terminal 1: VTON Server
cd ml && conda activate catvton && python vton_server.py

# Terminal 2: Backend
cd backend && conda activate pytorch && uvicorn app.main:app --host 0.0.0.0 --port 6008

# Terminal 3: Frontend
cd frontend && npm run dev
```

---

## 访问应用

启动成功后访问:

- **前端界面**: `http://localhost:6006`
- **后端 API**: `http://localhost:6008/docs`
- **健康检查**: `http://localhost:6008/health`

AutoDL 实例访问:
- 将 `localhost` 替换为你的实例 IP
- 例: `http://123.45.67.89:6006`

---

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 6006 | React 开发服务器 |
| Backend API | 6008 | FastAPI + Qwen3-VL |
| VTON Server | 8001 | CatVTON 虚拟试衣 |

---

## 常用命令

```bash
# 环境检查
bash scripts/utils/check_env.sh

# 启动所有服务
bash start.sh

# 停止所有服务
bash stop.sh

# 查看日志
tail -f logs/*.log

# 单独查看
tail -f logs/backend.log
tail -f logs/vton.log
tail -f logs/frontend.log
```

---

## 故障排查

### 端口被占用
```bash
netstat -tulnp | grep -E "6006|6008|8001"
kill -9 <PID>
```

### CUDA Out of Memory
```bash
python -c "import torch; torch.cuda.empty_cache()"
nvidia-smi  # 查看 GPU 使用情况
```

### 模型下载失败
```bash
export HF_ENDPOINT=https://hf-mirror.com
cd ml && python download_model.py
```

### 前端无法连接后端
1. 检查后端是否启动: `curl http://localhost:6008/health`
2. 检查 `frontend/.env` 配置
3. 检查防火墙/安全组设置

---

## 项目结构

```
fashion-recommendation/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── core/        # 配置和数据库
│   │   ├── models/      # SQLAlchemy 模型 (含 ConversationSession)
│   │   ├── routes/      # API 路由 (/recommend/adjust 多轮对话)
│   │   ├── schemas/     # Pydantic 模式
│   │   └── services/    # 业务逻辑 (conversation_manager)
│   └── requirements.txt
├── frontend/            # React 前端
│   ├── src/
│   │   ├── pages/       # 页面组件 (Wardrobe/Recommendations/Conversation/Profile)
│   │   └── services/    # API 调用
│   └── package.json
├── ml/                  # AI 服务
│   ├── CatVTON/         # 虚拟试衣模型
│   └── vton_server.py   # VTON FastAPI 服务器
├── autodl_install.sh    # AutoDL 自动安装脚本
├── start.sh             # 启动脚本
├── stop.sh              # 停止脚本
└── check_env.sh         # 环境检查脚本
```

---

## 开发指南

### 添加新的 API 端点
1. 在 `backend/app/routes/` 创建路由文件
2. 在 `backend/app/main.py` 注册路由
3. 在 `frontend/src/services/api.js` 添加前端调用

### 修改前端页面
1. 编辑 `frontend/src/pages/` 下的组件
2. Vite 热重载自动生效

### 调试后端
```bash
cd backend
conda activate pytorch
uvicorn app.main:app --reload  # 开启热重载
```

---

## 许可证

MIT License

---

## 贡献

欢迎提交 Issue 和 Pull Request!

---

## 支持

遇到问题?
1. 查看 [AutoDL 部署文档](./AUTODL_SETUP.md)
2. 运行环境检查: `bash check_env.sh`
3. 查看日志: `tail -f logs/*.log`
4. 提交 Issue