# Fashion Recommendation System

> **📖 完整文档请查看 [`docs/`](./docs/) 目录**

## 快速开始

### AutoDL 部署
```bash
cd scripts/deployment
bash autodl_install.sh  # 安装环境
bash start.sh           # 启动服务
```

### 文档导航
- 📘 [项目介绍](./docs/README.md) - 完整文档
- 📗 [AutoDL 快速启动](./docs/QUICKSTART_AUTODL.md) - 3分钟部署
- 📙 [AutoDL 详细配置](./docs/AUTODL_SETUP.md) - 完整配置
- 📕 [代码上传指南](./docs/UPLOAD_GUIDE.md) - Windows 到 AutoDL

### 核心功能
1. **智能衣橱管理** - AI 自动识别分类
2. **语义搜索** - 自然语言检索
3. **场景推荐** - 天气/场合智能推荐
4. **虚拟试衣** - 实时预览效果

### 技术栈
- **后端**: FastAPI + Qwen3-VL (8B)
- **前端**: React 19 + Vite
- **AI**: CatVTON + DensePose + SCHP

### 目录结构
```
fashion-recommendation/
├── docs/              # 📚 项目文档
├── scripts/           # 🛠️ 脚本工具
│   ├── deployment/   # 部署脚本
│   └── utils/        # 工具脚本
├── backend/          # 🚀 FastAPI 后端
├── frontend/         # 💻 React 前端
└── ml/               # 🤖 AI 服务
```

### 系统要求
- GPU: RTX 4090 (24GB) / A100 (40GB+)
- 内存: 30GB+
- 存储: 80GB+

---

**更多详情请查看 [完整文档](./docs/README.md)**
