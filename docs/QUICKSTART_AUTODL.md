# AutoDL 快速启动指南 (3分钟部署)

## 前置要求

**推荐配置:**
- GPU: RTX 4090 (24GB) / A100 (40GB+)
- 内存: 30GB+
- 存储: 80GB+
- 镜像: PyTorch 2.0+ / Python 3.10

---

## 三步启动

### 步骤1: 上传代码到 AutoDL 实例

```bash
# 在 AutoDL JupyterLab Terminal 或 SSH 中执行
cd /root/autodl-tmp

# 方法1: 上传压缩包后解压
unzip fashion-recommendation.zip

# 方法2: 通过 Git 克隆
# git clone <你的仓库> fashion-recommendation
```

### 步骤2: 一键安装环境

```bash
cd /root/autodl-tmp/fashion-recommendation/scripts/deployment
bash autodl_install.sh
```

**安装内容:**
- 创建 `pytorch` 和 `catvton` 两个 Conda 环境
- 安装 PyTorch 2.4.0 + CUDA 12.1
- 安装后端依赖 (FastAPI, Qwen-VL)
- 安装前端依赖 (React, Vite)
- 安装 VTON 服务依赖 (CatVTON, Diffusers, Detectron2)
- 初始化数据库

**预计耗时:** 5-10 分钟

### 步骤3: 启动服务

```bash
cd /root/autodl-tmp/fashion-recommendation
bash start.sh
```

**启动的服务:**
- VTON AI Server (端口 8001) - 虚拟试衣
- Backend API (端口 6008) - FastAPI + Qwen3-VL
- Frontend (端口 6006) - React 界面

---

## 访问应用

启动成功后,在浏览器访问:

```
http://你的AutoDL实例IP:6006
```

**获取实例 IP:**
- 在 AutoDL 控制台查看「公网 IP」
- 或运行: `curl ifconfig.me`

**API 文档:**
```
http://你的AutoDL实例IP:6008/docs
```

---

## 检查环境

在安装前或出现问题时,运行环境检查:

```bash
bash scripts/utils/check_env.sh
```

---

## 查看日志

```bash
# 实时查看所有服务日志
tail -f logs/*.log

# 单独查看
tail -f logs/backend.log   # 后端日志
tail -f logs/vton.log      # VTON 服务日志
tail -f logs/frontend.log  # 前端日志
```

---

## 停止服务

```bash
bash stop.sh
```

---

## 手动启动 (如果自动脚本失败)

### 后端 (端口 6008)
```bash
cd /root/autodl-tmp/fashion-recommendation/backend
source ~/miniconda3/etc/profile.d/conda.sh
conda activate pytorch
uvicorn app.main:app --host 0.0.0.0 --port 6008
```

### VTON 服务 (端口 8001)
```bash
cd /root/autodl-tmp/fashion-recommendation/ml
source ~/miniconda3/etc/profile.d/conda.sh
conda activate catvton
python vton_server.py
```

### 前端 (端口 6006)
```bash
cd /root/autodl-tmp/fashion-recommendation/frontend
source ~/.nvm/nvm.sh  # 如果使用了 NVM
npm run dev
```

---

## 常见问题

### 1. 端口被占用

```bash
# 查看端口占用
netstat -tulnp | grep -E "6006|6008|8001"

# 杀死占用进程
kill -9 <PID>

# 或使用 stop.sh
bash stop.sh
```

### 2. 模型下载失败

```bash
# 设置 HuggingFace 镜像
export HF_ENDPOINT=https://hf-mirror.com

# 手动下载模型
cd /root/autodl-tmp/fashion-recommendation/ml
conda activate catvton
python download_model.py
```

### 3. CUDA Out of Memory

**解决方案:**
- 关闭其他 GPU 进程: `nvidia-smi` 查看并 `kill -9 <PID>`
- 清理显存: `python -c "import torch; torch.cuda.empty_cache()"`
- 或租用更大显存的 GPU (推荐 A100 40GB)

### 4. 前端无法连接后端

**检查清单:**
1. 后端是否启动: `curl http://localhost:6008/health`
2. AutoDL 端口是否开放 (默认全开)
3. 前端 `.env` 配置是否正确

```bash
# 查看前端配置
cat /root/autodl-tmp/fashion-recommendation/frontend/.env

# 应该显示 (替换为你的实例 IP):
# VITE_API_BASE_URL=http://<你的IP>:6008
```

---

## 模型自动下载说明

**首次运行时会自动下载:**
- Qwen3-VL (约 16GB) - 首次上传图片时下载
- CatVTON (约 5GB) - 首次使用虚拟试衣时下载
- DensePose (约 200MB) - 自动下载
- Stable Diffusion Inpainting (约 4GB) - 自动下载

**总计约 25GB,确保磁盘空间充足!**

---

## 性能优化建议

### 1. 保存自定义镜像
环境配置完成后,在 AutoDL 控制台保存自定义镜像,下次直接使用无需重复安装。

### 2. 使用持久化目录
数据库和上传文件已保存在 `/root/autodl-tmp` (持久化目录),关机后数据不会丢失。

### 3. 开启自动关机
在 AutoDL 控制台设置「无操作自动关机」,避免浪费费用。

---

## 功能测试

### 1. 测试后端健康检查
```bash
curl http://localhost:6008/health
# 应返回: {"status":"healthy"}
```

### 2. 测试 VTON 服务
```bash
curl -X POST http://localhost:8001/process_tryon
# 应返回 405 Method Not Allowed (正常,因为需要 POST multipart/form-data)
```

### 3. 测试前端
浏览器访问 `http://<你的IP>:6006`,应该能看到登录页面。

---

## 故障排查流程

1. **运行环境检查**
   ```bash
   bash scripts/utils/check_env.sh
   ```

2. **查看日志文件**
   ```bash
   tail -f logs/*.log
   ```

3. **检查 GPU 状态**
   ```bash
   nvidia-smi
   watch -n 1 nvidia-smi  # 实时监控
   ```

4. **检查进程**
   ```bash
   ps aux | grep -E "uvicorn|vton_server|node"
   ```

5. **重启服务**
   ```bash
   bash stop.sh
   bash start.sh
   ```

---

## 更多文档

详细部署文档: [AUTODL_SETUP.md](./AUTODL_SETUP.md)

---

## 快速检查清单

- [ ] AutoDL 实例已启动 (GPU: 24GB+, 内存: 30GB+)
- [ ] 代码已上传到 `/root/autodl-tmp/fashion-recommendation`
- [ ] 已执行 `bash scripts/deployment/autodl_install.sh`
- [ ] 已执行 `bash start.sh`
- [ ] 能访问 `http://<IP>:6006`
- [ ] 后端健康检查通过 `curl http://localhost:6008/health`
- [ ] GPU 可用 `nvidia-smi` 有输出

全部打勾即可正常使用!
