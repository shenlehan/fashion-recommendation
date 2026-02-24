# Scripts 脚本目录

## 目录结构

```
scripts/
├── deployment/      # 部署相关脚本
│   ├── autodl_install.sh    # AutoDL 一键安装
│   ├── start.sh             # 启动所有服务
│   ├── stop.sh              # 停止所有服务
│   └── upload_to_autodl.ps1 # Windows 上传工具
└── utils/           # 工具脚本
    └── check_env.sh         # 环境检查
```

## 部署脚本 (deployment/)

### autodl_install.sh
**用途**: AutoDL 实例一键安装所有依赖

**使用**:
```bash
cd scripts/deployment
bash autodl_install.sh
```

**功能**:
- 创建 pytorch 和 catvton Conda 环境
- 安装所有 Python 依赖
- 安装 Node.js 依赖
- 初始化数据库

---

### start.sh
**用途**: 启动所有服务 (Backend + Frontend + VTON)

**使用**:
```bash
cd scripts/deployment
bash start.sh
```

**启动的服务**:
- VTON Server (端口 8001)
- Backend API (端口 6008)  
- Frontend (端口 6006)

---

### stop.sh
**用途**: 停止所有服务

**使用**:
```bash
cd scripts/deployment
bash stop.sh
```

---

### upload_to_autodl.ps1
**用途**: Windows 本地上传代码到 AutoDL

**使用**:
```powershell
# 1. 编辑文件填入 AutoDL 信息
# 2. 运行
powershell -ExecutionPolicy Bypass -File upload_to_autodl.ps1
```

**配置项**:
- AUTODL_HOST: AutoDL 实例地址
- AUTODL_PORT: SSH 端口
- PROJECT_DIR: 本地项目路径

---

## 工具脚本 (utils/)

### check_env.sh
**用途**: 检查环境配置是否完整

**使用**:
```bash
cd scripts/utils
bash check_env.sh
```

**检查项**:
- Conda 环境 (pytorch, catvton)
- GPU 状态
- Python 依赖
- Node.js 环境
- 项目文件结构
- 端口状态 (6006, 6008, 8001)
- 磁盘空间
- 系统内存

**输出示例**:
```
==============================================
  检查结果汇总
==============================================
通过: 12
失败: 0

环境检查全部通过,可以运行 bash start.sh 启动服务
```
